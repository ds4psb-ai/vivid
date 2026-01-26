"""
Prompt Alchemy Endpoints - AI Video Platform Prompt Translator.

Translates scene descriptions into optimized prompts for:
- Veo 3.1: Dialogue/narration-heavy viral videos (Native Audio)
- Kling 2.6: High-quality silent cinematic videos (recommended, Lip Sync)
- Sora Max 2 Pro: Animation-style videos (Physics simulation)

2026 Best Practices Applied:
- Six-Layer Framework for prompt engineering
- Native Audio integration patterns (dialogue, ambient, SFX)
- Beat timestamp format for lip sync
- Platform-specific negative prompts
- trace_id and evidence_refs for RAG Protocol v2
"""
from __future__ import annotations

import logging
import re
import uuid
from enum import Enum
from typing import Annotated, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from ._base import (
    get_db,
    get_current_user,
    get_byok_key,
    _execute_dimension_tool,
    _execute_dimension_tool_stream,
    _execute_dimension_tool_multi,
    _execute_dimension_tool_multi_stream,
    _validate_language,
    _validate_model,
    _strip_string,
    sanitize_generic_text,
    DimensionResponse,
    DimensionErrorResponse,
    DimensionCapsuleId,
    ALLOWED_LANGUAGES,
    MAX_DESCRIPTION_LENGTH,
    get_sse_headers,
    Optional,
    AsyncSession,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Constants & Enums
# ============================================================================

SUPPORTED_PLATFORMS = ["veo_31", "kling_26", "sora_max_2pro"]


# ============================================================================
# 2026 Best Practices: Enums and Models
# ============================================================================

class SixLayerDimension(str, Enum):
    """Six-Layer Framework for AI Video Prompt Engineering (2026).

    Based on professional cinematography hierarchy for generative models.
    Reference: vidwave.ai, Medium @creativeaininja
    """
    SUBJECT_ACTION_EMOTION = "subject_action_emotion"  # Layer 1: Who, What, Feeling
    SHOT_FRAMING = "shot_framing"  # Layer 2: Shot type, composition
    CAMERA_MOVEMENT = "camera_movement"  # Layer 3: Dolly, pan, tilt, tracking
    LIGHTING_ENVIRONMENT = "lighting_environment"  # Layer 4: Light, time, place
    STYLE_AESTHETIC = "style_aesthetic"  # Layer 5: Visual style, references
    AUDIO_DIALOGUE = "audio_dialogue"  # Layer 6: Native audio, SFX, dialogue


class AudioIntegrationType(str, Enum):
    """Audio integration strategy for AI video generation (2026).

    Determines how audio is generated/synced with video.
    """
    NATIVE = "native"  # Audio generated with video (Veo 3.1, Kling 2.6)
    SEPARATE = "separate"  # Audio generated separately (Suno, ElevenLabs)
    HYBRID = "hybrid"  # Native + post-enhancement
    NONE = "none"  # No audio (silent video)


class MotionIntensity(str, Enum):
    """Motion intensity level for shot classification (2026).

    Used for tool selection heuristics.
    """
    STATIC = "static"  # No movement, locked camera
    LOW = "low"  # Subtle movement, breathing room
    MEDIUM = "medium"  # Normal action, moderate camera work
    HIGH = "high"  # Fast action, dynamic camera
    EXTREME = "extreme"  # Chase, fight, intense action


class CameraMovement(str, Enum):
    """Standard camera movements for prompt engineering (2026).

    Based on film industry terminology recognized by AI models.
    """
    STATIC = "static"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    CRANE_UP = "crane_up"
    CRANE_DOWN = "crane_down"
    TRACKING = "tracking"
    STEADICAM = "steadicam"
    HANDHELD = "handheld"
    ORBIT = "orbit"
    WHIP_PAN = "whip_pan"


class PromptQualityDimension(str, Enum):
    """Prompt quality evaluation dimensions (2026).

    Used for automatic prompt quality scoring.
    """
    SPECIFICITY = "specificity"  # How specific is the description
    CLARITY = "clarity"  # Is the instruction clear
    MOTION_GUIDANCE = "motion_guidance"  # Camera/subject motion clarity
    AUDIO_CUES = "audio_cues"  # Native audio instructions
    STYLE_COHERENCE = "style_coherence"  # Visual style consistency
    TEMPORAL_STRUCTURE = "temporal_structure"  # Beat/timeline structure


class Veo31Capabilities(BaseModel):
    """Google Veo 3.1 capabilities (Oct 2025 release)."""
    max_duration_seconds: int = Field(default=8, description="Max duration (8s default, 120s extended)")
    max_resolution: str = Field(default="4K", description="Maximum resolution")
    native_audio: bool = Field(default=True, description="Supports native audio generation")
    lip_sync: bool = Field(default=True, description="Supports lip synchronization")
    dialogue_format: str = Field(
        default="[Dialogue]: Speaker (Tone): \"text\"",
        description="Dialogue prompt format"
    )
    generation_time_fast: str = Field(default="30-90s", description="Fast mode generation time")
    primary_strength: str = Field(default="emotional_realism", description="Primary strength")


class Kling26Capabilities(BaseModel):
    """Kling 2.6 capabilities (Dec 2025 release)."""
    max_duration_seconds: int = Field(default=120, description="Max 2-minute duration")
    max_resolution: str = Field(default="1080p", description="Maximum resolution")
    native_audio: bool = Field(default=True, description="Supports native audio")
    lip_sync: bool = Field(default=True, description="Best-in-class lip sync")
    beat_timestamp_format: str = Field(
        default="Beat 0-4s: [Action], Beat 5-8s: [Dialogue]",
        description="Beat timestamp prompt format"
    )
    dialogue_format: str = Field(
        default="Beat 5-8s: Close up. Character (Tone): \"text\"",
        description="Dialogue with beat timestamps"
    )
    generation_time: str = Field(default="2-5min", description="Generation time")
    primary_strength: str = Field(default="photorealistic_humans", description="Primary strength")


class SoraMax2ProCapabilities(BaseModel):
    """OpenAI Sora Max 2 Pro capabilities (2025 release)."""
    max_duration_seconds: int = Field(default=60, description="Max 60s (Pro tier)")
    max_resolution: str = Field(default="4K", description="Maximum resolution")
    native_audio: bool = Field(default=True, description="Supports native audio")
    lip_sync: bool = Field(default=True, description="Supports dialogue sync")
    generation_time: str = Field(default="5-15min", description="Generation time")
    primary_strength: str = Field(default="physics_accuracy", description="Primary strength: physics simulation")


class NativeAudioPromptTemplate(BaseModel):
    """Native audio prompt template for 2026 platforms."""
    platform: str = Field(..., description="Target platform")
    visual_block: str = Field(..., description="Visual description block")
    dialogue_block: Optional[str] = Field(None, description="Dialogue with speaker tags")
    ambient_block: Optional[str] = Field(None, description="Ambient sound description")
    mood_block: Optional[str] = Field(None, description="Emotional mood/tone")
    sfx_block: Optional[str] = Field(None, description="Sound effects description")
    no_subtitles: bool = Field(default=True, description="Add 'No subtitles' instruction")


class PromptOptimizationResult(BaseModel):
    """Result of prompt optimization with RAG Protocol v2 fields."""
    trace_id: str = Field(default="", description="Unique trace identifier")
    optimized_prompt: str = Field(..., description="Optimized prompt text")
    platform: str = Field(..., description="Target platform")
    quality_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Quality scores by dimension"
    )
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall quality score")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    audio_strategy: AudioIntegrationType = Field(
        default=AudioIntegrationType.NATIVE,
        description="Recommended audio integration"
    )
    evidence_refs: List[str] = Field(default_factory=list, description="RAG evidence references")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score")


