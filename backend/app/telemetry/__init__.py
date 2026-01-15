"""
OpenTelemetry Integration Module (2026 Best Practices)
=====================================================

Provides comprehensive distributed tracing, metrics, and logging
following OpenTelemetry 2026 production standards.

Usage:
    from app.telemetry import setup_opentelemetry, get_tracer, get_meter

    # In main.py lifespan
    setup_opentelemetry(app, db_engine)

    # In service code
    tracer = get_tracer(__name__)
    with tracer.start_as_current_span("my_operation") as span:
        span.set_attribute("user.id", user_id)
        result = await do_work()
"""

from app.telemetry.otel_setup import (
    setup_opentelemetry,
    get_tracer,
    get_meter,
    create_span,
    record_exception,
    add_span_attributes,
)

__all__ = [
    "setup_opentelemetry",
    "get_tracer",
    "get_meter",
    "create_span",
    "record_exception",
    "add_span_attributes",
]
