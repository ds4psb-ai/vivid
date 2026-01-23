"""
Monitoring Integration Module

Provides Sentry error tracking and Prometheus metrics collection.
"""
from typing import Optional
from fastapi import FastAPI

from app.config import settings
from app.logging_config import get_logger

logger = get_logger("monitoring")


def setup_sentry(app: FastAPI) -> bool:
    """
    Initialize Sentry SDK for error tracking and performance monitoring.
    
    Returns True if Sentry was successfully initialized, False otherwise.
    """
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured, skipping initialization")
        return False
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.asyncio import AsyncioIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            integrations=[
                FastApiIntegration(
                    transaction_style="url",  # Use URL path as transaction name
                ),
                SqlalchemyIntegration(),
                AsyncioIntegration(),
                LoggingIntegration(
                    level=None,  # Don't capture logs as breadcrumbs
                    event_level=40,  # Capture ERROR level logs as events
                ),
            ],
            # Filter out health check endpoints from performance monitoring
            traces_sampler=lambda ctx: 0 if ctx.get("asgi_scope", {}).get("path", "").startswith("/health") else settings.SENTRY_TRACES_SAMPLE_RATE,
            # Don't send PII
            send_default_pii=False,
            # Release version
            release=f"{settings.PROJECT_NAME}@1.0.0",
        )
        
        logger.info(
            f"Sentry initialized",
            extra={
                "environment": settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT,
                "traces_sample_rate": settings.SENTRY_TRACES_SAMPLE_RATE,
            }
        )
        return True
        
    except ImportError:
        logger.warning("sentry-sdk not installed, skipping Sentry initialization")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def setup_prometheus(app: FastAPI) -> bool:
    """
    Configure Prometheus metrics collection with FastAPI instrumentator.
    
    Returns True if Prometheus was successfully initialized, False otherwise.
    """
    if not settings.PROMETHEUS_ENABLED:
        logger.info("Prometheus metrics disabled")
        return False
    
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        from prometheus_fastapi_instrumentator.metrics import (
            latency,
            requests,
            default,
        )
        
        # Create instrumentator
        instrumentator = Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            should_respect_env_var=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=["/metrics", "/health", "/health/live", "/health/ready"],
            env_var_name="ENABLE_METRICS",
            inprogress_name="http_requests_inprogress",
            inprogress_labels=True,
        )
        
        # Add default metrics
        instrumentator.add(
            latency(
                buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0],
            )
        )
        instrumentator.add(
            requests()
        )
        
        # Instrument the app
        instrumentator.instrument(app)
        
        # Expose metrics endpoint
        instrumentator.expose(
            app,
            endpoint=settings.PROMETHEUS_METRICS_PATH,
            include_in_schema=True,
            tags=["monitoring"],
        )
        
        logger.info(
            f"Prometheus metrics enabled",
            extra={
                "metrics_path": settings.PROMETHEUS_METRICS_PATH,
            }
        )
        return True
        
    except ImportError:
        logger.warning("prometheus-fastapi-instrumentator not installed, skipping Prometheus")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Prometheus: {e}")
        return False


def setup_monitoring(app: FastAPI) -> dict:
    """
    Initialize all monitoring integrations.

    Returns a dict with the status of each integration.
    """
    status = {
        "sentry": setup_sentry(app),
        "prometheus": setup_prometheus(app),
        "opentelemetry": setup_opentelemetry(app),
        "openllmetry": setup_openllmetry(app),
        "profiling": setup_profiling(app),
    }

    logger.info(
        "Monitoring setup complete",
        extra={"status": status}
    )

    return status


def setup_openllmetry(app: FastAPI) -> bool:
    """
    Initialize OpenLLMetry for GenAI observability (H3.1).

    Provides:
    - GenAI semantic conventions v1.38+
    - Automatic Gemini/Google GenAI instrumentation
    - LLM workflow/task tracing with @workflow/@task decorators

    Requires:
        OTEL_ENABLED=true
        OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
    """
    if not getattr(settings, "OTEL_ENABLED", False):
        logger.info("OpenLLMetry disabled (OTEL_ENABLED=false)")
        return False

    try:
        from traceloop.sdk import Traceloop

        otlp_endpoint = getattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT", None)

        # Initialize Traceloop SDK with OpenLLMetry
        Traceloop.init(
            app_name=getattr(settings, "OTEL_SERVICE_NAME", "vivid-backend"),
            disable_batch=settings.ENVIRONMENT in ("development", "local", "dev"),
            api_endpoint=otlp_endpoint if otlp_endpoint else None,
        )

        # Instrument Google Generative AI (Gemini)
        try:
            from opentelemetry.instrumentation.google_generativeai import GoogleGenerativeAIInstrumentor
            GoogleGenerativeAIInstrumentor().instrument()
            logger.info("Google GenerativeAI instrumentation enabled")
        except ImportError:
            logger.warning("opentelemetry-instrumentation-google-generativeai not installed")
        except Exception as e:
            logger.warning(f"Failed to instrument Google GenerativeAI: {e}")

        logger.info(
            "OpenLLMetry initialized with GenAI semantic conventions",
            extra={
                "app_name": getattr(settings, "OTEL_SERVICE_NAME", "vivid-backend"),
                "otlp_endpoint": otlp_endpoint,
                "environment": settings.ENVIRONMENT,
            }
        )
        return True

    except ImportError:
        logger.warning("traceloop-sdk not installed, skipping OpenLLMetry")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize OpenLLMetry: {e}")
        return False


