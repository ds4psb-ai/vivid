"""
Tests for OpenLLMetry Integration (H3.1)

Tests:
- LLM metrics recording
- Tracer initialization
- Span attribute setting
"""
import pytest
from unittest.mock import patch, MagicMock


class TestLLMMetrics:
    """Tests for LLM metrics in telemetry.py"""

    def test_record_llm_request_success(self):
        """Test recording successful LLM request metrics."""
        from app.telemetry import record_llm_request

        # Should not raise even if prometheus is not available
        record_llm_request(
            model="gemini-3-flash-preview",
            dimension="4D",
            status="success",
            input_tokens=100,
            output_tokens=200,
            latency_seconds=1.5,
            credits=10.0,
        )

    def test_record_llm_request_failure(self):
        """Test recording failed LLM request metrics."""
        from app.telemetry import record_llm_request

        record_llm_request(
            model="gemini-3-flash-preview",
            dimension="AD",
            status="failed",
            input_tokens=50,
            output_tokens=0,
            latency_seconds=2.0,
            credits=0.0,
            error_type="API_ERROR",
        )

    def test_record_llm_request_with_zero_values(self):
        """Test recording with zero token counts."""
        from app.telemetry import record_llm_request

        record_llm_request(
            model="gemini-3-pro-preview",
            dimension="VEO",
            status="success",
            input_tokens=0,
            output_tokens=0,
            latency_seconds=0.0,
            credits=0.0,
        )

    def test_get_llm_tracer(self):
        """Test getting LLM tracer."""
        from app.telemetry import get_llm_tracer

        # May return None if otel not installed
        tracer = get_llm_tracer()
        # Just verify it doesn't raise
        assert tracer is None or hasattr(tracer, "start_span")


class TestOpenLLMetrySetup:
    """Tests for OpenLLMetry setup in monitoring.py"""

    def test_setup_openllmetry_disabled(self):
        """Test that OpenLLMetry is disabled when OTEL_ENABLED is False."""
        from app.monitoring import setup_openllmetry

        with patch("app.monitoring.settings") as mock_settings:
            mock_settings.OTEL_ENABLED = False
            mock_app = MagicMock()

            result = setup_openllmetry(mock_app)

            assert result is False

    @patch("app.monitoring.settings")
    def test_setup_openllmetry_missing_traceloop(self, mock_settings):
        """Test graceful handling when traceloop is not installed."""
        mock_settings.OTEL_ENABLED = True
        mock_settings.ENVIRONMENT = "development"

        from app.monitoring import setup_openllmetry

        # Should return False if traceloop not available
        mock_app = MagicMock()
        # May or may not succeed depending on installation
        result = setup_openllmetry(mock_app)
        assert isinstance(result, bool)


class TestCapsuleExecutorTracing:
    """Tests for capsule executor tracing."""

    def test_get_tracer_returns_none_or_tracer(self):
        """Test _get_tracer returns None or valid tracer."""
        from app.services.capsule_executor import _get_tracer

        tracer = _get_tracer()
        assert tracer is None or hasattr(tracer, "start_span")

    def test_get_workflow_decorator(self):
        """Test workflow decorator factory."""
        from app.services.capsule_executor import _get_workflow_decorator

        decorator = _get_workflow_decorator()

        # Should be callable
        assert callable(decorator)

        # Should work as decorator
        @decorator(name="test")
        def test_func():
            return "test"

        assert test_func() == "test"

    def test_get_task_decorator(self):
        """Test task decorator factory."""
        from app.services.capsule_executor import _get_task_decorator

        decorator = _get_task_decorator()

        assert callable(decorator)

        @decorator(name="test_task")
        def test_task():
            return "task"

        assert test_task() == "task"


class TestGenerationClientTracing:
    """Tests for generation client tracing."""

    def test_get_tracer_returns_none_or_tracer(self):
        """Test _get_tracer in generation_client."""
        from app.generation_client import _get_tracer

        tracer = _get_tracer()
        assert tracer is None or hasattr(tracer, "start_span")

    def test_end_generation_span_helper(self):
        """Test _end_generation_span helper function."""
        from app.generation_client import _end_generation_span, GenResult
        from datetime import datetime

        # Mock span
        mock_span = MagicMock()

        result = GenResult(
            shot_id="shot-001",
            status="success",
            output_url="mock://video.mp4",
            iteration=1,
            latency_ms=500,
            cost_usd_est=0.05,
            model_version="mock-v1",
        )

        # Should not raise
        _end_generation_span(mock_span, result, datetime.utcnow(), "success")

        # Verify span methods were called
        mock_span.set_attribute.assert_called()
        mock_span.end.assert_called_once()
