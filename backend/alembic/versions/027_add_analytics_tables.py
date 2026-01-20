"""Phase 9: Monetization & Analytics tables.

Revenue Attribution + Engagement Analytics + Dynamic Pricing.

Revision ID: 027_add_analytics_tables
Revises: 026_personalization
Create Date: 2026-01-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "027_add_analytics_tables"
down_revision: Union[str, None] = "026_personalization"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create analytics tables for Phase 9."""

    # ==========================================================================
    # User Revenue Metrics (Daily Snapshots)
    # ==========================================================================
    op.create_table(
        "user_revenue_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(160), nullable=False, index=True),
        sa.Column("snapshot_date", sa.Date, nullable=False),
        sa.Column("total_revenue_credits", sa.Integer, server_default="0"),
        sa.Column("tool_revenue_breakdown", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("dimension_revenue_breakdown", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("fork_revenue_received", sa.Integer, server_default="0"),
        sa.Column("fork_revenue_shared", sa.Integer, server_default="0"),
        sa.Column("attribution_scores", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("total_executions", sa.Integer, server_default="0"),
        sa.Column("successful_executions", sa.Integer, server_default="0"),
        sa.Column("avg_latency_ms", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_user_revenue_user_date",
        "user_revenue_metrics",
        ["user_id", "snapshot_date"],
        unique=True,
    )

    # ==========================================================================
    # Engagement Funnel Events
    # ==========================================================================
    op.create_table(
        "engagement_funnel_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(160), nullable=False, index=True),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("funnel_name", sa.String(64), nullable=False),
        sa.Column("step_name", sa.String(64), nullable=False),
        sa.Column("step_order", sa.Integer, nullable=False),
        sa.Column("completed", sa.Boolean, server_default="false"),
        sa.Column("time_in_step_ms", sa.Integer, server_default="0"),
        sa.Column("drop_off_reason", sa.String(200), nullable=True),
        sa.Column("context", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_funnel_user_created",
        "engagement_funnel_events",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_funnel_name_step",
        "engagement_funnel_events",
        ["funnel_name", "step_order"],
    )

    # ==========================================================================
    # Retention Cohort Snapshots
    # ==========================================================================
    op.create_table(
        "retention_cohort_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("cohort_date", sa.Date, nullable=False),
        sa.Column("cohort_type", sa.String(32), nullable=False),  # signup, first_purchase, first_tool
        sa.Column("period_type", sa.String(16), nullable=False),  # daily, weekly, monthly
        sa.Column("period_offset", sa.Integer, nullable=False),  # 0, 1, 2, ...
        sa.Column("cohort_size", sa.Integer, nullable=False),
        sa.Column("retained_count", sa.Integer, nullable=False),
        sa.Column("retention_rate", sa.Float, nullable=False),
        sa.Column("revenue_per_user", sa.Float, server_default="0"),
        sa.Column("dimension_breakdown", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("computed_at", sa.DateTime, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_cohort_date_type",
        "retention_cohort_snapshots",
        ["cohort_date", "cohort_type"],
    )
    op.create_index(
        "ix_cohort_type_period",
        "retention_cohort_snapshots",
        ["cohort_type", "period_type", "period_offset"],
    )

    # ==========================================================================
    # Pricing Experiments
    # ==========================================================================
    op.create_table(
        "pricing_experiments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("experiment_name", sa.String(128), unique=True, nullable=False),
        sa.Column("tool_key", sa.String(160), nullable=True, index=True),
        sa.Column("status", sa.String(20), server_default="'draft'"),  # draft, running, completed, cancelled
        sa.Column("variants", postgresql.JSONB, nullable=False),  # [{"name": "control", "price_multiplier": 1.0}, ...]
        sa.Column("winning_variant", sa.String(64), nullable=True),
        sa.Column("min_sample_size", sa.Integer, server_default="100"),
        sa.Column("confidence_level", sa.Float, server_default="0.95"),
        sa.Column("start_at", sa.DateTime, nullable=True),
        sa.Column("end_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()"), onupdate=sa.text("now()")),
    )

    # ==========================================================================
    # Pricing Experiment Assignments
    # ==========================================================================
    op.create_table(
        "pricing_experiment_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pricing_experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(160), nullable=False),
        sa.Column("variant_name", sa.String(64), nullable=False),
        sa.Column("price_multiplier", sa.Float, nullable=False),
        sa.Column("assigned_at", sa.DateTime, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_experiment_assignment_exp_user",
        "pricing_experiment_assignments",
        ["experiment_id", "user_id"],
        unique=True,
    )
    op.create_index(
        "ix_experiment_assignment_user",
        "pricing_experiment_assignments",
        ["user_id"],
    )

    # ==========================================================================
    # Leaderboard Snapshots
    # ==========================================================================
    op.create_table(
        "leaderboard_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("leaderboard_type", sa.String(32), nullable=False),  # creator_revenue, tool_usage, fork_contribution
        sa.Column("scope", sa.String(32), nullable=False),  # global, dimension, category
        sa.Column("scope_value", sa.String(64), nullable=True),  # dimension name or category name
        sa.Column("period_type", sa.String(16), nullable=False),  # daily, weekly, monthly, all_time
        sa.Column("period_date", sa.Date, nullable=False),
        sa.Column("rankings", postgresql.JSONB, nullable=False),  # [{"rank": 1, "user_id": "...", "score": 1000}, ...]
        sa.Column("computed_at", sa.DateTime, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_leaderboard_type_period",
        "leaderboard_snapshots",
        ["leaderboard_type", "period_date"],
    )
    op.create_index(
        "ix_leaderboard_scope",
        "leaderboard_snapshots",
        ["scope", "scope_value", "period_date"],
    )

    # ==========================================================================
    # Real-time KPI Cache
    # ==========================================================================
    op.create_table(
        "real_time_kpi_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("kpi_key", sa.String(128), unique=True, nullable=False),
        sa.Column("kpi_value", sa.Float, nullable=False),
        sa.Column("kpi_meta", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("ttl_seconds", sa.Integer, server_default="300"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()")),
    )

    # ==========================================================================
    # Extend Existing Tables
    # ==========================================================================

    # Add attribution_touches to tool_run_events
    op.add_column(
        "tool_run_events",
        sa.Column("attribution_touches", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
    )

    # Add pricing_tier and dynamic_price_enabled to tool_manifests
    op.add_column(
        "tool_manifests",
        sa.Column("pricing_tier", sa.String(32), server_default="'standard'"),
    )
    op.add_column(
        "tool_manifests",
        sa.Column("dynamic_price_enabled", sa.Boolean, server_default="false"),
    )

    # Add funnel_context to user_interaction_signals
    op.add_column(
        "user_interaction_signals",
        sa.Column("funnel_context", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
    )


def downgrade() -> None:
    """Drop analytics tables."""
    # Drop columns from existing tables
    op.drop_column("user_interaction_signals", "funnel_context")
    op.drop_column("tool_manifests", "dynamic_price_enabled")
    op.drop_column("tool_manifests", "pricing_tier")
    op.drop_column("tool_run_events", "attribution_touches")

    # Drop new tables
    op.drop_table("real_time_kpi_cache")
    op.drop_table("leaderboard_snapshots")
    op.drop_table("pricing_experiment_assignments")
    op.drop_table("pricing_experiments")
    op.drop_table("retention_cohort_snapshots")
    op.drop_table("engagement_funnel_events")
    op.drop_table("user_revenue_metrics")
