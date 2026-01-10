"""
Kling AI Video Generation API Router

Provides REST endpoints for Kling AI video generation.
Credit-only billing (no BYOK support).

Endpoints:
- POST /api/v1/dimension/kling/generate - Generate video
- GET /api/v1/dimension/kling/status/{task_id} - Get task status

License: arkain.info@gmail.com (Gemini Enterprise)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.credit_service import deduct_credits, get_or_create_user_credits, refund_credits
from app.services.kling_service import (
    KlingService,
    KlingVideoRequest,
    KlingVideoResponse,
    KlingDuration,
    KlingAspectRatio,
    KlingResolution,
    KlingMode,
    get_kling_service,
)
from app.services.telemetry_integration import record_tool_run

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kling", tags=["Kling AI"])


# =============================================================================
# Request/Response Models
# =============================================================================

class KlingGenerateRequest(BaseModel):
    """API request for Kling video generation."""
    
    prompt: str = Field(..., min_length=1, max_length=2500, description="Video description")
    negative_prompt: Optional[str] = Field(None, max_length=500, description="Elements to avoid")
    duration: str = Field(default="5", description="Duration: 5 or 10 seconds")
    aspect_ratio: str = Field(default="16:9", description="Aspect ratio")
    resolution: str = Field(default="1080p", description="Resolution: 720p or 1080p")
    mode: str = Field(default="std", description="Mode: std or pro")
    enable_audio: bool = Field(default=False, description="Enable audio generation")
    image_url: Optional[str] = Field(None, description="Initial image for image-to-video")


class KlingGenerateResponse(BaseModel):
    """API response for Kling video generation."""
    
    success: bool
    task_id: str
    status: str
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    credits_used: int = 0
    error: Optional[str] = None


class KlingStatusResponse(BaseModel):
    """API response for task status."""
    
    task_id: str
    status: str
    video_url: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# Credit Cost Calculation
# =============================================================================

def get_credit_cost(duration: str, resolution: str) -> int:
    """Calculate credit cost based on duration and resolution."""
    costs = {
        ("5", "720p"): 35,
        ("5", "1080p"): 50,
        ("10", "720p"): 70,
        ("10", "1080p"): 100,
    }
    return costs.get((duration, resolution), 50)


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/generate",
    response_model=KlingGenerateResponse,
    summary="Generate Video with Kling AI",
    description="Generate a video using Kling AI. Always uses platform credits (no BYOK).",
)
async def generate_video(
    request: KlingGenerateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KlingGenerateResponse:
    """Generate video using Kling AI."""
    import time
    start_time = time.time()
    
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )
    
    # Calculate credit cost
    credit_cost = get_credit_cost(request.duration, request.resolution)
    
    # Check and deduct credits (always required for Kling - no BYOK)
    user_credits = await get_or_create_user_credits(db, user_id)
    if user_credits.balance < credit_cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "INSUFFICIENT_CREDITS",
                "message": "크레딧이 부족합니다.",
                "required": credit_cost,
                "balance": user_credits.balance,
            },
        )
    
    await deduct_credits(
        db, user_id, credit_cost,
        description="Kling AI: Video Generation",
        meta={"duration": request.duration, "resolution": request.resolution},
    )
    
    try:
        # Build service request
        service_request = KlingVideoRequest(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            duration=KlingDuration(request.duration),
            aspect_ratio=KlingAspectRatio(request.aspect_ratio),
            resolution=KlingResolution(request.resolution),
            mode=KlingMode(request.mode),
            enable_audio=request.enable_audio,
            image_url=request.image_url,
        )
        
        # Generate video
        service = get_kling_service()
        result = await service.generate_video(service_request, wait_for_completion=True)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        if not result.success:
            # Refund on failure
            await refund_credits(
                db, user_id, credit_cost,
                description="Refund: Kling generation failed",
                meta={"error": result.error[:200] if result.error else "Unknown"},
            )
            
            await record_tool_run(
                db=db,
                tool_key="kling_video_generate",
                user_id=user_id,
                inputs_summary={"prompt": request.prompt[:100]},
                outputs_summary={},
                status="failed",
                latency_ms=latency_ms,
                credits_charged=0,
                error_message=result.error,
            )
            
            return KlingGenerateResponse(
                success=False,
                task_id=result.task_id,
                status="failed",
                error=result.error,
            )
        
        await record_tool_run(
            db=db,
            tool_key="kling_video_generate",
            user_id=user_id,
            inputs_summary={"prompt": request.prompt[:100], "duration": request.duration},
            outputs_summary={"has_video": bool(result.video_url)},
            status="success",
            latency_ms=latency_ms,
            credits_charged=credit_cost,
        )
        
        return KlingGenerateResponse(
            success=True,
            task_id=result.task_id,
            status="completed",
            video_url=result.video_url,
            credits_used=credit_cost,
        )
        
    except Exception as e:
        logger.error(f"Kling generation error: {e}")
        
        # Refund on error
        await refund_credits(
            db, user_id, credit_cost,
            description="Refund: Kling generation error",
            meta={"error": str(e)[:200]},
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/status/{task_id}",
    response_model=KlingStatusResponse,
    summary="Get Generation Status",
    description="Get the status of a Kling video generation task.",
)
async def get_status(
    task_id: str,
    user: dict = Depends(get_current_user),
) -> KlingStatusResponse:
    """Get status of a generation task."""
    service = get_kling_service()
    result = await service.get_task_status(task_id)
    
    return KlingStatusResponse(
        task_id=result.task_id,
        status=result.status,
        video_url=result.video_url,
        error=result.error,
    )


@router.get(
    "/pricing",
    summary="Get Pricing Information",
    description="Get Kling AI pricing information in credits.",
)
async def get_pricing() -> Dict[str, Any]:
    """Get pricing information."""
    return {
        "service": "Kling AI",
        "provider": "kling",
        "credit_only": True,
        "byok_supported": False,
        "pricing": {
            "5s_720p": {"credits": 35, "usd": 0.25},
            "5s_1080p": {"credits": 50, "usd": 0.35},
            "10s_720p": {"credits": 70, "usd": 0.50},
            "10s_1080p": {"credits": 100, "usd": 0.70},
        },
        "supported_models": ["kling-v2.6", "kling-v2.5", "kling-v2.2"],
        "features": [
            "Text-to-video",
            "Image-to-video",
            "Audio generation (v2.6+)",
            "720p / 1080p resolution",
            "5s / 10s duration",
        ],
    }
