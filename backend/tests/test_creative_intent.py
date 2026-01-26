"""
Tests for Creative Intent Schema

Phase 1 검증: CreativeIntent 스키마의 유효성, 직렬화, 팩토리 프리셋 테스트
"""
import pytest
from datetime import datetime

from app.schemas.creative_intent import (
    CreativeIntent,
    CreativeMood,
    CreativePace,
    TargetAudience,
    ContentDomain,
    OutputFormat,
    AestheticHints,
    IntentMetadata,
    TemplateIntentPreset,
    IntentFactory,
)


class TestCreativeMoodEnum:
    """CreativeMood Enum 테스트"""
    
    def test_all_moods_have_values(self):
        """모든 mood 값이 정의되어 있는지 확인"""
        expected = {"cinematic", "energetic", "calm", "documentary", 
                    "experimental", "nostalgic", "dark", "whimsical"}
        actual = {m.value for m in CreativeMood}
        assert actual == expected
    
    def test_mood_from_string(self):
        """문자열에서 Enum 변환"""
        assert CreativeMood("cinematic") == CreativeMood.CINEMATIC
        assert CreativeMood("energetic") == CreativeMood.ENERGETIC


class TestCreativeIntent:
    """CreativeIntent 핵심 스키마 테스트"""
    
    def test_minimal_intent(self):
        """필수 필드만으로 생성"""
        intent = CreativeIntent(mood=CreativeMood.CINEMATIC)
        
        assert intent.mood == CreativeMood.CINEMATIC
        assert intent.pace == CreativePace.DYNAMIC  # 기본값
        assert intent.target == TargetAudience.GENERAL  # 기본값
        assert intent.domain_sources == []
        assert intent.metadata.intent_id is not None
    
    def test_full_intent(self):
        """모든 필드를 채운 Intent"""
        intent = CreativeIntent(
            mood=CreativeMood.CINEMATIC,
            pace=CreativePace.SLOW,
            target=TargetAudience.EXPERT,
            domain_sources=[ContentDomain.AUTEUR_BONG, ContentDomain.GENRE_THRILLER],
            output_format=OutputFormat.VIDEO,
            aesthetic_hints=AestheticHints(
                color_temperature="cool",
                lighting_style="low-key",
            ),
            keywords=["tension", "social-commentary"],
            custom_notes="강주노 감독 스타일 참조",
        )
        
        assert intent.mood == CreativeMood.CINEMATIC
        assert len(intent.domain_sources) == 2
        assert intent.aesthetic_hints.lighting_style == "low-key"
        assert "tension" in intent.keywords
    
    def test_keyword_validation(self):
        """키워드 정제 검증"""
        intent = CreativeIntent(
            mood=CreativeMood.CALM,
            keywords=["  TENSION  ", "Drama", "  "],
        )
        
        # 공백 제거, 소문자화, 빈 문자열 제거
        assert intent.keywords == ["tension", "drama"]
    
    def test_to_resolver_context(self):
        """Resolver 컨텍스트 변환"""
        intent = CreativeIntent(
            mood=CreativeMood.DOCUMENTARY,
            pace=CreativePace.CONTEMPLATIVE,
            domain_sources=[ContentDomain.SOURCE_SAJU],
        )
        
        context = intent.to_resolver_context()
        
        assert context["mood"] == "documentary"
        assert context["pace"] == "contemplative"
        assert "saju" in context["domain_sources"]
    
    def test_has_auteur_source(self):
        """거장 소스 확인"""
        intent_with_auteur = CreativeIntent(
            mood=CreativeMood.CINEMATIC,
            domain_sources=[ContentDomain.AUTEUR_BONG],
        )
        intent_without_auteur = CreativeIntent(
            mood=CreativeMood.CALM,
            domain_sources=[ContentDomain.GENRE_DRAMA],
        )
        
        assert intent_with_auteur.has_auteur_source() is True
        assert intent_without_auteur.has_auteur_source() is False
    
    def test_has_special_source(self):
        """특수 소스 (사주/논문) 확인"""
        intent_with_saju = CreativeIntent(
            mood=CreativeMood.NOSTALGIC,
            domain_sources=[ContentDomain.SOURCE_SAJU],
        )
        intent_normal = CreativeIntent(
            mood=CreativeMood.ENERGETIC,
            domain_sources=[ContentDomain.PLATFORM_TIKTOK],
        )
        
        assert intent_with_saju.has_special_source() is True
        assert intent_normal.has_special_source() is False
    
    def test_json_serialization(self):
        """JSON 직렬화/역직렬화"""
        intent = CreativeIntent(
            mood=CreativeMood.CINEMATIC,
            pace=CreativePace.SLOW,
            domain_sources=[ContentDomain.AUTEUR_BONG],
        )
        
        # 직렬화
        json_str = intent.model_dump_json()
        assert '"mood":"cinematic"' in json_str
        
        # 역직렬화
        restored = CreativeIntent.model_validate_json(json_str)
        assert restored.mood == CreativeMood.CINEMATIC
        assert restored.domain_sources[0] == ContentDomain.AUTEUR_BONG


