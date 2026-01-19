"""Remove legacy_params from blackhole_templates input_preset.

Revision ID: 024_remove_legacy_params_from_blackhole_templates
Revises: 023_remove_workflow_session_id
Create Date: 2026-01-19
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "024_remove_legacy_params_from_blackhole_templates"
down_revision = "023_remove_workflow_session_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            UPDATE blackhole_templates
            SET input_preset = input_preset - 'legacy_params'
            WHERE input_preset ? 'legacy_params'
            """
        )


def downgrade() -> None:
    # Data-only migration; cannot restore removed legacy_params.
    pass
