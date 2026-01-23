"""
P1.1 OpenTelemetry Tests
========================

Tests for OpenTelemetry integration following 2026 best practices.
Updated to match the current otel_setup module API.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os


class TestGetTracer:
    """Test tracer retrieval."""

    def test_get_tracer_returns_tracer(self):
        """Test get_tracer returns a tracer instance."""
        from app.telemetry.otel_setup import get_tracer

        tracer = get_tracer()
        assert tracer is not None

    def test_get_tracer_has_start_span(self):
        """Test tracer has start_as_current_span method."""
        from app.telemetry.otel_setup import get_tracer

        tracer = get_tracer()
        assert hasattr(tracer, "start_as_current_span")


class TestGetMeter:
    """Test meter retrieval."""

    def test_get_meter_returns_meter(self):
        """Test get_meter returns a meter instance."""
        from app.telemetry.otel_setup import get_meter

        meter = get_meter()
        assert meter is not None

    def test_get_meter_has_create_counter(self):
        """Test meter has create_counter method."""
        from app.telemetry.otel_setup import get_meter

        meter = get_meter()
        assert hasattr(meter, "create_counter")

    def test_get_meter_has_create_histogram(self):
        """Test meter has create_histogram method."""
        from app.telemetry.otel_setup import get_meter

        meter = get_meter()
        assert hasattr(meter, "create_histogram")


class TestSpanOperations:
    """Test span operations."""

    def test_tracer_creates_span(self):
        """Test tracer can create spans."""
        from app.telemetry.otel_setup import get_tracer

        tracer = get_tracer()
        with tracer.start_as_current_span("test_operation") as span:
            assert span is not None

    def test_span_set_attribute(self):
        """Test span can set attributes."""
        from app.telemetry.otel_setup import get_tracer

        tracer = get_tracer()
        with tracer.start_as_current_span("test_operation") as span:
            # Should not raise
            span.set_attribute("test.key", "test_value")
            span.set_attribute("test.number", 42)

    def test_span_add_event(self):
        """Test span can add events."""
        from app.telemetry.otel_setup import get_tracer

        tracer = get_tracer()
        with tracer.start_as_current_span("test_operation") as span:
            # Should not raise
            span.add_event("test_event", {"key": "value"})


class TestGetCurrentSpan:
    """Test getting current span."""

    def test_get_current_span_returns_span(self):
        """Test get_current_span returns a span."""
        from app.telemetry.otel_setup import get_tracer, get_current_span

        tracer = get_tracer()
        with tracer.start_as_current_span("test_operation"):
            span = get_current_span()
            assert span is not None


class TestSetupTelemetry:
    """Test telemetry setup function."""

    def test_setup_telemetry_returns_bool(self):
        """Test setup_telemetry returns a boolean."""
        from app.telemetry.otel_setup import setup_telemetry

        result = setup_telemetry(
            service_name="test-service",
            console_export=False,
        )

        assert isinstance(result, bool)

    def test_setup_telemetry_with_service_name(self):
        """Test setup with custom service name."""
        from app.telemetry.otel_setup import setup_telemetry

        # Should not raise
        result = setup_telemetry(
            service_name="custom-service",
            service_version="2.0.0",
        )
        assert isinstance(result, bool)


class TestShutdownTelemetry:
    """Test graceful shutdown."""

    def test_shutdown_does_not_raise(self):
        """Test shutdown handles case where providers may be None."""
        from app.telemetry.otel_setup import shutdown_telemetry

        # Should not raise
        shutdown_telemetry()


class TestNoOpImplementations:
    """Test no-op implementations when OpenTelemetry is unavailable."""

    def test_noop_span_context_manager(self):
        """Test NoOpSpan works as context manager."""
        from app.telemetry.otel_setup import NoOpSpan

        span = NoOpSpan()
        with span as s:
            s.set_attribute("key", "value")
            s.add_event("event")
            s.record_exception(ValueError("test"))

    def test_noop_tracer_creates_span(self):
        """Test NoOpTracer creates NoOpSpan."""
        from app.telemetry.otel_setup import NoOpTracer

        tracer = NoOpTracer()
        span = tracer.start_as_current_span("test")
        assert span is not None

    def test_noop_meter_creates_counter(self):
        """Test NoOpMeter creates counter."""
        from app.telemetry.otel_setup import NoOpMeter

        meter = NoOpMeter()
        counter = meter.create_counter("test_counter")
        # Should not raise
        counter.add(1)

    def test_noop_meter_creates_histogram(self):
        """Test NoOpMeter creates histogram."""
        from app.telemetry.otel_setup import NoOpMeter

        meter = NoOpMeter()
        histogram = meter.create_histogram("test_histogram")
        # Should not raise
        histogram.record(100)


class TestMeterOperations:
    """Test meter operations."""

    def test_create_counter(self):
        """Test meter can create counter."""
        from app.telemetry.otel_setup import get_meter

        meter = get_meter()
        counter = meter.create_counter(
            "test_counter",
            description="Test counter",
            unit="1",
        )
        assert counter is not None

    def test_create_histogram(self):
        """Test meter can create histogram."""
        from app.telemetry.otel_setup import get_meter

        meter = get_meter()
        histogram = meter.create_histogram(
            "test_histogram",
            description="Test histogram",
            unit="ms",
        )
        assert histogram is not None

    def test_counter_add(self):
        """Test counter add operation."""
        from app.telemetry.otel_setup import get_meter

        meter = get_meter()
        counter = meter.create_counter("test_counter")
        # Should not raise
        counter.add(1, {"dimension": "test"})

    def test_histogram_record(self):
        """Test histogram record operation."""
        from app.telemetry.otel_setup import get_meter

        meter = get_meter()
        histogram = meter.create_histogram("test_histogram")
        # Should not raise
        histogram.record(100, {"dimension": "test"})


class TestOtelAvailability:
    """Test OTEL_AVAILABLE flag handling."""

    def test_otel_available_is_boolean(self):
        """Test OTEL_AVAILABLE is a boolean."""
        from app.telemetry.otel_setup import OTEL_AVAILABLE

        assert isinstance(OTEL_AVAILABLE, bool)
