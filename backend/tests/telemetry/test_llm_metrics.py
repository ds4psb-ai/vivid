"""Tests for LLM Metrics (Phase 5.5).

Tests cover:
- Token recording
- Latency tracking
- Error counting
- Summary statistics
"""
import pytest
from unittest.mock import patch, MagicMock

from app.telemetry.llm_metrics import (
    LLMMetrics,
    LLMCallRecord,
    get_llm_metrics,
)


class TestLLMCallRecord:
    """Tests for LLMCallRecord."""

    def test_record_creation(self):
        """Should create record with all fields."""
        record = LLMCallRecord(
            model="gemini-2.0-flash",
            input_tokens=100,
            output_tokens=50,
            latency_ms=150.5,
            success=True,
        )

        assert record.model == "gemini-2.0-flash"
        assert record.input_tokens == 100
        assert record.output_tokens == 50
        assert record.latency_ms == 150.5
        assert record.success is True
        assert record.timestamp is not None

    def test_record_with_error(self):
        """Should store error type."""
        record = LLMCallRecord(
            model="gemini-2.0-pro",
            input_tokens=100,
            output_tokens=0,
            latency_ms=50.0,
            success=False,
            error_type="rate_limit",
        )

        assert record.success is False
        assert record.error_type == "rate_limit"


class TestLLMMetrics:
    """Tests for LLMMetrics."""

    @pytest.fixture
    def metrics(self):
        return LLMMetrics()

    def test_record_tokens(self, metrics):
        """Should track token usage."""
        metrics.record_tokens(input_tokens=100, output_tokens=50, model="test")

        assert metrics._total_input_tokens == 100
        assert metrics._total_output_tokens == 50

    def test_record_multiple_tokens(self, metrics):
        """Should accumulate tokens."""
        metrics.record_tokens(100, 50)
        metrics.record_tokens(200, 100)

        assert metrics._total_input_tokens == 300
        assert metrics._total_output_tokens == 150

    def test_record_latency(self, metrics):
        """Should record latency."""
        # Just verify no errors - actual histogram recording is mocked
        metrics.record_latency(150.0, model="test")
        metrics.record_latency(200.0, model="test", operation="embed")

    def test_record_error(self, metrics):
        """Should count errors."""
        metrics.record_error("rate_limit", model="test")
        metrics.record_error("timeout", model="test")

        assert metrics._total_errors == 2

    def test_record_call_complete(self, metrics):
        """Should record complete call with all metrics."""
        metrics.record_call(
            model="gemini-2.0-flash",
            input_tokens=100,
            output_tokens=50,
            latency_ms=150.0,
            success=True,
        )

        assert metrics._total_calls == 1
        assert metrics._total_input_tokens == 100
        assert metrics._total_output_tokens == 50
        assert len(metrics._call_history) == 1

    def test_record_failed_call(self, metrics):
        """Should record failed call with error."""
        metrics.record_call(
            model="gemini-2.0-pro",
            input_tokens=100,
            output_tokens=0,
            latency_ms=50.0,
            success=False,
            error_type="api_error",
        )

        assert metrics._total_calls == 1
        assert metrics._total_errors == 1
        assert metrics._call_history[0].success is False
        assert metrics._call_history[0].error_type == "api_error"

    def test_history_limit(self, metrics):
        """Should limit history size."""
        metrics._max_history = 10

        for i in range(20):
            metrics.record_call(
                model="test",
                input_tokens=i,
                output_tokens=i,
                latency_ms=float(i),
                success=True,
            )

        assert len(metrics._call_history) == 10
        # Should keep last 10
        assert metrics._call_history[0].input_tokens == 10

    def test_get_summary(self, metrics):
        """Should return summary statistics."""
        # Record some calls
        for i in range(10):
            metrics.record_call(
                model="test",
                input_tokens=100,
                output_tokens=50,
                latency_ms=100.0 + i * 10,
                success=i != 5,  # One failure
                error_type="error" if i == 5 else None,
            )

        summary = metrics.get_summary()

        assert summary["total_calls"] == 10
        assert summary["total_errors"] == 1
        assert summary["total_input_tokens"] == 1000
        assert summary["total_output_tokens"] == 500
        assert summary["error_rate"] == 0.1
        assert summary["recent_calls"] == 10
        assert summary["recent_avg_latency_ms"] > 0

    def test_get_model_breakdown(self, metrics):
        """Should break down by model."""
        metrics.record_call("gemini-flash", 100, 50, 100.0, True)
        metrics.record_call("gemini-flash", 100, 50, 150.0, True)
        metrics.record_call("gemini-pro", 200, 100, 200.0, True)
        metrics.record_call("gemini-pro", 200, 100, 250.0, False, "error")

        breakdown = metrics.get_model_breakdown()

        assert "gemini-flash" in breakdown
        assert breakdown["gemini-flash"]["calls"] == 2
        assert breakdown["gemini-flash"]["errors"] == 0

        assert "gemini-pro" in breakdown
        assert breakdown["gemini-pro"]["calls"] == 2
        assert breakdown["gemini-pro"]["errors"] == 1
        assert breakdown["gemini-pro"]["error_rate"] == 0.5


class TestLLMMetricsTraceContext:
    """Tests for trace context manager."""

    @pytest.fixture
    def metrics(self):
        return LLMMetrics()

    def test_trace_llm_call_success(self, metrics):
        """Should trace successful call."""
        with metrics.trace_llm_call("test-model") as call_info:
            call_info["input_tokens"] = 100
            call_info["output_tokens"] = 50
            call_info["success"] = True

        assert metrics._total_calls == 1
        assert metrics._total_input_tokens == 100

    def test_trace_llm_call_failure(self, metrics):
        """Should handle exceptions in trace."""
        with pytest.raises(ValueError):
            with metrics.trace_llm_call("test-model") as call_info:
                call_info["input_tokens"] = 100
                raise ValueError("test error")

        # Should still record the call
        assert metrics._total_calls == 1
        assert metrics._total_errors == 1
        assert metrics._call_history[0].error_type == "ValueError"


class TestLLMMetricsSingleton:
    """Tests for singleton pattern."""

    def test_get_llm_metrics_returns_same_instance(self):
        """Should return same instance."""
        m1 = get_llm_metrics()
        m2 = get_llm_metrics()
        assert m1 is m2

    def test_singleton_persists_state(self):
        """Singleton should persist metrics."""
        metrics = get_llm_metrics()
        initial_calls = metrics._total_calls

        metrics.record_call("test", 100, 50, 100.0, True)

        metrics2 = get_llm_metrics()
        assert metrics2._total_calls == initial_calls + 1
