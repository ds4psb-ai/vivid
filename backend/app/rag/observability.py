"""RAG Pipeline Observability with Langfuse.

Phase 4: LLM tracing and monitoring for the hybrid RAG pipeline.
Provides decorators and utilities for tracking:
- Query execution (retrieval, generation, reranking)
- Latency and token usage
- Source attribution and scores

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
    Decorator to trace RAG operations with Langfuse.
    
    Falls back to no-op if Langfuse is not configured.
    
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
            
            if langfuse is None:
                # No-op: just execute the function
                return await func(*args, **kwargs)
            
            # Extract query from args/kwargs for trace context
            query = kwargs.get("query") or (args[0] if args else "unknown")
            
            start_time = time.monotonic()
            trace = None
            span = None
            
            try:
                # Create trace
                trace = langfuse.trace(
                    name=name,
                    input={"query": query, **kwargs},
                    metadata={
                        **(metadata or {}),
                        "auteur_key": kwargs.get("auteur_key"),
                        "dimension": kwargs.get("dimension"),
                    },
                    tags=tags or ["rag"],
                )
                
                # Create span for the operation
                span = trace.span(
                    name=f"{name}_execution",
                    input={"query": query},
                )
                
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Calculate metrics
                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                
                # Update span with output
                if span:
                    output_data = {}
                    if hasattr(result, "__dict__"):
                        # Dataclass or object with __dict__
                        output_data = {
                            k: v for k, v in result.__dict__.items()
                            if not k.startswith("_") and not callable(v)
                        }
                    elif isinstance(result, dict):
                        output_data = result
                    else:
                        output_data = {"result": str(result)[:500]}
                    
                    span.end(
                        output=output_data,
                        metadata={"elapsed_ms": elapsed_ms},
                    )
                
                # Score the trace
                if trace and hasattr(result, "confidence"):
                    trace.score(
                        name="confidence",
                        value=result.confidence,
                    )
                
                if trace and hasattr(result, "retrieval_count"):
                    trace.score(
                        name="retrieval_count",
                        value=result.retrieval_count,
                    )
                
                logger.debug(
                    f"[Observability] {name} traced | "
                    f"elapsed={elapsed_ms}ms | trace_id={trace.id if trace else 'N/A'}"
                )
                
                return result
                
            except Exception as e:
                # Log error to trace
                if span:
                    span.end(
                        level="ERROR",
                        status_message=str(e),
                    )
                if trace:
                    trace.update(
                        metadata={"error": str(e)},
                    )
                raise
            
            finally:
                # Flush traces (async-safe)
                if langfuse:
                    try:
                        langfuse.flush()
                    except Exception:
                        pass
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Sync fallback (rarely used in RAG)
            langfuse = get_langfuse()
            if langfuse is None:
                return func(*args, **kwargs)
            
            start_time = time.monotonic()
            query = kwargs.get("query") or (args[0] if args else "unknown")
            
            trace = langfuse.trace(
                name=name,
                input={"query": query},
                tags=tags or ["rag"],
            )
            
            try:
                result = func(*args, **kwargs)
                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                trace.update(
                    output={"result": str(result)[:500]},
                    metadata={"elapsed_ms": elapsed_ms},
                )
                return result
            except Exception as e:
                trace.update(metadata={"error": str(e)})
                raise
            finally:
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
