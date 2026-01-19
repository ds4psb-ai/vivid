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
    # workflow_executions: add IP linkage
    op.add_column(
        "workflow_executions",
        sa.Column("ip_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "workflow_executions",
        sa.Column("preset_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "workflow_executions",
        sa.Column("ip_context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_foreign_key(
        "fk_workflow_executions_ip_id",
        "workflow_executions",
        "ip_catalog",
        ["ip_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_workflow_executions_preset_id",
        "workflow_executions",
        "ip_workflow_presets",
        ["preset_id"],
        ["id"],
    )
    op.create_index(
        "ix_workflow_executions_ip_id",
        "workflow_executions",
        ["ip_id"],
    )
    op.create_index(
        "ix_workflow_executions_preset_id",
        "workflow_executions",
        ["preset_id"],
    )

    # workflow_executions: add run_token_id
    op.add_column(
        "workflow_executions",
        sa.Column("run_token_id", sa.String(160), nullable=True),
    )

    # ip_generations: link to workflow execution
    op.add_column(
        "ip_generations",
        sa.Column("workflow_execution_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_ip_generations_workflow_execution",
        "ip_generations",
        "workflow_executions",
        ["workflow_execution_id"],
        ["id"],
    )
    op.create_index(
        "ix_ip_generations_workflow_execution_id",
        "ip_generations",
        ["workflow_execution_id"],
    )


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
