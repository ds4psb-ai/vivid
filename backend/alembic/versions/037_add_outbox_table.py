"""Add outbox table for Transactional Outbox pattern.

Revision ID: 037_add_outbox
Revises: 036_add_user_id_to_capsule_runs
Create Date: 2026-01-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "037_add_outbox"
down_revision = "036_add_user_id_capsule"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create outbox table."""
    op.create_table(
        "outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(50), nullable=False, index=True),
        sa.Column("aggregate_type", sa.String(50), nullable=True),
        sa.Column("aggregate_id", sa.String(64), nullable=True),
        sa.Column("payload", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer, nullable=False, server_default="3"),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("published_at", sa.DateTime, nullable=True),
        sa.Column("scheduled_at", sa.DateTime, nullable=True, server_default=sa.func.now()),
    )

    # Composite indexes for efficient querying
    op.create_index(
        "ix_outbox_status_created",
        "outbox",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_outbox_scheduled",
        "outbox",
        ["scheduled_at"],
    )
    op.create_index(
        "ix_outbox_aggregate",
        "outbox",
        ["aggregate_type", "aggregate_id"],
    )


def downgrade() -> None:
    """Drop outbox table."""
    op.drop_index("ix_outbox_aggregate", table_name="outbox")
    op.drop_index("ix_outbox_scheduled", table_name="outbox")
    op.drop_index("ix_outbox_status_created", table_name="outbox")
    op.drop_table("outbox")
