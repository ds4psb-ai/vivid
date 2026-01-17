"""
Suno AI Music Generation API Router

Provides REST endpoints for Suno AI music generation.
Credit-only billing (no BYOK support).

Endpoints:
- POST /api/v1/dimension/suno/generate - Generate music
- GET /api/v1/dimension/suno/status/{task_id} - Get task status

Security:
- XSS sanitization for prompt, title, style
- Model whitelist validation
"""
from __future__ import annotations

import html
import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
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
# Constants & Validation
# =============================================================================

ALLOWED_SUNO_MODELS = frozenset(["V5", "V4_5PLUS", "V4_5ALL", "V4_5", "V4"])


# =============================================================================
# Sanitization Helpers
# =============================================================================

def _sanitize_text(value: str) -> str:
    """Sanitize text fields to prevent XSS.

    Args:
        value: Raw text input

    Returns:
        Sanitized string
    """
    if not value:
        return value
    value = value.strip()
    # Remove HTML tags
    value = re.sub(r"<[^>]+>", "", value)
    # Escape HTML entities
    value = html.escape(value)
    # Remove script/javascript patterns
    value = re.sub(r"(?i)javascript\s*:", "", value)
    value = re.sub(r"(?i)on\w+\s*=", "", value)
    return value


def _validate_suno_model(value: str) -> str:
    """Validate Suno model is in allowed list.

    Args:
        value: Raw model name

    Returns:
        Validated model name

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip()
    if value not in ALLOWED_SUNO_MODELS:
        raise ValueError(
            f"Invalid model: {value}. Allowed: {sorted(ALLOWED_SUNO_MODELS)}"
        )
    return value


# =============================================================================
# Request/Response Models
# =============================================================================

class SunoGenerateRequest(BaseModel):
    """API request for Suno music generation.

    Includes:
    - XSS sanitization for prompt, title, style
    - Model whitelist validation
    """

    prompt: str = Field(..., min_length=1, max_length=2000, description="Music description or lyrics (sanitized)")
    title: str = Field(..., min_length=1, max_length=100, description="Song title (sanitized)")
    style: str = Field(..., min_length=1, max_length=500, description="Music style/genre (sanitized)")
    instrumental: bool = Field(default=False, description="Instrumental only (no vocals)")
    model: str = Field(default="V5", description="Model: V5, V4_5PLUS, V4_5ALL, V4_5, V4")

    @field_validator("prompt", mode="before")
    @classmethod
    def sanitize_prompt(cls, v: str) -> str:
        """Sanitize prompt to prevent XSS."""
        return _sanitize_text(v)

    @field_validator("title", mode="before")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        """Sanitize title to prevent XSS."""
        return _sanitize_text(v)

    @field_validator("style", mode="before")
    @classmethod
    def sanitize_style(cls, v: str) -> str:
        """Sanitize style to prevent XSS."""
        return _sanitize_text(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate model is in allowed whitelist."""
        return _validate_suno_model(v)


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
    logger.info(
        f"[SUNO_GENERATE] user={user_id} title={request.title[:50]} "
        f"style={request.style[:50]} model={request.model} instrumental={request.instrumental}"
    )

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
