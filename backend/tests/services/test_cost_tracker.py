"""Tests for Cost Tracker service (Phase 5).

Tests cover:
- Cost recording
- Savings calculation
- Daily budget enforcement
- Cost summaries
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.cost_tracker import (
    CostRecord,
    CostTracker,
    DailyBudgetExceededError,
    get_cost_tracker,
)


# =============================================================================
# Cost Record Tests
# =============================================================================


class TestCostRecord:
    """Tests for CostRecord model."""

    def test_cost_record_creation(self):
        """Should create cost record with all fields."""
        record = CostRecord(
            task_id=uuid4(),
            model_id="gemini-2.0-flash",
            input_tokens=1000,
            output_tokens=500,
            estimated_cost_usd=0.015,
            actual_cost_usd=0.0003,
            savings_usd=0.0147,
        )

        assert record.model_id == "gemini-2.0-flash"
        assert record.input_tokens == 1000
        assert record.savings_usd == 0.0147
        assert record.created_at is not None

    def test_cost_record_default_timestamp(self):
        """Should auto-set created_at."""
        before = datetime.utcnow()
        record = CostRecord(
            task_id=uuid4(),
            model_id="gemini-2.0-flash",
            input_tokens=100,
            output_tokens=50,
            estimated_cost_usd=0.01,
            actual_cost_usd=0.001,
            savings_usd=0.009,
        )
        after = datetime.utcnow()

        assert before <= record.created_at <= after


# =============================================================================
# Cost Tracker Tests
# =============================================================================


class TestCostTracker:
    """Tests for CostTracker."""

    @pytest.fixture
    def tracker(self):
        return CostTracker()

    def test_record_cost_basic(self, tracker):
        """Should record cost and return record."""
        task_id = uuid4()
        record = tracker.record_cost(
            task_id=task_id,
            model_id="gemini-2.0-flash",
            input_tokens=1000,
            output_tokens=500,
            actual_cost=0.0003,
        )

        assert record.task_id == task_id
        assert record.model_id == "gemini-2.0-flash"
        assert record.actual_cost_usd == 0.0003

    def test_record_cost_calculates_savings(self, tracker):
        """Should calculate savings vs ULTRA baseline."""
        record = tracker.record_cost(
            task_id=uuid4(),
            model_id="gemini-2.0-flash",
            input_tokens=1000,
            output_tokens=500,
            actual_cost=0.0003,
        )

        # ULTRA would cost: (1000/1M * 5.00) + (500/1M * 15.00) = 0.0125
        expected_ultra = 0.0125
        assert record.estimated_cost_usd == pytest.approx(expected_ultra, abs=0.001)
        assert record.savings_usd == pytest.approx(expected_ultra - 0.0003, abs=0.001)

    def test_multiple_records_tracked(self, tracker):
        """Should track multiple cost records."""
        for i in range(5):
            tracker.record_cost(
                task_id=uuid4(),
                model_id="gemini-2.0-flash",
                input_tokens=1000,
                output_tokens=500,
                actual_cost=0.001 * (i + 1),
            )

        records = tracker.get_records()
        assert len(records) == 5


# =============================================================================
# Daily Budget Tests
# =============================================================================


class TestDailyBudget:
    """Tests for daily budget enforcement."""

    @pytest.fixture
    def tracker(self):
        return CostTracker()

    def test_set_daily_budget(self, tracker):
        """Should set daily budget."""
        tracker.set_daily_budget(10.0)

        status = tracker.get_daily_status()
        assert status["daily_budget"] == 10.0
        assert status["daily_spent"] == 0.0
        assert status["daily_remaining"] == 10.0

    def test_clear_daily_budget(self, tracker):
        """Should clear daily budget."""
        tracker.set_daily_budget(10.0)
        tracker.clear_daily_budget()

        status = tracker.get_daily_status()
        assert status["daily_budget"] is None

    def test_check_budget_no_budget(self, tracker):
        """Should allow any cost if no budget set."""
        allowed, message = tracker.check_budget(1000.0)
        assert allowed is True
        assert "No budget set" in message

    def test_check_budget_within_limit(self, tracker):
        """Should allow cost within budget."""
        tracker.set_daily_budget(10.0)

        allowed, message = tracker.check_budget(5.0)
        assert allowed is True
        assert "Within budget" in message

    def test_check_budget_exceeds_limit(self, tracker):
        """Should reject cost exceeding budget."""
        tracker.set_daily_budget(10.0)

        # Spend some
        tracker.record_cost(
            task_id=uuid4(),
            model_id="test",
            input_tokens=1000,
            output_tokens=500,
            actual_cost=8.0,
        )

        # Try to spend more than remaining
        allowed, message = tracker.check_budget(5.0)
        assert allowed is False
        assert "exceed" in message.lower()

    def test_enforce_budget_raises_error(self, tracker):
        """Should raise error when enforcing exceeded budget."""
        tracker.set_daily_budget(5.0)

        # Spend budget
        tracker.record_cost(
            task_id=uuid4(),
            model_id="test",
            input_tokens=1000,
            output_tokens=500,
            actual_cost=5.0,
        )

        # Try to enforce more spending
        with pytest.raises(DailyBudgetExceededError) as exc_info:
            tracker.enforce_budget(1.0)

        assert exc_info.value.daily_budget == 5.0
        assert exc_info.value.daily_spent == 5.0
        assert exc_info.value.estimated_cost == 1.0

    def test_budget_utilization_percentage(self, tracker):
        """Should calculate budget utilization percentage."""
        tracker.set_daily_budget(10.0)
        tracker.record_cost(
            task_id=uuid4(),
            model_id="test",
            input_tokens=1000,
            output_tokens=500,
            actual_cost=3.0,
        )

        status = tracker.get_daily_status()
        assert status["budget_utilization_pct"] == 30.0


# =============================================================================
# Cost Summary Tests
# =============================================================================


class TestCostSummary:
    """Tests for cost summary functionality."""

    @pytest.fixture
    def tracker_with_records(self):
        """Create tracker with sample records."""
        tracker = CostTracker()

        # Add records for different models
        for _ in range(3):
            tracker.record_cost(
                task_id=uuid4(),
                model_id="gemini-2.0-flash",
                input_tokens=1000,
                output_tokens=500,
                actual_cost=0.0003,
            )

        for _ in range(2):
            tracker.record_cost(
                task_id=uuid4(),
                model_id="gemini-2.0-pro",
                input_tokens=1000,
                output_tokens=500,
                actual_cost=0.003,
            )

        tracker.record_cost(
            task_id=uuid4(),
            model_id="gemini-2.0-ultra",
            input_tokens=1000,
            output_tokens=500,
            actual_cost=0.0125,
        )

        return tracker

    def test_summary_totals(self, tracker_with_records):
        """Should calculate correct totals."""
        summary = tracker_with_records.get_summary(days=7)

        # 3 * 0.0003 + 2 * 0.003 + 1 * 0.0125 = 0.0009 + 0.006 + 0.0125 = 0.0194
        expected_total = 0.0009 + 0.006 + 0.0125
        assert summary["total_cost_usd"] == pytest.approx(expected_total, abs=0.001)
        assert summary["record_count"] == 6

    def test_summary_by_model(self, tracker_with_records):
        """Should break down costs by model."""
        summary = tracker_with_records.get_summary(days=7)

        assert "gemini-2.0-flash" in summary["by_model"]
        assert "gemini-2.0-pro" in summary["by_model"]
        assert "gemini-2.0-ultra" in summary["by_model"]

        assert summary["by_model"]["gemini-2.0-flash"]["count"] == 3
        assert summary["by_model"]["gemini-2.0-pro"]["count"] == 2
        assert summary["by_model"]["gemini-2.0-ultra"]["count"] == 1

    def test_summary_savings_calculation(self, tracker_with_records):
        """Should calculate total savings correctly."""
        summary = tracker_with_records.get_summary(days=7)

        # All tasks were 1000 input + 500 output tokens
        # ULTRA baseline per task: 0.0125
        # Total ULTRA baseline: 6 * 0.0125 = 0.075
        # Total actual: ~0.0194
        # Total savings: ~0.075 - 0.0194 = ~0.0556

        assert summary["total_savings_usd"] > 0
        assert summary["savings_percentage"] > 0

    def test_summary_empty_period(self):
        """Should handle empty period gracefully."""
        tracker = CostTracker()
        summary = tracker.get_summary(days=7)

        assert summary["total_cost_usd"] == 0
        assert summary["record_count"] == 0


# =============================================================================
# Record Filtering Tests
# =============================================================================


class TestRecordFiltering:
    """Tests for record filtering."""

    @pytest.fixture
    def tracker_with_records(self):
        """Create tracker with varied records."""
        tracker = CostTracker()

        # Multiple records with different models
        task_id_1 = uuid4()
        task_id_2 = uuid4()

        tracker.record_cost(
            task_id=task_id_1,
            model_id="gemini-2.0-flash",
            input_tokens=1000,
            output_tokens=500,
            actual_cost=0.001,
        )
        tracker.record_cost(
            task_id=task_id_1,
            model_id="gemini-2.0-pro",
            input_tokens=2000,
            output_tokens=1000,
            actual_cost=0.01,
        )
        tracker.record_cost(
            task_id=task_id_2,
            model_id="gemini-2.0-flash",
            input_tokens=500,
            output_tokens=250,
            actual_cost=0.0005,
        )

        return tracker, task_id_1, task_id_2

    def test_filter_by_task_id(self, tracker_with_records):
        """Should filter records by task_id."""
        tracker, task_id_1, task_id_2 = tracker_with_records

        records = tracker.get_records(task_id=task_id_1)
        assert len(records) == 2
        assert all(r.task_id == task_id_1 for r in records)

    def test_filter_by_model_id(self, tracker_with_records):
        """Should filter records by model_id."""
        tracker, _, _ = tracker_with_records

        records = tracker.get_records(model_id="gemini-2.0-flash")
        assert len(records) == 2
        assert all(r.model_id == "gemini-2.0-flash" for r in records)

    def test_filter_with_limit(self, tracker_with_records):
        """Should limit number of records."""
        tracker, _, _ = tracker_with_records

        records = tracker.get_records(limit=1)
        assert len(records) == 1

    def test_records_sorted_by_date_descending(self, tracker_with_records):
        """Should return records newest first."""
        tracker, _, _ = tracker_with_records

        records = tracker.get_records()
        for i in range(len(records) - 1):
            assert records[i].created_at >= records[i + 1].created_at


# =============================================================================
# Clear Records Tests
# =============================================================================


class TestClearRecords:
    """Tests for clearing records."""

    def test_clear_all_records(self):
        """Should clear all records."""
        tracker = CostTracker()

        for i in range(5):
            tracker.record_cost(
                task_id=uuid4(),
                model_id="test",
                input_tokens=100,
                output_tokens=50,
                actual_cost=0.001,
            )

        count = tracker.clear_records()
        assert count == 5
        assert len(tracker.get_records()) == 0

    def test_clear_records_before_date(self):
        """Should clear records before specific date."""
        tracker = CostTracker()

        # Record some costs
        for i in range(3):
            tracker.record_cost(
                task_id=uuid4(),
                model_id="test",
                input_tokens=100,
                output_tokens=50,
                actual_cost=0.001,
            )

        # Clear records before now (should keep current records)
        future = datetime.utcnow() + timedelta(hours=1)
        count = tracker.clear_records(before=future)
        assert count == 3
        assert len(tracker.get_records()) == 0


# =============================================================================
# Singleton Tests
# =============================================================================


class TestCostTrackerSingleton:
    """Tests for singleton pattern."""

    def test_get_cost_tracker_returns_same_instance(self):
        """Should return same instance."""
        tracker1 = get_cost_tracker()
        tracker2 = get_cost_tracker()
        assert tracker1 is tracker2

    def test_singleton_persists_state(self):
        """Singleton should persist cost state."""
        tracker = get_cost_tracker()

        # Record a cost
        task_id = uuid4()
        tracker.record_cost(
            task_id=task_id,
            model_id="singleton-test",
            input_tokens=100,
            output_tokens=50,
            actual_cost=0.001,
        )

        # Get again and verify record exists
        tracker2 = get_cost_tracker()
        records = tracker2.get_records(model_id="singleton-test")
        assert len(records) >= 1


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_zero_tokens(self):
        """Should handle zero tokens."""
        tracker = CostTracker()
        record = tracker.record_cost(
            task_id=uuid4(),
            model_id="test",
            input_tokens=0,
            output_tokens=0,
            actual_cost=0.0,
        )
        assert record.actual_cost_usd == 0.0
        assert record.savings_usd == 0.0

    def test_large_token_counts(self):
        """Should handle large token counts."""
        tracker = CostTracker()
        record = tracker.record_cost(
            task_id=uuid4(),
            model_id="test",
            input_tokens=1_000_000,
            output_tokens=500_000,
            actual_cost=5.0,
        )
        assert record.input_tokens == 1_000_000
        assert record.output_tokens == 500_000

    def test_summary_with_no_tokens(self):
        """Should handle records with no tokens in summary."""
        tracker = CostTracker()
        tracker.record_cost(
            task_id=uuid4(),
            model_id="test",
            input_tokens=0,
            output_tokens=0,
            actual_cost=0.0,
        )

        summary = tracker.get_summary(days=7)
        assert summary["total_tokens"] == 0
        assert summary["cost_per_1k_tokens"] == 0
