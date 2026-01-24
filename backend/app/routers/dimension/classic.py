"""
Classic Dimension Endpoints - 1D, 2D, 3D, 4D.

- 1D Origin: Veo Prompt Generation
- 2D Blueprint: Storyboard Creation
- 3D Ambience: Image Prompt Generation
- 4D Moment: Reference Analysis (Enhanced with 2026 Expert Workflow)

Security:
- XSS sanitization for style/mood fields
- Enum validation for analysis_depth/output_format/strategy
- Focus areas whitelist validation

4D Hardening (2026):
- Style extraction from reference images
- Video frame-by-frame analysis
- Shot list generation for recreation
- Moodboard generation
"""
from __future__ import annotations

import base64
import logging
from enum import Enum
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

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
    _validate_aspect_ratio,
    _strip_string,
    sanitize_generic_text,
    DimensionResponse,
    DimensionErrorResponse,
    DimensionCapsuleId,
    ALLOWED_LANGUAGES,
    MAX_TOPIC_LENGTH,
    MAX_CONCEPT_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MIN_SCENE_COUNT,
    MAX_SCENE_COUNT,
    get_sse_headers,
    Optional,
    safe_error_detail,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Constants & Enums
# ============================================================================

class AnalysisDepth(str, Enum):
    """4D analysis depth levels."""
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class OutputFormat(str, Enum):
    """4D output format options."""
    STRUCTURED = "structured"
    NARRATIVE = "narrative"
    BULLET = "bullet"


class UQSLStrategy(str, Enum):
    """UQSL selection strategy."""
    AUTO = "auto"
    QUALITY = "quality"
    HITL = "hitl"


ALLOWED_FOCUS_AREAS = frozenset([
    "cinematography", "editing", "color", "sound", "lighting",
    "composition", "movement", "pacing", "narrative", "mood",
    "performance", "dialogue", "vfx", "production_design",
])

DEFAULT_FOCUS_AREAS = ["cinematography", "editing", "color", "sound"]


def _validate_analysis_depth(value: str) -> str:
    """Validate analysis_depth is one of allowed values.

    Args:
        value: Raw analysis depth

    Returns:
        Validated analysis depth

    Raises:
        ValueError: If not in allowed values
    """
    value = value.strip().lower()
    try:
        return AnalysisDepth(value).value
    except ValueError:
        allowed = [d.value for d in AnalysisDepth]
        raise ValueError(f"Invalid analysis_depth: {value}. Allowed: {allowed}")


def _validate_output_format(value: str) -> str:
    """Validate output_format is one of allowed values.

    Args:
        value: Raw output format

    Returns:
        Validated output format

    Raises:
        ValueError: If not in allowed values
    """
    value = value.strip().lower()
    try:
        return OutputFormat(value).value
    except ValueError:
        allowed = [f.value for f in OutputFormat]
        raise ValueError(f"Invalid output_format: {value}. Allowed: {allowed}")


def _validate_focus_areas(areas: List[str]) -> List[str]:
    """Validate and sanitize focus_areas list.

    Args:
        areas: Raw focus areas list

    Returns:
        Validated focus areas list

    Raises:
        ValueError: If invalid areas found
    """
    if not areas:
        return DEFAULT_FOCUS_AREAS.copy()

    # Normalize and validate
    normalized = []
    invalid = []
    for area in areas:
        clean = area.strip().lower().replace(" ", "_")
        if clean in ALLOWED_FOCUS_AREAS:
            if clean not in normalized:  # Deduplicate
                normalized.append(clean)
        else:
            invalid.append(area)

    if invalid:
        raise ValueError(
            f"Invalid focus_areas: {invalid}. Allowed: {sorted(ALLOWED_FOCUS_AREAS)}"
        )

    return normalized or DEFAULT_FOCUS_AREAS.copy()


def _validate_strategy(value: str) -> str:
    """Validate UQSL strategy is one of allowed values.

    Args:
        value: Raw strategy

    Returns:
        Validated strategy

    Raises:
        ValueError: If not in allowed values
    """
    value = value.strip().lower()
    try:
        return UQSLStrategy(value).value
    except ValueError:
        allowed = [s.value for s in UQSLStrategy]
        raise ValueError(f"Invalid strategy: {value}. Allowed: {allowed}")


