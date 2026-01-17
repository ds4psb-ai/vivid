"""
Prompt Alchemy Endpoints - AI Video Platform Prompt Translator.

Translates scene descriptions into optimized prompts for:
- Veo 3.1: Dialogue/narration-heavy viral videos
- Kling 2.6: High-quality silent cinematic videos (recommended)
- Sora Max 2 Pro: Animation-style videos
"""
from __future__ import annotations

import html
import logging
import re
from enum import Enum
from typing import Annotated, List, Literal, Optional

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

# UQSL Strategy enum for multi-candidate generation
class UQSLStrategy(str, Enum):
    AUTO = "auto"
    DIVERSITY = "diversity"
    QUALITY = "quality"
    SPEED = "speed"


# Auteur key pattern: alphanumeric and underscore only (e.g., "kubrick", "bong_joonho")
AUTEUR_KEY_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")


# ============================================================================
# Sanitization Helpers
# ============================================================================

def _sanitize_style(value: str) -> str:
    """Sanitize style field to prevent XSS and injection attacks.

    Args:
        value: Raw style input

    Returns:
        Sanitized style string
    """
    if not value:
        return "cinematic"
    # Strip whitespace
    value = value.strip()
    # Remove HTML tags
    value = re.sub(r"<[^>]+>", "", value)
    # Escape HTML entities
    value = html.escape(value)
    # Remove script/javascript patterns
    value = re.sub(r"(?i)javascript\s*:", "", value)
    value = re.sub(r"(?i)on\w+\s*=", "", value)
    # Limit to reasonable characters
    value = re.sub(r"[^\w\s가-힣\-_.,]", "", value)
    return value[:100] or "cinematic"


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
            "alphanumeric characters and underscores (e.g., 'kubrick', 'bong_joonho')"
        )
    return value


# ============================================================================
# Supported Platforms
# ============================================================================

PLATFORM_INFO = {
    "veo_31": {
        "name": "Google Veo 3.1",
        "use_case": "대화/나레이션 중심 바이럴 영상",
        "max_duration": 8,
        "native_audio": True,
    },
    "kling_26": {
        "name": "Kling 2.6",
        "use_case": "고화질 음성 없는 영상 (특히 추천)",
        "max_duration": 120,
        "native_audio": False,
        "recommended": True,
    },
    "sora_max_2pro": {
        "name": "Sora Max 2 Pro",
        "use_case": "애니메이션 스타일 영상",
        "max_duration": 20,
        "native_audio": True,
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
        examples=["kubrick", "bong_joonho", "nolan"],
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
        return _sanitize_style(v)

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
        return _sanitize_style(v)

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
