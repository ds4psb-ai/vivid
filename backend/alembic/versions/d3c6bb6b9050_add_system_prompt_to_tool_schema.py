"""add_system_prompt_to_tool_schema

Revision ID: d3c6bb6b9050
Revises: 008_update_dimension_endpoints
Create Date: 2026-01-04 19:59:16.577121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd3c6bb6b9050'
down_revision: Union[str, Sequence[str], None] = '008_update_dimension_endpoints'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add system_prompt column to tool_schemas table."""
    op.add_column('tool_schemas', sa.Column('system_prompt', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove system_prompt column from tool_schemas table."""
    op.drop_column('tool_schemas', 'system_prompt')
