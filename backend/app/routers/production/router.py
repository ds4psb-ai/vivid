"""Production Bridge Router - Unified Media Generation API.

Mega app router for video/audio/image generation:
- /api/production/generate - Generate with specific provider
- /api/production/generate/auto - Automatic provider selection
- /api/production/generate/multi - Multi-provider parallel generation

Features:
- Unified request/response model
- SSE streaming for progress
- Credit management with refund
- Provider capabilities endpoint

Usage:
    POST /api/production/generate
    {
        "provider": "veo",
        "prompt": "Cinematic scene of a sunset",
        "duration_seconds": 8
    }
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.production.providers.base import (
    MediaType,
    GenerationRequest,
    GenerationProgress,
    GenerationResult,
)
from app.services.production_bridge_service import (
    ProductionBridgeService,
    ProductionBridgeResult,
    get_production_bridge_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/production", tags=["Production Bridge"])


# =============================================================================
# Dependencies
# =============================================================================

async def get_db():
    """Get database session."""
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user() -> dict:
    """Get current authenticated user."""
    return {"id": "test-user", "email": "test@example.com"}


async def get_or_create_user_credits(user_id: str, db: AsyncSession):
    """Get or create user credits record."""
    from app.services.kelly_credit_service import get_or_create_user_credits as _get_credits
    return await _get_credits(db, user_id)


async def deduct_credits(user_id: str, amount: int, db: AsyncSession, reason: str = ""):
    """Deduct credits from user account."""
    from app.services.kelly_credit_service import deduct_credits as _deduct
    return await _deduct(db, user_id, amount, reason)


async def refund_credits(user_id: str, amount: int, db: AsyncSession, reason: str = ""):
    """Refund credits to user account."""
    from app.services.kelly_credit_service import refund_credits as _refund
    return await _refund(db, user_id, amount, reason)


# =============================================================================
# Request/Response Models
# =============================================================================

class GenerateRequest(BaseModel):
    """Request for content generation.

    Veo 3.1 Enhancements (2026):
    - reference_images: Up to 3 reference images for character/style consistency
    - first_frame_url/last_frame_url: Frame control for transition generation
    """
    provider: str = Field("veo", description="Provider: veo, kling, suno")
    prompt: str = Field(..., min_length=5, max_length=5000, description="Generation prompt")
    negative_prompt: Optional[str] = Field(None, max_length=1000, description="Negative prompt")
    media_type: str = Field("video", description="Media type: video, audio, image")
    duration_seconds: Optional[int] = Field(8, ge=1, le=300, description="Duration in seconds")
    aspect_ratio: str = Field("16:9", description="Aspect ratio")
    resolution: str = Field("1080p", description="Resolution")
    system_prompt: Optional[str] = Field(None, max_length=3000, description="System prompt from DNA Lab")
    style: Optional[str] = Field(None, max_length=100, description="Visual style")

    # Legacy field (deprecated, use reference_images instead)
    reference_image_url: Optional[str] = Field(
        None,
        description="(Deprecated) Single reference image URL - use reference_images instead"
    )

    # Veo 3.1 Reference Images (max 3) - Character/Style Consistency
    reference_images: List[str] = Field(
        default_factory=list,
        max_length=3,
        description="Reference images for character/style consistency (max 3, Veo 3.1)"
    )

    # Veo 3.1 First/Last Frame Control - Transition Generation
    first_frame_url: Optional[str] = Field(
        None,
        description="First frame image URL for transition generation (Veo 3.1)"
    )
    last_frame_url: Optional[str] = Field(
        None,
        description="Last frame image URL for transition generation (Veo 3.1)"
    )

    include_audio: bool = Field(True, description="Include audio generation")
    model: Optional[str] = Field(None, description="Specific model to use")

    @field_validator("media_type")
    @classmethod
    def validate_media_type(cls, v: str) -> str:
        valid = ["video", "audio", "image"]
        if v.lower() not in valid:
            raise ValueError(f"Invalid media type: {v}. Must be one of: {valid}")
        return v.lower()

    @field_validator("reference_images")
    @classmethod
    def validate_reference_images(cls, v: List[str]) -> List[str]:
        if len(v) > 3:
            raise ValueError("Maximum 3 reference images allowed (Veo 3.1 limit)")
        return v


class GenerateAutoRequest(BaseModel):
    """Request for auto-selected generation."""
    prompt: str = Field(..., min_length=5, max_length=5000)
    negative_prompt: Optional[str] = Field(None, max_length=1000)
    media_type: str = Field("video")
    duration_seconds: Optional[int] = Field(8, ge=1, le=300)
    aspect_ratio: str = Field("16:9")
    system_prompt: Optional[str] = Field(None, max_length=3000)
    style: Optional[str] = Field(None)


class GenerateMultiRequest(BaseModel):
    """Request for multi-provider generation."""
    jobs: List[Dict[str, Any]] = Field(..., min_length=1, max_length=5)
    parallel: bool = Field(True, description="Run jobs in parallel")


class GenerationResponse(BaseModel):
    """Response from content generation."""
    success: bool
    provider: str
    media_type: str
    media_uri: Optional[str] = None
    trace_id: str = ""
    duration_ms: int = 0
    credits_used: int = 0
    evidence_refs: List[str] = []
    error: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProviderInfoResponse(BaseModel):
    """Provider capabilities response."""
    name: str
    display_name: str
    media_types: List[str]
    max_duration_seconds: Optional[int] = None
    supported_resolutions: List[str] = []
    supported_aspect_ratios: List[str] = []
    supports_audio: bool = False
    supports_image_to_video: bool = False
    supports_reference_images: bool = False
    max_reference_images: int = 0  # Veo 3.1 supports up to 3
    supports_frame_control: bool = False  # Veo 3.1 first/last frame
    default_model: str = ""
    available_models: List[str] = []
    credit_cost_base: int = 0


# =============================================================================
# Helper Functions
# =============================================================================

def _to_generation_request(req: GenerateRequest) -> GenerationRequest:
    """Convert API request to GenerationRequest."""
    media_type = MediaType(req.media_type)
    return GenerationRequest(
        prompt=req.prompt,
        negative_prompt=req.negative_prompt,
        media_type=media_type,
        duration_seconds=req.duration_seconds,
        aspect_ratio=req.aspect_ratio,
        resolution=req.resolution,
        system_prompt=req.system_prompt,
        style=req.style,
        reference_image_url=req.reference_image_url,  # Deprecated, kept for backward compatibility
        reference_images=req.reference_images,  # Veo 3.1: up to 3 reference images
        first_frame_url=req.first_frame_url,  # Veo 3.1: transition start frame
        last_frame_url=req.last_frame_url,  # Veo 3.1: transition end frame
        include_audio=req.include_audio,
        model=req.model,
    )


def _to_response(result: GenerationResult) -> GenerationResponse:
    """Convert GenerationResult to API response."""
    return GenerationResponse(
        success=result.success,
        provider=result.provider,
        media_type=result.media_type.value,
        media_uri=result.media_uri,
        trace_id=result.trace_id,
        duration_ms=result.duration_ms,
        credits_used=result.credits_used,
        evidence_refs=result.evidence_refs,
        error=result.error,
        error_code=result.error_code,
        metadata=result.metadata,
    )


async def _sse_event(event_type: str, data: Any) -> str:
    """Format SSE event."""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/generate",
    response_model=GenerationResponse,
    summary="Generate Content",
    description="Generate video/audio/image content using a specific provider.",
)
async def generate_content(
    request: GenerateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GenerationResponse:
    """Generate content with specific provider."""
    user_id = user.get("id", "unknown")
    trace_id = f"production-{uuid.uuid4().hex[:12]}"

    logger.info(
        f"[PRODUCTION] user={user_id} provider={request.provider} "
        f"media_type={request.media_type} duration={request.duration_seconds}s"
    )

    service = get_production_bridge_service()

    # Check provider exists
    provider = service.get_provider(request.provider)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{request.provider}' not found. Available: {service.list_providers()}",
        )

    # Calculate credits
    gen_request = _to_generation_request(request)
    required_credits = service.calculate_credits(request.provider, gen_request)

    # Check user credits
    try:
        user_credits = await get_or_create_user_credits(user_id, db)
        if user_credits.balance < required_credits:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "Insufficient credits",
                    "required": required_credits,
                    "available": user_credits.balance,
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"[PRODUCTION] Credit check skipped: {e}")

    try:
        # Deduct credits
        await deduct_credits(user_id, required_credits, db, f"production:{request.provider}:{trace_id}")

        # Generate content
        result = await service.generate(request.provider, gen_request)

        # Partial refund if failed
        if not result.success:
            await refund_credits(user_id, required_credits, db, f"production-failed:{trace_id}")

        return _to_response(result)

    except Exception as e:
        logger.error(f"[PRODUCTION] Generation error: {e}")
        # Full refund on error
        await refund_credits(user_id, required_credits, db, f"production-error:{trace_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e), "trace_id": trace_id},
        )


@router.post(
    "/generate/stream",
    summary="Generate Content (SSE Stream)",
    description="Generate content with real-time progress updates via SSE.",
)
async def generate_content_stream(
    request: GenerateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Generate content with SSE streaming."""
    user_id = user.get("id", "unknown")
    trace_id = f"production-{uuid.uuid4().hex[:12]}"

    async def stream_generator():
        try:
            yield await _sse_event("start", {
                "trace_id": trace_id,
                "provider": request.provider,
                "status": "started",
            })

            service = get_production_bridge_service()
            gen_request = _to_generation_request(request)

            # Progress callback for SSE
            async def progress_callback(progress: GenerationProgress):
                yield await _sse_event("progress", {
                    "status": progress.status.value,
                    "progress": progress.progress,
                    "message": progress.message,
                    "elapsed_seconds": progress.elapsed_seconds,
                })

            result = await service.generate(request.provider, gen_request)

            yield await _sse_event("complete", _to_response(result).model_dump())

        except Exception as e:
            logger.error(f"[PRODUCTION_STREAM] Error: {e}")
            yield await _sse_event("error", {"error": str(e), "trace_id": trace_id})

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/generate/auto",
    response_model=GenerationResponse,
    summary="Generate Content (Auto Provider)",
    description="Generate content with automatic best provider selection.",
)
async def generate_content_auto(
    request: GenerateAutoRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GenerationResponse:
    """Generate content with automatic provider selection."""
    user_id = user.get("id", "unknown")

    logger.info(f"[PRODUCTION_AUTO] user={user_id} media_type={request.media_type}")

    service = get_production_bridge_service()

    gen_request = GenerationRequest(
        prompt=request.prompt,
        negative_prompt=request.negative_prompt,
        media_type=MediaType(request.media_type),
        duration_seconds=request.duration_seconds,
        aspect_ratio=request.aspect_ratio,
        system_prompt=request.system_prompt,
        style=request.style,
    )

    result = await service.generate_auto(gen_request)
    return _to_response(result)


@router.post(
    "/generate/multi",
    summary="Generate Multi-Provider",
    description="Generate content with multiple providers in parallel.",
)
async def generate_content_multi(
    request: GenerateMultiRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate content with multiple providers."""
    user_id = user.get("id", "unknown")

    logger.info(f"[PRODUCTION_MULTI] user={user_id} jobs={len(request.jobs)}")

    service = get_production_bridge_service()

    # Convert job dicts to proper format
    jobs = []
    for job in request.jobs:
        provider = job.get("provider", "veo")
        req_data = job.get("request", {})
        if isinstance(req_data, dict):
            gen_request = GenerationRequest(
                prompt=req_data.get("prompt", ""),
                media_type=MediaType(req_data.get("media_type", "video")),
                duration_seconds=req_data.get("duration_seconds", 8),
                aspect_ratio=req_data.get("aspect_ratio", "16:9"),
                system_prompt=req_data.get("system_prompt"),
            )
        else:
            gen_request = req_data

        jobs.append({"provider": provider, "request": gen_request})

    result = await service.generate_multi(jobs, parallel=request.parallel)

    return {
        "success": result.success,
        "trace_id": result.trace_id,
        "jobs": [
            {
                "job_id": j.job_id,
                "provider": j.provider,
                "status": j.status,
                "result": _to_response(j.result).model_dump() if j.result else None,
                "error": j.error,
            }
            for j in result.jobs
        ],
        "total_credits_used": result.total_credits_used,
        "evidence_refs": result.evidence_refs,
        "errors": result.errors if result.errors else None,
    }


@router.get(
    "/providers",
    summary="List Providers",
    description="List all available generation providers.",
)
async def list_providers():
    """List available providers."""
    service = get_production_bridge_service()
    providers = []

    for name in service.list_providers():
        caps = service.get_provider_capabilities(name)
        if caps:
            providers.append(ProviderInfoResponse(
                name=caps.name,
                display_name=caps.display_name,
                media_types=[mt.value for mt in caps.media_types],
                max_duration_seconds=caps.max_duration_seconds,
                supported_resolutions=caps.supported_resolutions,
                supported_aspect_ratios=caps.supported_aspect_ratios,
                supports_audio=caps.supports_audio,
                supports_image_to_video=caps.supports_image_to_video,
                supports_reference_images=caps.supports_reference_images,
                max_reference_images=caps.max_reference_images,
                supports_frame_control=caps.supports_frame_control,
                default_model=caps.default_model,
                available_models=caps.available_models,
                credit_cost_base=caps.credit_cost_base,
            ))

    return {
        "providers": [p.model_dump() for p in providers],
        "default_video": "veo",
        "default_audio": "suno",
    }


@router.get(
    "/providers/{provider_name}",
    response_model=ProviderInfoResponse,
    summary="Get Provider Info",
    description="Get detailed information about a specific provider.",
)
async def get_provider_info(provider_name: str):
    """Get provider capabilities."""
    service = get_production_bridge_service()
    caps = service.get_provider_capabilities(provider_name)

    if not caps:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_name}' not found",
        )

    return ProviderInfoResponse(
        name=caps.name,
        display_name=caps.display_name,
        media_types=[mt.value for mt in caps.media_types],
        max_duration_seconds=caps.max_duration_seconds,
        supported_resolutions=caps.supported_resolutions,
        supported_aspect_ratios=caps.supported_aspect_ratios,
        supports_audio=caps.supports_audio,
        supports_image_to_video=caps.supports_image_to_video,
        supports_reference_images=caps.supports_reference_images,
        max_reference_images=caps.max_reference_images,
        supports_frame_control=caps.supports_frame_control,
        default_model=caps.default_model,
        available_models=caps.available_models,
        credit_cost_base=caps.credit_cost_base,
    )


@router.post(
    "/calculate-credits",
    summary="Calculate Credits",
    description="Calculate credit cost for a generation request.",
)
async def calculate_credits(
    request: GenerateRequest,
):
    """Calculate credits for a request."""
    service = get_production_bridge_service()
    gen_request = _to_generation_request(request)
    credits = service.calculate_credits(request.provider, gen_request)

    return {
        "provider": request.provider,
        "credits": credits,
        "media_type": request.media_type,
        "duration_seconds": request.duration_seconds,
    }


@router.get(
    "/health",
    summary="Health Check",
    description="Production Bridge service health check.",
)
async def health_check():
    """Health check endpoint."""
    service = get_production_bridge_service()
    return {
        "service": "production_bridge",
        "status": "healthy",
        "providers": service.list_providers(),
        "version": "1.0.0",
    }


# =============================================================================
# Exports
# =============================================================================

__all__ = ["router"]
