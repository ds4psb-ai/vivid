"""Tests for Model Router service (Phase 5).

Tests cover:
- Complexity analysis
- Model tier routing
- Cost estimation
- Routing statistics
"""
import pytest
from uuid import uuid4

from app.schemas.agent_task import AgentTask, AgentTaskType, TaskComplexity
from app.services.model_router import (
    ComplexityAnalyzer,
    ModelConfig,
    ModelRouter,
    ModelTier,
    MODEL_CONFIGS,
    get_model_router,
)


# =============================================================================
# Model Configuration Tests
# =============================================================================


class TestModelConfig:
    """Tests for ModelConfig dataclass."""

    def test_flash_config_exists(self):
        """FLASH tier config should exist."""
        config = MODEL_CONFIGS[ModelTier.FLASH]
        assert config.tier == ModelTier.FLASH
        assert config.model_id == "gemini-2.0-flash"
        assert config.input_cost_per_million == 0.10

    def test_pro_config_exists(self):
        """PRO tier config should exist."""
        config = MODEL_CONFIGS[ModelTier.PRO]
        assert config.tier == ModelTier.PRO
        assert config.model_id == "gemini-2.0-pro"
        assert config.input_cost_per_million == 1.25

    def test_ultra_config_exists(self):
        """ULTRA tier config should exist."""
        config = MODEL_CONFIGS[ModelTier.ULTRA]
        assert config.tier == ModelTier.ULTRA
        assert config.model_id == "gemini-2.0-ultra"
        assert config.input_cost_per_million == 5.00

    def test_flash_cheapest(self):
        """FLASH should have lowest input cost."""
        flash_cost = MODEL_CONFIGS[ModelTier.FLASH].input_cost_per_million
        pro_cost = MODEL_CONFIGS[ModelTier.PRO].input_cost_per_million
        ultra_cost = MODEL_CONFIGS[ModelTier.ULTRA].input_cost_per_million

        assert flash_cost < pro_cost < ultra_cost

    def test_ultra_highest_max_tokens(self):
        """ULTRA should have highest max_tokens."""
        flash_tokens = MODEL_CONFIGS[ModelTier.FLASH].max_tokens
        ultra_tokens = MODEL_CONFIGS[ModelTier.ULTRA].max_tokens

        assert ultra_tokens > flash_tokens

    def test_all_configs_support_streaming(self):
        """All models should support streaming."""
        for config in MODEL_CONFIGS.values():
            assert config.supports_streaming is True


# =============================================================================
# Complexity Analyzer Tests
# =============================================================================


