"""
VEO (Video Maker) Capsule Resolver

비디오 생성 캡슐의 Intent → Params 해석기.
Veo 3.1 API 파라미터를 Intent 기반으로 최적화합니다.
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
    ContentDomain,
)

logger = logging.getLogger(__name__)


class VEOResolver(BaseCapsuleResolver):
    """
    VEO (Video Maker) Dimension Resolver
    
    Veo 3.1 비디오 생성을 위한 Intent 해석기.
    mood/pace/target에 따라 최적의 영상 스타일 파라미터를 결정합니다.
    """
    
    dimension_code = "VEO"
    dimension_name = "비디오 메이커"
    
    # =========================================================================
    # Intent → Params 매핑
    # =========================================================================
    
    INTENT_MAP = {
        # Cinematic - 영화적, 21:9, 느린 동작, 깊이감
        "cinematic": {
            "aspect_ratio": "21:9",
            "duration": 8,
            "camera_style": "cinematic",
            "lens_style": "anamorphic",
            "color_grade": "filmic",
            "motion_intensity": "subtle",
            "depth_of_field": "shallow",
        },
        
        # Energetic - 역동적, 빠른 동작, 넓은 화각
        "energetic": {
            "aspect_ratio": "16:9",
            "duration": 6,
            "camera_style": "dynamic",
            "lens_style": "wide",
            "color_grade": "vibrant",
            "motion_intensity": "high",
            "depth_of_field": "deep",
        },
        
        # Calm - 차분한, 느린 호흡, 자연광
        "calm": {
            "aspect_ratio": "16:9",
            "duration": 8,
            "camera_style": "static",
            "lens_style": "natural",
            "color_grade": "soft",
            "motion_intensity": "minimal",
            "depth_of_field": "medium",
        },
        
        # Documentary - 다큐멘터리, 자연스러운, 핸드헬드
        "documentary": {
            "aspect_ratio": "16:9",
            "duration": 6,
            "camera_style": "handheld",
            "lens_style": "natural",
            "color_grade": "neutral",
            "motion_intensity": "organic",
            "depth_of_field": "deep",
        },
        
        # Experimental - 실험적, 예측불가, 왜곡
        "experimental": {
            "aspect_ratio": "1:1",
            "duration": 4,
            "camera_style": "abstract",
            "lens_style": "fisheye",
            "color_grade": "stylized",
            "motion_intensity": "variable",
            "depth_of_field": "variable",
        },
        
        # Nostalgic - 레트로, 필름 그레인, 따뜻한 색감
        "nostalgic": {
            "aspect_ratio": "4:3",
            "duration": 6,
            "camera_style": "vintage",
            "lens_style": "vintage",
            "color_grade": "warm_vintage",
            "motion_intensity": "gentle",
            "depth_of_field": "soft",
            "film_grain": True,
        },
        
        # Dark - 어둡고 무거운, 로우키, 하이 콘트라스트
        "dark": {
            "aspect_ratio": "21:9",
            "duration": 8,
            "camera_style": "ominous",
            "lens_style": "anamorphic",
            "color_grade": "dark_contrast",
            "motion_intensity": "slow",
            "depth_of_field": "shallow",
            "lighting_style": "low_key",
        },
        
        # Whimsical - 기발한, 밝은, 애니메이션적
        "whimsical": {
            "aspect_ratio": "16:9",
            "duration": 6,
            "camera_style": "playful",
            "lens_style": "wide",
            "color_grade": "saturated",
            "motion_intensity": "bouncy",
            "depth_of_field": "deep",
        },
    }
    
    # Pace별 조정
    PACE_ADJUSTMENTS = {
        "fast": {
            "duration": 4,  # 짧은 영상
            "motion_intensity": "high",
            "cut_frequency": "quick",
        },
        "slow": {
            "duration": 8,  # 긴 영상
            "motion_intensity": "subtle",
            "cut_frequency": "long_take",
        },
        "dynamic": {
            "duration": 6,
            "motion_intensity": "variable",
            "cut_frequency": "mixed",
        },
        "contemplative": {
            "duration": 8,
            "motion_intensity": "minimal",
            "cut_frequency": "very_long",
        },
    }
    
    # Target별 조정
    TARGET_ADJUSTMENTS = {
        "expert": {
            "complexity": "high",
            "technical_control": True,
        },
        "beginner": {
            "complexity": "low",
            "auto_enhance": True,
        },
        "general": {
            "complexity": "medium",
        },
        "kids": {
            "brightness": "high",
            "color_grade": "bright",
            "motion_intensity": "gentle",
        },
        "professional": {
            "quality_preset": "high",
            "export_format": "prores",
        },
    }
    
    # =========================================================================
    # Auteur-specific Overrides
    # =========================================================================
    
    AUTEUR_STYLES = {
        "bong-joon-ho": {
            "aspect_ratio": "21:9",
            "camera_style": "composed",
            "lens_style": "anamorphic",
            "color_grade": "muted_contrast",
            "depth_of_field": "deep",
            "composition": "symmetrical",
        },
        "tarantino": {
            "aspect_ratio": "21:9",
            "camera_style": "bold",
            "lens_style": "wide",
            "color_grade": "saturated_retro",
            "motion_intensity": "punchy",
        },
        "nolan": {
            "aspect_ratio": "21:9",
            "camera_style": "epic",
            "lens_style": "imax",
            "color_grade": "cold_teal",
            "motion_intensity": "precise",
        },
        "villeneuve": {
            "aspect_ratio": "21:9",
            "camera_style": "atmospheric",
            "lens_style": "large_format",
            "color_grade": "desaturated",
            "motion_intensity": "slow",
        },
        "wong-kar-wai": {
            "aspect_ratio": "16:9",
            "camera_style": "intimate",
            "lens_style": "vintage",
            "color_grade": "neon_noir",
            "motion_intensity": "dreamy",
            "slow_motion": True,
        },
    }
    
    # =========================================================================
    # Resolution Implementation
    # =========================================================================
    
    def get_default_params(self) -> Dict[str, Any]:
        """기본 VEO 파라미터"""
        return {
            "aspect_ratio": "16:9",
            "duration": 6,
            "camera_style": "natural",
            "lens_style": "standard",
            "color_grade": "neutral",
            "motion_intensity": "medium",
            "depth_of_field": "medium",
        }
    
    async def resolve_from_intent(
        self,
        intent: CreativeIntent,
        rag_context: Optional[Dict[str, Any]] = None,
    ) -> ResolvedParams:
        """
        CreativeIntent를 VEO 파라미터로 변환
        
        해석 순서:
        1. mood에서 기본 스타일 가져오기
        2. pace에 따른 시간/리듬 조정
        3. target에 따른 복잡도 조정
        4. auteur source가 있으면 스타일 오버라이드
        5. RAG 컨텍스트 힌트 적용
        """
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
        
        # 4. Auteur style override
        auteur_applied = self._apply_auteur_style(params, intent)
        if auteur_applied != params:
            params = auteur_applied
            notes.append("Auteur style applied")
        
        # 5. RAG hints
        params = self._apply_rag_hints(params, rag_context)
        if rag_context:
            notes.append("RAG context applied")
        
        # 6. Aesthetic hints from intent
        if intent.aesthetic_hints:
            params = self._apply_aesthetic_hints(params, intent)
            notes.append("Aesthetic hints applied")
        
        return ResolvedParams(
            params=params,
            rag_context=rag_context,
            resolved_from="intent",
            confidence=0.95,
            resolution_notes=notes,
        )
    
    def _apply_auteur_style(
        self, 
        params: Dict[str, Any], 
        intent: CreativeIntent
    ) -> Dict[str, Any]:
        """거장 스타일 적용"""
        for domain in intent.domain_sources:
            if domain.value in self.AUTEUR_STYLES:
                auteur_params = self.AUTEUR_STYLES[domain.value]
                logger.debug(f"Applying auteur style: {domain.value}")
                return {**params, **auteur_params}
        return params
    
    def _apply_aesthetic_hints(
        self,
        params: Dict[str, Any],
        intent: CreativeIntent,
    ) -> Dict[str, Any]:
        """AestheticHints에서 VEO 파라미터 추출"""
        hints = intent.aesthetic_hints
        if not hints:
            return params
        
        result = params.copy()
        
        if hints.color_temperature:
            result["color_temperature"] = hints.color_temperature
        
        if hints.lighting_style:
            result["lighting_style"] = hints.lighting_style
        
        if hints.composition_style:
            result["composition"] = hints.composition_style
        
        if hints.texture_feel:
            result["texture"] = hints.texture_feel
        
        return result


# Singleton instance
veo_resolver = VEOResolver()
