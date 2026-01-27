"""
Telemetry Service (P1 Stub)

Provides OpenTelemetry tracing and metrics.

TODO (P2): Implement full OTel integration.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Generator, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Stub Tracer
# =============================================================================


class StubSpan:
    """Stub span for when OTel is not available."""

    def __init__(self, name: str):
        self.name = name

    def set_attribute(self, key: str, value: Any) -> None:
        """Set span attribute (no-op)."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class StubTracer:
    """Stub tracer for when OTel is not available."""

    @contextmanager
    def start_as_current_span(self, name: str, **kwargs) -> Generator[StubSpan, None, None]:
        """Start a stub span."""
        yield StubSpan(name)


def get_tracer(name: str = "default") -> StubTracer:
    """
    Get a tracer instance.

    P1 Stub: Returns stub tracer.
    P2 TODO: Return real OTel tracer.

    Args:
        name: Tracer name

    Returns:
        StubTracer
    """
    return StubTracer()


@contextmanager
def trace_span(name: str, **attributes) -> Generator[StubSpan, None, None]:
    """
    Context manager for tracing a span.

    P1 Stub: No-op.

    Args:
        name: Span name
        **attributes: Span attributes

    Yields:
        StubSpan
    """
    span = StubSpan(name)
    for key, value in attributes.items():
        span.set_attribute(key, value)
    yield span


# =============================================================================
# VDG Metrics
# =============================================================================


class VDGMetrics:
    """
    VDG pipeline metrics collector.

    P1 Stub: Logs metrics.
    P2 TODO: Export to Prometheus/OTel.
    """

    def __init__(self):
        self._success_count = 0
        self._failure_count = 0
        self._analysis_durations = {}

    def increment_success(self) -> None:
        """Increment success counter."""
        self._success_count += 1
        logger.debug(f"[VDG_METRICS] success_count={self._success_count}")

    def increment_failure(self, reason: str = "unknown") -> None:
        """Increment failure counter."""
        self._failure_count += 1
        logger.debug(f"[VDG_METRICS] failure_count={self._failure_count}, reason={reason}")

    def record_analysis_duration(self, pass_name: str, duration_seconds: float) -> None:
        """Record analysis pass duration."""
        if pass_name not in self._analysis_durations:
            self._analysis_durations[pass_name] = []
        self._analysis_durations[pass_name].append(duration_seconds)
        logger.debug(f"[VDG_METRICS] {pass_name}_duration={duration_seconds:.2f}s")

    def get_stats(self) -> dict:
        """Get current stats."""
        return {
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "analysis_durations": self._analysis_durations,
        }


# Singleton instance
vdg_metrics = VDGMetrics()


__all__ = [
    "get_tracer",
    "trace_span",
    "vdg_metrics",
    "VDGMetrics",
    "StubTracer",
    "StubSpan",
]
