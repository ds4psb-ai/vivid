"""add_workflow_state_table

Revision ID: f29ed9135c30
Revises: 010_add_miniapp_submissions
Create Date: 2026-01-08 00:41:51.359101

P1-4: Add workflow_states table for agent session recovery.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f29ed9135c30'
down_revision: Union[str, Sequence[str], None] = '010b_add_agent_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add workflow_states table."""
    op.create_table('workflow_states',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(length=160), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('current_step_index', sa.Integer(), nullable=False),
        sa.Column('total_steps', sa.Integer(), nullable=False),
        sa.Column('current_tool', sa.String(length=100), nullable=True),
        sa.Column('workflow_definition', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('step_results', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('context_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('total_credits_used', sa.Integer(), nullable=False),
        sa.Column('total_execution_ms', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('last_checkpoint_at', sa.DateTime(), nullable=True),
        sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['agent_sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', name='uq_workflow_states_session')
    )
    op.create_index('ix_workflow_states_session_id', 'workflow_states', ['session_id'], unique=False)
    op.create_index('ix_workflow_states_status', 'workflow_states', ['status'], unique=False)
    op.create_index('ix_workflow_states_updated_at', 'workflow_states', ['updated_at'], unique=False)
    op.create_index('ix_workflow_states_user_id', 'workflow_states', ['user_id'], unique=False)


def downgrade() -> None:
    """Drop workflow_states table."""
    op.drop_index('ix_workflow_states_user_id', table_name='workflow_states')
    op.drop_index('ix_workflow_states_updated_at', table_name='workflow_states')
    op.drop_index('ix_workflow_states_status', table_name='workflow_states')
    op.drop_index('ix_workflow_states_session_id', table_name='workflow_states')
    op.drop_table('workflow_states')
