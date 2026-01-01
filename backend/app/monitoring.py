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
                namespace="crebit",
            )
        )
        instrumentator.add(
            requests(
                namespace="crebit",
            )
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
    }
    
    logger.info(
        "Monitoring setup complete",
        extra={"status": status}
    )
    
    return status
