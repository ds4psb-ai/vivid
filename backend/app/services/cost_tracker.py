"""Cost Tracker for LLM API Usage.

Tracks actual costs, compares with estimates, and enforces budgets.
Part of Phase 5: Cost Optimization.

Usage:
    from app.services.cost_tracker import CostTracker

    tracker = CostTracker()
    tracker.set_daily_budget(10.0)  # $10/day

    record = tracker.record_cost(
        task_id=task.task_id,
        model_id="gemini-2.0-flash",
        input_tokens=1000,
        output_tokens=500,
        actual_cost=0.0006,
    )
    print(f"Saved ${record.savings_usd:.4f}")
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CostRecord(BaseModel):
    """Individual cost record."""

    task_id: UUID
    model_id: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float  # Cost if using ULTRA
    actual_cost_usd: float
    savings_usd: float  # vs. always using ULTRA
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DailyBudgetExceededError(Exception):
    """Raised when daily budget would be exceeded."""

    def __init__(self, daily_spent: float, daily_budget: float, estimated_cost: float):
        self.daily_spent = daily_spent
        self.daily_budget = daily_budget
        self.estimated_cost = estimated_cost
        super().__init__(
            f"Would exceed daily budget: ${daily_spent:.2f} + ${estimated_cost:.2f} > ${daily_budget:.2f}"
        )


class CostTracker:
    """Track and analyze LLM costs.

    Features:
    - Record costs per task/model
    - Calculate savings vs ULTRA baseline
    - Enforce daily budgets
    - Generate cost reports
    """

    # Reference cost: always using ULTRA (for savings calculation)
    ULTRA_INPUT_COST = 5.00  # per million
    ULTRA_OUTPUT_COST = 15.00

    def __init__(self):
        self._records: list[CostRecord] = []
        self._daily_budget: float | None = None
        self._daily_spent: float = 0.0
        self._budget_reset_date: datetime | None = None

    def set_daily_budget(self, budget_usd: float) -> None:
        """Set daily cost budget.

        Args:
            budget_usd: Maximum daily spend in USD
        """
        self._daily_budget = budget_usd
        self._budget_reset_date = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
        logger.info(f"Daily budget set to ${budget_usd:.2f}, resets at {self._budget_reset_date}")

    def clear_daily_budget(self) -> None:
        """Remove daily budget constraint."""
        self._daily_budget = None
        self._budget_reset_date = None
        logger.info("Daily budget cleared")

    def _check_budget_reset(self) -> None:
        """Reset daily spent if past reset date."""
        if self._budget_reset_date and datetime.utcnow() >= self._budget_reset_date:
            old_spent = self._daily_spent
            self._daily_spent = 0.0
            self._budget_reset_date += timedelta(days=1)
            logger.info(f"Daily budget reset (was ${old_spent:.4f})")

    def _calculate_ultra_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate what the cost would be if using ULTRA."""
        return (
            (input_tokens / 1_000_000) * self.ULTRA_INPUT_COST
            + (output_tokens / 1_000_000) * self.ULTRA_OUTPUT_COST
        )

    def record_cost(
        self,
        task_id: UUID,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        actual_cost: float,
    ) -> CostRecord:
        """Record a cost event.

        Args:
            task_id: Task UUID
            model_id: Model identifier used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            actual_cost: Actual cost in USD

        Returns:
            CostRecord with savings calculation
        """
        self._check_budget_reset()

        # Calculate what it would have cost with ULTRA
        ultra_cost = self._calculate_ultra_cost(input_tokens, output_tokens)

        record = CostRecord(
            task_id=task_id,
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=ultra_cost,
            actual_cost_usd=actual_cost,
            savings_usd=ultra_cost - actual_cost,
        )

        self._records.append(record)
        self._daily_spent += actual_cost

        logger.info(
            f"Cost recorded: ${actual_cost:.4f} for {model_id} "
            f"(saved ${record.savings_usd:.4f} vs ULTRA)"
        )

        return record

    def check_budget(self, estimated_cost: float) -> tuple[bool, str]:
        """Check if estimated cost fits within budget.

        Args:
            estimated_cost: Expected cost in USD

        Returns:
            (allowed, message) tuple
        """
        self._check_budget_reset()

        if self._daily_budget is None:
            return True, "No budget set"

        if self._daily_spent + estimated_cost > self._daily_budget:
            return False, (
                f"Would exceed daily budget "
                f"(${self._daily_spent:.2f} + ${estimated_cost:.2f} > ${self._daily_budget:.2f})"
            )

        remaining = self._daily_budget - self._daily_spent - estimated_cost
        return True, f"Within budget (${remaining:.2f} remaining after)"

    def enforce_budget(self, estimated_cost: float) -> None:
        """Enforce budget constraint, raising if exceeded.

        Args:
            estimated_cost: Expected cost in USD

        Raises:
            DailyBudgetExceededError: If budget would be exceeded
        """
        self._check_budget_reset()

        if self._daily_budget is None:
            return

        if self._daily_spent + estimated_cost > self._daily_budget:
            raise DailyBudgetExceededError(
                self._daily_spent, self._daily_budget, estimated_cost
            )

    def get_daily_status(self) -> dict[str, Any]:
        """Get current daily budget status."""
        self._check_budget_reset()

        return {
            "daily_budget": self._daily_budget,
            "daily_spent": round(self._daily_spent, 4),
            "daily_remaining": (
                round(self._daily_budget - self._daily_spent, 4)
                if self._daily_budget
                else None
            ),
            "budget_utilization_pct": (
                round((self._daily_spent / self._daily_budget) * 100, 1)
                if self._daily_budget and self._daily_budget > 0
                else None
            ),
            "reset_at": self._budget_reset_date.isoformat() if self._budget_reset_date else None,
        }

    def get_summary(self, days: int = 7) -> dict[str, Any]:
        """Get cost summary for recent period.

        Args:
            days: Number of days to include

        Returns:
            Summary statistics
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [r for r in self._records if r.created_at >= cutoff]

        if not recent:
            return {
                "period_days": days,
                "total_cost_usd": 0,
                "total_savings_usd": 0,
                "record_count": 0,
            }

        total_cost = sum(r.actual_cost_usd for r in recent)
        total_savings = sum(r.savings_usd for r in recent)
        total_tokens = sum(r.input_tokens + r.output_tokens for r in recent)

        # Cost by model
        by_model: dict[str, dict[str, Any]] = {}
        for r in recent:
            if r.model_id not in by_model:
                by_model[r.model_id] = {
                    "cost_usd": 0.0,
                    "count": 0,
                    "tokens": 0,
                }
            by_model[r.model_id]["cost_usd"] += r.actual_cost_usd
            by_model[r.model_id]["count"] += 1
            by_model[r.model_id]["tokens"] += r.input_tokens + r.output_tokens

        # Round model stats
        for model_id in by_model:
            by_model[model_id]["cost_usd"] = round(by_model[model_id]["cost_usd"], 4)

        return {
            "period_days": days,
            "total_cost_usd": round(total_cost, 4),
            "total_savings_usd": round(total_savings, 4),
            "savings_percentage": (
                round((total_savings / (total_cost + total_savings)) * 100, 1)
                if total_cost + total_savings > 0
                else 0
            ),
            "total_tokens": total_tokens,
            "cost_per_1k_tokens": (
                round((total_cost / total_tokens) * 1000, 6) if total_tokens > 0 else 0
            ),
            "record_count": len(recent),
            "by_model": by_model,
            "daily_budget": self._daily_budget,
            "daily_spent": round(self._daily_spent, 4),
        }

    def get_records(
        self,
        task_id: UUID | None = None,
        model_id: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[CostRecord]:
        """Get cost records with optional filters.

        Args:
            task_id: Filter by task
            model_id: Filter by model
            since: Only records after this time
            limit: Maximum records to return

        Returns:
            Filtered list of records
        """
        records = self._records

        if task_id:
            records = [r for r in records if r.task_id == task_id]
        if model_id:
            records = [r for r in records if r.model_id == model_id]
        if since:
            records = [r for r in records if r.created_at >= since]

        # Sort by created_at descending and limit
        records = sorted(records, key=lambda r: r.created_at, reverse=True)
        return records[:limit]

    def clear_records(self, before: datetime | None = None) -> int:
        """Clear old records.

        Args:
            before: Clear records before this time (None = clear all)

        Returns:
            Number of records cleared
        """
        if before is None:
            count = len(self._records)
            self._records = []
            logger.info(f"Cleared all {count} cost records")
            return count

        old_count = len(self._records)
        self._records = [r for r in self._records if r.created_at >= before]
        cleared = old_count - len(self._records)
        logger.info(f"Cleared {cleared} cost records before {before}")
        return cleared


# Singleton instance
_default_tracker: CostTracker | None = None


def get_cost_tracker() -> CostTracker:
    """Get default cost tracker instance."""
    global _default_tracker
    if _default_tracker is None:
        _default_tracker = CostTracker()
    return _default_tracker
