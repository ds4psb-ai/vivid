"""Add user_id column to capsule_runs for BOLA prevention.

Revision ID: 036_add_user_id_capsule
Revises: 035_add_chain_sessions
Create Date: 2026-01-28

This migration adds user_id to capsule_runs to enable:
- User-scoped queries (BOLA prevention)
- Previous run lookups in chain workflow
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '036_add_user_id_capsule'
down_revision: Union[str, None] = '035_add_chain_sessions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_id column to capsule_runs
    op.add_column(
        'capsule_runs',
        sa.Column('user_id', sa.String(64), nullable=True)
    )

    # Create index for user_id lookups
    op.create_index(
        'ix_capsule_runs_user_id',
        'capsule_runs',
        ['user_id']
    )

    # Create composite index for user + capsule_key + status queries
    op.create_index(
        'ix_capsule_runs_user_key_status',
        'capsule_runs',
        ['user_id', 'capsule_key', 'status']
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_capsule_runs_user_key_status', table_name='capsule_runs')
    op.drop_index('ix_capsule_runs_user_id', table_name='capsule_runs')

    # Drop column
    op.drop_column('capsule_runs', 'user_id')
