"""Add agent tables (sessions, messages, artifacts)

Revision ID: 010b_add_agent_tables
Revises: 010_add_miniapp_submissions
Create Date: 2026-01-26

Creates agent_sessions, agent_messages, agent_artifacts tables
required for workflow_states foreign key.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '010b_add_agent_tables'
down_revision: Union[str, None] = '010_add_miniapp_submissions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create agent tables (idempotent - checks if tables exist)."""
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    # agent_sessions
    if 'agent_sessions' not in existing_tables:
        op.create_table('agent_sessions',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
            sa.Column('title', sa.String(length=200), nullable=True),
            sa.Column('owner_id', sa.String(length=160), nullable=True),
            sa.Column('persona_key', sa.String(length=80), nullable=True),
            sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_agent_sessions_owner_id', 'agent_sessions', ['owner_id'], unique=False)
        op.create_index('ix_agent_sessions_status', 'agent_sessions', ['status'], unique=False)
        op.create_index('ix_agent_sessions_created_at', 'agent_sessions', ['created_at'], unique=False)

    # agent_messages
    if 'agent_messages' not in existing_tables:
        op.create_table('agent_messages',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('session_id', sa.UUID(), nullable=False),
            sa.Column('role', sa.String(length=24), nullable=False),
            sa.Column('content', sa.Text(), nullable=False, server_default=''),
            sa.Column('tool_calls', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
            sa.Column('tool_call_id', sa.String(length=120), nullable=True),
            sa.Column('name', sa.String(length=120), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['session_id'], ['agent_sessions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_agent_messages_session_id', 'agent_messages', ['session_id'], unique=False)
        op.create_index('ix_agent_messages_created_at', 'agent_messages', ['created_at'], unique=False)

    # agent_artifacts
    if 'agent_artifacts' not in existing_tables:
        op.create_table('agent_artifacts',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('session_id', sa.UUID(), nullable=False),
            sa.Column('artifact_type', sa.String(length=80), nullable=False),
            sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
            sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['session_id'], ['agent_sessions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_agent_artifacts_session_id', 'agent_artifacts', ['session_id'], unique=False)
        op.create_index('ix_agent_artifacts_created_at', 'agent_artifacts', ['created_at'], unique=False)


def downgrade() -> None:
    """Drop agent tables."""
    op.drop_index('ix_agent_artifacts_created_at', table_name='agent_artifacts')
    op.drop_index('ix_agent_artifacts_session_id', table_name='agent_artifacts')
    op.drop_table('agent_artifacts')

    op.drop_index('ix_agent_messages_created_at', table_name='agent_messages')
    op.drop_index('ix_agent_messages_session_id', table_name='agent_messages')
    op.drop_table('agent_messages')

    op.drop_index('ix_agent_sessions_created_at', table_name='agent_sessions')
    op.drop_index('ix_agent_sessions_status', table_name='agent_sessions')
    op.drop_index('ix_agent_sessions_owner_id', table_name='agent_sessions')
    op.drop_table('agent_sessions')
