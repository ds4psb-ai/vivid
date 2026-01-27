"""Add chain_sessions table for workflow chain persistence.

Revision ID: 035_add_chain_sessions
Revises: 034_add_ocean
Create Date: 2026-01-28

This migration adds the chain_sessions table for P7+ Chain UX:
- Persists workflow chain data across browser sessions
- Supports optimistic locking via version field
- Enables cross-device workflow continuation
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = '035_add_chain_sessions'
down_revision: Union[str, None] = '034_add_ocean'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create chain_sessions table
    op.create_table(
        'chain_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('ip_slug', sa.String(100), nullable=True),

        # Chain state (JSONB)
        sa.Column('chain_data', JSONB, nullable=False, server_default='{}'),
        sa.Column('accumulated_evidence_refs', JSONB, nullable=False, server_default='[]'),
        sa.Column('current_dimension', sa.String(50), nullable=True),
        sa.Column('navigation_history', JSONB, nullable=False, server_default='[]'),

        # Metadata
        sa.Column('mega_app', sa.String(50), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),

        # Optimistic Locking
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),

        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
    )

    # Create indexes
    op.create_index('ix_chain_sessions_user_id', 'chain_sessions', ['user_id'])
    op.create_index('ix_chain_sessions_ip_slug', 'chain_sessions', ['ip_slug'])
    op.create_index('ix_chain_sessions_updated_at', 'chain_sessions', ['updated_at'])
    op.create_index('ix_chain_sessions_user_updated', 'chain_sessions', ['user_id', 'updated_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_chain_sessions_user_updated', table_name='chain_sessions')
    op.drop_index('ix_chain_sessions_updated_at', table_name='chain_sessions')
    op.drop_index('ix_chain_sessions_ip_slug', table_name='chain_sessions')
    op.drop_index('ix_chain_sessions_user_id', table_name='chain_sessions')

    # Drop table
    op.drop_table('chain_sessions')
