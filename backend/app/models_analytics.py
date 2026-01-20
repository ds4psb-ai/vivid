"""Analytics DB Models for Phase 9 Monetization & Analytics.

Tracks revenue attribution, engagement funnels, retention cohorts,
pricing experiments, leaderboards, and real-time KPIs.
"""
import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from sqlalchemy import String, DateTime, Integer, Float, Text, Index, Date, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class ExperimentStatus(str, enum.Enum):
    """Pricing experiment status."""
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LeaderboardType(str, enum.Enum):
    """Leaderboard types."""
    CREATOR_REVENUE = "creator_revenue"
    TOOL_USAGE = "tool_usage"
    FORK_CONTRIBUTION = "fork_contribution"
    ENGAGEMENT_SCORE = "engagement_score"


class CohortType(str, enum.Enum):
    """Cohort definition types."""
    SIGNUP = "signup"
    FIRST_PURCHASE = "first_purchase"
    FIRST_TOOL = "first_tool"
    FIRST_CREATION = "first_creation"


class PeriodType(str, enum.Enum):
    """Period aggregation types."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"


# =============================================================================
# User Revenue Metrics - Daily Snapshots
# =============================================================================

class UserRevenueMetrics(Base):
    """Daily revenue snapshot for a user.

    Aggregates all revenue-related metrics for analytics dashboards.
    Pre-computed daily to enable fast queries.
    """
    __tablename__ = "user_revenue_metrics"
    __table_args__ = (
        Index("ix_user_revenue_user_date", "user_id", "snapshot_date", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Revenue totals
    total_revenue_credits: Mapped[int] = mapped_column(Integer, default=0)
    tool_revenue_breakdown: Mapped[dict] = mapped_column(JSONB, default=dict)  # {tool_key: credits}
    dimension_revenue_breakdown: Mapped[dict] = mapped_column(JSONB, default=dict)  # {dimension: credits}

    # Fork revenue
    fork_revenue_received: Mapped[int] = mapped_column(Integer, default=0)  # Credits received from forks
    fork_revenue_shared: Mapped[int] = mapped_column(Integer, default=0)  # Credits shared to ancestors

    # Attribution data
    attribution_scores: Mapped[list] = mapped_column(JSONB, default=list)  # [{touchpoint, weight, revenue_attributed}]

    # Execution metrics
    total_executions: Mapped[int] = mapped_column(Integer, default=0)
    successful_executions: Mapped[int] = mapped_column(Integer, default=0)
    avg_latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# =============================================================================
# Engagement Funnel Events
# =============================================================================

class EngagementFunnelEvent(Base):
    """Tracks user progression through conversion funnels.

    Enables funnel analysis with drop-off detection.
    """
    __tablename__ = "engagement_funnel_events"
    __table_args__ = (
        Index("ix_funnel_user_created", "user_id", "created_at"),
        Index("ix_funnel_name_step", "funnel_name", "step_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Funnel definition
    funnel_name: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., "onboarding", "first_tool_run"
    step_name: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., "signup", "profile_complete"
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Step metrics
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    time_in_step_ms: Mapped[int] = mapped_column(Integer, default=0)
    drop_off_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Context
    context: Mapped[dict] = mapped_column(JSONB, default=dict)  # {page: "...", referrer: "...", device: "..."}

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# =============================================================================
# Retention Cohort Snapshots
# =============================================================================

class RetentionCohortSnapshot(Base):
    """Pre-computed retention cohort data.

    Enables cohort analysis with retention matrices.
    """
    __tablename__ = "retention_cohort_snapshots"
    __table_args__ = (
        Index("ix_cohort_date_type", "cohort_date", "cohort_type"),
        Index("ix_cohort_type_period", "cohort_type", "period_type", "period_offset"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Cohort definition
    cohort_date: Mapped[date] = mapped_column(Date, nullable=False)  # When cohort was formed
    cohort_type: Mapped[str] = mapped_column(String(32), nullable=False)  # signup, first_purchase
    period_type: Mapped[str] = mapped_column(String(16), nullable=False)  # daily, weekly, monthly
    period_offset: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=same period, 1=next period, etc.

    # Retention metrics
    cohort_size: Mapped[int] = mapped_column(Integer, nullable=False)
    retained_count: Mapped[int] = mapped_column(Integer, nullable=False)
    retention_rate: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 1.0

    # Revenue metrics
    revenue_per_user: Mapped[float] = mapped_column(Float, default=0.0)
    dimension_breakdown: Mapped[dict] = mapped_column(JSONB, default=dict)  # {dimension: {count, revenue}}

    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# =============================================================================
# Pricing Experiments
# =============================================================================

class PricingExperiment(Base):
    """A/B pricing experiment configuration.

    Supports multi-variant testing with statistical significance tracking.
    """
    __tablename__ = "pricing_experiments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    tool_key: Mapped[Optional[str]] = mapped_column(String(160), nullable=True, index=True)  # None = global

    # Experiment status
    status: Mapped[str] = mapped_column(String(20), default=ExperimentStatus.DRAFT.value)

    # Variants configuration
    # [{"name": "control", "price_multiplier": 1.0, "weight": 0.5}, {"name": "high", "price_multiplier": 1.2, "weight": 0.5}]
    variants: Mapped[list] = mapped_column(JSONB, nullable=False)
    winning_variant: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Statistical parameters
    min_sample_size: Mapped[int] = mapped_column(Integer, default=100)
    confidence_level: Mapped[float] = mapped_column(Float, default=0.95)

    # Time bounds
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignments: Mapped[List["PricingExperimentAssignment"]] = relationship(
        "PricingExperimentAssignment",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )


class PricingExperimentAssignment(Base):
    """User assignment to a pricing experiment variant.

    Ensures deterministic variant assignment per user.
    """
    __tablename__ = "pricing_experiment_assignments"
    __table_args__ = (
        Index("ix_experiment_assignment_exp_user", "experiment_id", "user_id", unique=True),
        Index("ix_experiment_assignment_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pricing_experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(String(160), nullable=False)
    variant_name: Mapped[str] = mapped_column(String(64), nullable=False)
    price_multiplier: Mapped[float] = mapped_column(Float, nullable=False)

    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    experiment: Mapped["PricingExperiment"] = relationship(
        "PricingExperiment",
        back_populates="assignments",
    )


# =============================================================================
# Leaderboard Snapshots
# =============================================================================

class LeaderboardSnapshot(Base):
    """Pre-computed leaderboard rankings.

    Enables fast leaderboard queries without real-time aggregation.
    """
    __tablename__ = "leaderboard_snapshots"
    __table_args__ = (
        Index("ix_leaderboard_type_period", "leaderboard_type", "period_date"),
        Index("ix_leaderboard_scope", "scope", "scope_value", "period_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Leaderboard definition
    leaderboard_type: Mapped[str] = mapped_column(String(32), nullable=False)  # creator_revenue, tool_usage
    scope: Mapped[str] = mapped_column(String(32), nullable=False)  # global, dimension, category
    scope_value: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # dimension or category name

    # Time period
    period_type: Mapped[str] = mapped_column(String(16), nullable=False)  # daily, weekly, monthly, all_time
    period_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Rankings
    # [{"rank": 1, "user_id": "...", "display_name": "...", "score": 1000, "delta": 2}, ...]
    rankings: Mapped[list] = mapped_column(JSONB, nullable=False)

    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# =============================================================================
# Real-time KPI Cache
# =============================================================================

class RealTimeKPICache(Base):
    """Cached KPI values for real-time dashboard updates.

    TTL-based cache for frequently accessed KPIs.
    """
    __tablename__ = "real_time_kpi_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kpi_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    kpi_value: Mapped[float] = mapped_column(Float, nullable=False)
    kpi_meta: Mapped[dict] = mapped_column(JSONB, default=dict)  # {unit: "credits", trend: "up", delta_pct: 5.2}
    ttl_seconds: Mapped[int] = mapped_column(Integer, default=300)  # 5 minutes default

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    @property
    def is_expired(self) -> bool:
        """Check if KPI value has expired."""
        from datetime import timezone
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        age_seconds = (now - self.updated_at).total_seconds()
        return age_seconds > self.ttl_seconds