def setup_opentelemetry(app: FastAPI) -> bool:
    """
    Configure OpenTelemetry for distributed tracing with B3 propagation.

    Features:
    - B3 multi-format propagation for cross-service tracing
    - OTLP export to collector/Jaeger
    - FastAPI and SQLAlchemy instrumentation

    Requires:
        OTEL_ENABLED=true
        OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
    """
    if not getattr(settings, "OTEL_ENABLED", False):
        logger.info("OpenTelemetry disabled")
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        # B3 Propagation for cross-service tracing (Zipkin/Jaeger compatible)
        try:
            from opentelemetry.propagate import set_global_textmap
            from opentelemetry.propagators.composite import CompositePropagator
            from opentelemetry.propagators.b3 import B3MultiFormat
            from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

            # Set composite propagator: W3C TraceContext + B3 Multi-format
            set_global_textmap(CompositePropagator([
                TraceContextTextMapPropagator(),  # W3C standard
                B3MultiFormat(),                   # Zipkin/Jaeger B3
            ]))
            logger.info("B3 multi-format propagation enabled")
        except ImportError:
            logger.warning("B3 propagator not available, using default propagation")

        # Create resource with service metadata
        resource = Resource.create({
            SERVICE_NAME: getattr(settings, "OTEL_SERVICE_NAME", settings.PROJECT_NAME),
            "deployment.environment": settings.ENVIRONMENT,
            "service.namespace": "vivid",
            "service.version": "1.0.0",
        })

        # Create tracer provider
        provider = TracerProvider(resource=resource)

        # Add OTLP exporter if configured
        otlp_endpoint = getattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT", None)
        if otlp_endpoint:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(f"OTLP exporter configured: {otlp_endpoint}")

        trace.set_tracer_provider(provider)

        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)

        # Instrument SQLAlchemy
        SQLAlchemyInstrumentor().instrument()

        # Try to instrument additional libraries
        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
            HTTPXClientInstrumentor().instrument()
            logger.info("HTTPX instrumentation enabled")
        except ImportError:
            pass

        try:
            from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
            AioHttpClientInstrumentor().instrument()
            logger.info("aiohttp client instrumentation enabled")
        except ImportError:
            pass

        logger.info(
            "OpenTelemetry tracing initialized",
            extra={
                "service_name": getattr(settings, "OTEL_SERVICE_NAME", settings.PROJECT_NAME),
                "otlp_endpoint": otlp_endpoint,
            }
        )
        return True

    except ImportError:
        logger.warning("OpenTelemetry packages not installed")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        return False


def setup_profiling(app: FastAPI) -> bool:
    """
    Add debug profiling endpoint (development only).
    
    GET /debug/profile - Returns slow query stats
    """
    if settings.ENVIRONMENT == "production":
        return False
    
    try:
        from fastapi import APIRouter
        from starlette.responses import JSONResponse
        import time
        
        profiling_router = APIRouter(prefix="/debug", tags=["debug"])
        
        # Store for slow requests
        slow_requests: list = []
        
        @profiling_router.get("/profile")
        async def get_profile_stats():
            """Get profiling statistics for debugging."""
            return JSONResponse({
                "slow_requests": slow_requests[-50:],  # Last 50
                "timestamp": time.time(),
                "environment": settings.ENVIRONMENT,
            })
        
        @profiling_router.get("/config")
        async def get_config():
            """Get non-sensitive configuration for debugging."""
            return JSONResponse({
                "environment": settings.ENVIRONMENT,
                "debug": getattr(settings, "DEBUG", False),
                "log_level": getattr(settings, "LOG_LEVEL", "INFO"),
                "sentry_enabled": bool(settings.SENTRY_DSN),
                "prometheus_enabled": getattr(settings, "PROMETHEUS_ENABLED", False),
            })
        
        app.include_router(profiling_router)
        logger.info("Debug profiling endpoints enabled")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup profiling: {e}")
        return False

