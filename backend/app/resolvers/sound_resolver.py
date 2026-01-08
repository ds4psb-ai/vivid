"""
Sound Crafter Capsule Resolver

사운드/음악 생성 캡슐의 Intent → Params 해석기.
BGM, 효과음, 음악 스타일을 Intent 기반으로 결정합니다.
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


class SoundResolver(BaseCapsuleResolver):
    """
    SOUND (Sound Crafter) Dimension Resolver
    
    사운드/음악 생성을 위한 Intent 해석기.
    mood/pace에 따라 음악 장르, 템포, 분위기를 결정합니다.
    """
    
    dimension_code = "SOUND"
    dimension_name = "사운드 크래프터"
    
    # =========================================================================
    # Intent → Params 매핑
    # =========================================================================
    
    INTENT_MAP = {
        "cinematic": {
            "genre": "orchestral",
            "mood_tag": "epic",
            "tempo": "moderate",
            "dynamics": "wide",
            "reverb": "hall",
            "instruments": ["strings", "brass", "percussion"],
        },
        
        "energetic": {
            "genre": "electronic",
            "mood_tag": "upbeat",
            "tempo": "fast",
            "dynamics": "punchy",
            "reverb": "tight",
            "instruments": ["synth", "drums", "bass"],
        },
        
        "calm": {
            "genre": "ambient",
            "mood_tag": "peaceful",
            "tempo": "slow",
            "dynamics": "soft",
            "reverb": "spacious",
            "instruments": ["piano", "pads", "nature_sounds"],
        },
        
        "documentary": {
            "genre": "minimal",
            "mood_tag": "neutral",
            "tempo": "moderate",
            "dynamics": "subtle",
            "reverb": "natural",
            "instruments": ["piano", "strings_minimal"],
        },
        
        "experimental": {
            "genre": "experimental",
            "mood_tag": "abstract",
            "tempo": "variable",
            "dynamics": "unpredictable",
            "reverb": "processed",
            "instruments": ["synth", "glitch", "found_sounds"],
        },
        
        "nostalgic": {
            "genre": "vintage",
            "mood_tag": "warm",
            "tempo": "relaxed",
            "dynamics": "smooth",
            "reverb": "tape_warmth",
            "instruments": ["acoustic_guitar", "vintage_keys", "light_percussion"],
            "vinyl_crackle": True,
        },
        
        "dark": {
            "genre": "dark_ambient",
            "mood_tag": "tense",
            "tempo": "slow",
            "dynamics": "brooding",
            "reverb": "cavernous",
            "instruments": ["low_drones", "dissonant_strings", "sub_bass"],
        },
        
        "whimsical": {
            "genre": "playful",
            "mood_tag": "fun",
            "tempo": "bouncy",
            "dynamics": "lively",
            "reverb": "bright",
            "instruments": ["xylophone", "pizzicato", "bells", "woodwinds"],
        },
    }
    
    # Pace별 조정
    PACE_ADJUSTMENTS = {
        "fast": {
            "tempo": "fast",
            "bpm_range": [120, 160],
            "energy_level": "high",
        },
        "slow": {
            "tempo": "slow",
            "bpm_range": [60, 80],
            "energy_level": "low",
        },
        "dynamic": {
            "tempo": "variable",
            "bpm_range": [80, 140],
            "energy_level": "variable",
        },
        "contemplative": {
            "tempo": "very_slow",
            "bpm_range": [50, 70],
            "energy_level": "minimal",
        },
    }
    
    # Target별 조정
    TARGET_ADJUSTMENTS = {
        "expert": {
            "complexity": "high",
            "layering": "rich",
        },
        "beginner": {
            "complexity": "simple",
            "layering": "minimal",
        },
        "general": {
            "complexity": "moderate",
        },
        "kids": {
            "mood_tag": "cheerful",
            "tempo": "moderate",
            "volume_level": "gentle",
        },
        "professional": {
            "quality": "broadcast",
            "mix_clarity": "high",
        },
    }
    
    # =========================================================================
    # Resolution Implementation
    # =========================================================================
    
    def get_default_params(self) -> Dict[str, Any]:
        """기본 SOUND 파라미터"""
        return {
            "genre": "ambient",
            "mood_tag": "neutral",
            "tempo": "moderate",
            "dynamics": "medium",
            "reverb": "natural",
            "instruments": ["piano", "pads"],
        }
    
    async def resolve_from_intent(
        self,
        intent: CreativeIntent,
        rag_context: Optional[Dict[str, Any]] = None,
    ) -> ResolvedParams:
        """CreativeIntent를 SOUND 파라미터로 변환"""
        notes = []
        
        # 1. Base params from mood
        params = self._get_base_params(intent.mood)
        notes.append(f"Base from mood={intent.mood.value}")
        
        # 2. Pace adjustments
        params = self._apply_pace_adjustments(params, intent.pace)
        notes.append(f"Pace adjusted: {intent.pace.value}")
        
        # 3. Target adjustments
        params = self._apply_target_adjustments(params, intent.target)
        notes.append(f"Target adjusted: {intent.target.value}")
        
        # 4. Special source handling (사주 기반)
        params = self._apply_special_sources(params, intent)
        
        # 5. RAG hints
        params = self._apply_rag_hints(params, rag_context)
        if rag_context:
            notes.append("RAG context applied")
        
        return ResolvedParams(
            params=params,
            rag_context=rag_context,
            resolved_from="intent",
            confidence=0.9,
            resolution_notes=notes,
        )
    
    def _apply_special_sources(
        self, 
        params: Dict[str, Any],
        intent: CreativeIntent,
    ) -> Dict[str, Any]:
        """특수 소스 (사주/주역 등) 기반 조정"""
        from app.schemas.creative_intent import ContentDomain
        
        if ContentDomain.SOURCE_SAJU in intent.domain_sources:
            # 사주 소스가 있으면 동양적 요소 추가
            logger.debug("Applying saju-based sound elements")
            params = params.copy()
            params["additional_instruments"] = ["guqin", "bamboo_flute", "temple_bells"]
            params["harmonic_mode"] = "pentatonic"
        
        if ContentDomain.SOURCE_PHILOSOPHY in intent.domain_sources:
            params = params.copy()
            params["mood_tag"] = "contemplative"
            params["space"] = "meditative"
        
        return params


# Singleton instance
sound_resolver = SoundResolver()
