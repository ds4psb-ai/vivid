"""Add IP payout ledger tables.

Revision ID: 019_add_ip_payout_ledger
Revises: 018_add_ip_catalog
Create Date: 2026-01-19

Adds tables for:
- ip_payout_ledger: revenue split + holdback tracking
- ip_payout_disputes: dispute records for payouts
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "019_add_ip_payout_ledger"
down_revision = "018_add_ip_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create IP payout ledger tables."""
    op.create_table(
        "ip_payout_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ip_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ip_catalog.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("creator_id", sa.String(160), nullable=False),
        sa.Column("gross_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ip_owner_share", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("creator_share", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("platform_share", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("holdback_until", sa.DateTime(), nullable=True),
        sa.Column("dispute_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_ip_payout_ledger_ip_id", "ip_payout_ledger", ["ip_id"])
    op.create_index("ix_ip_payout_ledger_creator_id", "ip_payout_ledger", ["creator_id"])
    op.create_index("ix_ip_payout_ledger_status", "ip_payout_ledger", ["status"])
    op.create_index("ix_ip_payout_ledger_holdback_until", "ip_payout_ledger", ["holdback_until"])

    op.create_table(
        "ip_payout_disputes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ledger_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ip_payout_ledger.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("complainant_id", sa.String(160), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("resolved_by", sa.String(160), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_ip_payout_disputes_ledger_id", "ip_payout_disputes", ["ledger_id"])
    op.create_index("ix_ip_payout_disputes_status", "ip_payout_disputes", ["status"])
    op.create_index("ix_ip_payout_disputes_created_at", "ip_payout_disputes", ["created_at"])


def downgrade() -> None:
    """Drop IP payout ledger tables."""
    op.drop_index("ix_ip_payout_disputes_created_at", table_name="ip_payout_disputes")
    op.drop_index("ix_ip_payout_disputes_status", table_name="ip_payout_disputes")
    op.drop_index("ix_ip_payout_disputes_ledger_id", table_name="ip_payout_disputes")
    op.drop_table("ip_payout_disputes")

    op.drop_index("ix_ip_payout_ledger_holdback_until", table_name="ip_payout_ledger")
    op.drop_index("ix_ip_payout_ledger_status", table_name="ip_payout_ledger")
    op.drop_index("ix_ip_payout_ledger_creator_id", table_name="ip_payout_ledger")
    op.drop_index("ix_ip_payout_ledger_ip_id", table_name="ip_payout_ledger")
    op.drop_table("ip_payout_ledger")
