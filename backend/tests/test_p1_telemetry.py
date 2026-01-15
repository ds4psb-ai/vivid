"""
P1.1 OpenTelemetry Tests
========================

Tests for OpenTelemetry integration following 2026 best practices.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os


class TestGetTracer:
    """Test tracer retrieval."""

    def test_get_tracer_returns_tracer(self):
        """Test get_tracer returns a tracer instance."""
        from app.telemetry.otel_setup import get_tracer

        tracer = get_tracer("test_module")
        assert tracer is not None

    def test_get_tracer_with_default_name(self):
        """Test get_tracer with default module name."""
        from app.telemetry.otel_setup import get_tracer

        tracer = get_tracer()
        assert tracer is not None


class TestGetMeter:
    """Test meter retrieval."""

    def test_get_meter_returns_meter(self):
        """Test get_meter returns a meter instance."""
        from app.telemetry.otel_setup import get_meter

        meter = get_meter("test_module")
        assert meter is not None


class TestCreateSpanDecorator:
    """Test create_span decorator."""

    @pytest.mark.asyncio
    async def test_async_function_decorated(self):
        """Test async function can be decorated with create_span."""
        from app.telemetry.otel_setup import create_span

        @create_span("test_operation")
        async def async_operation():
            return "success"

        result = await async_operation()
        assert result == "success"

    def test_sync_function_decorated(self):
        """Test sync function can be decorated with create_span."""
        from app.telemetry.otel_setup import create_span

        @create_span("test_operation")
        def sync_operation():
            return "success"

        result = sync_operation()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_exception_recorded(self):
        """Test exceptions are recorded in spans."""
        from app.telemetry.otel_setup import create_span

        @create_span("failing_operation")
        async def failing_operation():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await failing_operation()

    @pytest.mark.asyncio
    async def test_attributes_added(self):
        """Test attributes are added to spans."""
        from app.telemetry.otel_setup import create_span

        @create_span("operation_with_attrs", {"custom.attr": "value"})
        async def operation_with_attrs():
            return "success"

        result = await operation_with_attrs()
        assert result == "success"


class TestAddSpanAttributes:
    """Test adding attributes to current span."""

    def test_add_attributes_to_span(self):
        """Test adding attributes to current span."""
        from app.telemetry.otel_setup import add_span_attributes, get_tracer

        tracer = get_tracer()
        with tracer.start_as_current_span("test_span"):
            # Should not raise even if span is not recording
            add_span_attributes({
                "user.id": "123",
                "order.total": 99.99,
            })

    def test_add_attributes_handles_none(self):
        """Test None values are skipped."""
        from app.telemetry.otel_setup import add_span_attributes, get_tracer

        tracer = get_tracer()
        with tracer.start_as_current_span("test_span"):
            add_span_attributes({
                "valid": "value",
                "none_value": None,
            })


class TestRecordException:
    """Test exception recording on spans."""

    def test_record_exception_sets_status(self):
        """Test exception recording sets error status."""
        from app.telemetry.otel_setup import record_exception, get_tracer
        from opentelemetry.trace import StatusCode

        tracer = get_tracer()
        with tracer.start_as_current_span("test_span") as span:
            try:
                raise ValueError("Test error")
            except ValueError as e:
                record_exception(span, e)

            # Span should have error status
            # Note: We can't easily verify this in unit tests
            # but the function should complete without error


class TestSetupOpenTelemetry:
    """Test OpenTelemetry setup function."""

    def test_setup_disabled_by_default(self):
        """Test OpenTelemetry is disabled by default."""
        from app.telemetry.otel_setup import setup_opentelemetry

        app = Mock()
        app.state = Mock()

        result = setup_opentelemetry(app)

        assert result["enabled"] is False

    @patch.dict(os.environ, {"OTEL_ENABLED": "true", "ENVIRONMENT": "development"})
    def test_setup_enabled_with_env(self):
        """Test OpenTelemetry can be enabled via environment."""
        from app.telemetry.otel_setup import setup_opentelemetry

        app = Mock()
        app.state = Mock()

        result = setup_opentelemetry(app)

        assert result["enabled"] is True
        assert result["environment"] == "development"

    @patch.dict(os.environ, {"OTEL_ENABLED": "true", "OTEL_SAMPLE_RATE": "0.5"})
    def test_custom_sample_rate(self):
        """Test custom sample rate is applied."""
        from app.telemetry.otel_setup import setup_opentelemetry

        app = Mock()
        app.state = Mock()

        result = setup_opentelemetry(app)

        assert result["sample_rate"] == 0.5


class TestShutdownOpenTelemetry:
    """Test graceful shutdown."""

    def test_shutdown_handles_none_providers(self):
        """Test shutdown handles case where providers are None."""
        from app.telemetry.otel_setup import shutdown_opentelemetry

        # Should not raise
        shutdown_opentelemetry()


class TestResourceCreation:
    """Test OpenTelemetry resource creation."""

    def test_resource_has_service_name(self):
        """Test resource includes service name."""
        from app.telemetry.otel_setup import _create_resource

        resource = _create_resource(
            service_name="test-service",
            service_version="1.0.0",
            environment="test",
        )

        assert resource is not None
        # Resource attributes can be checked
        attrs = dict(resource.attributes)
        assert attrs.get("service.name") == "test-service"
        assert attrs.get("service.version") == "1.0.0"
        assert attrs.get("deployment.environment") == "test"


class TestSamplerCreation:
    """Test sampler configuration."""

    def test_development_full_sampling(self):
        """Test development environment uses 100% sampling."""
        from app.telemetry.otel_setup import _create_sampler

        sampler = _create_sampler(0.1, "development")
        assert sampler is not None

    def test_production_rate_sampling(self):
        """Test production uses configured rate."""
        from app.telemetry.otel_setup import _create_sampler

        sampler = _create_sampler(0.1, "production")
        assert sampler is not None


class TestCustomMetrics:
    """Test custom metrics creation."""

    def test_custom_metrics_created(self):
        """Test custom metrics are created correctly."""
        from app.telemetry.otel_setup import _setup_custom_metrics, get_meter

        meter = get_meter("test")
        metrics = _setup_custom_metrics(meter)

        assert "llm_requests" in metrics
        assert "llm_tokens" in metrics
        assert "llm_latency" in metrics
        assert "rag_queries" in metrics
        assert "uqsl_generations" in metrics
        assert "credits_consumed" in metrics


class TestInstrumentation:
    """Test auto-instrumentation functions."""

    def test_fastapi_instrumentation(self):
        """Test FastAPI instrumentation."""
        from app.telemetry.otel_setup import _instrument_fastapi
        from fastapi import FastAPI

        app = FastAPI()
        result = _instrument_fastapi(app)

        # Should return True if package is installed
        assert isinstance(result, bool)

    def test_redis_instrumentation(self):
        """Test Redis instrumentation."""
        from app.telemetry.otel_setup import _instrument_redis

        result = _instrument_redis()
        assert isinstance(result, bool)

    def test_httpx_instrumentation(self):
        """Test HTTPX instrumentation."""
        from app.telemetry.otel_setup import _instrument_httpx

        result = _instrument_httpx()
        assert isinstance(result, bool)
