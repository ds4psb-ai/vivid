"""Add settlement models

Revision ID: 002
Revises: 001_add_telemetry
Create Date: 2026-01-02 19:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_settlement'
down_revision = '001_add_telemetry'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create settlement_transactions table
    op.create_table(
        'settlement_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_run_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('tool_run_events.id', ondelete='CASCADE'),
                  nullable=False, unique=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tool_manifests.id', ondelete='SET NULL'),
                  nullable=True),
        sa.Column('tool_key', sa.String(64), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('total_credits', sa.Integer(), nullable=False),
        sa.Column('platform_fee', sa.Integer(), nullable=False),
        sa.Column('creator_pool', sa.Integer(), nullable=False),
        sa.Column('lineage_depth', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('attribution_score', sa.Float(), nullable=True),
        sa.Column('payer_user_id', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processed_by', sa.String(64), nullable=True),
        sa.Column('meta', postgresql.JSONB(), nullable=False, server_default='{}'),
    )
    op.create_index('ix_settlement_transactions_tool_run_id', 'settlement_transactions', ['tool_run_id'])
    op.create_index('ix_settlement_transactions_tool_id', 'settlement_transactions', ['tool_id'])
    op.create_index('ix_settlement_transactions_status', 'settlement_transactions', ['status'])
    op.create_index('ix_settlement_transactions_payer_user_id', 'settlement_transactions', ['payer_user_id'])
    op.create_index('ix_settlement_transactions_created_at', 'settlement_transactions', ['created_at'])
    op.create_index('ix_settlement_status_created', 'settlement_transactions', ['status', 'created_at'])

    # Create settlement_payouts table
    op.create_table(
        'settlement_payouts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('settlement_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('settlement_transactions.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('recipient_id', sa.String(64), nullable=False),
        sa.Column('recipient_tool_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('recipient_tool_key', sa.String(64), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('share_type', sa.String(20), nullable=False),
        sa.Column('share_rate', sa.Float(), nullable=False),
        sa.Column('lineage_position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('ledger_entry_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('credited_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
    )
    op.create_index('ix_settlement_payouts_settlement_id', 'settlement_payouts', ['settlement_id'])
    op.create_index('ix_settlement_payouts_recipient_id', 'settlement_payouts', ['recipient_id'])
    op.create_index('ix_settlement_payouts_status', 'settlement_payouts', ['status'])

    # Create settlement_disputes table
    op.create_table(
        'settlement_disputes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('settlement_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('settlement_transactions.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('complainant_id', sa.String(64), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('expected_amount', sa.Integer(), nullable=True),
        sa.Column('evidence', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(20), nullable=False, server_default='open'),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('adjustment_amount', sa.Integer(), nullable=True),
        sa.Column('resolved_by', sa.String(64), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_settlement_disputes_settlement_id', 'settlement_disputes', ['settlement_id'])
    op.create_index('ix_settlement_disputes_complainant_id', 'settlement_disputes', ['complainant_id'])
    op.create_index('ix_settlement_disputes_status', 'settlement_disputes', ['status'])
    op.create_index('ix_settlement_disputes_created_at', 'settlement_disputes', ['created_at'])


def downgrade() -> None:
    op.drop_table('settlement_disputes')
    op.drop_table('settlement_payouts')
    op.drop_table('settlement_transactions')
