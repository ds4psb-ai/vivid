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


@router.get(
    "/tools",
    summary="Dimension Tools Config",
    description="Get all dimension tools configuration for frontend.",
    tags=["Dimension Info"],
)
async def get_tools_config() -> Dict[str, Any]:
    """Return tool configuration for frontend DimensionConfigContext."""
    # Hardcoded credit costs (avoiding broken get_credit_cost import)
    tools = [
        {
            "toolId": "prompt_generator",
            "dimension": "1D",
            "displayName": "프롬프트 연금술",
            "displayNameEn": "Prompt Alchemy",
            "description": "AI가 이해하는 전문 언어로 번역",
            "icon": "sparkles",
            "color": "violet",
            "stage": "pre_production",
            "capsuleKey": "teaching.prompt.generate",
            "endpoint": "/api/dimension/1d/generate",
            "creditCost": 5,
        },
        {
            "toolId": "storyboard",
            "dimension": "2D",
            "displayName": "스토리보드 스케치",
            "displayNameEn": "Storyboard Sketch",
            "description": "글을 시각적 컷으로 스케치",
            "icon": "layout-grid",
            "color": "emerald",
            "stage": "pre_production",
            "capsuleKey": "teaching.storyboard.create",
            "endpoint": "/api/dimension/2d/create",
            "creditCost": 10,
        },
        {
            "toolId": "image_tool",
            "dimension": "3D",
            "displayName": "비주얼 리얼라이저",
            "displayNameEn": "Visual Realizer",
            "description": "Key Frame 고품질 생성",
            "icon": "image",
            "color": "amber",
            "stage": "production",
            "capsuleKey": "teaching.image.generate",
            "endpoint": "/api/dimension/3d/generate",
            "creditCost": 5,
        },
        {
            "toolId": "reference_analyzer",
            "dimension": "4D",
            "displayName": "레퍼런스 해석기",
            "displayNameEn": "Reference Decoder",
            "description": "조명, 색감, 연출의 전문가적 분석",
            "icon": "film",
            "color": "cyan",
            "stage": "planning",
            "capsuleKey": "teaching.reference.analyze",
            "endpoint": "/api/dimension/4d/analyze",
            "creditCost": 8,
        },
        {
            "toolId": "quality_check",
            "dimension": "QC",
            "displayName": "퀄리티 디렉터",
            "displayNameEn": "Quality Director",
            "description": "시각적 일관성 및 품질 검수",
            "icon": "check-circle",
            "color": "rose",
            "stage": "finishing",
            "capsuleKey": "dimension.quality.check",
            "endpoint": "/api/dimension/quality/check",
            "creditCost": 8,
        },
        {
            "toolId": "aesthetic_direct",
            "dimension": "AD",
            "displayName": "미학디렉터",
            "displayNameEn": "Aesthetic Director",
            "description": "시각적 스타일 가이드라인 생성",
            "icon": "palette",
            "color": "fuchsia",
            "stage": "planning",
            "capsuleKey": "dimension.aesthetic.direct",
            "endpoint": "/api/dimension/aesthetic/direct",
            "creditCost": 10,
        },
        {
            "toolId": "persona_analyze",
            "dimension": "AI",
            "displayName": "심연의 거울",
            "displayNameEn": "Abyss Mirror",
            "description": "내면의 욕구와 감정 해석",
            "icon": "moon",
            "color": "indigo",
            "stage": "planning",
            "capsuleKey": "dimension.persona.analyze",
            "endpoint": "/api/dimension/persona/analyze",
            "creditCost": 5,
        },
        {
            "toolId": "veo_generate",
            "dimension": "VEO",
            "displayName": "비디오 메이커",
            "displayNameEn": "Video Maker",
            "description": "최종 AI 영상 생성",
            "icon": "video",
            "color": "sky",
            "stage": "production",
            "capsuleKey": "veo.video.generate",
            "endpoint": "/api/dimension/veo/generate",
            "creditCost": 200,
        },
    ]
    
    # Build toolsById map
    tools_by_id = {tool["toolId"]: tool for tool in tools}
    
    return {
        "tools": tools,
        "toolsById": tools_by_id,
        "stageOrder": ["planning", "pre_production", "production", "finishing"],
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
