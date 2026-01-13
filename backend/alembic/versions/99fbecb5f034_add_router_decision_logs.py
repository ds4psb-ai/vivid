"""add_router_decision_logs

Revision ID: 99fbecb5f034
Revises: f29ed9135c30
Create Date: 2026-01-14 02:25:31.500056

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '99fbecb5f034'
down_revision: Union[str, Sequence[str], None] = 'f29ed9135c30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create router_decision_logs table with all indexes."""
    op.create_table(
        'router_decision_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trace_id', sa.String(length=64), nullable=False),
        sa.Column('query_hash', sa.String(length=64), nullable=False),
        sa.Column('dimension', sa.String(length=20), nullable=True),
        sa.Column('auteur_key', sa.String(length=50), nullable=True),
        sa.Column('strategy', sa.String(length=30), nullable=False),
        sa.Column('router_score', sa.Integer(), nullable=False),
        sa.Column('use_reranker', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('use_grounding', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('cache_hit', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes matching model definition
    op.create_index('ix_router_decision_logs_trace_id', 'router_decision_logs', ['trace_id'])
    op.create_index('ix_router_decision_logs_query_hash', 'router_decision_logs', ['query_hash'])
    op.create_index('ix_router_decision_logs_created_at', 'router_decision_logs', ['created_at'])
    op.create_index('ix_router_decision_logs_dimension', 'router_decision_logs', ['dimension'])


def downgrade() -> None:
    """Drop router_decision_logs table and indexes."""
    op.drop_index('ix_router_decision_logs_dimension', table_name='router_decision_logs')
    op.drop_index('ix_router_decision_logs_created_at', table_name='router_decision_logs')
    op.drop_index('ix_router_decision_logs_query_hash', table_name='router_decision_logs')
    op.drop_index('ix_router_decision_logs_trace_id', table_name='router_decision_logs')
    op.drop_table('router_decision_logs')
