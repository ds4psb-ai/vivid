"""Tests for app.core.entrypoint."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.entrypoint import (
    unified_query,
    unified_query_from_request,
    unified_query_compat,
    _state_to_response,
)
from app.core.unified_schemas import (
    UnifiedQueryRequest,
    QueryType,
    Intent,
    Dimension,
)


class TestStateToResponse:
    """_state_to_response 테스트."""

    def test_basic_conversion(self):
        """기본 상태 → 응답 변환."""
        state = {
            "query": "테스트",
            "query_type": QueryType.DOMAIN_SPECIFIC,
            "intent": Intent.ANALYZE,
            "confidence": 0.85,
            "final_response": "응답 텍스트",
            "evidence_refs": ["db:qdrant:doc1"],
            "selected_sources": ["qdrant"],
            "dimension": Dimension.MOMENT,
            "auteur_key": "bong",
            "retrieved_docs": [],
            "node_outputs": {},
            "execution_order": [],
            "request_id": "req_123",
        }

        result = _state_to_response(state)

        assert result["final_response"] == "응답 텍스트"
        assert result["query_type"] == "domain_specific"
        assert result["intent"] == "analyze"
        assert result["confidence"] == 0.85
        assert result["evidence_refs"] == ["db:qdrant:doc1"]
        assert result["dimension"] == "4D"
        assert result["auteur_key"] == "bong"

    def test_enum_value_extraction(self):
        """Enum 값 추출."""
        state = {
            "query_type": QueryType.SIMPLE_FACTUAL,
            "intent": Intent.CHAT,
            "dimension": Dimension.ORIGIN,
        }

        result = _state_to_response(state)

        assert result["query_type"] == "simple_factual"
        assert result["intent"] == "chat"
        assert result["dimension"] == "1D"

    def test_none_handling(self):
        """None 값 처리."""
        state = {
            "query_type": None,
            "intent": None,
            "dimension": None,
        }

        result = _state_to_response(state)

        assert result["query_type"] == "ambiguous"
        assert result["intent"] == "unknown"
        assert result["dimension"] is None


class TestUnifiedQuery:
    """unified_query 테스트."""

    @pytest.mark.asyncio
    async def test_query_execution(self):
        """쿼리 실행 테스트."""
        # Mock the graph
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "query": "테스트",
            "query_type": QueryType.DOMAIN_SPECIFIC,
            "intent": Intent.ANALYZE,
            "confidence": 0.85,
            "final_response": "테스트 응답",
            "evidence_refs": [],
            "selected_sources": ["qdrant"],
            "dimension": None,
            "auteur_key": None,
            "retrieved_docs": [],
            "node_outputs": {},
            "execution_order": [],
            "request_id": "req_123",
        })

        with patch("app.core.entrypoint.get_unified_graph", return_value=mock_graph), \
             patch("app.core.entrypoint._check_cache", return_value=None), \
             patch("app.core.entrypoint._save_to_cache", return_value=None):

            result = await unified_query("테스트 쿼리")

            assert result["final_response"] == "테스트 응답"
            assert result["query_type"] == "domain_specific"
            assert result["cache_hit"] is False

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """캐시 히트 테스트."""
        cached_result = {
            "final_response": "캐시된 응답",
            "query_type": "domain_specific",
            "intent": "analyze",
            "confidence": 0.9,
            "evidence_refs": [],
            "sources_used": [],
        }

        with patch("app.core.entrypoint._check_cache", return_value=cached_result):
            result = await unified_query("테스트 쿼리")

            assert result["final_response"] == "캐시된 응답"
            assert result["cache_hit"] is True

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """에러 처리 테스트."""
        with patch("app.core.entrypoint.get_unified_graph") as mock_get_graph, \
             patch("app.core.entrypoint._check_cache", return_value=None):
            mock_get_graph.side_effect = Exception("Graph error")

            result = await unified_query("테스트 쿼리")

            assert "오류" in result["final_response"]
            assert "error" in result
            assert result["cache_hit"] is False


class TestUnifiedQueryFromRequest:
    """unified_query_from_request 테스트."""

    @pytest.mark.asyncio
    async def test_request_processing(self):
        """요청 객체 처리."""
        request = UnifiedQueryRequest(
            query="테스트 쿼리",
            user_id="user_123",
            dimension="4D",
            auteur_key="bong",
        )

        with patch("app.core.entrypoint.unified_query") as mock_query:
            mock_query.return_value = {
                "final_response": "응답",
                "query_type": "domain_specific",
                "intent": "analyze",
                "confidence": 0.85,
                "evidence_refs": [],
                "sources_used": [],
                "dimension": "4D",
                "auteur_key": "bong",
                "latency_ms": 150.0,
                "cache_hit": False,
            }

            result = await unified_query_from_request(request)

            assert result.response == "응답"
            assert result.query_type == "domain_specific"
            assert result.dimension == "4D"

            # 인자 확인
            mock_query.assert_called_once_with(
                query="테스트 쿼리",
                user_id="user_123",
                session_id=None,
                dimension="4D",
                auteur_key="bong",
                skip_cache=False,
            )


class TestUnifiedQueryCompat:
    """unified_query_compat 호환성 래퍼 테스트."""

    @pytest.mark.asyncio
    async def test_compat_wrapper(self):
        """HybridRAGResult 호환 형식 반환."""
        with patch("app.core.entrypoint.unified_query") as mock_query:
            mock_query.return_value = {
                "final_response": "응답",
                "query_type": "domain_specific",
                "intent": "analyze",
                "confidence": 0.85,
                "evidence_refs": ["db:qdrant:doc1"],
                "sources_used": ["qdrant"],
                "retrieved_docs": [{"id": "doc1", "content": "내용"}],
                "latency_ms": 150.0,
            }

            result = await unified_query_compat(
                query="테스트",
                dimension="4D",
                auteur_key="bong",
                strategy="ensemble_rrf",  # ignored
                top_k=10,  # ignored
            )

            # HybridRAGResult 호환 형식 확인
            assert result["response"] == "응답"
            assert result["evidence_refs"] == ["db:qdrant:doc1"]
            assert result["confidence"] == 0.85
            assert "metadata" in result
            assert result["metadata"]["strategy"] == "unified_graph"
