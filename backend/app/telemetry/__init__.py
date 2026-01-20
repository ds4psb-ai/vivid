"""Telemetry package for LLM observability (Phase 5.5).

Provides OpenTelemetry tracing, LLM metrics, and structured logging.

Usage:
    from app.telemetry import setup_telemetry, get_tracer, get_llm_metrics

    # Setup at app startup
    setup_telemetry(service_name="vivid-backend")

    # Create spans
    tracer = get_tracer()
    with tracer.start_as_current_span("llm_call") as span:
        span.set_attribute("model", "gemini-2.0-flash")
        result = await call_llm()

    # Record metrics
    metrics = get_llm_metrics()
    metrics.record_tokens(input_tokens=100, output_tokens=50)
"""
from app.telemetry.otel_setup import (
    get_tracer,
    get_meter,
    setup_telemetry,
    shutdown_telemetry,
)
from app.telemetry.llm_metrics import (
    LLMMetrics,
    get_llm_metrics,
    record_llm_request,
    get_llm_tracer,
)

__all__ = [
    "setup_telemetry",
    "shutdown_telemetry",
    "get_tracer",
    "get_meter",
    "LLMMetrics",
    "get_llm_metrics",
    # H3.1: Convenience functions
    "record_llm_request",
    "get_llm_tracer",
]
