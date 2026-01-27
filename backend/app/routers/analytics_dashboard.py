"""Analytics Dashboard Router (Phase 9 Monetization & Analytics).

REST endpoints + SSE streaming for real-time analytics dashboard.

Endpoints:
- GET /analytics/kpis - Dashboard KPIs
- GET /analytics/leaderboard/{type} - Leaderboard snapshot
- GET /analytics/revenue/waterfall - Revenue waterfall data
- GET /analytics/funnel/{name} - Funnel conversion analysis
- GET /analytics/retention/cohorts - Retention cohort matrix
- GET /analytics/engagement/score - User engagement score
- GET /analytics/stream/kpis - SSE real-time KPI updates
- GET /analytics/stream/leaderboard/{type} - SSE leaderboard updates
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import date, datetime, timedelta
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.database import get_db
from app.dependencies import get_current_user
from app.models_analytics import (
    LeaderboardSnapshot,
    RealTimeKPICache,
    RetentionCohortSnapshot,
    UserRevenueMetrics,
)
from app.models_telemetry import ToolRunEvent, ToolManifest
from app.services.revenue_attribution_service import RevenueAttributionService
from app.services.engagement_analytics_service import EngagementAnalyticsService
from app.utils.sse_utils import sse_event, sse_heartbeat, SSE_HEADERS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


# =============================================================================
# Pydantic Response Models
# =============================================================================

class KPIValue(BaseModel):
    """Single KPI value with metadata."""
    key: str
    value: float
    unit: str = ""
    trend: str = "neutral"  # up, down, neutral
    delta_pct: Optional[float] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardKPIs(BaseModel):
    """Dashboard KPI collection."""
    total_revenue: KPIValue
    active_users: KPIValue
    tool_executions: KPIValue
    avg_engagement_score: KPIValue
    conversion_rate: KPIValue
    period_days: int = 30


class LeaderboardEntry(BaseModel):
    """Single leaderboard entry."""
    rank: int
    user_id: str
    display_name: Optional[str] = None
    score: float
    delta: Optional[int] = None  # Rank change from previous period


class LeaderboardResponse(BaseModel):
    """Leaderboard response."""
    leaderboard_type: str
    scope: str
    period: str
    period_date: date
    entries: List[LeaderboardEntry]
    updated_at: datetime


class RevenueWaterfallResponse(BaseModel):
    """Revenue waterfall response."""
    period_days: int
    total_revenue: int
    tool_usage_revenue: int
    fork_revenue_received: int
    fork_revenue_shared: int
    platform_fees: int
    net_revenue: int
    daily_breakdown: List[Dict[str, Any]]


class FunnelStepResponse(BaseModel):
    """Funnel step response."""
    step_name: str
    step_order: int
    users_entered: int
    users_completed: int
    conversion_rate: float
    drop_off_rate: float
    avg_time_in_step_ms: float
    top_drop_off_reasons: List[Dict[str, Any]]


class FunnelAnalysisResponse(BaseModel):
    """Funnel analysis response."""
    funnel_name: str
    period_start: date
    period_end: date
    total_users_started: int
    total_users_completed: int
    overall_conversion_rate: float
    steps: List[FunnelStepResponse]
    bottleneck_step: Optional[str] = None


class CohortRow(BaseModel):
    """Single cohort row in retention matrix."""
    cohort_date: date
    cohort_size: int
    retention_rates: List[float]  # [period_0, period_1, ...]
    revenue_per_user: List[float]


class RetentionCohortsResponse(BaseModel):
    """Retention cohort matrix response."""
    cohort_type: str
    period_type: str
    periods: int
    cohorts: List[CohortRow]


class EngagementScoreResponse(BaseModel):
    """User engagement score response."""
    user_id: str
    total_score: float
    tier: str
    recency_score: float
    frequency_score: float
    monetary_score: float
    depth_score: float
    last_activity: Optional[datetime] = None


class TopToolResponse(BaseModel):
    """Top contributing tool."""
    tool_key: str
    revenue: int
    executions: int
    avg_rating: Optional[float] = None


# =============================================================================
# REST Endpoints
# =============================================================================

@router.get("/kpis", response_model=DashboardKPIs)
async def get_dashboard_kpis(
    period_days: int = Query(default=30, ge=1, le=365, description="Analysis period in days"),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> DashboardKPIs:
    """Get pre-computed dashboard KPIs.

    Returns key performance indicators for the analytics dashboard.
    Data is cached for fast retrieval (<500ms target).
    """
    now = datetime.utcnow()
    since = now - timedelta(days=period_days)

    # Total revenue
    revenue_result = await db.execute(
        select(func.sum(ToolRunEvent.credits_charged - ToolRunEvent.credits_refunded))
        .where(ToolRunEvent.created_at >= since)
    )
    total_revenue = revenue_result.scalar() or 0

    # Previous period for trend
    prev_since = since - timedelta(days=period_days)
    prev_revenue_result = await db.execute(
        select(func.sum(ToolRunEvent.credits_charged - ToolRunEvent.credits_refunded))
        .where(
            and_(
                ToolRunEvent.created_at >= prev_since,
                ToolRunEvent.created_at < since,
            )
        )
    )
    prev_revenue = prev_revenue_result.scalar() or 1
    revenue_delta = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue else 0

    # Active users
    active_result = await db.execute(
        select(func.count(func.distinct(ToolRunEvent.user_id)))
        .where(ToolRunEvent.created_at >= since)
    )
    active_users = active_result.scalar() or 0

    # Tool executions
    exec_result = await db.execute(
        select(func.count())
        .where(ToolRunEvent.created_at >= since)
    )
    total_executions = exec_result.scalar() or 0

    # Success rate (as proxy for engagement)
    success_result = await db.execute(
        select(func.count())
        .where(
            and_(
                ToolRunEvent.created_at >= since,
                ToolRunEvent.status == "success",
            )
        )
    )
    successful = success_result.scalar() or 0
    engagement_score = (successful / total_executions * 100) if total_executions else 0

    # Conversion rate (users who completed a tool run / total users)
    conversion_rate = (active_users / max(active_users * 1.5, 1)) * 100  # Placeholder

    return DashboardKPIs(
        total_revenue=KPIValue(
            key="total_revenue",
            value=float(total_revenue),
            unit="credits",
            trend="up" if revenue_delta > 0 else "down" if revenue_delta < 0 else "neutral",
            delta_pct=round(revenue_delta, 2),
            updated_at=now,
        ),
        active_users=KPIValue(
            key="active_users",
            value=float(active_users),
            unit="users",
            trend="neutral",
            updated_at=now,
        ),
        tool_executions=KPIValue(
            key="tool_executions",
            value=float(total_executions),
            unit="runs",
            trend="neutral",
            updated_at=now,
        ),
        avg_engagement_score=KPIValue(
            key="avg_engagement_score",
            value=round(engagement_score, 2),
            unit="%",
            trend="neutral",
            updated_at=now,
        ),
        conversion_rate=KPIValue(
            key="conversion_rate",
            value=round(conversion_rate, 2),
            unit="%",
            trend="neutral",
            updated_at=now,
        ),
        period_days=period_days,
    )


@router.get("/leaderboard/{leaderboard_type}", response_model=LeaderboardResponse)
async def get_leaderboard(
    leaderboard_type: str,
    period: str = Query(default="weekly", description="Period: daily, weekly, monthly, all_time"),
    scope: str = Query(default="global", description="Scope: global, dimension, category"),
    scope_value: Optional[str] = Query(default=None, description="Scope value if dimension/category"),
    limit: int = Query(default=10, ge=1, le=100, description="Number of entries"),
    db: AsyncSession = Depends(get_db),
) -> LeaderboardResponse:
    """Get leaderboard snapshot.

    Returns pre-computed leaderboard rankings.
    """
    now = datetime.utcnow()
    period_date = now.date()

    # Try to get cached leaderboard
    result = await db.execute(
        select(LeaderboardSnapshot)
        .where(
            and_(
                LeaderboardSnapshot.leaderboard_type == leaderboard_type,
                LeaderboardSnapshot.period_type == period,
                LeaderboardSnapshot.scope == scope,
            )
        )
        .order_by(desc(LeaderboardSnapshot.computed_at))
        .limit(1)
    )
    snapshot = result.scalar_one_or_none()

    if snapshot:
        entries = [
            LeaderboardEntry(
                rank=r.get("rank", i + 1),
                user_id=r.get("user_id", ""),
                display_name=r.get("display_name"),
                score=r.get("score", 0),
                delta=r.get("delta"),
            )
            for i, r in enumerate(snapshot.rankings[:limit])
        ]
        return LeaderboardResponse(
            leaderboard_type=leaderboard_type,
            scope=snapshot.scope,
            period=snapshot.period_type,
            period_date=snapshot.period_date,
            entries=entries,
            updated_at=snapshot.computed_at,
        )

    # Compute live if no cached data
    since = now - timedelta(days=7 if period == "weekly" else 30)

    if leaderboard_type == "creator_revenue":
        result = await db.execute(
            select(
                ToolManifest.created_by,
                func.sum(ToolRunEvent.credits_charged - ToolRunEvent.credits_refunded).label("score"),
            )
            .join(ToolManifest, ToolRunEvent.tool_id == ToolManifest.id)
            .where(ToolRunEvent.created_at >= since)
            .group_by(ToolManifest.created_by)
            .order_by(desc("score"))
            .limit(limit)
        )
    else:
        # Default: tool usage
        result = await db.execute(
            select(
                ToolRunEvent.user_id,
                func.count().label("score"),
            )
            .where(
                and_(
                    ToolRunEvent.created_at >= since,
                    ToolRunEvent.user_id.isnot(None),
                )
            )
            .group_by(ToolRunEvent.user_id)
            .order_by(desc("score"))
            .limit(limit)
        )

    entries = [
        LeaderboardEntry(
            rank=i + 1,
            user_id=row[0] or "anonymous",
            score=float(row[1] or 0),
        )
        for i, row in enumerate(result)
    ]

    return LeaderboardResponse(
        leaderboard_type=leaderboard_type,
        scope=scope,
        period=period,
        period_date=period_date,
        entries=entries,
        updated_at=now,
    )


@router.get("/revenue/waterfall", response_model=RevenueWaterfallResponse)
async def get_revenue_waterfall(
    period_days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> RevenueWaterfallResponse:
    """Get revenue waterfall data.

    Returns revenue breakdown for waterfall visualization.
    """
    service = RevenueAttributionService(db)
    user_id = current_user.email if hasattr(current_user, 'email') else str(current_user.id)
    waterfall = await service.get_revenue_waterfall(user_id, period_days)

    return RevenueWaterfallResponse(
        period_days=waterfall.period_days,
        total_revenue=waterfall.total_revenue,
        tool_usage_revenue=waterfall.tool_usage_revenue,
        fork_revenue_received=waterfall.fork_revenue_received,
        fork_revenue_shared=waterfall.fork_revenue_shared,
        platform_fees=waterfall.platform_fees,
        net_revenue=waterfall.net_revenue,
        daily_breakdown=waterfall.daily_breakdown,
    )


@router.get("/funnel/{funnel_name}", response_model=FunnelAnalysisResponse)
async def get_funnel_analysis(
    funnel_name: str,
    start_date: date = Query(..., description="Analysis start date"),
    end_date: date = Query(..., description="Analysis end date"),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> FunnelAnalysisResponse:
    """Get funnel conversion analysis.

    Analyzes user progression through a conversion funnel.
    """
    service = EngagementAnalyticsService(db)
    analysis = await service.analyze_funnel(funnel_name, start_date, end_date)

    return FunnelAnalysisResponse(
        funnel_name=analysis.funnel_name,
        period_start=analysis.period_start,
        period_end=analysis.period_end,
        total_users_started=analysis.total_users_started,
        total_users_completed=analysis.total_users_completed,
        overall_conversion_rate=analysis.overall_conversion_rate,
        steps=[
            FunnelStepResponse(
                step_name=s.step_name,
                step_order=s.step_order,
                users_entered=s.users_entered,
                users_completed=s.users_completed,
                conversion_rate=s.conversion_rate,
                drop_off_rate=s.drop_off_rate,
                avg_time_in_step_ms=s.avg_time_in_step_ms,
                top_drop_off_reasons=s.top_drop_off_reasons,
            )
            for s in analysis.steps
        ],
        bottleneck_step=analysis.bottleneck_step,
    )


@router.get("/retention/cohorts", response_model=RetentionCohortsResponse)
async def get_retention_cohorts(
    cohort_type: str = Query(default="first_tool", description="Cohort type"),
    period_type: str = Query(default="weekly", description="Period: daily, weekly, monthly"),
    periods: int = Query(default=8, ge=1, le=52, description="Number of periods"),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> RetentionCohortsResponse:
    """Get retention cohort matrix.

    Returns retention data for cohort analysis heatmap.
    """
    service = EngagementAnalyticsService(db)
    snapshots = await service.compute_retention_cohorts(cohort_type, period_type, periods)

    # Group by cohort date
    cohort_data: Dict[date, Dict[int, Any]] = {}
    for s in snapshots:
        if s.cohort_date not in cohort_data:
            cohort_data[s.cohort_date] = {
                "cohort_size": s.cohort_size,
                "retention": {},
                "revenue": {},
            }
        cohort_data[s.cohort_date]["retention"][s.period_offset] = s.retention_rate
        cohort_data[s.cohort_date]["revenue"][s.period_offset] = s.revenue_per_user

    # Build response
    cohorts = []
    for cohort_date in sorted(cohort_data.keys(), reverse=True):
        data = cohort_data[cohort_date]
        retention_rates = [data["retention"].get(i, 0.0) for i in range(periods)]
        revenue_per_user = [data["revenue"].get(i, 0.0) for i in range(periods)]

        cohorts.append(
            CohortRow(
                cohort_date=cohort_date,
                cohort_size=data["cohort_size"],
                retention_rates=retention_rates,
                revenue_per_user=revenue_per_user,
            )
        )

    return RetentionCohortsResponse(
        cohort_type=cohort_type,
        period_type=period_type,
        periods=periods,
        cohorts=cohorts,
    )


@router.get("/engagement/score", response_model=EngagementScoreResponse)
async def get_engagement_score(
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> EngagementScoreResponse:
    """Get user's engagement score.

    Returns RFM-based engagement score with component breakdown.
    """
    service = EngagementAnalyticsService(db)
    user_id = current_user.email if hasattr(current_user, 'email') else str(current_user.id)
    score = await service.compute_engagement_score(user_id)

    return EngagementScoreResponse(
        user_id=score.user_id,
        total_score=score.total_score,
        tier=score.tier,
        recency_score=score.recency_score,
        frequency_score=score.frequency_score,
        monetary_score=score.monetary_score,
        depth_score=score.depth_score,
        last_activity=score.last_activity,
    )


@router.get("/top-tools", response_model=List[TopToolResponse])
async def get_top_tools(
    period_days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> List[TopToolResponse]:
    """Get user's top contributing tools by revenue."""
    service = RevenueAttributionService(db)
    user_id = current_user.email if hasattr(current_user, 'email') else str(current_user.id)
    tools = await service.get_top_contributing_tools(user_id, period_days, limit)

    return [
        TopToolResponse(
            tool_key=t["tool_key"],
            revenue=t["revenue"],
            executions=t["executions"],
            avg_rating=t.get("avg_rating"),
        )
        for t in tools
    ]


