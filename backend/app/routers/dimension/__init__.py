"""
Dimension Router Package - Modular dimension API endpoints.

This package provides all dimension-related API endpoints, organized by domain:
- classic: 1D, 2D, 3D, 4D (Origin, Blueprint, Ambience, Moment)
- aesthetic: Aesthetic Director, Moodboard
- sound: Sound Crafter, Moodboard
- story: Story Architect, Refine
- quality: Quality Check, Creative Editor

Usage in main.py:
    from app.routers.dimension import router as dimension_router
    app.include_router(dimension_router, prefix="/api/dimension")
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

# Import sub-routers
from .classic import router as classic_router
from .aesthetic import router as aesthetic_router
from .sound import router as sound_router
from .story import router as story_router
from .quality import router as quality_router
from .veo import router as veo_router

# Re-export from _base for backward compatibility
from ._base import (
    DimensionResponse,
    DimensionErrorResponse,
    MetricsResponse,
    DIMENSION_NAMES,
    CAPSULE_TO_DIMENSION,
    get_credit_cost,
    _execute_dimension_tool,
    _execute_dimension_tool_stream,
    DimensionCapsuleId,
)

# Create combined router
router = APIRouter()

# Include all sub-routers
router.include_router(classic_router)
router.include_router(aesthetic_router)
router.include_router(sound_router)
router.include_router(story_router)
router.include_router(quality_router)
router.include_router(veo_router)


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
    """List all dimensions and their purposes (legacy format)."""
    return {
        "dimensions": [
            # Classic Dimensions
            {"id": "1d", "name": "Origin", "description": "Veo 프롬프트 생성 - 비디오의 시작점", "endpoint": "/api/dimension/1d/generate"},
            {"id": "2d", "name": "Blueprint", "description": "스토리보드 생성 - 구조와 흐름", "endpoint": "/api/dimension/2d/create"},
            {"id": "3d", "name": "Ambience", "description": "이미지 프롬프트 생성 - 분위기와 시각", "endpoint": "/api/dimension/3d/generate"},
            {"id": "4d", "name": "Moment", "description": "레퍼런스 분석 - 순간 포착", "endpoint": "/api/dimension/4d/analyze"},
        ],
        "workflow_4stage": [
            # Stage 1: Planning
            {"stage": 1, "name": "Story Architect", "description": "컨셉 정제 및 시나리오 생성", "endpoints": ["/api/dimension/story/refine", "/api/dimension/story/architect"]},
            # Stage 2: Visual Design  
            {"stage": 2, "name": "Aesthetic Director", "description": "비주얼 디렉션 및 스타일 가이드", "endpoints": ["/api/dimension/aesthetic/moodboard", "/api/dimension/aesthetic/direct"]},
            # Stage 3: Sound Design
            {"stage": 3, "name": "Sound Crafter", "description": "사운드 디자인 및 음악 프롬프트", "endpoints": ["/api/dimension/sound/moodboard", "/api/dimension/sound/craft"]},
            # Stage 4: Quality Control
            {"stage": 4, "name": "Quality Gate", "description": "품질 검수 및 콘텐츠 개선", "endpoints": ["/api/dimension/quality/check", "/api/dimension/quality/editor"]},
        ],
        "extended": [
            {"id": "veo", "name": "Video Maker", "description": "AI 영상 생성 (Veo 3.1)", "endpoint": "/api/dimension/veo/generate/stream"},
        ],
    }


@router.get(
    "/credits/info",
    summary="Credits Info",
    description="Get credit costs for all dimension tools.",
    tags=["Dimension Info"],
)
async def credits_info() -> Dict[str, Any]:
    """Get credit costs for all dimension tools."""
    credit_costs = {}
    for capsule_id in DimensionCapsuleId:
        try:
            credit_costs[capsule_id.value] = {
                "flash": get_credit_cost(capsule_id, "gemini-2.0-flash-exp"),
                "pro": get_credit_cost(capsule_id, "gemini-1.5-pro"),
            }
        except Exception:
            pass
    
    return {
        "costs": credit_costs,
        "byok_info": "BYOK 사용자는 크레딧이 차감되지 않습니다.",
    }


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "router",
    "DimensionResponse",
    "DimensionErrorResponse",
    "MetricsResponse",
    "DIMENSION_NAMES",
    "CAPSULE_TO_DIMENSION",
    "get_credit_cost",
    "_execute_dimension_tool",
    "_execute_dimension_tool_stream",
    "DimensionCapsuleId",
]
