"""Add review models

Revision ID: 004
Revises: 003_add_versioning
Create Date: 2026-01-03 00:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_review'
down_revision = '003_add_versioning'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tool_reviews table
    op.create_table(
        'tool_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tool_manifests.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('version_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tool_versions.id', ondelete='SET NULL'),
                  nullable=True),
        sa.Column('review_type', sa.String(30), nullable=False, server_default='fork_submission'),
        sa.Column('status', sa.String(30), nullable=False, server_default='pending'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('submitted_by', sa.String(64), nullable=False),
        sa.Column('submission_notes', sa.Text(), nullable=True),
        sa.Column('assigned_to', sa.String(64), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('decision_by', sa.String(64), nullable=True),
        sa.Column('decision_at', sa.DateTime(), nullable=True),
        sa.Column('decision_notes', sa.Text(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('auto_checks_passed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('auto_checks_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('check_results', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_tool_reviews_tool_id', 'tool_reviews', ['tool_id'])
    op.create_index('ix_tool_reviews_status', 'tool_reviews', ['status'])
    op.create_index('ix_tool_reviews_submitted_by', 'tool_reviews', ['submitted_by'])
    op.create_index('ix_tool_review_status_priority', 'tool_reviews', ['status', 'priority'])
    op.create_index('ix_tool_review_type_status', 'tool_reviews', ['review_type', 'status'])

    # Create review_check_results table
    op.create_table(
        'review_check_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('review_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tool_reviews.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('category', sa.String(30), nullable=False),
        sa.Column('check_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('passed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('details', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('is_automated', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('checked_by', sa.String(64), nullable=True),
        sa.Column('checked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_review_check_results_review_id', 'review_check_results', ['review_id'])

    # Create tier_promotions table
    op.create_table(
        'tier_promotions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tool_manifests.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('from_tier', sa.String(20), nullable=False),
        sa.Column('to_tier', sa.String(20), nullable=False),
        sa.Column('promotion_type', sa.String(30), nullable=False),
        sa.Column('decided_by', sa.String(64), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('metrics_snapshot', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('review_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tool_reviews.id', ondelete='SET NULL'),
                  nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_tier_promotions_tool_id', 'tier_promotions', ['tool_id'])


def downgrade() -> None:
    op.drop_table('tier_promotions')
    op.drop_table('review_check_results')
    op.drop_table('tool_reviews')
