"""
Intent-Resolver Integration Layer

dimension_adapter.py의 기존 캡슐 함수들과 
Resolver 시스템을 연결하는 통합 레이어.

이 모듈은:
1. CreativeIntent → Resolver → dimension_adapter 파라미터 변환
2. 기존 RAG 시스템과 Resolver RAG 컨텍스트 통합
3. input_preset에서 Intent 추출
"""
from __future__ import annotations

from typing import Any, Dict, Optional
import logging

from app.schemas.creative_intent import (
    CreativeIntent,
    CreativeMood,
    CreativePace,
    TargetAudience,
    ContentDomain,
    TemplateIntentPreset,
)
from app.resolvers import (
    get_resolver,
    resolve_intent_for_dimension,
    ResolvedParams,
)

logger = logging.getLogger(__name__)


# =========================================================================
# Intent Extraction from Template Presets
# =========================================================================

def extract_intent_from_preset(
    input_preset: Dict[str, Any]
) -> Optional[CreativeIntent]:
    """
    템플릿 input_preset에서 Intent 추출
    
    AS-IS 형식 (legacy):
        {"veo_model": "veo-2", "veo_aspect_ratio": "21:9", "mood": "cinematic"}
    
    TO-BE 형식 (new):
        {"intent": {...}, "schema_version": "2.0"}
    
    Returns:
        CreativeIntent or None
    """
    if not input_preset:
        return None
    
    # 신규 형식 체크
    if "intent" in input_preset and "schema_version" in input_preset:
        try:
            preset = TemplateIntentPreset.model_validate(input_preset)
            return preset.intent
        except Exception as e:
            logger.warning(f"Failed to parse new format preset: {e}")
    
    # Legacy 형식: mood/style에서 Intent 유추
    mood_value = input_preset.get("mood", "").lower()
    style_value = input_preset.get("style", "").lower()
    
    # Mood 매핑
    mood_map = {
        "cinematic": CreativeMood.CINEMATIC,
        "energetic": CreativeMood.ENERGETIC,
        "calm": CreativeMood.CALM,
        "documentary": CreativeMood.DOCUMENTARY,
        "experimental": CreativeMood.EXPERIMENTAL,
        "nostalgic": CreativeMood.NOSTALGIC,
        "dark": CreativeMood.DARK,
        "whimsical": CreativeMood.WHIMSICAL,
    }
    
    inferred_mood = mood_map.get(mood_value) or mood_map.get(style_value)
    
    if inferred_mood:
        # Legacy에서 유추한 Intent 생성
        intent = CreativeIntent(
            mood=inferred_mood,
            pace=CreativePace.DYNAMIC,  # 기본값
            target=TargetAudience.GENERAL,  # 기본값
        )
        logger.debug(f"Inferred intent from legacy preset: mood={inferred_mood.value}")
        return intent
    
    return None


# =========================================================================
# Resolver-Enhanced Parameter Generation
# =========================================================================

async def get_enhanced_capsule_params(
    dimension_code: str,
    input_preset: Optional[Dict[str, Any]] = None,
    explicit_intent: Optional[CreativeIntent] = None,
    rag_context: Optional[Dict[str, Any]] = None,
    query: Optional[str] = None,  # RAG 조회용 쿼리
) -> Dict[str, Any]:
    """
    Intent + Resolver를 사용한 캡슐 파라미터 생성
    
    우선순위:
    1. explicit_intent가 있으면 사용
    2. input_preset에서 intent 추출 시도
    3. Resolver로 파라미터 생성
    4. intent가 없으면 empty params
    
    Args:
        dimension_code: 대상 Dimension (e.g., "VEO", "1D", "SOUND")
        input_preset: 템플릿의 input_preset
        explicit_intent: 직접 전달된 Intent (우선)
        rag_context: RAG 시스템에서 가져온 컨텍스트 (직접 제공)
        query: RAG 조회용 쿼리 (intent.domain_sources 기반 자동 조회)
        
    Returns:
        최종 캡슐 실행 파라미터
    """
    # 1. Intent 결정
    if explicit_intent:
        intent = explicit_intent
    else:
        intent = extract_intent_from_preset(input_preset or {})
    
    # 2. RAG Context 자동 조회 (Phase 4: Source Resolver)
    if intent and query and not rag_context:
        try:
            from app.resolvers.source_resolver import get_intent_rag_context
            rag_context = await get_intent_rag_context(intent, query)
            logger.debug(f"[{dimension_code}] RAG context from sources: {rag_context.get('sources_used', [])}")
        except ImportError:
            logger.debug("Source resolver not available")
        except Exception as e:
            logger.warning(f"Source resolver failed: {e}")
    
    # 3. Resolver로 파라미터 생성
    resolver = get_resolver(dimension_code)
    
    if resolver and intent:
        try:
            resolved = await resolver.resolve_with_fallback(
                intent=intent,
                rag_context=rag_context,
            )
            
            logger.debug(
                f"[{dimension_code}] Resolved params: "
                f"from={resolved.resolved_from}, "
                f"keys={list(resolved.params.keys())[:5]}"
            )
            
            return resolved.params
            
        except Exception as e:
            logger.warning(f"Resolver failed for {dimension_code}: {e}")
    
    # 4. Fallback: empty params
    return {}


