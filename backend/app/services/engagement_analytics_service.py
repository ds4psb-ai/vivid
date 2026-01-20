"""Engagement Analytics Service (Phase 9 Monetization & Analytics).

RFM-based engagement scoring and funnel tracking.

2026 Best Practices:
- RFM Model: Recency, Frequency, Monetary for engagement scoring
- Funnel Analysis: Conversion tracking with drop-off detection
- Cohort Retention: Weekly/monthly retention matrices

Usage:
    from app.services.engagement_analytics_service import EngagementAnalyticsService

    service = EngagementAnalyticsService(db)
    score = await service.compute_engagement_score(user_id)
    funnel = await service.analyze_funnel("onboarding", start_date, end_date)
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, func, and_, desc, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_analytics import (
    EngagementFunnelEvent,
    RetentionCohortSnapshot,
    CohortType,
    PeriodType,
)
from app.models_telemetry import ToolRunEvent
from app.models_personalization import UserInteractionSignal

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# RFM weights for engagement score
RFM_WEIGHTS = {
    "recency": 0.35,     # Days since last activity (lower = better)
    "frequency": 0.30,   # Activity count in 30-day window
    "monetary": 0.25,    # Credits spent
    "depth": 0.10,       # Feature penetration (unique features used)
}

# Engagement score thresholds
ENGAGEMENT_TIERS = {
    "champion": 80,      # 80-100
    "loyal": 60,         # 60-79
    "potential": 40,     # 40-59
    "at_risk": 20,       # 20-39
    "hibernating": 0,    # 0-19
}

# Standard funnel definitions
FUNNEL_DEFINITIONS = {
    "onboarding": [
        {"name": "signup", "order": 1},
        {"name": "profile_complete", "order": 2},
        {"name": "first_tool_view", "order": 3},
        {"name": "first_tool_run", "order": 4},
        {"name": "first_success", "order": 5},
    ],
    "tool_discovery": [
        {"name": "search", "order": 1},
        {"name": "tool_view", "order": 2},
        {"name": "tool_run", "order": 3},
        {"name": "tool_complete", "order": 4},
        {"name": "tool_rate", "order": 5},
    ],
    "creator_journey": [
        {"name": "view_creator_hub", "order": 1},
        {"name": "start_tool_creation", "order": 2},
        {"name": "submit_tool", "order": 3},
        {"name": "tool_approved", "order": 4},
        {"name": "first_revenue", "order": 5},
    ],
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class EngagementScore:
    """User engagement score with component breakdown."""
    user_id: str
    total_score: float  # 0-100
    tier: str  # champion, loyal, potential, at_risk, hibernating
    recency_score: float
    frequency_score: float
    monetary_score: float
    depth_score: float
    last_activity: Optional[datetime]
    computed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FunnelStep:
    """Funnel step metrics."""
    step_name: str
    step_order: int
    users_entered: int
    users_completed: int
    conversion_rate: float  # 0-1
    drop_off_rate: float  # 0-1
    avg_time_in_step_ms: float
    top_drop_off_reasons: List[Dict[str, Any]]


@dataclass
class FunnelAnalysis:
    """Complete funnel analysis."""
    funnel_name: str
    period_start: date
    period_end: date
    total_users_started: int
    total_users_completed: int
    overall_conversion_rate: float
    steps: List[FunnelStep]
    bottleneck_step: Optional[str]  # Step with highest drop-off


@dataclass
class CohortSnapshot:
    """Retention cohort snapshot."""
    cohort_date: date
    cohort_type: str
    period_type: str
    period_offset: int
    cohort_size: int
    retained_count: int
    retention_rate: float
    revenue_per_user: float


# =============================================================================
# Engagement Analytics Service
# =============================================================================

class EngagementAnalyticsService:
    """RFM-based engagement scoring and funnel tracking.

    Features:
    - Real-time engagement score computation
    - Funnel conversion analysis
    - Retention cohort computation

    Attributes:
        db: Async database session
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize engagement analytics service.

        Args:
            db: Async database session
        """
        self._db = db
        self._score_cache: Dict[str, Tuple[EngagementScore, datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)

    async def compute_engagement_score(
        self,
        user_id: str,
        use_cache: bool = True,
    ) -> EngagementScore:
        """Compute real-time engagement score (0-100).

        Uses RFM model:
        - Recency: Days since last activity
        - Frequency: Activity count in 30-day window
        - Monetary: Credits spent
        - Depth: Feature penetration

        Args:
            user_id: User ID
            use_cache: Whether to use cached score

        Returns:
            EngagementScore: Computed score with breakdown
        """
        # Check cache
        if use_cache and user_id in self._score_cache:
            cached_score, cached_at = self._score_cache[user_id]
            if datetime.utcnow() - cached_at < self._cache_ttl:
                return cached_score

        now = datetime.utcnow()
        window_30d = now - timedelta(days=30)

        # 1. Recency: Days since last activity (0-100, lower days = higher score)
        recency_score, last_activity = await self._compute_recency_score(user_id, now)

        # 2. Frequency: Activity count in 30-day window
        frequency_score = await self._compute_frequency_score(user_id, window_30d, now)

        # 3. Monetary: Credits spent
        monetary_score = await self._compute_monetary_score(user_id, window_30d, now)

        # 4. Depth: Feature penetration
        depth_score = await self._compute_depth_score(user_id, window_30d, now)

        # Calculate weighted total
        total_score = (
            recency_score * RFM_WEIGHTS["recency"]
            + frequency_score * RFM_WEIGHTS["frequency"]
            + monetary_score * RFM_WEIGHTS["monetary"]
            + depth_score * RFM_WEIGHTS["depth"]
        )

        # Determine tier
        tier = self._determine_tier(total_score)

        score = EngagementScore(
            user_id=user_id,
            total_score=round(total_score, 2),
            tier=tier,
            recency_score=round(recency_score, 2),
            frequency_score=round(frequency_score, 2),
            monetary_score=round(monetary_score, 2),
            depth_score=round(depth_score, 2),
            last_activity=last_activity,
            computed_at=now,
        )

        # Update cache
        self._score_cache[user_id] = (score, now)

        return score

    async def record_funnel_event(
        self,
        user_id: str,
        session_id: str,
        funnel_name: str,
        step_name: str,
        step_order: int,
        completed: bool = True,
        time_in_step_ms: int = 0,
        drop_off_reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> uuid.UUID:
        """Record funnel step event.

        Args:
            user_id: User ID
            session_id: Session ID
            funnel_name: Name of the funnel
            step_name: Name of the step
            step_order: Order in the funnel (1-based)
            completed: Whether step was completed
            time_in_step_ms: Time spent in step
            drop_off_reason: Reason for drop-off (if not completed)
            context: Additional context

        Returns:
            UUID: Created event ID
        """
        event = EngagementFunnelEvent(
            user_id=user_id,
            session_id=session_id,
            funnel_name=funnel_name,
            step_name=step_name,
            step_order=step_order,
            completed=completed,
            time_in_step_ms=time_in_step_ms,
            drop_off_reason=drop_off_reason,
            context=context or {},
        )

        self._db.add(event)
        await self._db.flush()

        return event.id

    async def analyze_funnel(
        self,
        funnel_name: str,
        start_date: date,
        end_date: date,
    ) -> FunnelAnalysis:
        """Analyze funnel conversion rates.

        Args:
            funnel_name: Name of the funnel to analyze
            start_date: Start date
            end_date: End date

        Returns:
            FunnelAnalysis: Complete funnel analysis
        """
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        # Get funnel definition
        funnel_def = FUNNEL_DEFINITIONS.get(funnel_name)
        if not funnel_def:
            funnel_def = [{"name": "step_1", "order": 1}]  # Default

        # Query all events for this funnel
        result = await self._db.execute(
            select(EngagementFunnelEvent)
            .where(
                and_(
                    EngagementFunnelEvent.funnel_name == funnel_name,
                    EngagementFunnelEvent.created_at >= start_dt,
                    EngagementFunnelEvent.created_at <= end_dt,
                )
            )
            .order_by(EngagementFunnelEvent.step_order)
        )
        events = list(result.scalars())

        # Group by step
        step_metrics: Dict[int, Dict[str, Any]] = {}
        user_progress: Dict[str, int] = {}  # user_id -> max completed step

        for event in events:
            step = event.step_order
            if step not in step_metrics:
                step_metrics[step] = {
                    "step_name": event.step_name,
                    "users_entered": set(),
                    "users_completed": set(),
                    "times": [],
                    "drop_off_reasons": [],
                }

            step_metrics[step]["users_entered"].add(event.user_id)
            if event.completed:
                step_metrics[step]["users_completed"].add(event.user_id)
                user_progress[event.user_id] = max(
                    user_progress.get(event.user_id, 0), step
                )
            if event.time_in_step_ms:
                step_metrics[step]["times"].append(event.time_in_step_ms)
            if event.drop_off_reason:
                step_metrics[step]["drop_off_reasons"].append(event.drop_off_reason)

        # Calculate step metrics
        steps: List[FunnelStep] = []
        prev_completed = None
        bottleneck_step = None
        max_drop_off = 0.0

        for step_def in funnel_def:
            order = step_def["order"]
            name = step_def["name"]

            if order in step_metrics:
                metrics = step_metrics[order]
                entered = len(metrics["users_entered"])
                completed = len(metrics["users_completed"])

                # Conversion rate
                conv_rate = completed / entered if entered > 0 else 0.0

                # Drop-off rate (from previous step)
                if prev_completed is not None and prev_completed > 0:
                    drop_off = 1.0 - (entered / prev_completed)
                else:
                    drop_off = 0.0

                # Track bottleneck
                if drop_off > max_drop_off:
                    max_drop_off = drop_off
                    bottleneck_step = name

                # Avg time
                avg_time = (
                    sum(metrics["times"]) / len(metrics["times"])
                    if metrics["times"]
                    else 0.0
                )

                # Top drop-off reasons
                reason_counts: Dict[str, int] = {}
                for reason in metrics["drop_off_reasons"]:
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
                top_reasons = sorted(
                    [{"reason": r, "count": c} for r, c in reason_counts.items()],
                    key=lambda x: x["count"],
                    reverse=True,
                )[:5]

                steps.append(
                    FunnelStep(
                        step_name=name,
                        step_order=order,
                        users_entered=entered,
                        users_completed=completed,
                        conversion_rate=round(conv_rate, 4),
                        drop_off_rate=round(drop_off, 4),
                        avg_time_in_step_ms=round(avg_time, 2),
                        top_drop_off_reasons=top_reasons,
                    )
                )
                prev_completed = completed
            else:
                # No data for this step
                steps.append(
                    FunnelStep(
                        step_name=name,
                        step_order=order,
                        users_entered=0,
                        users_completed=0,
                        conversion_rate=0.0,
                        drop_off_rate=0.0,
                        avg_time_in_step_ms=0.0,
                        top_drop_off_reasons=[],
                    )
                )

        # Overall metrics
        total_started = steps[0].users_entered if steps else 0
        total_completed = steps[-1].users_completed if steps else 0
        overall_rate = total_completed / total_started if total_started > 0 else 0.0

        return FunnelAnalysis(
            funnel_name=funnel_name,
            period_start=start_date,
            period_end=end_date,
            total_users_started=total_started,
            total_users_completed=total_completed,
            overall_conversion_rate=round(overall_rate, 4),
            steps=steps,
            bottleneck_step=bottleneck_step,
        )

    async def compute_retention_cohorts(
        self,
        cohort_type: str,
        period_type: str,
        lookback_periods: int = 12,
    ) -> List[CohortSnapshot]:
        """Compute retention cohort matrix.

        Args:
            cohort_type: Type of cohort (signup, first_purchase, first_tool)
            period_type: Period granularity (daily, weekly, monthly)
            lookback_periods: Number of periods to look back

        Returns:
            List[CohortSnapshot]: Cohort retention data
        """
        now = datetime.utcnow()
        snapshots: List[CohortSnapshot] = []

        # Calculate period length
        if period_type == "daily":
            period_delta = timedelta(days=1)
        elif period_type == "weekly":
            period_delta = timedelta(weeks=1)
        else:  # monthly
            period_delta = timedelta(days=30)

        # For each cohort period
        for cohort_offset in range(lookback_periods):
            cohort_start = now - period_delta * (cohort_offset + 1)
            cohort_end = now - period_delta * cohort_offset

            # Get users in this cohort
            cohort_users = await self._get_cohort_users(
                cohort_type, cohort_start, cohort_end
            )
            cohort_size = len(cohort_users)

            if cohort_size == 0:
                continue

            # For each retention period
            for retention_offset in range(cohort_offset + 1):
                retention_start = cohort_end + period_delta * retention_offset
                retention_end = cohort_end + period_delta * (retention_offset + 1)

                if retention_end > now:
                    break

                # Count retained users
                retained = await self._count_active_users(
                    cohort_users, retention_start, retention_end
                )

                # Calculate revenue per user
                revenue = await self._get_cohort_revenue(
                    cohort_users, retention_start, retention_end
                )
                rpu = revenue / len(cohort_users) if cohort_users else 0.0

                snapshots.append(
                    CohortSnapshot(
                        cohort_date=cohort_start.date(),
                        cohort_type=cohort_type,
                        period_type=period_type,
                        period_offset=retention_offset,
                        cohort_size=cohort_size,
                        retained_count=retained,
                        retention_rate=round(retained / cohort_size, 4) if cohort_size > 0 else 0,
                        revenue_per_user=round(rpu, 2),
                    )
                )

        return snapshots

    async def save_retention_cohort(
        self,
        snapshot: CohortSnapshot,
    ) -> RetentionCohortSnapshot:
        """Save retention cohort snapshot to database.

        Args:
            snapshot: Snapshot to save

        Returns:
            RetentionCohortSnapshot: Saved model
        """
        model = RetentionCohortSnapshot(
            cohort_date=snapshot.cohort_date,
            cohort_type=snapshot.cohort_type,
            period_type=snapshot.period_type,
            period_offset=snapshot.period_offset,
            cohort_size=snapshot.cohort_size,
            retained_count=snapshot.retained_count,
            retention_rate=snapshot.retention_rate,
            revenue_per_user=snapshot.revenue_per_user,
        )

        self._db.add(model)
        await self._db.flush()

        return model

    async def get_engagement_distribution(
        self,
        period_days: int = 30,
    ) -> Dict[str, int]:
        """Get distribution of users by engagement tier.

        Args:
            period_days: Days to consider for activity

        Returns:
            Dict mapping tier to user count
        """
        # This would normally query all users and compute scores
        # For performance, we'd use pre-computed scores or sampling

        # Simulated distribution
        return {
            "champion": 150,
            "loyal": 450,
            "potential": 800,
            "at_risk": 400,
            "hibernating": 200,
        }

    # =========================================================================
    # Score Computation Methods
    # =========================================================================

    async def _compute_recency_score(
        self,
        user_id: str,
        now: datetime,
    ) -> Tuple[float, Optional[datetime]]:
        """Compute recency score (0-100).

        Lower days since activity = higher score.
        """
        # Get last activity from tool runs
        result = await self._db.execute(
            select(ToolRunEvent.created_at)
            .where(ToolRunEvent.user_id == user_id)
            .order_by(desc(ToolRunEvent.created_at))
            .limit(1)
        )
        last_run = result.scalar_one_or_none()

        # Also check interaction signals
        signal_result = await self._db.execute(
            select(UserInteractionSignal.created_at)
            .where(UserInteractionSignal.user_id == user_id)
            .order_by(desc(UserInteractionSignal.created_at))
            .limit(1)
        )
        last_signal = signal_result.scalar_one_or_none()

        # Use most recent activity
        last_activity = None
        if last_run and last_signal:
            last_activity = max(last_run, last_signal)
        elif last_run:
            last_activity = last_run
        elif last_signal:
            last_activity = last_signal

        if not last_activity:
            return 0.0, None

        days_since = (now - last_activity).days

        # Score: 100 for same day, decays to 0 at 30+ days
        if days_since == 0:
            score = 100.0
        elif days_since >= 30:
            score = 0.0
        else:
            score = 100.0 * (1 - days_since / 30)

        return score, last_activity

    async def _compute_frequency_score(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> float:
        """Compute frequency score (0-100).

        Higher activity count = higher score.
        """
        # Count tool runs
        run_count = await self._db.execute(
            select(func.count())
            .where(
                and_(
                    ToolRunEvent.user_id == user_id,
                    ToolRunEvent.created_at >= start,
                    ToolRunEvent.created_at <= end,
                )
            )
        )
        count = run_count.scalar() or 0

        # Score: 100 for 30+ activities in 30 days (1/day avg)
        # Linear scale up to that point
        score = min(100.0, (count / 30) * 100)

        return score

    async def _compute_monetary_score(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> float:
        """Compute monetary score (0-100).

        Higher credits spent = higher score.
        """
        result = await self._db.execute(
            select(func.sum(ToolRunEvent.credits_charged - ToolRunEvent.credits_refunded))
            .where(
                and_(
                    ToolRunEvent.user_id == user_id,
                    ToolRunEvent.created_at >= start,
                    ToolRunEvent.created_at <= end,
                )
            )
        )
        credits_spent = result.scalar() or 0

        # Score: 100 for 1000+ credits spent
        score = min(100.0, (credits_spent / 1000) * 100)

        return score

    async def _compute_depth_score(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> float:
        """Compute depth score (0-100).

        More unique features used = higher score.
        """
        # Count unique tool keys used
        result = await self._db.execute(
            select(func.count(distinct(ToolRunEvent.tool_key)))
            .where(
                and_(
                    ToolRunEvent.user_id == user_id,
                    ToolRunEvent.created_at >= start,
                    ToolRunEvent.created_at <= end,
                )
            )
        )
        unique_tools = result.scalar() or 0

        # Score: 100 for 10+ unique tools
        score = min(100.0, (unique_tools / 10) * 100)

        return score

    def _determine_tier(self, score: float) -> str:
        """Determine engagement tier from score."""
        for tier, threshold in sorted(ENGAGEMENT_TIERS.items(), key=lambda x: x[1], reverse=True):
            if score >= threshold:
                return tier
        return "hibernating"

    # =========================================================================
    # Cohort Helper Methods
    # =========================================================================

    async def _get_cohort_users(
        self,
        cohort_type: str,
        start: datetime,
        end: datetime,
    ) -> List[str]:
        """Get users in a cohort period.

        Args:
            cohort_type: Type of cohort
            start: Cohort start time
            end: Cohort end time

        Returns:
            List of user IDs
        """
        if cohort_type == "first_tool":
            # Users who ran their first tool in this period
            result = await self._db.execute(
                select(ToolRunEvent.user_id)
                .where(
                    and_(
                        ToolRunEvent.created_at >= start,
                        ToolRunEvent.created_at < end,
                    )
                )
                .group_by(ToolRunEvent.user_id)
                .having(func.min(ToolRunEvent.created_at) >= start)
            )
            return [row[0] for row in result if row[0]]
        else:
            # Default: all active users in period
            result = await self._db.execute(
                select(distinct(ToolRunEvent.user_id))
                .where(
                    and_(
                        ToolRunEvent.created_at >= start,
                        ToolRunEvent.created_at < end,
                        ToolRunEvent.user_id.isnot(None),
                    )
                )
            )
            return [row[0] for row in result if row[0]]

    async def _count_active_users(
        self,
        user_ids: List[str],
        start: datetime,
        end: datetime,
    ) -> int:
        """Count active users in a period.

        Args:
            user_ids: Users to check
            start: Period start
            end: Period end

        Returns:
            Count of active users
        """
        if not user_ids:
            return 0

        result = await self._db.execute(
            select(func.count(distinct(ToolRunEvent.user_id)))
            .where(
                and_(
                    ToolRunEvent.user_id.in_(user_ids),
                    ToolRunEvent.created_at >= start,
                    ToolRunEvent.created_at < end,
                )
            )
        )
        return result.scalar() or 0

    async def _get_cohort_revenue(
        self,
        user_ids: List[str],
        start: datetime,
        end: datetime,
    ) -> float:
        """Get total revenue for a cohort in a period.

        Args:
            user_ids: Users to check
            start: Period start
            end: Period end

        Returns:
            Total credits spent
        """
        if not user_ids:
            return 0.0

        result = await self._db.execute(
            select(func.sum(ToolRunEvent.credits_charged - ToolRunEvent.credits_refunded))
            .where(
                and_(
                    ToolRunEvent.user_id.in_(user_ids),
                    ToolRunEvent.created_at >= start,
                    ToolRunEvent.created_at < end,
                )
            )
        )
        return float(result.scalar() or 0)
