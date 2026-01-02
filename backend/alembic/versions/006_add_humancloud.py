"""Add Human Cloud tables

Revision ID: 006
Revises: 005_add_sandbox
Create Date: 2026-01-03 01:20:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '006_add_humancloud'
down_revision = '005_add_sandbox'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Creator Profiles
    op.create_table(
        'creator_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(64), unique=True, nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('portfolio_urls', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('categories', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('skills', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('hourly_rate', sa.Integer(), nullable=True),
        sa.Column('min_budget', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('completed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_earned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('avg_response_hours', sa.Integer(), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_creator_profiles_user_id', 'creator_profiles', ['user_id'])

    # Creative Requests
    op.create_table(
        'creative_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', sa.String(64), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False, server_default='video_creative'),
        sa.Column('tags', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('requirements', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('reference_urls', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('attached_files', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('budget_credits', sa.Integer(), nullable=False),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('estimated_hours', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('assigned_creator_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('creator_profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('client_rating', sa.Integer(), nullable=True),
        sa.Column('client_feedback', sa.Text(), nullable=True),
        sa.Column('credits_escrowed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('credits_released', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('platform_fee', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_creative_requests_client_id', 'creative_requests', ['client_id'])
    op.create_index('ix_creative_requests_status', 'creative_requests', ['status'])
    op.create_index('ix_creative_requests_status_category', 'creative_requests', ['status', 'category'])

    # Assignments
    op.create_table(
        'assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('request_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('creative_requests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('creator_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('agreed_credits', sa.Integer(), nullable=False),
        sa.Column('agreed_deadline', sa.DateTime(), nullable=True),
        sa.Column('agreed_revisions', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('milestones', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('current_milestone', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('creator_rating', sa.Integer(), nullable=True),
        sa.Column('client_rating', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_assignments_request_id', 'assignments', ['request_id'])
    op.create_index('ix_assignments_creator_id', 'assignments', ['creator_id'])

    # Evidence Logs
    op.create_table(
        'evidence_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('assignment_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('assignments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(30), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('actor_id', sa.String(64), nullable=False),
        sa.Column('actor_role', sa.String(20), nullable=False),
        sa.Column('attachments', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('extra', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('file_version', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_evidence_logs_assignment_id', 'evidence_logs', ['assignment_id'])

    # Deliveries
    op.create_table(
        'deliveries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('assignment_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('assignments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('files', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('revision_request', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_deliveries_assignment_id', 'deliveries', ['assignment_id'])


def downgrade() -> None:
    op.drop_table('deliveries')
    op.drop_table('evidence_logs')
    op.drop_table('assignments')
    op.drop_table('creative_requests')
    op.drop_table('creator_profiles')
