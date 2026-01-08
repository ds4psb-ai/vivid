"""
Prompt Director Capsule Resolver

프롬프트 생성 캡슐의 Intent → Params 해석기.
LLM 프롬프트의 톤, 복잡도, 스타일을 Intent 기반으로 결정합니다.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
import logging

from app.resolvers.base import BaseCapsuleResolver, ResolvedParams
from app.schemas.creative_intent import (
    CreativeIntent, 
    CreativeMood, 
    CreativePace, 
    TargetAudience,
)

logger = logging.getLogger(__name__)


class PromptResolver(BaseCapsuleResolver):
    """
    1D (Prompt Director) Dimension Resolver
    
    Veo 프롬프트 생성을 위한 Intent 해석기.
    mood/target에 따라 프롬프트의 톤, 디테일 수준, 문체를 결정합니다.
    """
    
    dimension_code = "1D"
    dimension_name = "프롬프트 디렉터"
    
    # =========================================================================
    # Intent → Params 매핑
    # =========================================================================
    
    INTENT_MAP = {
        "cinematic": {
            "tone": "dramatic",
            "detail_level": "high",
            "style": "narrative",
            "emphasis": ["atmosphere", "lighting", "composition"],
            "vocabulary": "filmic",
        },
        
        "energetic": {
            "tone": "dynamic",
            "detail_level": "medium",
            "style": "action",
            "emphasis": ["motion", "energy", "rhythm"],
            "vocabulary": "punchy",
        },
        
        "calm": {
            "tone": "serene",
            "detail_level": "medium",
            "style": "descriptive",
            "emphasis": ["peace", "nature", "stillness"],
            "vocabulary": "gentle",
        },
        
        "documentary": {
            "tone": "objective",
            "detail_level": "high",
            "style": "factual",
            "emphasis": ["authenticity", "detail", "context"],
            "vocabulary": "precise",
        },
        
        "experimental": {
            "tone": "avant_garde",
            "detail_level": "variable",
            "style": "abstract",
            "emphasis": ["uniqueness", "surprise", "texture"],
            "vocabulary": "creative",
        },
        
        "nostalgic": {
            "tone": "warm",
            "detail_level": "medium",
            "style": "evocative",
            "emphasis": ["memory", "emotion", "authenticity"],
            "vocabulary": "sentimental",
        },
        
        "dark": {
            "tone": "ominous",
            "detail_level": "high",
            "style": "atmospheric",
            "emphasis": ["shadow", "tension", "contrast"],
            "vocabulary": "dramatic",
        },
        
        "whimsical": {
            "tone": "playful",
            "detail_level": "medium",
            "style": "imaginative",
            "emphasis": ["fun", "color", "fantasy"],
            "vocabulary": "whimsical",
        },
    }
    
    # Target별 조정 - 프롬프트 복잡도에 영향
    TARGET_ADJUSTMENTS = {
        "expert": {
            "detail_level": "very_high",
            "technical_terms": True,
            "prompt_length": "long",
            "include_camera_specs": True,
        },
        "beginner": {
            "detail_level": "low",
            "technical_terms": False,
            "prompt_length": "short",
            "simplify": True,
        },
        "general": {
            "detail_level": "medium",
            "prompt_length": "medium",
        },
        "kids": {
            "detail_level": "simple",
            "tone": "cheerful",
            "vocabulary": "simple",
            "prompt_length": "short",
        },
        "professional": {
            "detail_level": "high",
            "technical_terms": True,
            "prompt_length": "detailed",
            "output_format": "structured",
        },
    }
    
    # Pace별 조정 - 프롬프트 톤에 영향
    PACE_ADJUSTMENTS = {
        "fast": {
            "sentence_structure": "short",
            "action_words": True,
        },
        "slow": {
            "sentence_structure": "flowing",
            "descriptive_depth": "high",
        },
        "dynamic": {
            "sentence_structure": "varied",
        },
        "contemplative": {
            "sentence_structure": "poetic",
            "introspective": True,
        },
    }
    
    # =========================================================================
    # Resolution Implementation
    # =========================================================================
    
    def get_default_params(self) -> Dict[str, Any]:
        """기본 프롬프트 파라미터"""
        return {
            "tone": "neutral",
            "detail_level": "medium",
            "style": "descriptive",
            "emphasis": ["visual", "atmosphere"],
            "vocabulary": "standard",
            "prompt_length": "medium",
        }
    
    async def resolve_from_intent(
        self,
        intent: CreativeIntent,
        rag_context: Optional[Dict[str, Any]] = None,
    ) -> ResolvedParams:
        """CreativeIntent를 프롬프트 생성 파라미터로 변환"""
        notes = []
        
        # 1. Base params from mood
        params = self._get_base_params(intent.mood)
        notes.append(f"Base from mood={intent.mood.value}")
        
        # 2. Target adjustments (매우 중요 - 프롬프트 복잡도 결정)
        params = self._apply_target_adjustments(params, intent.target)
        notes.append(f"Target adjusted: {intent.target.value}")
        
        # 3. Pace adjustments
        params = self._apply_pace_adjustments(params, intent.pace)
        notes.append(f"Pace adjusted: {intent.pace.value}")
        
        # 4. Keywords 반영
        if intent.keywords:
            params["emphasis"] = params.get("emphasis", []) + intent.keywords[:3]
            notes.append(f"Keywords added: {intent.keywords[:3]}")
        
        # 5. Custom notes 반영
        if intent.custom_notes:
            params["user_direction"] = intent.custom_notes
            notes.append("Custom notes included")
        
        # 6. RAG hints
        params = self._apply_rag_hints(params, rag_context)
        if rag_context:
            notes.append("RAG context applied")
        
        return ResolvedParams(
            params=params,
            rag_context=rag_context,
            resolved_from="intent",
            confidence=0.92,
            resolution_notes=notes,
        )


# Singleton instance
prompt_resolver = PromptResolver()
