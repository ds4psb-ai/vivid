"""
P5 Query Classifier Unit Tests.

Tests for:
- QueryType enum
- RoutingConfig
- SemanticRouter
- LLM Classifier (mocked)
- Strategy Selector
- Direct LLM Response
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.rag.query_classifier import (
    QueryType,
    QueryClassificationResult,
    RoutingConfig,
    get_strategy,
    should_skip_retrieval,
    STRATEGY_MAP,
    COST_ESTIMATE,
)
from app.rag.strategy_selector import (
    Strategy,
    STRATEGIES,
    get_strategy_for_query_type,
    QUERY_TYPE_TO_STRATEGY,
    list_strategies,
)


# ============================================================================
# QueryType Tests
# ============================================================================


class TestQueryType:
    """QueryType enum tests."""

    def test_all_query_types_exist(self):
        """All expected QueryTypes are defined."""
        expected = {
            "simple_factual",
            "domain_specific",
            "recency_required",
            "multi_hop",
            "creative",
            "ambiguous",
        }
        actual = {qt.value for qt in QueryType}
        assert actual == expected

    def test_query_type_string_value(self):
        """QueryType values are strings."""
        assert QueryType.SIMPLE_FACTUAL.value == "simple_factual"
        assert QueryType.DOMAIN_SPECIFIC.value == "domain_specific"
        assert QueryType.MULTI_HOP.value == "multi_hop"

    def test_query_type_from_string(self):
        """QueryType can be created from string."""
        qt = QueryType("domain_specific")
        assert qt == QueryType.DOMAIN_SPECIFIC

    def test_invalid_query_type_raises(self):
        """Invalid string raises ValueError."""
        with pytest.raises(ValueError):
            QueryType("invalid_type")


# ============================================================================
# RoutingConfig Tests
# ============================================================================


class TestRoutingConfig:
    """RoutingConfig tests."""

    def test_default_values(self):
        """Default routing config has correct values."""
        config = RoutingConfig()
        assert config.enabled is True
        assert config.semantic_threshold == 0.7
        assert config.llm_fallback is True
        assert QueryType.SIMPLE_FACTUAL in config.skip_retrieval_types
        assert QueryType.CREATIVE in config.skip_retrieval_types

    def test_custom_values(self):
        """Custom routing config works."""
        config = RoutingConfig(
            enabled=False,
            semantic_threshold=0.8,
            llm_fallback=False,
            skip_retrieval_types=[QueryType.SIMPLE_FACTUAL],
        )
        assert config.enabled is False
        assert config.semantic_threshold == 0.8
        assert len(config.skip_retrieval_types) == 1

    def test_threshold_validation(self):
        """Semantic threshold must be 0-1."""
        with pytest.raises(ValueError):
            RoutingConfig(semantic_threshold=1.5)
        with pytest.raises(ValueError):
            RoutingConfig(semantic_threshold=-0.1)


# ============================================================================
# Strategy Mapping Tests
# ============================================================================


class TestStrategyMapping:
    """Strategy mapping tests."""

    def test_all_query_types_have_strategy(self):
        """All QueryTypes map to a strategy."""
        for qt in QueryType:
            assert qt in STRATEGY_MAP
            strategy = get_strategy(qt)
            assert strategy in STRATEGIES

    def test_strategy_map_values(self):
        """Strategy map has correct values."""
        assert STRATEGY_MAP[QueryType.SIMPLE_FACTUAL] == "direct_llm"
        assert STRATEGY_MAP[QueryType.DOMAIN_SPECIFIC] == "ensemble_rrf"
        assert STRATEGY_MAP[QueryType.RECENCY_REQUIRED] == "grounding_first"
        assert STRATEGY_MAP[QueryType.MULTI_HOP] == "full_pipeline"
        assert STRATEGY_MAP[QueryType.CREATIVE] == "minimal_rag"
        assert STRATEGY_MAP[QueryType.AMBIGUOUS] == "ensemble_rrf"

    def test_cost_estimates(self):
        """Cost estimates are reasonable."""
        for qt in QueryType:
            cost = COST_ESTIMATE[qt]
            assert 0 < cost < 0.02  # $0 - $0.02 range
        # Direct LLM should be cheapest
        assert COST_ESTIMATE[QueryType.SIMPLE_FACTUAL] < COST_ESTIMATE[QueryType.MULTI_HOP]


# ============================================================================
# Skip Retrieval Tests
# ============================================================================


class TestSkipRetrieval:
    """Skip retrieval logic tests."""

    def test_simple_factual_skips(self):
        """Simple factual queries should skip retrieval."""
        assert should_skip_retrieval(QueryType.SIMPLE_FACTUAL) is True

    def test_creative_skips(self):
        """Creative queries should skip retrieval by default."""
        assert should_skip_retrieval(QueryType.CREATIVE) is True

    def test_domain_specific_does_not_skip(self):
        """Domain-specific queries should not skip retrieval."""
        assert should_skip_retrieval(QueryType.DOMAIN_SPECIFIC) is False

    def test_multi_hop_does_not_skip(self):
        """Multi-hop queries should not skip retrieval."""
        assert should_skip_retrieval(QueryType.MULTI_HOP) is False

    def test_custom_config_skip_types(self):
        """Custom config can change skip behavior."""
        config = RoutingConfig(
            skip_retrieval_types=[QueryType.DOMAIN_SPECIFIC]
        )
        # Domain-specific now skips
        assert should_skip_retrieval(QueryType.DOMAIN_SPECIFIC, config) is True
        # Simple factual no longer skips (not in list)
        assert should_skip_retrieval(QueryType.SIMPLE_FACTUAL, config) is False


# ============================================================================
# Strategy Selector Tests
# ============================================================================


class TestStrategySelector:
    """Strategy selector tests."""

    def test_all_strategies_defined(self):
        """All strategy names are defined."""
        expected = {"direct_llm", "minimal_rag", "ensemble_rrf", "grounding_first", "full_pipeline"}
        actual = set(STRATEGIES.keys())
        assert actual == expected

    def test_strategy_properties(self):
        """Strategies have correct properties."""
        # Direct LLM should skip retrieval
        direct = STRATEGIES["direct_llm"]
        assert direct.skip_retrieval is True
        assert direct.use_reranker is False
        assert len(direct.backends) == 0

        # Full pipeline should use everything
        full = STRATEGIES["full_pipeline"]
        assert full.skip_retrieval is False
        assert full.use_reranker is True
        assert full.use_grounding is True
        assert "tavily_grounding" in full.backends

    def test_get_strategy_for_query_type(self):
        """get_strategy_for_query_type returns correct Strategy."""
        strategy = get_strategy_for_query_type(QueryType.SIMPLE_FACTUAL)
        assert strategy.name == "direct_llm"

        strategy = get_strategy_for_query_type(QueryType.DOMAIN_SPECIFIC)
        assert strategy.name == "ensemble_rrf"

    def test_list_strategies(self):
        """list_strategies returns all strategy names."""
        strategies = list_strategies()
        assert len(strategies) == 5
        assert "direct_llm" in strategies
        assert "full_pipeline" in strategies


# ============================================================================
# QueryClassificationResult Tests
# ============================================================================


class TestQueryClassificationResult:
    """QueryClassificationResult tests."""

    def test_create_result(self):
        """Can create classification result."""
        result = QueryClassificationResult(
            query_type=QueryType.DOMAIN_SPECIFIC,
            confidence=0.85,
            classifier_used="semantic_router",
            matched_example="강주노 롱테이크",
            latency_ms=15,
        )
        assert result.query_type == QueryType.DOMAIN_SPECIFIC
        assert result.confidence == 0.85
        assert result.classifier_used == "semantic_router"
        assert result.matched_example == "강주노 롱테이크"
        assert result.latency_ms == 15

    def test_confidence_validation(self):
        """Confidence must be 0-1."""
        with pytest.raises(ValueError):
            QueryClassificationResult(
                query_type=QueryType.AMBIGUOUS,
                confidence=1.5,
                classifier_used="test",
            )


# ============================================================================
# SemanticRouter Tests (with mock model)
# ============================================================================


class TestSemanticRouterMocked:
    """SemanticRouter tests with mocked model."""

    @pytest.fixture
    def mock_sentence_transformer(self):
        """Mock SentenceTransformer."""
        with patch("sentence_transformers.SentenceTransformer") as mock:
            # Mock model encode
            mock_model = MagicMock()
            mock_model.encode.return_value = [0.1] * 384  # 384-dim vector
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock.return_value = mock_model
            yield mock_model

    def test_router_initialization(self, mock_sentence_transformer):
        """Router initializes with model."""
        from app.rag.semantic_router import SemanticRouter, reset_semantic_router

        reset_semantic_router()
        SemanticRouter._model = None  # Force re-init
        SemanticRouter._routes = None
        SemanticRouter._route_embeddings = None

        # Model should be loaded
        router = SemanticRouter()
        assert router is not None


# ============================================================================
# LLM Classifier Tests (with mock)
# ============================================================================


class TestLLMClassifierMocked:
    """LLM Classifier tests with mocked Gemini (google.genai - new library)."""

    @pytest.fixture
    def mock_genai_client(self):
        """Mock get_genai_client for llm_classifier (google.genai - new library)."""
        mock_response = MagicMock()
        mock_response.text = '{"query_type": "domain_specific", "confidence": 0.9, "reasoning": "test"}'

        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with patch("app.services.genai_utils.get_genai_client", return_value=mock_client):
            yield mock_client

    @pytest.mark.asyncio
    async def test_classify_with_llm(self, mock_genai_client):
        """LLM classifier returns correct type."""
        from app.rag.llm_classifier import classify_with_llm

        query_type, confidence = await classify_with_llm("강주노 롱테이크")

        assert query_type == QueryType.DOMAIN_SPECIFIC
        assert confidence == 0.9

    @pytest.mark.asyncio
    async def test_classify_with_llm_error_fallback(self):
        """LLM classifier returns AMBIGUOUS on error."""
        from app.rag.llm_classifier import classify_with_llm

        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(side_effect=Exception("API Error"))

        with patch("app.services.genai_utils.get_genai_client", return_value=mock_client):
            query_type, confidence = await classify_with_llm("test query")

            assert query_type == QueryType.AMBIGUOUS
            assert confidence == 0.5


# ============================================================================
# Direct LLM Tests (with mock)
# ============================================================================


class TestDirectLLMMocked:
    """Direct LLM tests with mocked Gemini (google.genai - new library)."""

    @pytest.fixture
    def mock_genai_for_direct(self):
        """Mock get_genai_client for direct LLM (google.genai - new library)."""
        mock_response = MagicMock()
        mock_response.text = "Python is a programming language."

        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with patch("app.services.genai_utils.get_genai_client", return_value=mock_client):
            yield mock_client

    @pytest.mark.asyncio
    async def test_direct_llm_response(self, mock_genai_for_direct):
        """Direct LLM generates response."""
        from app.rag.direct_llm import direct_llm_response

        result = await direct_llm_response("Python이란?", QueryType.SIMPLE_FACTUAL)

        assert result.answer == "Python is a programming language."
        assert result.skip_retrieval is True
        assert result.strategy_used == "direct_llm"
        assert result.confidence == 0.9

    @pytest.mark.asyncio
    async def test_direct_llm_to_hybrid_result(self, mock_genai_for_direct):
        """DirectLLMResult converts to HybridRAGResult."""
        from app.rag.direct_llm import direct_llm_response

        result = await direct_llm_response("test query", QueryType.SIMPLE_FACTUAL)
        hybrid_result = result.to_hybrid_result()

        assert hybrid_result.answer == result.answer
        assert hybrid_result.strategy_used == "direct_llm"
        assert hybrid_result.retrieval_count == 0


# ============================================================================
# Mock Classifier Tests
# ============================================================================


class TestMockClassifier:
    """Mock classifier tests for testing purposes."""

    @pytest.mark.asyncio
    async def test_mock_llm_classifier(self):
        """Mock LLM classifier works correctly."""
        from app.rag.llm_classifier import MockLLMClassifier

        mock = MockLLMClassifier()

        # Domain-specific query
        qt, conf = await mock.classify("강주노 영화 특징")
        assert qt == QueryType.DOMAIN_SPECIFIC

        # Simple factual
        qt, conf = await mock.classify("Python이 뭐야?")
        assert qt == QueryType.SIMPLE_FACTUAL

        # Creative
        qt, conf = await mock.classify("영화 시놉시스 써줘")
        assert qt == QueryType.CREATIVE

        # Multi-hop
        qt, conf = await mock.classify("왜 기생충이 성공했나?")
        assert qt == QueryType.MULTI_HOP

        # Recency
        qt, conf = await mock.classify("2026년 AI 트렌드")
        assert qt == QueryType.RECENCY_REQUIRED

        assert mock.call_count == 5

    @pytest.mark.asyncio
    async def test_mock_direct_llm(self):
        """Mock Direct LLM works correctly."""
        from app.rag.direct_llm import MockDirectLLM

        mock = MockDirectLLM()

        result = await mock.generate("test query", QueryType.SIMPLE_FACTUAL)

        assert "[Mock Response" in result.answer
        assert result.skip_retrieval is True
        assert mock.call_count == 1
