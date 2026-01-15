"""Unit tests for Tier1DimensionRAG hybrid_search.

P0 Verification:
- hybrid_search() dense-only fallback 동작 확인
- Circuit breaker 동작 확인
- 필터 조건 구성 확인
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import sys
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class MockQueryResponse:
    """Mock Qdrant query response."""

    def __init__(self, points):
        self.points = points


class MockPoint:
    """Mock Qdrant point."""

    def __init__(self, id, score, payload):
        self.id = id
        self.score = score
        self.payload = payload


class TestHybridSearch:
    """Test Tier1DimensionRAG.hybrid_search()."""

    @pytest.fixture
    def mock_qdrant_client(self):
        """Create mock Qdrant client."""
        client = MagicMock()
        client.get_collections.return_value = MagicMock(collections=[])
        client.query_points.return_value = MockQueryResponse([
            MockPoint("id1", 0.95, {"content": "Test content", "doc_id": "doc1"}),
            MockPoint("id2", 0.85, {"content": "Another content", "doc_id": "doc2"}),
        ])
        return client

    @pytest.fixture
    def mock_embedder(self):
        """Create mock embedder."""
        embedder = MagicMock()
        embedder.embed.return_value = [0.1] * 384
        return embedder

    @pytest.fixture
    def mock_sparse_embedder(self):
        """Create mock sparse embedder."""
        embedder = MagicMock()
        embedder.embed.return_value = ([1, 2, 3], [0.5, 0.3, 0.2])
        return embedder

    def test_hybrid_search_returns_results(
        self,
        mock_qdrant_client,
        mock_embedder,
        mock_sparse_embedder
    ):
        """Test hybrid_search returns formatted results."""
        from app.rag.tier1_dimension_rag import Tier1DimensionRAG

        with patch.object(Tier1DimensionRAG, "client", new_callable=PropertyMock) as mock_client_prop:
            with patch.object(Tier1DimensionRAG, "embedder", new_callable=PropertyMock) as mock_emb_prop:
                with patch.object(Tier1DimensionRAG, "sparse_embedder", new_callable=PropertyMock) as mock_sparse_prop:
                    with patch("app.rag.tier1_dimension_rag.QDRANT_BREAKER") as mock_breaker:
                        mock_client_prop.return_value = mock_qdrant_client
                        mock_emb_prop.return_value = mock_embedder
                        mock_sparse_prop.return_value = mock_sparse_embedder
                        mock_breaker.check_state.return_value = None

                        rag = Tier1DimensionRAG("AI")
                        results = rag.hybrid_search("INTJ 성격")

                        assert len(results) == 2
                        assert results[0]["content"] == "Test content"
                        assert results[0]["score"] == 0.95
                        assert results[0]["doc_id"] == "doc1"

    def test_hybrid_search_fallback_no_sparse_embedder(
        self,
        mock_qdrant_client,
        mock_embedder
    ):
        """Test fallback to dense-only when sparse embedder unavailable."""
        from app.rag.tier1_dimension_rag import Tier1DimensionRAG

        with patch.object(Tier1DimensionRAG, "client", new_callable=PropertyMock) as mock_client_prop:
            with patch.object(Tier1DimensionRAG, "embedder", new_callable=PropertyMock) as mock_emb_prop:
                with patch.object(Tier1DimensionRAG, "sparse_embedder", new_callable=PropertyMock) as mock_sparse_prop:
                    with patch.object(Tier1DimensionRAG, "search") as mock_search:
                        mock_client_prop.return_value = mock_qdrant_client
                        mock_emb_prop.return_value = mock_embedder
                        mock_sparse_prop.return_value = None  # No sparse embedder
                        mock_search.return_value = [{"content": "fallback", "score": 0.8}]

                        rag = Tier1DimensionRAG("AI")
                        results = rag.hybrid_search("INTJ 성격")

                        # Should fall back to search()
                        mock_search.assert_called_once()
                        assert results[0]["content"] == "fallback"

    def test_hybrid_search_fallback_circuit_open(
        self,
        mock_qdrant_client,
        mock_embedder,
        mock_sparse_embedder
    ):
        """Test fallback when circuit breaker is open."""
        from app.rag.tier1_dimension_rag import Tier1DimensionRAG
        from app.services.circuit_breaker import CircuitBreakerOpen

        with patch.object(Tier1DimensionRAG, "client", new_callable=PropertyMock) as mock_client_prop:
            with patch.object(Tier1DimensionRAG, "embedder", new_callable=PropertyMock) as mock_emb_prop:
                with patch.object(Tier1DimensionRAG, "sparse_embedder", new_callable=PropertyMock) as mock_sparse_prop:
                    with patch("app.rag.tier1_dimension_rag.QDRANT_BREAKER") as mock_breaker:
                        with patch.object(Tier1DimensionRAG, "search") as mock_search:
                            mock_client_prop.return_value = mock_qdrant_client
                            mock_emb_prop.return_value = mock_embedder
                            mock_sparse_prop.return_value = mock_sparse_embedder
                            mock_breaker.check_state.side_effect = CircuitBreakerOpen(
                                name="qdrant", remaining_seconds=30.0
                            )
                            mock_search.return_value = [{"content": "circuit fallback", "score": 0.7}]

                            rag = Tier1DimensionRAG("AI")
                            results = rag.hybrid_search("INTJ 성격")

                            # Should fall back to search()
                            mock_search.assert_called_once()
                            assert results[0]["content"] == "circuit fallback"

    def test_hybrid_search_fallback_on_exception(
        self,
        mock_qdrant_client,
        mock_embedder,
        mock_sparse_embedder
    ):
        """Test fallback when hybrid search raises exception."""
        from app.rag.tier1_dimension_rag import Tier1DimensionRAG

        mock_qdrant_client.query_points.side_effect = Exception("Query failed")

        with patch.object(Tier1DimensionRAG, "client", new_callable=PropertyMock) as mock_client_prop:
            with patch.object(Tier1DimensionRAG, "embedder", new_callable=PropertyMock) as mock_emb_prop:
                with patch.object(Tier1DimensionRAG, "sparse_embedder", new_callable=PropertyMock) as mock_sparse_prop:
                    with patch("app.rag.tier1_dimension_rag.QDRANT_BREAKER") as mock_breaker:
                        with patch.object(Tier1DimensionRAG, "search") as mock_search:
                            mock_client_prop.return_value = mock_qdrant_client
                            mock_emb_prop.return_value = mock_embedder
                            mock_sparse_prop.return_value = mock_sparse_embedder
                            mock_breaker.check_state.return_value = None
                            mock_search.return_value = [{"content": "exception fallback", "score": 0.6}]

                            rag = Tier1DimensionRAG("AI")
                            results = rag.hybrid_search("INTJ 성격")

                            # Should fall back to search() after exception
                            mock_search.assert_called_once()
                            assert results[0]["content"] == "exception fallback"

    def test_hybrid_search_with_filters(
        self,
        mock_qdrant_client,
        mock_embedder,
        mock_sparse_embedder
    ):
        """Test hybrid_search applies filters correctly."""
        from app.rag.tier1_dimension_rag import Tier1DimensionRAG

        with patch.object(Tier1DimensionRAG, "client", new_callable=PropertyMock) as mock_client_prop:
            with patch.object(Tier1DimensionRAG, "embedder", new_callable=PropertyMock) as mock_emb_prop:
                with patch.object(Tier1DimensionRAG, "sparse_embedder", new_callable=PropertyMock) as mock_sparse_prop:
                    with patch("app.rag.tier1_dimension_rag.QDRANT_BREAKER") as mock_breaker:
                        mock_client_prop.return_value = mock_qdrant_client
                        mock_emb_prop.return_value = mock_embedder
                        mock_sparse_prop.return_value = mock_sparse_embedder
                        mock_breaker.check_state.return_value = None

                        rag = Tier1DimensionRAG("AI")
                        rag.hybrid_search(
                            "INTJ 성격",
                            app_key="dimension.persona.analyze",
                            metadata_filters={"dataset_id": {"$in": ["mbti", "psych_core"]}}
                        )

                        # Verify query_points was called with filter
                        call_kwargs = mock_qdrant_client.query_points.call_args.kwargs
                        assert call_kwargs["query_filter"] is not None

    def test_hybrid_search_empty_when_no_client(self):
        """Test hybrid_search returns empty when client unavailable."""
        from app.rag.tier1_dimension_rag import Tier1DimensionRAG

        with patch.object(Tier1DimensionRAG, "client", new_callable=PropertyMock) as mock_client_prop:
            with patch.object(Tier1DimensionRAG, "sparse_embedder", new_callable=PropertyMock) as mock_sparse_prop:
                with patch("app.rag.tier1_dimension_rag.QDRANT_BREAKER") as mock_breaker:
                    mock_client_prop.return_value = None  # No client
                    mock_sparse_prop.return_value = MagicMock()
                    mock_breaker.check_state.return_value = None

                    rag = Tier1DimensionRAG("AI")
                    results = rag.hybrid_search("INTJ 성격")

                    assert results == []
