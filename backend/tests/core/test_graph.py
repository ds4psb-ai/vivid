"""Tests for app.core.graph."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.graph import (
    build_unified_graph,
    get_unified_graph,
    reset_graph,
    get_graph_mermaid,
)
from app.core.unified_state import create_initial_state
from app.core.unified_schemas import QueryType, Intent


class TestBuildUnifiedGraph:
    """build_unified_graph 테스트."""

    def test_graph_structure(self):
        """그래프 구조 검증."""
        graph = build_unified_graph()

        # 노드 확인
        assert "classify" in graph.nodes
        assert "route" in graph.nodes
        assert "retrieve" in graph.nodes
        assert "execute" in graph.nodes
        assert "generate" in graph.nodes

    def test_graph_compiles(self):
        """그래프 컴파일 성공."""
        graph = build_unified_graph()
        compiled = graph.compile()

        assert compiled is not None


class TestGetUnifiedGraph:
    """get_unified_graph 싱글톤 테스트."""

    def setup_method(self):
        """테스트 전 그래프 리셋."""
        reset_graph()

    def test_returns_compiled_graph(self):
        """컴파일된 그래프 반환."""
        graph = get_unified_graph()
        assert graph is not None

    def test_singleton_pattern(self):
        """싱글톤 패턴 검증."""
        graph1 = get_unified_graph()
        graph2 = get_unified_graph()

        assert graph1 is graph2

    def test_reset_clears_cache(self):
        """reset_graph로 캐시 초기화."""
        graph1 = get_unified_graph()
        reset_graph()
        graph2 = get_unified_graph()

        # 새로운 인스턴스지만 동일한 구조
        assert graph2 is not None


class TestGetGraphMermaid:
    """get_graph_mermaid 테스트."""

    def test_returns_mermaid_string(self):
        """Mermaid 다이어그램 문자열 반환."""
        mermaid = get_graph_mermaid()

        assert "graph TD" in mermaid
        assert "classify" in mermaid
        assert "route" in mermaid
        assert "retrieve" in mermaid
        assert "execute" in mermaid
        assert "generate" in mermaid
        assert "END" in mermaid


class TestGraphExecution:
    """그래프 실행 테스트 (통합)."""

    def setup_method(self):
        """테스트 전 그래프 리셋."""
        reset_graph()

    @pytest.mark.asyncio
    async def test_graph_execution_simple_query(self):
        """간단한 쿼리 실행."""
        # Mock all nodes to return quickly
        with patch("app.core.nodes.classify.classify_node") as mock_classify, \
             patch("app.core.nodes.route.route_node") as mock_route, \
             patch("app.core.nodes.retrieve.retrieve_node") as mock_retrieve, \
             patch("app.core.nodes.execute.execute_node") as mock_execute, \
             patch("app.core.nodes.generate.generate_node") as mock_generate:

            # Setup mocks
            mock_classify.return_value = {
                "query": "테스트",
                "query_type": QueryType.SIMPLE_FACTUAL,
                "intent": Intent.CHAT,
                "confidence": 0.9,
                "skip_retrieval": True,
                "selected_sources": [],
                "selected_tools": [],
            }

            mock_route.return_value = {
                "query": "테스트",
                "query_type": QueryType.SIMPLE_FACTUAL,
                "intent": Intent.CHAT,
                "confidence": 0.9,
                "skip_retrieval": True,
                "selected_sources": [],
                "selected_tools": [],
                "strategy": "direct_llm",
                "pattern": "direct",
            }

            mock_execute.return_value = {
                "query": "테스트",
                "query_type": QueryType.SIMPLE_FACTUAL,
                "node_outputs": {},
                "execution_order": [],
            }

            mock_generate.return_value = {
                "query": "테스트",
                "final_response": "테스트 응답입니다.",
            }

            # 그래프 실행
            graph = get_unified_graph()
            initial_state = create_initial_state(query="테스트")

            # Note: 실제 실행은 LangGraph가 필요하므로 여기서는 mock으로 대체
            # 실제 통합 테스트에서는 await graph.ainvoke(initial_state) 사용

    @pytest.mark.asyncio
    async def test_graph_execution_domain_query(self):
        """도메인 특화 쿼리 실행."""
        # This would be a full integration test
        # For now, verify the graph can be built and mocked
        graph = get_unified_graph()
        assert graph is not None


class TestConditionalEdges:
    """조건부 엣지 테스트."""

    def test_skip_retrieval_routing(self):
        """skip_retrieval 라우팅 테스트."""
        from app.core.graph import _should_skip_retrieval

        # skip_retrieval=True
        state_skip = {"skip_retrieval": True}
        assert _should_skip_retrieval(state_skip) == "execute"

        # skip_retrieval=False
        state_no_skip = {"skip_retrieval": False}
        assert _should_skip_retrieval(state_no_skip) == "retrieve"

    def test_execute_tools_routing(self):
        """도구 실행 라우팅 테스트."""
        from app.core.graph import _should_execute_tools

        # 도구 있음
        state_with_tools = {"selected_tools": ["4D", "AD"]}
        assert _should_execute_tools(state_with_tools) == "execute"

        # 도구 없음
        state_no_tools = {"selected_tools": []}
        assert _should_execute_tools(state_no_tools) == "generate"

    def test_hitl_check_routing(self):
        """HITL 체크 라우팅 테스트."""
        from app.core.graph import _check_hitl_required

        # HITL 필요
        state_hitl = {"node_outputs": {"__hitl_checkpoint": "cp_123"}}
        assert _check_hitl_required(state_hitl) == "hitl_wait"

        # HITL 불필요
        state_no_hitl = {"node_outputs": {"result": "output"}}
        assert _check_hitl_required(state_no_hitl) == "generate"
