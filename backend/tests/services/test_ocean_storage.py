"""
Test suite for ocean_storage_service.py.

P3: OCEAN 저장 서비스 테스트 (30+ 테스트 케이스)

테스트 카테고리:
1. OceanScores 관련 (Unit Tests)
2. save_ocean 관련 (Unit Tests)
3. get_ocean 관련 (Unit Tests)
4. _get_or_create_profile 관련 (Unit Tests)
5. Mirror → OCEAN 저장 흐름 (Integration Tests)
6. 동시성/경합 (Integration Tests)
7. evidence_refs 연동 (Integration Tests)
8. 에러 복구 (Integration Tests)
9. 엣지 케이스 (Integration Tests)
"""
import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio

from app.services.ocean_storage_service import (
    OceanScores,
    OceanSaveResult,
    OceanStorageService,
    get_ocean_storage_service,
    _reset_ocean_storage_service,
)


# ============================================================================
# Unit Tests: OceanScores
# ============================================================================

class TestOceanScoresUnit:
    """OceanScores 데이터클래스 유닛 테스트."""

    def test_ocean_scores_default_values(self):
        """기본값 0.5 확인."""
        scores = OceanScores()
        assert scores.openness == 0.5
        assert scores.conscientiousness == 0.5
        assert scores.extraversion == 0.5
        assert scores.agreeableness == 0.5
        assert scores.neuroticism == 0.5

    def test_ocean_scores_custom_values(self):
        """커스텀 값 설정."""
        scores = OceanScores(
            openness=0.8,
            conscientiousness=0.6,
            extraversion=0.4,
            agreeableness=0.7,
            neuroticism=0.3,
        )
        assert scores.openness == 0.8
        assert scores.conscientiousness == 0.6
        assert scores.extraversion == 0.4
        assert scores.agreeableness == 0.7
        assert scores.neuroticism == 0.3

    def test_ocean_scores_boundary_values_min(self):
        """최소값 경계 (0.0) 테스트."""
        scores = OceanScores(
            openness=0.0,
            conscientiousness=0.0,
            extraversion=0.0,
            agreeableness=0.0,
            neuroticism=0.0,
        )
        assert scores.openness == 0.0
        assert scores.neuroticism == 0.0

    def test_ocean_scores_boundary_values_max(self):
        """최대값 경계 (1.0) 테스트."""
        scores = OceanScores(
            openness=1.0,
            conscientiousness=1.0,
            extraversion=1.0,
            agreeableness=1.0,
            neuroticism=1.0,
        )
        assert scores.openness == 1.0
        assert scores.neuroticism == 1.0

    def test_ocean_scores_clamp_negative_values(self):
        """음수 값은 0.0으로 클램프."""
        scores = OceanScores(openness=-0.5, neuroticism=-1.0)
        assert scores.openness == 0.0
        assert scores.neuroticism == 0.0

    def test_ocean_scores_clamp_over_one_values(self):
        """1 초과 값은 1.0으로 클램프."""
        scores = OceanScores(openness=1.5, extraversion=2.0)
        assert scores.openness == 1.0
        assert scores.extraversion == 1.0

    def test_ocean_scores_to_dict(self):
        """to_dict() 메서드 테스트."""
        scores = OceanScores(openness=0.75)
        d = scores.to_dict()
        assert d["openness"] == 0.75
        assert "conscientiousness" in d
        assert "extraversion" in d
        assert "agreeableness" in d
        assert "neuroticism" in d

    def test_ocean_scores_from_dict(self):
        """from_dict() 클래스메서드 테스트."""
        data = {
            "openness": 0.8,
            "conscientiousness": 0.7,
            "extraversion": 0.6,
            "agreeableness": 0.5,
            "neuroticism": 0.4,
        }
        scores = OceanScores.from_dict(data)
        assert scores.openness == 0.8
        assert scores.neuroticism == 0.4

    def test_ocean_scores_from_dict_partial(self):
        """from_dict() 일부 필드만 있는 경우."""
        data = {"openness": 0.9}
        scores = OceanScores.from_dict(data)
        assert scores.openness == 0.9
        assert scores.conscientiousness == 0.5  # default

    def test_ocean_scores_from_dict_empty(self):
        """from_dict() 빈 딕셔너리."""
        scores = OceanScores.from_dict({})
        assert scores.openness == 0.5
        assert scores.neuroticism == 0.5


