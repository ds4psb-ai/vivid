"""
OpenTelemetry Setup (2026 Best Practices)
=========================================

Comprehensive OpenTelemetry configuration following 2026 production standards:
- BatchSpanProcessor for performance
- OTLP exporters (gRPC/HTTP) for Jaeger/Tempo
- Auto-instrumentation: FastAPI, SQLAlchemy, Redis, HTTPX
- Custom metrics for business KPIs
- Sampling strategies for production
- Context propagation for distributed tracing

References:
- https://opentelemetry.io/docs/languages/python/
- Context7 MCP research (2026-01-16)
"""

import os
import logging
from typing import Optional, Any
from contextlib import contextmanager
from functools import wraps

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider, SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased, ParentBased
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat

logger = logging.getLogger(__name__)

# Global instances
_tracer_provider: Optional[TracerProvider] = None
_meter_provider: Optional[MeterProvider] = None


def get_tracer(name: str = __name__) -> trace.Tracer:
    """Get a tracer instance for creating spans."""
    return trace.get_tracer(name)


def get_meter(name: str = __name__) -> metrics.Meter:
    """Get a meter instance for creating metrics."""
    return metrics.get_meter(name)


def create_span(name: str, attributes: Optional[dict] = None):
    """
    Decorator to create a span around a function.

    Usage:
        @create_span("process_order", {"order.type": "premium"})
        async def process_order(order_id: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__)
            with tracer.start_as_current_span(name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    record_exception(span, e)
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__)
            with tracer.start_as_current_span(name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    record_exception(span, e)
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def record_exception(span: Span, exception: Exception) -> None:
    """Record an exception on a span following 2026 best practices."""
    span.record_exception(exception)
    span.set_status(Status(StatusCode.ERROR, str(exception)))
    span.set_attribute("error.type", type(exception).__name__)
    span.set_attribute("error.message", str(exception))


def add_span_attributes(attributes: dict[str, Any]) -> None:
    """Add attributes to the current span."""
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(key, value)


def _create_resource(service_name: str, service_version: str, environment: str) -> Resource:
    """Create OpenTelemetry resource with service metadata."""
    return Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        "deployment.environment": environment,
        "telemetry.sdk.language": "python",
        "service.namespace": "vivid",
    })


def _create_sampler(sample_rate: float, environment: str) -> ParentBased:
    """
    Create a sampler following 2026 best practices.

    - Production: 10% sampling by default
    - Development: 100% sampling
    - Uses ParentBased to respect parent span decisions
    """
    if environment == "development":
        # Full sampling in development
        inner_sampler = TraceIdRatioBased(1.0)
    else:
        # Configurable sampling in production
        inner_sampler = TraceIdRatioBased(sample_rate)

    return ParentBased(root=inner_sampler)


def _setup_trace_exporter(endpoint: str, use_grpc: bool = True) -> SpanProcessor:
    """
    Configure OTLP span exporter.

    Supports both gRPC (default, better performance) and HTTP/protobuf.
    """
    try:
        if use_grpc:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        else:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")

        # Use BatchSpanProcessor for production (2026 best practice)
        return BatchSpanProcessor(
            exporter,
            max_queue_size=2048,
            max_export_batch_size=512,
            schedule_delay_millis=5000,
        )
    except Exception as e:
        logger.warning(f"Failed to create OTLP exporter: {e}")
        return None


def _setup_metrics_exporter(endpoint: str, use_grpc: bool = True) -> Optional[PeriodicExportingMetricReader]:
    """Configure OTLP metrics exporter."""
    try:
        if use_grpc:
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
            exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
        else:
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
            exporter = OTLPMetricExporter(endpoint=f"{endpoint}/v1/metrics")

        return PeriodicExportingMetricReader(
            exporter,
            export_interval_millis=60000,  # Export every 60 seconds
        )
    except Exception as e:
        logger.warning(f"Failed to create metrics exporter: {e}")
        return None


def _instrument_fastapi(app) -> bool:
    """Auto-instrument FastAPI application."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        # Exclude health check endpoints from tracing
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="health,health/live,health/ready,metrics",
        )
        logger.info("FastAPI instrumentation enabled")
        return True
    except ImportError:
        logger.warning("opentelemetry-instrumentation-fastapi not installed")
        return False


def _instrument_sqlalchemy(engine) -> bool:
    """Auto-instrument SQLAlchemy for database tracing."""
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument(
            engine=engine,
            enable_commenter=True,  # Add SQL comments with trace info
        )
        logger.info("SQLAlchemy instrumentation enabled")
        return True
    except ImportError:
        logger.warning("opentelemetry-instrumentation-sqlalchemy not installed")
        return False
    except Exception as e:
        logger.warning(f"SQLAlchemy instrumentation failed: {e}")
        return False


def _instrument_redis() -> bool:
    """Auto-instrument Redis for cache tracing."""
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        RedisInstrumentor().instrument()
        logger.info("Redis instrumentation enabled")
        return True
    except ImportError:
        logger.warning("opentelemetry-instrumentation-redis not installed")
        return False


def _instrument_httpx() -> bool:
    """Auto-instrument HTTPX for outgoing HTTP requests."""
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumentation enabled")
        return True
    except ImportError:
        logger.warning("opentelemetry-instrumentation-httpx not installed")
        return False


