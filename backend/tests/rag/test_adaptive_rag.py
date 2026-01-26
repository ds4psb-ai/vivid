"""
P5 Adaptive RAG Integration Tests.

Tests the full adaptive RAG flow:
- Query Classification → Strategy Selection → Skip/Retrieval
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.rag.query_classifier import QueryType, RoutingConfig


# ============================================================================
# Integration Test: Full Classification Flow
# ============================================================================


class TestAdaptiveRAGIntegration:
    """Integration tests for Adaptive RAG flow."""

    @pytest.fixture
    def mock_semantic_router(self):
        """Mock SemanticRouter for fast testing."""
        with patch("app.rag.semantic_router.get_semantic_router") as mock:
            router = AsyncMock()
            # Default to domain_specific
            router.classify.return_value = (QueryType.DOMAIN_SPECIFIC, 0.85)
            router.classify_with_details.return_value = (
                QueryType.DOMAIN_SPECIFIC,
                0.85,
                "강주노 롱테이크",
            )
            mock.return_value = router
            yield router

    @pytest.fixture
    def mock_llm_classifier(self):
        """Mock LLM classifier."""
        with patch("app.rag.llm_classifier.classify_with_llm") as mock:
            async def return_multi_hop(*args, **kwargs):
                return (QueryType.MULTI_HOP, 0.90)
            mock.side_effect = return_multi_hop
            yield mock

    @pytest.mark.asyncio
    async def test_classify_query_semantic_router(self, mock_semantic_router):
        """Classification uses SemanticRouter first."""
        from app.rag.query_classifier import classify_query

        query_type, confidence = await classify_query("강주노 롱테이크")

        assert query_type == QueryType.DOMAIN_SPECIFIC
        assert confidence == 0.85
        mock_semantic_router.classify.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_query_llm_fallback(self, mock_semantic_router, mock_llm_classifier):
        """Classification falls back to LLM when confidence is low."""
        from app.rag.query_classifier import classify_query

        # Semantic router returns AMBIGUOUS (below threshold)
        mock_semantic_router.classify.return_value = (QueryType.AMBIGUOUS, 0.5)

        config = RoutingConfig(semantic_threshold=0.7, llm_fallback=True)
        query_type, confidence = await classify_query("복잡한 쿼리", config)

        assert query_type == QueryType.MULTI_HOP
        assert confidence == 0.90
        mock_llm_classifier.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_query_no_llm_fallback(self, mock_semantic_router):
        """Returns AMBIGUOUS when LLM fallback is disabled."""
        from app.rag.query_classifier import classify_query

        mock_semantic_router.classify.return_value = (QueryType.AMBIGUOUS, 0.5)

        config = RoutingConfig(llm_fallback=False)
        query_type, confidence = await classify_query("불확실한 쿼리", config)

        assert query_type == QueryType.AMBIGUOUS
        assert confidence == 0.5


# ============================================================================
# Integration Test: Strategy Selection Flow
# ============================================================================


class TestStrategySelectionIntegration:
    """Integration tests for strategy selection."""

    @pytest.fixture
    def mock_classify_query(self):
        """Mock classify_query function where it's used."""
        # Patch in strategy_selector where it's imported, not where defined
        with patch("app.rag.strategy_selector.classify_query") as mock:
            async def return_domain_specific(*args, **kwargs):
                return (QueryType.DOMAIN_SPECIFIC, 0.85)
            mock.side_effect = return_domain_specific
            yield mock

    @pytest.mark.asyncio
    async def test_select_strategy_domain_specific(self, mock_classify_query):
        """Domain-specific query gets ensemble_rrf strategy."""
        from app.rag.strategy_selector import select_strategy

        strategy = await select_strategy("강주노 롱테이크")

        assert strategy.name == "ensemble_rrf"
        assert strategy.skip_retrieval is False
        assert strategy.use_reranker is True

    @pytest.mark.asyncio
    async def test_select_strategy_simple_factual(self, mock_classify_query):
        """Simple factual query gets direct_llm strategy."""
        from app.rag.strategy_selector import select_strategy

        async def return_simple_factual(*args, **kwargs):
            return (QueryType.SIMPLE_FACTUAL, 0.90)
        mock_classify_query.side_effect = return_simple_factual

        strategy = await select_strategy("Python이란?")

        assert strategy.name == "direct_llm"
        assert strategy.skip_retrieval is True
        assert strategy.use_reranker is False

    @pytest.mark.asyncio
    async def test_select_strategy_multi_hop(self, mock_classify_query):
        """Multi-hop query gets full_pipeline strategy."""
        from app.rag.strategy_selector import select_strategy

        async def return_multi_hop(*args, **kwargs):
            return (QueryType.MULTI_HOP, 0.80)
        mock_classify_query.side_effect = return_multi_hop

        strategy = await select_strategy("왜 기생충이 상징적인가?")

        assert strategy.name == "full_pipeline"
        assert strategy.skip_retrieval is False
        assert strategy.use_reranker is True
        assert strategy.use_grounding is True


