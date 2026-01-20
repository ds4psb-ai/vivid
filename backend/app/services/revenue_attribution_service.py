"""Revenue Attribution Service (Phase 9 Monetization & Analytics).

Multi-touch attribution with Shapley-inspired model for revenue distribution.

2026 Best Practices:
- Shapley Value Attribution: Fair contribution allocation across touchpoints
- Time Decay: Recent interactions weighted more heavily
- Attribution Windows: 30-day lookback for revenue attribution

Usage:
    from app.services.revenue_attribution_service import RevenueAttributionService

    service = RevenueAttributionService(db)
    results = await service.compute_user_attribution(user_id, revenue_event_id, amount)
    snapshot = await service.aggregate_daily_snapshot(user_id, target_date)
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional, Tuple
import math

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_analytics import UserRevenueMetrics
from app.models_telemetry import ToolRunEvent, ForkEvent, ToolManifest

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Touchpoint weights for attribution
TOUCHPOINT_WEIGHTS = {
    "tool_usage": 1.0,        # Direct tool usage
    "tool_rating": 0.5,       # User rated a tool
    "fork_created": 2.0,      # Created a fork (high value)
    "fork_used": 1.5,         # Used a forked tool
    "content_viewed": 0.2,    # Viewed content
    "search_click": 0.3,      # Clicked from search
    "workflow_step": 0.8,     # Part of workflow
    "recommendation": 0.4,    # Clicked recommendation
}

# Time decay factor (per day)
TIME_DECAY_FACTOR = 0.95  # 5% decay per day

# Attribution lookback window
DEFAULT_LOOKBACK_DAYS = 30


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Touchpoint:
    """A user interaction touchpoint for attribution."""
    touchpoint_type: str
    touchpoint_id: str
    user_id: str
    timestamp: datetime
    tool_key: Optional[str] = None
    dimension: Optional[str] = None
    value: float = 1.0
    context: Dict[str, Any] = field(default_factory=dict)

    @property
    def weight(self) -> float:
        """Get base weight for this touchpoint type."""
        return TOUCHPOINT_WEIGHTS.get(self.touchpoint_type, 0.5)


@dataclass
class AttributionResult:
    """Attribution result for a single touchpoint."""
    touchpoint_type: str
    touchpoint_id: str
    tool_key: Optional[str]
    raw_weight: float
    time_decay_factor: float
    normalized_weight: float  # 0-1, sums to 1.0 across all touchpoints
    revenue_attributed: int  # Credits attributed


@dataclass
class UserRevenueSnapshot:
    """Daily revenue snapshot for a user."""
    user_id: str
    snapshot_date: date
    total_revenue_credits: int
    tool_revenue_breakdown: Dict[str, int]
    dimension_revenue_breakdown: Dict[str, int]
    fork_revenue_received: int
    fork_revenue_shared: int
    attribution_scores: List[Dict[str, Any]]
    total_executions: int
    successful_executions: int
    avg_latency_ms: Optional[float]


@dataclass
class RevenueWaterfallData:
    """Revenue waterfall visualization data."""
    period_days: int
    total_revenue: int
    tool_usage_revenue: int
    fork_revenue_received: int
    fork_revenue_shared: int
    platform_fees: int
    net_revenue: int
    daily_breakdown: List[Dict[str, Any]]


@dataclass
class ContributionPoint:
    """Tool contribution time-series point."""
    date: date
    revenue: int
    executions: int
    unique_users: int
    avg_rating: Optional[float]


# =============================================================================
# Revenue Attribution Service
# =============================================================================

class RevenueAttributionService:
    """Multi-touch attribution with Shapley-inspired model.

    Computes fair revenue attribution across multiple touchpoints:
    - Direct tool usage
    - Fork relationships
    - Recommendations and search
    - Workflow participation

    Attributes:
        db: Async database session
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize revenue attribution service.

        Args:
            db: Async database session
        """
        self._db = db

    async def compute_user_attribution(
        self,
        user_id: str,
        revenue_event_id: uuid.UUID,
        revenue_amount: int,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    ) -> List[AttributionResult]:
        """Compute multi-touch attribution for a revenue event.

        Uses Shapley-inspired weighting:
        1. Collect all touchpoints in the lookback window
        2. Apply base weights by touchpoint type
        3. Apply time decay (more recent = higher weight)
        4. Normalize weights to sum to 1.0
        5. Distribute revenue proportionally

        Args:
            user_id: User who generated the revenue
            revenue_event_id: ID of the revenue-generating event
            revenue_amount: Revenue amount in credits
            lookback_days: Days to look back for touchpoints

        Returns:
            List[AttributionResult]: Attribution for each contributing touchpoint
        """
        # Collect touchpoints from the lookback window
        since = datetime.utcnow() - timedelta(days=lookback_days)
        touchpoints = await self._collect_touchpoints(user_id, since)

        if not touchpoints:
            # No touchpoints found, attribute 100% to direct
            return [
                AttributionResult(
                    touchpoint_type="direct",
                    touchpoint_id=str(revenue_event_id),
                    tool_key=None,
                    raw_weight=1.0,
                    time_decay_factor=1.0,
                    normalized_weight=1.0,
                    revenue_attributed=revenue_amount,
                )
            ]

        # Calculate weighted scores with time decay
        now = datetime.utcnow()
        weighted_scores: List[Tuple[Touchpoint, float]] = []
        total_weight = 0.0

        for tp in touchpoints:
            # Days since touchpoint
            days_ago = (now - tp.timestamp).total_seconds() / 86400
            time_decay = TIME_DECAY_FACTOR ** days_ago

            # Combined weight
            raw_weight = tp.weight * tp.value
            weighted_score = raw_weight * time_decay
            weighted_scores.append((tp, weighted_score))
            total_weight += weighted_score

        # Normalize and compute attribution
        results: List[AttributionResult] = []
        for tp, weighted_score in weighted_scores:
            normalized_weight = weighted_score / total_weight if total_weight > 0 else 0
            revenue_attributed = int(revenue_amount * normalized_weight)

            days_ago = (now - tp.timestamp).total_seconds() / 86400
            time_decay = TIME_DECAY_FACTOR ** days_ago

            results.append(
                AttributionResult(
                    touchpoint_type=tp.touchpoint_type,
                    touchpoint_id=tp.touchpoint_id,
                    tool_key=tp.tool_key,
                    raw_weight=tp.weight * tp.value,
                    time_decay_factor=time_decay,
                    normalized_weight=normalized_weight,
                    revenue_attributed=revenue_attributed,
                )
            )

        # Sort by revenue attributed (descending)
        results.sort(key=lambda r: r.revenue_attributed, reverse=True)

        return results

    async def aggregate_daily_snapshot(
        self,
        user_id: str,
        target_date: date,
    ) -> UserRevenueSnapshot:
        """Generate daily revenue snapshot for user.

        Aggregates all revenue-related metrics for the specified date.

        Args:
            user_id: User ID
            target_date: Date to aggregate

        Returns:
            UserRevenueSnapshot: Daily snapshot
        """
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = datetime.combine(target_date, datetime.max.time())

        # Query tool run events for the day
        result = await self._db.execute(
            select(ToolRunEvent)
            .where(
                and_(
                    ToolRunEvent.user_id == user_id,
                    ToolRunEvent.created_at >= start_dt,
                    ToolRunEvent.created_at <= end_dt,
                )
            )
        )
        run_events = list(result.scalars())

        # Aggregate metrics
        total_revenue = 0
        tool_revenue: Dict[str, int] = {}
        dimension_revenue: Dict[str, int] = {}
        total_executions = len(run_events)
        successful_executions = 0
        latencies: List[int] = []

        for event in run_events:
            credits = event.credits_charged - event.credits_refunded
            total_revenue += credits

            # Tool breakdown
            tool_revenue[event.tool_key] = tool_revenue.get(event.tool_key, 0) + credits

            # Track success/latency
            if event.status == "success":
                successful_executions += 1
            if event.latency_ms:
                latencies.append(event.latency_ms)

        # Get dimension from tool manifests
        for tool_key in tool_revenue.keys():
            manifest_result = await self._db.execute(
                select(ToolManifest).where(ToolManifest.tool_key == tool_key)
            )
            manifest = manifest_result.scalar_one_or_none()
            if manifest:
                dim = manifest.category or "unknown"
                dimension_revenue[dim] = dimension_revenue.get(dim, 0) + tool_revenue[tool_key]

        # Fork revenue
        fork_received, fork_shared = await self._get_fork_revenue(user_id, start_dt, end_dt)

        # Calculate avg latency
        avg_latency = sum(latencies) / len(latencies) if latencies else None

        # Build attribution scores summary
        attribution_scores = await self._summarize_attributions(user_id, start_dt, end_dt)

        return UserRevenueSnapshot(
            user_id=user_id,
            snapshot_date=target_date,
            total_revenue_credits=total_revenue,
            tool_revenue_breakdown=tool_revenue,
            dimension_revenue_breakdown=dimension_revenue,
            fork_revenue_received=fork_received,
            fork_revenue_shared=fork_shared,
            attribution_scores=attribution_scores,
            total_executions=total_executions,
            successful_executions=successful_executions,
            avg_latency_ms=avg_latency,
        )

    async def save_daily_snapshot(
        self,
        snapshot: UserRevenueSnapshot,
    ) -> UserRevenueMetrics:
        """Save daily snapshot to database.

        Args:
            snapshot: Snapshot to save

        Returns:
            UserRevenueMetrics: Saved model
        """
        # Check for existing snapshot
        result = await self._db.execute(
            select(UserRevenueMetrics).where(
                and_(
                    UserRevenueMetrics.user_id == snapshot.user_id,
                    UserRevenueMetrics.snapshot_date == snapshot.snapshot_date,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.total_revenue_credits = snapshot.total_revenue_credits
            existing.tool_revenue_breakdown = snapshot.tool_revenue_breakdown
            existing.dimension_revenue_breakdown = snapshot.dimension_revenue_breakdown
            existing.fork_revenue_received = snapshot.fork_revenue_received
            existing.fork_revenue_shared = snapshot.fork_revenue_shared
            existing.attribution_scores = snapshot.attribution_scores
            existing.total_executions = snapshot.total_executions
            existing.successful_executions = snapshot.successful_executions
            existing.avg_latency_ms = snapshot.avg_latency_ms
            await self._db.flush()
            return existing
        else:
            # Create new
            metrics = UserRevenueMetrics(
                user_id=snapshot.user_id,
                snapshot_date=snapshot.snapshot_date,
                total_revenue_credits=snapshot.total_revenue_credits,
                tool_revenue_breakdown=snapshot.tool_revenue_breakdown,
                dimension_revenue_breakdown=snapshot.dimension_revenue_breakdown,
                fork_revenue_received=snapshot.fork_revenue_received,
                fork_revenue_shared=snapshot.fork_revenue_shared,
                attribution_scores=snapshot.attribution_scores,
                total_executions=snapshot.total_executions,
                successful_executions=snapshot.successful_executions,
                avg_latency_ms=snapshot.avg_latency_ms,
            )
            self._db.add(metrics)
            await self._db.flush()
            return metrics

    async def get_revenue_waterfall(
        self,
        user_id: str,
        period_days: int = 30,
    ) -> RevenueWaterfallData:
        """Get revenue waterfall visualization data.

        Args:
            user_id: User ID
            period_days: Days to analyze

        Returns:
            RevenueWaterfallData: Waterfall data
        """
        since = datetime.utcnow() - timedelta(days=period_days)

        # Query daily snapshots
        result = await self._db.execute(
            select(UserRevenueMetrics)
            .where(
                and_(
                    UserRevenueMetrics.user_id == user_id,
                    UserRevenueMetrics.snapshot_date >= since.date(),
                )
            )
            .order_by(UserRevenueMetrics.snapshot_date)
        )
        snapshots = list(result.scalars())

        # Aggregate
        total_revenue = sum(s.total_revenue_credits for s in snapshots)
        fork_received = sum(s.fork_revenue_received for s in snapshots)
        fork_shared = sum(s.fork_revenue_shared for s in snapshots)
        tool_usage_revenue = total_revenue - fork_received

        # Platform fee estimate (30%)
        platform_fees = int(total_revenue * 0.30)
        net_revenue = total_revenue - platform_fees

        # Daily breakdown
        daily_breakdown = [
            {
                "date": s.snapshot_date.isoformat(),
                "revenue": s.total_revenue_credits,
                "executions": s.total_executions,
            }
            for s in snapshots
        ]

        return RevenueWaterfallData(
            period_days=period_days,
            total_revenue=total_revenue,
            tool_usage_revenue=tool_usage_revenue,
            fork_revenue_received=fork_received,
            fork_revenue_shared=fork_shared,
            platform_fees=platform_fees,
            net_revenue=net_revenue,
            daily_breakdown=daily_breakdown,
        )

    async def get_tool_contribution_history(
        self,
        tool_id: uuid.UUID,
        period_days: int = 30,
    ) -> List[ContributionPoint]:
        """Get tool contribution time-series.

        Args:
            tool_id: Tool UUID
            period_days: Days to analyze

        Returns:
            List[ContributionPoint]: Daily contribution points
        """
        since = datetime.utcnow() - timedelta(days=period_days)

        # Query tool run events grouped by date
        result = await self._db.execute(
            select(
                func.date(ToolRunEvent.created_at).label("date"),
                func.sum(ToolRunEvent.credits_charged - ToolRunEvent.credits_refunded).label("revenue"),
                func.count().label("executions"),
                func.count(func.distinct(ToolRunEvent.user_id)).label("unique_users"),
                func.avg(ToolRunEvent.user_rating).label("avg_rating"),
            )
            .where(
                and_(
                    ToolRunEvent.tool_id == tool_id,
                    ToolRunEvent.created_at >= since,
                )
            )
            .group_by(func.date(ToolRunEvent.created_at))
            .order_by(func.date(ToolRunEvent.created_at))
        )

        points: List[ContributionPoint] = []
        for row in result:
            points.append(
                ContributionPoint(
                    date=row.date,
                    revenue=int(row.revenue or 0),
                    executions=int(row.executions or 0),
                    unique_users=int(row.unique_users or 0),
                    avg_rating=float(row.avg_rating) if row.avg_rating else None,
                )
            )

        return points

    async def get_top_contributing_tools(
        self,
        user_id: str,
        period_days: int = 30,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get top contributing tools by revenue.

        Args:
            user_id: User ID
            period_days: Days to analyze
            limit: Max tools to return

        Returns:
            List of tool contribution data
        """
        since = datetime.utcnow() - timedelta(days=period_days)

        result = await self._db.execute(
            select(
                ToolRunEvent.tool_key,
                func.sum(ToolRunEvent.credits_charged - ToolRunEvent.credits_refunded).label("revenue"),
                func.count().label("executions"),
                func.avg(ToolRunEvent.user_rating).label("avg_rating"),
            )
            .where(
                and_(
                    ToolRunEvent.user_id == user_id,
                    ToolRunEvent.created_at >= since,
                )
            )
            .group_by(ToolRunEvent.tool_key)
            .order_by(desc("revenue"))
            .limit(limit)
        )

        tools: List[Dict[str, Any]] = []
        for row in result:
            tools.append({
                "tool_key": row.tool_key,
                "revenue": int(row.revenue or 0),
                "executions": int(row.executions or 0),
                "avg_rating": float(row.avg_rating) if row.avg_rating else None,
            })

        return tools

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _collect_touchpoints(
        self,
        user_id: str,
        since: datetime,
    ) -> List[Touchpoint]:
        """Collect all touchpoints for a user in the given time window.

        Args:
            user_id: User ID
            since: Start of lookback window

        Returns:
            List[Touchpoint]: All touchpoints
        """
        touchpoints: List[Touchpoint] = []

        # 1. Tool run events
        result = await self._db.execute(
            select(ToolRunEvent)
            .where(
                and_(
                    ToolRunEvent.user_id == user_id,
                    ToolRunEvent.created_at >= since,
                )
            )
        )
        for event in result.scalars():
            tp_type = "tool_usage"
            value = 1.0

            # Boost value if user rated the tool
            if event.user_rating:
                tp_type = "tool_rating"
                value = event.user_rating / 5.0 * 2.0  # Scale rating to 0-2x boost

            touchpoints.append(
                Touchpoint(
                    touchpoint_type=tp_type,
                    touchpoint_id=str(event.id),
                    user_id=user_id,
                    timestamp=event.created_at,
                    tool_key=event.tool_key,
                    value=value,
                )
            )

        # 2. Fork events (as creator)
        fork_result = await self._db.execute(
            select(ForkEvent)
            .where(
                and_(
                    ForkEvent.forker_id == user_id,
                    ForkEvent.created_at >= since,
                )
            )
        )
        for fork in fork_result.scalars():
            touchpoints.append(
                Touchpoint(
                    touchpoint_type="fork_created",
                    touchpoint_id=str(fork.id),
                    user_id=user_id,
                    timestamp=fork.created_at,
                    value=fork.attribution_score / 50.0 if fork.attribution_score else 1.0,
                )
            )

        return touchpoints

    async def _get_fork_revenue(
        self,
        user_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> Tuple[int, int]:
        """Get fork revenue received and shared.

        Args:
            user_id: User ID
            start_dt: Start datetime
            end_dt: End datetime

        Returns:
            Tuple of (received, shared) credits
        """
        # Revenue received from forks of user's tools
        received_result = await self._db.execute(
            select(func.sum(ForkEvent.revenue_shared))
            .join(ToolManifest, ForkEvent.parent_tool_id == ToolManifest.id)
            .where(
                and_(
                    ToolManifest.created_by == user_id,
                    ForkEvent.created_at >= start_dt,
                    ForkEvent.created_at <= end_dt,
                )
            )
        )
        received = received_result.scalar() or 0

        # Revenue shared to ancestors
        shared_result = await self._db.execute(
            select(func.sum(ForkEvent.revenue_shared))
            .where(
                and_(
                    ForkEvent.forker_id == user_id,
                    ForkEvent.created_at >= start_dt,
                    ForkEvent.created_at <= end_dt,
                )
            )
        )
        shared = shared_result.scalar() or 0

        return int(received), int(shared)

    async def _summarize_attributions(
        self,
        user_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> List[Dict[str, Any]]:
        """Summarize attributions by type.

        Args:
            user_id: User ID
            start_dt: Start datetime
            end_dt: End datetime

        Returns:
            List of attribution summaries
        """
        # Query tool run events with attribution_touches
        result = await self._db.execute(
            select(ToolRunEvent)
            .where(
                and_(
                    ToolRunEvent.user_id == user_id,
                    ToolRunEvent.created_at >= start_dt,
                    ToolRunEvent.created_at <= end_dt,
                )
            )
        )

        # Aggregate by touchpoint type
        type_totals: Dict[str, Dict[str, Any]] = {}

        for event in result.scalars():
            touches = event.attribution_touches if hasattr(event, 'attribution_touches') else []
            if not touches:
                touches = [{"type": "direct", "weight": 1.0}]

            credits = event.credits_charged - event.credits_refunded
            total_weight = sum(t.get("weight", 1.0) for t in touches)

            for touch in touches:
                tp_type = touch.get("type", "direct")
                weight = touch.get("weight", 1.0)
                attributed = int(credits * weight / total_weight) if total_weight > 0 else 0

                if tp_type not in type_totals:
                    type_totals[tp_type] = {"type": tp_type, "count": 0, "revenue": 0}
                type_totals[tp_type]["count"] += 1
                type_totals[tp_type]["revenue"] += attributed

        return list(type_totals.values())