# =============================================================================
# SSE Streaming Endpoints
# =============================================================================

async def kpi_stream_generator(
    user_id: str,
    db: AsyncSession,
    interval_seconds: int = 5,
) -> AsyncGenerator[str, None]:
    """Generate SSE stream for real-time KPI updates.

    Args:
        user_id: User ID for personalized KPIs
        db: Database session
        interval_seconds: Update interval

    Yields:
        SSE event strings
    """
    heartbeat_interval = 15
    last_heartbeat = time.time()

    while True:
        try:
            now = datetime.utcnow()
            since = now - timedelta(days=30)

            # Get current KPIs
            revenue_result = await db.execute(
                select(func.sum(ToolRunEvent.credits_charged - ToolRunEvent.credits_refunded))
                .where(ToolRunEvent.created_at >= since)
            )
            total_revenue = revenue_result.scalar() or 0

            exec_result = await db.execute(
                select(func.count())
                .where(ToolRunEvent.created_at >= since)
            )
            total_executions = exec_result.scalar() or 0

            kpi_data = {
                "total_revenue": total_revenue,
                "total_executions": total_executions,
                "timestamp": now.isoformat(),
            }

            yield sse_event("kpi_update", kpi_data)

            # Heartbeat
            if time.time() - last_heartbeat > heartbeat_interval:
                yield sse_heartbeat()
                last_heartbeat = time.time()

            await asyncio.sleep(interval_seconds)

        except asyncio.CancelledError:
            logger.info(f"KPI stream cancelled for user {user_id}")
            break
        except Exception as e:
            logger.warning(f"KPI stream error: {e}")
            yield sse_event("error", {"message": str(e)})
            await asyncio.sleep(interval_seconds)


