"""Tests for Backend Implementations.

pytest tests/rag/test_backends.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestQdrantHybridBackend:
    """QdrantHybridBackend 통합 테스트."""

    @pytest.mark.asyncio
    async def test_retrieve_basic(self):
        """기본 검색 테스트 (mock)."""
        from app.rag.backends import get_backend

        backend = get_backend("qdrant_hybrid")

        # Mock tier1_dimension_rag.hybrid_search
        mock_results = [
            {"doc_id": "doc_1", "content": "Content 1", "score": 0.9, "metadata": {}},
            {"doc_id": "doc_2", "content": "Content 2", "score": 0.8, "metadata": {}},
        ]

        with patch.object(backend, "_get_rag") as mock_get_rag:
            mock_rag = MagicMock()
            mock_rag.hybrid_search.return_value = mock_results
            mock_get_rag.return_value = mock_rag

            results = await backend.retrieve(
                query="강주노 스타일",
                config={"dimension": "AD"},
            )

            assert len(results) == 2
            assert results[0].doc_id == "doc_1"
            assert results[0].score == 0.9
            assert results[0].source == "qdrant_hybrid"
            assert results[0].rank == 1

    @pytest.mark.asyncio
    async def test_retrieve_with_filters(self):
        """필터 적용 검색 테스트."""
        from app.rag.backends import get_backend

        backend = get_backend("qdrant_hybrid")

        with patch.object(backend, "_get_rag") as mock_get_rag:
            mock_rag = MagicMock()
            mock_rag.hybrid_search.return_value = []
            mock_get_rag.return_value = mock_rag

            await backend.retrieve(
                query="test",
                filters={"app_key": "dimension.aesthetic.direct"},
                config={"dimension": "AD"},
            )

            # hybrid_search에 app_key가 전달되었는지 확인
            mock_rag.hybrid_search.assert_called_once()
            call_kwargs = mock_rag.hybrid_search.call_args[1]
            assert call_kwargs["app_key"] == "dimension.aesthetic.direct"

    @pytest.mark.asyncio
    async def test_retrieve_error_handling(self):
        """검색 에러 처리 테스트."""
        from app.rag.backends import get_backend

        backend = get_backend("qdrant_hybrid")

        with patch.object(backend, "_get_rag") as mock_get_rag:
            mock_rag = MagicMock()
            mock_rag.hybrid_search.side_effect = Exception("Connection failed")
            mock_get_rag.return_value = mock_rag

            results = await backend.retrieve(query="test", config={"dimension": "AD"})

            # 에러 시 빈 결과 반환
            assert results == []

    @pytest.mark.asyncio
    async def test_health_check(self):
        """헬스체크 테스트."""
        from app.rag.backends import get_backend

        backend = get_backend("qdrant_hybrid")

        with patch.object(backend, "_get_rag") as mock_get_rag:
            mock_rag = MagicMock()
            mock_rag.get_collection_stats.return_value = {"available": True}
            mock_get_rag.return_value = mock_rag

            healthy = await backend.health_check()

            assert healthy is True

    @pytest.mark.asyncio
    async def test_index_document(self):
        """문서 인덱싱 테스트."""
        from app.rag.backends import get_backend

        backend = get_backend("qdrant_hybrid")

        with patch.object(backend, "_get_rag") as mock_get_rag:
            mock_rag = MagicMock()
            mock_rag.index_document.return_value = True
            mock_get_rag.return_value = mock_rag

            success = await backend.index_document(
                doc_id="doc_1",
                text="Test content",
                metadata={"dimension": "AD"},
            )

            assert success is True


class TestNotebookLMBackend:
    """NotebookLMBackend 통합 테스트."""

    @pytest.mark.asyncio
    async def test_retrieve_without_notebook_id(self):
        """notebook_id 없이 검색 시 빈 결과 반환."""
        from app.rag.backends import get_backend

        backend = get_backend("notebooklm")

        results = await backend.retrieve(query="test")

        assert results == []

    @pytest.mark.asyncio
    async def test_retrieve_with_notebook_id(self):
        """notebook_id와 함께 검색 테스트."""
        from app.rag.backends import get_backend
        from app.rag.tier0_notebooklm import NotebookQueryResult, NotebookSource

        backend = get_backend("notebooklm")

        mock_result = NotebookQueryResult(
            answer="Test answer",
            sources=[
                NotebookSource(
                    source_id="src_1",
                    title="Source 1",
                    excerpt="Excerpt 1",
                    relevance_score=0.9,
                    citation_text="[1]",
                ),
            ],
            confidence=0.92,
            grounded=True,
        )

        with patch.object(backend, "_get_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.query_notebook = AsyncMock(return_value=mock_result)
            mock_get_service.return_value = mock_service

            results = await backend.retrieve(
                query="강주노 스타일",
                config={"notebook_id": "DNA_강주노"},
            )

            assert len(results) == 1
            assert results[0].doc_id == "src_1"
            assert results[0].source == "notebooklm"
            assert results[0].metadata["grounded"] is True

    @pytest.mark.asyncio
    async def test_health_check(self):
        """헬스체크 테스트."""
        from app.rag.backends import get_backend

        backend = get_backend("notebooklm")

        with patch.object(backend, "_get_service") as mock_get_service:
            mock_get_service.return_value = MagicMock()

            healthy = await backend.health_check()

            assert healthy is True


class TestBackendConfig:
    """BackendConfig Pydantic 모델 테스트."""

    def test_backend_config_creation(self):
        """BackendConfig 생성 테스트."""
        from app.rag.manifest_loader import BackendConfig

        config = BackendConfig(
            id="qdrant_hybrid",
            weight=0.6,
            enabled=True,
            config={"dimension": "AD", "prefetch_limit": 30},
        )

        assert config.id == "qdrant_hybrid"
        assert config.weight == 0.6
        assert config.enabled is True
        assert config.config["dimension"] == "AD"

    def test_backend_config_defaults(self):
        """BackendConfig 기본값 테스트."""
        from app.rag.manifest_loader import BackendConfig

        config = BackendConfig(id="notebooklm")

        assert config.weight == 1.0
        assert config.enabled is True
        assert config.config == {}

    def test_yaml_manifest_with_backends(self):
        """YAMLManifest backends 필드 테스트."""
        from app.rag.manifest_loader import YAMLManifest, BackendConfig

        manifest = YAMLManifest(
            app_key="dimension.aesthetic.direct",
            dimensions=["AD"],
            backends=[
                BackendConfig(
                    id="qdrant_hybrid",
                    weight=0.6,
                    config={"dimension": "AD"},
                ),
                BackendConfig(
                    id="notebooklm",
                    weight=0.4,
                    config={"notebook_id": "DNA_강주노"},
                ),
            ],
        )

        assert len(manifest.backends) == 2
        assert manifest.backends[0].id == "qdrant_hybrid"
        assert manifest.backends[1].weight == 0.4