class TestIntentFactory:
    """IntentFactory 프리셋 테스트"""
    
    def test_cinematic_bong(self):
        """강주노 시네마틱 프리셋"""
        intent = IntentFactory.cinematic_bong()
        
        assert intent.mood == CreativeMood.CINEMATIC
        assert intent.target == TargetAudience.EXPERT
        assert ContentDomain.AUTEUR_BONG in intent.domain_sources
        assert intent.aesthetic_hints.lighting_style == "low-key"
    
    def test_documentary_calm(self):
        """다큐멘터리 프리셋"""
        intent = IntentFactory.documentary_calm()
        
        assert intent.mood == CreativeMood.DOCUMENTARY
        assert intent.pace == CreativePace.CONTEMPLATIVE
        assert intent.aesthetic_hints.lighting_style == "natural"
    
    def test_shortform_energetic(self):
        """숏폼 바이럴 프리셋"""
        intent = IntentFactory.shortform_energetic()
        
        assert intent.mood == CreativeMood.ENERGETIC
        assert intent.pace == CreativePace.FAST
        assert ContentDomain.PLATFORM_TIKTOK in intent.domain_sources
        assert "viral" in intent.keywords
    
    def test_saju_guided(self):
        """사주 가이드 프리셋"""
        intent = IntentFactory.saju_guided()
        
        assert ContentDomain.SOURCE_SAJU in intent.domain_sources
        assert ContentDomain.SOURCE_PHILOSOPHY in intent.domain_sources
        assert intent.has_special_source() is True


class TestTemplateIntentPreset:
    """템플릿 Input Preset 마이그레이션 스키마 테스트"""
    
    def test_new_format(self):
        """신규 Intent 기반 형식"""
        preset = TemplateIntentPreset(
            intent=CreativeIntent(mood=CreativeMood.CINEMATIC),
        )
        
        assert preset.schema_version == "2.0"
        
        params = preset.get_resolved_params("VEO")
        assert params["mood"] == "cinematic"


class TestAestheticHints:
    """AestheticHints 테스트"""
    
    def test_partial_hints(self):
        """일부 힌트만 지정"""
        hints = AestheticHints(
            lighting_style="low-key",
            color_temperature="cool",
        )
        
        assert hints.lighting_style == "low-key"
        assert hints.composition_style is None
    
    def test_visual_references(self):
        """시각적 참조 리스트"""
        hints = AestheticHints(
            visual_references=["blade-runner", "neo-noir"]
        )
        
        assert "blade-runner" in hints.visual_references


class TestIntentMetadata:
    """IntentMetadata 테스트"""
    
    def test_auto_generated_id(self):
        """자동 생성 ID"""
        meta = IntentMetadata()
        
        assert meta.intent_id is not None
        assert len(meta.intent_id) == 12
    
    def test_timestamp(self):
        """타임스탬프 자동 생성"""
        meta = IntentMetadata()
        
        assert isinstance(meta.created_at, datetime)


# =========================================================================
# Integration Tests
# =========================================================================

class TestIntentIntegration:
    """통합 테스트"""
    
    def test_complete_workflow(self):
        """전체 워크플로우 시뮬레이션"""
        # 1. Intent 생성
        intent = IntentFactory.cinematic_bong()
        
        # 2. 컨텍스트 추출
        context = intent.to_resolver_context()
        
        # 3. Resolver 시뮬레이션 (Phase 2에서 실제 구현)
        assert context["mood"] == "cinematic"
        assert "bong-joon-ho" in context["domain_sources"]
        
        # 4. JSON 직렬화/역직렬화 (API 전송 시뮬레이션)
        json_str = intent.model_dump_json()
        restored = CreativeIntent.model_validate_json(json_str)
        
        assert restored.mood == intent.mood
        assert restored.domain_sources == intent.domain_sources
