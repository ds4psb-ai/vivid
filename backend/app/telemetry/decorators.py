"""Tracing Decorators for OpenTelemetry instrumentation.

Provides decorators for easy span creation with automatic
attribute extraction and error handling.

2026 Best Practices:
- Semantic conventions for GenAI and RAG operations
- Automatic span attributes from function arguments
- Error recording with stack traces
- Context propagation

Usage:
    from app.telemetry.decorators import trace_operation, trace_rag_operation

    @trace_operation("my_service.process", {"operation.type": "batch"})
    async def process_batch(items: list) -> dict:
        # Automatically creates span with attributes
        pass

    @trace_rag_operation
    async def hybrid_query(query: str, dimension: str) -> Result:
        # Creates RAG-specific span with dimension, query attributes
        pass
"""
from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from app.telemetry.otel_setup import get_tracer, get_current_span, OTEL_AVAILABLE

if OTEL_AVAILABLE:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode, SpanKind
else:
    trace = None
    Status = None
    StatusCode = None
    SpanKind = None

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


# =============================================================================
# Core Decorator
# =============================================================================


def trace_operation(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    record_args: Optional[list[str]] = None,
    kind: Optional[Any] = None,
) -> Callable[[F], F]:
    """Decorator to trace a function with OpenTelemetry span.

    Args:
        name: Span name (e.g., "rag.hybrid_query", "service.process")
        attributes: Static attributes to add to span
        record_args: List of argument names to record as span attributes
        kind: Span kind (default: INTERNAL)

    Returns:
        Decorated function

    Example:
        @trace_operation(
            "rag.hybrid_query",
            {"rag.type": "hybrid"},
            record_args=["query", "dimension"],
        )
        async def hybrid_query(query: str, dimension: str) -> Result:
            pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer()
            span_kind = kind if kind else (SpanKind.INTERNAL if OTEL_AVAILABLE else None)

            with tracer.start_as_current_span(name, kind=span_kind) as span:
                # Add static attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Record specified arguments
                if record_args:
                    # Get function signature for positional args
                    import inspect
                    sig = inspect.signature(func)
                    params = list(sig.parameters.keys())

                    # Map positional args to names
                    bound_args = {}
                    for i, arg in enumerate(args):
                        if i < len(params):
                            bound_args[params[i]] = arg
                    bound_args.update(kwargs)

                    # Record requested args
                    for arg_name in record_args:
                        if arg_name in bound_args:
                            value = bound_args[arg_name]
                            # Truncate long strings
                            if isinstance(value, str) and len(value) > 500:
                                value = value[:500] + "..."
                            span.set_attribute(f"input.{arg_name}", str(value))

                start_time = time.perf_counter()

                try:
                    result = await func(*args, **kwargs)

                    # Record duration
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    span.set_attribute("duration_ms", duration_ms)

                    # Mark success
                    if OTEL_AVAILABLE:
                        span.set_status(Status(StatusCode.OK))

                    return result

                except Exception as e:
                    # Record error
                    if OTEL_AVAILABLE:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e)[:500])
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer()
            span_kind = kind if kind else (SpanKind.INTERNAL if OTEL_AVAILABLE else None)

            with tracer.start_as_current_span(name, kind=span_kind) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                start_time = time.perf_counter()

                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    span.set_attribute("duration_ms", duration_ms)
                    if OTEL_AVAILABLE:
                        span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    if OTEL_AVAILABLE:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


# =============================================================================
# RAG-Specific Decorator
# =============================================================================


def trace_rag_operation(
    name: Optional[str] = None,
    record_query: bool = True,
    record_dimension: bool = True,
    record_auteur: bool = True,
) -> Callable[[F], F]:
    """Decorator specifically for RAG operations with semantic conventions.

    Automatically extracts RAG-specific attributes:
    - rag.query: Search query
    - rag.dimension: Dimension code
    - rag.auteur_key: Auteur key if present
    - rag.strategy: Strategy used
    - rag.confidence: Result confidence
    - rag.results_count: Number of results

    Args:
        name: Optional span name (defaults to function name)
        record_query: Whether to record query attribute
        record_dimension: Whether to record dimension attribute
        record_auteur: Whether to record auteur_key attribute

    Returns:
        Decorated function

    Example:
        @trace_rag_operation
        async def hybrid_query(
            query: str,
            dimension: str = None,
            auteur_key: str = None,
        ) -> HybridRAGResult:
            pass
    """
    def decorator(func: F) -> F:
        span_name = name or f"rag.{func.__name__}"

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer()

            with tracer.start_as_current_span(
                span_name,
                kind=SpanKind.INTERNAL if OTEL_AVAILABLE else None,
            ) as span:
                # Set RAG semantic attributes
                span.set_attribute("rag.operation", func.__name__)

                # Extract known RAG arguments
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())

                bound_args = {}
                for i, arg in enumerate(args):
                    if i < len(params):
                        bound_args[params[i]] = arg
                bound_args.update(kwargs)

                # Record query
                if record_query and "query" in bound_args:
                    query = bound_args["query"]
                    if isinstance(query, str):
                        span.set_attribute("rag.query", query[:200])
                        span.set_attribute("rag.query_length", len(query))

                # Record dimension
                if record_dimension and "dimension" in bound_args:
                    dimension = bound_args.get("dimension")
                    if dimension:
                        span.set_attribute("rag.dimension", dimension)

                # Record auteur_key
                if record_auteur and "auteur_key" in bound_args:
                    auteur_key = bound_args.get("auteur_key")
                    if auteur_key:
                        span.set_attribute("rag.auteur_key", auteur_key)

                # Record strategy if present
                if "strategy" in bound_args:
                    span.set_attribute("rag.strategy", bound_args["strategy"])

                start_time = time.perf_counter()

                try:
                    result = await func(*args, **kwargs)

                    duration_ms = (time.perf_counter() - start_time) * 1000
                    span.set_attribute("duration_ms", duration_ms)

                    # Extract result attributes
                    if hasattr(result, "confidence"):
                        span.set_attribute("rag.confidence", result.confidence)
                    if hasattr(result, "retrieval_count"):
                        span.set_attribute("rag.results_count", result.retrieval_count)
                    if hasattr(result, "strategy_used"):
                        span.set_attribute("rag.strategy_used", result.strategy_used)
                    if hasattr(result, "grounded"):
                        span.set_attribute("rag.grounded", result.grounded)
                    if hasattr(result, "rrf_enabled"):
                        span.set_attribute("rag.rrf_enabled", result.rrf_enabled)
                    if hasattr(result, "query_time_ms"):
                        span.set_attribute("rag.query_time_ms", result.query_time_ms)

                    if OTEL_AVAILABLE:
                        span.set_status(Status(StatusCode.OK))

                    return result

                except Exception as e:
                    if OTEL_AVAILABLE:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                    span.set_attribute("error.type", type(e).__name__)
                    raise

        return wrapper  # type: ignore

    return decorator


# =============================================================================
# LLM-Specific Decorator (GenAI Semantic Conventions)
# =============================================================================


def trace_llm_operation(
    model: Optional[str] = None,
    operation_type: str = "chat",
) -> Callable[[F], F]:
    """Decorator for LLM operations with GenAI semantic conventions.

    Follows OpenTelemetry GenAI semantic conventions v1.38+:
    - gen_ai.system: "gemini"
    - gen_ai.request.model
    - gen_ai.response.model
    - gen_ai.usage.input_tokens
    - gen_ai.usage.output_tokens

    Args:
        model: Model name (extracted from kwargs if not provided)
        operation_type: "chat", "completion", "embedding"

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer()

            # Determine model name
            model_name = model or kwargs.get("model", "unknown")

            span_name = f"gen_ai.{operation_type}"

            with tracer.start_as_current_span(
                span_name,
                kind=SpanKind.CLIENT if OTEL_AVAILABLE else None,
            ) as span:
                # GenAI semantic attributes
                span.set_attribute("gen_ai.system", "gemini")
                span.set_attribute("gen_ai.operation.name", operation_type)
                span.set_attribute("gen_ai.request.model", model_name)

                # Extract temperature if present
                if "temperature" in kwargs:
                    span.set_attribute("gen_ai.request.temperature", kwargs["temperature"])

                start_time = time.perf_counter()

                try:
                    result = await func(*args, **kwargs)

                    duration_ms = (time.perf_counter() - start_time) * 1000
                    span.set_attribute("duration_ms", duration_ms)

                    # Extract token usage if available
                    if hasattr(result, "usage_metadata"):
                        usage = result.usage_metadata
                        if hasattr(usage, "prompt_token_count"):
                            span.set_attribute("gen_ai.usage.input_tokens", usage.prompt_token_count)
                        if hasattr(usage, "candidates_token_count"):
                            span.set_attribute("gen_ai.usage.output_tokens", usage.candidates_token_count)

                    if OTEL_AVAILABLE:
                        span.set_status(Status(StatusCode.OK))

                    return result

                except Exception as e:
                    if OTEL_AVAILABLE:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                    raise

        return wrapper  # type: ignore

    return decorator


# =============================================================================
# Utility Functions
# =============================================================================


def add_span_attributes(attributes: Dict[str, Any]) -> None:
    """Add attributes to the current span.

    Args:
        attributes: Dictionary of attributes to add
    """
    span = get_current_span()
    for key, value in attributes.items():
        span.set_attribute(key, value)


def add_span_event(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
) -> None:
    """Add an event to the current span.

    Args:
        name: Event name
        attributes: Optional event attributes
    """
    span = get_current_span()
    span.add_event(name, attributes=attributes)


def record_span_error(
    error: Exception,
    message: Optional[str] = None,
) -> None:
    """Record an error on the current span.

    Args:
        error: The exception
        message: Optional error message
    """
    span = get_current_span()
    if OTEL_AVAILABLE:
        span.set_status(Status(StatusCode.ERROR, message or str(error)))
        span.record_exception(error)
    span.set_attribute("error.type", type(error).__name__)
    span.set_attribute("error.message", str(error)[:500])


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "trace_operation",
    "trace_rag_operation",
    "trace_llm_operation",
    "add_span_attributes",
    "add_span_event",
    "record_span_error",
]
