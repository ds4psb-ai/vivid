"""Dimension API endpoints for Crebit creative tools.

Renamed from Teaching API → Dimension API (2026-01)
Provides API endpoints for dimension-based creative tools:
- POST /api/dimension/1d/generate  (Origin - Veo Prompt)
- POST /api/dimension/2d/create    (Blueprint - Storyboard)
- POST /api/dimension/3d/generate  (Ambience - Image Prompt)
- POST /api/dimension/4d/analyze   (Moment - Reference Analysis)

Uses server API key by default, supports BYOK via header.
Credits are deducted when using server API key (BYOK bypasses billing).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user

# Import existing teaching router functions for now (Phase 1 - delegation)
from app.routers.teaching import (
    PromptGenerateRequest,
    StoryboardCreateRequest,
    ImageGenerateRequest,
    ReferenceAnalyzeRequest,
    TeachingResponse,
    TeachingErrorResponse,
    get_byok_key,
    generate_prompt as _generate_prompt,
    create_storyboard as _create_storyboard,
    generate_image_prompt as _generate_image_prompt,
    analyze_reference as _analyze_reference,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Dimension Mapping
# ============================================================================

DIMENSION_NAMES = {
    "1d": "Origin",      # Veo Prompt Generation
    "2d": "Blueprint",   # Storyboard Creation
    "3d": "Ambience",    # Image Prompt Generation
    "4d": "Moment",      # Reference Analysis
}


# ============================================================================
# 1D Origin - Veo Prompt Generation
# ============================================================================

@router.post(
    "/1d/generate",
    response_model=TeachingResponse,
    responses={
        400: {"model": TeachingErrorResponse, "description": "Invalid input"},
        401: {"description": "Not authenticated"},
        402: {"model": TeachingErrorResponse, "description": "Insufficient credits"},
        500: {"model": TeachingErrorResponse, "description": "Generation failed"},
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
) -> TeachingResponse:
    """Generate Veo video prompt (1D Origin)."""
    return await _generate_prompt(request, user, byok_key, db)


# ============================================================================
# 2D Blueprint - Storyboard Creation
# ============================================================================

@router.post(
    "/2d/create",
    response_model=TeachingResponse,
    responses={
        400: {"model": TeachingErrorResponse},
        402: {"model": TeachingErrorResponse, "description": "Insufficient credits"},
        500: {"model": TeachingErrorResponse},
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
) -> TeachingResponse:
    """Create storyboard cards (2D Blueprint)."""
    return await _create_storyboard(request, user, byok_key, db)


# ============================================================================
# 3D Ambience - Image Prompt Generation
# ============================================================================

@router.post(
    "/3d/generate",
    response_model=TeachingResponse,
    responses={
        400: {"model": TeachingErrorResponse},
        402: {"model": TeachingErrorResponse, "description": "Insufficient credits"},
        500: {"model": TeachingErrorResponse},
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
) -> TeachingResponse:
    """Generate optimized image prompt (3D Ambience)."""
    return await _generate_image_prompt(request, user, byok_key, db)


# ============================================================================
# 4D Moment - Reference Analysis
# ============================================================================

@router.post(
    "/4d/analyze",
    response_model=TeachingResponse,
    responses={
        400: {"model": TeachingErrorResponse},
        402: {"model": TeachingErrorResponse, "description": "Insufficient credits"},
        500: {"model": TeachingErrorResponse},
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
) -> TeachingResponse:
    """Analyze video reference (4D Moment)."""
    return await _analyze_reference(request, user, byok_key, db)


# ============================================================================
# Info Endpoints
# ============================================================================

@router.get(
    "/info",
    summary="Dimension Info",
    description="Get information about all dimensions.",
    tags=["Dimension Info"],
)
async def dimension_info() -> Dict[str, Any]:
    """List all dimensions and their purposes."""
    return {
        "dimensions": [
            {
                "id": "1d",
                "name": "Origin",
                "description": "Veo 프롬프트 생성 - 비디오의 시작점",
                "endpoint": "/api/dimension/1d/generate",
            },
            {
                "id": "2d",
                "name": "Blueprint",
                "description": "스토리보드 생성 - 구조와 흐름",
                "endpoint": "/api/dimension/2d/create",
            },
            {
                "id": "3d",
                "name": "Ambience",
                "description": "이미지 프롬프트 생성 - 분위기와 시각",
                "endpoint": "/api/dimension/3d/generate",
            },
            {
                "id": "4d",
                "name": "Moment",
                "description": "레퍼런스 분석 - 순간 포착",
                "endpoint": "/api/dimension/4d/analyze",
            },
        ]
    }


@router.get(
    "/health",
    summary="Health Check",
    description="Check dimension API health status.",
    tags=["Dimension Info"],
)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    from app.config import settings
    
    return {
        "status": "healthy",
        "api_key_configured": "yes" if settings.GEMINI_API_KEY else "no",
        "api_version": "dimension-v1",
    }


# ============================================================================
# Metrics Endpoints (Evidence Loop Integration)
# ============================================================================

@router.get(
    "/metrics/stats",
    summary="Evidence Stats",
    description="Get overall evidence collection statistics.",
    tags=["Dimension Metrics"],
)
async def get_metrics_stats() -> Dict[str, Any]:
    """Get evidence collection statistics."""
    from app.agents.evidence_loop import get_evidence_stats
    
    stats = get_evidence_stats()
    return {
        "evidence": stats,
        "api_version": "dimension-v1",
    }


@router.get(
    "/metrics/session/{session_id}",
    summary="Session Metrics",
    description="Get metrics for a specific user session.",
    tags=["Dimension Metrics"],
)
async def get_metrics_by_session(session_id: str) -> Dict[str, Any]:
    """Get metrics for a specific session."""
    from app.agents.evidence_loop import get_session_metrics
    
    metrics = get_session_metrics(session_id)
    return {
        "session_id": session_id,
        "metrics": metrics,
    }


@router.get(
    "/metrics/tool/{tool_name}",
    summary="Tool Metrics",
    description="Get metrics for a specific dimension tool.",
    tags=["Dimension Metrics"],
)
async def get_metrics_by_tool(tool_name: str) -> Dict[str, Any]:
    """Get metrics for a specific tool.
    
    Valid tool names:
    - generate_veo_prompt (1D Origin)
    - create_storyboard (2D Blueprint)
    - generate_image_prompt (3D Ambience)
    - analyze_reference (4D Moment)
    """
    from app.agents.evidence_loop import get_tool_metrics
    
    metrics = get_tool_metrics(tool_name)
    return {
        "tool_name": tool_name,
        "metrics": metrics,
    }


@router.get(
    "/metrics/summary",
    summary="Metrics Summary",
    description="Get aggregated metrics summary for all dimensions.",
    tags=["Dimension Metrics"],
)
async def get_metrics_summary() -> Dict[str, Any]:
    """Get aggregated metrics summary for all dimension tools."""
    from app.agents.evidence_loop import get_tool_metrics, get_evidence_stats
    
    DIMENSION_TOOLS = {
        "1d": "generate_veo_prompt",
        "2d": "create_storyboard",
        "3d": "generate_image_prompt",
        "4d": "analyze_reference",
    }
    
    summary = {
        "dimensions": {},
        "overall": get_evidence_stats(),
    }
    
    for dim_id, tool_name in DIMENSION_TOOLS.items():
        tool_metrics = get_tool_metrics(tool_name)
        summary["dimensions"][dim_id] = {
            "name": DIMENSION_NAMES.get(dim_id, dim_id),
            "tool_name": tool_name,
            "total_executions": tool_metrics.get("total_executions", 0),
            "success_count": tool_metrics.get("success_count", 0),
            "completion_rate": tool_metrics.get("completion_rate", 0),
            "avg_latency_ms": tool_metrics.get("avg_latency_ms", 0),
        }
    
    return summary

