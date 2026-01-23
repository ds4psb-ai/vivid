"""Tests for app.core.unified_state."""
import pytest

from app.core.unified_state import (
    UnifiedState,
    create_initial_state,
    state_with_classification,
    state_with_routing,
    state_with_retrieval,
    state_with_response,
    state_with_error,
    get_context_for_llm,
    should_skip_node,
)
from app.core.unified_schemas import (
    QueryType,
    Intent,
    Dimension,
    OrchestrationPattern,
)


class TestCreateInitialState:
    """create_initial_state 테스트."""

    def test_basic_creation(self):
        """기본 상태 생성."""
        state = create_initial_state(query="테스트 쿼리")

        assert state["query"] == "테스트 쿼리"
        assert state["query_type"] == QueryType.AMBIGUOUS
        assert state["intent"] == Intent.UNKNOWN
        assert state["confidence"] == 0.0
        assert state["skip_retrieval"] is False
        assert state["selected_sources"] == []
        assert state["selected_tools"] == []
        assert state["retrieved_docs"] == []
        assert state["evidence_refs"] == []
        assert state["request_id"] is not None

    def test_with_user_id(self):
        """사용자 ID 포함."""
        state = create_initial_state(
            query="테스트",
            user_id="user_123",
            session_id="session_456",
        )

        assert state["user_id"] == "user_123"
        assert state["session_id"] == "session_456"

    def test_with_dimension(self):
        """차원 지정."""
        state = create_initial_state(
            query="테스트",
            dimension="4D",
        )

        assert state["dimension"] == Dimension.MOMENT

    def test_with_invalid_dimension(self):
        """잘못된 차원은 None으로 처리."""
        state = create_initial_state(
            query="테스트",
            dimension="INVALID",
        )

        assert state["dimension"] is None

    def test_with_auteur_key(self):
        """거장 키 지정."""
        state = create_initial_state(
            query="테스트",
            auteur_key="bong",
        )

        assert state["auteur_key"] == "bong"

    def test_with_request_id(self):
        """요청 ID 지정."""
        state = create_initial_state(
            query="테스트",
            request_id="req_123",
        )

        assert state["request_id"] == "req_123"


class TestStateUpdaters:
    """상태 업데이트 함수 테스트."""

    def test_state_with_classification(self):
        """분류 결과 업데이트."""
        initial = create_initial_state(query="테스트")

        updated = state_with_classification(
            initial,
            query_type=QueryType.DOMAIN_SPECIFIC,
            intent=Intent.ANALYZE,
            confidence=0.85,
            skip_retrieval=False,
            dimension=Dimension.MOMENT,
            auteur_key="bong",
        )

        assert updated["query_type"] == QueryType.DOMAIN_SPECIFIC
        assert updated["intent"] == Intent.ANALYZE
        assert updated["confidence"] == 0.85
        assert updated["dimension"] == Dimension.MOMENT
        assert updated["auteur_key"] == "bong"
        # 원본 필드 유지
        assert updated["query"] == "테스트"

    def test_state_with_routing(self):
        """라우팅 결정 업데이트."""
        initial = create_initial_state(query="테스트")

        updated = state_with_routing(
            initial,
            selected_sources=["notebooklm", "qdrant"],
            selected_tools=["4D"],
            strategy="ensemble_rrf",
            pattern=OrchestrationPattern.DIRECT,
            sub_queries=["서브쿼리1"],
        )

        assert updated["selected_sources"] == ["notebooklm", "qdrant"]
        assert updated["selected_tools"] == ["4D"]
        assert updated["strategy"] == "ensemble_rrf"
        assert updated["pattern"] == OrchestrationPattern.DIRECT
        assert updated["sub_queries"] == ["서브쿼리1"]

    def test_state_with_retrieval(self):
        """검색 결과 업데이트."""
        initial = create_initial_state(query="테스트")

        docs = [{"id": "doc1", "content": "내용1", "score": 0.9, "source": "qdrant"}]
        refs = ["db:qdrant:doc1"]

        updated = state_with_retrieval(
            initial,
            retrieved_docs=docs,
            evidence_refs=refs,
        )

        assert updated["retrieved_docs"] == docs
        assert updated["evidence_refs"] == refs

    def test_state_with_response(self):
        """최종 응답 업데이트."""
        initial = create_initial_state(query="테스트")

        updated = state_with_response(
            initial,
            final_response="응답 텍스트",
            total_latency_ms=150.0,
        )

        assert updated["final_response"] == "응답 텍스트"
        assert updated["total_latency_ms"] == 150.0

    def test_state_with_error(self):
        """에러 상태 업데이트."""
        initial = create_initial_state(query="테스트")

        updated = state_with_error(
            initial,
            error="Something went wrong",
        )

        assert updated["error"] == "Something went wrong"


class TestGetContextForLLM:
    """get_context_for_llm 테스트."""

    def test_empty_docs(self):
        """문서 없을 때."""
        state = create_initial_state(query="테스트")
        context = get_context_for_llm(state)
        assert context == ""

    def test_with_docs(self):
        """문서 있을 때."""
        state = create_initial_state(query="테스트")
        state = state_with_retrieval(
            state,
            retrieved_docs=[
                {"content": "첫 번째 문서", "source": "qdrant"},
                {"content": "두 번째 문서", "source": "notebooklm"},
            ],
            evidence_refs=[],
        )

        context = get_context_for_llm(state)

        assert "[1] (qdrant)" in context
        assert "첫 번째 문서" in context
        assert "[2] (notebooklm)" in context
        assert "두 번째 문서" in context

    def test_max_docs_limit(self):
        """최대 10개 문서 제한."""
        state = create_initial_state(query="테스트")
        docs = [
            {"content": f"문서 {i}", "source": "qdrant"}
            for i in range(15)
        ]
        state = state_with_retrieval(
            state,
            retrieved_docs=docs,
            evidence_refs=[],
        )

        context = get_context_for_llm(state)

        assert "[10]" in context
        assert "[11]" not in context


class TestShouldSkipNode:
    """should_skip_node 테스트."""

    def test_skip_retrieval_when_flag_set(self):
        """skip_retrieval=True일 때 retrieve 스킵."""
        state = create_initial_state(query="테스트")
        state = state_with_classification(
            state,
            query_type=QueryType.SIMPLE_FACTUAL,
            intent=Intent.CHAT,
            confidence=0.9,
            skip_retrieval=True,
        )

        assert should_skip_node(state, "retrieve") is True
        assert should_skip_node(state, "execute") is False

    def test_skip_on_error(self):
        """에러 시 노드 스킵 (generate 제외)."""
        state = create_initial_state(query="테스트")
        state = state_with_error(state, error="에러 발생")

        assert should_skip_node(state, "retrieve") is True
        assert should_skip_node(state, "execute") is True
        assert should_skip_node(state, "generate") is False

    def test_no_skip_normal_state(self):
        """정상 상태에서 스킵 없음."""
        state = create_initial_state(query="테스트")

        assert should_skip_node(state, "retrieve") is False
        assert should_skip_node(state, "execute") is False
        assert should_skip_node(state, "generate") is False
