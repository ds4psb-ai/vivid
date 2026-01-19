"""Remove workflow_session_id from ip_generations.

Revision ID: 023_remove_workflow_session_id
Revises: 022_add_ip_evidence_tables
Create Date: 2026-01-19
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "023_remove_workflow_session_id"
down_revision = "022_add_ip_evidence_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("ip_generations", "workflow_session_id")


def downgrade() -> None:
    op.add_column(
        "ip_generations",
        sa.Column("workflow_session_id", sa.String(160), nullable=True),
    )
