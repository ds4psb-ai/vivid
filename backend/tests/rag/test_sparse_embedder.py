"""Unit tests for SparseEmbedder.

P0 Verification:
- SparseEmbedder.embed() 동작 테스트
- Empty input 처리
- Batch embedding 테스트
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _fastembed_available() -> bool:
    """Check if fastembed is available."""
    try:
        import fastembed  # noqa: F401
        return True
    except ImportError:
        return False


class MockSparseEmbedding:
    """Mock sparse embedding result."""

    def __init__(self, indices, values):
        self.indices = MagicMock()
        self.indices.tolist.return_value = indices
        self.values = MagicMock()
        self.values.tolist.return_value = values


class TestSparseEmbedder:
    """Test SparseEmbedder class."""

    def test_embed_returns_tuple(self):
        """Test that embed returns (indices, values) tuple."""
        from app.rag.sparse.fastembed_sparse import SparseEmbedder

        # Create mock model
        mock_model = MagicMock()
        mock_model.embed.return_value = iter([
            MockSparseEmbedding([45, 129, 2048], [0.42, 0.38, 0.25])
        ])

        embedder = SparseEmbedder()
        embedder._model = mock_model  # Bypass lazy loading

        result = embedder.embed("INTJ 성격 유형")

        assert isinstance(result, tuple)
        assert len(result) == 2

        indices, values = result
        assert isinstance(indices, list)
        assert isinstance(values, list)
        assert len(indices) == len(values)

    def test_embed_indices_and_values(self):
        """Test that embed returns correct indices and values."""
        from app.rag.sparse.fastembed_sparse import SparseEmbedder

        mock_model = MagicMock()
        mock_model.embed.return_value = iter([
            MockSparseEmbedding([45, 129, 2048], [0.42, 0.38, 0.25])
        ])

        embedder = SparseEmbedder()
        embedder._model = mock_model

        indices, values = embedder.embed("INTJ 성격 유형")

        assert indices == [45, 129, 2048]
        assert values == [0.42, 0.38, 0.25]

    def test_embed_empty_text(self):
        """Test that embed handles empty text."""
        from app.rag.sparse.fastembed_sparse import SparseEmbedder

        mock_model = MagicMock()
        embedder = SparseEmbedder()
        embedder._model = mock_model

        # Empty string - should return empty without calling model
        indices, values = embedder.embed("")
        assert indices == []
        assert values == []

        # Whitespace only - should return empty
        indices, values = embedder.embed("   ")
        assert indices == []
        assert values == []

        # Model should not be called for empty text
        mock_model.embed.assert_not_called()

    def test_embed_batch(self):
        """Test batch embedding."""
        from app.rag.sparse.fastembed_sparse import SparseEmbedder

        mock_model = MagicMock()
        mock_model.embed.return_value = iter([
            MockSparseEmbedding([1, 2], [0.5, 0.5]),
            MockSparseEmbedding([3, 4], [0.6, 0.4]),
        ])

        embedder = SparseEmbedder()
        embedder._model = mock_model

        results = embedder.embed_batch(["text1", "text2"])

        assert len(results) == 2
        assert results[0] == ([1, 2], [0.5, 0.5])
        assert results[1] == ([3, 4], [0.6, 0.4])

    def test_embed_batch_empty(self):
        """Test batch embedding with empty list."""
        from app.rag.sparse.fastembed_sparse import SparseEmbedder

        mock_model = MagicMock()
        embedder = SparseEmbedder()
        embedder._model = mock_model

        results = embedder.embed_batch([])
        assert results == []

    def test_model_name_configuration(self):
        """Test that model name can be configured."""
        from app.rag.sparse.fastembed_sparse import SparseEmbedder

        # Default model
        embedder1 = SparseEmbedder()
        assert embedder1.model_name == "Qdrant/bm25"

        # Custom model
        embedder2 = SparseEmbedder(model_name="custom/model")
        assert embedder2.model_name == "custom/model"


class TestSparseEmbedderIntegration:
    """Integration tests (requires fastembed installed)."""

    @pytest.mark.skipif(
        not _fastembed_available(),
        reason="fastembed not installed"
    )
    def test_real_embed(self):
        """Test real embedding generation (requires fastembed)."""
        from app.rag.sparse.fastembed_sparse import SparseEmbedder

        embedder = SparseEmbedder()
        indices, values = embedder.embed("INTJ 성격 유형 분석")

        # Should return non-empty results
        assert len(indices) > 0
        assert len(values) > 0
        assert len(indices) == len(values)

        # All indices should be non-negative integers
        assert all(isinstance(i, int) and i >= 0 for i in indices)

        # All values should be floats
        assert all(isinstance(v, float) for v in values)
