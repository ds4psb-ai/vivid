"""Add versioning models

Revision ID: 003
Revises: 002_add_settlement
Create Date: 2026-01-03 00:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_versioning'
down_revision = '002_add_settlement'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tool_versions table
    op.create_table(
        'tool_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tool_manifests.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('code_type', sa.String(30), nullable=False, server_default='prompt_template'),
        sa.Column('code_content', sa.Text(), nullable=False),
        sa.Column('input_schema', postgresql.JSONB(), nullable=True),
        sa.Column('output_schema', postgresql.JSONB(), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('dependencies', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('config', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('is_live', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by', sa.String(64), nullable=False),
        sa.Column('reviewed_by', sa.String(64), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('changelog', sa.Text(), nullable=True),
    )
    op.create_index('ix_tool_versions_tool_id', 'tool_versions', ['tool_id'])
    op.create_index('ix_tool_versions_status', 'tool_versions', ['status'])
    op.create_index('ix_tool_versions_created_by', 'tool_versions', ['created_by'])
    op.create_index('ix_tool_version_tool_status', 'tool_versions', ['tool_id', 'status'])
    op.create_index('ix_tool_version_tool_live', 'tool_versions', ['tool_id', 'is_live'])

    # Create tool_diffs table
    op.create_table(
        'tool_diffs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('fork_event_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('fork_events.id', ondelete='SET NULL'),
                  nullable=True),
        sa.Column('original_version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tool_versions.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('forked_version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tool_versions.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('diff_content', sa.Text(), nullable=False),
        sa.Column('lines_added', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lines_removed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lines_modified', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('semantic_changes', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('diff_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('similarity_ratio', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_trivial_change', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sybil_flags', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_tool_diffs_fork_event_id', 'tool_diffs', ['fork_event_id'])

    # Create tool_test_cases table
    op.create_table(
        'tool_test_cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tool_manifests.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('input_data', postgresql.JSONB(), nullable=False),
        sa.Column('expected_output', postgresql.JSONB(), nullable=True),
        sa.Column('validation_rules', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(64), nullable=False),
    )
    op.create_index('ix_tool_test_cases_tool_id', 'tool_test_cases', ['tool_id'])


def downgrade() -> None:
    op.drop_table('tool_test_cases')
    op.drop_table('tool_diffs')
    op.drop_table('tool_versions')
