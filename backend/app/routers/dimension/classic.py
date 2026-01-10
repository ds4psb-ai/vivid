"""
Classic Dimension Endpoints - 1D, 2D, 3D, 4D.

- 1D Origin: Veo Prompt Generation
- 2D Blueprint: Storyboard Creation
- 3D Ambience: Image Prompt Generation
- 4D Moment: Reference Analysis
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from ._base import (
    get_db,
    get_current_user,
    get_byok_key,
    _execute_dimension_tool,
    _execute_dimension_tool_stream,
    _validate_language,
    _validate_model,
    _validate_aspect_ratio,
    _strip_string,
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
)

router = APIRouter()


# ============================================================================
# Request Models
# ============================================================================

class PromptGenerateRequest(BaseModel):
    """Request model for 1D Origin prompt generation."""
    topic: str = Field(..., min_length=1, max_length=MAX_TOPIC_LENGTH, description="Video topic or concept")
    style: str = Field("cinematic", max_length=100, description="Visual style")
    mood: str = Field("neutral", max_length=100, description="Mood or atmosphere")
    duration: int = Field(6, ge=4, le=8, description="Video duration in seconds")
    language: str = Field("ko", description="Output language")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("topic", "style", "mood", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return _strip_string(v)

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
    """Request model for 3D Ambience image prompt generation."""
    description: str = Field(..., min_length=1, max_length=MAX_DESCRIPTION_LENGTH, description="Image description")
    style: str = Field("photorealistic", max_length=100, description="Image style")
    aspect_ratio: str = Field("16:9", description="Aspect ratio")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("description", "style", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("aspect_ratio")
    @classmethod
    def validate_aspect_ratio(cls, v: str) -> str:
        return _validate_aspect_ratio(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class ReferenceAnalyzeRequest(BaseModel):
    """Request model for 4D Moment reference analysis."""
    video_description: str = Field(..., min_length=1, max_length=MAX_DESCRIPTION_LENGTH, description="Video to analyze")
    focus_areas: list[str] = Field(
        default=["cinematography", "editing", "color", "sound"],
        description="Areas to focus analysis on"
    )
    analysis_depth: str = Field("standard", max_length=50, description="Analysis depth (quick, standard, deep)")
    output_format: str = Field("structured", max_length=50, description="Output format (structured, narrative, bullet)")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("video_description", mode="before")
    @classmethod
    def strip_description(cls, v: str) -> str:
        return _strip_string(v)

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
