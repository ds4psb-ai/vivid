"""Add miniapp_submissions table

Revision ID: 010_add_miniapp_submissions
Revises: 009_add_constellation
Create Date: 2026-01-06

Tables:
- miniapp_submissions: User-submitted MiniApp/Dimension Portal proposals
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '010_add_miniapp_submissions'
down_revision = '009_add_constellation'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'miniapp_submissions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(160), nullable=False),

        # App info
        sa.Column('app_name', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=False),

        # Source
        sa.Column('source_type', sa.String(10), nullable=False),  # 'github' or 'zip'
        sa.Column('github_url', sa.String(500), nullable=True),
        sa.Column('zip_file_uri', sa.String(500), nullable=True),

        # Optional metadata
        sa.Column('ai_tool', sa.String(50), nullable=True),

        # Review status
        sa.Column('status', sa.String(20), nullable=False, server_default='pending_review'),
        sa.Column('reviewer_notes', sa.Text, nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by', sa.String(160), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # Indexes
    op.create_index('ix_miniapp_submissions_user', 'miniapp_submissions', ['user_id'])
    op.create_index('ix_miniapp_submissions_status', 'miniapp_submissions', ['status'])
    op.create_index('ix_miniapp_submissions_created', 'miniapp_submissions', ['created_at'])


def downgrade():
    op.drop_index('ix_miniapp_submissions_created', 'miniapp_submissions')
    op.drop_index('ix_miniapp_submissions_status', 'miniapp_submissions')
    op.drop_index('ix_miniapp_submissions_user', 'miniapp_submissions')
    op.drop_table('miniapp_submissions')
