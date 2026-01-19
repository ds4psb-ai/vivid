"""OpenTelemetry setup for LLM observability (Phase 5.5).

2026 Best Practices:
- OpenTelemetry is the de facto standard for observability
- Distributed tracing across services
- Metrics for tokens, latency, errors

References:
- OpenTelemetry FastAPI: https://opentelemetry-python-contrib.readthedocs.io/
- FastAPI Observability: https://github.com/blueswen/fastapi-observability

Usage:
    from app.telemetry.otel_setup import setup_telemetry, get_tracer

    # At app startup
    setup_telemetry(
        service_name="vivid-backend",
        otlp_endpoint="http://localhost:4317",
    )

    # Create spans
    tracer = get_tracer()
    with tracer.start_as_current_span("my_operation") as span:
        span.set_attribute("key", "value")
        result = do_work()
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# OpenTelemetry imports (with graceful fallback)
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        PeriodicExportingMetricReader,
        ConsoleMetricExporter,
    )
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.warning(
        "OpenTelemetry not installed. Install with: "
        "pip install opentelemetry-api opentelemetry-sdk"
    )

# Global state
_tracer: Any = None
_meter: Any = None
_initialized = False


class NoOpSpan:
    """No-op span for when OpenTelemetry is not available."""

    def __enter__(self) -> "NoOpSpan":
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def set_status(self, status: Any) -> None:
        pass

    def record_exception(self, exception: Exception) -> None:
        pass

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        pass


class NoOpTracer:
    """No-op tracer for when OpenTelemetry is not available."""

    def start_as_current_span(self, name: str, **kwargs: Any) -> NoOpSpan:
        return NoOpSpan()

    def start_span(self, name: str, **kwargs: Any) -> NoOpSpan:
        return NoOpSpan()


class NoOpMeter:
    """No-op meter for when OpenTelemetry is not available."""

    def create_counter(self, name: str, **kwargs: Any) -> "NoOpCounter":
        return NoOpCounter()

    def create_histogram(self, name: str, **kwargs: Any) -> "NoOpHistogram":
        return NoOpHistogram()

    def create_up_down_counter(self, name: str, **kwargs: Any) -> "NoOpCounter":
        return NoOpCounter()


class NoOpCounter:
    """No-op counter."""

    def add(self, amount: int | float, attributes: dict[str, Any] | None = None) -> None:
        pass


class NoOpHistogram:
    """No-op histogram."""

    def record(self, amount: int | float, attributes: dict[str, Any] | None = None) -> None:
        pass


def setup_telemetry(
    service_name: str = "vivid-backend",
    service_version: str = "1.0.0",
    otlp_endpoint: str | None = None,
    console_export: bool = False,
) -> bool:
    """Initialize OpenTelemetry tracing and metrics.

    Args:
        service_name: Name of the service for resource identification
        service_version: Version of the service
        otlp_endpoint: OTLP collector endpoint (e.g., "http://localhost:4317")
        console_export: Export to console (for development)

    Returns:
        True if setup successful, False otherwise
    """
    global _tracer, _meter, _initialized

    if _initialized:
        logger.info("Telemetry already initialized")
        return True

    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available, using no-op implementations")
        _tracer = NoOpTracer()
        _meter = NoOpMeter()
        _initialized = True
        return False

    try:
        # Create resource with service info
        resource = Resource.create(
            {
                SERVICE_NAME: service_name,
                "service.version": service_version,
                "deployment.environment": os.getenv("ENVIRONMENT", "development"),
            }
        )

        # Setup tracing
        tracer_provider = TracerProvider(resource=resource)

        if console_export:
            tracer_provider.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )

        if otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter,
                )
                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            except ImportError:
                logger.warning("OTLP exporter not installed")

        trace.set_tracer_provider(tracer_provider)
        _tracer = trace.get_tracer(service_name, service_version)

        # Setup metrics
        metric_readers = []
        if console_export:
            metric_readers.append(
                PeriodicExportingMetricReader(ConsoleMetricExporter())
            )

        if metric_readers:
            meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
        else:
            meter_provider = MeterProvider(resource=resource)

        metrics.set_meter_provider(meter_provider)
        _meter = metrics.get_meter(service_name, service_version)

        _initialized = True
        logger.info(f"Telemetry initialized: service={service_name}")
        return True

    except Exception as e:
        logger.exception(f"Failed to initialize telemetry: {e}")
        _tracer = NoOpTracer()
        _meter = NoOpMeter()
        _initialized = True
        return False


def shutdown_telemetry() -> None:
    """Shutdown OpenTelemetry providers."""
    global _initialized

    if not OTEL_AVAILABLE or not _initialized:
        return

    try:
        tracer_provider = trace.get_tracer_provider()
        if hasattr(tracer_provider, "shutdown"):
            tracer_provider.shutdown()

        meter_provider = metrics.get_meter_provider()
        if hasattr(meter_provider, "shutdown"):
            meter_provider.shutdown()

        logger.info("Telemetry shutdown complete")
    except Exception as e:
        logger.exception(f"Error during telemetry shutdown: {e}")
    finally:
        _initialized = False


def get_tracer() -> Any:
    """Get the global tracer instance."""
    global _tracer
    if _tracer is None:
        setup_telemetry()
    return _tracer


def get_meter() -> Any:
    """Get the global meter instance."""
    global _meter
    if _meter is None:
        setup_telemetry()
    return _meter


def get_current_span() -> Any:
    """Get the current active span."""
    if not OTEL_AVAILABLE:
        return NoOpSpan()
    return trace.get_current_span()