# UQSL Strategy enum for multi-candidate generation
class UQSLStrategy(str, Enum):
    AUTO = "auto"
    DIVERSITY = "diversity"
    QUALITY = "quality"
    SPEED = "speed"


# AI Auteur key pattern: alphanumeric and underscore only (e.g., "prism", "kang")
AUTEUR_KEY_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")


def _validate_auteur_key(value: Optional[str]) -> Optional[str]:
    """Validate auteur_key format.

    Must be:
    - Start with a letter
    - Contain only alphanumeric and underscore characters
    - Max 50 characters

    Args:
        value: Raw auteur key

    Returns:
        Validated auteur key or None

    Raises:
        ValueError: If format is invalid
    """
    if value is None or value == "":
        return None
    value = value.strip().lower()
    if len(value) > 50:
        raise ValueError("auteur_key must be 50 characters or less")
    if not AUTEUR_KEY_PATTERN.match(value):
        raise ValueError(
            "auteur_key must start with a letter and contain only "
            "alphanumeric characters and underscores (e.g., 'prism', 'kang')"
        )
    return value


# ============================================================================
# Supported Platforms
# ============================================================================

PLATFORM_INFO = {
    "veo_31": {
        "name": "Google Veo 3.1",
        "use_case": "대화/나레이션 중심 바이럴 영상",
        "max_duration": 120,  # Extended from 8s
        "max_resolution": "4K",
        "native_audio": True,
        "lip_sync": True,
        "generation_time": "30-90s (fast)",
        "primary_strength": "emotional_realism",
        "prompt_tips": [
            "대화는 3-5초로 짧게 유지",
            "톤 지시어 필수: (whispering), (excited), (calm)",
            "'No subtitles' 항상 추가",
            "[Dialogue]: Speaker (Tone): \"text\" 형식 사용",
        ],
        "negative_prompts": ["No subtitles", "No text overlay", "No watermark"],
        "audio_format": "[Dialogue]: Speaker (Tone): \"text\"\n[Ambient]: description\n[Mood]: tone",
    },
    "kling_26": {
        "name": "Kling 2.6",
        "use_case": "고화질 실사 영상 + 립싱크 (추천)",
        "max_duration": 120,
        "max_resolution": "1080p",
        "native_audio": True,  # Updated: Now supports native audio
        "lip_sync": True,  # Best-in-class lip sync
        "generation_time": "2-5min",
        "primary_strength": "photorealistic_humans",
        "recommended": True,
        "prompt_tips": [
            "Beat timestamp 형식 사용: Beat 0-4s: [Action]",
            "카메라 움직임 구체적 지정",
            "2분까지 가능 - 긴 씬에 최적",
            "물리적 모션에 강점",
        ],
        "negative_prompts": ["No background music", "No mumble", "No overlapping speech", "No distortion"],
        "audio_format": "Beat 5-8s: Close up. Character (Tone): \"text\"",
    },
    "sora_max_2pro": {
        "name": "Sora Max 2 Pro",
        "use_case": "애니메이션 스타일 + 물리 시뮬레이션",
        "max_duration": 60,  # Updated: 60s Pro tier
        "max_resolution": "4K",
        "native_audio": True,
        "lip_sync": True,
        "generation_time": "5-15min",
        "primary_strength": "physics_accuracy",
        "prompt_tips": [
            "스타일 레퍼런스 명시 ('Ghibli', 'Pixar', 'Anime')",
            "캐릭터 묘사 일관되게 반복",
            "감정/분위기 키워드 중요",
            "Force-reaction 구문으로 물리 동작 묘사",
        ],
        "negative_prompts": ["No text overlay", "No watermark", "No lens flare"],
        "audio_format": "[Visual Description]\n+ [SFX descriptions]\n+ [Dialogue if any]",
    },
}


