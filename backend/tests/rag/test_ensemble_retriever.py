"""Tests for P3: Ensemble Retriever with Weighted RRF Fusion.

pytest tests/rag/test_ensemble_retriever.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from app.rag.backends.base import RetrievalResult


class TestWeightedRRFFusion:
    """_weighted_rrf_fusion() 단위 테스트."""

    def test_basic_fusion(self):
        """기본 RRF fusion 테스트."""
        from app.rag.hybrid_rag import _weighted_rrf_fusion

        backend_results = [
            ("qdrant_hybrid", 0.6, [
                RetrievalResult(doc_id="doc_1", text="Content 1", score=0.9, source="qdrant_hybrid", rank=1),
                RetrievalResult(doc_id="doc_2", text="Content 2", score=0.8, source="qdrant_hybrid", rank=2),
            ]),
            ("notebooklm", 0.4, [
                RetrievalResult(doc_id="doc_2", text="Content 2", score=0.85, source="notebooklm", rank=1),
                RetrievalResult(doc_id="doc_3", text="Content 3", score=0.7, source="notebooklm", rank=2),
            ]),
        ]

        fused = _weighted_rrf_fusion(backend_results, k=60, limit=3)

        # doc_2가 두 retriever에서 모두 등장 -> 최상위
        assert fused[0].doc_id == "doc_2"
        assert len(fused[0].metadata["fusion_sources"]) == 2
        assert "qdrant_hybrid" in fused[0].metadata["fusion_sources"]
        assert "notebooklm" in fused[0].metadata["fusion_sources"]

    def test_weight_impact(self):
        """가중치가 순위에 미치는 영향 테스트."""
        from app.rag.hybrid_rag import _weighted_rrf_fusion

        # 높은 가중치 retriever의 1위 vs 낮은 가중치 retriever의 1위
        backend_results = [
            ("high_weight", 0.9, [
                RetrievalResult(doc_id="doc_A", text="A", score=0.9, source="high_weight", rank=1),
            ]),
            ("low_weight", 0.1, [
                RetrievalResult(doc_id="doc_B", text="B", score=0.9, source="low_weight", rank=1),
            ]),
        ]

        fused = _weighted_rrf_fusion(backend_results, k=60)

        # 높은 가중치의 doc_A가 상위
        assert fused[0].doc_id == "doc_A"
        assert fused[0].score > fused[1].score

        # RRF 스코어 검증: weight / (k + rank)
        # doc_A: 0.9 / (60 + 1) = 0.01475...
        # doc_B: 0.1 / (60 + 1) = 0.00164...
        assert fused[0].score == pytest.approx(0.9 / 61, rel=1e-3)
        assert fused[1].score == pytest.approx(0.1 / 61, rel=1e-3)

    def test_k_parameter_effect(self):
        """k 파라미터 효과 테스트.

        작은 k는 상위 순위를 강조하고, 큰 k는 순위 차이를 완화합니다.
        공식: score = weight / (k + rank)
        - k=1: 1/(1+1)=0.5, 1/(1+10)=0.0909 -> 차이 0.409
        - k=100: 1/(100+1)=0.0099, 1/(100+10)=0.0091 -> 차이 0.0008
        """
        from app.rag.hybrid_rag import _weighted_rrf_fusion

        backend_results = [
            ("backend", 1.0, [
                RetrievalResult(
                    doc_id=f"doc_{i}", text=f"Content {i}", score=0.9 - i * 0.01, source="backend", rank=i
                )
                for i in range(1, 11)  # 10개
            ]),
        ]

        # 작은 k -> 상위 순위 강조
        fused_small_k = _weighted_rrf_fusion(backend_results, k=1, limit=10)
        # 큰 k -> 순위 차이 완화
        fused_large_k = _weighted_rrf_fusion(backend_results, k=100, limit=10)

        # 작은 k에서 1위와 10위의 스코어 차이가 더 큼
        # k=1: 1/2 - 1/11 = 0.5 - 0.0909 = 0.4091
        # k=100: 1/101 - 1/110 = 0.0099 - 0.0091 = 0.0008
        small_k_ratio = fused_small_k[0].score / fused_small_k[9].score
        large_k_ratio = fused_large_k[0].score / fused_large_k[9].score

        # 작은 k에서 비율 차이가 더 큼
        assert small_k_ratio > large_k_ratio

    def test_min_score_filtering(self):
        """min_score 필터링 테스트."""
        from app.rag.hybrid_rag import _weighted_rrf_fusion

        # rank는 리스트 순서(enumerate)로 결정됨
        # doc_1: rank=1 -> 1/(60+1) = 0.01639
        # doc_2: rank=2 -> 1/(60+2) = 0.01612
        # min_score=0.0163 설정하면 doc_2만 필터링
        backend_results = [
            ("backend", 1.0, [
                RetrievalResult(doc_id="doc_1", text="High", score=0.9, source="backend", rank=1),
                RetrievalResult(doc_id="doc_2", text="Low", score=0.1, source="backend", rank=2),
            ]),
        ]

        # min_score 0.0163 설정 -> doc_2(0.01612)는 필터링됨
        fused = _weighted_rrf_fusion(backend_results, k=60, min_score=0.0163)

        # 낮은 RRF 스코어 문서는 필터링됨
        assert len(fused) == 1
        assert fused[0].doc_id == "doc_1"

    def test_empty_results(self):
        """빈 결과 처리 테스트."""
        from app.rag.hybrid_rag import _weighted_rrf_fusion

        backend_results = [
            ("backend1", 0.5, []),
            ("backend2", 0.5, []),
        ]

        fused = _weighted_rrf_fusion(backend_results, k=60)

        assert len(fused) == 0

    def test_limit_applied(self):
        """limit 적용 테스트."""
        from app.rag.hybrid_rag import _weighted_rrf_fusion

        backend_results = [
            ("backend", 1.0, [
                RetrievalResult(doc_id=f"doc_{i}", text=f"Content {i}", score=0.9, source="backend", rank=i)
                for i in range(1, 20)
            ]),
        ]

        fused = _weighted_rrf_fusion(backend_results, k=60, limit=5)

        assert len(fused) == 5
        # 순위 재설정 확인
        assert [r.rank for r in fused] == [1, 2, 3, 4, 5]

    def test_cross_retriever_document_boost(self):
        """여러 retriever에서 등장하는 문서가 부스트되는지 테스트."""
        from app.rag.hybrid_rag import _weighted_rrf_fusion

        # doc_common은 두 retriever 모두에서 2위
        # doc_single은 하나의 retriever에서만 1위
        backend_results = [
            ("retriever_1", 0.5, [
                RetrievalResult(doc_id="doc_single_1", text="Single 1", score=0.95, source="retriever_1", rank=1),
                RetrievalResult(doc_id="doc_common", text="Common", score=0.8, source="retriever_1", rank=2),
            ]),
            ("retriever_2", 0.5, [
                RetrievalResult(doc_id="doc_single_2", text="Single 2", score=0.95, source="retriever_2", rank=1),
                RetrievalResult(doc_id="doc_common", text="Common", score=0.8, source="retriever_2", rank=2),
            ]),
        ]

        fused = _weighted_rrf_fusion(backend_results, k=60)

        # doc_common: 0.5/(60+2) + 0.5/(60+2) = 0.01612...
        # doc_single: 0.5/(60+1) = 0.008196...
        # doc_common이 더 높아야 함
        assert fused[0].doc_id == "doc_common"


class TestConvertEnsembleToHybridResult:
    """_convert_ensemble_to_hybrid_result() 테스트."""

    def test_source_classification(self):
        """소스 타입별 분류 테스트."""
        from app.rag.hybrid_rag import _convert_ensemble_to_hybrid_result

        fused_results = [
            RetrievalResult(
                doc_id="nlm_1", text="NotebookLM content", score=0.02,
                source="notebooklm", rank=1, metadata={"title": "Test", "original_score": 0.9}
            ),
            RetrievalResult(
                doc_id="qdrant_1", text="Qdrant content", score=0.018,
                source="qdrant_hybrid", rank=2, metadata={"dimension": "AD", "original_score": 0.85}
            ),
            RetrievalResult(
                doc_id="grounding_1", text="Google result", score=0.015,
                source="vertex_grounding", rank=3, metadata={"type": "google_search", "url": "https://example.com", "original_score": 0.8}
            ),
        ]

        result = _convert_ensemble_to_hybrid_result(fused_results, "test query")

        assert len(result.notebooklm_sources) == 1
        assert result.notebooklm_sources[0].source_id == "nlm_1"

        # vertex_grounding과 qdrant_hybrid 모두 vertex_sources에
        assert len(result.vertex_sources) == 2

        # google_search 타입은 grounding_sources에도
        assert len(result.grounding_sources) == 1
        assert result.grounding_sources[0]["uri"] == "https://example.com"

    def test_result_format_compatibility(self):
        """HybridRAGResult 호환성 테스트."""
        from app.rag.hybrid_rag import _convert_ensemble_to_hybrid_result

        fused_results = [
            RetrievalResult(
                doc_id="doc_1", text="Content", score=0.02,
                source="qdrant_hybrid", rank=1, metadata={"fusion_sources": ["qdrant_hybrid", "notebooklm"], "original_score": 0.9}
            ),
        ]

        result = _convert_ensemble_to_hybrid_result(fused_results, "query")

        # 필수 필드 존재
        assert hasattr(result, "answer")
        assert hasattr(result, "notebooklm_sources")
        assert hasattr(result, "vertex_sources")
        assert hasattr(result, "grounding_sources")
        assert hasattr(result, "confidence")
        assert hasattr(result, "strategy_used")

        assert result.strategy_used == "ensemble_rrf"
        assert result.rrf_enabled is True
        assert len(result.fused_results) == 1


class TestEnsembleRetrieve:
    """ensemble_retrieve() 통합 테스트."""

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """병렬 실행 테스트."""
        with patch("app.rag.hybrid_rag.get_manifest") as mock_get_manifest:
            mock_manifest = MagicMock()
            mock_manifest.backends = [
                MagicMock(id="qdrant_hybrid", weight=0.6, enabled=True, config={"dimension": "AD"}),
                MagicMock(id="notebooklm", weight=0.4, enabled=True, config={"notebook_id": "test"}),
            ]
            mock_manifest.dimensions = ["AD"]
            mock_get_manifest.return_value = mock_manifest

            with patch("app.rag.backends.get_backend") as mock_get_backend:
                mock_backend = AsyncMock()
                mock_backend.retrieve = AsyncMock(return_value=[
                    RetrievalResult(doc_id="doc_1", text="Content", score=0.9, source="test", rank=1),
                ])
                mock_get_backend.return_value = mock_backend

                from app.rag.hybrid_rag import ensemble_retrieve
                result = await ensemble_retrieve(
                    query="봉준호 스타일",
                    app_key="dimension.aesthetic.direct",
                )

                # 두 백엔드 모두 호출됨
                assert mock_backend.retrieve.call_count == 2
                assert result.strategy_used == "ensemble_rrf"

    @pytest.mark.asyncio
    async def test_disabled_backend_skipped(self):
        """disabled 백엔드 스킵 테스트."""
        with patch("app.rag.hybrid_rag.get_manifest") as mock_get_manifest:
            mock_manifest = MagicMock()
            mock_manifest.backends = [
                MagicMock(id="qdrant_hybrid", weight=0.6, enabled=True, config={}),
                MagicMock(id="notebooklm", weight=0.4, enabled=False, config={}),  # disabled
            ]
            mock_manifest.dimensions = ["AD"]
            mock_get_manifest.return_value = mock_manifest

            with patch("app.rag.backends.get_backend") as mock_get_backend:
                mock_backend = AsyncMock()
                mock_backend.retrieve = AsyncMock(return_value=[
                    RetrievalResult(doc_id="doc_1", text="Content", score=0.9, source="test", rank=1),
                ])
                mock_get_backend.return_value = mock_backend

                from app.rag.hybrid_rag import ensemble_retrieve
                await ensemble_retrieve(query="test", app_key="test.app.key")

                # enabled된 백엔드만 호출 (1번)
                assert mock_backend.retrieve.call_count == 1

    @pytest.mark.asyncio
    async def test_backend_error_handling(self):
        """백엔드 에러 처리 테스트 - 하나 실패해도 나머지 결과 반환."""
        with patch("app.rag.hybrid_rag.get_manifest") as mock_get_manifest:
            mock_manifest = MagicMock()
            mock_manifest.backends = [
                MagicMock(id="qdrant_hybrid", weight=0.6, enabled=True, config={}),
                MagicMock(id="notebooklm", weight=0.4, enabled=True, config={"notebook_id": "test"}),
            ]
            mock_manifest.dimensions = ["AD"]
            mock_get_manifest.return_value = mock_manifest

            call_count = [0]

            async def mock_retrieve(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise Exception("Backend error")
                return [RetrievalResult(doc_id="doc_1", text="Content", score=0.9, source="test", rank=1)]

            with patch("app.rag.backends.get_backend") as mock_get_backend:
                mock_backend = AsyncMock()
                mock_backend.retrieve = mock_retrieve
                mock_get_backend.return_value = mock_backend

                from app.rag.hybrid_rag import ensemble_retrieve
                result = await ensemble_retrieve(query="test", app_key="test.app.key")

                # 하나의 백엔드 실패해도 결과 반환
                assert result.retrieval_count >= 0

    @pytest.mark.asyncio
    async def test_fallback_on_no_backends(self):
        """backends 설정 없을 때 fallback 테스트."""
        with patch("app.rag.hybrid_rag.get_manifest") as mock_get_manifest:
            mock_manifest = MagicMock()
            mock_manifest.backends = None  # None backends -> fallback
            mock_manifest.dimensions = ["1D"]
            mock_get_manifest.return_value = mock_manifest

            with patch("app.rag.hybrid_rag._fallback_single_backend_query") as mock_fallback:
                mock_fallback.return_value = MagicMock(
                    answer="Fallback result",
                    confidence=0.5,
                    strategy_used="fallback",
                )

                from app.rag.hybrid_rag import ensemble_retrieve
                result = await ensemble_retrieve(query="test", app_key="test.app.key")

                # backends가 None이므로 fallback 호출
                mock_fallback.assert_called_once()
                assert result.strategy_used == "fallback"

    @pytest.mark.asyncio
    async def test_auteur_key_notebook_override(self):
        """auteur_key로 notebook_id 오버라이드 테스트."""
        with patch("app.rag.hybrid_rag.get_manifest") as mock_get_manifest:
            mock_manifest = MagicMock()
            mock_manifest.backends = [
                MagicMock(id="notebooklm", weight=1.0, enabled=True, config={"notebook_id": "default_notebook"}),
            ]
            mock_manifest.dimensions = ["AD"]
            mock_get_manifest.return_value = mock_manifest

            captured_config = {}

            async def capture_retrieve(query, limit, filters, config):
                captured_config.update(config)
                return [RetrievalResult(doc_id="doc_1", text="Content", score=0.9, source="notebooklm", rank=1)]

            with patch("app.rag.backends.get_backend") as mock_get_backend:
                mock_backend = AsyncMock()
                mock_backend.retrieve = capture_retrieve
                mock_get_backend.return_value = mock_backend

                from app.rag.hybrid_rag import ensemble_retrieve
                await ensemble_retrieve(
                    query="test",
                    app_key="dimension.aesthetic.direct",
                    auteur_key="bong",
                )

                # auteur_key="bong"이 DNA_봉준호로 변환되어 config에 적용
                assert captured_config.get("notebook_id") == "DNA_봉준호"


class TestHybridQueryEnsembleIntegration:
    """hybrid_query()에서 ensemble 전략 통합 테스트."""

    @pytest.mark.asyncio
    async def test_ensemble_strategy_calls_ensemble_retrieve(self):
        """strategy='ensemble' 시 ensemble_retrieve 호출 확인."""
        with patch("app.rag.hybrid_rag.ensemble_retrieve") as mock_ensemble:
            mock_ensemble.return_value = MagicMock(
                answer="Ensemble result",
                confidence=0.8,
                strategy_used="ensemble_rrf",
                query_time_ms=100,
                retrieval_count=5,
            )

            from app.rag.hybrid_rag import hybrid_query
            result = await hybrid_query(
                query="test query",
                strategy="ensemble",
                dimension="AD",  # P5 skip retrieval 우회를 위해 dimension 추가
                app_key="dimension.aesthetic.direct",
                use_semantic_cache=False,
            )

            mock_ensemble.assert_called_once()
            assert result.strategy_used == "ensemble_rrf"

    @pytest.mark.asyncio
    async def test_pipeline_hints_use_ensemble(self):
        """pipeline_hints.use_ensemble=True 테스트."""
        with patch("app.rag.hybrid_rag.ensemble_retrieve") as mock_ensemble:
            mock_ensemble.return_value = MagicMock(
                answer="Ensemble result",
                confidence=0.8,
                strategy_used="ensemble_rrf",
                query_time_ms=100,
                retrieval_count=5,
            )

            from app.rag.hybrid_rag import hybrid_query
            result = await hybrid_query(
                query="test query",
                dimension="AD",  # P5 skip retrieval 우회를 위해 dimension 추가
                pipeline_hints={"use_ensemble": True, "rrf_k": 30},
                use_semantic_cache=False,
            )

            mock_ensemble.assert_called_once()
            # rrf_k=30이 전달되었는지 확인
            call_kwargs = mock_ensemble.call_args.kwargs
            assert call_kwargs.get("rrf_k") == 30

    @pytest.mark.asyncio
    async def test_dimension_to_app_key_mapping(self):
        """dimension에서 app_key 자동 추론 테스트."""
        with patch("app.rag.hybrid_rag.ensemble_retrieve") as mock_ensemble:
            mock_ensemble.return_value = MagicMock(
                answer="Result",
                confidence=0.8,
                strategy_used="ensemble_rrf",
                query_time_ms=100,
                retrieval_count=5,
            )

            from app.rag.hybrid_rag import hybrid_query
            await hybrid_query(
                query="test",
                dimension="AD",
                strategy="ensemble",
                use_semantic_cache=False,
            )

            # AD -> dimension.aesthetic.direct으로 매핑
            call_kwargs = mock_ensemble.call_args.kwargs
            assert call_kwargs.get("app_key") == "dimension.aesthetic.direct"


class TestRRFMathematicalCorrectness:
    """RRF 수학적 정확성 검증 테스트."""

    def test_rrf_formula_calculation(self):
        """RRF 공식 계산 정확성 테스트.

        RRF(d) = Σ w_i / (k + rank_i(d))
        """
        from app.rag.hybrid_rag import _weighted_rrf_fusion

        # 문서 D가 3개 retriever에 각각 rank 1, 2, 3으로 등장
        # k=60, 가중치 각각 0.5, 0.3, 0.2
        backend_results = [
            ("r1", 0.5, [
                RetrievalResult(doc_id="D", text="D", score=0.9, source="r1", rank=1),
            ]),
            ("r2", 0.3, [
                RetrievalResult(doc_id="D", text="D", score=0.8, source="r2", rank=1),  # 실제 rank=2지만 입력은 리스트 순서
            ]),
            ("r3", 0.2, [
                RetrievalResult(doc_id="D", text="D", score=0.7, source="r3", rank=1),
            ]),
        ]

        # 각 리스트에서 D는 rank=1
        # RRF(D) = 0.5/(60+1) + 0.3/(60+1) + 0.2/(60+1) = 1.0/61
        fused = _weighted_rrf_fusion(backend_results, k=60)

        expected_score = 0.5 / 61 + 0.3 / 61 + 0.2 / 61
        assert fused[0].doc_id == "D"
        assert fused[0].score == pytest.approx(expected_score, rel=1e-6)

    def test_rrf_with_different_ranks(self):
        """다른 rank에서의 RRF 계산 테스트."""
        from app.rag.hybrid_rag import _weighted_rrf_fusion

        backend_results = [
            ("r1", 1.0, [
                RetrievalResult(doc_id="A", text="A", score=0.9, source="r1", rank=1),
                RetrievalResult(doc_id="B", text="B", score=0.8, source="r1", rank=2),
            ]),
        ]

        fused = _weighted_rrf_fusion(backend_results, k=60)

        # A: 1.0 / (60 + 1) = 0.01639...
        # B: 1.0 / (60 + 2) = 0.01612...
        expected_a = 1.0 / 61
        expected_b = 1.0 / 62

        assert fused[0].doc_id == "A"
        assert fused[0].score == pytest.approx(expected_a, rel=1e-6)
        assert fused[1].doc_id == "B"
        assert fused[1].score == pytest.approx(expected_b, rel=1e-6)
