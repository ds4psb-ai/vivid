"""
VEO Dimension Endpoints - Video Generation.

- VEO Generate: Generate video using Veo 3.1
- VEO Generate Stream: SSE streaming version with progress

Security:
- XSS sanitization for style and negative_prompt fields
- Veo model whitelist validation

2026 Best Practices:
- Veo 3.1: Native audio, 60s max, 1080p, multi-image consistency (Oct 2025)
- Kling 2.6: Native audio, 2-min duration, high-action scenes
- Sora 2: Social integration, narrative coherence
- Image-to-Video workflow: Character consistency via reference images
- Multi-platform approach: Use 2-3 platforms based on project needs
- RAG Protocol v2: trace_id, evidence_refs (List[str]), confidence
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid as uuid_lib
from enum import Enum
from typing import Dict, List

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
from ._video_base import sanitize_video_text
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
# 2026 Video Generation Platform Capabilities
# ============================================================================

class VideoGenerationPlatform(str, Enum):
    """Supported video generation platforms (2026)."""
    VEO = "veo"  # Google Veo 3.1
    KLING = "kling"  # Kling 2.6 (native audio)
    SORA = "sora"  # OpenAI Sora 2
    HAILUO = "hailuo"  # Hailuo T2V-01
    SEEDANCE = "seedance"  # Seedance 1.5 Pro (budget)
    RUNWAY = "runway"  # Runway Gen-4


class VideoOutputQuality(str, Enum):
    """Video output quality levels (2026 standards)."""
    SD = "sd"  # 480p
    HD = "hd"  # 720p
    FHD = "fhd"  # 1080p (most common)
    UHD = "uhd"  # 4K (Runway Gen-4)


class AudioIntegrationMode(str, Enum):
    """Audio integration modes (2026 trend: native audio)."""
    NONE = "none"  # No audio
    NATIVE = "native"  # Platform-native audio generation
    SYNC = "sync"  # Synced audio from external source
    DIALOGUE = "dialogue"  # Lip-synced dialogue (Kling 2.6)


class Veo31Capabilities(BaseModel):
    """Veo 3.1 (Oct 2025) platform capabilities.

    Reference: Native audio, multi-image consistency, 60s max, 1080p
    Pricing: $0.15-0.40/sec
    """
    max_duration_seconds: int = Field(60, description="60-second max")
    resolution: VideoOutputQuality = Field(VideoOutputQuality.FHD, description="1080p FHD")
    supports_native_audio: bool = Field(True, description="Native audio generation")
    supports_multi_image: bool = Field(True, description="Multi-image consistency")
    supports_camera_control: bool = Field(True, description="Camera control (Oct 2025)")
    pricing_per_second: float = Field(0.25, description="Average $0.15-0.40/sec")


class Kling26Capabilities(BaseModel):
    """Kling 2.6 (Dec 2025) platform capabilities.

    Reference: Native audio + dialogue sync, 2-minute duration, high action
    Pricing: $5-11/month
    """
    max_duration_seconds: int = Field(120, description="2-minute max")
    resolution: VideoOutputQuality = Field(VideoOutputQuality.FHD, description="1080p FHD")
    supports_native_audio: bool = Field(True, description="Native audio + SFX")
    supports_dialogue_sync: bool = Field(True, description="Lip-synced dialogue")
    supports_high_action: bool = Field(True, description="High action scenes")
    frame_rate: int = Field(48, description="Up to 48 FPS")


class VideoGenerationResult(BaseModel):
    """Comprehensive video generation result (2026 pattern).

    Includes:
    - Platform-specific metadata
    - Character consistency tracking
    - RAG Protocol v2 fields
    """
    success: bool = Field(False, description="Generation success")
    video_uri: str = Field("", description="Generated video URI")
    duration_ms: int = Field(0, description="Generation time in ms")
    credit_cost: int = Field(0, description="Credits consumed")

    # Platform info
    platform: VideoGenerationPlatform = Field(
        VideoGenerationPlatform.VEO,
        description="Platform used"
    )
    output_quality: VideoOutputQuality = Field(
        VideoOutputQuality.FHD,
        description="Output quality"
    )
    audio_mode: AudioIntegrationMode = Field(
        AudioIntegrationMode.NATIVE,
        description="Audio integration mode"
    )

    # Character consistency (2026 trend)
    characters_used: List[str] = Field(
        default_factory=list,
        description="Character IDs used for consistency"
    )

    # RAG Protocol v2 fields
    trace_id: str = Field("", description="Trace ID for auditability")
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="RAG evidence references (format: 'rag:veo:style', 'config:model:veo-3.1')"
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="AI confidence score")


# ============================================================================
# Veo-specific Validation
# ============================================================================

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
    - Character Consistency integration (character_ids)
    """
    prompt: str = Field(..., min_length=1, max_length=5000, description="Video generation prompt")
    negative_prompt: str = Field("", max_length=1000, description="Negative prompt (sanitized)")
    aspect_ratio: str = Field("16:9", description="Aspect ratio")
    duration: int = Field(6, ge=4, le=8, description="Video duration (4-8 seconds)")
    style: str = Field("cinematic", max_length=100, description="Visual style (sanitized)")
    seed: int = Field(0, ge=0, description="Random seed (0 for random)")
    model: str = Field("veo-3.1-generate-preview", description="Veo model")
    character_ids: list[str] = Field(
        default=[],
        max_length=3,
        description="Character UUIDs for consistency (max 3, Veo Ingredients)"
    )

    @field_validator("prompt", mode="before")
    @classmethod
    def strip_prompt(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("negative_prompt", mode="before")
    @classmethod
    def sanitize_negative_prompt(cls, v: str) -> str:
        """Sanitize negative_prompt to prevent XSS."""
        return sanitize_video_text(v, default="")

    @field_validator("style", mode="before")
    @classmethod
    def sanitize_style(cls, v: str) -> str:
        """Sanitize style to prevent XSS."""
        return sanitize_video_text(v, default="cinematic")

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
    """Generate video with Veo 3.1 with Intent-Resolver integration.

    2026 Best Practice: Multi-platform support with RAG Protocol v2 trace fields.
    """
    user_id = user.get("id", "unknown")
    trace_id = f"veo-{uuid_lib.uuid4().hex[:12]}"

    veo_logger.info(
        f"[VEO_GENERATE] trace={trace_id} user={user_id} prompt_len={len(request.prompt)} "
        f"duration={request.duration}s aspect={request.aspect_ratio} model={request.model}"
    )

    from app.routers.intent_helpers import with_intent
    intent = with_intent(request)

    # 2026: Build evidence_refs for traceability
    evidence_refs = [
        f"rag:veo:style:{request.style}",
        f"config:model:{request.model}",
        f"config:aspect_ratio:{request.aspect_ratio}",
        f"config:duration:{request.duration}s",
    ]
    if request.character_ids:
        for char_id in request.character_ids[:3]:
            evidence_refs.append(f"db:character:{char_id}")

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
            # 2026: RAG Protocol v2 trace fields
            "trace_id": trace_id,
            "evidence_refs": evidence_refs,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={
            "prompt": request.prompt[:100],
            "style": request.style,
            "trace_id": trace_id,
        },
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
    """Generate video with Veo 3.1 with SSE progress streaming and Intent-Resolver integration.

    2026 Best Practice: Multi-platform support with RAG Protocol v2 trace fields.

    Character Consistency Integration:
    - If character_ids provided, auto-injects as Veo Ingredients
    - Uses StoryMem memory bank for best reference selection
    - Creates CharacterAppearance records on success
    """
    from app.services.veo_service import VeoConfig, VeoProgress, get_veo_service
    from app.services.character_veo_service import get_character_veo_service
    from app.fixtures.dimension_capsules import DIMENSION_CAPSULES
    from app.routers.intent_helpers import with_intent

    user_id = user.get("id", "anonymous")
    trace_id = f"veos-{uuid_lib.uuid4().hex[:12]}"
    has_characters = bool(request.character_ids)

    veo_logger.info(
        f"[VEO_STREAM] trace={trace_id} user={user_id} prompt_len={len(request.prompt)} "
        f"duration={request.duration}s aspect={request.aspect_ratio} model={request.model} "
        f"characters={len(request.character_ids) if has_characters else 0}"
    )

    # 2026: Build evidence_refs for traceability
    evidence_refs = [
        f"rag:veo:style:{request.style}",
        f"config:model:{request.model}",
        f"config:aspect_ratio:{request.aspect_ratio}",
        f"config:duration:{request.duration}s",
    ]
    if request.character_ids:
        for char_id in request.character_ids[:3]:
            evidence_refs.append(f"db:character:{char_id}")

    # Intent inference for RAG context
    intent = with_intent(request)

    # Get capsule info for credit cost
    capsule_info = next(
        (c for c in DIMENSION_CAPSULES if c.get("capsule_key") == DimensionCapsuleId.VEO_VIDEO_GENERATE.value),
        None
    )
    # credit_costs is a dict keyed by model name
    credit_costs = capsule_info.get("credit_costs", {}) if capsule_info else {}
    credit_cost = credit_costs.get(request.model, 200)

    async def event_stream():
        """SSE event generator with progress updates."""
        credits_deducted = False
        enhanced_prompt = request.prompt
        char_veo_service = get_character_veo_service() if has_characters else None
        character_ingredients = []

        try:
            # Character Consistency: Prepare ingredients if character_ids provided
            if has_characters and char_veo_service:
                try:
                    character_ingredients = await char_veo_service.prepare_character_ingredients(
                        db=db,
                        user_id=user_id,
                        character_ids=request.character_ids,
                    )
                    if character_ingredients:
                        yield f"data: {json.dumps({'type': 'progress', 'status': 'preparing_characters', 'message': f'캐릭터 준비 중: {len(character_ingredients)}명'})}\n\n"
                except Exception as e:
                    logger.warning(f"[VEO Stream] Character preparation failed: {e}")

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

            # Enhance prompt with character names
            if character_ingredients:
                char_names = [c.character_name for c in character_ingredients]
                prompt_lower = enhanced_prompt.lower()
                unmentioned = [n for n in char_names if n.lower() not in prompt_lower]
                if unmentioned:
                    if len(unmentioned) == 1:
                        enhanced_prompt = f"[Character: {unmentioned[0]}] {enhanced_prompt}"
                    else:
                        enhanced_prompt = f"[Characters: {', '.join(unmentioned)}] {enhanced_prompt}"

            # Check credits if not BYOK
            if not byok_key:
                user_credits = await get_or_create_user_credits(db, user_id)
                if user_credits.balance < credit_cost:
                    yield f"data: {json.dumps({'type': 'error', 'error': '크레딧이 부족합니다.', 'code': 'INSUFFICIENT_CREDITS', 'required': credit_cost, 'available': user_credits.balance})}\n\n"
                    return

                # Deduct credits upfront
                try:
                    await deduct_credits(
                        db=db,
                        user_id=user_id,
                        amount=credit_cost,
                        description=f"Veo video generation: {request.prompt[:50]}...",
                        meta={"capsule_id": DimensionCapsuleId.VEO_VIDEO_GENERATE.value}
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
                # Character Consistency: Create appearance records on success
                appearances_created = []
                if character_ingredients and char_veo_service:
                    try:
                        from app.models_character import CharacterAppearance
                        import uuid as uuid_module
                        for ingredient in character_ingredients:
                            appearance = CharacterAppearance(
                                id=uuid_module.uuid4(),
                                character_id=uuid_module.UUID(ingredient.character_id),
                                shot_id=None,
                                scene_description=enhanced_prompt[:500],
                                generated_frame_url=result.video_uri,
                            )
                            db.add(appearance)
                            appearances_created.append(str(appearance.id))
                        await db.commit()
                        logger.info(f"[VEO Stream] Created {len(appearances_created)} character appearances")
                    except Exception as e:
                        logger.warning(f"[VEO Stream] Failed to create appearances: {e}")

                # Build response with character info and 2026 trace fields
                response_data = {
                    'type': 'complete',
                    'success': True,
                    'video_uri': result.video_uri,
                    'duration_ms': result.duration_ms,
                    'credit_cost': result.credit_cost,
                    'metadata': result.metadata,
                    # 2026: RAG Protocol v2 trace fields
                    'trace_id': trace_id,
                    'evidence_refs': evidence_refs,
                    'confidence': 0.9,  # High confidence for successful generation
                }
                if character_ingredients:
                    response_data['characters_used'] = [
                        {'id': c.character_id, 'name': c.character_name}
                        for c in character_ingredients
                    ]
                    response_data['appearances_created'] = appearances_created

                yield f"data: {json.dumps(response_data)}\n\n"
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
