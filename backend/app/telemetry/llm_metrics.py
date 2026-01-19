"""LLM-specific metrics for observability (Phase 5.5).

2026 Best Practices:
- Track tokens in/out for cost monitoring
- Record latency for performance SLOs
- Count errors by type for reliability tracking

References:
- Teknasyon Engineering: Building Observable LLM Agents
- Splunk: LLM Observability for cost control

Usage:
    from app.telemetry.llm_metrics import get_llm_metrics

    metrics = get_llm_metrics()

    # Record a complete LLM call
    metrics.record_call(
        model="gemini-2.0-flash",
        input_tokens=100,
        output_tokens=50,
        latency_ms=150,
        success=True,
    )

    # Or record individual metrics
    metrics.record_tokens(input_tokens=100, output_tokens=50, model="gemini-2.0-flash")
    metrics.record_latency(latency_ms=150, model="gemini-2.0-flash")
    metrics.record_error(error_type="rate_limit", model="gemini-2.0-flash")
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generator

from app.telemetry.otel_setup import get_meter, get_tracer

logger = logging.getLogger(__name__)


@dataclass
class LLMCallRecord:
    """Record of a single LLM API call."""

    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    success: bool
    error_type: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class LLMMetrics:
    """LLM-specific metrics collection.

    Tracks:
    - Token usage (input/output) per model
    - Latency distribution per model
    - Error counts by type
    - Cache hit rates
    """

    def __init__(self, service_name: str = "vivid-backend"):
        self.service_name = service_name
        self._meter = get_meter()
        self._tracer = get_tracer()

        # Initialize counters and histograms
        self._tokens_in = self._meter.create_counter(
            name="llm.tokens.input",
            description="Total input tokens processed",
            unit="tokens",
        )
        self._tokens_out = self._meter.create_counter(
            name="llm.tokens.output",
            description="Total output tokens generated",
            unit="tokens",
        )
        self._calls_total = self._meter.create_counter(
            name="llm.calls.total",
            description="Total LLM API calls",
            unit="calls",
        )
        self._errors_total = self._meter.create_counter(
            name="llm.errors.total",
            description="Total LLM API errors",
            unit="errors",
        )
        self._latency = self._meter.create_histogram(
            name="llm.latency",
            description="LLM API call latency",
            unit="ms",
        )
        self._cache_hits = self._meter.create_counter(
            name="llm.cache.hits",
            description="LLM cache hits",
            unit="hits",
        )
        self._cache_misses = self._meter.create_counter(
            name="llm.cache.misses",
            description="LLM cache misses",
            unit="misses",
        )

        # In-memory aggregates for quick access
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_calls = 0
        self._total_errors = 0
        self._call_history: list[LLMCallRecord] = []
        self._max_history = 1000  # Keep last 1000 calls

    def record_tokens(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "unknown",
    ) -> None:
        """Record token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model identifier
        """
        attributes = {"model": model}

        self._tokens_in.add(input_tokens, attributes)
        self._tokens_out.add(output_tokens, attributes)

        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens

    def record_latency(
        self,
        latency_ms: float,
        model: str = "unknown",
        operation: str = "generate",
    ) -> None:
        """Record call latency.

        Args:
            latency_ms: Latency in milliseconds
            model: Model identifier
            operation: Operation type (generate, embed, etc.)
        """
        attributes = {"model": model, "operation": operation}
        self._latency.record(latency_ms, attributes)

    def record_error(
        self,
        error_type: str,
        model: str = "unknown",
    ) -> None:
        """Record an error.

        Args:
            error_type: Type of error (rate_limit, timeout, api_error, etc.)
            model: Model identifier
        """
        attributes = {"model": model, "error_type": error_type}
        self._errors_total.add(1, attributes)
        self._total_errors += 1

    def record_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        success: bool,
        error_type: str | None = None,
        cache_hit: bool = False,
    ) -> None:
        """Record a complete LLM API call.

        Args:
            model: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            latency_ms: Call latency in milliseconds
            success: Whether the call succeeded
            error_type: Error type if failed
            cache_hit: Whether result was from cache
        """
        attributes = {"model": model}

        # Record call count
        self._calls_total.add(1, attributes)
        self._total_calls += 1

        # Record tokens
        self.record_tokens(input_tokens, output_tokens, model)

        # Record latency
        self.record_latency(latency_ms, model)

        # Record error if failed
        if not success and error_type:
            self.record_error(error_type, model)

        # Record cache
        if cache_hit:
            self._cache_hits.add(1, attributes)
        else:
            self._cache_misses.add(1, attributes)

        # Add to history
        record = LLMCallRecord(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=success,
            error_type=error_type,
        )
        self._call_history.append(record)

        # Trim history if needed
        if len(self._call_history) > self._max_history:
            self._call_history = self._call_history[-self._max_history :]

    @contextmanager
    def trace_llm_call(
        self,
        model: str,
        operation: str = "generate",
        **span_attributes: Any,
    ) -> Generator[dict[str, Any], None, None]:
        """Context manager for tracing an LLM call.

        Usage:
            with metrics.trace_llm_call("gemini-2.0-flash") as call_info:
                result = await llm.generate(prompt)
                call_info["input_tokens"] = result.input_tokens
                call_info["output_tokens"] = result.output_tokens
                call_info["success"] = True

        Args:
            model: Model identifier
            operation: Operation type
            **span_attributes: Additional span attributes

        Yields:
            Dict to populate with call results
        """
        call_info: dict[str, Any] = {
            "model": model,
            "input_tokens": 0,
            "output_tokens": 0,
            "success": True,
            "error_type": None,
            "cache_hit": False,
        }

        start_time = time.perf_counter()

        with self._tracer.start_as_current_span(
            f"llm.{operation}",
            attributes={"llm.model": model, **span_attributes},
        ) as span:
            try:
                yield call_info
            except Exception as e:
                call_info["success"] = False
                call_info["error_type"] = type(e).__name__
                span.record_exception(e)
                raise
            finally:
                latency_ms = (time.perf_counter() - start_time) * 1000

                # Set span attributes
                span.set_attribute("llm.tokens.input", call_info["input_tokens"])
                span.set_attribute("llm.tokens.output", call_info["output_tokens"])
                span.set_attribute("llm.latency_ms", latency_ms)
                span.set_attribute("llm.success", call_info["success"])
                span.set_attribute("llm.cache_hit", call_info["cache_hit"])

                # Record metrics
                self.record_call(
                    model=model,
                    input_tokens=call_info["input_tokens"],
                    output_tokens=call_info["output_tokens"],
                    latency_ms=latency_ms,
                    success=call_info["success"],
                    error_type=call_info["error_type"],
                    cache_hit=call_info["cache_hit"],
                )

    def get_summary(self) -> dict[str, Any]:
        """Get metrics summary.

        Returns:
            Summary dict with totals and recent stats
        """
        # Calculate recent stats (last 100 calls)
        recent = self._call_history[-100:] if self._call_history else []
        recent_latencies = [r.latency_ms for r in recent if r.success]

        return {
            "total_calls": self._total_calls,
            "total_errors": self._total_errors,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "error_rate": (
                self._total_errors / self._total_calls
                if self._total_calls > 0
                else 0.0
            ),
            "recent_calls": len(recent),
            "recent_avg_latency_ms": (
                sum(recent_latencies) / len(recent_latencies)
                if recent_latencies
                else 0.0
            ),
            "recent_p95_latency_ms": (
                sorted(recent_latencies)[int(len(recent_latencies) * 0.95)]
                if len(recent_latencies) >= 20
                else None
            ),
        }

    def get_model_breakdown(self) -> dict[str, dict[str, Any]]:
        """Get metrics broken down by model.

        Returns:
            Dict mapping model names to their metrics
        """
        breakdown: dict[str, dict[str, Any]] = {}

        for record in self._call_history:
            if record.model not in breakdown:
                breakdown[record.model] = {
                    "calls": 0,
                    "errors": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_latency_ms": 0.0,
                }

            stats = breakdown[record.model]
            stats["calls"] += 1
            stats["input_tokens"] += record.input_tokens
            stats["output_tokens"] += record.output_tokens
            stats["total_latency_ms"] += record.latency_ms

            if not record.success:
                stats["errors"] += 1

        # Calculate averages
        for model, stats in breakdown.items():
            if stats["calls"] > 0:
                stats["avg_latency_ms"] = stats["total_latency_ms"] / stats["calls"]
                stats["error_rate"] = stats["errors"] / stats["calls"]
            del stats["total_latency_ms"]

        return breakdown


# Singleton instance
_default_metrics: LLMMetrics | None = None


def get_llm_metrics() -> LLMMetrics:
    """Get default LLM metrics instance."""
    global _default_metrics
    if _default_metrics is None:
        _default_metrics = LLMMetrics()
    return _default_metrics
