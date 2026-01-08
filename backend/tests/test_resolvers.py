"""
Tests for Capsule Resolvers

Phase 2 검증: Resolver 동작, Intent 해석, Registry 기능 테스트
"""
import pytest
from typing import Dict, Any

from app.resolvers import (
    get_resolver,
    get_all_resolvers,
    list_dimensions,
    resolve_intent_for_dimension,
    resolve_intent_for_all,
    register_resolver,
    unregister_resolver,
)
from app.resolvers.base import BaseCapsuleResolver, ResolvedParams
from app.resolvers.veo_resolver import VEOResolver
from app.resolvers.sound_resolver import SoundResolver
from app.resolvers.prompt_resolver import PromptResolver
from app.schemas.creative_intent import (
    CreativeIntent,
    CreativeMood,
    CreativePace,
    TargetAudience,
    ContentDomain,
    IntentFactory,
    AestheticHints,
)


class TestResolverRegistry:
    """Resolver Registry 테스트"""
    
    def test_list_dimensions(self):
        """등록된 Dimension 목록"""
        dims = list_dimensions()
        
        assert "VEO" in dims
        assert "SOUND" in dims
        assert "1D" in dims
    
    def test_get_resolver(self):
        """Resolver 조회"""
        veo = get_resolver("VEO")
        sound = get_resolver("SOUND")
        
        assert isinstance(veo, VEOResolver)
        assert isinstance(sound, SoundResolver)
    
    def test_get_resolver_case_insensitive(self):
        """Resolver 조회 - 대소문자 무관"""
        veo1 = get_resolver("veo")
        veo2 = get_resolver("VEO")
        
        assert veo1 is veo2
    
    def test_get_invalid_resolver(self):
        """존재하지 않는 Resolver"""
        resolver = get_resolver("INVALID")
        assert resolver is None
    
    def test_get_all_resolvers(self):
        """모든 Resolver 조회"""
        all_resolvers = get_all_resolvers()
        
        assert len(all_resolvers) >= 3
        assert all(isinstance(r, BaseCapsuleResolver) for r in all_resolvers.values())


class TestVEOResolver:
    """VEO Resolver 테스트"""
    
    @pytest.fixture
    def resolver(self):
        return VEOResolver()
    
    @pytest.mark.asyncio
    async def test_cinematic_mood(self, resolver):
        """Cinematic mood 해석"""
        intent = CreativeIntent(mood=CreativeMood.CINEMATIC)
        result = await resolver.resolve_from_intent(intent)
        
        assert result.params["aspect_ratio"] == "21:9"
        assert result.params["camera_style"] == "cinematic"
        assert result.params["lens_style"] == "anamorphic"
    
    @pytest.mark.asyncio
    async def test_energetic_mood(self, resolver):
        """Energetic mood 해석"""
        intent = CreativeIntent(
            mood=CreativeMood.ENERGETIC,
            pace=CreativePace.FAST,  # Explicit fast pace
        )
        result = await resolver.resolve_from_intent(intent)
        
        assert result.params["motion_intensity"] == "high"
        assert result.params["lens_style"] == "wide"
    
    @pytest.mark.asyncio
    async def test_pace_adjustment(self, resolver):
        """Pace 조정 적용"""
        intent = CreativeIntent(
            mood=CreativeMood.CINEMATIC,
            pace=CreativePace.FAST,
        )
        result = await resolver.resolve_from_intent(intent)
        
        assert result.params["duration"] == 4  # fast pace = shorter
    
    @pytest.mark.asyncio
    async def test_target_adjustment(self, resolver):
        """Target 조정 적용"""
        intent = CreativeIntent(
            mood=CreativeMood.CINEMATIC,
            target=TargetAudience.KIDS,
        )
        result = await resolver.resolve_from_intent(intent)
        
        assert result.params["brightness"] == "high"
    
    @pytest.mark.asyncio
    async def test_auteur_style_bong(self, resolver):
        """봉준호 스타일 적용"""
        intent = CreativeIntent(
            mood=CreativeMood.CINEMATIC,
            domain_sources=[ContentDomain.AUTEUR_BONG],
        )
        result = await resolver.resolve_from_intent(intent)
        
        assert result.params["composition"] == "symmetrical"
        assert "Auteur style applied" in result.resolution_notes
    
    @pytest.mark.asyncio
    async def test_auteur_style_wong(self, resolver):
        """왕가위 스타일 적용"""
        intent = CreativeIntent(
            mood=CreativeMood.NOSTALGIC,
            domain_sources=[ContentDomain.AUTEUR_WONG],
        )
        result = await resolver.resolve_from_intent(intent)
        
        assert result.params["color_grade"] == "neon_noir"
        assert result.params.get("slow_motion") is True
    
    @pytest.mark.asyncio
    async def test_aesthetic_hints(self, resolver):
        """AestheticHints 적용"""
        intent = CreativeIntent(
            mood=CreativeMood.CINEMATIC,
            aesthetic_hints=AestheticHints(
                color_temperature="cool",
                lighting_style="low-key",
            ),
        )
        result = await resolver.resolve_from_intent(intent)
        
        assert result.params["color_temperature"] == "cool"
        assert result.params["lighting_style"] == "low-key"
    
    def test_default_params(self, resolver):
        """기본 파라미터"""
        defaults = resolver.get_default_params()
        
        assert "aspect_ratio" in defaults
        assert "duration" in defaults


