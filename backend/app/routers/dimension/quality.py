"""
Quality Dimension Endpoints - Quality Check & Creative Editor.

- Quality Check: Evaluate content quality across 6 criteria
- Creative Editor: Analyze and rewrite content using an editorial persona
"""
from __future__ import annotations

from typing import List

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
    get_sse_headers,
    Optional,
)

router = APIRouter()


# ============================================================================
# Request Models
# ============================================================================

class QualityCheckRequest(BaseModel):
    """Request model for Quality Check evaluation."""
    content: str = Field(..., min_length=1, max_length=10000, description="Content to evaluate")
    content_type: str = Field("prompt", max_length=50, description="Type of content")
    criteria: List[str] = Field(
        default=["clarity", "specificity", "creativity", "coherence", "grammar", "impact"],
        description="Evaluation criteria"
    )
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="Quality threshold")
    model: str = Field("gemini-1.5-pro", description="AI model")

    @field_validator("content", mode="before")
    @classmethod
    def strip_content(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class CreativeEditorRequest(BaseModel):
    """Request model for Creative Editor."""
    content: str = Field(..., min_length=1, max_length=10000, description="Content to improve")
    context: str = Field(..., min_length=1, max_length=1000, description="Context/Genre/Audience")
    persona: str = Field("Senior Editor", max_length=100, description="Editorial persona")
    use_rag: bool = Field(True, description="Use RAG for editing principles")
    model: str = Field("gemini-1.5-pro", description="AI model")

    @field_validator("content", "context", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


# ============================================================================
# Quality Check
# ============================================================================

@router.post(
    "/quality/check",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Quality Checker: Evaluate Content",
    description="Evaluate content quality across 6 criteria.",
    tags=["Dimension Extended"],
)
async def check_quality(
    request: QualityCheckRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Check content quality with Intent-Resolver integration."""
    from app.routers.intent_helpers import infer_intent_from_request
    intent = infer_intent_from_request()
    
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.QUALITY_CHECK,
        tool_key="quality_check",
        inputs={
            "content": request.content,
            "content_type": request.content_type,
            "criteria": request.criteria,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"content_type": request.content_type, "criteria": request.criteria},
        params={"threshold": request.threshold},
        intent=intent,
    )


@router.post(
    "/quality/check/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Quality Checker: Evaluate Content (SSE Stream)",
    description="Evaluate content quality with real-time progress updates via SSE.",
    tags=["Dimension Extended"],
)
async def check_quality_stream(
    request: QualityCheckRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Check content quality with SSE streaming."""
    from app.routers.intent_helpers import infer_intent_from_request
    intent = infer_intent_from_request()
    
    return StreamingResponse(
        _execute_dimension_tool_stream(
            capsule_id=DimensionCapsuleId.QUALITY_CHECK,
            tool_key="quality_check",
            operation_name="품질 검수",
            inputs={
                "content": request.content,
                "content_type": request.content_type,
                "criteria": request.criteria,
            },
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={"content_type": request.content_type, "criteria": request.criteria},
            params={"threshold": request.threshold},
            intent=intent,
        ),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


# ============================================================================
# Creative Editor
# ============================================================================

@router.post(
    "/quality/editor",
    response_model=DimensionResponse,
    summary="Creative Editor: Improve Content",
    description="Analyze and rewrite content using an editorial persona.",
    tags=["Dimension Quality"],
)
async def run_creative_editor(
    request: CreativeEditorRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Run Creative Editor with Intent-Resolver integration."""
    from app.routers.intent_helpers import infer_intent_from_request
    intent = infer_intent_from_request()
    
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.CREATIVE_EDITOR,
        tool_key="run_creative_editor",
        inputs={
            "content": request.content,
            "context": request.context,
            "persona": request.persona,
        },
        params={"use_rag": request.use_rag},
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"content_len": len(request.content), "persona": request.persona},
        intent=intent,
    )


@router.post(
    "/quality/editor/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Creative Editor: Improve Content (SSE Stream)",
    description="Improve content with real-time progress updates via SSE.",
    tags=["Dimension Quality"],
)
async def run_creative_editor_stream(
    request: CreativeEditorRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Run Creative Editor with SSE streaming."""
    from app.routers.intent_helpers import infer_intent_from_request
    intent = infer_intent_from_request()
    
    return StreamingResponse(
        _execute_dimension_tool_stream(
            capsule_id=DimensionCapsuleId.CREATIVE_EDITOR,
            tool_key="run_creative_editor",
            operation_name="콘텐츠 개선",
            inputs={
                "content": request.content,
                "context": request.context,
                "persona": request.persona,
            },
            params={"use_rag": request.use_rag},
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={"content_len": len(request.content), "persona": request.persona},
            intent=intent,
        ),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )
