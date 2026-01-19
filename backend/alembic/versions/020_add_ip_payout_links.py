"""Add workflow preset metadata and payout generation links.

Revision ID: 020_add_ip_payout_links
Revises: 019_add_ip_payout_ledger
Create Date: 2026-01-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "020_add_ip_payout_links"
down_revision = "019_add_ip_payout_ledger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ip_workflow_presets",
        sa.Column("workflow_capsule_id", sa.String(160), nullable=True),
    )
    op.add_column(
        "ip_workflow_presets",
        sa.Column("pattern_version", sa.String(32), nullable=True),
    )

    op.add_column(
        "ip_payout_ledger",
        sa.Column("generation_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_ip_payout_ledger_generation",
        "ip_payout_ledger",
        "ip_generations",
        ["generation_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_ip_payout_ledger_generation_id",
        "ip_payout_ledger",
        ["generation_id"],
    )
    op.create_unique_constraint(
        "uq_ip_payout_ledger_generation_id",
        "ip_payout_ledger",
        ["generation_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_ip_payout_ledger_generation_id",
        "ip_payout_ledger",
        type_="unique",
    )
    op.drop_index("ix_ip_payout_ledger_generation_id", table_name="ip_payout_ledger")
    op.drop_constraint(
        "fk_ip_payout_ledger_generation",
        "ip_payout_ledger",
        type_="foreignkey",
    )
    op.drop_column("ip_payout_ledger", "generation_id")

    op.drop_column("ip_workflow_presets", "pattern_version")
    op.drop_column("ip_workflow_presets", "workflow_capsule_id")
