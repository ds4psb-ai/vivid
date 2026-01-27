"""
E2E Tests for Mirror → Story Chain.

P4: Mirror→Story 체인 E2E 테스트

테스트 시나리오:
1. Mirror init → 페르소나 분석 시작
2. Mirror chat → 페르소나 데이터 누적
3. Mirror complete → OCEAN 저장 (is_complete=True)
4. OCEAN 데이터 조회 확인
5. 페르소나 데이터 → Story Architect 전달
6. Story Architect → 시나리오 생성
7. 체인 데이터 흐름 검증

데이터 흐름:
    Mirror (PersonaDNA + OCEAN)
         ↓
    Story Architect (persona_data 파라미터)
         ↓
    시나리오 생성 (persona 반영)
"""
from __future__ import annotations

import json
import pytest
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

from app.routers.dimension.mirror import (
    MirrorInitRequest,
    MirrorChatRequest,
    MirrorInitResponse,
    MirrorChatResponse,
    OceanTraits,
)
from app.routers.dimension.story import (
    StoryArchitectRequest,
)
from app.services.ocean_storage_service import (
    OceanScores,
    OceanSaveResult,
    OceanStorageService,
    get_ocean_storage_service,
    _reset_ocean_storage_service,
)
from app.services.mirror_service import (
    calculate_ocean_from_mbti,
    calculate_saju_pillars,
    validate_persona_preset,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_mirror_init_data() -> Dict[str, Any]:
    """Sample Mirror init request data with MBTI."""
    return {
        "mbti": "INTJ",
        "blood_type": "A",
        "birth_year": 1990,
        "birth_month": 5,
        "birth_day": 15,
        "birth_hour": 14,
        "gender": "M",
        "model": "gemini-3-flash-preview",
    }


@pytest.fixture
def sample_persona_data() -> Dict[str, Any]:
    """Sample accumulated persona data from Mirror."""
    return {
        "meta": {
            "id": "test-persona-id",
            "created_at": "2026-01-01T00:00:00",
            "version": "1.0",
            "completion_rate": 85,
        },
        "input": {
            "mbti": "INTJ",
            "blood_type": "A",
            "birth_datetime": "1990-05-15T14:00:00",
            "gender": "M",
        },
        "saju": {
            "year_pillar": "경오(庚午)",
            "month_pillar": "신사(辛巳)",
            "day_pillar": "갑자(甲子)",
            "hour_pillar": "임인(壬寅)",
            "dominant_element": "금",
        },
        "psychology": {
            "maslow_level": {
                "physiological": 8,
                "safety": 7,
                "belonging": 5,
                "esteem": 6,
                "self_actualization": 8,
                "self_transcendence": 4,
            },
            "unconscious_patterns": ["perfectionism", "isolation tendency"],
            "shadow_traits": ["fear of failure", "emotional suppression"],
            "core_values": ["achievement", "knowledge", "independence"],
            "emotional_triggers": ["incompetence", "chaos"],
        },
        "creativity": {
            "visual_style_affinity": ["minimalist", "dark", "geometric"],
            "narrative_tendencies": ["complex plot", "unreliable narrator"],
            "color_palette_preference": ["monochrome", "cold tones"],
            "recommended_auteurs": ["epoch", "abyss"],
        },
        "persona": {
            "archetype": "The Architect",
            "voice_tone": "analytical and precise",
            "world_view": "systematic and logical",
            "summary": "A meticulous planner who values structure and efficiency",
        },
    }


@pytest.fixture
def sample_ocean_scores() -> OceanScores:
    """Sample OCEAN scores for INTJ."""
    return OceanScores(
        openness=0.80,       # N (intuitive) → high openness
        conscientiousness=0.75,  # J (judging) → high conscientiousness
        extraversion=0.35,   # I (introvert) → low extraversion
        agreeableness=0.40,  # T (thinking) → low agreeableness
        neuroticism=0.55,    # I+N+J → moderate neuroticism
    )


# ============================================================================
# Unit Tests: MBTI → OCEAN Conversion
# ============================================================================

class TestMbtiOceanConversion:
    """MBTI → OCEAN 변환 정확성 테스트."""

    def test_intj_ocean_values(self):
        """INTJ 타입의 OCEAN 값 검증."""
        ocean = calculate_ocean_from_mbti("INTJ")

        # INTJ: I→low E, N→high O, T→low A, J→high C
        assert ocean["extraversion"] < 0.5, "INTJ should have low extraversion"
        assert ocean["openness"] > 0.5, "INTJ should have high openness"
        assert ocean["agreeableness"] < 0.5, "INTJ should have low agreeableness"
        assert ocean["conscientiousness"] > 0.5, "INTJ should have high conscientiousness"

    def test_enfp_ocean_values(self):
        """ENFP 타입의 OCEAN 값 검증."""
        ocean = calculate_ocean_from_mbti("ENFP")

        # ENFP: E→high E, N→high O, F→high A, P→low C
        assert ocean["extraversion"] > 0.5, "ENFP should have high extraversion"
        assert ocean["openness"] > 0.5, "ENFP should have high openness"
        assert ocean["agreeableness"] > 0.5, "ENFP should have high agreeableness"
        assert ocean["conscientiousness"] < 0.5, "ENFP should have low conscientiousness"

    def test_all_mbti_types_produce_valid_ocean(self):
        """모든 16개 MBTI 타입이 유효한 OCEAN 범위 생성."""
        mbti_types = [
            "INTJ", "INTP", "ENTJ", "ENTP",
            "INFJ", "INFP", "ENFJ", "ENFP",
            "ISTJ", "ISFJ", "ESTJ", "ESFJ",
            "ISTP", "ISFP", "ESTP", "ESFP",
        ]

        for mbti in mbti_types:
            ocean = calculate_ocean_from_mbti(mbti)
            for trait, value in ocean.items():
                assert 0.0 <= value <= 1.0, f"{mbti} {trait}={value} out of range"


# ============================================================================
# Unit Tests: Persona Data Validation
# ============================================================================

class TestPersonaDataValidation:
    """페르소나 데이터 유효성 검증 테스트."""

    def test_validate_persona_preset_fills_defaults(self):
        """빈 필드에 기본값 채우기."""
        minimal = {"input": {"mbti": "INTJ"}}
        validated = validate_persona_preset(minimal)

        assert "meta" in validated
        assert "saju" in validated
        assert "psychology" in validated
        assert "creativity" in validated
        assert "persona" in validated

    def test_validate_persona_preset_preserves_values(self):
        """기존 값 보존."""
        data = {
            "input": {"mbti": "ENFP"},
            "saju": {"dominant_element": "목"},
        }
        validated = validate_persona_preset(data)

        assert validated["input"]["mbti"] == "ENFP"
        assert validated["saju"]["dominant_element"] == "목"


# ============================================================================
# Integration Tests: Mirror Init → OCEAN Calculation
# ============================================================================

class TestMirrorInitOcean:
    """Mirror init 시 OCEAN 계산 테스트."""

    def test_mirror_init_calculates_ocean_from_mbti(self, sample_mirror_init_data):
        """Mirror init 시 MBTI에서 OCEAN 계산."""
        mbti = sample_mirror_init_data["mbti"]
        ocean = calculate_ocean_from_mbti(mbti)

        assert ocean is not None
        assert "openness" in ocean
        assert "conscientiousness" in ocean
        assert "extraversion" in ocean
        assert "agreeableness" in ocean
        assert "neuroticism" in ocean

    def test_mirror_init_creates_saju_data(self, sample_mirror_init_data):
        """Mirror init 시 사주 데이터 생성."""
        saju = calculate_saju_pillars(
            year=sample_mirror_init_data["birth_year"],
            month=sample_mirror_init_data["birth_month"],
            day=sample_mirror_init_data["birth_day"],
            hour=sample_mirror_init_data["birth_hour"],
        )

        assert "year_pillar" in saju
        assert "month_pillar" in saju
        assert "day_pillar" in saju
        assert "hour_pillar" in saju
        assert "dominant_element" in saju


# ============================================================================
# Integration Tests: Mirror Chat → OCEAN Save
# ============================================================================

class TestMirrorChatOceanSave:
    """Mirror 채팅 완료 시 OCEAN 저장 테스트."""

    @pytest.fixture
    def ocean_service(self):
        """테스트용 OceanStorageService."""
        _reset_ocean_storage_service()
        return OceanStorageService()

    @pytest.mark.asyncio
    async def test_ocean_save_on_complete(self, ocean_service, sample_ocean_scores):
        """is_complete=True 시 OCEAN 저장 호출."""
        # Simulate save
        with patch("app.services.ocean_storage_service.get_db_context") as mock_db:
            mock_session = AsyncMock()
            mock_profile = MagicMock()
            mock_profile.openness = 0.5
            mock_profile.conscientiousness = 0.5
            mock_profile.extraversion = 0.5
            mock_profile.agreeableness = 0.5
            mock_profile.neuroticism = 0.5
            mock_profile.last_ocean_update = None

            mock_db.return_value.__aenter__.return_value = mock_session

            # Mock _get_or_create_profile
            with patch.object(ocean_service, "_get_or_create_profile") as mock_get:
                mock_get.return_value = (mock_profile, False)

                result = await ocean_service.save_ocean(
                    user_id="test_user",
                    ocean=sample_ocean_scores,
                    source="mirror",
                )

                assert result.success is True
                assert result.user_id == "test_user"
                assert result.new_values is not None

    @pytest.mark.asyncio
    async def test_ocean_not_saved_when_incomplete(self):
        """is_complete=False 시 OCEAN 저장 미호출."""
        mock_service = AsyncMock()

        is_complete = False
        ocean_traits = {"openness": 0.8}

        if is_complete and ocean_traits:
            await mock_service.save_ocean(user_id="test", ocean=ocean_traits)

        mock_service.save_ocean.assert_not_called()


# ============================================================================
# Integration Tests: Mirror → Story Chain
# ============================================================================

class TestMirrorStoryChain:
    """Mirror → Story 체인 통합 테스트."""

    def test_persona_data_can_be_serialized_for_story(self, sample_persona_data):
        """페르소나 데이터가 Story로 전달 가능한 형식인지 확인."""
        # Story expects persona_data as JSON string
        serialized = json.dumps(sample_persona_data, ensure_ascii=False)

        assert isinstance(serialized, str)
        assert len(serialized) > 0

        # Can be deserialized back
        deserialized = json.loads(serialized)
        assert deserialized["input"]["mbti"] == "INTJ"

    def test_story_request_accepts_persona_data(self, sample_persona_data):
        """StoryArchitectRequest가 persona_data를 받을 수 있는지 확인."""
        request = StoryArchitectRequest(
            concept="A visionary architect designs a futuristic city",
            persona_data=json.dumps(sample_persona_data, ensure_ascii=False),
            reference_analysis="Reference: Blade Runner 2049",
            genre="drama",
            duration=120,
            structure="3-act",
            language="ko",
            model="gemini-3-flash-preview",
        )

        assert request.concept is not None
        assert request.persona_data is not None
        assert len(request.persona_data) > 0

    def test_story_request_accepts_dict_persona_data(self, sample_persona_data):
        """StoryArchitectRequest가 dict 형식 persona_data도 처리."""
        # The validator should convert dict to JSON string
        request = StoryArchitectRequest(
            concept="A visionary architect designs a futuristic city",
            persona_data=sample_persona_data,  # Pass as dict
            reference_analysis={},  # Also test dict reference
            genre="drama",
            duration=120,
            structure="3-act",
            language="ko",
            model="gemini-3-flash-preview",
        )

        assert request.persona_data is not None
        # Should be serialized to string
        assert isinstance(request.persona_data, str)


# ============================================================================
# E2E Flow Tests
# ============================================================================

class TestE2EFlow:
    """전체 E2E 흐름 테스트."""

    def test_full_chain_data_flow(self, sample_mirror_init_data, sample_persona_data):
        """Mirror→Story 전체 데이터 흐름."""
        # Step 1: Mirror Init - Calculate OCEAN from MBTI
        mbti = sample_mirror_init_data["mbti"]
        ocean = calculate_ocean_from_mbti(mbti)

        assert ocean["openness"] > 0.5  # N type

        # Step 2: Mirror builds persona_data
        persona_data = sample_persona_data.copy()

        # Verify OCEAN values are consistent with persona
        assert persona_data["input"]["mbti"] == mbti

        # Step 3: Prepare Story request with persona_data
        story_request = StoryArchitectRequest(
            concept="A brilliant architect creates an impossible structure",
            persona_data=json.dumps(persona_data, ensure_ascii=False),
            reference_analysis="Reference: Inception, The Matrix",
            genre="drama",
            duration=180,
            structure="3-act",
            language="ko",
            model="gemini-3-flash-preview",
        )

        # Step 4: Verify persona context is embedded
        assert "INTJ" in story_request.persona_data
        assert "The Architect" in story_request.persona_data

    def test_ocean_traits_in_response_chain(self):
        """응답에 OCEAN 특성 포함 확인."""
        ocean = calculate_ocean_from_mbti("INTJ")
        ocean_traits = OceanTraits(**ocean)

        assert ocean_traits.openness == ocean["openness"]
        assert ocean_traits.conscientiousness == ocean["conscientiousness"]
        assert ocean_traits.extraversion == ocean["extraversion"]
        assert ocean_traits.agreeableness == ocean["agreeableness"]
        assert ocean_traits.neuroticism == ocean["neuroticism"]

    def test_evidence_refs_chain_format(self, sample_persona_data):
        """evidence_refs 체인 포맷 검증."""
        user_id = "test_user_123"
        session_id = "session_abc"
        mbti = sample_persona_data["input"]["mbti"]

        # Mirror evidence refs
        mirror_refs = [
            f"db:mirror:session:{session_id}",
            f"rag:mirror:mbti_profile:{mbti.lower()}",
        ]

        # OCEAN save evidence ref
        ocean_ref = f"db:user_preference_profiles:{user_id}:ocean"

        # Story evidence refs would include persona reference
        story_refs = [
            f"db:persona:{sample_persona_data['meta']['id']}",
        ]

        # All refs follow Vivid convention (List[str])
        all_refs = mirror_refs + [ocean_ref] + story_refs

        for ref in all_refs:
            assert isinstance(ref, str)
            assert ":" in ref  # format: source:type:id


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """에러 처리 테스트."""

    def test_empty_mbti_returns_default_ocean(self):
        """빈 MBTI는 기본 OCEAN 반환."""
        ocean = calculate_ocean_from_mbti("")

        for value in ocean.values():
            assert value == 0.5

    def test_invalid_mbti_length_returns_default_ocean(self):
        """잘못된 길이의 MBTI는 기본 OCEAN 반환."""
        # Only length != 4 returns defaults
        ocean = calculate_ocean_from_mbti("XYZ")  # 3 chars

        for value in ocean.values():
            assert value == 0.5

    def test_invalid_mbti_chars_returns_else_values(self):
        """유효하지 않은 문자의 4자리 MBTI는 else 값 반환."""
        ocean = calculate_ocean_from_mbti("XXXX")

        # 4 chars but invalid - returns else values (not E, N, F, J)
        assert ocean["extraversion"] == 0.35  # not E
        assert ocean["openness"] == 0.35      # not N
        assert ocean["agreeableness"] == 0.40  # not F
        assert ocean["conscientiousness"] == 0.40  # not J

    def test_story_request_with_empty_persona(self):
        """빈 persona_data로도 Story 요청 가능."""
        request = StoryArchitectRequest(
            concept="A simple story",
            persona_data="",  # Empty
            reference_analysis="",
            genre="drama",
            duration=60,
            structure="3-act",
            language="ko",
            model="gemini-3-flash-preview",
        )

        assert request.persona_data == ""
        assert request.concept == "A simple story"


# ============================================================================
# Data Consistency Tests
# ============================================================================

class TestDataConsistency:
    """데이터 일관성 테스트."""

    def test_ocean_scores_consistent_across_chain(self, sample_ocean_scores):
        """체인 전체에서 OCEAN 점수 일관성."""
        # Original scores
        original = sample_ocean_scores.to_dict()

        # Serialized and deserialized
        serialized = json.dumps(original)
        restored = OceanScores.from_dict(json.loads(serialized))

        assert restored.openness == sample_ocean_scores.openness
        assert restored.conscientiousness == sample_ocean_scores.conscientiousness
        assert restored.extraversion == sample_ocean_scores.extraversion
        assert restored.agreeableness == sample_ocean_scores.agreeableness
        assert restored.neuroticism == sample_ocean_scores.neuroticism

    def test_persona_data_integrity_through_chain(self, sample_persona_data):
        """체인 통과 시 페르소나 데이터 무결성."""
        # Serialize for Story request
        serialized = json.dumps(sample_persona_data, ensure_ascii=False)

        # Deserialize back (simulating Story reading it)
        restored = json.loads(serialized)

        # Key fields preserved
        assert restored["input"]["mbti"] == sample_persona_data["input"]["mbti"]
        assert restored["saju"]["dominant_element"] == sample_persona_data["saju"]["dominant_element"]
        assert restored["persona"]["archetype"] == sample_persona_data["persona"]["archetype"]


# ============================================================================
# Creative Style Chain Tests
# ============================================================================

class TestCreativeStyleChain:
    """창작 스타일 체인 테스트."""

    def test_mbti_to_creative_style_to_auteur(self, sample_persona_data):
        """MBTI → 창작 스타일 → 추천 거장 체인."""
        from app.routers.dimension.mirror import (
            get_creative_style,
            get_auteur_affinity,
            CreativeStyle,
        )

        mbti = sample_persona_data["input"]["mbti"]
        creative_style = get_creative_style(mbti)
        auteur_affinity = get_auteur_affinity(creative_style)

        # INTJ should map to LOGICAL_ARCHITECT
        assert creative_style == CreativeStyle.LOGICAL_ARCHITECT

        # LOGICAL_ARCHITECT should have specific auteur recommendations
        assert len(auteur_affinity) > 0

    def test_recommended_auteurs_in_persona_data(self, sample_persona_data):
        """페르소나 데이터에 추천 거장 포함."""
        recommended = sample_persona_data["creativity"]["recommended_auteurs"]

        assert isinstance(recommended, list)
        assert len(recommended) > 0
        assert "epoch" in recommended or "abyss" in recommended


# ============================================================================
# Profile Quality Chain Tests
# ============================================================================

class TestProfileQualityChain:
    """프로필 품질 체인 테스트."""

    def test_profile_quality_affects_story_generation(self, sample_persona_data):
        """프로필 품질이 Story 생성에 영향."""
        from app.routers.dimension.mirror import assess_mirror_profile_quality

        mbti = sample_persona_data["input"]["mbti"]
        quality = assess_mirror_profile_quality(
            mbti=mbti,
            persona_data=sample_persona_data,
            completion_rate=85,
            chat_turn_count=12,
        )

        # High quality profile should have good scores
        assert quality.overall_score >= 50
        assert quality.creative_style != "unknown"
        assert len(quality.auteur_affinity) > 0

    def test_low_quality_profile_has_suggestions(self):
        """낮은 품질 프로필은 개선 제안 포함."""
        from app.routers.dimension.mirror import assess_mirror_profile_quality

        quality = assess_mirror_profile_quality(
            mbti="",  # No MBTI
            persona_data={},  # Empty data
            completion_rate=10,
            chat_turn_count=2,
        )

        assert quality.overall_score < 50
        assert len(quality.suggestions) > 0
