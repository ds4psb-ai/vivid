"""Add prompty tables

Revision ID: 042_add_prompty_tables
Revises: 041_add_user_accounts_table
Create Date: 2026-02-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '042_add_prompty_tables'
down_revision: Union[str, None] = '041_add_user_accounts'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create prompty_templates table
    op.create_table(
        'prompty_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('creator_id', sa.String(160), nullable=False),
        sa.Column('creator_name', sa.String(100), nullable=False, server_default='Prompty Team'),
        sa.Column('category', sa.String(64), nullable=False, server_default='video'),
        sa.Column('workflow_config', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('critique_config', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('example_project_url', sa.String(500), nullable=True),
        sa.Column('tags', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('use_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('rating_sum', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('rating_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_featured', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_public', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_prompty_templates_category', 'prompty_templates', ['category'])
    op.create_index('ix_prompty_templates_featured', 'prompty_templates', ['is_featured'])
    op.create_index('ix_prompty_templates_use_count', 'prompty_templates', ['use_count'])

    # Create prompty_projects table
    op.create_table(
        'prompty_projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('user_id', sa.String(160), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('state', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('current_stage', sa.String(64), nullable=False, server_default='analysis'),
        sa.Column('current_step', sa.String(128), nullable=False, server_default=''),
        sa.Column('progress_percent', sa.Integer, nullable=False, server_default='0'),
        sa.Column('status', sa.String(32), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_prompty_projects_user', 'prompty_projects', ['user_id'])
    op.create_index('ix_prompty_projects_template', 'prompty_projects', ['template_id'])
    op.create_index('ix_prompty_projects_status', 'prompty_projects', ['status'])
    op.create_index('ix_prompty_projects_created', 'prompty_projects', ['created_at'])

    # Create prompty_critiques table
    op.create_table(
        'prompty_critiques',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('prompty_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stage', sa.String(64), nullable=False),
        sa.Column('step_id', sa.String(128), nullable=False),
        sa.Column('scores', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('total_score', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('passed', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('revision_number', sa.Integer, nullable=False, server_default='1'),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_prompty_critiques_project', 'prompty_critiques', ['project_id'])
    op.create_index('ix_prompty_critiques_stage', 'prompty_critiques', ['stage'])
    op.create_index('ix_prompty_critiques_created', 'prompty_critiques', ['created_at'])

    # Create prompty_guide_logs table
    op.create_table(
        'prompty_guide_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(160), nullable=False),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('stage', sa.String(64), nullable=True),
        sa.Column('step_id', sa.String(128), nullable=True),
        sa.Column('extra_data', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_prompty_guide_logs_project', 'prompty_guide_logs', ['project_id'])
    op.create_index('ix_prompty_guide_logs_action', 'prompty_guide_logs', ['action'])
    op.create_index('ix_prompty_guide_logs_created', 'prompty_guide_logs', ['created_at'])


def downgrade() -> None:
    op.drop_table('prompty_guide_logs')
    op.drop_table('prompty_critiques')
    op.drop_table('prompty_projects')
    op.drop_table('prompty_templates')