class TestSoundResolver:
    """Sound Resolver 테스트"""
    
    @pytest.fixture
    def resolver(self):
        return SoundResolver()
    
    @pytest.mark.asyncio
    async def test_cinematic_sound(self, resolver):
        """Cinematic 사운드 해석"""
        intent = CreativeIntent(mood=CreativeMood.CINEMATIC)
        result = await resolver.resolve_from_intent(intent)
        
        assert result.params["genre"] == "orchestral"
        assert "strings" in result.params["instruments"]
    
    @pytest.mark.asyncio
    async def test_energetic_sound(self, resolver):
        """Energetic 사운드 해석"""
        intent = CreativeIntent(
            mood=CreativeMood.ENERGETIC,
            pace=CreativePace.FAST,  # Explicit fast pace
        )
        result = await resolver.resolve_from_intent(intent)
        
        assert result.params["genre"] == "electronic"
        assert result.params["tempo"] == "fast"
    
    @pytest.mark.asyncio
    async def test_saju_source(self, resolver):
        """사주 소스 적용"""
        intent = CreativeIntent(
            mood=CreativeMood.CALM,
            domain_sources=[ContentDomain.SOURCE_SAJU],
        )
        result = await resolver.resolve_from_intent(intent)
        
        assert "guqin" in result.params.get("additional_instruments", [])
        assert result.params.get("harmonic_mode") == "pentatonic"


class TestPromptResolver:
    """Prompt Resolver 테스트"""
    
    @pytest.fixture
    def resolver(self):
        return PromptResolver()
    
    @pytest.mark.asyncio
    async def test_expert_target(self, resolver):
        """전문가 대상 프롬프트"""
        intent = CreativeIntent(
            mood=CreativeMood.CINEMATIC,
            target=TargetAudience.EXPERT,
        )
        result = await resolver.resolve_from_intent(intent)
        
        assert result.params["detail_level"] == "very_high"
        assert result.params["technical_terms"] is True
    
    @pytest.mark.asyncio
    async def test_beginner_target(self, resolver):
        """초보자 대상 프롬프트"""
        intent = CreativeIntent(
            mood=CreativeMood.CALM,
            target=TargetAudience.BEGINNER,
        )
        result = await resolver.resolve_from_intent(intent)
        
        assert result.params["detail_level"] == "low"
        assert result.params["simplify"] is True
    
    @pytest.mark.asyncio
    async def test_keywords_applied(self, resolver):
        """키워드 반영"""
        intent = CreativeIntent(
            mood=CreativeMood.DARK,
            keywords=["tension", "shadow", "mystery"],
        )
        result = await resolver.resolve_from_intent(intent)
        
        assert "tension" in result.params.get("emphasis", [])


class TestResolveIntentForAll:
    """전체 Dimension 해석 테스트"""
    
    @pytest.mark.asyncio
    async def test_resolve_all_dimensions(self):
        """모든 등록된 Dimension 해석"""
        intent = IntentFactory.cinematic_bong()
        results = await resolve_intent_for_all(intent)
        
        assert "VEO" in results
        assert "SOUND" in results
        assert "1D" in results
        
        assert all(isinstance(r, ResolvedParams) for r in results.values())
    
    @pytest.mark.asyncio
    async def test_resolve_specific_dimensions(self):
        """특정 Dimension만 해석"""
        intent = CreativeIntent(mood=CreativeMood.CALM)
        results = await resolve_intent_for_all(intent, dimensions=["VEO", "SOUND"])
        
        assert "VEO" in results
        assert "SOUND" in results
        assert "1D" not in results


class TestResolvedParams:
    """ResolvedParams 테스트"""
    
    def test_merge_with(self):
        """파라미터 병합"""
        params1 = ResolvedParams(
            params={"a": 1, "b": 2},
            resolved_from="intent",
        )
        
        merged = params1.merge_with({"b": 3, "c": 4})
        
        assert merged.params["a"] == 1
        assert merged.params["b"] == 3  # 덮어씀
        assert merged.params["c"] == 4


class TestFallbackBehavior:
    """Fallback 동작 테스트"""
    
    @pytest.mark.asyncio
    async def test_legacy_params_priority(self):
        """레거시 파라미터 우선"""
        resolver = VEOResolver()
        intent = CreativeIntent(mood=CreativeMood.CINEMATIC)
        legacy = {"aspect_ratio": "4:3", "custom": "value"}
        
        result = await resolver.resolve_with_fallback(
            intent=intent,
            legacy_params=legacy,
        )
        
        assert result.resolved_from == "legacy"
        assert result.params["aspect_ratio"] == "4:3"
    
    @pytest.mark.asyncio
    async def test_no_intent_fallback(self):
        """Intent 없을 때 기본값"""
        resolver = VEOResolver()
        
        result = await resolver.resolve_with_fallback(intent=None)
        
        assert result.resolved_from == "fallback"
        assert "aspect_ratio" in result.params
