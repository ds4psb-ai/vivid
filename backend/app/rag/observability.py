"""RAG Pipeline Observability with Langfuse + OpenTelemetry.

Phase 4: LLM tracing and monitoring for the hybrid RAG pipeline.
Provides decorators and utilities for tracking:
- Query execution (retrieval, generation, reranking)
- Latency and token usage
- Source attribution and scores

Dual Tracing:
- Langfuse: LLM-specific observability (prompts, tokens, generations)
- OpenTelemetry: Distributed tracing (spans, B3 propagation, Jaeger)

Usage:
    from app.rag.observability import trace_rag, get_langfuse

    @trace_rag(name="my_query")
    async def my_query_function(...):
        ...
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from contextlib import asynccontextmanager

from app.config import settings
from app.telemetry.otel_setup import get_tracer, OTEL_AVAILABLE

if OTEL_AVAILABLE:
    from opentelemetry.trace import Status, StatusCode, SpanKind
else:
    Status = None
    StatusCode = None
    SpanKind = None

logger = logging.getLogger(__name__)

# Type vars for decorator
F = TypeVar("F", bound=Callable[..., Any])

# Lazy-loaded Langfuse client
_langfuse = None
_langfuse_available = True


def _init_langfuse():
    """Initialize Langfuse client lazily."""
    global _langfuse, _langfuse_available
    
    if not settings.LANGFUSE_ENABLED:
        logger.debug("[Observability] Langfuse disabled via config")
        _langfuse_available = False
        return None
        
    if not settings.LANGFUSE_SECRET_KEY or not settings.LANGFUSE_PUBLIC_KEY:
        logger.warning(
            "[Observability] Langfuse keys not configured. "
            "Set LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY for tracing."
        )
        _langfuse_available = False
        return None
    
    try:
        from langfuse import Langfuse
        
        _langfuse = Langfuse(
            secret_key=settings.LANGFUSE_SECRET_KEY,
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            host=settings.LANGFUSE_HOST,
        )
        logger.info(f"[Observability] Langfuse initialized: {settings.LANGFUSE_HOST}")
        return _langfuse
    except ImportError:
        logger.warning(
            "[Observability] langfuse package not installed. "
            "Run: pip install langfuse"
        )
        _langfuse_available = False
        return None
    except Exception as e:
        logger.error(f"[Observability] Langfuse init failed: {e}")
        _langfuse_available = False
        return None


def get_langfuse():
    """Get the Langfuse client (lazy initialization)."""
    global _langfuse
    if _langfuse is None and _langfuse_available:
        _init_langfuse()
    return _langfuse


def trace_rag(
    name: str,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
):
    """
    Decorator to trace RAG operations with Langfuse + OpenTelemetry.

    Dual tracing:
    - Langfuse: LLM-specific observability (prompts, tokens, scores)
    - OpenTelemetry: Distributed tracing (spans, B3 propagation, Jaeger)

    Falls back to no-op if neither is configured.

    Args:
        name: Name of the operation (e.g., "hybrid_query", "rerank")
        metadata: Additional metadata to attach to trace
        tags: Tags for filtering in Langfuse dashboard

    Example:
        @trace_rag(name="hybrid_query", tags=["rag", "auteur"])
        async def hybrid_query(query: str, auteur_key: str = None):
            ...
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            langfuse = get_langfuse()
            tracer = get_tracer()

            # Extract query from args/kwargs for trace context
            query = kwargs.get("query") or (args[0] if args else "unknown")
            auteur_key = kwargs.get("auteur_key")
            dimension = kwargs.get("dimension")
            strategy = kwargs.get("strategy", "vector")

            start_time = time.monotonic()
            trace = None
            langfuse_span = None

            # OpenTelemetry span context
            otel_span_name = f"rag.{name}"
            span_kind = SpanKind.INTERNAL if OTEL_AVAILABLE else None

            # Start OpenTelemetry span
            with tracer.start_as_current_span(otel_span_name, kind=span_kind) as otel_span:
                # Set RAG semantic attributes
                if OTEL_AVAILABLE:
                    otel_span.set_attribute("rag.operation", name)
                    if isinstance(query, str):
                        otel_span.set_attribute("rag.query", query[:200])
                        otel_span.set_attribute("rag.query_length", len(query))
                    if auteur_key:
                        otel_span.set_attribute("rag.auteur_key", auteur_key)
                    if dimension:
                        otel_span.set_attribute("rag.dimension", dimension)
                    otel_span.set_attribute("rag.strategy", strategy)
                    if tags:
                        otel_span.set_attribute("rag.tags", ",".join(tags))

                try:
                    # Langfuse trace (if available)
                    if langfuse:
                        trace = langfuse.trace(
                            name=name,
                            input={"query": query, **{k: v for k, v in kwargs.items() if k != "query"}},
                            metadata={
                                **(metadata or {}),
                                "auteur_key": auteur_key,
                                "dimension": dimension,
                            },
                            tags=tags or ["rag"],
                        )
                        langfuse_span = trace.span(
                            name=f"{name}_execution",
                            input={"query": query},
                        )

                    # Execute the function
                    result = await func(*args, **kwargs)

                    # Calculate metrics
                    elapsed_ms = int((time.monotonic() - start_time) * 1000)

                    # Update OpenTelemetry span with result attributes
                    if OTEL_AVAILABLE:
                        otel_span.set_attribute("duration_ms", elapsed_ms)
                        if hasattr(result, "confidence"):
                            otel_span.set_attribute("rag.confidence", result.confidence)
                        if hasattr(result, "retrieval_count"):
                            otel_span.set_attribute("rag.results_count", result.retrieval_count)
                        if hasattr(result, "strategy_used"):
                            otel_span.set_attribute("rag.strategy_used", result.strategy_used)
                        if hasattr(result, "grounded"):
                            otel_span.set_attribute("rag.grounded", result.grounded)
                        if hasattr(result, "rrf_enabled"):
                            otel_span.set_attribute("rag.rrf_enabled", result.rrf_enabled)
                        if hasattr(result, "query_time_ms"):
                            otel_span.set_attribute("rag.query_time_ms", result.query_time_ms)
                        otel_span.set_status(Status(StatusCode.OK))

                    # Update Langfuse span with output
                    if langfuse_span:
                        output_data = {}
                        if hasattr(result, "__dict__"):
                            output_data = {
                                k: v for k, v in result.__dict__.items()
                                if not k.startswith("_") and not callable(v)
                            }
                        elif isinstance(result, dict):
                            output_data = result
                        else:
                            output_data = {"result": str(result)[:500]}

                        langfuse_span.end(
                            output=output_data,
                            metadata={"elapsed_ms": elapsed_ms},
                        )

                    # Score the Langfuse trace
                    if trace and hasattr(result, "confidence"):
                        trace.score(name="confidence", value=result.confidence)
                    if trace and hasattr(result, "retrieval_count"):
                        trace.score(name="retrieval_count", value=result.retrieval_count)

                    logger.debug(
                        f"[Observability] {name} traced | "
                        f"elapsed={elapsed_ms}ms | trace_id={trace.id if trace else 'N/A'}"
                    )

                    return result

                except Exception as e:
                    # Log error to OpenTelemetry span
                    if OTEL_AVAILABLE:
                        otel_span.set_status(Status(StatusCode.ERROR, str(e)))
                        otel_span.record_exception(e)
                    otel_span.set_attribute("error.type", type(e).__name__)
                    otel_span.set_attribute("error.message", str(e)[:500])

                    # Log error to Langfuse trace
                    if langfuse_span:
                        langfuse_span.end(level="ERROR", status_message=str(e))
                    if trace:
                        trace.update(metadata={"error": str(e)})
                    raise

                finally:
                    # Flush Langfuse traces (async-safe)
                    if langfuse:
                        try:
                            langfuse.flush()
                        except Exception:
                            pass

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Sync fallback (rarely used in RAG)
            langfuse = get_langfuse()
            tracer = get_tracer()

            if langfuse is None and not OTEL_AVAILABLE:
                return func(*args, **kwargs)

            start_time = time.monotonic()
            query = kwargs.get("query") or (args[0] if args else "unknown")

            otel_span_name = f"rag.{name}"
            span_kind = SpanKind.INTERNAL if OTEL_AVAILABLE else None

            with tracer.start_as_current_span(otel_span_name, kind=span_kind) as otel_span:
                if OTEL_AVAILABLE:
                    otel_span.set_attribute("rag.operation", name)
                    if isinstance(query, str):
                        otel_span.set_attribute("rag.query", query[:200])

                trace = None
                if langfuse:
                    trace = langfuse.trace(
                        name=name,
                        input={"query": query},
                        tags=tags or ["rag"],
                    )

                try:
                    result = func(*args, **kwargs)
                    elapsed_ms = int((time.monotonic() - start_time) * 1000)

                    if OTEL_AVAILABLE:
                        otel_span.set_attribute("duration_ms", elapsed_ms)
                        otel_span.set_status(Status(StatusCode.OK))

                    if trace:
                        trace.update(
                            output={"result": str(result)[:500]},
                            metadata={"elapsed_ms": elapsed_ms},
                        )
                    return result
                except Exception as e:
                    if OTEL_AVAILABLE:
                        otel_span.set_status(Status(StatusCode.ERROR, str(e)))
                        otel_span.record_exception(e)
                    if trace:
                        trace.update(metadata={"error": str(e)})
                    raise
                finally:
                    if langfuse:
                        langfuse.flush()

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


