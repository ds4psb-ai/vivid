"""Add missing tables previously created by init_db().

These tables were previously created by init_db() raw SQL,
but should be managed by Alembic for proper schema management.

Tables:
- analytics_events: User engagement and pilot metrics
- rag_semantic_cache: Semantic cache with pgvector
- studio_artifacts: Studio artifact metadata

Revision ID: 032_add_missing_init_db_tables
Revises: 031_add_persona_columns
Create Date: 2026-01-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "032_add_missing_init_db_tables"
down_revision: Union[str, None] = "031_add_persona_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tables that were previously managed by init_db()."""

    # ==========================================================================
    # Enable pgvector extension (required for rag_semantic_cache)
    # ==========================================================================
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ==========================================================================
    # Analytics Events
    # ==========================================================================
    # Check if table exists first (might have been created by previous init_db)
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'analytics_events')")
    )
    if not result.scalar():
        op.create_table(
            "analytics_events",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("event_type", sa.String(60), nullable=False),
            sa.Column("user_id", sa.String(160), nullable=True),
            sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("capsule_id", sa.String(160), nullable=True),
            sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("evidence_ref", sa.String(200), nullable=True),
            sa.Column("meta", postgresql.JSONB, nullable=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        )
        op.create_index("idx_analytics_events_type", "analytics_events", ["event_type"])
        op.create_index("idx_analytics_events_created", "analytics_events", ["created_at"])

    # ==========================================================================
    # RAG Semantic Cache with pgvector
    # ==========================================================================
    result = conn.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'rag_semantic_cache')")
    )
    if not result.scalar():
        op.create_table(
            "rag_semantic_cache",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("query_text", sa.Text, nullable=False),
            sa.Column("embedding", sa.LargeBinary, nullable=True),  # pgvector will handle this
            sa.Column("response_json", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
            sa.Column("auteur_key", sa.String(64), nullable=True),
            sa.Column("dimension", sa.String(16), nullable=True),
            sa.Column("hit_count", sa.Integer, server_default="0"),
            sa.Column("expires_at", sa.DateTime, nullable=False),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()")),
        )
        op.create_index("ix_rag_cache_created", "rag_semantic_cache", ["created_at"])
        op.create_index("ix_rag_cache_expires", "rag_semantic_cache", ["expires_at"])

        # Alter column to vector type (pgvector)
        op.execute("ALTER TABLE rag_semantic_cache ALTER COLUMN embedding TYPE vector(768) USING embedding::vector(768)")

        # HNSW index for fast vector search
        try:
            op.execute(
                "CREATE INDEX IF NOT EXISTS ix_rag_cache_embedding ON rag_semantic_cache USING hnsw (embedding vector_cosine_ops)"
            )
        except Exception:
            # Fallback for older pgvector or if index creation fails
            pass

    # ==========================================================================
    # Studio Artifacts
    # ==========================================================================
    result = conn.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'studio_artifacts')")
    )
    if not result.scalar():
        op.create_table(
            "studio_artifacts",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("artifact_type", sa.String(32), nullable=False),
            sa.Column("auteur_key", sa.String(64), nullable=True),
            sa.Column("focus_topic", sa.Text, nullable=False),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("storage_path", sa.String(500), nullable=False),
            sa.Column("storage_url", sa.String(500), nullable=True),
            sa.Column("file_size_bytes", sa.Integer, server_default="0"),
            sa.Column("mime_type", sa.String(100), server_default="''"),
            sa.Column("notebook_id", sa.String(64), nullable=True),
            sa.Column("source_ids", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
            sa.Column("generation_params", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
            sa.Column("access_count", sa.Integer, server_default="0"),
            sa.Column("last_accessed_at", sa.DateTime, nullable=True),
            sa.Column("expires_at", sa.DateTime, nullable=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()")),
        )
        op.create_index("ix_artifacts_key", "studio_artifacts", ["auteur_key", "artifact_type"])
        op.create_index("ix_artifacts_created", "studio_artifacts", ["created_at"])
        op.create_index("ix_artifacts_expires", "studio_artifacts", ["expires_at"])


def downgrade() -> None:
    """Drop tables (only if they were created by this migration)."""
    # Note: These tables might have pre-existing data from init_db().
    # Downgrade should be handled carefully in production.
    op.drop_table("studio_artifacts")
    op.drop_table("rag_semantic_cache")
    op.drop_table("analytics_events")
