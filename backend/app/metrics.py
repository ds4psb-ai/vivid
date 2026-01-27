"""
Application Metrics (P1 Stub)

Provides Prometheus-compatible metrics.

TODO (P2): Implement full Prometheus integration.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def record_analysis_complete(
    duration_seconds: float,
    status: str = "completed",
    pass_name: str = "total",
) -> None:
    """
    Record analysis completion metric.

    P1 Stub: Logs the metric.
    P2 TODO: Export to Prometheus.

    Args:
        duration_seconds: Analysis duration
        status: Completion status
        pass_name: Name of the pass
    """
    logger.debug(
        f"[METRICS] analysis_complete: "
        f"pass={pass_name}, status={status}, duration={duration_seconds:.2f}s"
    )


def record_request(
    endpoint: str,
    method: str = "POST",
    status_code: int = 200,
    duration_ms: float = 0.0,
) -> None:
    """
    Record HTTP request metric.

    P1 Stub: Logs the metric.

    Args:
        endpoint: Request endpoint
        method: HTTP method
        status_code: Response status code
        duration_ms: Request duration in milliseconds
    """
    logger.debug(
        f"[METRICS] request: "
        f"endpoint={endpoint}, method={method}, status={status_code}, duration={duration_ms:.0f}ms"
    )


def record_error(
    error_type: str,
    module: str = "unknown",
    message: Optional[str] = None,
) -> None:
    """
    Record error metric.

    P1 Stub: Logs the metric.

    Args:
        error_type: Type of error
        module: Module where error occurred
        message: Optional error message
    """
    logger.debug(f"[METRICS] error: type={error_type}, module={module}")


__all__ = [
    "record_analysis_complete",
    "record_request",
    "record_error",
]
