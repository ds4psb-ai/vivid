"""
Telemetry Configuration - OpenTelemetry + Sentry

Provides distributed tracing, metrics, and error tracking for production.

Usage:
    from app.telemetry import setup_telemetry
    setup_telemetry(app)
"""
import os
import logging
from typing import Optional

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def setup_telemetry(app: FastAPI) -> None:
    """Configure OpenTelemetry and Sentry for the application.
    
    Environment Variables:
        OTEL_ENABLED: Enable OpenTelemetry (default: false)
        OTEL_EXPORTER_OTLP_ENDPOINT: OTLP collector endpoint
        SENTRY_DSN: Sentry DSN for error tracking
        ENVIRONMENT: Environment name (development, staging, production)
    """
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Setup Sentry for error tracking
    _setup_sentry(environment)
    
    # Setup OpenTelemetry for tracing and metrics
    if os.getenv("OTEL_ENABLED", "false").lower() == "true":
        _setup_opentelemetry(app, environment)


def _setup_sentry(environment: str) -> None:
    """Configure Sentry SDK for error tracking."""
    sentry_dsn = os.getenv("SENTRY_DSN")
    
    if not sentry_dsn:
        logger.info("Sentry DSN not configured, skipping Sentry setup")
        return
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            integrations=[
                FastApiIntegration(
                    transaction_style="endpoint",
                ),
                SqlalchemyIntegration(),
            ],
            # Capture 100% of transactions in development, 10% in production
            traces_sample_rate=1.0 if environment == "development" else 0.1,
            # Profile 100% of sampled transactions
            profiles_sample_rate=1.0 if environment == "development" else 0.1,
            # Send personal data (useful for debugging)
            send_default_pii=True if environment == "development" else False,
        )
        logger.info(f"Sentry initialized for {environment}")
        
    except ImportError:
        logger.warning("sentry-sdk not installed, skipping Sentry setup")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def _setup_opentelemetry(app: FastAPI, environment: str) -> None:
    """Configure OpenTelemetry for distributed tracing."""
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        
        # Check for OTLP endpoint
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        
        # Create resource with service info
        resource = Resource.create({
            SERVICE_NAME: "vivid-backend",
            "deployment.environment": environment,
            "service.version": os.getenv("APP_VERSION", "1.0.0"),
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Add OTLP exporter if endpoint configured
        if otlp_endpoint:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(f"OTLP exporter configured: {otlp_endpoint}")
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        
        # Instrument SQLAlchemy
        SQLAlchemyInstrumentor().instrument()
        
        # Instrument HTTPX for outgoing requests
        HTTPXClientInstrumentor().instrument()
        
        logger.info("OpenTelemetry initialized")
        
    except ImportError as e:
        logger.warning(f"OpenTelemetry packages not installed: {e}")
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")


# Prometheus metrics endpoint (optional)
def create_metrics_endpoint(app: FastAPI) -> None:
    """Add Prometheus metrics endpoint to the application."""
    try:
        from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
        from starlette.responses import Response
        
        # Custom metrics
        REQUEST_COUNT = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"]
        )
        
        REQUEST_LATENCY = Histogram(
            "http_request_duration_seconds",
            "HTTP request latency",
            ["method", "endpoint"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        CREDITS_DEDUCTED = Counter(
            "credits_deducted_total",
            "Total credits deducted",
            ["dimension", "model"]
        )
        
        AGENT_TOOL_CALLS = Counter(
            "agent_tool_calls_total",
            "Total agent tool invocations",
            ["tool_name", "status"]
        )
        
        @app.get("/metrics")
        async def metrics():
            """Prometheus metrics endpoint."""
            return Response(
                content=generate_latest(),
                media_type=CONTENT_TYPE_LATEST
            )
        
        logger.info("Prometheus metrics endpoint enabled at /metrics")
        
        # Store metrics in app state for access elsewhere
        app.state.metrics = {
            "request_count": REQUEST_COUNT,
            "request_latency": REQUEST_LATENCY,
            "credits_deducted": CREDITS_DEDUCTED,
            "agent_tool_calls": AGENT_TOOL_CALLS,
        }
        
    except ImportError:
        logger.info("prometheus-client not installed, metrics endpoint disabled")


# =============================================================================
# H3.1: GenAI-Specific Metrics (OpenLLMetry Integration)
# =============================================================================

# Lazy-loaded metrics (initialized on first use)
_llm_metrics_initialized = False
_LLM_REQUESTS = None
_LLM_TOKENS = None
_LLM_LATENCY = None
_LLM_COST = None
_LLM_ERRORS = None


def _init_llm_metrics():
    """Initialize LLM metrics lazily to avoid import issues."""
    global _llm_metrics_initialized, _LLM_REQUESTS, _LLM_TOKENS, _LLM_LATENCY, _LLM_COST, _LLM_ERRORS

    if _llm_metrics_initialized:
        return

    try:
        from prometheus_client import Counter, Histogram

        _LLM_REQUESTS = Counter(
            "vivid_llm_requests_total",
            "Total LLM API requests",
            ["model", "dimension", "status"]
        )

        _LLM_TOKENS = Counter(
            "vivid_llm_tokens_total",
            "Total LLM tokens used",
            ["model", "dimension", "type"]  # type: input/output
        )

        _LLM_LATENCY = Histogram(
            "vivid_llm_latency_seconds",
            "LLM request latency",
            ["model", "dimension"],
            buckets=[0.5, 1, 2, 5, 10, 30, 60, 120]
        )

        _LLM_COST = Counter(
            "vivid_llm_cost_credits",
            "LLM cost in credits",
            ["model", "dimension"]
        )

        _LLM_ERRORS = Counter(
            "vivid_llm_errors_total",
            "Total LLM API errors",
            ["model", "dimension", "error_type"]
        )

        _llm_metrics_initialized = True
        logger.info("LLM metrics initialized")

    except ImportError:
        logger.warning("prometheus-client not installed, LLM metrics disabled")


def record_llm_request(
    model: str,
    dimension: str,
    status: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    latency_seconds: float = 0.0,
    credits: float = 0.0,
    error_type: str = None,
):
    """
    Record LLM request metrics for observability (H3.1).

    Args:
        model: LLM model name (e.g., "gemini-3-flash-preview")
        dimension: Dimension app name (e.g., "4D", "AD", "VEO")
        status: Request status ("success", "failed", "timeout")
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        latency_seconds: Request latency in seconds
        credits: Credits charged for this request
        error_type: Error type if failed (optional)
    """
    _init_llm_metrics()

    if not _llm_metrics_initialized:
        return

    try:
        # Record request count
        _LLM_REQUESTS.labels(model=model, dimension=dimension, status=status).inc()

        # Record tokens
        if input_tokens > 0:
            _LLM_TOKENS.labels(model=model, dimension=dimension, type="input").inc(input_tokens)
        if output_tokens > 0:
            _LLM_TOKENS.labels(model=model, dimension=dimension, type="output").inc(output_tokens)

        # Record latency
        if latency_seconds > 0:
            _LLM_LATENCY.labels(model=model, dimension=dimension).observe(latency_seconds)

        # Record cost
        if credits > 0:
            _LLM_COST.labels(model=model, dimension=dimension).inc(credits)

        # Record errors
        if error_type and status in ("failed", "error"):
            _LLM_ERRORS.labels(model=model, dimension=dimension, error_type=error_type).inc()

    except Exception as e:
        logger.warning(f"Failed to record LLM metrics: {e}")


def get_llm_tracer():
    """
    Get OpenTelemetry tracer for LLM operations.

    Returns:
        Tracer instance for creating spans.
    """
    try:
        from opentelemetry import trace
        return trace.get_tracer("vivid.llm", "1.0.0")
    except ImportError:
        return None


__all__ = [
    "setup_telemetry",
    "create_metrics_endpoint",
    "record_llm_request",
    "get_llm_tracer",
]