# ============================================================================
# Integration Test: Skip Retrieval Flow
# ============================================================================


class TestSkipRetrievalIntegration:
    """Integration tests for skip retrieval in hybrid_query."""

    @pytest.mark.asyncio
    async def test_no_skip_with_auteur_key(self):
        """Query with auteur_key does not skip retrieval."""
        from app.rag.hybrid_rag import _check_skip_retrieval

        result = await _check_skip_retrieval(
            query="Python이란?",
            auteur_key="bong",  # Has domain context
        )

        # Should return None (no skip)
        assert result is None

    @pytest.mark.asyncio
    async def test_no_skip_with_dimension(self):
        """Query with dimension does not skip retrieval."""
        from app.rag.hybrid_rag import _check_skip_retrieval

        result = await _check_skip_retrieval(
            query="Python이란?",
            dimension="1D",  # Has domain context
        )

        # Should return None (no skip)
        assert result is None

    @pytest.mark.asyncio
    async def test_skip_with_simple_factual(self):
        """Simple factual query without context skips retrieval."""
        from app.rag.hybrid_rag import _check_skip_retrieval

        with patch("app.rag.semantic_router.get_semantic_router") as router_mock, \
             patch("app.services.genai_utils.get_genai_client") as genai_mock:

            # Router returns simple_factual
            router = AsyncMock()
            router.classify.return_value = (QueryType.SIMPLE_FACTUAL, 0.92)
            router_mock.return_value = router

            # Mock google-genai client
            mock_response = MagicMock()
            mock_response.text = "Python is a programming language."
            mock_models = MagicMock()
            mock_models.generate_content = AsyncMock(return_value=mock_response)
            mock_aio = MagicMock()
            mock_aio.models = mock_models
            mock_client = MagicMock()
            mock_client.aio = mock_aio
            genai_mock.return_value = mock_client

            result = await _check_skip_retrieval(
                query="Python이란?",
                auteur_key=None,
                dimension=None,
            )

            # Should return a result (skip retrieval)
            assert result is not None
            assert result.strategy_used == "direct_llm"


# ============================================================================
# Integration Test: Full Flow with Different Query Types
# ============================================================================


