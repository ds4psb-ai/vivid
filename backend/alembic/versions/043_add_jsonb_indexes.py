"""Add JSONB GIN indexes for prompty

Revision ID: 043_add_jsonb_indexes
Revises: 042_add_prompty_tables
Create Date: 2026-02-02
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '043_add_jsonb_indexes'
down_revision: Union[str, None] = '042_add_prompty_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Expression index for category filter
    op.execute("""
        CREATE INDEX idx_template_workflow_category
        ON prompty_templates ((workflow_config->>'category'))
    """)

    # GIN index for complex JSONB queries
    op.execute("""
        CREATE INDEX idx_template_workflow_gin
        ON prompty_templates USING GIN (workflow_config jsonb_path_ops)
    """)

    op.execute("""
        CREATE INDEX idx_template_critique_gin
        ON prompty_templates USING GIN (critique_config jsonb_path_ops)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_template_workflow_category")
    op.execute("DROP INDEX IF EXISTS idx_template_workflow_gin")
    op.execute("DROP INDEX IF EXISTS idx_template_critique_gin")
