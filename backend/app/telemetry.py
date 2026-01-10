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


__all__ = [
    "setup_telemetry",
    "create_metrics_endpoint",
]