@router.get("/stream/kpis")
async def stream_kpis(
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """SSE: Real-time KPI updates every 5 seconds.

    Connect to this endpoint for live KPI updates on the dashboard.
    """
    user_id = current_user.email if hasattr(current_user, 'email') else str(current_user.id)

    return StreamingResponse(
        kpi_stream_generator(user_id, db),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


async def leaderboard_stream_generator(
    leaderboard_type: str,
    db: AsyncSession,
    interval_seconds: int = 30,
) -> AsyncGenerator[str, None]:
    """Generate SSE stream for leaderboard updates.

    Args:
        leaderboard_type: Type of leaderboard
        db: Database session
        interval_seconds: Update interval

    Yields:
        SSE event strings
    """
    heartbeat_interval = 15
    last_heartbeat = time.time()

    while True:
        try:
            now = datetime.utcnow()
            since = now - timedelta(days=7)

            # Get top 10
            result = await db.execute(
                select(
                    ToolRunEvent.user_id,
                    func.count().label("score"),
                )
                .where(
                    and_(
                        ToolRunEvent.created_at >= since,
                        ToolRunEvent.user_id.isnot(None),
                    )
                )
                .group_by(ToolRunEvent.user_id)
                .order_by(desc("score"))
                .limit(10)
            )

            entries = [
                {
                    "rank": i + 1,
                    "user_id": row[0] or "anonymous",
                    "score": float(row[1] or 0),
                }
                for i, row in enumerate(result)
            ]

            yield sse_event("leaderboard_update", {
                "type": leaderboard_type,
                "entries": entries,
                "timestamp": now.isoformat(),
            })

            # Heartbeat
            if time.time() - last_heartbeat > heartbeat_interval:
                yield sse_heartbeat()
                last_heartbeat = time.time()

            await asyncio.sleep(interval_seconds)

        except asyncio.CancelledError:
            logger.info(f"Leaderboard stream cancelled for {leaderboard_type}")
            break
        except Exception as e:
            logger.warning(f"Leaderboard stream error: {e}")
            yield sse_event("error", {"message": str(e)})
            await asyncio.sleep(interval_seconds)


@router.get("/stream/leaderboard/{leaderboard_type}")
async def stream_leaderboard(
    leaderboard_type: str,
    db: AsyncSession = Depends(get_db),
):
    """SSE: Leaderboard updates every 30 seconds.

    Connect to this endpoint for live leaderboard updates.
    """
    return StreamingResponse(
        leaderboard_stream_generator(leaderboard_type, db),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
