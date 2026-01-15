"""Reranker 단위/통합 테스트.

P4: BaseReranker ABC, Registry, Local/Vertex Rerankers 테스트.

Test Coverage:
- BaseReranker ABC 계약
- DocumentToRerank, RerankResult 데이터 클래스
- LocalCrossEncoderReranker (mock)
- VertexReranker (mock)
- Auto-discovery Registry
- ensemble_retrieve() reranker 통합
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from app.rag.rerankers import (
    get_reranker,
    list_rerankers,
    get_reranker_class,
    reload_rerankers,
)
from app.rag.rerankers.base import (
    BaseReranker,
    DocumentToRerank,
    RerankResult,
    RerankerError,
)


# ============================================================================
# Data Class Tests
# ============================================================================


class TestDocumentToRerank:
    """DocumentToRerank 데이터 클래스 테스트."""

    def test_create_minimal(self):
        """필수 필드만으로 생성."""
        doc = DocumentToRerank(id="doc_1", text="테스트 문서")
        assert doc.id == "doc_1"
        assert doc.text == "테스트 문서"
        assert doc.metadata is None

    def test_create_with_metadata(self):
        """메타데이터 포함 생성."""
        doc = DocumentToRerank(
            id="doc_2",
            text="메타데이터 포함 문서",
            metadata={"source": "notebooklm", "score": 0.95},
        )
        assert doc.id == "doc_2"
        assert doc.metadata["source"] == "notebooklm"
        assert doc.metadata["score"] == 0.95


class TestRerankResult:
    """RerankResult 데이터 클래스 테스트."""

    def test_create_minimal(self):
        """필수 필드만으로 생성."""
        result = RerankResult(
            documents=[],
            query="테스트 쿼리",
            model="bge-base",
            latency_ms=50,
            original_count=10,
            reranked_count=5,
        )
        assert result.query == "테스트 쿼리"
        assert result.model == "bge-base"
        assert result.latency_ms == 50
        assert result.metadata == {}

    def test_create_with_documents(self):
        """문서 목록 포함 생성."""
        docs = [
            {"id": "doc_1", "text": "문서 1", "rerank_score": 0.95},
            {"id": "doc_2", "text": "문서 2", "rerank_score": 0.80},
        ]
        result = RerankResult(
            documents=docs,
            query="검색 쿼리",
            model="vertex-default",
            latency_ms=100,
            original_count=10,
            reranked_count=2,
            metadata={"fallback": False},
        )
        assert len(result.documents) == 2
        assert result.documents[0]["rerank_score"] == 0.95
        assert result.metadata["fallback"] is False


# ============================================================================
# Registry Tests
# ============================================================================


class TestRerankerRegistry:
    """Reranker Registry 테스트."""

    def test_list_rerankers_discovers_all(self):
        """자동 발견된 모든 reranker 목록."""
        rerankers = list_rerankers()
        assert isinstance(rerankers, list)
        assert "local_cross_encoder" in rerankers
        assert "vertex" in rerankers

    def test_get_reranker_local(self):
        """local_cross_encoder reranker 조회."""
        reranker = get_reranker("local_cross_encoder")
        assert reranker is not None
        assert reranker.backend_id == "local_cross_encoder"

    def test_get_reranker_vertex(self):
        """vertex reranker 조회."""
        # VertexReranker는 GOOGLE_CLOUD_PROJECT 설정이 필요하므로
        # 클래스만 확인
        cls = get_reranker_class("vertex")
        assert cls is not None
        assert cls.backend_id == "vertex"

    def test_get_reranker_unknown_returns_none(self):
        """존재하지 않는 reranker는 None 반환."""
        reranker = get_reranker("unknown_reranker")
        assert reranker is None

    def test_get_reranker_class(self):
        """reranker 클래스 조회."""
        cls = get_reranker_class("local_cross_encoder")
        assert cls is not None
        assert issubclass(cls, BaseReranker)

    def test_get_reranker_with_model_override(self):
        """모델 오버라이드로 reranker 생성."""
        reranker = get_reranker("local_cross_encoder", model="bge-large")
        assert reranker is not None
        # 별도 인스턴스가 캐시됨
        assert reranker.model_name == "BAAI/bge-reranker-large"


# ============================================================================
# LocalCrossEncoderReranker Tests
# ============================================================================


class TestLocalCrossEncoderReranker:
    """LocalCrossEncoderReranker 테스트 (mock)."""

    @pytest.fixture
    def mock_cross_encoder(self):
        """CrossEncoder mock."""
        with patch("app.rag.rerankers.cross_encoder._get_cross_encoder") as mock:
            mock_model = MagicMock()
            mock_model.predict.return_value = [0.95, 0.80, 0.60]
            mock_model.model.device = "cpu"
            mock.return_value = lambda *args, **kwargs: mock_model
            yield mock_model

    @pytest.mark.asyncio
    async def test_rerank_basic(self, mock_cross_encoder):
        """기본 리랭킹 동작."""
        from app.rag.rerankers.cross_encoder import LocalCrossEncoderReranker

        reranker = LocalCrossEncoderReranker(model="bge-base")
        reranker._model = mock_cross_encoder

        docs = [
            DocumentToRerank(id="d1", text="문서 1"),
            DocumentToRerank(id="d2", text="문서 2"),
            DocumentToRerank(id="d3", text="문서 3"),
        ]

        result = await reranker.rerank(
            query="테스트 쿼리",
            documents=docs,
            top_k=2,
        )

        assert result.reranked_count == 2
        assert len(result.documents) == 2
        # 점수순 정렬 확인
        assert result.documents[0]["rerank_score"] >= result.documents[1]["rerank_score"]

    @pytest.mark.asyncio
    async def test_rerank_empty_documents(self, mock_cross_encoder):
        """빈 문서 목록 처리."""
        from app.rag.rerankers.cross_encoder import LocalCrossEncoderReranker

        reranker = LocalCrossEncoderReranker()
        result = await reranker.rerank(
            query="테스트",
            documents=[],
            top_k=5,
        )

        assert result.reranked_count == 0
        assert len(result.documents) == 0

    def test_model_alias_resolution(self):
        """모델 별칭 해석."""
        from app.rag.rerankers.cross_encoder import MODEL_ALIASES

        assert "bge-base" in MODEL_ALIASES
        assert MODEL_ALIASES["bge-base"] == "BAAI/bge-reranker-base"
        assert "ms-marco" in MODEL_ALIASES


# ============================================================================
# VertexReranker Tests
# ============================================================================


class TestVertexReranker:
    """VertexReranker 테스트 (mock)."""

    @pytest.fixture
    def mock_vertex_client(self):
        """Vertex Discovery Engine client mock."""
        with patch("app.rag.rerankers.vertex._discoveryengine") as mock_de:
            mock_client = MagicMock()

            # Mock response
            mock_response = MagicMock()
            mock_record_1 = MagicMock()
            mock_record_1.id = "doc_1"
            mock_record_1.score = 0.95
            mock_record_2 = MagicMock()
            mock_record_2.id = "doc_2"
            mock_record_2.score = 0.75
            mock_response.records = [mock_record_1, mock_record_2]

            mock_client.rank.return_value = mock_response
            mock_de.RankServiceClient.return_value = mock_client
            mock_de.RankingRecord = MagicMock
            mock_de.RankRequest = MagicMock

            yield mock_de, mock_client

    @pytest.mark.asyncio
    async def test_rerank_basic(self, mock_vertex_client):
        """기본 Vertex 리랭킹 동작."""
        from app.rag.rerankers.vertex import VertexReranker

        mock_de, mock_client = mock_vertex_client

        reranker = VertexReranker(project_id="test-project")
        reranker._client = mock_client

        docs = [
            DocumentToRerank(id="doc_1", text="문서 1"),
            DocumentToRerank(id="doc_2", text="문서 2"),
        ]

        result = await reranker.rerank(
            query="테스트 쿼리",
            documents=docs,
            top_k=2,
        )

        assert result.reranked_count == 2
        assert result.model == "semantic-ranker-default-004"

    def test_ranking_config_format(self):
        """ranking_config 리소스 이름 형식."""
        from app.rag.rerankers.vertex import VertexReranker

        reranker = VertexReranker(project_id="my-project", location="global")
        config = reranker.ranking_config

        assert "projects/my-project" in config
        assert "locations/global" in config
        assert "rankingConfigs/default_ranking_config" in config


# ============================================================================
# RerankerConfig Integration Tests
# ============================================================================


class TestRerankerConfig:
    """manifest_loader.RerankerConfig 통합 테스트."""

    def test_reranker_config_defaults(self):
        """RerankerConfig 기본값."""
        from app.rag.manifest_loader import RerankerConfig

        config = RerankerConfig()
        assert config.enabled is False
        assert config.backend == "local_cross_encoder"
        assert config.model == "bge-base"
        assert config.top_k == 5
        assert config.min_score == 0.0

    def test_reranker_config_custom(self):
        """RerankerConfig 커스텀 설정."""
        from app.rag.manifest_loader import RerankerConfig

        config = RerankerConfig(
            enabled=True,
            backend="vertex",
            config={
                "model": "semantic-ranker-fast-004",
                "top_k": 10,
                "min_score": 0.3,
            },
        )
        assert config.enabled is True
        assert config.backend == "vertex"
        assert config.model == "semantic-ranker-fast-004"
        assert config.top_k == 10
        assert config.min_score == 0.3


class TestYAMLManifestReranker:
    """YAMLManifest reranker 필드 테스트."""

    def test_manifest_without_reranker(self):
        """reranker 설정 없는 manifest."""
        from app.rag.manifest_loader import YAMLManifest

        manifest = YAMLManifest(
            app_key="test.app.minimal",
            version="1.0",
        )
        assert manifest.reranker is None

    def test_manifest_with_reranker(self):
        """reranker 설정 포함 manifest."""
        from app.rag.manifest_loader import YAMLManifest, RerankerConfig

        manifest = YAMLManifest(
            app_key="test.app.reranker",
            version="1.0",
            reranker=RerankerConfig(
                enabled=True,
                backend="local_cross_encoder",
                config={"model": "bge-large", "top_k": 7},
            ),
        )
        assert manifest.reranker is not None
        assert manifest.reranker.enabled is True
        assert manifest.reranker.model == "bge-large"
        assert manifest.reranker.top_k == 7


# ============================================================================
# Ensemble + Reranker Integration Tests
# ============================================================================


class TestEnsembleRerankerIntegration:
    """ensemble_retrieve() + reranker 통합 테스트."""

    @pytest.fixture
    def mock_manifest_with_reranker(self):
        """Reranker 설정이 포함된 manifest mock."""
        from app.rag.manifest_loader import (
            YAMLManifest,
            BackendConfig,
            RerankerConfig,
        )

        return YAMLManifest(
            app_key="test.ensemble.reranker",
            version="1.0",
            dimensions=["AD"],
            backends=[
                BackendConfig(id="qdrant_hybrid", weight=0.7, enabled=True),
            ],
            reranker=RerankerConfig(
                enabled=True,
                backend="local_cross_encoder",
                config={"model": "bge-base", "top_k": 5, "min_score": 0.0},
            ),
        )

    @pytest.fixture
    def mock_manifest_without_reranker(self):
        """Reranker 설정 없는 manifest mock."""
        from app.rag.manifest_loader import YAMLManifest, BackendConfig

        return YAMLManifest(
            app_key="test.ensemble.no_reranker",
            version="1.0",
            dimensions=["AD"],
            backends=[
                BackendConfig(id="qdrant_hybrid", weight=0.7, enabled=True),
            ],
        )

    @pytest.mark.asyncio
    async def test_ensemble_with_reranker_enabled(
        self, mock_manifest_with_reranker
    ):
        """ensemble_retrieve()에서 reranker 활성화."""
        from app.rag.hybrid_rag import ensemble_retrieve
        from app.rag.backends.base import RetrievalResult

        mock_results = [
            RetrievalResult(
                doc_id="doc_1",
                text="봉준호 감독의 롱테이크",
                score=0.9,
                source="qdrant_hybrid",
                rank=1,
            ),
            RetrievalResult(
                doc_id="doc_2",
                text="기생충 계단 장면",
                score=0.8,
                source="qdrant_hybrid",
                rank=2,
            ),
        ]

        # Patch where the names are used (in hybrid_rag module namespace)
        with patch.object(
            __import__("app.rag.hybrid_rag", fromlist=["get_manifest"]),
            "get_manifest",
            return_value=mock_manifest_with_reranker
        ), patch.object(
            __import__("app.rag.backends", fromlist=["get_backend"]),
            "get_backend",
        ) as mock_get_backend, patch.object(
            __import__("app.rag.hybrid_rag", fromlist=["get_reranker"]),
            "get_reranker",
        ) as mock_get_reranker:

            # Backend mock
            mock_backend = AsyncMock()
            mock_backend.retrieve.return_value = mock_results
            mock_get_backend.return_value = mock_backend

            # Reranker mock
            mock_reranker = AsyncMock()
            mock_reranker.rerank.return_value = RerankResult(
                documents=[
                    {"id": "doc_2", "text": "기생충 계단 장면", "rerank_score": 0.95},
                    {"id": "doc_1", "text": "봉준호 감독의 롱테이크", "rerank_score": 0.85},
                ],
                query="봉준호",
                model="BAAI/bge-reranker-base",
                latency_ms=30,
                original_count=2,
                reranked_count=2,
            )
            mock_get_reranker.return_value = mock_reranker

            result = await ensemble_retrieve(
                query="봉준호 스타일",
                app_key="test.ensemble.reranker",
            )

            # reranker가 호출되었는지 확인
            mock_get_reranker.assert_called_once()
            mock_reranker.rerank.assert_called_once()

            # 결과에 reranked 플래그가 설정되었는지 확인
            assert result.reranked is True
            assert result.rerank_model == "BAAI/bge-reranker-base"

    @pytest.mark.asyncio
    async def test_ensemble_without_reranker(
        self, mock_manifest_without_reranker
    ):
        """reranker 비활성화 시 스킵."""
        from app.rag.hybrid_rag import ensemble_retrieve
        from app.rag.backends.base import RetrievalResult

        mock_results = [
            RetrievalResult(
                doc_id="doc_1",
                text="테스트 문서",
                score=0.9,
                source="qdrant_hybrid",
                rank=1,
            ),
        ]

        # Patch at the right location
        with patch("app.rag.manifest_loader.get_manifest") as mock_get_manifest, \
             patch("app.rag.backends.get_backend") as mock_get_backend, \
             patch("app.rag.rerankers.get_reranker") as mock_get_reranker:

            mock_get_manifest.return_value = mock_manifest_without_reranker

            # Backend mock
            mock_backend = AsyncMock()
            mock_backend.retrieve.return_value = mock_results
            mock_get_backend.return_value = mock_backend

            result = await ensemble_retrieve(
                query="테스트",
                app_key="test.ensemble.no_reranker",
            )

            # reranker가 호출되지 않아야 함
            mock_get_reranker.assert_not_called()
            assert result.reranked is False


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestRerankerErrorHandling:
    """Reranker 오류 처리 테스트."""

    @pytest.mark.asyncio
    async def test_rerank_exception_fallback(self):
        """리랭킹 실패 시 폴백 동작."""
        from app.rag.rerankers.cross_encoder import LocalCrossEncoderReranker

        reranker = LocalCrossEncoderReranker()

        # 예외를 발생시키는 모델 mock
        reranker._model = MagicMock()
        reranker._model.predict.side_effect = RuntimeError("Model error")

        docs = [
            DocumentToRerank(id="d1", text="문서 1"),
            DocumentToRerank(id="d2", text="문서 2"),
        ]

        result = await reranker.rerank(
            query="테스트",
            documents=docs,
            top_k=2,
        )

        # 폴백: 원래 순서로 반환, score=0.0
        assert result.reranked_count == 2
        assert result.metadata.get("fallback") is True
        assert all(doc["rerank_score"] == 0.0 for doc in result.documents)

    def test_reranker_error_class(self):
        """RerankerError 예외 클래스."""
        error = RerankerError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
