"""Qdrant Vector DB Tracing (P8: OpenTelemetry Integration).

Provides OpenTelemetry instrumentation for Qdrant operations:
- Search/query operations
- Index/upsert operations
- Collection management

Usage:
    from app.rag.qdrant_tracing import traced_qdrant_search, traced_qdrant_upsert

    # Wrap Qdrant operations
    with traced_qdrant_search("hybrid_search", dimension="4D", collection="dimension_4d_contexts"):
        results = await qdrant_client.search(...)

    # Or use decorator
    @trace_qdrant_operation("search")
    async def my_search_function(...):
        ...
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

from app.config import settings
from app.telemetry.otel_setup import get_tracer, OTEL_AVAILABLE

if OTEL_AVAILABLE:
    from opentelemetry.trace import Status, StatusCode, SpanKind
else:
    Status = None
    StatusCode = None
    SpanKind = None

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# Qdrant semantic conventions (custom, following OTel conventions)
QDRANT_SYSTEM = "qdrant"
QDRANT_OPERATION_KEY = "db.qdrant.operation"
QDRANT_COLLECTION_KEY = "db.qdrant.collection"
QDRANT_DIMENSION_KEY = "db.qdrant.dimension"
QDRANT_QUERY_LENGTH_KEY = "db.qdrant.query_length"
QDRANT_LIMIT_KEY = "db.qdrant.limit"
QDRANT_RESULTS_COUNT_KEY = "db.qdrant.results_count"
QDRANT_QUERY_TIME_MS_KEY = "db.qdrant.query_time_ms"
QDRANT_FILTERS_KEY = "db.qdrant.filters"
QDRANT_HYBRID_KEY = "db.qdrant.hybrid"
QDRANT_PREFETCH_LIMIT_KEY = "db.qdrant.prefetch_limit"


@contextmanager
def traced_qdrant_operation(
    operation: str,
    collection: str,
    dimension: Optional[str] = None,
    query_length: Optional[int] = None,
    limit: Optional[int] = None,
    is_hybrid: bool = False,
    filters: Optional[Dict[str, Any]] = None,
    prefetch_limit: Optional[int] = None,
):
    """Context manager for tracing Qdrant operations.

    Args:
        operation: Operation type (search, hybrid_search, upsert, delete)
        collection: Collection name
        dimension: Dimension ID (1D, 2D, ..., VEO)
        query_length: Length of query text
        limit: Result limit
        is_hybrid: Whether this is a hybrid (dense+sparse) search
        filters: Filter conditions applied
        prefetch_limit: Prefetch limit for hybrid search

    Yields:
        Span context for additional attribute setting

    Example:
        with traced_qdrant_operation("search", "dimension_4d_contexts", dimension="4D") as span:
            results = client.search(...)
            span.set_attribute("custom_key", "value")
    """
    tracer = get_tracer()
    span_name = f"qdrant.{operation}"
    span_kind = SpanKind.CLIENT if OTEL_AVAILABLE else None

    start_time = time.monotonic()

    with tracer.start_as_current_span(span_name, kind=span_kind) as span:
        # Set standard DB attributes
        if OTEL_AVAILABLE:
            span.set_attribute("db.system", QDRANT_SYSTEM)
            span.set_attribute(QDRANT_OPERATION_KEY, operation)
            span.set_attribute(QDRANT_COLLECTION_KEY, collection)

            if dimension:
                span.set_attribute(QDRANT_DIMENSION_KEY, dimension)
            if query_length is not None:
                span.set_attribute(QDRANT_QUERY_LENGTH_KEY, query_length)
            if limit is not None:
                span.set_attribute(QDRANT_LIMIT_KEY, limit)
            if is_hybrid:
                span.set_attribute(QDRANT_HYBRID_KEY, True)
            if prefetch_limit is not None:
                span.set_attribute(QDRANT_PREFETCH_LIMIT_KEY, prefetch_limit)
            if filters:
                # Store filter keys only (not values for security)
                span.set_attribute(QDRANT_FILTERS_KEY, ",".join(filters.keys()))

        try:
            yield span

            # Record success
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            if OTEL_AVAILABLE:
                span.set_attribute(QDRANT_QUERY_TIME_MS_KEY, elapsed_ms)
                span.set_status(Status(StatusCode.OK))

        except Exception as e:
            # Record failure
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            if OTEL_AVAILABLE:
                span.set_attribute(QDRANT_QUERY_TIME_MS_KEY, elapsed_ms)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e)[:500])
            raise


def set_results_count(span: Any, count: int) -> None:
    """Set the results count on a Qdrant span.

    Args:
        span: The span from traced_qdrant_operation
        count: Number of results returned
    """
    if OTEL_AVAILABLE and span:
        span.set_attribute(QDRANT_RESULTS_COUNT_KEY, count)


def trace_qdrant(
    operation: str,
    collection_arg: str = "collection_name",
    dimension_arg: str = "dimension",
    query_arg: str = "query",
    limit_arg: str = "limit",
):
    """Decorator for tracing Qdrant operations.

    Args:
        operation: Operation type (search, hybrid_search, upsert)
        collection_arg: Argument name for collection
        dimension_arg: Argument name for dimension
        query_arg: Argument name for query text
        limit_arg: Argument name for limit

    Example:
        @trace_qdrant("search")
        async def search(self, query: str, limit: int = 5):
            ...
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract parameters from args/kwargs
            # Handle both instance methods (self) and standalone functions
            collection = kwargs.get(collection_arg)
            dimension = kwargs.get(dimension_arg)
            query = kwargs.get(query_arg)
            limit = kwargs.get(limit_arg)

            # For instance methods, check self attributes
            if args and hasattr(args[0], "collection_name"):
                instance = args[0]
                if collection is None:
                    collection = getattr(instance, "collection_name", "unknown")
                if dimension is None:
                    dimension = getattr(instance, "dimension", None)

            query_length = len(query) if isinstance(query, str) else None
            is_hybrid = "hybrid" in operation.lower()

            with traced_qdrant_operation(
                operation=operation,
                collection=collection or "unknown",
                dimension=dimension,
                query_length=query_length,
                limit=limit,
                is_hybrid=is_hybrid,
            ) as span:
                result = await func(*args, **kwargs)

                # Set results count if result is a list
                if isinstance(result, list):
                    set_results_count(span, len(result))

                return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            collection = kwargs.get(collection_arg)
            dimension = kwargs.get(dimension_arg)
            query = kwargs.get(query_arg)
            limit = kwargs.get(limit_arg)

            if args and hasattr(args[0], "collection_name"):
                instance = args[0]
                if collection is None:
                    collection = getattr(instance, "collection_name", "unknown")
                if dimension is None:
                    dimension = getattr(instance, "dimension", None)

            query_length = len(query) if isinstance(query, str) else None
            is_hybrid = "hybrid" in operation.lower()

            with traced_qdrant_operation(
                operation=operation,
                collection=collection or "unknown",
                dimension=dimension,
                query_length=query_length,
                limit=limit,
                is_hybrid=is_hybrid,
            ) as span:
                result = func(*args, **kwargs)

                if isinstance(result, list):
                    set_results_count(span, len(result))

                return result

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Export for convenience
__all__ = [
    "traced_qdrant_operation",
    "set_results_count",
    "trace_qdrant",
    "QDRANT_SYSTEM",
    "QDRANT_OPERATION_KEY",
    "QDRANT_COLLECTION_KEY",
    "QDRANT_DIMENSION_KEY",
    "QDRANT_RESULTS_COUNT_KEY",
    "QDRANT_QUERY_TIME_MS_KEY",
]
