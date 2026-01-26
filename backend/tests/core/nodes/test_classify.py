"""Tests for app.core.nodes.classify."""
import pytest
from unittest.mock import AsyncMock, patch

from app.core.nodes.classify import (
    classify_node,
    _heuristic_classify,
    _intent_from_query_type,
)
from app.core.unified_state import create_initial_state
from app.core.unified_schemas import QueryType, Intent


class TestClassifyNode:
    """classify_node 테스트."""

    @pytest.mark.asyncio
    async def test_empty_query(self):
        """빈 쿼리 처리."""
        state = create_initial_state(query="")

        result = await classify_node(state)

        assert result["query_type"] == QueryType.AMBIGUOUS
        assert result["intent"] == Intent.UNKNOWN
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_classification_with_fallback(self):
        """폴백 분류기 사용."""
        # Mock existing classifiers to fail
        with patch("app.core.nodes.classify._classify_with_existing") as mock_classify:
            mock_classify.return_value = (
                QueryType.DOMAIN_SPECIFIC,
                0.85,
                None,
                None,
            )

            state = create_initial_state(query="강주노 롱테이크 분석")
            result = await classify_node(state)

            assert result["query_type"] == QueryType.DOMAIN_SPECIFIC
            assert result["confidence"] == 0.85

    @pytest.mark.asyncio
    async def test_classification_exception_handling(self):
        """분류 예외 처리."""
        with patch("app.core.nodes.classify._classify_with_existing") as mock_classify:
            mock_classify.side_effect = Exception("Classification error")

            state = create_initial_state(query="테스트 쿼리")
            result = await classify_node(state)

            # 에러 시 안전한 기본값
            assert result["query_type"] == QueryType.AMBIGUOUS
            assert result["intent"] == Intent.UNKNOWN
            assert result["confidence"] == 0.0


class TestHeuristicClassify:
    """_heuristic_classify 테스트."""

    def test_simple_factual_patterns(self):
        """단순 사실 쿼리 패턴."""
        assert _heuristic_classify("Python이란 무엇인가요?") == QueryType.SIMPLE_FACTUAL
        assert _heuristic_classify("HTTP란?") == QueryType.SIMPLE_FACTUAL
        assert _heuristic_classify("What is AI?") == QueryType.SIMPLE_FACTUAL

    def test_creative_patterns(self):
        """창작 쿼리 패턴."""
        assert _heuristic_classify("영화 시놉시스 만들어줘") == QueryType.CREATIVE
        assert _heuristic_classify("프롬프트 생성해줘") == QueryType.CREATIVE
        assert _heuristic_classify("캐릭터 이름 써줘") == QueryType.CREATIVE

    def test_domain_specific_patterns(self):
        """도메인 특화 쿼리 패턴."""
        assert _heuristic_classify("강주노 감독의 롱테이크") == QueryType.DOMAIN_SPECIFIC
        assert _heuristic_classify("쿠브릭 스타일 분석") == QueryType.DOMAIN_SPECIFIC
        assert _heuristic_classify("기생충 계단 장면") == QueryType.DOMAIN_SPECIFIC
        assert _heuristic_classify("카메라 워크 설명") == QueryType.DOMAIN_SPECIFIC

    def test_recency_patterns(self):
        """최신 정보 쿼리 패턴."""
        assert _heuristic_classify("2026년 AI 트렌드") == QueryType.RECENCY_REQUIRED
        assert _heuristic_classify("최신 영화 기술") == QueryType.RECENCY_REQUIRED
        assert _heuristic_classify("latest developments") == QueryType.RECENCY_REQUIRED

    def test_multi_hop_patterns(self):
        """복합 추론 쿼리 패턴."""
        assert _heuristic_classify("왜 이 장면이 중요한가?") == QueryType.MULTI_HOP
        assert _heuristic_classify("강주노 vs 테오 에포크 비교") == QueryType.MULTI_HOP
        assert _heuristic_classify("compare the two directors") == QueryType.MULTI_HOP

    def test_ambiguous_fallback(self):
        """분류 불확실 시 AMBIGUOUS."""
        assert _heuristic_classify("안녕하세요") == QueryType.AMBIGUOUS
        assert _heuristic_classify("테스트") == QueryType.AMBIGUOUS


class TestIntentFromQueryType:
    """_intent_from_query_type 테스트."""

    def test_generate_keywords(self):
        """생성 키워드."""
        assert _intent_from_query_type(
            QueryType.CREATIVE, "프롬프트 만들어줘"
        ) == Intent.GENERATE

        assert _intent_from_query_type(
            QueryType.CREATIVE, "이미지 생성해줘"
        ) == Intent.GENERATE

    def test_analyze_keywords(self):
        """분석 키워드."""
        assert _intent_from_query_type(
            QueryType.DOMAIN_SPECIFIC, "이 장면 분석해줘"
        ) == Intent.ANALYZE

        assert _intent_from_query_type(
            QueryType.MULTI_HOP, "왜 이런 연출을 했는지 설명해줘"
        ) == Intent.ANALYZE

    def test_validate_keywords(self):
        """검증 키워드."""
        assert _intent_from_query_type(
            QueryType.DOMAIN_SPECIFIC, "퀄리티 체크해줘"
        ) == Intent.VALIDATE

    def test_fallback_to_query_type(self):
        """QueryType 기반 폴백."""
        # CREATIVE → CREATE
        assert _intent_from_query_type(
            QueryType.CREATIVE, "일반적인 창작 요청"
        ) == Intent.CREATE

        # SIMPLE_FACTUAL → CHAT
        assert _intent_from_query_type(
            QueryType.SIMPLE_FACTUAL, "일반적인 질문"
        ) == Intent.CHAT