# =========================================================================
# Adapter Function Enhancers
# =========================================================================

def enhance_prompt_generator_params(
    base_params: Dict[str, Any],
    resolved_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Prompt Generator (1D) 파라미터 병합
    
    Resolver에서 생성된 tone, detail_level 등을 
    기존 params와 병합합니다.
    """
    result = base_params.copy()
    
    # Resolver 결과 적용
    if "tone" in resolved_params:
        result["style"] = resolved_params["tone"]
    
    if "detail_level" in resolved_params:
        result["complexity"] = resolved_params["detail_level"]
    
    if "emphasis" in resolved_params:
        result["focus_areas"] = resolved_params["emphasis"]
    
    # 기본값이 없으면 추가
    result.setdefault("style", "cinematic")
    result.setdefault("mood", "neutral")
    
    return result


def enhance_veo_params(
    base_params: Dict[str, Any],
    resolved_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    VEO Video Generator 파라미터 병합
    """
    result = base_params.copy()
    
    # Resolver 결과 직접 적용 (VEO는 직접 사용 가능)
    if "aspect_ratio" in resolved_params:
        result["veo_aspect_ratio"] = resolved_params["aspect_ratio"]
    
    if "duration" in resolved_params:
        result["veo_duration"] = resolved_params["duration"]
    
    if "camera_style" in resolved_params:
        result["camera_style"] = resolved_params["camera_style"]
    
    if "lens_style" in resolved_params:
        result["lens_style"] = resolved_params["lens_style"]
    
    if "color_grade" in resolved_params:
        result["color_grade"] = resolved_params["color_grade"]
    
    # 기본값
    result.setdefault("veo_model", "veo-3.1")
    result.setdefault("veo_aspect_ratio", "16:9")
    
    return result


def enhance_sound_params(
    base_params: Dict[str, Any],
    resolved_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Sound Crafter 파라미터 병합
    """
    result = base_params.copy()
    
    # Resolver 결과 적용
    if "genre" in resolved_params:
        result["music_genre"] = resolved_params["genre"]
    
    if "tempo" in resolved_params:
        result["tempo"] = resolved_params["tempo"]
    
    if "mood_tag" in resolved_params:
        result["mood"] = resolved_params["mood_tag"]
    
    if "instruments" in resolved_params:
        result["preferred_instruments"] = resolved_params["instruments"]
    
    return result


# =========================================================================
# Convenience Functions
# =========================================================================

async def prepare_dimension_params(
    dimension_code: str,
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    intent: Optional[CreativeIntent] = None,
    rag_context: Optional[Dict[str, Any]] = None,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Dimension 캡슐 실행을 위한 파라미터 준비
    
    기존 dimension_adapter.py의 run_* 함수에서 사용:
    
    ```python
    # Before
    style = inputs.get("style", "cinematic")
    
    # After  
    inputs, params = await prepare_dimension_params(
        "1D", inputs, params, intent=intent
    )
    style = inputs.get("style", "cinematic")
    ```
    
    Returns:
        (enhanced_inputs, enhanced_params)
    """
    # Resolver 파라미터 생성
    resolved = await get_enhanced_capsule_params(
        dimension_code=dimension_code,
        input_preset=params,
        explicit_intent=intent,
        rag_context=rag_context,
    )
    
    # Dimension별 파라미터 병합
    enhancers = {
        "1D": enhance_prompt_generator_params,
        "VEO": enhance_veo_params,
        "SOUND": enhance_sound_params,
    }
    
    enhancer = enhancers.get(dimension_code)
    if enhancer:
        # inputs에 resolved params 반영
        enhanced_inputs = enhancer(inputs, resolved)
        enhanced_params = {**params, **resolved}
    else:
        enhanced_inputs = {**inputs, **resolved}
        enhanced_params = {**params, **resolved}
    
    return enhanced_inputs, enhanced_params


# =========================================================================
# Exports
# =========================================================================

__all__ = [
    "extract_intent_from_preset",
    "get_enhanced_capsule_params",
    "prepare_dimension_params",
    "enhance_prompt_generator_params",
    "enhance_veo_params",
    "enhance_sound_params",
]
