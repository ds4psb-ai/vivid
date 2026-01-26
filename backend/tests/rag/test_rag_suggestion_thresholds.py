"""
P6-1 Tests: confidence_threshold 백엔드 강제 검증.

Tests:
1. SuggestionService: threshold 이하 결과 필터링
2. SuggestionService: threshold 통과 결과만 evidence_refs에 포함
3. SemanticCache: min_confidence 게이팅
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from dataclasses import dataclass
from typing import List, Dict, Any


# ============================================================================
# Suggestion Threshold Tests
# ============================================================================

class TestSuggestionThresholds:
    """RAGSuggestionService confidence_threshold 테스트."""
    
    def _make_mock_results(self, scores: List[float]) -> List[Dict[str, Any]]:
        """테스트용 검색 결과 생성."""
        return [
            {
                "doc_id": f"doc_{i}",
                "content": f"Test content {i}",
                "score": score,
                "source_dimension": "1D",
                "metadata": {"dataset_id": "test_dataset"},
            }
            for i, score in enumerate(scores)
        ]

    def test_all_below_threshold_returns_no_suggestion(self):
        """모든 결과가 threshold 이하면 has_suggestion=False."""
        from app.rag.rag_suggestion_service import RAGSuggestionService
        from app.rag.rag_suggestion import RAGSuggestion
        
        service = RAGSuggestionService()
        
        # Mock: threshold=0.5인 preset
        with patch("app.rag.rag_suggestion_service.get_rag_preset") as mock_preset:
            mock_preset.return_value = MagicMock(confidence_threshold=0.5)
            
            # Mock: 모든 score가 0.5 미만
            with patch.object(service._registry, "get_context_for_app") as mock_rag:
                mock_rag.return_value = {
                    "results": self._make_mock_results([0.3, 0.4, 0.45]),
                    "formatted_context": "test context",
                }
                
                with patch("app.rag.rag_suggestion_service.get_manifest") as mock_manifest:
                    mock_manifest.return_value = MagicMock(
                        dimensions=["1D"],
                        dataset_labels={"test_dataset": "Test Dataset"},
                    )
                    
                    result = service.get_suggestion(
                        app_key="test.app",
                        query="test query",
                    )
                    
                    assert result.has_suggestion is False
                    assert len(result.evidence_refs) == 0

    def test_mixed_scores_filters_below_threshold(self):
        """threshold 이상/이하 혼합 시 이상만 evidence_refs에 포함."""
        from app.rag.rag_suggestion_service import RAGSuggestionService
        
        service = RAGSuggestionService()
        
        with patch("app.rag.rag_suggestion_service.get_rag_preset") as mock_preset:
            mock_preset.return_value = MagicMock(confidence_threshold=0.5)
            
            # 5개 중 2개만 threshold 통과
            with patch.object(service._registry, "get_context_for_app") as mock_rag:
                mock_rag.return_value = {
                    "results": self._make_mock_results([0.3, 0.6, 0.4, 0.8, 0.45]),
                    "formatted_context": "test context",
                }
                
                with patch("app.rag.rag_suggestion_service.get_manifest") as mock_manifest:
                    mock_manifest.return_value = MagicMock(
                        dimensions=["1D"],
                        dataset_labels={"test_dataset": "Test Dataset"},
                    )
                    
                    with patch("app.rag.rag_suggestion_service._get_trace_context") as mock_trace:
                        mock_trace.return_value = ("test_trace_id", "span_id")
                        
                        result = service.get_suggestion(
                            app_key="test.app",
                            query="test query",
                        )
                        
                        assert result.has_suggestion is True
                        assert result.total_results == 2  # filtered count
                        # confidence는 filtered results의 max
                        assert result.confidence == 0.8

    def test_dimension_specific_threshold(self):
        """차원별로 다른 threshold 적용 확인."""
        from app.rag.rag_suggestion_service import RAGSuggestionService
        
        service = RAGSuggestionService()
        
        # AD 차원은 threshold=0.7
        with patch("app.rag.rag_suggestion_service.get_rag_preset") as mock_preset:
            mock_preset.return_value = MagicMock(confidence_threshold=0.7)
            
            with patch.object(service._registry, "get_context_for_app") as mock_rag:
                mock_rag.return_value = {
                    "results": [
                        {
                            "doc_id": "doc_1",
                            "content": "Test",
                            "score": 0.65,  # AD threshold(0.7) 미만
                            "source_dimension": "AD",
                            "metadata": {"dataset_id": "auteur_dna"},
                        }
                    ],
                    "formatted_context": "test",
                }
                
                with patch("app.rag.rag_suggestion_service.get_manifest") as mock_manifest:
                    mock_manifest.return_value = MagicMock(
                        dimensions=["AD"],
                        dataset_labels={},
                    )
                    
                    result = service.get_suggestion(
                        app_key="dimension.aesthetic.direct",
                        query="강주노 스타일",
                    )
                    
                    # 0.65 < 0.7 이므로 필터됨
                    assert result.has_suggestion is False


# ============================================================================
# Semantic Cache Gating Tests
# ============================================================================

class TestSemanticCacheGating:
    """SemanticCache min_confidence 게이팅 테스트."""
    
    @pytest.mark.asyncio
    async def test_skip_cache_below_min_confidence(self):
        """min_confidence 미만이면 캐시 저장 스킵."""
        from app.rag.semantic_cache import SemanticCache
        
        cache = SemanticCache(use_db=False)
        cache._embeddings_model = "hash_only"  # 외부 의존 제거
        
        @dataclass
        class MockResponse:
            confidence: float = 0.0
            grounded: bool = False
        
        # min_confidence=0.7, response.confidence=0.6 → 저장 안됨
        await cache.set(
            query="test query",
            response=MockResponse(confidence=0.6),
            min_confidence=0.7,
        )
        
        # 캐시에 없어야 함
        result = await cache.get(query="test query")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_above_min_confidence(self):
        """min_confidence 이상이면 캐시 저장됨."""
        from app.rag.semantic_cache import SemanticCache
        
        cache = SemanticCache(use_db=False)
        cache._embeddings_model = "hash_only"
        
        @dataclass
        class MockResponse:
            confidence: float = 0.0
            grounded: bool = False
            answer: str = "test answer"
            strategy_used: str = "test"
        
        # min_confidence=0.7, response.confidence=0.8 → 저장됨
        await cache.set(
            query="test query 2",
            response=MockResponse(confidence=0.8),
            min_confidence=0.7,
        )
        
        # 캐시에 있어야 함 (Memory L1에서)
        query_hash = cache._make_hash("test query 2", None, None, None)
        assert query_hash in cache._memory_cache

    @pytest.mark.asyncio
    async def test_cache_ttl_override(self):
        """cache_ttl 인자가 기본 TTL을 override."""
        from app.rag.semantic_cache import SemanticCache
        from datetime import datetime, timedelta
        
        cache = SemanticCache(use_db=False)
        cache._embeddings_model = "hash_only"
        
        @dataclass
        class MockResponse:
            confidence: float = 0.8
            grounded: bool = False
        
        custom_ttl = 7200  # 2시간
        
        await cache.set(
            query="ttl test query",
            response=MockResponse(),
            cache_ttl=custom_ttl,
        )
        
        query_hash = cache._make_hash("ttl test query", None, None, None)
        entry = cache._memory_cache.get(query_hash)
        
        assert entry is not None
        # expires_at이 대략 2시간 후여야 함 (±1분 오차 허용)
        expected_expires = datetime.now() + timedelta(seconds=custom_ttl)
        delta = abs((entry.expires_at - expected_expires).total_seconds())
        assert delta < 60  # 1분 이내 오차
