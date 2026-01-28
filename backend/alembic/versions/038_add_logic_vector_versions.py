"""Add logic_vector_versions table for versioning and drift detection.

Revision ID: 038_add_logic_vector_versions
Revises: 037_add_outbox
Create Date: 2026-01-28

Stores Logic Vector versions for each IP with drift tracking.
Supports:
- Version history per IP
- Drift scoring between versions
- Active version tracking with valid_from/valid_until
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "038_add_logic_vector_versions"
down_revision = "037_add_outbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create logic_vector_versions table."""
    op.create_table(
        "logic_vector_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ip_id", sa.String(64), nullable=False, index=True),
        sa.Column("version_number", sa.Integer, nullable=False),

        # Logic Vector data
        sa.Column("embedding", postgresql.ARRAY(sa.Float), nullable=True),  # 384-dim
        sa.Column("logic_vector", postgresql.JSONB, nullable=False),
        sa.Column("source_videos", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),

        # Validity tracking
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("valid_from", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("valid_until", sa.DateTime, nullable=True),

        # Drift metadata
        sa.Column("drift_score_from_prev", sa.Float, nullable=True),
        sa.Column("drift_reason", sa.String(50), nullable=True),

        # Audit
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.String(64), nullable=True),

        # Unique constraint: one version number per IP
        sa.UniqueConstraint("ip_id", "version_number", name="uq_ip_version"),
    )

    # Index for finding active version
    op.create_index(
        "ix_logic_vector_versions_ip_active",
        "logic_vector_versions",
        ["ip_id", "is_active"],
    )

    # Index for version history queries
    op.create_index(
        "ix_logic_vector_versions_ip_version",
        "logic_vector_versions",
        ["ip_id", "version_number"],
    )


def downgrade() -> None:
    """Drop logic_vector_versions table."""
    op.drop_index("ix_logic_vector_versions_ip_version", table_name="logic_vector_versions")
    op.drop_index("ix_logic_vector_versions_ip_active", table_name="logic_vector_versions")
    op.drop_table("logic_vector_versions")
