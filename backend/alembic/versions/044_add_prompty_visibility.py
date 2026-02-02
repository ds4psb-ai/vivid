"""Add visibility and fork fields to prompty_projects.

Revision ID: 044_prompty_visibility
Revises: 043_add_jsonb_indexes
Create Date: 2026-02-02

Community platform features:
- visibility: private | prompts-only | full
- forked_from_id: track fork relationships
- fork_count: denormalized fork counter
- avg_score: denormalized critique average for community display
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers
revision = "044_prompty_visibility"
down_revision = "043_add_jsonb_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add visibility column with default 'private'
    op.add_column(
        "prompty_projects",
        sa.Column("visibility", sa.String(20), server_default="private", nullable=False),
    )

    # Add fork tracking columns
    op.add_column(
        "prompty_projects",
        sa.Column("forked_from_id", UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "prompty_projects",
        sa.Column("fork_count", sa.Integer(), server_default="0", nullable=False),
    )

    # Add denormalized score for community display
    op.add_column(
        "prompty_projects",
        sa.Column("avg_score", sa.Float(), nullable=True),
    )

    # Add index for visibility (community queries)
    op.create_index(
        "ix_prompty_projects_visibility",
        "prompty_projects",
        ["visibility"],
    )


def downgrade() -> None:
    op.drop_index("ix_prompty_projects_visibility", table_name="prompty_projects")
    op.drop_column("prompty_projects", "avg_score")
    op.drop_column("prompty_projects", "fork_count")
    op.drop_column("prompty_projects", "forked_from_id")
    op.drop_column("prompty_projects", "visibility")
