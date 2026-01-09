"""
Aesthetic Dimension Endpoints - Aesthetic Director.

- Aesthetic Direct: Generate style guide with auteur matching
- Aesthetic Moodboard: Generate visual direction cards
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
    _validate_model,
    _strip_string,
    DimensionResponse,
    DimensionErrorResponse,
    DimensionCapsuleId,
    MAX_CONCEPT_LENGTH,
    get_sse_headers,
    Optional,
)

router = APIRouter()


# ============================================================================
# Request Models
# ============================================================================

class AestheticDirectRequest(BaseModel):
    """Request model for Aesthetic Director style guide generation."""
    concept: str = Field(..., min_length=1, max_length=MAX_CONCEPT_LENGTH, description="Visual concept")
    reference_style: str = Field("wong", max_length=100, description="Auteur reference style")
    mood: str = Field("cinematic", max_length=100, description="Visual mood")
    target_medium: str = Field("video", max_length=50, description="Target medium")
    use_rag: bool = Field(True, description="Use RAG for auteur knowledge")
    model: str = Field("gemini-1.5-pro", description="AI model")

    @field_validator("concept", "reference_style", "mood", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class AestheticMoodboardRequest(BaseModel):
    """Request model for Aesthetic Moodboard generation."""
    concept: str = Field(..., min_length=1, max_length=MAX_CONCEPT_LENGTH, description="Visual concept")
    mood: str = Field("cinematic", max_length=100, description="Visual mood")
    model: str = Field("gemini-2.0-flash-exp", description="AI model")

    @field_validator("concept", "mood", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


# ============================================================================
# Aesthetic Direct
# ============================================================================

@router.post(
    "/aesthetic/direct",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Aesthetic Director: Generate Style Guide",
    description="Generate visual style guidelines with auteur matching.",
    tags=["Dimension Extended"],
)
async def direct_aesthetic(
    request: AestheticDirectRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Generate aesthetic style guide with Intent-Resolver integration."""
    from app.routers.intent_helpers import infer_intent_for_aesthetic
    intent = infer_intent_for_aesthetic(
        concept=request.concept,
        mood=request.mood,
        reference_style=request.reference_style,
        target_medium=request.target_medium,
    )
    
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.AESTHETIC_DIRECT,
        tool_key="aesthetic_direct",
        inputs={
            "concept": request.concept,
            "reference_style": request.reference_style,
            "mood": request.mood,
            "target_medium": request.target_medium,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"concept": request.concept[:100], "style": request.reference_style},
        params={"use_rag": request.use_rag},
        intent=intent,
    )


@router.post(
    "/aesthetic/direct/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Aesthetic Director: Generate Style Guide (SSE Stream)",
    description="Generate visual style guidelines with real-time progress updates via SSE.",
    tags=["Dimension Extended"],
)
async def direct_aesthetic_stream(
    request: AestheticDirectRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Generate aesthetic style guide with SSE streaming."""
    from app.routers.intent_helpers import infer_intent_for_aesthetic
    intent = infer_intent_for_aesthetic(
        concept=request.concept,
        mood=request.mood,
        reference_style=request.reference_style,
        target_medium=request.target_medium,
    )
    
    return StreamingResponse(
        _execute_dimension_tool_stream(
            capsule_id=DimensionCapsuleId.AESTHETIC_DIRECT,
            tool_key="aesthetic_direct",
            operation_name="스타일 가이드 생성",
            inputs={
                "concept": request.concept,
                "reference_style": request.reference_style,
                "mood": request.mood,
                "target_medium": request.target_medium,
            },
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={"concept": request.concept[:100], "style": request.reference_style},
            params={"use_rag": request.use_rag},
            intent=intent,
        ),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


# ============================================================================
# Aesthetic Moodboard
# ============================================================================

@router.post(
    "/aesthetic/moodboard",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Aesthetic Director: Generate Mood Board",
    description="Stage 1: Generate 3 distinct visual direction cards.",
    tags=["Dimension Extended"],
)
async def generate_aesthetic_moodboard(
    request: AestheticMoodboardRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Generate visual direction cards with Intent-Resolver integration."""
    from app.routers.intent_helpers import with_intent
    intent = with_intent(request, "aesthetic")
    
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.AESTHETIC_MOODBOARD,
        tool_key="aesthetic_moodboard",
        inputs={
            "concept": request.concept,
            "mood": request.mood,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"concept": request.concept[:100], "mood": request.mood},
        intent=intent,
    )


@router.post(
    "/aesthetic/moodboard/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Aesthetic Director: Generate Mood Board (SSE Stream)",
    description="Generate mood board with real-time progress updates via SSE.",
    tags=["Dimension Extended"],
)
async def generate_aesthetic_moodboard_stream(
    request: AestheticMoodboardRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Generate visual direction cards with SSE streaming."""
    from app.routers.intent_helpers import with_intent
    intent = with_intent(request, "aesthetic")
    
    return StreamingResponse(
        _execute_dimension_tool_stream(
            capsule_id=DimensionCapsuleId.AESTHETIC_MOODBOARD,
            tool_key="aesthetic_moodboard",
            operation_name="무드보드 생성",
            inputs={
                "concept": request.concept,
                "mood": request.mood,
            },
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={"concept": request.concept[:100], "mood": request.mood},
            intent=intent,
        ),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )
