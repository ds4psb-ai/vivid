"""Add telemetry models

Revision ID: 001
Revises: 
Create Date: 2026-01-02 19:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_telemetry'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tool_manifests table
    op.create_table(
        'tool_manifests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_key', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('display_name', sa.String(128), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('version', sa.String(20), nullable=False, server_default='1.0.0'),
        sa.Column('category', sa.String(32), nullable=False, index=True),
        sa.Column('tier', sa.String(20), nullable=False, index=True, server_default='experimental'),
        sa.Column('input_schema', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('output_schema', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('credit_cost', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('fork_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_revenue', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('parent_tool_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('fork_depth', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by', sa.String(64), nullable=False, index=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by', sa.String(64), nullable=True),
        sa.Column('safety_rating', sa.String(20), nullable=False, server_default='review'),
        sa.Column('sandbox_required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('test_pass_rate', sa.Float(), nullable=True),
        sa.Column('quality_rating', sa.Float(), nullable=True),
        sa.Column('human_cloud_success_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_tool_id'], ['tool_manifests.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_tool_manifests_tier_active', 'tool_manifests', ['tier', 'is_active'])

    # Create tool_run_events table
    op.create_table(
        'tool_run_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('tool_key', sa.String(64), nullable=False, index=True),
        sa.Column('tool_version', sa.String(20), nullable=False, server_default='1.0.0'),
        sa.Column('user_id', sa.String(64), nullable=True, index=True),
        sa.Column('session_id', sa.String(64), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, index=True),
        sa.Column('inputs_hash', sa.String(64), nullable=True),
        sa.Column('inputs_summary', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('outputs_summary', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('token_usage', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('cost_usd_est', sa.Float(), nullable=True),
        sa.Column('credits_charged', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('credits_refunded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('canvas_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('workflow_position', sa.Integer(), nullable=True),
        sa.Column('previous_tool_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tool_id'], ['tool_manifests.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_tool_run_events_created_at_status', 'tool_run_events', ['created_at', 'status'])

    # Create fork_events table
    op.create_table(
        'fork_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('parent_tool_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('child_tool_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('fork_depth', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('forker_id', sa.String(64), nullable=False, index=True),
        sa.Column('fork_reason', sa.Text(), nullable=True),
        sa.Column('diff_lines_added', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('diff_lines_removed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('diff_lines_modified', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('diff_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('test_passed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('test_run_at', sa.DateTime(), nullable=True),
        sa.Column('test_details', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('attribution_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('attribution_calculated_at', sa.DateTime(), nullable=True),
        sa.Column('revenue_generated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('revenue_shared', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_suspicious', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('suspicion_reason', sa.String(256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_tool_id'], ['tool_manifests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['child_tool_id'], ['tool_manifests.id'], ondelete='CASCADE'),
    )

    # Create metric_events table
    op.create_table(
        'metric_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('metric_key', sa.String(64), nullable=False, index=True),
        sa.Column('metric_type', sa.String(32), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False, index=True),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),
        sa.Column('dimension_type', sa.String(32), nullable=False),
        sa.Column('dimension_value', sa.String(128), nullable=False, index=True),
        sa.Column('count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sum_value', sa.Float(), nullable=False, server_default='0'),
        sa.Column('min_value', sa.Float(), nullable=True),
        sa.Column('max_value', sa.Float(), nullable=True),
        sa.Column('avg_value', sa.Float(), nullable=True),
        sa.Column('breakdown', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('meta', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_metric_events_key_period', 'metric_events', ['metric_key', 'period_start', 'dimension_value'])

    # Create tool_workflow_patterns table
    op.create_table(
        'tool_workflow_patterns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pattern_key', sa.String(64), nullable=False, unique=True),
        sa.Column('tool_sequence', postgresql.JSONB(), nullable=False),
        sa.Column('frequency', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('avg_completion_rate', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('avg_user_rating', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_tool_workflow_patterns_frequency', 'tool_workflow_patterns', ['frequency'])


def downgrade() -> None:
    op.drop_table('tool_workflow_patterns')
    op.drop_table('metric_events')
    op.drop_table('fork_events')
    op.drop_table('tool_run_events')
    op.drop_table('tool_manifests')
