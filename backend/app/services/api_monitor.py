"""
API Monitoring Service - Cost Tracking and Cache Performance

Provides real-time monitoring for:
- Gemini API usage and costs
- Context cache hit rates
- Batch job performance
- Cost alerts and thresholds

References:
- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/docs/caching
"""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# Pricing Constants (USD per 1M tokens, as of 2025)
# =============================================================================

GEMINI_PRICING = {
    "gemini-3-flash-preview": {
        "input": 0.075,       # $0.075 per 1M input tokens
        "output": 0.30,       # $0.30 per 1M output tokens
        "cached_input": 0.01875,  # 75% discount on cached
        "cache_storage": 1.00,    # $1.00 per 1M tokens per hour
    },
    "gemini-2.5-pro": {
        "input": 1.25,
        "output": 10.00,
        "cached_input": 0.3125,
        "cache_storage": 4.50,
    },
}

BATCH_DISCOUNT = 0.50  # 50% discount for batch API


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class UsageMetrics:
    """Metrics for a single API call."""
    timestamp: datetime
    model: str
    prompt_tokens: int = 0
    cached_tokens: int = 0
    output_tokens: int = 0
    cache_hit_rate: float = 0.0
    is_batch: bool = False
    latency_ms: float = 0.0
    
    @property
    def estimated_cost_usd(self) -> float:
        """Calculate estimated cost in USD."""
        pricing = GEMINI_PRICING.get(self.model, GEMINI_PRICING["gemini-3-flash-preview"])
        
        # Calculate non-cached input tokens
        non_cached_input = max(0, self.prompt_tokens - self.cached_tokens)
        
        # Input cost (cached vs non-cached)
        input_cost = (non_cached_input / 1_000_000) * pricing["input"]
        cached_cost = (self.cached_tokens / 1_000_000) * pricing["cached_input"]
        output_cost = (self.output_tokens / 1_000_000) * pricing["output"]
        
        total = input_cost + cached_cost + output_cost
        
        # Apply batch discount if applicable
        if self.is_batch:
            total *= (1 - BATCH_DISCOUNT)
        
        return total


@dataclass
class AggregatedStats:
    """Aggregated statistics over a time period."""
    period_start: datetime
    period_end: datetime
    total_calls: int = 0
    total_prompt_tokens: int = 0
    total_cached_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_cache_hit_rate: float = 0.0
    avg_latency_ms: float = 0.0
    batch_calls: int = 0
    cache_savings_usd: float = 0.0


@dataclass 
class Alert:
    """System alert for cost or performance issues."""
    timestamp: datetime
    level: AlertLevel
    message: str
    metric_name: str
    current_value: float
    threshold: float
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# API Monitor Service
# =============================================================================

