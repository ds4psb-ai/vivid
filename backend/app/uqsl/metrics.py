"""
UQSL Production Metrics Module

Prometheus + OpenTelemetry metrics for Universal Quality Selection Layer.

2026 Best Practices:
- Counter/Histogram for Prometheus metrics
- Structured logging for observability
- Fire-and-forget async recording
- Per-dimension/app_key labels for Grafana dashboards

Metrics:
- uqsl_generations_total: Total generation requests
- uqsl_generation_latency_ms: Generation latency histogram
- uqsl_candidates_generated: Candidates per request
- uqsl_quality_score: Quality score distribution
- uqsl_selections_total: Total selections (auto/hitl)
- uqsl_feedback_total: User feedback count
- uqsl_thompson_sampling_updates: Thompson Sampling arm updates
- uqsl_three_way_comparisons_total: Ensemble++ comparisons
- uqsl_errors_total: Error count by stage
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

# Prometheus metrics (enabled if prometheus-client installed)
_metrics_enabled = False
_generation_total: Optional[object] = None
_generation_latency: Optional[object] = None
_candidates_generated: Optional[object] = None
_quality_score: Optional[object] = None
_selections_total: Optional[object] = None
_feedback_total: Optional[object] = None
_ts_updates_total: Optional[object] = None
_three_way_total: Optional[object] = None
_errors_total: Optional[object] = None
_arm_success_rate: Optional[object] = None
_generation_in_progress: Optional[object] = None

try:
    from prometheus_client import Counter, Histogram, Gauge

    # Generation metrics
    _generation_total = Counter(
        "uqsl_generations_total",
        "Total UQSL generation requests",
        ["app_key", "strategy", "tier"]
    )

    _generation_latency = Histogram(
        "uqsl_generation_latency_ms",
        "UQSL generation latency in milliseconds",
        ["app_key", "n_candidates"],
        buckets=[100, 250, 500, 1000, 2500, 5000, 10000, 30000, 60000]
    )

    _candidates_generated = Histogram(
        "uqsl_candidates_generated",
        "Number of candidates generated per request",
        ["app_key"],
        buckets=[1, 2, 3, 4, 5]
    )

    _generation_in_progress = Gauge(
        "uqsl_generations_in_progress",
        "Number of UQSL generations currently in progress",
        ["app_key"]
    )

    # Quality metrics
    _quality_score = Histogram(
        "uqsl_quality_score",
        "Quality score distribution (weighted)",
        ["app_key", "metric_type"],
        buckets=[0.1, 0.3, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0]
    )

    # Selection metrics
    _selections_total = Counter(
        "uqsl_selections_total",
        "Total UQSL selections",
        ["app_key", "method", "selection_type"]  # auto/hitl
    )

    # Feedback metrics
    _feedback_total = Counter(
        "uqsl_feedback_total",
        "User feedback count",
        ["app_key", "feedback_type"]  # positive/negative
    )

    # Thompson Sampling metrics
    _ts_updates_total = Counter(
        "uqsl_thompson_sampling_updates_total",
        "Thompson Sampling arm updates",
        ["arm_id", "reward"]  # reward: true/false
    )

    _arm_success_rate = Gauge(
        "uqsl_arm_success_rate",
        "Thompson Sampling arm success rate (alpha / (alpha + beta))",
        ["arm_id"]
    )

    # Ensemble++ 3-way metrics
    _three_way_total = Counter(
        "uqsl_three_way_comparisons_total",
        "Ensemble++ 3-way comparison count",
        ["dimension", "recommended", "user_selected"]
    )

    # Error metrics
    _errors_total = Counter(
        "uqsl_errors_total",
        "UQSL error count",
        ["stage", "error_type", "app_key"]
    )

    _metrics_enabled = True
    logger.info("UQSL Prometheus metrics initialized")

except ImportError:
    logger.warning("prometheus-client not installed, UQSL metrics disabled")


# =============================================================================
# Metric Recording Functions
# =============================================================================

def record_generation(
    app_key: str,
    strategy: str,
    tier: str,
    n_candidates: int,
    latency_ms: float,
) -> None:
    """Record UQSL generation metrics.

    Args:
        app_key: Application key (e.g., "dimension.aesthetic")
        strategy: Selection strategy (auto/quality/confidence/random)
        tier: UQSL tier (free/premium/dev)
        n_candidates: Number of candidates generated
        latency_ms: Total generation latency
    """
    if _metrics_enabled:
        _generation_total.labels(
            app_key=app_key or "unknown",
            strategy=strategy or "auto",
            tier=tier or "free",
        ).inc()

        _generation_latency.labels(
            app_key=app_key or "unknown",
            n_candidates=str(n_candidates),
        ).observe(latency_ms)

        _candidates_generated.labels(
            app_key=app_key or "unknown",
        ).observe(n_candidates)

    logger.info(
        "UQSL generation completed",
        extra={
            "event_type": "uqsl.generation",
            "app_key": app_key,
            "strategy": strategy,
            "tier": tier,
            "n_candidates": n_candidates,
            "latency_ms": round(latency_ms, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


def record_quality_scores(
    app_key: str,
    groundedness: float,
    relevance: float,
    coherence: float,
    creativity: float,
    safety: float,
    weighted_score: float,
) -> None:
    """Record quality score distribution.

    Args:
        app_key: Application key
        groundedness: Groundedness score (0-1)
        relevance: Relevance score (0-1)
        coherence: Coherence score (0-1)
        creativity: Creativity score (0-1)
        safety: Safety score (0-1)
        weighted_score: Weighted total score (0-1)
    """
    if _metrics_enabled:
        _quality_score.labels(app_key=app_key, metric_type="groundedness").observe(groundedness)
        _quality_score.labels(app_key=app_key, metric_type="relevance").observe(relevance)
        _quality_score.labels(app_key=app_key, metric_type="coherence").observe(coherence)
        _quality_score.labels(app_key=app_key, metric_type="creativity").observe(creativity)
        _quality_score.labels(app_key=app_key, metric_type="safety").observe(safety)
        _quality_score.labels(app_key=app_key, metric_type="weighted").observe(weighted_score)


def record_selection(
    app_key: str,
    method: str,
    selection_type: str,  # "auto" or "hitl"
    selected_idx: int,
    confidence: float,
) -> None:
    """Record selection metrics.

    Args:
        app_key: Application key
        method: Selection method (quality/confidence/random)
        selection_type: "auto" or "hitl"
        selected_idx: Index of selected candidate
        confidence: Selection confidence
    """
    if _metrics_enabled:
        _selections_total.labels(
            app_key=app_key or "unknown",
            method=method or "auto",
            selection_type=selection_type,
        ).inc()

    logger.info(
        "UQSL selection recorded",
        extra={
            "event_type": "uqsl.selection",
            "app_key": app_key,
            "method": method,
            "selection_type": selection_type,
            "selected_idx": selected_idx,
            "confidence": round(confidence, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


def record_feedback(
    app_key: str,
    feedback_type: str,  # "positive" or "negative"
    selection_id: Optional[str] = None,
) -> None:
    """Record user feedback.

    Args:
        app_key: Application key
        feedback_type: "positive" or "negative"
        selection_id: Selection ID (optional)
    """
    if _metrics_enabled:
        _feedback_total.labels(
            app_key=app_key or "unknown",
            feedback_type=feedback_type,
        ).inc()

    logger.info(
        "UQSL feedback recorded",
        extra={
            "event_type": "uqsl.feedback",
            "app_key": app_key,
            "feedback_type": feedback_type,
            "selection_id": selection_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


def record_thompson_sampling_update(
    arm_id: str,
    reward: bool,
    alpha: int,
    beta: int,
) -> None:
    """Record Thompson Sampling arm update.

    Args:
        arm_id: Arm identifier (e.g., "backend:qdrant_hybrid")
        reward: Whether this was a positive reward
        alpha: Updated alpha parameter
        beta: Updated beta parameter
    """
    if _metrics_enabled:
        _ts_updates_total.labels(
            arm_id=arm_id,
            reward=str(reward).lower(),
        ).inc()

        # Update success rate gauge
        success_rate = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.5
        _arm_success_rate.labels(arm_id=arm_id).set(success_rate)

    logger.debug(
        "Thompson Sampling arm updated",
        extra={
            "event_type": "uqsl.ts_update",
            "arm_id": arm_id,
            "reward": reward,
            "alpha": alpha,
            "beta": beta,
            "success_rate": round(alpha / (alpha + beta), 3) if (alpha + beta) > 0 else 0.5,
        }
    )


def record_three_way_comparison(
    dimension: str,
    auteur_key: Optional[str],
    recommended: str,
    user_selected: Optional[str] = None,
    latency_ms: float = 0,
) -> None:
    """Record Ensemble++ 3-way comparison.

    Args:
        dimension: Dimension code (e.g., "AD")
        auteur_key: Auteur key (optional)
        recommended: Recommended option (a/b/ab)
        user_selected: User's selection (optional)
        latency_ms: Comparison latency
    """
    if _metrics_enabled:
        _three_way_total.labels(
            dimension=dimension or "unknown",
            recommended=recommended,
            user_selected=user_selected or "pending",
        ).inc()

    logger.info(
        "Ensemble++ 3-way comparison",
        extra={
            "event_type": "uqsl.three_way",
            "dimension": dimension,
            "auteur_key": auteur_key,
            "recommended": recommended,
            "user_selected": user_selected,
            "latency_ms": round(latency_ms, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


def record_error(
    stage: str,
    error_type: str,
    error_message: str,
    app_key: Optional[str] = None,
) -> None:
    """Record UQSL error.

    Args:
        stage: Error stage (generation/evaluation/selection/feedback)
        error_type: Error type name
        error_message: Error message (truncated)
        app_key: Application key (optional)
    """
    if _metrics_enabled:
        _errors_total.labels(
            stage=stage,
            error_type=error_type,
            app_key=app_key or "unknown",
        ).inc()

    logger.warning(
        "UQSL error",
        extra={
            "event_type": "uqsl.error",
            "stage": stage,
            "error_type": error_type,
            "error_message": error_message[:200] if error_message else "",
            "app_key": app_key,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


def set_generation_in_progress(app_key: str, delta: int = 1) -> None:
    """Update generation in progress gauge.

    Args:
        app_key: Application key
        delta: +1 to increment, -1 to decrement
    """
    if _metrics_enabled and _generation_in_progress:
        if delta > 0:
            _generation_in_progress.labels(app_key=app_key or "unknown").inc()
        else:
            _generation_in_progress.labels(app_key=app_key or "unknown").dec()


# =============================================================================
# Decorator for Automatic Tracking (2026 Best Practice)
# =============================================================================

T = TypeVar("T")


def track_uqsl_operation(operation_name: str) -> Callable:
    """UQSL operation tracking decorator.

    Automatically records latency and errors for UQSL operations.

    Usage:
        @track_uqsl_operation("quality_evaluation")
        async def evaluate_batch(candidates):
            ...

    Effects:
        - Records latency on success
        - Records error on failure
        - Logs operation completion
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.monotonic()
            app_key = kwargs.get("app_key", "unknown")

            try:
                result = await func(*args, **kwargs)
                latency_ms = (time.monotonic() - start) * 1000

                logger.debug(
                    f"[UQSL-Track] {operation_name} completed",
                    extra={
                        "operation": operation_name,
                        "latency_ms": round(latency_ms, 2),
                        "app_key": app_key,
                    }
                )
                return result

            except Exception as e:
                latency_ms = (time.monotonic() - start) * 1000
                record_error(
                    stage=operation_name,
                    error_type=type(e).__name__,
                    error_message=str(e)[:200],
                    app_key=app_key,
                )
                logger.warning(
                    f"[UQSL-Track] {operation_name} failed",
                    extra={
                        "operation": operation_name,
                        "error": type(e).__name__,
                        "latency_ms": round(latency_ms, 2),
                    }
                )
                raise

        return wrapper
    return decorator


# =============================================================================
# Health Check Helper
# =============================================================================

def get_uqsl_metrics_summary() -> dict:
    """Get UQSL metrics summary for health checks.

    Returns:
        Dictionary with metrics status and counts
    """
    return {
        "metrics_enabled": _metrics_enabled,
        "prometheus_available": _generation_total is not None,
    }


__all__ = [
    "record_generation",
    "record_quality_scores",
    "record_selection",
    "record_feedback",
    "record_thompson_sampling_update",
    "record_three_way_comparison",
    "record_error",
    "set_generation_in_progress",
    "track_uqsl_operation",
    "get_uqsl_metrics_summary",
]