class TestFullFlowByQueryType:
    """Test full flow for different query types."""

    @pytest.fixture
    def setup_mocks(self):
        """Setup common mocks for strategy selection tests."""
        with patch("app.rag.semantic_router.get_semantic_router") as router_mock:
            router = AsyncMock()
            router_mock.return_value = router
            yield router, None  # Second element unused but keeps signature compatible

    @pytest.mark.asyncio
    async def test_flow_simple_factual(self, setup_mocks):
        """Simple factual flow: classify → direct_llm."""
        from app.rag.strategy_selector import select_strategy_with_details

        router, _ = setup_mocks
        router.classify.return_value = (QueryType.SIMPLE_FACTUAL, 0.90)
        router.classify_with_details.return_value = (QueryType.SIMPLE_FACTUAL, 0.90, "API란?")

        result = await select_strategy_with_details("API란?")

        assert result.query_type == QueryType.SIMPLE_FACTUAL
        assert result.strategy.name == "direct_llm"
        assert result.strategy.skip_retrieval is True

    @pytest.mark.asyncio
    async def test_flow_domain_specific(self, setup_mocks):
        """Domain-specific flow: classify → ensemble_rrf."""
        from app.rag.strategy_selector import select_strategy_with_details

        router, _ = setup_mocks
        router.classify.return_value = (QueryType.DOMAIN_SPECIFIC, 0.88)
        router.classify_with_details.return_value = (
            QueryType.DOMAIN_SPECIFIC,
            0.88,
            "강주노 롱테이크",
        )

        result = await select_strategy_with_details("강주노 감독 스타일")

        assert result.query_type == QueryType.DOMAIN_SPECIFIC
        assert result.strategy.name == "ensemble_rrf"
        assert result.strategy.skip_retrieval is False
        assert result.strategy.use_reranker is True

    @pytest.mark.asyncio
    async def test_flow_recency_required(self, setup_mocks):
        """Recency-required flow: classify → grounding_first."""
        from app.rag.strategy_selector import select_strategy_with_details

        router, _ = setup_mocks
        router.classify.return_value = (QueryType.RECENCY_REQUIRED, 0.85)
        router.classify_with_details.return_value = (
            QueryType.RECENCY_REQUIRED,
            0.85,
            "최신 AI 트렌드",
        )

        result = await select_strategy_with_details("2026년 AI 트렌드")

        assert result.query_type == QueryType.RECENCY_REQUIRED
        assert result.strategy.name == "grounding_first"
        assert result.strategy.use_grounding is True

    @pytest.mark.asyncio
    async def test_flow_multi_hop(self, setup_mocks):
        """Multi-hop flow: classify → full_pipeline."""
        from app.rag.strategy_selector import select_strategy_with_details

        router, _ = setup_mocks
        router.classify.return_value = (QueryType.MULTI_HOP, 0.82)
        router.classify_with_details.return_value = (
            QueryType.MULTI_HOP,
            0.82,
            "비교 분석",
        )

        result = await select_strategy_with_details("강주노와 테오 에포크의 스타일 비교")

        assert result.query_type == QueryType.MULTI_HOP
        assert result.strategy.name == "full_pipeline"
        assert result.strategy.skip_retrieval is False
        assert result.strategy.use_reranker is True
        assert result.strategy.use_grounding is True


# ============================================================================
# Performance Test: Latency Expectations
# ============================================================================


class TestLatencyExpectations:
    """Test that latency expectations are met."""

    def test_strategy_latency_estimates(self):
        """Strategy latency estimates are reasonable."""
        from app.rag.strategy_selector import STRATEGIES

        # Direct LLM should be fastest
        assert STRATEGIES["direct_llm"].estimated_latency_ms <= 150

        # Minimal RAG should be fast
        assert STRATEGIES["minimal_rag"].estimated_latency_ms <= 200

        # Full pipeline should be slowest
        assert STRATEGIES["full_pipeline"].estimated_latency_ms >= 400

    def test_cost_expectations(self):
        """Strategy cost estimates are reasonable."""
        from app.rag.strategy_selector import STRATEGIES

        # Direct LLM should be cheapest
        assert STRATEGIES["direct_llm"].estimated_cost <= 0.002

        # Full pipeline should be most expensive
        assert STRATEGIES["full_pipeline"].estimated_cost >= 0.01

        # Cost should increase with complexity
        assert (
            STRATEGIES["direct_llm"].estimated_cost
            < STRATEGIES["minimal_rag"].estimated_cost
            < STRATEGIES["ensemble_rrf"].estimated_cost
            < STRATEGIES["full_pipeline"].estimated_cost
        )