class APIMonitor:
    """
    Centralized API monitoring and cost tracking.
    
    Features:
    - Real-time usage tracking
    - Cost estimation
    - Cache hit rate monitoring
    - Threshold-based alerts
    - Aggregated statistics
    
    Thresholds are based on production best practices:
    - Cache hit rate: Research shows 68.8% optimal for semantic caching (arxiv),
      50% is reasonable minimum for explicit system prompt caching
    - Cost alerts: Industry standard 50%/70%/90% tiered warnings
    
    Usage:
        monitor = APIMonitor.get_instance()
        monitor.record_usage(metrics)
        stats = monitor.get_stats(period="1h")
    """
    
    _instance: Optional["APIMonitor"] = None
    _lock = threading.Lock()
    
    # ==========================================================================
    # Research-Based Thresholds
    # ==========================================================================
    
    # Cache hit rate thresholds
    # - Gemini explicit caching should achieve 60-80% on stable system prompts
    # - Below 50% indicates cache refresh issues or prompt instability
    # - Semantic caching research (arxiv) shows 68.8% optimal at 0.8 similarity
    CACHE_HIT_RATE_CRITICAL = 0.20  # Critical: cache likely broken
    CACHE_HIT_RATE_WARNING = 0.50   # Warning: investigate cache config
    CACHE_HIT_RATE_OPTIMAL = 0.65   # Target: good cache performance
    
    # Minimum tokens for cache hit rate alerts (avoid false positives on small requests)
    # Gemini Flash requires 1024 tokens minimum for caching benefits
    MIN_TOKENS_FOR_CACHE_ALERT = 1024
    
    # Cost alert thresholds (tiered 50%/70%/90% of budget)
    # Adjust these based on your monthly budget
    DAILY_BUDGET_USD = 10.0           # $10/day default budget
    HOURLY_COST_INFO = DAILY_BUDGET_USD / 24 * 0.5      # 50% of hourly budget (~$0.21)
    HOURLY_COST_WARNING = DAILY_BUDGET_USD / 24 * 0.7   # 70% of hourly budget (~$0.29)
    HOURLY_COST_CRITICAL = DAILY_BUDGET_USD / 24 * 0.9  # 90% of hourly budget (~$0.38)
    
    # Latency thresholds (based on user experience research)
    # - <500ms: Excellent, feels instant
    # - 500-1500ms: Good, acceptable for complex queries
    # - >3000ms: Poor, may cause user frustration
    LATENCY_WARNING_MS = 3000.0
    LATENCY_CRITICAL_MS = 8000.0
    
    def __init__(self):
        self._usage_log: List[UsageMetrics] = []
        self._alerts: List[Alert] = []
        self._hourly_costs: Dict[str, float] = defaultdict(float)
        self._log_lock = threading.Lock()
        
    @classmethod
    def get_instance(cls) -> "APIMonitor":
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def record_usage(self, metrics: UsageMetrics) -> None:
        """
        Record API usage metrics.
        
        Args:
            metrics: Usage metrics from API call
        """
        with self._log_lock:
            self._usage_log.append(metrics)
            
            # Update hourly costs
            hour_key = metrics.timestamp.strftime("%Y-%m-%d-%H")
            self._hourly_costs[hour_key] += metrics.estimated_cost_usd
            
            # Check alerts
            self._check_alerts(metrics, hour_key)
            
            # Log structured metrics
            logger.info(
                "api_usage_recorded",
                extra={
                    "model": metrics.model,
                    "prompt_tokens": metrics.prompt_tokens,
                    "cached_tokens": metrics.cached_tokens,
                    "output_tokens": metrics.output_tokens,
                    "cache_hit_rate": round(metrics.cache_hit_rate, 3),
                    "cost_usd": round(metrics.estimated_cost_usd, 6),
                    "is_batch": metrics.is_batch,
                    "latency_ms": metrics.latency_ms,
                }
            )
            
            # Prune old logs (keep last 24 hours)
            self._prune_old_logs()
    
    def record_from_response(
        self,
        response: Any,
        model: str = "gemini-3-flash-preview",
        is_batch: bool = False,
        latency_ms: float = 0.0,
    ) -> UsageMetrics:
        """
        Record usage from Gemini API response.
        
        Args:
            response: Gemini API response with usage_metadata
            model: Model name
            is_batch: Whether this was a batch API call
            latency_ms: Request latency
            
        Returns:
            Recorded UsageMetrics
        """
        try:
            metadata = response.usage_metadata
            prompt_tokens = getattr(metadata, "prompt_token_count", 0)
            cached_tokens = getattr(metadata, "cached_content_token_count", 0)
            output_tokens = getattr(metadata, "candidates_token_count", 0)
            
            cache_hit_rate = cached_tokens / prompt_tokens if prompt_tokens > 0 else 0.0
            
            metrics = UsageMetrics(
                timestamp=datetime.now(timezone.utc),
                model=model,
                prompt_tokens=prompt_tokens,
                cached_tokens=cached_tokens,
                output_tokens=output_tokens,
                cache_hit_rate=cache_hit_rate,
                is_batch=is_batch,
                latency_ms=latency_ms,
            )
            
            self.record_usage(metrics)
            return metrics
            
        except Exception as e:
            logger.warning("Failed to record usage metrics", exc_info=e)
            return UsageMetrics(
                timestamp=datetime.now(timezone.utc),
                model=model,
            )
    
    def _check_alerts(self, metrics: UsageMetrics, hour_key: str) -> None:
        """
        Check and generate alerts based on research-based thresholds.
        
        Alert logic:
        - Cache: Only alert if tokens >= MIN_TOKENS_FOR_CACHE_ALERT (1024)
        - Cost: Tiered 50%/70%/90% of daily budget
        - Latency: Based on UX research (3s warning, 8s critical)
        """
        # ==========================================================================
        # Cache Hit Rate Alerts
        # Only check for requests with enough tokens to benefit from caching
        # ==========================================================================
        if metrics.prompt_tokens >= self.MIN_TOKENS_FOR_CACHE_ALERT:
            if metrics.cache_hit_rate < self.CACHE_HIT_RATE_CRITICAL:
                self._add_alert(
                    level=AlertLevel.CRITICAL,
                    message=f"Cache likely broken: {metrics.cache_hit_rate:.1%} hit rate",
                    metric_name="cache_hit_rate",
                    current_value=metrics.cache_hit_rate,
                    threshold=self.CACHE_HIT_RATE_CRITICAL,
                )
            elif metrics.cache_hit_rate < self.CACHE_HIT_RATE_WARNING:
                self._add_alert(
                    level=AlertLevel.WARNING,
                    message=f"Low cache hit rate: {metrics.cache_hit_rate:.1%} (target: {self.CACHE_HIT_RATE_OPTIMAL:.0%})",
                    metric_name="cache_hit_rate",
                    current_value=metrics.cache_hit_rate,
                    threshold=self.CACHE_HIT_RATE_WARNING,
                )
        
        # ==========================================================================
        # Hourly Cost Alerts (tiered 50%/70%/90%)
        # ==========================================================================
        hourly_cost = self._hourly_costs[hour_key]
        if hourly_cost >= self.HOURLY_COST_CRITICAL:
            self._add_alert(
                level=AlertLevel.CRITICAL,
                message=f"Critical: 90%+ hourly budget (${hourly_cost:.2f})",
                metric_name="hourly_cost_usd",
                current_value=hourly_cost,
                threshold=self.HOURLY_COST_CRITICAL,
            )
        elif hourly_cost >= self.HOURLY_COST_WARNING:
            self._add_alert(
                level=AlertLevel.WARNING,
                message=f"Warning: 70%+ hourly budget (${hourly_cost:.2f})",
                metric_name="hourly_cost_usd",
                current_value=hourly_cost,
                threshold=self.HOURLY_COST_WARNING,
            )
        elif hourly_cost >= self.HOURLY_COST_INFO:
            self._add_alert(
                level=AlertLevel.INFO,
                message=f"Info: 50%+ hourly budget (${hourly_cost:.2f})",
                metric_name="hourly_cost_usd",
                current_value=hourly_cost,
                threshold=self.HOURLY_COST_INFO,
            )
        
        # ==========================================================================
        # Latency Alerts (based on UX research)
        # ==========================================================================
        if metrics.latency_ms >= self.LATENCY_CRITICAL_MS:
            self._add_alert(
                level=AlertLevel.CRITICAL,
                message=f"Very slow response: {metrics.latency_ms:.0f}ms (user frustration likely)",
                metric_name="latency_ms",
                current_value=metrics.latency_ms,
                threshold=self.LATENCY_CRITICAL_MS,
            )
        elif metrics.latency_ms >= self.LATENCY_WARNING_MS:
            self._add_alert(
                level=AlertLevel.WARNING,
                message=f"Slow response: {metrics.latency_ms:.0f}ms (target: <{self.LATENCY_WARNING_MS:.0f}ms)",
                metric_name="latency_ms",
                current_value=metrics.latency_ms,
                threshold=self.LATENCY_WARNING_MS,
            )
    
    def _add_alert(
        self,
        level: AlertLevel,
        message: str,
        metric_name: str,
        current_value: float,
        threshold: float,
    ) -> None:
        """Add an alert to the log."""
        alert = Alert(
            timestamp=datetime.now(timezone.utc),
            level=level,
            message=message,
            metric_name=metric_name,
            current_value=current_value,
            threshold=threshold,
        )
        self._alerts.append(alert)
        
        log_method = logger.warning if level == AlertLevel.WARNING else logger.error
        log_method(
            f"api_alert: {message}",
            extra={
                "level": level.value,
                "metric": metric_name,
                "value": current_value,
                "threshold": threshold,
            }
        )
    
    def _prune_old_logs(self) -> None:
        """Remove logs older than 24 hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        self._usage_log = [m for m in self._usage_log if m.timestamp > cutoff]
        self._alerts = [a for a in self._alerts if a.timestamp > cutoff]
    
    def get_stats(self, period: str = "1h") -> AggregatedStats:
        """
        Get aggregated statistics for a time period.
        
        Args:
            period: "1h", "6h", "24h"
            
        Returns:
            AggregatedStats for the period
        """
        hours = {"1h": 1, "6h": 6, "24h": 24}.get(period, 1)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        with self._log_lock:
            recent = [m for m in self._usage_log if m.timestamp > cutoff]
        
        if not recent:
            return AggregatedStats(
                period_start=cutoff,
                period_end=datetime.now(timezone.utc),
            )
        
        total_cache_hit_rates = [m.cache_hit_rate for m in recent if m.prompt_tokens > 0]
        total_latencies = [m.latency_ms for m in recent if m.latency_ms > 0]
        
        # Calculate cache savings
        total_cost = sum(m.estimated_cost_usd for m in recent)
        total_cached_tokens = sum(m.cached_tokens for m in recent)
        pricing = GEMINI_PRICING["gemini-3-flash-preview"]
        cache_savings = (total_cached_tokens / 1_000_000) * (pricing["input"] - pricing["cached_input"])
        
        return AggregatedStats(
            period_start=cutoff,
            period_end=datetime.now(timezone.utc),
            total_calls=len(recent),
            total_prompt_tokens=sum(m.prompt_tokens for m in recent),
            total_cached_tokens=total_cached_tokens,
            total_output_tokens=sum(m.output_tokens for m in recent),
            total_cost_usd=total_cost,
            avg_cache_hit_rate=sum(total_cache_hit_rates) / len(total_cache_hit_rates) if total_cache_hit_rates else 0.0,
            avg_latency_ms=sum(total_latencies) / len(total_latencies) if total_latencies else 0.0,
            batch_calls=sum(1 for m in recent if m.is_batch),
            cache_savings_usd=cache_savings,
        )
    
    def get_recent_alerts(self, level: Optional[AlertLevel] = None) -> List[Alert]:
        """Get recent alerts, optionally filtered by level."""
        with self._log_lock:
            if level:
                return [a for a in self._alerts if a.level == level]
            return list(self._alerts)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get data for monitoring dashboard.
        
        Returns:
            Dict with dashboard-ready data
        """
        stats_1h = self.get_stats("1h")
        stats_24h = self.get_stats("24h")
        recent_alerts = self.get_recent_alerts()
        
        return {
            "last_hour": {
                "calls": stats_1h.total_calls,
                "cost_usd": round(stats_1h.total_cost_usd, 4),
                "cache_hit_rate": round(stats_1h.avg_cache_hit_rate, 3),
                "cache_savings_usd": round(stats_1h.cache_savings_usd, 4),
                "avg_latency_ms": round(stats_1h.avg_latency_ms, 1),
            },
            "last_24h": {
                "calls": stats_24h.total_calls,
                "cost_usd": round(stats_24h.total_cost_usd, 4),
                "cache_hit_rate": round(stats_24h.avg_cache_hit_rate, 3),
                "cache_savings_usd": round(stats_24h.cache_savings_usd, 4),
                "batch_calls": stats_24h.batch_calls,
                "tokens": {
                    "prompt": stats_24h.total_prompt_tokens,
                    "cached": stats_24h.total_cached_tokens,
                    "output": stats_24h.total_output_tokens,
                }
            },
            "alerts": {
                "total": len(recent_alerts),
                "critical": sum(1 for a in recent_alerts if a.level == AlertLevel.CRITICAL),
                "warning": sum(1 for a in recent_alerts if a.level == AlertLevel.WARNING),
                "recent": [
                    {
                        "timestamp": a.timestamp.isoformat() + "Z",
                        "level": a.level.value,
                        "message": a.message,
                    }
                    for a in recent_alerts[-5:]
                ]
            },
            "thresholds": {
                "cache_hit_rate": {
                    "optimal": self.CACHE_HIT_RATE_OPTIMAL,
                    "warning": self.CACHE_HIT_RATE_WARNING,
                    "critical": self.CACHE_HIT_RATE_CRITICAL,
                    "min_tokens": self.MIN_TOKENS_FOR_CACHE_ALERT,
                },
                "hourly_cost_usd": {
                    "info_50pct": round(self.HOURLY_COST_INFO, 2),
                    "warning_70pct": round(self.HOURLY_COST_WARNING, 2),
                    "critical_90pct": round(self.HOURLY_COST_CRITICAL, 2),
                    "daily_budget": self.DAILY_BUDGET_USD,
                },
                "latency_ms": {
                    "warning": self.LATENCY_WARNING_MS,
                    "critical": self.LATENCY_CRITICAL_MS,
                },
            },
            "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def get_api_monitor() -> APIMonitor:
    """Get the API monitor singleton."""
    return APIMonitor.get_instance()


def record_gemini_usage(
    response: Any,
    model: str = "gemini-3-flash-preview",
    is_batch: bool = False,
    latency_ms: float = 0.0,
) -> UsageMetrics:
    """
    Record Gemini API usage from response.
    
    Usage:
        response = model.generate_content(prompt)
        record_gemini_usage(response, model="gemini-3-flash-preview")
    """
    return get_api_monitor().record_from_response(
        response, model, is_batch, latency_ms
    )
