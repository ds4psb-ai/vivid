"""Add sandbox tables

Revision ID: 005
Revises: 004_add_review
Create Date: 2026-01-03 01:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_add_sandbox'
down_revision = '004_add_review'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create sandbox_configs table
    op.create_table(
        'sandbox_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('tier', sa.String(20), nullable=False, server_default='strict'),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('memory_mb', sa.Integer(), nullable=False, server_default='512'),
        sa.Column('cpu_limit', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('network_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('allowed_hosts', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('filesystem_readonly', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allowed_paths', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('max_output_bytes', sa.Integer(), nullable=False, server_default='1048576'),
        sa.Column('max_input_bytes', sa.Integer(), nullable=False, server_default='102400'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Create sandbox_executions table
    op.create_table(
        'sandbox_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tool_manifests.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tool_versions.id', ondelete='SET NULL'),
                  nullable=True),
        sa.Column('config_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('sandbox_configs.id', ondelete='RESTRICT'),
                  nullable=False),
        sa.Column('user_id', sa.String(64), nullable=False),
        sa.Column('session_id', sa.String(64), nullable=True),
        sa.Column('input_data', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('output_data', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('memory_used_mb', sa.Integer(), nullable=True),
        sa.Column('cpu_time_ms', sa.Integer(), nullable=True),
        sa.Column('container_id', sa.String(100), nullable=True),
        sa.Column('exit_code', sa.Integer(), nullable=True),
        sa.Column('stdout', sa.Text(), nullable=True),
        sa.Column('stderr', sa.Text(), nullable=True),
        sa.Column('queued_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('credits_charged', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('credits_refunded', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index('ix_sandbox_executions_tool_id', 'sandbox_executions', ['tool_id'])
    op.create_index('ix_sandbox_executions_user_id', 'sandbox_executions', ['user_id'])
    op.create_index('ix_sandbox_executions_status', 'sandbox_executions', ['status'])


def downgrade() -> None:
    op.drop_table('sandbox_executions')
    op.drop_table('sandbox_configs')
