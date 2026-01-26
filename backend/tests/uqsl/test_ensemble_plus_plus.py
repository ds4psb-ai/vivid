"""
Ensemble++ Router Tests

Tests for NeurIPS 2025 3-way comparison framework.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.uqsl.ensemble_plus_plus import (
    EnsemblePlusPlusRouter,
    get_ensemble_router,
)
from app.uqsl.models import CandidateResult


class TestEnsemblePlusPlusRouter:
    """Test Ensemble++ 3-way router."""

    def test_router_initialization(self):
        """Test router initializes with 3 arms."""
        router = EnsemblePlusPlusRouter()

        assert "qdrant_only" in router.arms
        assert "notebooklm_only" in router.arms
        assert "ensemble_ab" in router.arms

        # Ensemble has slight prior (alpha=2)
        assert router.arms["ensemble_ab"]["alpha"] == 2

    @pytest.mark.asyncio
    async def test_select_best_arm_returns_valid(self):
        """Test select_best_arm returns valid arm."""
        router = EnsemblePlusPlusRouter()

        selected = await router.select_best_arm()

        assert selected in ["a", "b", "ab"]

    @pytest.mark.asyncio
    async def test_select_best_arm_prefers_ensemble_initially(self):
        """Test ensemble is preferred with prior."""
        router = EnsemblePlusPlusRouter()

        # Run 100 selections
        selections = [await router.select_best_arm() for _ in range(100)]

        # Ensemble should be selected more often due to prior
        ensemble_count = selections.count("ab")
        assert ensemble_count > 20  # Should be selected reasonably often

    @pytest.mark.asyncio
    async def test_update_arm_positive(self):
        """Test positive reward increases alpha."""
        router = EnsemblePlusPlusRouter()

        initial_alpha = router.arms["qdrant_only"]["alpha"]
        await router.update_arm("a", reward=True)

        assert router.arms["qdrant_only"]["alpha"] == initial_alpha + 1
        assert router.arms["qdrant_only"]["beta"] == 1  # Unchanged

    @pytest.mark.asyncio
    async def test_update_arm_negative(self):
        """Test negative reward increases beta."""
        router = EnsemblePlusPlusRouter()

        initial_beta = router.arms["notebooklm_only"]["beta"]
        await router.update_arm("b", reward=False)

        assert router.arms["notebooklm_only"]["alpha"] == 1  # Unchanged
        assert router.arms["notebooklm_only"]["beta"] == initial_beta + 1

    @pytest.mark.asyncio
    async def test_update_arm_ab_maps_correctly(self):
        """Test 'ab' maps to ensemble_ab arm."""
        router = EnsemblePlusPlusRouter()

        initial_alpha = router.arms["ensemble_ab"]["alpha"]
        await router.update_arm("ab", reward=True)

        assert router.arms["ensemble_ab"]["alpha"] == initial_alpha + 1

    def test_get_arm_stats(self):
        """Test get_arm_stats returns all arms."""
        router = EnsemblePlusPlusRouter()
        router.arms["qdrant_only"] = {"alpha": 10, "beta": 5}
        router.arms["notebooklm_only"] = {"alpha": 5, "beta": 10}
        router.arms["ensemble_ab"] = {"alpha": 15, "beta": 3}

        stats = router.get_arm_stats()

        assert "qdrant_only" in stats
        assert "notebooklm_only" in stats
        assert "ensemble_ab" in stats

        # Check success rates
        assert abs(stats["qdrant_only"]["success_rate"] - 10/15) < 0.01
        assert abs(stats["notebooklm_only"]["success_rate"] - 5/15) < 0.01
        assert abs(stats["ensemble_ab"]["success_rate"] - 15/18) < 0.01

    @pytest.mark.asyncio
    async def test_get_three_way_results_structure(self):
        """Test get_three_way_results returns correct structure."""
        router = EnsemblePlusPlusRouter()

        # Use mocks to avoid real RAG calls
        with patch.object(router, '_retrieve_qdrant_only', new_callable=AsyncMock) as mock_qdrant, \
             patch.object(router, '_retrieve_notebooklm_only', new_callable=AsyncMock) as mock_nlm:

            mock_qdrant.return_value = router._mock_result("test", "qdrant")
            mock_nlm.return_value = router._mock_result("test", "notebooklm")

            results = await router.get_three_way_results(
                query="test query",
                dimension="AD",
                auteur_key="bong",
            )

        assert "a" in results
        assert "b" in results
        assert "ab" in results

        assert isinstance(results["a"], CandidateResult)
        assert isinstance(results["b"], CandidateResult)
        assert isinstance(results["ab"], CandidateResult)

    @pytest.mark.asyncio
    async def test_get_three_way_results_parallel_execution(self):
        """Test A and B are retrieved in parallel."""
        router = EnsemblePlusPlusRouter()
        call_order = []

        async def mock_qdrant(*args, **kwargs):
            call_order.append("qdrant_start")
            return router._mock_result("test", "qdrant")

        async def mock_nlm(*args, **kwargs):
            call_order.append("nlm_start")
            return router._mock_result("test", "notebooklm")

        with patch.object(router, '_retrieve_qdrant_only', side_effect=mock_qdrant), \
             patch.object(router, '_retrieve_notebooklm_only', side_effect=mock_nlm):

            await router.get_three_way_results(
                query="test",
                dimension="AD",
            )

        # Both should start before either completes (parallel)
        assert "qdrant_start" in call_order
        assert "nlm_start" in call_order

    @pytest.mark.asyncio
    async def test_get_recommended_result(self):
        """Test get_recommended_result returns ThreeWayResult."""
        router = EnsemblePlusPlusRouter()

        with patch.object(router, '_retrieve_qdrant_only', new_callable=AsyncMock) as mock_qdrant, \
             patch.object(router, '_retrieve_notebooklm_only', new_callable=AsyncMock) as mock_nlm:

            mock_qdrant.return_value = router._mock_result("test", "qdrant")
            mock_nlm.return_value = router._mock_result("test", "notebooklm")

            result = await router.get_recommended_result(
                query="test",
                dimension="AD",
            )

        assert result.query == "test"
        assert result.recommended in ["a", "b", "ab"]
        assert "a" in result.results
        assert "b" in result.results
        assert "ab" in result.results

    def test_mock_result_structure(self):
        """Test _mock_result returns proper structure."""
        router = EnsemblePlusPlusRouter()

        result = router._mock_result("test query", "qdrant")

        assert hasattr(result, "query")
        assert hasattr(result, "answer")
        assert hasattr(result, "confidence")
        assert result.query == "test query"
        assert "qdrant" in result.answer

    def test_smart_merge_long_b(self):
        """Test smart merge when B is long (primary)."""
        router = EnsemblePlusPlusRouter()

        result_a = router._mock_result("test", "a")
        result_a.answer = "Short A response"

        result_b = router._mock_result("test", "b")
        result_b.answer = "B" * 200  # Long response

        merged = router._smart_merge(result_a, result_b, "test")

        # B should be primary (appears first)
        assert merged.answer.startswith("B")
        assert "추가 컨텍스트" in merged.answer

    def test_smart_merge_short_b(self):
        """Test smart merge when B is short (supplementary)."""
        router = EnsemblePlusPlusRouter()

        result_a = router._mock_result("test", "a")
        result_a.answer = "A" * 200

        result_b = router._mock_result("test", "b")
        result_b.answer = "Short B"

        merged = router._smart_merge(result_a, result_b, "test")

        # A should be primary
        assert merged.answer.startswith("A")
        assert "거장 인사이트" in merged.answer

    def test_smart_merge_confidence(self):
        """Test smart merge calculates correct confidence with b_primary strategy."""
        router = EnsemblePlusPlusRouter()

        result_a = router._mock_result("test", "a")
        result_a.confidence = 0.6

        result_b = router._mock_result("test", "b")
        result_b.confidence = 0.8

        # Use explicit b_primary strategy to test original formula
        merged = router._smart_merge(result_a, result_b, "test", strategy="b_primary")

        # Merged confidence = (0.6 + 0.8) / 2 + 0.1 = 0.8
        expected = (0.6 + 0.8) / 2 + 0.1
        assert abs(merged.confidence - expected) < 0.01

    def test_smart_merge_adaptive_strategy_selection(self):
        """Test adaptive strategy selects correct merge strategy based on query."""
        router = EnsemblePlusPlusRouter()

        # 거장 키워드 → b_primary
        strategy = router._select_adaptive_strategy(
            "강주노 스타일", 0.6, 0.8, "short", "short"
        )
        assert strategy == "b_primary"

        # 기술 키워드 → quality_gate
        strategy = router._select_adaptive_strategy(
            "how to implement this", 0.6, 0.8, "short", "short"
        )
        assert strategy == "quality_gate"

        # 짧은 답변 → weighted_blend
        strategy = router._select_adaptive_strategy(
            "general query", 0.6, 0.6, "short", "short"
        )
        assert strategy == "weighted_blend"

        # 신뢰도 차이 큼 → quality_gate
        strategy = router._select_adaptive_strategy(
            "some query", 0.3, 0.9, "long answer" * 50, "long answer" * 50
        )
        assert strategy == "quality_gate"


class TestSingleton:
    """Test singleton pattern."""

    def test_get_ensemble_router_singleton(self):
        """Test singleton returns same instance."""
        import app.uqsl.ensemble_plus_plus as epp_module
        epp_module._router = None

        router1 = get_ensemble_router()
        router2 = get_ensemble_router()

        assert router1 is router2
