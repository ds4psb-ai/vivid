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

import logging
from typing import Any, Dict

from fastapi import APIRouter

logger = logging.getLogger(__name__)

# Import sub-routers
from .classic import router as classic_router
from .aesthetic import router as aesthetic_router
from .sound import router as sound_router
from .story import router as story_router
from .quality import router as quality_router
from .veo import router as veo_router
from .kling import router as kling_router
from .suno import router as suno_router
from .json_gen import router as json_gen_router
from .nanobanana import router as nanobanana_router
from .mirror import router as mirror_router
from .prompt import router as prompt_router
from .character import router as character_router
from .storyboard import router as storyboard_router
from .veo_sequence import router as veo_sequence_router
from .kling_motion import router as kling_motion_router

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
router.include_router(kling_router)
router.include_router(suno_router)
router.include_router(json_gen_router)
router.include_router(nanobanana_router)
router.include_router(mirror_router)
router.include_router(prompt_router)
router.include_router(character_router)
router.include_router(storyboard_router)
router.include_router(veo_sequence_router)
router.include_router(kling_motion_router)


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
                "flash": get_credit_cost(capsule_id, "gemini-3-flash-preview"),
                "pro": get_credit_cost(capsule_id, "gemini-3-pro-preview"),
            }
        except Exception as e:
            logger.debug(f"[credits_info] Failed to get cost for {capsule_id}: {e}")
    
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
    """Return tool configuration for frontend DimensionConfigContext.
    
    v2: AppRegistry SSoT 기반 동적 로딩 (하드코딩 폴백 유지).
    """
    tools = []
    
    # Try AppRegistry first (SSoT)
    try:
        from app.core.app_registry import AppRegistry
        from app.core.app_schema import AppType
        
        dimension_apps = AppRegistry.get_by_type(AppType.DIMENSION)
        
        # Display settings per dimension
        DIMENSION_DISPLAY = {
            "1d": {"toolId": "prompt_generator", "displayName": "프롬프트 연금술", "displayNameEn": "Prompt Alchemy", "icon": "sparkles", "color": "violet", "stage": "pre_production"},
            "2d": {"toolId": "storyboard", "displayName": "스토리보드 스케치", "displayNameEn": "Storyboard Sketch", "icon": "layout-grid", "color": "emerald", "stage": "pre_production"},
            "3d": {"toolId": "image_tool", "displayName": "비주얼 리얼라이저", "displayNameEn": "Visual Realizer", "icon": "image", "color": "amber", "stage": "production"},
            "4d": {"toolId": "reference_analyzer", "displayName": "레퍼런스 해석기", "displayNameEn": "Reference Decoder", "icon": "film", "color": "cyan", "stage": "planning"},
            "qc": {"toolId": "quality_check", "displayName": "퀄리티 디렉터", "displayNameEn": "Quality Director", "icon": "check-circle", "color": "rose", "stage": "finishing"},
            "ad": {"toolId": "aesthetic_direct", "displayName": "미학디렉터", "displayNameEn": "Aesthetic Director", "icon": "palette", "color": "fuchsia", "stage": "planning"},
            "ai": {"toolId": "persona_analyze", "displayName": "심연의 거울", "displayNameEn": "Abyss Mirror", "icon": "moon", "color": "indigo", "stage": "planning"},
            "veo": {"toolId": "veo_generate", "displayName": "비디오 메이커", "displayNameEn": "Video Maker", "icon": "video", "color": "sky", "stage": "production"},
            "sound": {"toolId": "sound_craft", "displayName": "사운드 크래프터", "displayNameEn": "Sound Crafter", "icon": "music", "color": "purple", "stage": "production"},
            "story": {"toolId": "story_architect", "displayName": "스토리 아키텍트", "displayNameEn": "Story Architect", "icon": "book-open", "color": "emerald", "stage": "planning"},
        }
        
        for app in dimension_apps:
            name = app.metadata.name.lower()
            display_info = DIMENSION_DISPLAY.get(name, {})
            
            # Get execution capability config
            exec_cap = app.get_capability("execution")
            exec_config = exec_cap.config if exec_cap else {}
            
            tool = {
                "toolId": display_info.get("toolId", name),
                "dimension": name.upper(),
                "displayName": display_info.get("displayName", app.display.name_ko),
                "displayNameEn": display_info.get("displayNameEn", app.display.name_en),
                "description": app.display.description or "",
                "icon": display_info.get("icon", "sparkles"),
                "color": display_info.get("color", "gray"),
                "stage": display_info.get("stage", "production"),
                "capsuleKey": exec_config.get("capsule_key", ""),
                "endpoint": exec_config.get("endpoint", ""),
                "creditCost": exec_config.get("credit_cost", 5),
            }
            tools.append(tool)
        
        if tools:
            # Build toolsById map
            tools_by_id = {tool["toolId"]: tool for tool in tools}
            return {
                "tools": tools,
                "toolsById": tools_by_id,
                "stageOrder": ["planning", "pre_production", "production", "finishing"],
                "source": "appregistry",  # Debug: indicate SSoT source
            }
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"AppRegistry load failed, using fallback: {e}")
    
    # Fallback: hardcoded tools (for backward compatibility)
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
        "source": "fallback",  # Debug: indicate fallback was used
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
