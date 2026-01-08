"""
VEO Dimension Endpoints - Video Generation.

- VEO Generate: Generate video using Veo 3.1
- VEO Generate Stream: SSE streaming version with progress
"""
from __future__ import annotations

import asyncio
import json

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


# ============================================================================
# Request Models
# ============================================================================

class VeoGenerateRequest(BaseModel):
    """Request model for Veo 3.1 video generation."""
    prompt: str = Field(..., min_length=1, max_length=5000, description="Video generation prompt")
    negative_prompt: str = Field("", max_length=1000, description="Negative prompt")
    aspect_ratio: str = Field("16:9", description="Aspect ratio")
    duration: int = Field(6, ge=4, le=8, description="Video duration (4-8 seconds)")
    style: str = Field("cinematic", max_length=100, description="Visual style")
    seed: int = Field(0, ge=0, description="Random seed (0 for random)")
    model: str = Field("veo-3.1-generate-preview", description="Veo model")

    @field_validator("prompt", "negative_prompt", "style", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("aspect_ratio")
    @classmethod
    def validate_aspect_ratio(cls, v: str) -> str:
        return _validate_aspect_ratio(v)

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        return _validate_veo_duration(v)


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
    
    # Intent inference for RAG context
    intent = with_intent(request)
    
    user_id = user.get("id", "anonymous")

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
