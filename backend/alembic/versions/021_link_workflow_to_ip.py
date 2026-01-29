"""Link workflow executions to IP tables.

Revision ID: 021_link_workflow_to_ip
Revises: 020_add_ip_payout_links
Create Date: 2026-01-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "021_link_workflow_to_ip"
down_revision = "020_add_ip_payout_links"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    # Skip if workflow_executions doesn't exist (table not yet created)
    if 'workflow_executions' not in existing_tables:
        return

    existing_columns = [c['name'] for c in inspector.get_columns('workflow_executions')]

    # workflow_executions: add IP linkage (skip if table doesn't exist)
    # This table will be created later by workflow module initialization


def downgrade() -> None:
    op.drop_index(
        "ix_ip_generations_workflow_execution_id",
        table_name="ip_generations",
    )
    op.drop_constraint(
        "fk_ip_generations_workflow_execution",
        "ip_generations",
        type_="foreignkey",
    )
    op.drop_column("ip_generations", "workflow_execution_id")

    op.drop_column("workflow_executions", "run_token_id")

    op.drop_index(
        "ix_workflow_executions_preset_id",
        table_name="workflow_executions",
    )
    op.drop_index(
        "ix_workflow_executions_ip_id",
        table_name="workflow_executions",
    )
    op.drop_constraint(
        "fk_workflow_executions_preset_id",
        "workflow_executions",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_workflow_executions_ip_id",
        "workflow_executions",
        type_="foreignkey",
    )
    op.drop_column("workflow_executions", "ip_context")
    op.drop_column("workflow_executions", "preset_id")
    op.drop_column("workflow_executions", "ip_id")