@asynccontextmanager
async def trace_retrieval(
    parent_trace,
    source_name: str,
    query: str,
):
    """
    Context manager for tracing individual retrieval steps.
    
    Usage:
        async with trace_retrieval(trace, "notebooklm", query) as span:
            result = await notebooklm_query(query)
            span.update(output={"sources": len(result.sources)})
    """
    if parent_trace is None:
        yield None
        return
    
    start_time = time.monotonic()
    span = parent_trace.span(
        name=f"retrieval_{source_name}",
        input={"query": query, "source": source_name},
    )
    
    try:
        yield span
    finally:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        span.end(metadata={"elapsed_ms": elapsed_ms})


def trace_generation(
    parent_trace,
    model: str,
    prompt: str,
    response: str,
    token_usage: Optional[Dict[str, int]] = None,
):
    """
    Log a generation event to the trace.
    
    Args:
        parent_trace: Parent Langfuse trace
        model: Model name (e.g., "gemini-2.0-flash")
        prompt: Input prompt
        response: Model response
        token_usage: Optional dict with input_tokens, output_tokens
    """
    if parent_trace is None:
        return
    
    parent_trace.generation(
        name="llm_generation",
        model=model,
        input=prompt[:2000],  # Truncate for dashboard
        output=response[:2000],
        usage=token_usage,
    )


# Export for convenience
__all__ = [
    "get_langfuse",
    "trace_rag",
    "trace_retrieval",
    "trace_generation",
]
