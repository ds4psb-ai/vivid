"""
VEO Dimension Endpoints - Video Generation.

- VEO Generate: Generate video using Veo 3.1
- VEO Generate Stream: SSE streaming version with progress

Security:
- XSS sanitization for style and negative_prompt fields
- Veo model whitelist validation
"""
from __future__ import annotations

import asyncio
import html
import json
import logging
import re
from enum import Enum

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from ._base import (
    get_db,
    get_current_user,
    get_byok_key,
    _execute_dimension_tool,
    _refund_with_retry,
    _validate_model,
    _validate_aspect_ratio,
    _validate_veo_duration,
    _strip_string,
    DimensionResponse,
    DimensionErrorResponse,
    DimensionCapsuleId,
    get_sse_headers,
    sse_heartbeat,
    logger,
    Optional,
)
from app.credit_service import deduct_credits, get_or_create_user_credits

router = APIRouter()

# Module logger
veo_logger = logging.getLogger(__name__)


# ============================================================================
# Constants & Enums
# ============================================================================

class VeoModel(str, Enum):
    """Supported Veo 3.1 models."""
    GENERATE_PREVIEW = "veo-3.1-generate-preview"
    FAST_GENERATE_PREVIEW = "veo-3.1-fast-generate-preview"


ALLOWED_VEO_MODELS = frozenset([m.value for m in VeoModel])


# ============================================================================
# Sanitization Helpers
# ============================================================================

def _sanitize_text_field(value: str, default: str = "") -> str:
    """Sanitize text fields (style, negative_prompt) to prevent XSS.

    Args:
        value: Raw text input
        default: Default value if empty

    Returns:
        Sanitized string
    """
    if not value:
        return default
    # Strip whitespace
    value = value.strip()
    if not value:
        return default
    # Remove HTML tags
    value = re.sub(r"<[^>]+>", "", value)
    # Escape HTML entities
    value = html.escape(value)
    # Remove script/javascript patterns
    value = re.sub(r"(?i)javascript\s*:", "", value)
    value = re.sub(r"(?i)on\w+\s*=", "", value)
    return value or default


def _validate_veo_model(value: str) -> str:
    """Validate Veo model is in allowed list.

    Args:
        value: Raw model name

    Returns:
        Validated model name

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip()
    if value not in ALLOWED_VEO_MODELS:
        raise ValueError(
            f"Invalid Veo model: {value}. Allowed: {sorted(ALLOWED_VEO_MODELS)}"
        )
    return value


# ============================================================================
# Request Models
# ============================================================================

class VeoGenerateRequest(BaseModel):
    """Request model for Veo 3.1 video generation.

    Includes:
    - XSS sanitization for style and negative_prompt
    - Veo model whitelist validation
    """
    prompt: str = Field(..., min_length=1, max_length=5000, description="Video generation prompt")
    negative_prompt: str = Field("", max_length=1000, description="Negative prompt (sanitized)")
    aspect_ratio: str = Field("16:9", description="Aspect ratio")
    duration: int = Field(6, ge=4, le=8, description="Video duration (4-8 seconds)")
    style: str = Field("cinematic", max_length=100, description="Visual style (sanitized)")
    seed: int = Field(0, ge=0, description="Random seed (0 for random)")
    model: str = Field("veo-3.1-generate-preview", description="Veo model")

    @field_validator("prompt", mode="before")
    @classmethod
    def strip_prompt(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("negative_prompt", mode="before")
    @classmethod
    def sanitize_negative_prompt(cls, v: str) -> str:
        """Sanitize negative_prompt to prevent XSS."""
        return _sanitize_text_field(v, default="")

    @field_validator("style", mode="before")
    @classmethod
    def sanitize_style(cls, v: str) -> str:
        """Sanitize style to prevent XSS."""
        return _sanitize_text_field(v, default="cinematic")

    @field_validator("aspect_ratio")
    @classmethod
    def validate_aspect_ratio(cls, v: str) -> str:
        return _validate_aspect_ratio(v)

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        return _validate_veo_duration(v)

    @field_validator("model")
    @classmethod
    def validate_veo_model(cls, v: str) -> str:
        """Validate Veo model is in allowed whitelist."""
        return _validate_veo_model(v)


# ============================================================================
# VEO Generate (Non-Streaming)
# ============================================================================

@router.post(
    "/veo/generate",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Veo 3.1: Generate Video",
    description="Generate video using Veo 3.1 from text prompt.",
    tags=["Dimension VEO"],
)
async def generate_veo_video(
    request: VeoGenerateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Generate video with Veo 3.1 with Intent-Resolver integration."""
    user_id = user.get("id", "unknown")
    veo_logger.info(
        f"[VEO_GENERATE] user={user_id} prompt_len={len(request.prompt)} "
        f"duration={request.duration}s aspect={request.aspect_ratio} model={request.model}"
    )

    from app.routers.intent_helpers import with_intent
    intent = with_intent(request)

    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.VEO_VIDEO_GENERATE,
        tool_key="veo_generate",
        inputs={
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "aspect_ratio": request.aspect_ratio,
            "duration": request.duration,
            "style": request.style,
            "seed": request.seed,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"prompt": request.prompt[:100], "style": request.style},
        intent=intent,
    )


