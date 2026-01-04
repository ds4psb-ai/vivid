"""
Monitoring API Router - API Cost and Performance Dashboard

Provides endpoints for monitoring:
- Real-time API usage statistics
- Cache hit rates
- Cost tracking
- Active alerts
"""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from app.services.api_monitor import (
    APIMonitor,
    AlertLevel,
    get_api_monitor,
)
from app.dependencies import get_current_user_optional
from app.logging_config import get_logger

router = APIRouter(prefix="/api/v1/monitor", tags=["monitor"])
logger = get_logger("monitor_router")


# =============================================================================
# Response Models
# =============================================================================

class PeriodStats(BaseModel):
    """Statistics for a time period."""
    calls: int
    cost_usd: float
    cache_hit_rate: float
    cache_savings_usd: float
    avg_latency_ms: Optional[float] = None
    batch_calls: Optional[int] = None
    tokens: Optional[Dict[str, int]] = None


class AlertInfo(BaseModel):
    """Alert information."""
    timestamp: str
    level: str
    message: str


class AlertSummary(BaseModel):
    """Alert summary."""
    total: int
    critical: int
    warning: int
    recent: List[AlertInfo]


class CacheThresholds(BaseModel):
    """Cache hit rate thresholds."""
    optimal: float
    warning: float
    critical: float
    min_tokens: int


class CostThresholds(BaseModel):
    """Hourly cost thresholds (tiered 50%/70%/90%)."""
    info_50pct: float
    warning_70pct: float
    critical_90pct: float
    daily_budget: float


class LatencyThresholds(BaseModel):
    """Response latency thresholds (ms)."""
    warning: float
    critical: float


class ThresholdConfig(BaseModel):
    """Research-based threshold configuration."""
    cache_hit_rate: CacheThresholds
    hourly_cost_usd: CostThresholds
    latency_ms: LatencyThresholds


class DashboardResponse(BaseModel):
    """Complete dashboard response."""
    last_hour: PeriodStats
    last_24h: PeriodStats
    alerts: AlertSummary
    thresholds: ThresholdConfig
    generated_at: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    cache_status: str
    batch_status: str
    alert_count: int
    hourly_cost_usd: float


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Get API monitoring dashboard data.
    
    Returns real-time statistics including:
    - Last hour and 24h usage
    - Cache hit rates and savings
    - Cost tracking
    - Active alerts
    """
    monitor = get_api_monitor()
    data = monitor.get_dashboard_data()
    
    return DashboardResponse(
        last_hour=PeriodStats(**data["last_hour"]),
        last_24h=PeriodStats(**data["last_24h"]),
        alerts=AlertSummary(**data["alerts"]),
        thresholds=ThresholdConfig(**data["thresholds"]),
        generated_at=data["generated_at"],
    )


@router.get("/health", response_model=HealthResponse)
async def get_health():
    """
    Get API health status.
    
    Quick health check for monitoring systems.
    Uses research-based thresholds from APIMonitor.
    """
    from app.services.api_monitor import APIMonitor
    
    monitor = get_api_monitor()
    stats = monitor.get_stats("1h")
    alerts = monitor.get_recent_alerts(AlertLevel.CRITICAL)
    
    # Determine cache status using research-based thresholds
    cache_status = "healthy"
    if stats.total_calls > 10:  # Only evaluate if enough calls
        if stats.avg_cache_hit_rate < APIMonitor.CACHE_HIT_RATE_CRITICAL:
            cache_status = "unhealthy"
        elif stats.avg_cache_hit_rate < APIMonitor.CACHE_HIT_RATE_WARNING:
            cache_status = "degraded"
        elif stats.avg_cache_hit_rate >= APIMonitor.CACHE_HIT_RATE_OPTIMAL:
            cache_status = "optimal"
    
    # Determine batch status
    batch_status = "healthy"
    
    return HealthResponse(
        status="healthy" if not alerts else "warning",
        cache_status=cache_status,
        batch_status=batch_status,
        alert_count=len(alerts),
        hourly_cost_usd=round(stats.total_cost_usd, 4),
    )


@router.get("/alerts")
async def get_alerts(
    level: Optional[str] = None,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Get recent alerts.
    
    Query params:
    - level: Filter by alert level (info, warning, critical)
    """
    monitor = get_api_monitor()
    
    alert_level = None
    if level:
        try:
            alert_level = AlertLevel(level)
        except ValueError:
            pass
    
    alerts = monitor.get_recent_alerts(alert_level)
    
    return {
        "alerts": [
            {
                "timestamp": a.timestamp.isoformat() + "Z",
                "level": a.level.value,
                "message": a.message,
                "metric": a.metric_name,
                "value": a.current_value,
                "threshold": a.threshold,
            }
            for a in alerts
        ],
        "total": len(alerts),
    }


@router.get("/stats/{period}")
async def get_stats(
    period: str = "1h",
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Get usage statistics for a time period.
    
    Path params:
    - period: "1h", "6h", or "24h"
    """
    if period not in ["1h", "6h", "24h"]:
        period = "1h"
    
    monitor = get_api_monitor()
    stats = monitor.get_stats(period)
    
    return {
        "period": period,
        "period_start": stats.period_start.isoformat() + "Z",
        "period_end": stats.period_end.isoformat() + "Z",
        "total_calls": stats.total_calls,
        "total_cost_usd": round(stats.total_cost_usd, 4),
        "cache_hit_rate": round(stats.avg_cache_hit_rate, 3),
        "cache_savings_usd": round(stats.cache_savings_usd, 4),
        "tokens": {
            "prompt": stats.total_prompt_tokens,
            "cached": stats.total_cached_tokens,
            "output": stats.total_output_tokens,
        },
        "batch_calls": stats.batch_calls,
        "avg_latency_ms": round(stats.avg_latency_ms, 1) if stats.avg_latency_ms else 0,
    }


@router.get("/pricing")
async def get_pricing():
    """
    Get current Gemini API pricing.
    
    Returns pricing per 1M tokens in USD.
    """
    from app.services.api_monitor import GEMINI_PRICING, BATCH_DISCOUNT
    
    return {
        "models": GEMINI_PRICING,
        "batch_discount": BATCH_DISCOUNT,
        "note": "Prices in USD per 1M tokens",
    }
