"""Tests for Backend Registry and Auto-discovery.

pytest tests/rag/test_backend_registry.py -v
"""
import pytest


class TestBackendRegistry:
    """Backend Registry 단위 테스트."""

    def test_auto_discovery(self):
        """백엔드 자동 발견 테스트."""
        from app.rag.backends import list_backends, reload_backends

        # Reload to ensure fresh state
        reload_backends()

        backends = list_backends()

        # 3개 백엔드가 발견되어야 함
        assert "qdrant_hybrid" in backends
        assert "notebooklm" in backends
        assert "vertex_grounding" in backends
        assert len(backends) >= 3

    def test_get_backend_returns_instance(self):
        """백엔드 인스턴스 가져오기 테스트."""
        from app.rag.backends import get_backend

        backend = get_backend("qdrant_hybrid")

        assert backend is not None
        assert backend.backend_id == "qdrant_hybrid"

    def test_get_backend_singleton(self):
        """백엔드 싱글톤 확인 테스트."""
        from app.rag.backends import get_backend

        b1 = get_backend("qdrant_hybrid")
        b2 = get_backend("qdrant_hybrid")

        assert b1 is b2

    def test_get_backend_not_found(self):
        """존재하지 않는 백엔드 테스트."""
        from app.rag.backends import get_backend

        backend = get_backend("nonexistent_backend")

        assert backend is None

    def test_get_backend_class(self):
        """백엔드 클래스 가져오기 테스트."""
        from app.rag.backends import get_backend_class
        from app.rag.backends.base import BaseBackend

        cls = get_backend_class("qdrant_hybrid")

        assert cls is not None
        assert issubclass(cls, BaseBackend)

    def test_reload_backends(self):
        """백엔드 리로드 테스트."""
        from app.rag.backends import reload_backends, list_backends

        count = reload_backends()

        assert count >= 3
        assert len(list_backends()) == count


class TestRetrievalResult:
    """RetrievalResult 데이터클래스 테스트."""

    def test_retrieval_result_creation(self):
        """RetrievalResult 생성 테스트."""
        from app.rag.backends.base import RetrievalResult

        result = RetrievalResult(
            doc_id="doc_1",
            text="Test content",
            score=0.95,
            source="qdrant_hybrid",
            rank=1,
            metadata={"dimension": "AD"},
        )

        assert result.doc_id == "doc_1"
        assert result.text == "Test content"
        assert result.score == 0.95
        assert result.source == "qdrant_hybrid"
        assert result.rank == 1
        assert result.metadata["dimension"] == "AD"

    def test_retrieval_result_default_metadata(self):
        """RetrievalResult 기본 메타데이터 테스트."""
        from app.rag.backends.base import RetrievalResult

        result = RetrievalResult(
            doc_id="doc_1",
            text="Test content",
            score=0.95,
            source="qdrant_hybrid",
            rank=1,
        )

        assert result.metadata == {}


class TestBaseBackend:
    """BaseBackend ABC 테스트."""

    def test_base_backend_repr(self):
        """백엔드 __repr__ 테스트."""
        from app.rag.backends import get_backend

        backend = get_backend("qdrant_hybrid")

        repr_str = repr(backend)
        assert "QdrantHybridBackend" in repr_str
        assert "qdrant_hybrid" in repr_str

    def test_base_backend_has_required_methods(self):
        """필수 메서드 존재 확인."""
        from app.rag.backends import get_backend

        backend = get_backend("qdrant_hybrid")

        assert hasattr(backend, "retrieve")
        assert hasattr(backend, "health_check")
        assert hasattr(backend, "index_document")
        assert callable(backend.retrieve)
        assert callable(backend.health_check)
        assert callable(backend.index_document)
