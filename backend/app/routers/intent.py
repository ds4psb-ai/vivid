"""
Intent Preset API Router

프론트엔드에서 사용 가능한 Intent 프리셋 목록을 제공하는 API.
"""
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.schemas.creative_intent import IntentFactory, CreativeIntent

router = APIRouter(prefix="/intent", tags=["intent"])


class IntentPresetSummary(BaseModel):
    """프리셋 요약 정보"""
    name: str
    description: str
    mood: str
    pace: str
    target: str
    keywords: List[str]


class IntentPresetListResponse(BaseModel):
    """프리셋 목록 응답"""
    count: int
    presets: List[IntentPresetSummary]


class IntentPresetDetailResponse(BaseModel):
    """프리셋 상세 응답"""
    name: str
    intent: CreativeIntent


@router.get(
    "/presets",
    response_model=IntentPresetListResponse,
    summary="모든 Intent 프리셋 목록",
    description="Singularity 템플릿 및 앱에서 사용 가능한 모든 Intent 프리셋 목록을 반환합니다.",
)
async def list_intent_presets() -> IntentPresetListResponse:
    """모든 Intent 프리셋 목록 반환."""
    all_presets = IntentFactory.get_all_presets()
    
    summaries = []
    for name, factory_fn in all_presets.items():
        intent = factory_fn()
        summaries.append(IntentPresetSummary(
            name=name,
            description=factory_fn.__doc__ or "",
            mood=intent.mood.value if intent.mood else "default",
            pace=intent.pace.value if intent.pace else "default",
            target=intent.target.value if intent.target else "general",
            keywords=intent.keywords or [],
        ))
    
    return IntentPresetListResponse(
        count=len(summaries),
        presets=summaries,
    )


@router.get(
    "/presets/{preset_name}",
    response_model=IntentPresetDetailResponse,
    summary="특정 Intent 프리셋 상세",
    description="이름으로 특정 Intent 프리셋의 전체 정보를 반환합니다.",
    responses={
        404: {"description": "프리셋을 찾을 수 없음"},
    },
)
async def get_intent_preset(preset_name: str) -> IntentPresetDetailResponse:
    """특정 Intent 프리셋 상세 정보 반환."""
    from fastapi import HTTPException
    
    intent = IntentFactory.get_by_name(preset_name)
    if intent is None:
        raise HTTPException(
            status_code=404,
            detail=f"Preset '{preset_name}' not found. Use GET /intent/presets to see available presets.",
        )
    
    return IntentPresetDetailResponse(
        name=preset_name,
        intent=intent,
    )


@router.get(
    "/presets/by-category/{category}",
    response_model=IntentPresetListResponse,
    summary="카테고리별 Intent 프리셋",
    description="카테고리(auteur, platform, general)로 필터링된 프리셋 목록을 반환합니다.",
)
async def list_intent_presets_by_category(
    category: str,
) -> IntentPresetListResponse:
    """카테고리별 Intent 프리셋 목록."""
    all_presets = IntentFactory.get_all_presets()
    
    # 카테고리 분류
    auteur_presets = [
        "cinematic_bong", "cinematic_nolan", "cinematic_villeneuve",
        "cinematic_wong", "horror_na", "arthouse_hong", "animation_shinkai",
    ]
    platform_presets = [
        "shortform_energetic", "music_video", "youtube_tutorial",
        "instagram_reel", "commercial_product",
    ]
    general_presets = ["documentary_calm", "saju_guided"]
    
    if category == "auteur":
        filter_names = auteur_presets
    elif category == "platform":
        filter_names = platform_presets
    elif category == "general":
        filter_names = general_presets
    else:
        # 전체 반환
        filter_names = list(all_presets.keys())
    
    summaries = []
    for name in filter_names:
        factory_fn = all_presets.get(name)
        if factory_fn:
            intent = factory_fn()
            summaries.append(IntentPresetSummary(
                name=name,
                description=factory_fn.__doc__ or "",
                mood=intent.mood.value if intent.mood else "default",
                pace=intent.pace.value if intent.pace else "default",
                target=intent.target.value if intent.target else "general",
                keywords=intent.keywords or [],
            ))
    
    return IntentPresetListResponse(
        count=len(summaries),
        presets=summaries,
    )
