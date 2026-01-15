"""
Thompson Sampling Router Tests

Tests for Beta distribution-based multi-armed bandit.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.uqsl.thompson_sampling import (
    ThompsonSamplingRouter,
    get_thompson_sampling_router,
)


class TestThompsonSamplingRouter:
    """Test Thompson Sampling router."""

    def test_router_initialization(self):
        """Test router initializes with default parameters."""
        router = ThompsonSamplingRouter()
        assert router.min_exploration_rate == 0.05
        assert router.decay_factor == 0.99
        assert router.arms == {}

    def test_router_custom_params(self):
        """Test router with custom parameters."""
        router = ThompsonSamplingRouter(
            min_exploration_rate=0.1,
            decay_factor=0.95,
        )
        assert router.min_exploration_rate == 0.1
        assert router.decay_factor == 0.95

    def test_initialize_arm(self):
        """Test arm initialization."""
        router = ThompsonSamplingRouter()
        router.initialize_arm("backend:test")

        assert "backend:test" in router.arms
        assert router.arms["backend:test"]["alpha"] == 1
        assert router.arms["backend:test"]["beta"] == 1
        assert router.arms["backend:test"]["total"] == 0

    def test_initialize_arm_custom_prior(self):
        """Test arm initialization with custom prior."""
        router = ThompsonSamplingRouter()
        router.initialize_arm("backend:test", alpha=5, beta=2)

        assert router.arms["backend:test"]["alpha"] == 5
        assert router.arms["backend:test"]["beta"] == 2

    def test_initialize_arm_idempotent(self):
        """Test initializing same arm twice doesn't overwrite."""
        router = ThompsonSamplingRouter()
        router.initialize_arm("backend:test", alpha=5, beta=2)
        router.initialize_arm("backend:test", alpha=10, beta=10)  # Should not change

        # First initialization values should be preserved
        assert router.arms["backend:test"]["alpha"] == 5
        assert router.arms["backend:test"]["beta"] == 2

    def test_select_arm_no_candidates(self):
        """Test select_arm raises error when no arms match."""
        router = ThompsonSamplingRouter()
        router.initialize_arm("backend:qdrant")

        with pytest.raises(ValueError, match="No arms found"):
            router.select_arm("reranker")  # No reranker arms

    def test_select_arm_single_candidate(self):
        """Test select_arm with single candidate always selects it."""
        router = ThompsonSamplingRouter(min_exploration_rate=0.0)  # No exploration
        router.initialize_arm("backend:qdrant")

        selected = router.select_arm("backend")
        assert selected == "backend:qdrant"

    def test_select_arm_multiple_candidates(self):
        """Test select_arm returns one of the candidates."""
        router = ThompsonSamplingRouter()
        router.initialize_arm("backend:qdrant")
        router.initialize_arm("backend:notebooklm")
        router.initialize_arm("reranker:cross_encoder")

        # Select backend arm
        selected = router.select_arm("backend")
        assert selected in ["backend:qdrant", "backend:notebooklm"]

    def test_select_arm_prefers_high_alpha(self):
        """Test that arms with higher alpha are preferred."""
        router = ThompsonSamplingRouter(min_exploration_rate=0.0)
        router.initialize_arm("backend:good", alpha=100, beta=1)
        router.initialize_arm("backend:bad", alpha=1, beta=100)

        # Run multiple selections and count
        selections = [router.select_arm("backend") for _ in range(100)]
        good_count = selections.count("backend:good")

        # Good arm should be selected much more often
        assert good_count > 80

    def test_select_multiple_arms(self):
        """Test selecting top N arms."""
        router = ThompsonSamplingRouter()
        router.initialize_arm("backend:a")
        router.initialize_arm("backend:b")
        router.initialize_arm("backend:c")

        selected = router.select_multiple_arms("backend", n=2)
        assert len(selected) == 2
        assert all(s.startswith("backend:") for s in selected)

    @pytest.mark.asyncio
    async def test_update_positive_reward(self):
        """Test update with positive reward increases alpha."""
        router = ThompsonSamplingRouter()
        router.initialize_arm("backend:test")

        await router.update(None, "backend:test", reward=True)

        assert router.arms["backend:test"]["alpha"] == 2
        assert router.arms["backend:test"]["beta"] == 1
        assert router.arms["backend:test"]["total"] == 1

    @pytest.mark.asyncio
    async def test_update_negative_reward(self):
        """Test update with negative reward increases beta."""
        router = ThompsonSamplingRouter()
        router.initialize_arm("backend:test")

        await router.update(None, "backend:test", reward=False)

        assert router.arms["backend:test"]["alpha"] == 1
        assert router.arms["backend:test"]["beta"] == 2
        assert router.arms["backend:test"]["total"] == 1

    @pytest.mark.asyncio
    async def test_update_creates_arm_if_missing(self):
        """Test update creates arm if it doesn't exist."""
        router = ThompsonSamplingRouter()

        await router.update(None, "backend:new", reward=True)

        assert "backend:new" in router.arms
        assert router.arms["backend:new"]["alpha"] == 2
        assert router.arms["backend:new"]["total"] == 1

    def test_get_arm_stats(self):
        """Test get_arm_stats returns correct statistics."""
        router = ThompsonSamplingRouter()
        router.arms["backend:test"] = {"alpha": 8, "beta": 2, "total": 10}

        stats = router.get_arm_stats("backend:test")

        assert stats["success_rate"] == 0.8  # 8 / (8+2)
        assert stats["total_trials"] == 10
        assert stats["alpha"] == 8
        assert stats["beta"] == 2
        assert stats["confidence"] > 0.9  # High confidence after 10 trials

    def test_get_arm_stats_missing(self):
        """Test get_arm_stats for missing arm."""
        router = ThompsonSamplingRouter()
        stats = router.get_arm_stats("nonexistent")

        assert stats["success_rate"] == 0.5
        assert stats["confidence"] == 0.0
        assert stats["total_trials"] == 0

    def test_get_all_stats(self):
        """Test get_all_stats returns all arms."""
        router = ThompsonSamplingRouter()
        router.initialize_arm("backend:a")
        router.initialize_arm("backend:b")
        router.initialize_arm("reranker:c")

        all_stats = router.get_all_stats()
        assert len(all_stats) == 3

        backend_stats = router.get_all_stats("backend")
        assert len(backend_stats) == 2

    def test_apply_decay(self):
        """Test decay reduces alpha and beta."""
        router = ThompsonSamplingRouter(decay_factor=0.9)
        router.arms["backend:test"] = {"alpha": 10, "beta": 5, "total": 15}

        router.apply_decay()

        # 10 * 0.9 = 9, 5 * 0.9 = 4.5 -> 4
        assert router.arms["backend:test"]["alpha"] == 9
        assert router.arms["backend:test"]["beta"] == 4

    def test_apply_decay_minimum_one(self):
        """Test decay doesn't go below 1."""
        router = ThompsonSamplingRouter(decay_factor=0.5)
        router.arms["backend:test"] = {"alpha": 1, "beta": 1, "total": 0}

        router.apply_decay()

        # Should stay at 1, not go to 0
        assert router.arms["backend:test"]["alpha"] == 1
        assert router.arms["backend:test"]["beta"] == 1


class TestSingleton:
    """Test singleton pattern."""

    def test_get_thompson_sampling_router_singleton(self):
        """Test singleton returns same instance."""
        # Reset singleton for test
        import app.uqsl.thompson_sampling as ts_module
        ts_module._router = None

        router1 = get_thompson_sampling_router()
        router2 = get_thompson_sampling_router()

        assert router1 is router2

    def test_singleton_has_default_arms(self):
        """Test singleton initializes default arms."""
        import app.uqsl.thompson_sampling as ts_module
        ts_module._router = None

        router = get_thompson_sampling_router()

        assert "backend:qdrant_hybrid" in router.arms
        assert "backend:notebooklm" in router.arms
        assert "reranker:cross_encoder" in router.arms
