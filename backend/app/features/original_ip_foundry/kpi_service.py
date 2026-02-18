"""KPI aggregation service for Foundry operational metrics."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SlidingWindow:
    """Fixed-size sliding window for streaming percentile/mean computation."""

    max_size: int = 1000
    _values: deque = field(default_factory=lambda: deque(maxlen=1000))

    def __post_init__(self):
        self._values = deque(maxlen=self.max_size)

    def push(self, value: float) -> None:
        self._values.append(value)

    def percentile(self, p: float) -> Optional[float]:
        """Compute p-th percentile (0-100). Returns None if empty."""
        if not self._values:
            return None
        sorted_vals = sorted(self._values)
        n = len(sorted_vals)
        idx = (p / 100.0) * (n - 1)
        lower = int(idx)
        upper = min(lower + 1, n - 1)
        fraction = idx - lower
        return round(sorted_vals[lower] + fraction * (sorted_vals[upper] - sorted_vals[lower]), 2)

    def mean(self) -> Optional[float]:
        """Compute mean. Returns None if empty."""
        if not self._values:
            return None
        return round(sum(self._values) / len(self._values), 4)

    @property
    def count(self) -> int:
        return len(self._values)


CONTINUITY_BASELINE = 0.5


class FoundryKPIService:
    """Sliding-window KPI tracker for p95 latency, pattern reuse, and continuity."""

    def __init__(self, window_size: int = 1000):
        self._latency_window = SlidingWindow(max_size=window_size)
        self._continuity_scores = SlidingWindow(max_size=window_size)
        self._pattern_queries = SlidingWindow(max_size=window_size)

    def record_latency(self, latency_ms: float) -> None:
        """Record a request latency measurement."""
        self._latency_window.push(latency_ms)

    def record_continuity_score(self, score: float) -> None:
        """Record a scene continuity score."""
        self._continuity_scores.push(score)

    def record_pattern_reuse(self, reused: bool) -> None:
        """Record whether a pattern was reused (1.0) or new (0.0)."""
        self._pattern_queries.push(1.0 if reused else 0.0)

    ALERT_RULES = [
        {"rule": "p95_latency_breach", "threshold_ms": 2500, "metric": "p95"},
    ]

    def check_alerts(self) -> list[dict]:
        """Check all alert rules against current KPI snapshot."""
        alerts = []
        p95 = self._latency_window.percentile(95)
        if p95 is not None:
            for rule in self.ALERT_RULES:
                if rule["metric"] == "p95" and p95 > rule["threshold_ms"]:
                    alerts.append({
                        "rule": rule["rule"],
                        "threshold_ms": rule["threshold_ms"],
                        "actual_ms": p95,
                        "severity": "warning",
                    })
        return alerts

    def get_kpi_snapshot(self) -> dict:
        """Return current KPI snapshot with all tracked metrics."""
        mean_continuity = self._continuity_scores.mean()
        continuity_uplift = (
            round(mean_continuity - CONTINUITY_BASELINE, 4)
            if mean_continuity is not None
            else None
        )
        return {
            "p95_latency_ms": self._latency_window.percentile(95),
            "p50_latency_ms": self._latency_window.percentile(50),
            "pattern_reuse_rate": self._pattern_queries.mean(),
            "mean_continuity": mean_continuity,
            "continuity_uplift": continuity_uplift,
            "sample_counts": {
                "latency": self._latency_window.count,
                "continuity": self._continuity_scores.count,
                "pattern_queries": self._pattern_queries.count,
            },
        }
