"""Add hitl_review_items table for Human-in-the-Loop workflow.

Revision ID: 040_add_hitl_review_items
Revises: 039_add_pipeline_feedback
Create Date: 2026-01-28

Implements 2026 HITL best practices:
- Risk-based oversight (severity levels)
- Async review channels
- Human feedback as training data
- Structured review queues with tracing
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "040_add_hitl_review_items"
down_revision = "039_add_pipeline_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create hitl_review_items table."""
    op.create_table(
        "hitl_review_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),

        # Review type and severity
        sa.Column("review_type", sa.String(50), nullable=False),  # vector_drift, qc_failure, prompt_pattern
        sa.Column("severity", sa.String(20), nullable=False, server_default="medium"),  # low, medium, high, critical

        # Context
        sa.Column("ip_id", sa.String(64), nullable=True),
        sa.Column("trace_id", sa.String(64), nullable=True, index=True),

        # Review data
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("suggested_action", postgresql.JSONB, nullable=True),

        # Workflow
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),  # pending, in_review, approved, rejected
        sa.Column("assigned_to", sa.String(64), nullable=True),

        # Decision
        sa.Column("decision", sa.String(20), nullable=True),  # approve, reject, modify
        sa.Column("decision_by", sa.String(64), nullable=True),
        sa.Column("decision_at", sa.DateTime, nullable=True),
        sa.Column("decision_notes", sa.Text, nullable=True),

        # Auto-apply tracking
        sa.Column("auto_applied", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("applied_at", sa.DateTime, nullable=True),
        sa.Column("apply_result", postgresql.JSONB, nullable=True),

        # Timestamps
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime, nullable=True),
    )

    # Composite indexes
    op.create_index(
        "ix_hitl_status_severity",
        "hitl_review_items",
        ["status", "severity"],
    )
    op.create_index(
        "ix_hitl_review_type",
        "hitl_review_items",
        ["review_type"],
    )
    op.create_index(
        "ix_hitl_assigned_to",
        "hitl_review_items",
        ["assigned_to", "status"],
    )
    op.create_index(
        "ix_hitl_expires_at",
        "hitl_review_items",
        ["expires_at"],
    )


def downgrade() -> None:
    """Drop hitl_review_items table."""
    op.drop_index("ix_hitl_expires_at", table_name="hitl_review_items")
    op.drop_index("ix_hitl_assigned_to", table_name="hitl_review_items")
    op.drop_index("ix_hitl_review_type", table_name="hitl_review_items")
    op.drop_index("ix_hitl_status_severity", table_name="hitl_review_items")
    op.drop_table("hitl_review_items")