# ============================================================================
# Request Models
# ============================================================================

class PromptTranslateRequest(BaseModel):
    """Request model for Prompt Alchemy translation.

    Includes comprehensive validation for security and data integrity:
    - scene_description: Min 10, max 3000 chars
    - target_platform: Must be one of veo_31, kling_26, sora_max_2pro
    - style: Sanitized for XSS/injection
    - auteur_key: Alphanumeric + underscore only
    - duration: 1-120 seconds
    """
    scene_description: str = Field(
        ...,
        min_length=10,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="씬 설명 또는 스토리보드 텍스트",
        examples=["밤하늘 아래 두 연인이 걷고 있다. 달빛이 그들의 얼굴을 비춘다."],
    )
    target_platform: Optional[str] = Field(
        None,
        description="대상 플랫폼: veo_31, kling_26, sora_max_2pro (미지정시 자동 선택)",
        examples=["kling_26"],
    )
    style: str = Field(
        "cinematic",
        max_length=100,
        description="비주얼 스타일 (sanitized)",
        examples=["cinematic", "noir", "anime"],
    )
    auteur_key: Optional[str] = Field(
        None,
        max_length=50,
        description="거장 키 (RAG 활성화). 알파벳과 언더스코어만 허용.",
        examples=["prism", "kang", "epoch"],
    )
    duration: Optional[int] = Field(
        None,
        ge=1,
        le=120,
        description="목표 영상 길이 (초)",
    )
    language: str = Field("ko", description="출력 언어")
    model: str = Field("gemini-3-flash-preview", description="AI 모델")

    @field_validator("scene_description", mode="before")
    @classmethod
    def strip_description(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("target_platform")
    @classmethod
    def validate_platform(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in SUPPORTED_PLATFORMS:
            raise ValueError(f"지원하지 않는 플랫폼: {v}. 지원: {SUPPORTED_PLATFORMS}")
        return v

    @field_validator("style", mode="before")
    @classmethod
    def sanitize_style(cls, v: str) -> str:
        """Sanitize style to prevent XSS attacks."""
        return sanitize_generic_text(v, default="cinematic")

    @field_validator("auteur_key")
    @classmethod
    def validate_auteur_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate auteur_key format (alphanumeric + underscore)."""
        return _validate_auteur_key(v)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class BatchTranslateRequest(BaseModel):
    """Request for batch translation to multiple platforms.

    Translates a single scene description to all specified platforms simultaneously.
    """
    scene_description: str = Field(
        ...,
        min_length=10,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="씬 설명",
        examples=["밤하늘 아래 두 연인이 걷고 있다. 달빛이 그들의 얼굴을 비춘다."],
    )
    target_platforms: List[str] = Field(
        default_factory=lambda: SUPPORTED_PLATFORMS.copy(),
        description="대상 플랫폼 목록",
        examples=[["veo_31", "kling_26", "sora_max_2pro"]],
    )
    style: str = Field("cinematic", max_length=100)
    auteur_key: Optional[str] = Field(None, max_length=50)
    language: str = Field("ko")
    model: str = Field("gemini-3-flash-preview")

    @field_validator("scene_description", mode="before")
    @classmethod
    def strip_description(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("target_platforms")
    @classmethod
    def validate_platforms(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("최소 하나의 플랫폼을 지정해야 합니다")
        if len(v) > len(SUPPORTED_PLATFORMS):
            raise ValueError(f"최대 {len(SUPPORTED_PLATFORMS)}개 플랫폼만 지정 가능합니다")
        invalid = [p for p in v if p not in SUPPORTED_PLATFORMS]
        if invalid:
            raise ValueError(f"지원하지 않는 플랫폼: {invalid}")
        # Remove duplicates while preserving order
        return list(dict.fromkeys(v))

    @field_validator("style", mode="before")
    @classmethod
    def sanitize_style(cls, v: str) -> str:
        return sanitize_generic_text(v, default="cinematic")

    @field_validator("auteur_key")
    @classmethod
    def validate_auteur_key(cls, v: Optional[str]) -> Optional[str]:
        return _validate_auteur_key(v)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/prompt/translate",
    response_model=DimensionResponse,
    responses={
        402: {"model": DimensionErrorResponse},
        422: {"model": DimensionErrorResponse},
    },
    summary="프롬프트 변환",
    description="씬 설명을 AI 비디오 플랫폼별 최적화 프롬프트로 변환합니다.",
    tags=["Prompt Alchemy"],
)
async def translate_prompt(
    request: PromptTranslateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Translate scene description to platform-specific AI video prompt."""
    user_id = user.get("id", "unknown")
    logger.info(
        f"[PROMPT_TRANSLATE] user={user_id} platform={request.target_platform or 'auto'} "
        f"style={request.style} auteur={request.auteur_key} desc_len={len(request.scene_description)}"
    )

    inputs = {
        "scene_description": request.scene_description,
        "target_platform": request.target_platform,
        "style": request.style,
        "auteur_key": request.auteur_key,
        "duration": request.duration,
        "language": request.language,
    }

    params = {
        "model": request.model,
        "auto_select": request.target_platform is None,
    }

    inputs_summary = {
        "description_length": len(request.scene_description),
        "target_platform": request.target_platform or "auto",
        "style": request.style,
        "auteur_key": request.auteur_key,
    }

    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.PROMPT_TRANSLATE,
        tool_key="prompt.alchemy.translate",
        inputs=inputs,
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary=inputs_summary,
        params=params,
    )


@router.post(
    "/prompt/translate/stream",
    summary="프롬프트 변환 (스트리밍)",
    description="SSE 스트리밍으로 씬 설명을 플랫폼별 프롬프트로 변환합니다.",
    tags=["Prompt Alchemy"],
)
async def translate_prompt_stream(
    request: PromptTranslateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Translate scene description with SSE streaming."""
    inputs = {
        "scene_description": request.scene_description,
        "target_platform": request.target_platform,
        "style": request.style,
        "auteur_key": request.auteur_key,
        "duration": request.duration,
        "language": request.language,
    }

    params = {
        "model": request.model,
        "auto_select": request.target_platform is None,
    }

    inputs_summary = {
        "description_length": len(request.scene_description),
        "target_platform": request.target_platform or "auto",
    }

    async def stream_generator():
        async for event in _execute_dimension_tool_stream(
            capsule_id=DimensionCapsuleId.PROMPT_TRANSLATE,
            tool_key="prompt.alchemy.translate",
            operation_name="프롬프트 연금술",
            inputs=inputs,
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary=inputs_summary,
            params=params,
        ):
            yield event

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


@router.post(
    "/prompt/translate/multi",
    summary="프롬프트 다중 변환 (UQSL)",
    description="UQSL을 통해 여러 후보 프롬프트를 생성하고 최적의 것을 추천합니다.",
    tags=["Prompt Alchemy"],
)
async def translate_prompt_multi(
    request: PromptTranslateRequest,
    n_candidates: Annotated[
        int,
        Query(
            ge=1,
            le=5,
            description="생성할 후보 프롬프트 수 (1-5)",
            examples=[3],
        ),
    ] = 3,
    strategy: Annotated[
        UQSLStrategy,
        Query(
            description="UQSL 전략: auto(자동), diversity(다양성), quality(품질), speed(속도)",
            examples=["auto"],
        ),
    ] = UQSLStrategy.AUTO,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
):
    """Generate multiple prompt candidates with quality scoring.

    Args:
        request: Translation request with scene description
        n_candidates: Number of candidates to generate (1-5, default: 3)
        strategy: UQSL generation strategy
            - auto: Automatically balance quality and speed
            - diversity: Maximize variety in generated prompts
            - quality: Prioritize quality over speed
            - speed: Prioritize speed over quality

    Returns:
        Multiple prompt candidates with quality scores and recommendations
    """
    logger.info(
        f"[PROMPT_MULTI] Generating {n_candidates} candidates with {strategy.value} strategy"
    )

    inputs = {
        "scene_description": request.scene_description,
        "target_platform": request.target_platform,
        "style": request.style,
        "auteur_key": request.auteur_key,
        "duration": request.duration,
        "language": request.language,
    }

    params = {
        "model": request.model,
        "auto_select": request.target_platform is None,
    }

    inputs_summary = {
        "description_length": len(request.scene_description),
        "target_platform": request.target_platform or "auto",
    }

    return await _execute_dimension_tool_multi(
        capsule_id=DimensionCapsuleId.PROMPT_TRANSLATE,
        tool_key="prompt.alchemy.translate",
        inputs=inputs,
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary=inputs_summary,
        n_candidates=n_candidates,
        strategy=strategy.value,  # Convert enum to string
        params=params,
    )


@router.post(
    "/prompt/translate/batch",
    summary="배치 프롬프트 변환",
    description="하나의 씬 설명을 여러 플랫폼용 프롬프트로 동시 변환합니다.",
    tags=["Prompt Alchemy"],
)
async def translate_prompt_batch(
    request: BatchTranslateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
):
    """Translate scene description to multiple platform prompts at once."""
    import asyncio

    user_id = user.get("id", "unknown")
    logger.info(
        f"[PROMPT_BATCH] user={user_id} platforms={request.target_platforms} "
        f"desc_len={len(request.scene_description)}"
    )

    async def translate_for_platform(platform: str):
        inputs = {
            "scene_description": request.scene_description,
            "target_platform": platform,
            "style": request.style,
            "auteur_key": request.auteur_key,
            "language": request.language,
        }

        params = {
            "model": request.model,
            "auto_select": False,
        }

        inputs_summary = {
            "description_length": len(request.scene_description),
            "target_platform": platform,
        }

        result = await _execute_dimension_tool(
            capsule_id=DimensionCapsuleId.PROMPT_TRANSLATE,
            tool_key="prompt.alchemy.translate",
            inputs=inputs,
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary=inputs_summary,
            params=params,
        )

        return {
            "platform": platform,
            "platform_name": PLATFORM_INFO[platform]["name"],
            "result": result,
        }

    # Execute all translations in parallel
    tasks = [translate_for_platform(p) for p in request.target_platforms]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    translations = []
    errors = []

    for idx, r in enumerate(results):
        if isinstance(r, Exception):
            platform = request.target_platforms[idx]
            error_msg = str(r)
            logger.warning(f"[PROMPT_BATCH] Failed for platform={platform}: {error_msg}")
            errors.append({"platform": platform, "error": error_msg})
        else:
            translations.append(r)

    logger.info(
        f"[PROMPT_BATCH] Complete: success={len(translations)}/{len(request.target_platforms)}"
    )

    return {
        "success": len(translations) > 0,
        "translations": translations,
        "errors": errors if errors else None,
        "total_platforms": len(request.target_platforms),
        "successful_platforms": len(translations),
    }


@router.get(
    "/prompt/platforms",
    summary="지원 플랫폼 목록",
    description="Prompt Alchemy가 지원하는 AI 비디오 생성 플랫폼 정보를 반환합니다.",
    tags=["Prompt Alchemy"],
)
async def get_supported_platforms():
    """Get list of supported AI video platforms with details."""
    return {
        "platforms": PLATFORM_INFO,
        "supported_platforms": SUPPORTED_PLATFORMS,
        "default_platform": "kling_26",
        "auto_selection_rules": {
            "dialogue_or_narration": "veo_31",
            "animation_style": "sora_max_2pro",
            "default": "kling_26",
        },
    }


@router.get(
    "/prompt/info",
    summary="프롬프트 연금술 정보",
    description="Prompt Alchemy 앱 정보를 반환합니다.",
    tags=["Prompt Alchemy"],
)
async def get_prompt_alchemy_info():
    """Get Prompt Alchemy app information."""
    return {
        "app_id": "prompt",
        "name_ko": "프롬프트 연금술",
        "name_en": "Prompt Alchemy",
        "icon": "⚗️",
        "description": "씬 설명을 AI 비디오 플랫폼별 최적화 프롬프트로 변환합니다.",
        "version": "1.0.0",
        "capabilities": [
            "single_translate",
            "batch_translate",
            "uqsl_multi_generate",
            "sse_streaming",
            "auteur_rag",
        ],
        "endpoints": {
            "translate": "/api/dimension/prompt/translate",
            "translate_stream": "/api/dimension/prompt/translate/stream",
            "translate_multi": "/api/dimension/prompt/translate/multi",
            "batch": "/api/dimension/prompt/translate/batch",
            "platforms": "/api/dimension/prompt/platforms",
        },
        "credit_cost": 5,
    }