def _setup_custom_metrics(meter: metrics.Meter) -> dict:
    """
    Create custom business metrics for Vivid platform.

    Returns dict of metric instruments for use in application code.
    """
    return {
        # Request metrics
        "llm_requests": meter.create_counter(
            name="vivid.llm.requests",
            description="Number of LLM API requests",
            unit="1",
        ),
        "llm_tokens": meter.create_counter(
            name="vivid.llm.tokens",
            description="Total tokens consumed",
            unit="tokens",
        ),
        "llm_latency": meter.create_histogram(
            name="vivid.llm.latency",
            description="LLM request latency",
            unit="ms",
        ),
        # RAG metrics
        "rag_queries": meter.create_counter(
            name="vivid.rag.queries",
            description="Number of RAG queries",
            unit="1",
        ),
        "rag_latency": meter.create_histogram(
            name="vivid.rag.latency",
            description="RAG query latency",
            unit="ms",
        ),
        # UQSL metrics
        "uqsl_generations": meter.create_counter(
            name="vivid.uqsl.generations",
            description="Number of UQSL multi-generations",
            unit="1",
        ),
        "uqsl_quality_score": meter.create_histogram(
            name="vivid.uqsl.quality_score",
            description="UQSL quality scores distribution",
            unit="1",
        ),
        # Credit metrics
        "credits_consumed": meter.create_counter(
            name="vivid.credits.consumed",
            description="Total credits consumed",
            unit="credits",
        ),
        "credits_refunded": meter.create_counter(
            name="vivid.credits.refunded",
            description="Total credits refunded",
            unit="credits",
        ),
    }


def setup_opentelemetry(
    app,
    db_engine=None,
    service_name: str = "vivid-backend",
    service_version: str = "2.0.0",
) -> dict:
    """
    Initialize OpenTelemetry with 2026 best practices.

    Args:
        app: FastAPI application instance
        db_engine: SQLAlchemy engine for database tracing
        service_name: Service identifier
        service_version: Semantic version

    Returns:
        dict with initialization status and custom metrics

    Environment Variables:
        OTEL_ENABLED: Enable/disable OpenTelemetry (default: false)
        OTEL_EXPORTER_OTLP_ENDPOINT: OTLP collector endpoint (default: localhost:4317)
        OTEL_SAMPLE_RATE: Trace sampling rate (default: 0.1 for 10%)
        OTEL_USE_GRPC: Use gRPC instead of HTTP (default: true)
        ENVIRONMENT: deployment environment (development/staging/production)
    """
    global _tracer_provider, _meter_provider

    # Check if OpenTelemetry is enabled
    otel_enabled = os.getenv("OTEL_ENABLED", "false").lower() == "true"
    if not otel_enabled:
        logger.info("OpenTelemetry disabled (set OTEL_ENABLED=true to enable)")
        return {"enabled": False}

    # Configuration from environment
    environment = os.getenv("ENVIRONMENT", "development")
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
    sample_rate = float(os.getenv("OTEL_SAMPLE_RATE", "0.1"))
    use_grpc = os.getenv("OTEL_USE_GRPC", "true").lower() == "true"

    try:
        # Create resource
        resource = _create_resource(service_name, service_version, environment)

        # Create sampler
        sampler = _create_sampler(sample_rate, environment)

        # Setup TracerProvider
        _tracer_provider = TracerProvider(
            resource=resource,
            sampler=sampler,
        )

        # Add span processor with OTLP exporter
        span_processor = _setup_trace_exporter(otlp_endpoint, use_grpc)
        if span_processor:
            _tracer_provider.add_span_processor(span_processor)

        trace.set_tracer_provider(_tracer_provider)

        # Setup MeterProvider
        metric_reader = _setup_metrics_exporter(otlp_endpoint, use_grpc)
        if metric_reader:
            _meter_provider = MeterProvider(
                resource=resource,
                metric_readers=[metric_reader],
            )
            metrics.set_meter_provider(_meter_provider)

        # Setup B3 propagation for cross-service tracing
        set_global_textmap(B3MultiFormat())

        # Auto-instrumentation
        instrumentation_status = {
            "fastapi": _instrument_fastapi(app),
            "sqlalchemy": _instrument_sqlalchemy(db_engine) if db_engine else False,
            "redis": _instrument_redis(),
            "httpx": _instrument_httpx(),
        }

        # Create custom metrics
        meter = get_meter("vivid.metrics")
        custom_metrics = _setup_custom_metrics(meter)

        # Store metrics in app state for access in routes
        app.state.otel_metrics = custom_metrics

        logger.info(
            f"OpenTelemetry initialized",
            extra={
                "service_name": service_name,
                "environment": environment,
                "sample_rate": sample_rate,
                "otlp_endpoint": otlp_endpoint,
                "instrumentation": instrumentation_status,
            }
        )

        return {
            "enabled": True,
            "service_name": service_name,
            "environment": environment,
            "sample_rate": sample_rate,
            "instrumentation": instrumentation_status,
            "metrics": custom_metrics,
        }

    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        return {"enabled": False, "error": str(e)}


def shutdown_opentelemetry() -> None:
    """Gracefully shutdown OpenTelemetry providers."""
    global _tracer_provider, _meter_provider

    if _tracer_provider:
        _tracer_provider.shutdown()
        _tracer_provider = None

    if _meter_provider:
        _meter_provider.shutdown()
        _meter_provider = None

    logger.info("OpenTelemetry shutdown complete")