# ============================================================================
# VEO Generate with SSE Streaming
# ============================================================================

@router.post(
    "/veo/generate/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Veo 3.1: Generate Video with SSE Progress",
    description="Generate video using Veo 3.1 with real-time progress updates via SSE.",
    tags=["Dimension VEO"],
)
async def generate_veo_video_stream(
    request: VeoGenerateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Generate video with Veo 3.1 with SSE progress streaming and Intent-Resolver integration."""
    from app.services.veo_service import VeoConfig, VeoProgress, get_veo_service
    from app.fixtures.dimension_capsules import DIMENSION_CAPSULES
    from app.routers.intent_helpers import with_intent

    user_id = user.get("id", "anonymous")
    veo_logger.info(
        f"[VEO_STREAM] user={user_id} prompt_len={len(request.prompt)} "
        f"duration={request.duration}s aspect={request.aspect_ratio} model={request.model}"
    )

    # Intent inference for RAG context
    intent = with_intent(request)

    # Get capsule info for credit cost
    capsule_info = next(
        (c for c in DIMENSION_CAPSULES if c["id"] == DimensionCapsuleId.VEO_VIDEO_GENERATE.value),
        None
    )
    credit_cost = capsule_info["cost"] if capsule_info else 200

    async def event_stream():
        """SSE event generator with progress updates."""
        credits_deducted = False
        enhanced_prompt = request.prompt

        try:
            # Intent-Resolver enhancement for prompt
            if intent:
                try:
                    from app.resolvers.integration import prepare_dimension_params
                    enhanced_inputs, _ = await prepare_dimension_params(
                        dimension_code="VEO",
                        inputs={"prompt": request.prompt, "style": request.style},
                        params={},
                        intent=intent,
                    )
                    enhanced_prompt = enhanced_inputs.get("prompt", request.prompt)
                    logger.debug(f"[VEO Stream] Intent-enhanced prompt applied")
                except Exception as e:
                    logger.warning(f"[VEO Stream] Intent enhancement failed: {e}")

            # Check credits if not BYOK
            if not byok_key:
                user_credits = await get_or_create_user_credits(db, user_id)
                if user_credits.balance < credit_cost:
                    yield f"data: {json.dumps({'type': 'error', 'error': '크레딧이 부족합니다.', 'code': 'INSUFFICIENT_CREDITS', 'required': credit_cost, 'available': user_credits.balance})}\n\n"
                    return

                # Deduct credits upfront
                try:
                    await deduct_credits(
                        db, user_id, credit_cost,
                        f"Veo video generation: {request.prompt[:50]}...",
                        {"capsule_id": DimensionCapsuleId.VEO_VIDEO_GENERATE.value}
                    )
                    credits_deducted = True
                except ValueError as e:
                    if "insufficient" in str(e).lower():
                        yield f"data: {json.dumps({'type': 'error', 'error': '크레딧이 부족합니다. (동시 요청으로 인한 잔액 변동)', 'code': 'INSUFFICIENT_CREDITS'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'code': 'CREDIT_ERROR'})}\n\n"
                    return

            # Build config with enhanced prompt
            config = VeoConfig(
                prompt=enhanced_prompt,
                model=request.model if request.model in ["veo-3.1-generate-preview", "veo-3.1-fast-generate-preview"] else "veo-3.1-generate-preview",
                duration_seconds=min(max(request.duration, 4), 8),
                aspect_ratio=request.aspect_ratio or "16:9",
                negative_prompt=request.negative_prompt,
                include_audio=True,
            )

            # Progress callback
            progress_queue: asyncio.Queue[VeoProgress] = asyncio.Queue()

            def progress_callback(progress: VeoProgress):
                try:
                    progress_queue.put_nowait(progress)
                except Exception:
                    pass

            # Get service
            service = get_veo_service(api_key=byok_key)

            # Start generation in background
            generation_task = asyncio.create_task(
                service.generate_video(
                    config=config,
                    progress_callback=progress_callback,
                )
            )

            # Yield progress events
            while not generation_task.done():
                try:
                    progress = await asyncio.wait_for(
                        progress_queue.get(),
                        timeout=5.0
                    )
                    yield f"data: {json.dumps({'type': 'progress', 'status': progress.status, 'elapsed_seconds': round(progress.elapsed_seconds, 1), 'estimated_remaining_seconds': round(progress.estimated_remaining_seconds, 1) if progress.estimated_remaining_seconds else None, 'poll_count': progress.poll_count, 'message': progress.message})}\n\n"
                except asyncio.TimeoutError:
                    yield sse_heartbeat()

            # Get final result
            result = await generation_task

            if result.success:
                yield f"data: {json.dumps({'type': 'complete', 'success': True, 'video_uri': result.video_uri, 'duration_ms': result.duration_ms, 'credit_cost': result.credit_cost, 'metadata': result.metadata})}\n\n"
            else:
                if credits_deducted:
                    await _refund_with_retry(
                        db, user_id, credit_cost,
                        f"Veo generation failed: {result.error}",
                        {"capsule_id": DimensionCapsuleId.VEO_VIDEO_GENERATE.value}
                    )
                yield f"data: {json.dumps({'type': 'error', 'success': False, 'error': result.error, 'duration_ms': result.duration_ms})}\n\n"

        except asyncio.CancelledError:
            logger.info(f"VEO SSE client disconnected, user={user_id}")
            if 'generation_task' in locals() and not generation_task.done():
                generation_task.cancel()
            if credits_deducted:
                try:
                    await _refund_with_retry(
                        db, user_id, credit_cost,
                        "Veo client disconnected",
                        {"capsule_id": DimensionCapsuleId.VEO_VIDEO_GENERATE.value, "reason": "client_disconnect"}
                    )
                    logger.info(f"Refunded {credit_cost} VEO credits for disconnected user {user_id}")
                except Exception as refund_err:
                    logger.error(f"Failed to refund VEO credits on disconnect: {refund_err}")
            raise
        except Exception as e:
            logger.exception(f"Veo SSE stream error: {e}")
            if credits_deducted:
                try:
                    await _refund_with_retry(
                        db, user_id, credit_cost,
                        f"Veo generation error: {str(e)}",
                        {"capsule_id": DimensionCapsuleId.VEO_VIDEO_GENERATE.value}
                    )
                except Exception:
                    pass
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )
