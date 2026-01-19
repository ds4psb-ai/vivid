"""Model Router for Heterogeneous LLM Routing.

2026 Best Practice: Route 60% cheap, 30% balanced, 10% premium.

References:
- Anthropic: "Route easy queries to Claude Haiku, hard to Sonnet"
- Index.dev: "Cheapest model that can handle the task"

Usage:
    from app.services.model_router import ModelRouter, ModelTier

    router = ModelRouter()
    config = router.route(task)
    print(f"Using {config.model_id}")
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.agent_task import AgentTask, AgentTaskType, TaskComplexity

logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    """Model tier based on cost/capability."""

    FLASH = "flash"  # $0.10/M input - classification, extraction, validation
    PRO = "pro"  # $1.25/M input - generation, analysis
    ULTRA = "ultra"  # $5.00/M input - complex reasoning, creative


class ModelConfig(BaseModel):
    """Model configuration."""

    tier: ModelTier
    model_id: str
    input_cost_per_million: float
    output_cost_per_million: float
    max_tokens: int = 8192
    supports_tools: bool = True
    supports_vision: bool = False
    supports_streaming: bool = True


# 2026 Gemini Pricing (January)
MODEL_CONFIGS: dict[ModelTier, ModelConfig] = {
    ModelTier.FLASH: ModelConfig(
        tier=ModelTier.FLASH,
        model_id="gemini-2.0-flash",
        input_cost_per_million=0.10,
        output_cost_per_million=0.40,
        max_tokens=8192,
        supports_vision=True,
    ),
    ModelTier.PRO: ModelConfig(
        tier=ModelTier.PRO,
        model_id="gemini-2.0-pro",
        input_cost_per_million=1.25,
        output_cost_per_million=5.00,
        max_tokens=8192,
        supports_vision=True,
    ),
    ModelTier.ULTRA: ModelConfig(
        tier=ModelTier.ULTRA,
        model_id="gemini-2.0-ultra",
        input_cost_per_million=5.00,
        output_cost_per_million=15.00,
        max_tokens=32768,
        supports_vision=True,
    ),
}


class ComplexityAnalyzer:
    """Analyze task complexity for model routing.

    Uses keyword matching, task type, and input length to determine
    optimal model tier.
    """

    # Complexity indicators
    HIGH_COMPLEXITY_KEYWORDS = [
        "분석",
        "창작",
        "시나리오",
        "스토리",
        "감독",
        "미학",
        "analyze",
        "create",
        "scenario",
        "story",
        "director",
        "aesthetic",
        "complex",
        "reasoning",
        "creative",
        "worldbuilding",
    ]

    LOW_COMPLEXITY_KEYWORDS = [
        "분류",
        "추출",
        "검증",
        "확인",
        "요약",
        "classify",
        "extract",
        "validate",
        "check",
        "summarize",
        "simple",
        "basic",
        "list",
    ]

    # Task type weights
    HIGH_COMPLEXITY_TASK_TYPES = {AgentTaskType.CREATE, AgentTaskType.ANALYZE}
    LOW_COMPLEXITY_TASK_TYPES = {AgentTaskType.VALIDATE, AgentTaskType.PLAN}

    def __init__(
        self,
        high_threshold: int = 3,
        low_advantage: int = 2,
        long_input_threshold: int = 2000,
        short_input_threshold: int = 200,
    ):
        """Initialize analyzer with configurable thresholds.

        Args:
            high_threshold: Score needed for HIGH complexity
            low_advantage: Advantage LOW needs over HIGH for LOW complexity
            long_input_threshold: Input length considered long
            short_input_threshold: Input length considered short
        """
        self.high_threshold = high_threshold
        self.low_advantage = low_advantage
        self.long_input_threshold = long_input_threshold
        self.short_input_threshold = short_input_threshold

    def analyze(self, task: AgentTask) -> TaskComplexity:
        """Determine task complexity from context.

        Args:
            task: Task to analyze

        Returns:
            Determined complexity level
        """
        context_text = str(task.input_context).lower()

        # Score calculation
        high_score = self._count_keywords(context_text, self.HIGH_COMPLEXITY_KEYWORDS)
        low_score = self._count_keywords(context_text, self.LOW_COMPLEXITY_KEYWORDS)

        # Task type factor
        if task.task_type in self.HIGH_COMPLEXITY_TASK_TYPES:
            high_score += 2
        elif task.task_type in self.LOW_COMPLEXITY_TASK_TYPES:
            low_score += 1

        # Input length factor
        if len(context_text) > self.long_input_threshold:
            high_score += 1
        elif len(context_text) < self.short_input_threshold:
            low_score += 1

        # Determine complexity
        if high_score >= self.high_threshold:
            return TaskComplexity.HIGH
        elif low_score >= high_score + self.low_advantage:
            return TaskComplexity.LOW
        else:
            return TaskComplexity.MEDIUM

    def _count_keywords(self, text: str, keywords: list[str]) -> int:
        """Count matching keywords in text."""
        return sum(1 for kw in keywords if kw in text)

    def get_analysis_details(self, task: AgentTask) -> dict[str, Any]:
        """Get detailed analysis breakdown.

        Useful for debugging and transparency.
        """
        context_text = str(task.input_context).lower()

        high_matches = [kw for kw in self.HIGH_COMPLEXITY_KEYWORDS if kw in context_text]
        low_matches = [kw for kw in self.LOW_COMPLEXITY_KEYWORDS if kw in context_text]

        return {
            "high_score": len(high_matches),
            "low_score": len(low_matches),
            "high_keywords_matched": high_matches,
            "low_keywords_matched": low_matches,
            "task_type": task.task_type.value,
            "input_length": len(context_text),
            "determined_complexity": self.analyze(task).value,
        }


class ModelRouter:
    """Route tasks to appropriate models based on complexity.

    Implements Heterogeneous Model Routing pattern for cost optimization.
    Target: 60% FLASH, 30% PRO, 10% ULTRA.

    Usage:
        router = ModelRouter()
        config = router.route(task)
        # Use config.model_id for API calls
    """

    def __init__(self, analyzer: ComplexityAnalyzer | None = None):
        """Initialize router with optional custom analyzer."""
        self.analyzer = analyzer or ComplexityAnalyzer()
        self._routing_stats: dict[ModelTier, int] = {t: 0 for t in ModelTier}
        self._total_estimated_cost: float = 0.0
        self._total_actual_cost: float = 0.0

    def route(self, task: AgentTask) -> ModelConfig:
        """Select best model for task.

        Args:
            task: Task to route

        Returns:
            ModelConfig for the selected model
        """
        # Use pre-assigned complexity or analyze
        complexity = task.complexity or self.analyzer.analyze(task)

        # Map complexity to tier
        tier_map = {
            TaskComplexity.LOW: ModelTier.FLASH,
            TaskComplexity.MEDIUM: ModelTier.PRO,
            TaskComplexity.HIGH: ModelTier.ULTRA,
        }

        tier = tier_map.get(complexity, ModelTier.PRO)
        self._routing_stats[tier] += 1

        config = MODEL_CONFIGS[tier]
        logger.info(
            f"Routed task {task.task_id} to {config.model_id} "
            f"(complexity={complexity.value}, tier={tier.value})"
        )

        return config

    def route_with_override(
        self,
        task: AgentTask,
        min_tier: ModelTier | None = None,
        max_tier: ModelTier | None = None,
    ) -> ModelConfig:
        """Route with tier constraints.

        Args:
            task: Task to route
            min_tier: Minimum tier (floor)
            max_tier: Maximum tier (ceiling)

        Returns:
            ModelConfig within constraints
        """
        config = self.route(task)

        tier_order = [ModelTier.FLASH, ModelTier.PRO, ModelTier.ULTRA]
        current_idx = tier_order.index(config.tier)

        # Apply constraints
        if min_tier:
            min_idx = tier_order.index(min_tier)
            if current_idx < min_idx:
                config = MODEL_CONFIGS[min_tier]
                logger.info(f"Upgraded task {task.task_id} to {min_tier.value} (min_tier)")

        if max_tier:
            max_idx = tier_order.index(max_tier)
            if current_idx > max_idx:
                config = MODEL_CONFIGS[max_tier]
                logger.info(f"Downgraded task {task.task_id} to {max_tier.value} (max_tier)")

        return config

    def estimate_cost(
        self,
        task: AgentTask,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate cost for a task.

        Args:
            task: Task to estimate cost for
            input_tokens: Expected input token count
            output_tokens: Expected output token count

        Returns:
            Estimated cost in USD
        """
        config = self.route(task)
        input_cost = (input_tokens / 1_000_000) * config.input_cost_per_million
        output_cost = (output_tokens / 1_000_000) * config.output_cost_per_million
        total = input_cost + output_cost

        self._total_estimated_cost += total
        return total

    def record_actual_cost(self, cost: float) -> None:
        """Record actual cost for tracking accuracy."""
        self._total_actual_cost += cost

    def get_config_for_tier(self, tier: ModelTier) -> ModelConfig:
        """Get model config for a specific tier."""
        return MODEL_CONFIGS[tier]

    def get_stats(self) -> dict[str, Any]:
        """Get routing statistics."""
        total = sum(self._routing_stats.values())

        return {
            "total_routed": total,
            "by_tier": {t.value: c for t, c in self._routing_stats.items()},
            "percentages": {
                t.value: round((c / total * 100), 1) if total > 0 else 0
                for t, c in self._routing_stats.items()
            },
            "target_percentages": {
                "flash": 60,
                "pro": 30,
                "ultra": 10,
            },
            "total_estimated_cost_usd": round(self._total_estimated_cost, 4),
            "total_actual_cost_usd": round(self._total_actual_cost, 4),
            "cost_accuracy": (
                round(self._total_actual_cost / self._total_estimated_cost * 100, 1)
                if self._total_estimated_cost > 0
                else None
            ),
        }

    def reset_stats(self) -> None:
        """Reset routing statistics."""
        self._routing_stats = {t: 0 for t in ModelTier}
        self._total_estimated_cost = 0.0
        self._total_actual_cost = 0.0


# Singleton instance for shared routing statistics
_default_router: ModelRouter | None = None


def get_model_router() -> ModelRouter:
    """Get default model router instance."""
    global _default_router
    if _default_router is None:
        _default_router = ModelRouter()
    return _default_router