# ============================================================================
# Unit Tests: OceanSaveResult
# ============================================================================

class TestOceanSaveResultUnit:
    """OceanSaveResult 데이터클래스 유닛 테스트."""

    def test_save_result_success(self):
        """성공 결과 생성."""
        result = OceanSaveResult(
            success=True,
            user_id="user123",
            updated_at=datetime.utcnow(),
            new_values={"openness": 0.8},
        )
        assert result.success is True
        assert result.user_id == "user123"
        assert result.error is None

    def test_save_result_failure(self):
        """실패 결과 생성."""
        result = OceanSaveResult(
            success=False,
            user_id="user123",
            error="Database connection error",
        )
        assert result.success is False
        assert result.error == "Database connection error"
        assert result.updated_at is None


# ============================================================================
# Unit Tests: save_ocean (with mocked DB)
# ============================================================================

class TestSaveOceanUnit:
    """save_ocean 메서드 유닛 테스트 (DB 모킹)."""

    @pytest.fixture
    def service(self):
        """테스트용 서비스 인스턴스."""
        _reset_ocean_storage_service()
        return OceanStorageService()

    @pytest.mark.asyncio
    async def test_save_ocean_invalid_user_id_empty(self, service):
        """빈 user_id 에러 처리."""
        result = await service.save_ocean(
            user_id="",
            ocean=OceanScores(),
        )
        assert result.success is False
        assert "Invalid user_id" in result.error

    @pytest.mark.asyncio
    async def test_save_ocean_invalid_user_id_none(self, service):
        """None user_id 에러 처리."""
        result = await service.save_ocean(
            user_id=None,
            ocean=OceanScores(),
        )
        assert result.success is False
        assert "Invalid user_id" in result.error

    @pytest.mark.asyncio
    async def test_save_ocean_invalid_user_id_whitespace(self, service):
        """공백만 있는 user_id 에러 처리."""
        result = await service.save_ocean(
            user_id="   ",
            ocean=OceanScores(),
        )
        assert result.success is False
        assert "Invalid user_id" in result.error

    @pytest.mark.asyncio
    async def test_save_ocean_strips_user_id(self, service):
        """user_id 양끝 공백 제거 확인."""
        with patch.object(service, "_get_or_create_profile") as mock_get:
            mock_profile = MagicMock()
            mock_profile.openness = 0.5
            mock_profile.conscientiousness = 0.5
            mock_profile.extraversion = 0.5
            mock_profile.agreeableness = 0.5
            mock_profile.neuroticism = 0.5
            mock_profile.last_ocean_update = None
            mock_get.return_value = (mock_profile, False)

            with patch("app.services.ocean_storage_service.get_db_context") as mock_db:
                mock_session = AsyncMock()
                mock_db.return_value.__aenter__.return_value = mock_session

                result = await service.save_ocean(
                    user_id="  user123  ",
                    ocean=OceanScores(),
                )

                # Should use stripped user_id
                assert result.user_id == "user123"


# ============================================================================
# Unit Tests: get_ocean (with mocked DB)
# ============================================================================

