"""Add pipeline_results table for feedback and improvement tracking.

Revision ID: 039_add_pipeline_feedback
Revises: 038_add_logic_vector_versions
Create Date: 2026-01-28

Stores pipeline execution results with user feedback for:
- Success/failure pattern analysis
- User rating collection
- Automated improvement triggers
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "039_add_pipeline_feedback"
down_revision = "038_add_logic_vector_versions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create pipeline_results table."""
    op.create_table(
        "pipeline_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trace_id", sa.String(64), nullable=False, index=True),
        sa.Column("user_id", sa.String(160), nullable=False, index=True),

        # Pipeline config
        sa.Column("pipeline_type", sa.String(50), nullable=False, server_default="dna_lab"),
        sa.Column("steps_requested", postgresql.ARRAY(sa.String), nullable=False),
        sa.Column("steps_completed", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),

        # Result data
        sa.Column("dna_result", postgresql.JSONB, nullable=True),
        sa.Column("success", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("partial_success", sa.Boolean, nullable=False, server_default="false"),

        # Error tracking
        sa.Column("failure_step", sa.String(50), nullable=True),
        sa.Column("failure_reason", sa.String(500), nullable=True),
        sa.Column("error_category", sa.String(50), nullable=True),  # timeout, validation, api_error, etc.

        # User feedback
        sa.Column("user_rating", sa.Integer, nullable=True),  # 1-5 stars
        sa.Column("user_feedback", sa.Text, nullable=True),
        sa.Column("feedback_tags", postgresql.ARRAY(sa.String), nullable=True),

        # Performance metrics
        sa.Column("processing_time_ms", sa.Integer, nullable=True),
        sa.Column("credits_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("credits_refunded", sa.Integer, nullable=False, server_default="0"),

        # Analysis flags
        sa.Column("analyzed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("pattern_detected", sa.String(100), nullable=True),
        sa.Column("improvement_applied", sa.Boolean, nullable=False, server_default="false"),

        # Timestamps
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("feedback_at", sa.DateTime, nullable=True),
        sa.Column("analyzed_at", sa.DateTime, nullable=True),
    )

    # Index for failure analysis
    op.create_index(
        "ix_pipeline_results_failure",
        "pipeline_results",
        ["success", "failure_step", "error_category"],
    )

    # Index for feedback analysis
    op.create_index(
        "ix_pipeline_results_rating",
        "pipeline_results",
        ["user_rating", "created_at"],
    )

    # Index for pattern detection
    op.create_index(
        "ix_pipeline_results_analyzed",
        "pipeline_results",
        ["analyzed", "created_at"],
    )


def downgrade() -> None:
    """Drop pipeline_results table."""
    op.drop_index("ix_pipeline_results_analyzed", table_name="pipeline_results")
    op.drop_index("ix_pipeline_results_rating", table_name="pipeline_results")
    op.drop_index("ix_pipeline_results_failure", table_name="pipeline_results")
    op.drop_table("pipeline_results")
