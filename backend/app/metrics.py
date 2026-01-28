"""Prometheus Metrics for DNA Lab and system monitoring.

Provides Prometheus-compatible metrics for:
- Drift Detection
- HITL Review workflow
- Transpiler performance
- Pipeline execution
- Request tracking

Usage:
    from app.metrics import record_drift_score, record_transpiler_call, get_metrics

    # Record metrics
    record_drift_score("bong", 0.15)
    record_transpiler_call("veo", 0.05)

    # Export metrics
    metrics_output = get_metrics()
"""
from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Callable, Optional

from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY

logger = logging.getLogger(__name__)


# =============================================================================
# DNA Lab Metrics
# =============================================================================

# Drift Detection
drift_detection_score = Gauge(
    "dna_lab_drift_detection_score",
    "Current drift score for auteur logic vectors",
    ["auteur_key"],
)

drift_detection_duration = Histogram(
    "dna_lab_drift_detection_duration_seconds",
    "Time spent on drift detection",
    ["auteur_key"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)

drift_detection_total = Counter(
    "dna_lab_drift_detection_total",
    "Total drift detection runs",
    ["auteur_key", "action"],
)

vector_version_created = Counter(
    "dna_lab_vector_version_created_total",
    "Number of logic vector versions created",
    ["auteur_key", "action"],
)

# HITL
hitl_review_pending = Gauge(
    "dna_lab_hitl_review_pending_count",
    "Number of pending HITL reviews",
    ["item_type"],
)

hitl_review_total = Counter(
    "dna_lab_hitl_review_total",
    "Total HITL reviews processed",
    ["item_type", "decision"],
)

hitl_review_duration = Histogram(
    "dna_lab_hitl_review_duration_seconds",
    "Time from queue to review completion",
    ["item_type", "decision"],
    buckets=[60, 300, 900, 1800, 3600, 7200, 14400, 28800, 86400],
)

# Transpiler
transpiler_latency = Histogram(
    "dna_lab_transpiler_latency_seconds",
    "Transpiler execution time by engine",
    ["engine"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
)

transpiler_total = Counter(
    "dna_lab_transpiler_total",
    "Total transpiler calls",
    ["engine", "status"],
)

transpiler_errors = Counter(
    "dna_lab_transpiler_errors_total",
    "Transpiler error count by engine",
    ["engine", "error_type"],
)

# Pipeline
pipeline_execution_duration = Histogram(
    "dna_lab_pipeline_duration_seconds",
    "Full pipeline execution time",
    ["status"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)

pipeline_step_duration = Histogram(
    "dna_lab_pipeline_step_duration_seconds",
    "Individual step execution time",
    ["step"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

pipeline_total = Counter(
    "dna_lab_pipeline_total",
    "Total pipeline executions",
    ["status"],
)

# =============================================================================
# System Metrics
# =============================================================================

request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["endpoint", "method", "status_code"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

request_total = Counter(
    "http_request_total",
    "Total HTTP requests",
    ["endpoint", "method", "status_code"],
)

error_total = Counter(
    "error_total",
    "Total errors by type and module",
    ["error_type", "module"],
)

# =============================================================================
# Helper Functions - DNA Lab
# =============================================================================

def record_drift_score(auteur_key: str, score: float) -> None:
    """Record drift detection score for an auteur.

    Args:
        auteur_key: Auteur identifier
        score: Drift score (0.0-1.0+)
    """
    drift_detection_score.labels(auteur_key=auteur_key).set(score)
    logger.debug(f"[METRICS] drift_score: auteur={auteur_key}, score={score:.3f}")


def record_drift_detection(
    auteur_key: str,
    action: str,
    duration_seconds: float,
) -> None:
    """Record drift detection run.

    Args:
        auteur_key: Auteur identifier
        action: Action taken (NO_CHANGE, AUTO_UPGRADE, REQUIRE_HUMAN_REVIEW)
        duration_seconds: Detection duration
    """
    drift_detection_total.labels(auteur_key=auteur_key, action=action).inc()
    drift_detection_duration.labels(auteur_key=auteur_key).observe(duration_seconds)
    logger.debug(
        f"[METRICS] drift_detection: auteur={auteur_key}, action={action}, "
        f"duration={duration_seconds:.2f}s"
    )


def record_vector_version(auteur_key: str, action: str) -> None:
    """Record vector version creation.

    Args:
        auteur_key: Auteur identifier
        action: Creation action (manual, auto_upgrade, hitl_approved)
    """
    vector_version_created.labels(auteur_key=auteur_key, action=action).inc()
    logger.debug(f"[METRICS] vector_version: auteur={auteur_key}, action={action}")


def record_hitl_pending(item_type: str, count: int) -> None:
    """Update pending HITL review count.

    Args:
        item_type: Type of review item
        count: Current pending count
    """
    hitl_review_pending.labels(item_type=item_type).set(count)
    logger.debug(f"[METRICS] hitl_pending: type={item_type}, count={count}")


def record_hitl_decision(
    item_type: str,
    decision: str,
    duration_seconds: float,
) -> None:
    """Record HITL review decision.

    Args:
        item_type: Type of review item
        decision: Decision made (approved, rejected, expired)
        duration_seconds: Time from queue to decision
    """
    hitl_review_total.labels(item_type=item_type, decision=decision).inc()
    hitl_review_duration.labels(item_type=item_type, decision=decision).observe(
        duration_seconds
    )
    logger.debug(
        f"[METRICS] hitl_decision: type={item_type}, decision={decision}, "
        f"duration={duration_seconds:.0f}s"
    )


def record_transpiler_call(
    engine: str,
    duration_seconds: float,
    status: str = "success",
) -> None:
    """Record transpiler execution.

    Args:
        engine: Target engine (veo, kling, sora)
        duration_seconds: Execution time
        status: Call status (success, error)
    """
    transpiler_latency.labels(engine=engine).observe(duration_seconds)
    transpiler_total.labels(engine=engine, status=status).inc()
    logger.debug(
        f"[METRICS] transpiler: engine={engine}, status={status}, "
        f"duration={duration_seconds:.3f}s"
    )


def record_transpiler_error(engine: str, error_type: str) -> None:
    """Record transpiler error.

    Args:
        engine: Target engine
        error_type: Type of error
    """
    transpiler_errors.labels(engine=engine, error_type=error_type).inc()
    logger.debug(f"[METRICS] transpiler_error: engine={engine}, type={error_type}")


def record_pipeline_execution(status: str, duration_seconds: float) -> None:
    """Record full pipeline execution.

    Args:
        status: Execution status (success, error, timeout)
        duration_seconds: Total execution time
    """
    pipeline_execution_duration.labels(status=status).observe(duration_seconds)
    pipeline_total.labels(status=status).inc()
    logger.debug(
        f"[METRICS] pipeline: status={status}, duration={duration_seconds:.2f}s"
    )


def record_pipeline_step(step: str, duration_seconds: float) -> None:
    """Record individual pipeline step execution.

    Args:
        step: Step name
        duration_seconds: Step execution time
    """
    pipeline_step_duration.labels(step=step).observe(duration_seconds)
    logger.debug(f"[METRICS] pipeline_step: step={step}, duration={duration_seconds:.2f}s")


# =============================================================================
# Helper Functions - System (Legacy API compatibility)
# =============================================================================

def record_analysis_complete(
    duration_seconds: float,
    status: str = "completed",
    pass_name: str = "total",
) -> None:
    """Record analysis completion metric (legacy compatibility).

    Args:
        duration_seconds: Analysis duration
        status: Completion status
        pass_name: Name of the pass
    """
    record_pipeline_step(pass_name, duration_seconds)
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
    """Record HTTP request metric.

    Args:
        endpoint: Request endpoint
        method: HTTP method
        status_code: Response status code
        duration_ms: Request duration in milliseconds
    """
    duration_seconds = duration_ms / 1000.0
    request_duration.labels(
        endpoint=endpoint, method=method, status_code=str(status_code)
    ).observe(duration_seconds)
    request_total.labels(
        endpoint=endpoint, method=method, status_code=str(status_code)
    ).inc()
    logger.debug(
        f"[METRICS] request: "
        f"endpoint={endpoint}, method={method}, status={status_code}, "
        f"duration={duration_ms:.0f}ms"
    )


def record_error(
    error_type: str,
    module: str = "unknown",
    message: Optional[str] = None,
) -> None:
    """Record error metric.

    Args:
        error_type: Type of error
        module: Module where error occurred
        message: Optional error message
    """
    error_total.labels(error_type=error_type, module=module).inc()
    logger.debug(f"[METRICS] error: type={error_type}, module={module}")


# =============================================================================
# Metrics Export
# =============================================================================

def get_metrics() -> bytes:
    """Generate Prometheus metrics output.

    Returns:
        Prometheus text format metrics
    """
    return generate_latest(REGISTRY)


# =============================================================================
# Decorators
# =============================================================================

def track_transpiler(engine: str) -> Callable:
    """Decorator to track transpiler execution.

    Args:
        engine: Target engine name

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                record_transpiler_call(engine, duration, "success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                record_transpiler_call(engine, duration, "error")
                record_transpiler_error(engine, type(e).__name__)
                raise
        return wrapper
    return decorator


def track_pipeline_step(step_name: str) -> Callable:
    """Decorator to track pipeline step execution.

    Args:
        step_name: Step name

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                record_pipeline_step(step_name, duration)
                return result
            except Exception:
                duration = time.time() - start_time
                record_pipeline_step(step_name, duration)
                raise
        return wrapper
    return decorator


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # DNA Lab metrics
    "record_drift_score",
    "record_drift_detection",
    "record_vector_version",
    "record_hitl_pending",
    "record_hitl_decision",
    "record_transpiler_call",
    "record_transpiler_error",
    "record_pipeline_execution",
    "record_pipeline_step",
    # Legacy API compatibility
    "record_analysis_complete",
    "record_request",
    "record_error",
    # Export
    "get_metrics",
    # Decorators
    "track_transpiler",
    "track_pipeline_step",
]