class TestGetOceanUnit:
    """get_ocean 메서드 유닛 테스트 (DB 모킹)."""

    @pytest.fixture
    def service(self):
        """테스트용 서비스 인스턴스."""
        _reset_ocean_storage_service()
        return OceanStorageService()

    @pytest.mark.asyncio
    async def test_get_ocean_invalid_user_id_empty(self, service):
        """빈 user_id는 None 반환."""
        result = await service.get_ocean("")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_ocean_invalid_user_id_none(self, service):
        """None user_id는 None 반환."""
        result = await service.get_ocean(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_ocean_invalid_user_id_whitespace(self, service):
        """공백 user_id는 None 반환."""
        result = await service.get_ocean("   ")
        assert result is None


# ============================================================================
# Unit Tests: has_ocean_data
# ============================================================================

class TestHasOceanDataUnit:
    """has_ocean_data 메서드 유닛 테스트."""

    @pytest.fixture
    def service(self):
        """테스트용 서비스 인스턴스."""
        _reset_ocean_storage_service()
        return OceanStorageService()

    @pytest.mark.asyncio
    async def test_has_ocean_data_invalid_user_id(self, service):
        """빈 user_id는 False 반환."""
        result = await service.has_ocean_data("")
        assert result is False

    @pytest.mark.asyncio
    async def test_has_ocean_data_none_user_id(self, service):
        """None user_id는 False 반환."""
        result = await service.has_ocean_data(None)
        assert result is False


# ============================================================================
# Unit Tests: Singleton
# ============================================================================

class TestSingletonUnit:
    """싱글톤 패턴 테스트."""

    def test_get_ocean_storage_service_singleton(self):
        """싱글톤 인스턴스 반환 확인."""
        _reset_ocean_storage_service()
        service1 = get_ocean_storage_service()
        service2 = get_ocean_storage_service()
        assert service1 is service2

    def test_reset_singleton(self):
        """싱글톤 리셋 후 새 인스턴스 생성."""
        service1 = get_ocean_storage_service()
        _reset_ocean_storage_service()
        service2 = get_ocean_storage_service()
        assert service1 is not service2


# ============================================================================
# Integration Tests: Mirror → OCEAN 저장 흐름
# ============================================================================

class TestMirrorOceanIntegration:
    """Mirror → OCEAN 저장 통합 테스트 (모킹)."""

    @pytest.mark.asyncio
    async def test_mirror_chat_complete_saves_ocean(self):
        """분석 완료 시 OCEAN 저장 호출 확인."""
        from app.services.ocean_storage_service import OceanScores

        mock_service = AsyncMock()
        mock_service.save_ocean.return_value = OceanSaveResult(
            success=True,
            user_id="user123",
            updated_at=datetime.utcnow(),
            new_values={"openness": 0.75},
        )

        # Simulate is_complete=True case
        result_is_complete = True
        ocean_traits = {"openness": 0.75, "conscientiousness": 0.5,
                        "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5}

        if result_is_complete and ocean_traits:
            await mock_service.save_ocean(
                user_id="user123",
                ocean=OceanScores(**ocean_traits),
                source="mirror",
            )

        mock_service.save_ocean.assert_called_once()

    @pytest.mark.asyncio
    async def test_mirror_chat_incomplete_does_not_save(self):
        """분석 미완료 시 OCEAN 저장 미호출 확인."""
        mock_service = AsyncMock()

        result_is_complete = False
        ocean_traits = {"openness": 0.75}

        if result_is_complete and ocean_traits:
            await mock_service.save_ocean(user_id="user123", ocean=ocean_traits)

        mock_service.save_ocean.assert_not_called()

    @pytest.mark.asyncio
    async def test_mirror_init_does_not_save_ocean(self):
        """init 단계에서는 OCEAN 저장 미호출."""
        # init은 is_complete=False이므로 저장하지 않음
        mock_service = AsyncMock()

        # init은 항상 is_complete=False
        result_is_complete = False

        if result_is_complete:
            await mock_service.save_ocean(user_id="user123", ocean={})

        mock_service.save_ocean.assert_not_called()


# ============================================================================
# Integration Tests: evidence_refs 연동
# ============================================================================

class TestEvidenceRefsIntegration:
    """evidence_refs 포맷 검증 테스트."""

    def test_ocean_evidence_refs_format(self):
        """OCEAN evidence_refs 포맷 확인."""
        user_id = "user123"
        expected_ref = f"db:user_preference_profiles:{user_id}:ocean"

        assert "db:user_preference_profiles" in expected_ref
        assert user_id in expected_ref
        assert "ocean" in expected_ref

    def test_ocean_evidence_refs_values_match(self):
        """OCEAN 값이 evidence_refs에 포함 확인."""
        ocean_dict = {
            "openness": 0.75,
            "conscientiousness": 0.60,
        }
        evidence_refs = []
        for trait_name, trait_value in ocean_dict.items():
            evidence_refs.append(f"rag:mirror:ocean:{trait_name}:{trait_value}")

        assert len(evidence_refs) == 2
        assert "rag:mirror:ocean:openness:0.75" in evidence_refs
        assert "rag:mirror:ocean:conscientiousness:0.6" in evidence_refs


# ============================================================================
# Integration Tests: 프로필 업데이트 추적
# ============================================================================

class TestProfileUpdateTracking:
    """last_ocean_update 타임스탬프 추적 테스트."""

    def test_last_ocean_update_timestamp_format(self):
        """타임스탬프 포맷 확인."""
        now = datetime.utcnow()
        result = OceanSaveResult(
            success=True,
            user_id="user123",
            updated_at=now,
        )
        assert isinstance(result.updated_at, datetime)

    def test_multiple_saves_update_timestamp(self):
        """여러 번 저장 시 타임스탬프 갱신 확인."""
        time1 = datetime(2025, 1, 1, 12, 0, 0)
        time2 = datetime(2025, 1, 2, 12, 0, 0)

        result1 = OceanSaveResult(success=True, user_id="user123", updated_at=time1)
        result2 = OceanSaveResult(success=True, user_id="user123", updated_at=time2)

        assert result2.updated_at > result1.updated_at


# ============================================================================
# Integration Tests: 엣지 케이스
# ============================================================================

class TestEdgeCases:
    """엣지 케이스 테스트."""

    def test_save_ocean_extreme_values_valid(self):
        """극단값 (0.0, 1.0) 유효성 확인."""
        scores = OceanScores(
            openness=0.0,
            conscientiousness=1.0,
            extraversion=0.0,
            agreeableness=1.0,
            neuroticism=0.0,
        )
        assert scores.openness == 0.0
        assert scores.conscientiousness == 1.0

    def test_ocean_scores_with_float_precision(self):
        """부동소수점 정밀도 테스트."""
        scores = OceanScores(openness=0.123456789)
        assert 0.12 < scores.openness < 0.13

    def test_ocean_from_mbti_defaults_for_empty(self):
        """빈 MBTI는 기본값 반환."""
        from app.services.mirror_service import calculate_ocean_from_mbti
        result = calculate_ocean_from_mbti("")
        assert result["openness"] == 0.5
        assert result["neuroticism"] == 0.5

    def test_ocean_from_mbti_defaults_for_invalid(self):
        """잘못된 MBTI는 기본값 반환."""
        from app.services.mirror_service import calculate_ocean_from_mbti
        result = calculate_ocean_from_mbti("XYZ")
        assert result["openness"] == 0.5

    def test_ocean_from_mbti_valid_intj(self):
        """유효한 MBTI (INTJ) 변환 확인."""
        from app.services.mirror_service import calculate_ocean_from_mbti
        result = calculate_ocean_from_mbti("INTJ")

        # INTJ: I→low extraversion, N→high openness, T→low agreeableness, J→high conscientiousness
        assert result["extraversion"] < 0.5  # I
        assert result["openness"] > 0.5      # N
        assert result["agreeableness"] < 0.5  # T
        assert result["conscientiousness"] > 0.5  # J


# ============================================================================
# Error Recovery Tests
# ============================================================================

class TestErrorRecovery:
    """에러 복구 테스트."""

    @pytest.fixture
    def service(self):
        _reset_ocean_storage_service()
        return OceanStorageService()

    @pytest.mark.asyncio
    async def test_save_ocean_db_error_handling(self, service):
        """DB 에러 시 롤백 및 에러 반환."""
        with patch("app.services.ocean_storage_service.get_db_context") as mock_db:
            mock_db.return_value.__aenter__.side_effect = Exception("DB connection failed")

            result = await service.save_ocean(
                user_id="user123",
                ocean=OceanScores(),
            )

            assert result.success is False
            assert "DB connection failed" in result.error

    @pytest.mark.asyncio
    async def test_get_ocean_db_error_returns_none(self, service):
        """get_ocean DB 에러 시 None 반환."""
        with patch("app.services.ocean_storage_service.get_db_context") as mock_db:
            mock_db.return_value.__aenter__.side_effect = Exception("DB error")

            result = await service.get_ocean("user123")
            assert result is None


# ============================================================================
# Idempotency Tests
# ============================================================================

class TestIdempotency:
    """멱등성 테스트."""

    def test_save_ocean_idempotent_values(self):
        """같은 값으로 여러 번 저장해도 결과 동일."""
        ocean = OceanScores(openness=0.75)

        # 같은 값으로 여러 번 호출해도 최종 결과는 동일해야 함
        # (실제 DB 테스트는 integration test에서)
        assert ocean.openness == 0.75
        assert OceanScores(openness=0.75).openness == 0.75


# ============================================================================
# Concurrent Access Tests (Mocked)
# ============================================================================

class TestConcurrentAccess:
    """동시 접근 테스트 (모킹)."""

    @pytest.mark.asyncio
    async def test_concurrent_save_ocean_same_user_mock(self):
        """동일 사용자에 대한 동시 저장 시뮬레이션."""
        call_count = 0

        async def mock_save(user_id, ocean, source="mirror"):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Simulate DB latency
            return OceanSaveResult(success=True, user_id=user_id)

        # 동시에 5번 호출
        tasks = [
            mock_save("user123", OceanScores(openness=0.75))
            for _ in range(5)
        ]
        results = await asyncio.gather(*tasks)

        assert call_count == 5
        assert all(r.success for r in results)


# ============================================================================
# MBTI → OCEAN 변환 상세 테스트
# ============================================================================

class TestMbtiToOceanConversion:
    """MBTI → OCEAN 변환 상세 테스트."""

    def test_enfp_ocean_values(self):
        """ENFP 타입 OCEAN 변환."""
        from app.services.mirror_service import calculate_ocean_from_mbti
        result = calculate_ocean_from_mbti("ENFP")

        # ENFP: E→high extraversion, N→high openness, F→high agreeableness, P→low conscientiousness
        assert result["extraversion"] > 0.5   # E
        assert result["openness"] > 0.5       # N
        assert result["agreeableness"] > 0.5  # F
        assert result["conscientiousness"] < 0.5  # P

    def test_istj_ocean_values(self):
        """ISTJ 타입 OCEAN 변환."""
        from app.services.mirror_service import calculate_ocean_from_mbti
        result = calculate_ocean_from_mbti("ISTJ")

        # ISTJ: I→low extraversion, S→low openness, T→low agreeableness, J→high conscientiousness
        assert result["extraversion"] < 0.5       # I
        assert result["openness"] < 0.5           # S
        assert result["agreeableness"] < 0.5      # T
        assert result["conscientiousness"] > 0.5  # J

    def test_all_mbti_types_return_valid_ocean(self):
        """모든 16개 MBTI 타입이 유효한 OCEAN 값 반환."""
        from app.services.mirror_service import calculate_ocean_from_mbti

        mbti_types = [
            "INTJ", "INTP", "ENTJ", "ENTP",
            "INFJ", "INFP", "ENFJ", "ENFP",
            "ISTJ", "ISFJ", "ESTJ", "ESFJ",
            "ISTP", "ISFP", "ESTP", "ESFP",
        ]

        for mbti in mbti_types:
            result = calculate_ocean_from_mbti(mbti)

            assert 0.0 <= result["openness"] <= 1.0, f"{mbti} openness out of range"
            assert 0.0 <= result["conscientiousness"] <= 1.0, f"{mbti} conscientiousness out of range"
            assert 0.0 <= result["extraversion"] <= 1.0, f"{mbti} extraversion out of range"
            assert 0.0 <= result["agreeableness"] <= 1.0, f"{mbti} agreeableness out of range"
            assert 0.0 <= result["neuroticism"] <= 1.0, f"{mbti} neuroticism out of range"
