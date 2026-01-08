"""
Integration Tests for Intent-Resolver System

Phase 1-2 하드닝: 실제 dimension_adapter와의 통합 테스트
"""
import pytest
from typing import Dict, Any

from app.schemas.creative_intent import (
    CreativeIntent, 
    CreativeMood, 
    CreativePace,
    TargetAudience,
    ContentDomain,
    IntentFactory,
    TemplateIntentPreset,
)
from app.resolvers import (
    get_resolver,
    resolve_intent_for_dimension,
    resolve_intent_for_all,
)
from app.resolvers.integration import (
    extract_intent_from_preset,
    get_enhanced_capsule_params,
    prepare_dimension_params,
    enhance_prompt_generator_params,
    enhance_veo_params,
)


class TestIntentExtraction:
    """input_preset에서 Intent 추출 테스트"""
    
    def test_extract_from_new_format(self):
        """신규 포맷에서 Intent 추출"""
        preset = {
            "intent": {
                "mood": "cinematic",
                "pace": "slow",
                "target": "expert",
                "domain_sources": ["bong-joon-ho"],
            },
            "legacy_params": {"old_param": "value"},
            "schema_version": "2.0",
        }
        
        intent, legacy = extract_intent_from_preset(preset)
        
        assert intent is not None
        assert intent.mood == CreativeMood.CINEMATIC
        assert legacy == {"old_param": "value"}
    
    def test_extract_from_legacy_mood(self):
        """레거시 mood 필드에서 Intent 유추"""
        preset = {
            "mood": "cinematic",
            "veo_model": "veo-3.1",
        }
        
        intent, legacy = extract_intent_from_preset(preset)
        
        assert intent is not None
        assert intent.mood == CreativeMood.CINEMATIC
        assert legacy == preset  # 원본 유지
    
    def test_extract_from_legacy_style(self):
        """레거시 style 필드에서 Intent 유추"""
        preset = {
            "style": "documentary",
            "aspect_ratio": "16:9",
        }
        
        intent, legacy = extract_intent_from_preset(preset)
        
        assert intent is not None
        assert intent.mood == CreativeMood.DOCUMENTARY
    
    def test_extract_from_unknown_values(self):
        """알 수 없는 값일 때 None 반환"""
        preset = {
            "mood": "unknown_mood_xyz",
            "other_param": 123,
        }
        
        intent, legacy = extract_intent_from_preset(preset)
        
        assert intent is None
        assert legacy == preset
    
    def test_extract_from_empty(self):
        """빈 preset"""
        intent, legacy = extract_intent_from_preset({})
        
        assert intent is None
        assert legacy is None


class TestParameterEnhancement:
    """파라미터 병합 테스트"""
    
    def test_enhance_prompt_params(self):
        """Prompt Generator 파라미터 병합"""
        base = {"topic": "test video", "language": "ko"}
        resolved = {
            "tone": "dramatic",
            "detail_level": "high",
            "emphasis": ["tension", "shadow"],
        }
        
        result = enhance_prompt_generator_params(base, resolved)
        
        assert result["topic"] == "test video"
        assert result["style"] == "dramatic"
        assert result["complexity"] == "high"
        assert result["focus_areas"] == ["tension", "shadow"]
    
    def test_enhance_veo_params(self):
        """VEO 파라미터 병합"""
        base = {"prompt": "test"}
        resolved = {
            "aspect_ratio": "21:9",
            "duration": 8,
            "camera_style": "cinematic",
        }
        
        result = enhance_veo_params(base, resolved)
        
        assert result["veo_aspect_ratio"] == "21:9"
        assert result["veo_duration"] == 8
        assert result["camera_style"] == "cinematic"
        assert result["veo_model"] == "veo-3.1"  # 기본값


class TestEnhancedCapsuleParams:
    """Resolver 기반 파라미터 생성 테스트"""
    
    @pytest.mark.asyncio
    async def test_with_explicit_intent(self):
        """명시적 Intent로 파라미터 생성"""
        intent = IntentFactory.cinematic_bong()
        
        params = await get_enhanced_capsule_params(
            dimension_code="VEO",
            explicit_intent=intent,
        )
        
        assert "aspect_ratio" in params or "veo_aspect_ratio" in params
    
    @pytest.mark.asyncio
    async def test_with_preset_intent(self):
        """Preset에서 Intent 추출 후 파라미터 생성"""
        preset = {
            "intent": {
                "mood": "energetic",
                "pace": "fast",
            },
            "schema_version": "2.0",
        }
        
        params = await get_enhanced_capsule_params(
            dimension_code="SOUND",
            input_preset=preset,
        )
        
        # Resolver가 동작했으면 음악 관련 파라미터 존재
        assert len(params) > 0
    
    @pytest.mark.asyncio
    async def test_with_legacy_preset(self):
        """Legacy preset은 그대로 반환"""
        preset = {
            "mood": "unknown_xyz",  # Intent로 변환 불가
            "custom_param": 123,
        }
        
        params = await get_enhanced_capsule_params(
            dimension_code="VEO",
            input_preset=preset,
        )
        
        assert params.get("custom_param") == 123
    
    @pytest.mark.asyncio
    async def test_with_unregistered_dimension(self):
        """등록되지 않은 Dimension"""
        params = await get_enhanced_capsule_params(
            dimension_code="UNKNOWN_DIM",
            input_preset={"key": "value"},
        )
        
        assert params == {"key": "value"}


