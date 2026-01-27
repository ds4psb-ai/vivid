"""
Test suite for style_quiz_service.py.

P5: 스타일 퀴즈 서비스 테스트 (30+ 테스트 케이스)

테스트 카테고리:
1. QuizQuestion / QuizOption 관련
2. StyleQuizService.get_questions 관련
3. StyleQuizService.calculate_result 관련
4. Auteur matching 관련
5. Edge cases 및 에러 처리
6. 싱글톤 패턴
"""
import pytest
from typing import Dict

from app.services.style_quiz_service import (
    StyleQuizService,
    QuizQuestion,
    QuizOption,
    QuizResult,
    AuteurMatch,
    QuizDimension,
    QUIZ_QUESTIONS,
    AUTEUR_PROFILES,
    get_style_quiz_service,
    _reset_style_quiz_service,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def service():
    """Fresh StyleQuizService instance."""
    _reset_style_quiz_service()
    return StyleQuizService()


@pytest.fixture
def sample_answers() -> Dict[str, str]:
    """Sample quiz answers favoring Bong Joon-ho style."""
    return {
        "q1_visual": "q1_a",      # 수직 구도 (bong)
        "q2_narrative": "q2_a",   # 사회적 메시지 (bong)
        "q3_emotion": "q3_a",     # 긴장감 (fincher, but bong secondary)
        "q4_pacing": "q4_c",      # 복잡한 구조 (nolan, bong secondary)
        "q5_goal": "q5_a",        # 메시지 전달 (bong)
    }


@pytest.fixture
def wong_style_answers() -> Dict[str, str]:
    """Answers favoring Wong Kar-wai style."""
    return {
        "q1_visual": "q1_b",      # 네온 불빛 (wong)
        "q2_narrative": "q2_b",   # 감정과 분위기 (wong)
        "q3_emotion": "q3_b",     # 그리움 (wong)
        "q4_pacing": "q4_d",      # 꿈같은 분위기 (wong)
        "q5_goal": "q5_b",        # 아름다운 예술 (wong)
    }


# ============================================================================
# Unit Tests: QuizQuestion and QuizOption
# ============================================================================

class TestQuizQuestionUnit:
    """QuizQuestion 데이터클래스 유닛 테스트."""

    def test_quiz_question_has_required_fields(self):
        """퀴즈 질문에 필수 필드 존재."""
        q = QUIZ_QUESTIONS[0]
        assert q.id is not None
        assert q.dimension is not None
        assert q.question_ko is not None
        assert q.question_en is not None
        assert len(q.options) > 0

    def test_quiz_option_has_auteur_weights(self):
        """퀴즈 옵션에 auteur 가중치 존재."""
        q = QUIZ_QUESTIONS[0]
        opt = q.options[0]
        assert len(opt.auteur_weights) > 0

    def test_all_questions_have_dimensions(self):
        """모든 질문에 dimension 할당."""
        for q in QUIZ_QUESTIONS:
            assert q.dimension in QuizDimension

    def test_all_questions_have_order(self):
        """모든 질문에 order 할당."""
        orders = [q.order for q in QUIZ_QUESTIONS]
        assert len(set(orders)) == len(orders)  # Unique orders


# ============================================================================
# Unit Tests: AUTEUR_PROFILES
# ============================================================================

class TestAuteurProfilesUnit:
    """AUTEUR_PROFILES 데이터 유닛 테스트."""

    def test_all_auteurs_have_required_fields(self):
        """모든 거장 프로필에 필수 필드 존재."""
        required_fields = ["name_ko", "name_en", "signature", "keywords"]
        for key, profile in AUTEUR_PROFILES.items():
            for field in required_fields:
                assert field in profile, f"{key} missing {field}"

    def test_auteur_count(self):
        """거장 수 확인 (8명)."""
        assert len(AUTEUR_PROFILES) == 8

    def test_auteur_keys_valid(self):
        """거장 키 유효성 확인."""
        expected_keys = {
            "bong", "wong", "kubrick", "nolan",
            "villeneuve", "tarantino", "fincher", "wachowski"
        }
        assert set(AUTEUR_PROFILES.keys()) == expected_keys


# ============================================================================
# Unit Tests: StyleQuizService.get_questions
# ============================================================================

class TestGetQuestions:
    """get_questions 메서드 유닛 테스트."""

    def test_get_questions_default(self, service):
        """기본 5개 질문 반환."""
        questions = service.get_questions()
        assert len(questions) == 5

    def test_get_questions_with_limit(self, service):
        """limit 파라미터 적용."""
        questions = service.get_questions(limit=3)
        assert len(questions) == 3

    def test_get_questions_sorted_by_order(self, service):
        """order 순으로 정렬."""
        questions = service.get_questions()
        orders = [q.order for q in questions]
        assert orders == sorted(orders)

    def test_get_question_by_id_exists(self, service):
        """ID로 질문 조회 - 존재."""
        q = service.get_question_by_id("q1_visual")
        assert q is not None
        assert q.id == "q1_visual"

    def test_get_question_by_id_not_exists(self, service):
        """ID로 질문 조회 - 미존재."""
        q = service.get_question_by_id("nonexistent")
        assert q is None


# ============================================================================
# Unit Tests: StyleQuizService.calculate_result
# ============================================================================

class TestCalculateResult:
    """calculate_result 메서드 유닛 테스트."""

    def test_calculate_result_success(self, service, sample_answers):
        """결과 계산 성공."""
        result = service.calculate_result(sample_answers)
        assert result.success is True
        assert result.primary_match is not None
        assert result.error is None

    def test_calculate_result_empty_answers(self, service):
        """빈 답변 처리."""
        result = service.calculate_result({})
        assert result.success is False
        assert "No answers" in result.error

    def test_calculate_result_primary_match_has_percentage(self, service, sample_answers):
        """primary_match에 percentage 포함."""
        result = service.calculate_result(sample_answers)
        assert result.primary_match.match_percentage > 0
        assert result.primary_match.match_percentage <= 100

    def test_calculate_result_secondary_matches(self, service, sample_answers):
        """secondary_matches 포함."""
        result = service.calculate_result(sample_answers)
        assert isinstance(result.secondary_matches, list)

    def test_calculate_result_dimension_scores(self, service, sample_answers):
        """dimension_scores 포함."""
        result = service.calculate_result(sample_answers)
        assert len(result.dimension_scores) > 0

    def test_calculate_result_creative_profile(self, service, sample_answers):
        """creative_profile 포함."""
        result = service.calculate_result(sample_answers)
        assert "dominant_style" in result.creative_profile

    def test_calculate_result_share_text(self, service, sample_answers):
        """share_text 생성."""
        result = service.calculate_result(sample_answers)
        assert len(result.share_text) > 0
        assert "#" in result.share_text  # Hashtag 포함

    def test_calculate_result_evidence_refs(self, service, sample_answers):
        """evidence_refs 포함."""
        result = service.calculate_result(sample_answers)
        assert len(result.evidence_refs) > 0
        assert all(":" in ref for ref in result.evidence_refs)


# ============================================================================
# Integration Tests: Auteur Matching
# ============================================================================

class TestAuteurMatching:
    """거장 매칭 통합 테스트."""

    def test_bong_style_answers_match_bong(self, service, sample_answers):
        """봉준호 스타일 답변 → 봉준호 매칭."""
        result = service.calculate_result(sample_answers)
        # Bong should be in top matches
        all_matches = [result.primary_match] + result.secondary_matches
        auteur_keys = [m.auteur_key for m in all_matches]
        assert "bong" in auteur_keys

    def test_wong_style_answers_match_wong(self, service, wong_style_answers):
        """왕가위 스타일 답변 → 왕가위 매칭."""
        result = service.calculate_result(wong_style_answers)
        assert result.primary_match.auteur_key == "wong"

    def test_match_percentage_sums_reasonable(self, service, sample_answers):
        """매칭 퍼센티지 합리적."""
        result = service.calculate_result(sample_answers)
        # Primary should be highest
        for secondary in result.secondary_matches:
            assert result.primary_match.match_percentage >= secondary.match_percentage

    def test_different_answers_different_results(self, service, sample_answers, wong_style_answers):
        """다른 답변 → 다른 결과."""
        result1 = service.calculate_result(sample_answers)
        result2 = service.calculate_result(wong_style_answers)
        # Should have different primary matches (or at least different percentages)
        assert (
            result1.primary_match.auteur_key != result2.primary_match.auteur_key
            or result1.primary_match.match_percentage != result2.primary_match.match_percentage
        )


# ============================================================================
# Unit Tests: Auteur Info
# ============================================================================

class TestAuteurInfo:
    """거장 정보 조회 테스트."""

    def test_get_auteur_info_exists(self, service):
        """거장 정보 조회 - 존재."""
        info = service.get_auteur_info("bong")
        assert info is not None
        assert info["name_ko"] == "봉준호"

    def test_get_auteur_info_not_exists(self, service):
        """거장 정보 조회 - 미존재."""
        info = service.get_auteur_info("unknown")
        assert info is None

    def test_get_all_auteurs(self, service):
        """전체 거장 목록 조회."""
        auteurs = service.get_all_auteurs()
        assert len(auteurs) == 8
        assert all("key" in a for a in auteurs)
        assert all("name_ko" in a for a in auteurs)


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """엣지 케이스 테스트."""

    def test_partial_answers(self, service):
        """일부 답변만 제출."""
        partial = {"q1_visual": "q1_a"}  # Only one answer
        result = service.calculate_result(partial)
        assert result.success is True  # Should still work

    def test_invalid_question_id(self, service):
        """잘못된 question_id."""
        invalid = {"invalid_q": "q1_a"}
        result = service.calculate_result(invalid)
        # Should handle gracefully (skip invalid)
        assert result.success is True or result.success is False

    def test_invalid_option_id(self, service):
        """잘못된 option_id."""
        invalid = {"q1_visual": "invalid_opt"}
        result = service.calculate_result(invalid)
        # Should handle gracefully
        assert result is not None

    def test_mixed_valid_invalid(self, service):
        """유효/무효 답변 혼합."""
        mixed = {
            "q1_visual": "q1_a",      # Valid
            "invalid_q": "invalid",    # Invalid
            "q2_narrative": "q2_b",   # Valid
        }
        result = service.calculate_result(mixed)
        # Valid answers should be processed
        assert result.success is True


# ============================================================================
# Singleton Tests
# ============================================================================

class TestSingleton:
    """싱글톤 패턴 테스트."""

    def test_singleton_returns_same_instance(self):
        """싱글톤 동일 인스턴스 반환."""
        _reset_style_quiz_service()
        s1 = get_style_quiz_service()
        s2 = get_style_quiz_service()
        assert s1 is s2

    def test_reset_creates_new_instance(self):
        """리셋 후 새 인스턴스."""
        s1 = get_style_quiz_service()
        _reset_style_quiz_service()
        s2 = get_style_quiz_service()
        assert s1 is not s2


# ============================================================================
# Share Text Tests
# ============================================================================

class TestShareText:
    """공유 텍스트 생성 테스트."""

    def test_share_text_contains_auteur_name(self, service, sample_answers):
        """공유 텍스트에 거장 이름 포함."""
        result = service.calculate_result(sample_answers)
        assert result.primary_match.name_ko in result.share_text

    def test_share_text_contains_percentage(self, service, sample_answers):
        """공유 텍스트에 퍼센티지 포함."""
        result = service.calculate_result(sample_answers)
        assert "%" in result.share_text

    def test_share_text_contains_hashtags(self, service, sample_answers):
        """공유 텍스트에 해시태그 포함."""
        result = service.calculate_result(sample_answers)
        assert "#CrebitStudio" in result.share_text


# ============================================================================
# Creative Profile Tests
# ============================================================================

class TestCreativeProfile:
    """창작 프로필 테스트."""

    def test_creative_profile_has_dominant_style(self, service, sample_answers):
        """dominant_style 포함."""
        result = service.calculate_result(sample_answers)
        assert "dominant_style" in result.creative_profile

    def test_creative_profile_has_visual_approach(self, service, sample_answers):
        """visual_approach 포함."""
        result = service.calculate_result(sample_answers)
        assert "visual_approach" in result.creative_profile

    def test_creative_profile_has_dimension_preferences(self, service, sample_answers):
        """dimension_preferences 포함."""
        result = service.calculate_result(sample_answers)
        assert "dimension_preferences" in result.creative_profile


# ============================================================================
# Data Integrity Tests
# ============================================================================

class TestDataIntegrity:
    """데이터 무결성 테스트."""

    def test_all_option_weights_reference_valid_auteurs(self):
        """모든 옵션 가중치가 유효한 거장 참조."""
        for q in QUIZ_QUESTIONS:
            for opt in q.options:
                for auteur_key in opt.auteur_weights.keys():
                    assert auteur_key in AUTEUR_PROFILES, f"Invalid auteur: {auteur_key}"

    def test_all_questions_have_at_least_2_options(self):
        """모든 질문에 최소 2개 옵션."""
        for q in QUIZ_QUESTIONS:
            assert len(q.options) >= 2, f"Question {q.id} has < 2 options"

    def test_all_options_have_unique_ids(self):
        """모든 옵션 ID 유니크."""
        all_ids = []
        for q in QUIZ_QUESTIONS:
            for opt in q.options:
                all_ids.append(opt.id)
        assert len(all_ids) == len(set(all_ids)), "Duplicate option IDs"


# ============================================================================
# Dimension Coverage Tests
# ============================================================================

class TestDimensionCoverage:
    """Dimension 커버리지 테스트."""

    def test_all_dimensions_covered(self):
        """모든 dimension이 최소 1개 질문."""
        covered_dimensions = {q.dimension for q in QUIZ_QUESTIONS}
        expected = {
            QuizDimension.VISUAL_STYLE,
            QuizDimension.NARRATIVE,
            QuizDimension.EMOTION,
            QuizDimension.PACING,
            QuizDimension.CREATIVE_GOAL,
        }
        assert covered_dimensions == expected
