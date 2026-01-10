"""
Suno AI Music Generation API Router

Provides REST endpoints for Suno AI music generation.
Credit-only billing (no BYOK support).

Endpoints:
- POST /api/v1/dimension/suno/generate - Generate music
- GET /api/v1/dimension/suno/status/{task_id} - Get task status

License: arkain.info@gmail.com (Gemini Enterprise)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.credit_service import deduct_credits, get_or_create_user_credits, refund_credits
from app.services.suno_service import (
    SunoService,
    SunoMusicRequest,
    SunoMusicResponse,
    SunoModel,
    SunoSong,
    get_suno_service,
)
from app.services.telemetry_integration import record_tool_run

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/suno", tags=["Suno AI"])


# =============================================================================
# Request/Response Models
# =============================================================================

class SunoGenerateRequest(BaseModel):
    """API request for Suno music generation."""
    
    prompt: str = Field(..., min_length=1, max_length=2000, description="Music description or lyrics")
    title: str = Field(..., min_length=1, max_length=100, description="Song title")
    style: str = Field(..., min_length=1, max_length=500, description="Music style/genre (e.g., 'Jazz, Smooth, Relaxing')")
    instrumental: bool = Field(default=False, description="Instrumental only (no vocals)")
    model: str = Field(default="V5", description="Model: V5, V4_5PLUS, V4_5, V4")


class SunoSongResponse(BaseModel):
    """Individual song in response."""
    
    id: str
    title: str
    audio_url: Optional[str] = None
    stream_url: Optional[str] = None
    image_url: Optional[str] = None
    duration: Optional[float] = None


class SunoGenerateResponse(BaseModel):
    """API response for Suno music generation."""
    
    success: bool
    task_id: str
    status: str
    songs: List[SunoSongResponse] = []
    credits_used: int = 0
    error: Optional[str] = None


class SunoStatusResponse(BaseModel):
    """API response for task status."""
    
    task_id: str
    status: str
    songs: List[Dict[str, Any]] = []
    error: Optional[str] = None


# =============================================================================
# Credit Cost Calculation
# =============================================================================

def get_credit_cost(model: str) -> int:
    """Calculate credit cost based on model."""
    costs = {
        "V5": 20,
        "V4_5PLUS": 15,
        "V4_5ALL": 15,
        "V4_5": 12,
        "V4": 10,
    }
    return costs.get(model, 20)


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/generate",
    response_model=SunoGenerateResponse,
    summary="Generate Music with Suno AI",
    description="Generate music using Suno AI. Always uses platform credits (no BYOK).",
)
async def generate_music(
    request: SunoGenerateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SunoGenerateResponse:
    """Generate music using Suno AI."""
    import time
    start_time = time.time()
    
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )
    
    # Calculate credit cost
    credit_cost = get_credit_cost(request.model)
    
    # Check and deduct credits (always required for Suno - no BYOK)
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
        description="Suno AI: Music Generation",
        meta={"model": request.model, "style": request.style[:50]},
    )
    
    try:
        # Build service request
        service_request = SunoMusicRequest(
            prompt=request.prompt,
            title=request.title,
            style=request.style,
            custom_mode=True,
            instrumental=request.instrumental,
            model=SunoModel(request.model),
        )
        
        # Generate music
        service = get_suno_service()
        result = await service.generate_music(service_request, wait_for_completion=True)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        if not result.success:
            # Refund on failure
            await refund_credits(
                db, user_id, credit_cost,
                description="Refund: Suno generation failed",
                meta={"error": result.error[:200] if result.error else "Unknown"},
            )
            
            await record_tool_run(
                db=db,
                tool_key="suno_music_generate",
                user_id=user_id,
                inputs_summary={"title": request.title, "style": request.style[:50]},
                outputs_summary={},
                status="failed",
                latency_ms=latency_ms,
                credits_charged=0,
                error_message=result.error,
            )
            
            return SunoGenerateResponse(
                success=False,
                task_id=result.task_id,
                status="failed",
                error=result.error,
            )
        
        # Convert songs to response format
        songs = [
            SunoSongResponse(
                id=s.id,
                title=s.title,
                audio_url=s.audio_url,
                stream_url=s.stream_url,
                image_url=s.image_url,
                duration=s.duration,
            )
            for s in result.songs
        ]
        
        await record_tool_run(
            db=db,
            tool_key="suno_music_generate",
            user_id=user_id,
            inputs_summary={"title": request.title, "style": request.style[:50], "model": request.model},
            outputs_summary={"song_count": len(songs)},
            status="success",
            latency_ms=latency_ms,
            credits_charged=credit_cost,
        )
        
        return SunoGenerateResponse(
            success=True,
            task_id=result.task_id,
            status="completed",
            songs=songs,
            credits_used=credit_cost,
        )
        
    except Exception as e:
        logger.error(f"Suno generation error: {e}")
        
        # Refund on error
        await refund_credits(
            db, user_id, credit_cost,
            description="Refund: Suno generation error",
            meta={"error": str(e)[:200]},
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/status/{task_id}",
    response_model=SunoStatusResponse,
    summary="Get Generation Status",
    description="Get the status of a Suno music generation task.",
)
async def get_status(
    task_id: str,
    user: dict = Depends(get_current_user),
) -> SunoStatusResponse:
    """Get status of a generation task."""
    service = get_suno_service()
    result = await service.get_task_status(task_id)
    
    return SunoStatusResponse(
        task_id=result.task_id,
        status=result.status,
        songs=result.songs,
        error=result.error,
    )


@router.get(
    "/pricing",
    summary="Get Pricing Information",
    description="Get Suno AI pricing information in credits.",
)
async def get_pricing() -> Dict[str, Any]:
    """Get pricing information."""
    return {
        "service": "Suno AI",
        "provider": "suno",
        "credit_only": True,
        "byok_supported": False,
        "pricing": {
            "V5": {"credits": 20, "usd": 0.14, "songs_per_generation": 2},
            "V4_5PLUS": {"credits": 15, "usd": 0.10, "songs_per_generation": 2},
            "V4_5ALL": {"credits": 15, "usd": 0.10, "songs_per_generation": 2},
            "V4_5": {"credits": 12, "usd": 0.08, "songs_per_generation": 2},
            "V4": {"credits": 10, "usd": 0.07, "songs_per_generation": 2},
        },
        "supported_models": ["V5", "V4_5PLUS", "V4_5ALL", "V4_5", "V4"],
        "features": [
            "Custom mode with lyrics",
            "Instrumental mode",
            "Multiple music styles",
            "2 songs per generation",
            "Stream & download URLs",
        ],
    }
