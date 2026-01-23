"""Add persona_priority and persona_source columns to capsule_runs.

Fixes P0-3 Gap: Model defines these columns but DB was missing them.

- persona_priority: Controls persona resolution priority (script | blended | user)
- persona_source: Tracks actual persona source for KPI (script | user | auteur | blended)

Revision ID: 031_add_persona_columns
Revises: 030_extend_rls_policies
Create Date: 2026-01-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "031_add_persona_columns"
down_revision: Union[str, None] = "030_extend_rls_policies"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add persona columns to capsule_runs."""
    # Add persona_priority column
    op.add_column(
        "capsule_runs",
        sa.Column("persona_priority", sa.String(32), nullable=True),
    )

    # Add persona_source column
    op.add_column(
        "capsule_runs",
        sa.Column("persona_source", sa.String(32), nullable=True),
    )

    # Add index for persona_source for KPI queries
    op.create_index(
        "ix_capsule_runs_persona_source",
        "capsule_runs",
        ["persona_source"],
    )


def downgrade() -> None:
    """Remove persona columns from capsule_runs."""
    op.drop_index("ix_capsule_runs_persona_source", table_name="capsule_runs")
    op.drop_column("capsule_runs", "persona_source")
    op.drop_column("capsule_runs", "persona_priority")