# ============================================================================
# Request Models
# ============================================================================

class PromptGenerateRequest(BaseModel):
    """Request model for 1D Origin prompt generation.

    Includes XSS sanitization for style/mood fields.
    """
    topic: str = Field(..., min_length=1, max_length=MAX_TOPIC_LENGTH, description="Video topic or concept")
    style: str = Field("cinematic", max_length=100, description="Visual style (sanitized)")
    mood: str = Field("neutral", max_length=100, description="Mood or atmosphere (sanitized)")
    duration: int = Field(6, ge=4, le=8, description="Video duration in seconds")
    language: str = Field("ko", description="Output language")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("topic", mode="before")
    @classmethod
    def strip_topic(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("style", mode="before")
    @classmethod
    def sanitize_style(cls, v: str) -> str:
        """Sanitize style to prevent XSS attacks."""
        return sanitize_generic_text(v, default="cinematic")

    @field_validator("mood", mode="before")
    @classmethod
    def sanitize_mood(cls, v: str) -> str:
        """Sanitize mood to prevent XSS attacks."""
        return sanitize_generic_text(v, default="neutral")

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class StoryboardCreateRequest(BaseModel):
    """Request model for 2D Blueprint storyboard creation."""
    concept: str = Field(..., min_length=1, max_length=MAX_CONCEPT_LENGTH, description="Story concept")
    prompt: str = Field("", max_length=500, description="Additional storyboard guidance")
    scene_count: int = Field(4, ge=MIN_SCENE_COUNT, le=MAX_SCENE_COUNT, description="Number of scenes")
    language: str = Field("ko", description="Output language")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("concept", mode="before")
    @classmethod
    def strip_concept(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class ImageGenerateRequest(BaseModel):
    """Request model for 3D Ambience image prompt generation.

    Includes XSS sanitization for style field.
    """
    description: str = Field(..., min_length=1, max_length=MAX_DESCRIPTION_LENGTH, description="Image description")
    style: str = Field("photorealistic", max_length=100, description="Image style (sanitized)")
    aspect_ratio: str = Field("16:9", description="Aspect ratio")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("style", mode="before")
    @classmethod
    def sanitize_style(cls, v: str) -> str:
        """Sanitize style to prevent XSS attacks."""
        return sanitize_generic_text(v, default="photorealistic")

    @field_validator("aspect_ratio")
    @classmethod
    def validate_aspect_ratio(cls, v: str) -> str:
        return _validate_aspect_ratio(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class ReferenceAnalyzeRequest(BaseModel):
    """Request model for 4D Moment reference analysis.

    Includes:
    - Enum validation for analysis_depth and output_format
    - Whitelist validation for focus_areas
    """
    video_description: str = Field(..., min_length=1, max_length=MAX_DESCRIPTION_LENGTH, description="Video to analyze")
    focus_areas: List[str] = Field(
        default_factory=lambda: DEFAULT_FOCUS_AREAS.copy(),
        description=f"Areas to focus analysis on. Allowed: {sorted(ALLOWED_FOCUS_AREAS)}"
    )
    analysis_depth: str = Field("standard", description="Analysis depth: quick, standard, deep")
    output_format: str = Field("structured", description="Output format: structured, narrative, bullet")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("video_description", mode="before")
    @classmethod
    def strip_description(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("focus_areas")
    @classmethod
    def validate_focus_areas(cls, v: List[str]) -> List[str]:
        """Validate focus_areas against whitelist."""
        return _validate_focus_areas(v)

    @field_validator("analysis_depth")
    @classmethod
    def validate_analysis_depth(cls, v: str) -> str:
        """Validate analysis_depth is one of allowed enum values."""
        return _validate_analysis_depth(v)

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        """Validate output_format is one of allowed enum values."""
        return _validate_output_format(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


# ============================================================================
# 1D Origin - Prompt Generation
# ============================================================================

@router.post(
    "/1d/generate",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="1D Origin: Generate Veo Prompt",
    description="Generate a Veo 3.1 video prompt from topic, style, and mood.",
    tags=["Dimension 1D"],
)
async def generate_1d_prompt(
    request: PromptGenerateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Generate Veo video prompt (1D Origin) with Intent-Resolver integration."""
    user_id = user.get("id", "unknown")
    logger.info(
        f"[1D_GENERATE] user={user_id} topic_len={len(request.topic)} "
        f"style={request.style} mood={request.mood} duration={request.duration}s"
    )

    from app.routers.intent_helpers import with_intent
    intent = with_intent(request)

    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.PROMPT_GENERATE,
        tool_key="generate_veo_prompt",
        inputs={
            "topic": request.topic,
            "style": request.style,
            "mood": request.mood,
            "duration": f"{request.duration} seconds",  # Convert int to string format
            "language": request.language,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"topic": request.topic[:100], "style": request.style},
        intent=intent,
    )


@router.post(
    "/1d/generate/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="1D Origin: Generate Veo Prompt (SSE Stream)",
    description="Generate Veo prompt with real-time progress updates via SSE.",
    tags=["Dimension 1D"],
)
async def generate_1d_prompt_stream(
    request: PromptGenerateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Generate Veo video prompt with SSE streaming (1D Origin)."""
    from app.routers.intent_helpers import with_intent
    intent = with_intent(request)
    
    return StreamingResponse(
        _execute_dimension_tool_stream(
            capsule_id=DimensionCapsuleId.PROMPT_GENERATE,
            tool_key="generate_veo_prompt",
            operation_name="프롬프트 생성",
            inputs={
                "topic": request.topic,
                "style": request.style,
                "mood": request.mood,
                "duration": f"{request.duration} seconds",  # Convert int to string format
                "language": request.language,
            },
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={"topic": request.topic[:100], "style": request.style},
            intent=intent,
        ),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


# ============================================================================
# 1D Origin - UQSL Multi-Generate
# ============================================================================

class PromptMultiGenerateRequest(BaseModel):
    """Request model for 1D Origin UQSL multi-candidate generation.

    Includes:
    - XSS sanitization for style/mood fields
    - Enum validation for strategy
    """
    topic: str = Field(..., min_length=1, max_length=MAX_TOPIC_LENGTH, description="Video topic or concept")
    style: str = Field("cinematic", max_length=100, description="Visual style (sanitized)")
    mood: str = Field("neutral", max_length=100, description="Mood or atmosphere (sanitized)")
    duration: int = Field(6, ge=4, le=8, description="Video duration in seconds")
    language: str = Field("ko", description="Output language")
    model: str = Field("gemini-3-flash-preview", description="AI model")
    # UQSL specific
    n_candidates: int = Field(3, ge=2, le=5, description="Number of candidates to generate")
    strategy: str = Field("auto", description="Selection strategy: auto, quality, hitl")

    @field_validator("topic", mode="before")
    @classmethod
    def strip_topic(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("style", mode="before")
    @classmethod
    def sanitize_style(cls, v: str) -> str:
        """Sanitize style to prevent XSS attacks."""
        return sanitize_generic_text(v, default="cinematic")

    @field_validator("mood", mode="before")
    @classmethod
    def sanitize_mood(cls, v: str) -> str:
        """Sanitize mood to prevent XSS attacks."""
        return sanitize_generic_text(v, default="neutral")

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, v: str) -> str:
        """Validate UQSL strategy is one of allowed values."""
        return _validate_strategy(v)


@router.post(
    "/1d/multi-generate",
    summary="1D Origin: UQSL Multi-Generate",
    description="Generate multiple Veo prompt candidates with quality evaluation.",
    tags=["Dimension 1D", "UQSL"],
)
async def generate_1d_prompt_multi(
    request: PromptMultiGenerateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
):
    """
    UQSL Multi-Generate for 1D Origin.

    Generates N candidates in parallel, evaluates quality scores, and
    recommends the best candidate using Thompson Sampling.
    """
    user_id = user.get("id", "unknown")
    logger.info(
        f"[1D_MULTI] user={user_id} topic_len={len(request.topic)} "
        f"n_candidates={request.n_candidates} strategy={request.strategy}"
    )

    from app.routers.intent_helpers import with_intent
    intent = with_intent(request)

    return await _execute_dimension_tool_multi(
        capsule_id=DimensionCapsuleId.PROMPT_GENERATE,
        tool_key="generate_veo_prompt",
        inputs={
            "topic": request.topic,
            "style": request.style,
            "mood": request.mood,
            "duration": f"{request.duration} seconds",
            "language": request.language,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"topic": request.topic[:100], "style": request.style},
        n_candidates=request.n_candidates,
        strategy=request.strategy,
        intent=intent,
    )


@router.post(
    "/1d/multi-generate/stream",
    summary="1D Origin: UQSL Multi-Generate (SSE Stream)",
    description="Generate multiple Veo prompts with real-time streaming.",
    tags=["Dimension 1D", "UQSL"],
)
async def generate_1d_prompt_multi_stream(
    request: PromptMultiGenerateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    UQSL Multi-Generate SSE Streaming for 1D Origin.

    Events:
    - progress: Generation progress
    - candidate: Individual candidate result
    - quality: Quality score for candidate
    - selection: Final selection with recommendation
    - complete: Final response
    """
    from app.routers.intent_helpers import with_intent
    intent = with_intent(request)

    return StreamingResponse(
        _execute_dimension_tool_multi_stream(
            capsule_id=DimensionCapsuleId.PROMPT_GENERATE,
            tool_key="generate_veo_prompt",
            operation_name="프롬프트 다중 생성",
            inputs={
                "topic": request.topic,
                "style": request.style,
                "mood": request.mood,
                "duration": f"{request.duration} seconds",
                "language": request.language,
            },
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={"topic": request.topic[:100], "style": request.style},
            n_candidates=request.n_candidates,
            strategy=request.strategy,
            intent=intent,
        ),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


# ============================================================================
# 2D Blueprint - Storyboard Creation
# ============================================================================

@router.post(
    "/2d/create",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="2D Blueprint: Create Storyboard",
    description="Create storyboard cards from a concept or video idea.",
    tags=["Dimension 2D"],
)
async def create_2d_storyboard(
    request: StoryboardCreateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Create storyboard cards with Intent-Resolver integration."""
    user_id = user.get("id", "unknown")
    logger.info(
        f"[2D_CREATE] user={user_id} concept_len={len(request.concept)} "
        f"scene_count={request.scene_count}"
    )

    from app.routers.intent_helpers import with_intent
    intent = with_intent(request)

    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.STORYBOARD_CREATE,
        tool_key="create_storyboard",
        inputs={
            "concept": request.concept,
            "prompt": request.prompt,
            "scene_count": request.scene_count,
            "language": request.language,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"concept": request.concept[:100] if request.concept else "", "scene_count": request.scene_count},
        intent=intent,
    )


@router.post(
    "/2d/create/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="2D Blueprint: Create Storyboard (SSE Stream)",
    description="Create storyboard with real-time progress updates via SSE.",
    tags=["Dimension 2D"],
)
async def create_2d_storyboard_stream(
    request: StoryboardCreateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Create storyboard cards with SSE streaming (2D Blueprint)."""
    from app.routers.intent_helpers import with_intent
    intent = with_intent(request)
    
    return StreamingResponse(
        _execute_dimension_tool_stream(
            capsule_id=DimensionCapsuleId.STORYBOARD_CREATE,
            tool_key="create_storyboard",
            operation_name="스토리보드 생성",
            inputs={
                "concept": request.concept,
                "prompt": request.prompt,
                "scene_count": request.scene_count,
                "language": request.language,
            },
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={"concept": request.concept[:100] if request.concept else "", "scene_count": request.scene_count},
            intent=intent,
        ),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


# ============================================================================
# 3D Ambience - Image Prompt Generation
# ============================================================================

@router.post(
    "/3d/generate",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="3D Ambience: Generate Image Prompt",
    description="Generate an optimized image prompt for AI generation.",
    tags=["Dimension 3D"],
)
async def generate_3d_image_prompt(
    request: ImageGenerateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Generate optimized image prompt with Intent-Resolver integration."""
    user_id = user.get("id", "unknown")
    logger.info(
        f"[3D_GENERATE] user={user_id} desc_len={len(request.description)} "
        f"style={request.style} aspect_ratio={request.aspect_ratio}"
    )

    from app.routers.intent_helpers import with_intent
    intent = with_intent(request)

    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.IMAGE_GENERATE,
        tool_key="generate_image_prompt",
        inputs={
            "description": request.description,
            "style": request.style,
            "aspect_ratio": request.aspect_ratio,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"description": request.description[:100] if request.description else "", "style": request.style},
        intent=intent,
    )


@router.post(
    "/3d/generate/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="3D Ambience: Generate Image Prompt (SSE Stream)",
    description="Generate image prompt with real-time progress updates via SSE.",
    tags=["Dimension 3D"],
)
async def generate_3d_image_prompt_stream(
    request: ImageGenerateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Generate optimized image prompt with SSE streaming (3D Ambience)."""
    from app.routers.intent_helpers import with_intent
    intent = with_intent(request)
    
    return StreamingResponse(
        _execute_dimension_tool_stream(
            capsule_id=DimensionCapsuleId.IMAGE_GENERATE,
            tool_key="generate_image_prompt",
            operation_name="이미지 프롬프트 생성",
            inputs={
                "description": request.description,
                "style": request.style,
                "aspect_ratio": request.aspect_ratio,
            },
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={"description": request.description[:100] if request.description else "", "style": request.style},
            intent=intent,
        ),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


# ============================================================================
# 4D Moment - Reference Analysis
# ============================================================================

@router.post(
    "/4d/analyze",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="4D Moment: Analyze Reference",
    description="Analyze video reference for cinematic elements.",
    tags=["Dimension 4D"],
)
async def analyze_4d_reference(
    request: ReferenceAnalyzeRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Analyze video reference with Intent-Resolver integration."""
    user_id = user.get("id", "unknown")
    logger.info(
        f"[4D_ANALYZE] user={user_id} desc_len={len(request.video_description)} "
        f"depth={request.analysis_depth} format={request.output_format} "
        f"focus_areas={request.focus_areas}"
    )

    from app.routers.intent_helpers import with_intent
    intent = with_intent(request)

    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.REFERENCE_ANALYZE,
        tool_key="analyze_reference",
        inputs={
            "video_description": request.video_description,
            "focus_areas": request.focus_areas,
            "analysis_depth": request.analysis_depth,
            "output_format": request.output_format,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"video_description": request.video_description[:100] if request.video_description else "", "analysis_depth": request.analysis_depth},
        intent=intent,
    )


@router.post(
    "/4d/analyze/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="4D Moment: Analyze Reference (SSE Stream)",
    description="Analyze video reference with real-time progress updates via SSE.",
    tags=["Dimension 4D"],
)
async def analyze_4d_reference_stream(
    request: ReferenceAnalyzeRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Analyze video reference with SSE streaming (4D Moment)."""
    from app.routers.intent_helpers import with_intent
    intent = with_intent(request)

    return StreamingResponse(
        _execute_dimension_tool_stream(
            capsule_id=DimensionCapsuleId.REFERENCE_ANALYZE,
            tool_key="analyze_reference",
            operation_name="레퍼런스 분석",
            inputs={
                "video_description": request.video_description,
                "focus_areas": request.focus_areas,
                "analysis_depth": request.analysis_depth,
                "output_format": request.output_format,
            },
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={"video_description": request.video_description[:100] if request.video_description else "", "analysis_depth": request.analysis_depth},
            intent=intent,
        ),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


# ============================================================================
# 4D Moment - Enhanced Reference Analysis (2026 Expert Workflow)
# ============================================================================

# Allowed MIME types for file uploads
ALLOWED_IMAGE_TYPES = frozenset([
    "image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"
])
ALLOWED_VIDEO_TYPES = frozenset([
    "video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"
])

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB


class StyleExtractionResponse(BaseModel):
    """Response for style extraction endpoint."""
    success: bool = True
    style_tags: List[str] = Field(default_factory=list)
    style_prompt: str = ""
    color_palette: List[str] = Field(default_factory=list)
    lighting: str = ""
    composition: str = ""
    mood: str = ""
    camera_angle: Optional[str] = None
    reference_artists: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    evidence_refs: List[str] = Field(default_factory=list)


class VideoAnalysisResponse(BaseModel):
    """Response for video reference analysis endpoint."""
    success: bool = True
    total_duration: float = 0.0
    frame_count: int = 0
    frames: List[dict] = Field(default_factory=list)
    scenes: List[dict] = Field(default_factory=list)
    style: dict = Field(default_factory=dict)
    suggested_shots: List[dict] = Field(default_factory=list)
    moodboard_frames: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    evidence_refs: List[str] = Field(default_factory=list)


class ImageAnalysisResponse(BaseModel):
    """Response for image reference analysis endpoint."""
    success: bool = True
    description: str = ""
    style: dict = Field(default_factory=dict)
    objects: List[str] = Field(default_factory=list)
    composition_analysis: str = ""
    recreation_prompt: str = ""
    similar_references: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)


@router.post(
    "/4d/extract-style",
    response_model=StyleExtractionResponse,
    responses={
        400: {"model": DimensionErrorResponse, "description": "Invalid file type or size"},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="4D Moment: Extract Style from Reference Image",
    description="""
    Extract reusable visual style from a reference image.

    Expert Workflow (2026): "스타일 프롬프트라고 따로 둬요... 일관성을 위해서"

    Returns:
    - style_tags: Visual style descriptors
    - style_prompt: Reusable prompt for consistent style
    - color_palette: Dominant colors (K-Means extracted)
    - lighting, composition, mood analysis
    - reference_artists: Similar known styles
    """,
    tags=["Dimension 4D", "Style Extraction"],
)
async def extract_style_from_image(
    file: UploadFile = File(..., description="Reference image (JPEG, PNG, WebP)"),
    context: Optional[str] = None,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StyleExtractionResponse:
    """Extract style from reference image (2026 Expert Workflow)."""
    from app.services.ai.style_extractor import get_style_extractor, StyleExtractionError

    user_id = user.get("id", "unknown")

    # Validate file type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type: {content_type}. Allowed: {list(ALLOWED_IMAGE_TYPES)}"
        )

    # Read and validate size
    image_bytes = await file.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large. Maximum size: {MAX_IMAGE_SIZE // (1024*1024)}MB"
        )

    logger.info(
        f"[4D_STYLE_EXTRACT] user={user_id} file={file.filename} "
        f"size={len(image_bytes)} type={content_type}"
    )

    try:
        # Extract style using the new service
        extractor = get_style_extractor()
        result = await extractor.extract_style(
            image_bytes=image_bytes,
            additional_context=context,
            mime_type=content_type,
        )

        return StyleExtractionResponse(
            success=True,
            style_tags=result.style_tags,
            style_prompt=result.style_prompt,
            color_palette=result.color_palette,
            lighting=result.lighting,
            composition=result.composition,
            mood=result.mood,
            camera_angle=result.camera_angle,
            reference_artists=result.reference_artists,
            confidence=result.confidence,
            evidence_refs=[f"db:style_extractions:{user_id}:{file.filename}"],
        )

    except StyleExtractionError as e:
        logger.error(f"Style extraction failed: {e}")
        raise HTTPException(status_code=500, detail=safe_error_detail(e, "Style extraction"))
    except Exception as e:
        logger.exception(f"Unexpected error in style extraction: {e}")
        raise HTTPException(status_code=500, detail="스타일 추출 중 오류가 발생했습니다.")


@router.post(
    "/4d/analyze-video",
    response_model=VideoAnalysisResponse,
    responses={
        400: {"model": DimensionErrorResponse, "description": "Invalid file type or size"},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="4D Moment: Analyze Video Reference",
    description="""
    Comprehensive video reference analysis with frame-by-frame breakdown.

    Expert Workflow (2026): "레퍼런스 영상을 프레임별로 분석해서 샷 리스트를 만들어요"

    Returns:
    - Frame-by-frame analysis (objects, actions, camera movement)
    - Scene segmentation
    - Style extraction
    - Shot list for recreation
    - Moodboard frames (base64)
    """,
    tags=["Dimension 4D", "Video Analysis"],
)
async def analyze_video_reference(
    file: UploadFile = File(..., description="Video file (MP4, WebM, MOV)"),
    analysis_depth: str = "detailed",
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VideoAnalysisResponse:
    """Analyze video reference frame-by-frame (2026 Expert Workflow)."""
    from app.services.ai.reference_analyzer import (
        get_reference_analyzer,
        ReferenceAnalysisError,
    )

    user_id = user.get("id", "unknown")

    # Validate depth
    try:
        analysis_depth = _validate_analysis_depth(analysis_depth)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Validation"))

    # Validate file type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid video type: {content_type}. Allowed: {list(ALLOWED_VIDEO_TYPES)}"
        )

    # Read and validate size
    video_bytes = await file.read()
    if len(video_bytes) > MAX_VIDEO_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Video too large. Maximum size: {MAX_VIDEO_SIZE // (1024*1024)}MB"
        )

    logger.info(
        f"[4D_VIDEO_ANALYZE] user={user_id} file={file.filename} "
        f"size={len(video_bytes)} depth={analysis_depth}"
    )

    try:
        # Analyze video using the new service
        analyzer = get_reference_analyzer()
        result = await analyzer.analyze_video_reference(
            video_bytes=video_bytes,
            analysis_depth=analysis_depth,
        )

        return VideoAnalysisResponse(
            success=True,
            total_duration=result.total_duration,
            frame_count=result.frame_count,
            frames=[f.model_dump() for f in result.frames],
            scenes=[s.model_dump() for s in result.scenes],
            style=result.style.model_dump(),
            suggested_shots=[s.model_dump() for s in result.suggested_shots],
            moodboard_frames=result.moodboard_frames,
            confidence=result.confidence,
            evidence_refs=[f"db:video_analyses:{user_id}:{file.filename}"],
        )

    except ReferenceAnalysisError as e:
        logger.error(f"Video analysis failed: {e}")
        raise HTTPException(status_code=500, detail=safe_error_detail(e, "Video analysis"))
    except Exception as e:
        logger.exception(f"Unexpected error in video analysis: {e}")
        raise HTTPException(status_code=500, detail="비디오 분석 중 오류가 발생했습니다.")


@router.post(
    "/4d/analyze-image",
    response_model=ImageAnalysisResponse,
    responses={
        400: {"model": DimensionErrorResponse, "description": "Invalid file type or size"},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="4D Moment: Analyze Image Reference",
    description="""
    Detailed image reference analysis with recreation prompt.

    Returns:
    - Detailed description
    - Style extraction
    - Object detection
    - Composition analysis
    - Recreation prompt for AI generation
    """,
    tags=["Dimension 4D", "Image Analysis"],
)
async def analyze_image_reference(
    file: UploadFile = File(..., description="Reference image (JPEG, PNG, WebP)"),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImageAnalysisResponse:
    """Analyze image reference with recreation prompt (2026 Expert Workflow)."""
    from app.services.ai.reference_analyzer import (
        get_reference_analyzer,
        ReferenceAnalysisError,
    )

    user_id = user.get("id", "unknown")

    # Validate file type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type: {content_type}. Allowed: {list(ALLOWED_IMAGE_TYPES)}"
        )

    # Read and validate size
    image_bytes = await file.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large. Maximum size: {MAX_IMAGE_SIZE // (1024*1024)}MB"
        )

    logger.info(
        f"[4D_IMAGE_ANALYZE] user={user_id} file={file.filename} "
        f"size={len(image_bytes)} type={content_type}"
    )

    try:
        # Analyze image using the new service
        analyzer = get_reference_analyzer()
        result = await analyzer.analyze_image_reference(
            image_bytes=image_bytes,
            mime_type=content_type,
        )

        return ImageAnalysisResponse(
            success=True,
            description=result.description,
            style=result.style.model_dump(),
            objects=result.objects,
            composition_analysis=result.composition_analysis,
            recreation_prompt=result.recreation_prompt,
            similar_references=result.similar_references,
            evidence_refs=[f"db:image_analyses:{user_id}:{file.filename}"],
        )

    except ReferenceAnalysisError as e:
        logger.error(f"Image analysis failed: {e}")
        raise HTTPException(status_code=500, detail=safe_error_detail(e, "Image analysis"))
    except Exception as e:
        logger.exception(f"Unexpected error in image analysis: {e}")
        raise HTTPException(status_code=500, detail="이미지 분석 중 오류가 발생했습니다.")