class TestComplexityAnalyzer:
    """Tests for ComplexityAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        return ComplexityAnalyzer()

    def test_analyze_low_complexity_validate(self, analyzer):
        """Validate tasks should be LOW complexity."""
        task = AgentTask(
            task_type=AgentTaskType.VALIDATE,
            input_context={"content": "check this simple text"},
        )
        result = analyzer.analyze(task)
        assert result == TaskComplexity.LOW

    def test_analyze_high_complexity_create(self, analyzer):
        """Create tasks with creative keywords should be HIGH."""
        task = AgentTask(
            task_type=AgentTaskType.CREATE,
            input_context={
                "prompt": "분석하고 창작적인 시나리오를 만들어주세요. 미학적 감독 스타일로.",
            },
        )
        result = analyzer.analyze(task)
        assert result == TaskComplexity.HIGH

    def test_analyze_medium_complexity_default(self, analyzer):
        """Research tasks without strong indicators should be MEDIUM."""
        task = AgentTask(
            task_type=AgentTaskType.RESEARCH,
            input_context={"query": "Find information about this topic"},
        )
        result = analyzer.analyze(task)
        assert result == TaskComplexity.MEDIUM

    def test_analyze_low_complexity_keywords(self, analyzer):
        """Low complexity keywords should reduce complexity."""
        task = AgentTask(
            task_type=AgentTaskType.RESEARCH,
            input_context={
                "query": "classify and extract the summarized data for validation check",
            },
        )
        result = analyzer.analyze(task)
        assert result == TaskComplexity.LOW

    def test_analyze_high_complexity_long_input(self, analyzer):
        """Long input should increase complexity score."""
        long_context = "analyze " * 500  # Long input with analyze keyword
        task = AgentTask(
            task_type=AgentTaskType.ANALYZE,
            input_context={"content": long_context},
        )
        result = analyzer.analyze(task)
        assert result == TaskComplexity.HIGH

    def test_analyze_low_complexity_short_input(self, analyzer):
        """Short input with validate task should be LOW."""
        task = AgentTask(
            task_type=AgentTaskType.VALIDATE,
            input_context={"content": "ok"},
        )
        result = analyzer.analyze(task)
        assert result == TaskComplexity.LOW

    def test_get_analysis_details(self, analyzer):
        """Analysis details should show matched keywords."""
        task = AgentTask(
            task_type=AgentTaskType.CREATE,
            input_context={"prompt": "analyze and create a story"},
        )
        details = analyzer.get_analysis_details(task)

        assert "high_score" in details
        assert "low_score" in details
        assert "high_keywords_matched" in details
        assert "determined_complexity" in details
        assert "analyze" in details["high_keywords_matched"]
        assert "create" in details["high_keywords_matched"]
        assert "story" in details["high_keywords_matched"]

    def test_custom_thresholds(self):
        """Custom thresholds should affect analysis."""
        # Higher threshold makes it harder to get HIGH
        strict_analyzer = ComplexityAnalyzer(high_threshold=10)
        task = AgentTask(
            task_type=AgentTaskType.CREATE,
            input_context={"prompt": "analyze creative story"},
        )
        result = strict_analyzer.analyze(task)
        # With threshold 10, should not reach HIGH
        assert result in [TaskComplexity.LOW, TaskComplexity.MEDIUM]


# =============================================================================
# Model Router Tests
# =============================================================================


class TestModelRouter:
    """Tests for ModelRouter."""

    @pytest.fixture
    def router(self):
        return ModelRouter()

    def test_route_low_complexity_to_flash(self, router):
        """LOW complexity should route to FLASH."""
        task = AgentTask(
            task_type=AgentTaskType.VALIDATE,
            input_context={"content": "simple check"},
            complexity=TaskComplexity.LOW,
        )
        config = router.route(task)
        assert config.tier == ModelTier.FLASH

    def test_route_medium_complexity_to_pro(self, router):
        """MEDIUM complexity should route to PRO."""
        task = AgentTask(
            task_type=AgentTaskType.RESEARCH,
            input_context={"query": "find data"},
            complexity=TaskComplexity.MEDIUM,
        )
        config = router.route(task)
        assert config.tier == ModelTier.PRO

    def test_route_high_complexity_to_ultra(self, router):
        """HIGH complexity should route to ULTRA."""
        task = AgentTask(
            task_type=AgentTaskType.CREATE,
            input_context={"prompt": "complex task"},
            complexity=TaskComplexity.HIGH,
        )
        config = router.route(task)
        assert config.tier == ModelTier.ULTRA

    def test_route_analyzes_if_no_complexity(self, router):
        """Router should analyze if complexity not set."""
        task = AgentTask(
            task_type=AgentTaskType.VALIDATE,
            input_context={"content": "classify simple check"},
        )
        # complexity is None by default
        config = router.route(task)
        # Should analyze and determine LOW/MEDIUM
        assert config.tier in [ModelTier.FLASH, ModelTier.PRO]

    def test_estimate_cost_flash(self, router):
        """Cost estimation for FLASH should be cheap."""
        task = AgentTask(
            task_type=AgentTaskType.VALIDATE,
            input_context={"content": "check"},
            complexity=TaskComplexity.LOW,
        )
        cost = router.estimate_cost(task, input_tokens=1000, output_tokens=500)

        # FLASH: 0.10/M input, 0.40/M output
        # Expected: (1000/1M * 0.10) + (500/1M * 0.40) = 0.0001 + 0.0002 = 0.0003
        assert cost == pytest.approx(0.0003, abs=0.0001)

    def test_estimate_cost_ultra(self, router):
        """Cost estimation for ULTRA should be expensive."""
        task = AgentTask(
            task_type=AgentTaskType.CREATE,
            input_context={"prompt": "complex"},
            complexity=TaskComplexity.HIGH,
        )
        cost = router.estimate_cost(task, input_tokens=1000, output_tokens=500)

        # ULTRA: 5.00/M input, 15.00/M output
        # Expected: (1000/1M * 5.00) + (500/1M * 15.00) = 0.005 + 0.0075 = 0.0125
        assert cost == pytest.approx(0.0125, abs=0.001)

    def test_routing_stats_tracking(self, router):
        """Router should track routing statistics."""
        tasks = [
            AgentTask(task_type=AgentTaskType.VALIDATE, input_context={}, complexity=TaskComplexity.LOW),
            AgentTask(task_type=AgentTaskType.VALIDATE, input_context={}, complexity=TaskComplexity.LOW),
            AgentTask(task_type=AgentTaskType.RESEARCH, input_context={}, complexity=TaskComplexity.MEDIUM),
            AgentTask(task_type=AgentTaskType.CREATE, input_context={}, complexity=TaskComplexity.HIGH),
        ]

        for task in tasks:
            router.route(task)

        stats = router.get_stats()
        assert stats["total_routed"] == 4
        assert stats["by_tier"]["flash"] == 2
        assert stats["by_tier"]["pro"] == 1
        assert stats["by_tier"]["ultra"] == 1
        assert stats["percentages"]["flash"] == 50.0

    def test_reset_stats(self, router):
        """Router should reset statistics."""
        task = AgentTask(
            task_type=AgentTaskType.VALIDATE,
            input_context={},
            complexity=TaskComplexity.LOW,
        )
        router.route(task)
        assert router.get_stats()["total_routed"] == 1

        router.reset_stats()
        assert router.get_stats()["total_routed"] == 0

    def test_route_with_min_tier_override(self, router):
        """Min tier should upgrade routing."""
        task = AgentTask(
            task_type=AgentTaskType.VALIDATE,
            input_context={},
            complexity=TaskComplexity.LOW,
        )
        config = router.route_with_override(task, min_tier=ModelTier.PRO)
        assert config.tier == ModelTier.PRO

    def test_route_with_max_tier_override(self, router):
        """Max tier should downgrade routing."""
        task = AgentTask(
            task_type=AgentTaskType.CREATE,
            input_context={},
            complexity=TaskComplexity.HIGH,
        )
        config = router.route_with_override(task, max_tier=ModelTier.PRO)
        assert config.tier == ModelTier.PRO

    def test_get_config_for_tier(self, router):
        """Should get config for specific tier."""
        config = router.get_config_for_tier(ModelTier.FLASH)
        assert config.tier == ModelTier.FLASH
        assert config.model_id == "gemini-2.0-flash"

    def test_record_actual_cost(self, router):
        """Should record actual costs."""
        router.record_actual_cost(0.01)
        router.record_actual_cost(0.02)

        stats = router.get_stats()
        assert stats["total_actual_cost_usd"] == 0.03


# =============================================================================
# Singleton Tests
# =============================================================================


class TestModelRouterSingleton:
    """Tests for singleton pattern."""

    def test_get_model_router_returns_same_instance(self):
        """Should return same instance."""
        router1 = get_model_router()
        router2 = get_model_router()
        assert router1 is router2

    def test_singleton_persists_state(self):
        """Singleton should persist routing state."""
        router = get_model_router()
        initial_count = router.get_stats()["total_routed"]

        task = AgentTask(
            task_type=AgentTaskType.VALIDATE,
            input_context={},
            complexity=TaskComplexity.LOW,
        )
        router.route(task)

        # Get again and check state persisted
        router2 = get_model_router()
        assert router2.get_stats()["total_routed"] == initial_count + 1