class TestPrepareDimensionParams:
    """dimension_adapter 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_prepare_1d_params(self):
        """1D Prompt Director 파라미터 준비"""
        inputs = {"topic": "sunset video"}
        params = {"model": "gemini-3-flash-preview"}
        intent = CreativeIntent(
            mood=CreativeMood.CINEMATIC,
            target=TargetAudience.EXPERT,
        )
        
        enhanced_inputs, enhanced_params = await prepare_dimension_params(
            dimension_code="1D",
            inputs=inputs,
            params=params,
            intent=intent,
        )
        
        # Resolver가 detail_level 등을 추가해야 함
        assert enhanced_inputs["topic"] == "sunset video"
        assert "model" in enhanced_params
    
    @pytest.mark.asyncio
    async def test_prepare_veo_params(self):
        """VEO 파라미터 준비"""
        inputs = {}
        params = {}
        intent = IntentFactory.cinematic_bong()
        
        enhanced_inputs, enhanced_params = await prepare_dimension_params(
            dimension_code="VEO",
            inputs=inputs,
            params=params,
            intent=intent,
        )
        
        # VEO 특화 파라미터 존재
        assert "veo_aspect_ratio" in enhanced_params or "aspect_ratio" in enhanced_params


class TestResolverIntegrationHardening:
    """하드닝 테스트 - 에러 케이스"""
    
    @pytest.mark.asyncio
    async def test_resolver_handles_none_intent(self):
        """Intent가 None일 때 정상 동작"""
        params = await get_enhanced_capsule_params(
            dimension_code="VEO",
            input_preset=None,
            explicit_intent=None,
        )
        
        assert params == {}  # 빈 결과
    
    @pytest.mark.asyncio
    async def test_resolver_handles_invalid_mood(self):
        """잘못된 mood 값 처리"""
        preset = {
            "mood": "",  # 빈 문자열
        }
        
        # 에러 없이 처리되어야 함
        params = await get_enhanced_capsule_params(
            dimension_code="VEO",
            input_preset=preset,
        )
        
        assert params == preset
    
    def test_extract_handles_malformed_preset(self):
        """잘못된 형식의 preset"""
        # schema_version 있지만 intent 없음
        preset = {
            "schema_version": "2.0",
            "other": "data",
        }
        
        intent, legacy = extract_intent_from_preset(preset)
        
        # 에러 없이 None 반환
        assert intent is None


class TestFullPipelineIntegration:
    """전체 파이프라인 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_flow(self):
        """Intent → Resolver → 파라미터 전체 흐름"""
        # 1. Template에서 Intent 정의
        template_preset = {
            "intent": {
                "mood": "cinematic",
                "pace": "slow",
                "target": "expert",
                "domain_sources": ["bong-joon-ho", "thriller"],
            },
            "schema_version": "2.0",
        }
        
        # 2. Intent 추출
        intent, legacy = extract_intent_from_preset(template_preset)
        assert intent is not None
        
        # 3. 모든 Dimension에 대해 Resolve
        all_params = await resolve_intent_for_all(intent)
        
        assert "VEO" in all_params
        assert "SOUND" in all_params
        assert "1D" in all_params
        
        # 4. VEO 파라미터 검증
        veo_params = all_params["VEO"].params
        assert veo_params.get("aspect_ratio") == "21:9"  # 봉준호 스타일
        
        # 5. SOUND 파라미터 검증
        sound_params = all_params["SOUND"].params
        assert sound_params.get("genre") == "orchestral"  # cinematic mood
    
    @pytest.mark.asyncio
    async def test_saju_source_integration(self):
        """사주 소스 통합 테스트"""
        intent = CreativeIntent(
            mood=CreativeMood.CALM,
            domain_sources=[ContentDomain.SOURCE_SAJU],
        )
        
        sound_result = await resolve_intent_for_dimension("SOUND", intent)
        
        # 사주 소스가 적용되면 동양 악기 추가
        assert "guqin" in sound_result.params.get("additional_instruments", [])
