"""Phase 8: Personalization tables for GraphRAG + User Preferences.

Revision ID: 026_personalization
Revises: 025_add_hitl_enhancement_tables
Create Date: 2026-01-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "026_personalization"
down_revision: Union[str, None] = "025_add_hitl_enhancement"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create personalization tables for Phase 8."""

    # Ensure pgvector extension is enabled
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # ==========================================================================
    # User Preference Profile
    # ==========================================================================
    op.create_table(
        "user_preference_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(160), nullable=False, unique=True, index=True),
        sa.Column("embedding", postgresql.ARRAY(sa.Float), nullable=True),  # pgvector - 768 dim
        sa.Column("dimension_affinities", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("auteur_preferences", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("persona_memory", sa.Text, nullable=True),
        sa.Column("decay_factor", sa.Float, server_default="0.95"),
        sa.Column("total_signals", sa.Integer, server_default="0"),
        sa.Column("last_embedding_update", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()"), onupdate=sa.text("now()")),
    )

    # ==========================================================================
    # User Interaction Signals
    # ==========================================================================
    op.create_table(
        "user_interaction_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(160), nullable=False, index=True),
        sa.Column("session_id", sa.String(64), nullable=True, index=True),
        sa.Column("signal_type", sa.String(32), nullable=False),  # click, dwell_time, rating, query, generation_complete, feedback
        sa.Column("dimension", sa.String(16), nullable=True),
        sa.Column("auteur_key", sa.String(64), nullable=True),
        sa.Column("value", sa.Float, server_default="1.0"),
        sa.Column("query_text", sa.Text, nullable=True),
        sa.Column("query_embedding", postgresql.ARRAY(sa.Float), nullable=True),  # 768 dim
        sa.Column("evidence_ref", sa.String(256), nullable=True),
        sa.Column("meta", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
    )

    # Composite indexes for efficient queries
    op.create_index(
        "ix_user_signals_user_created",
        "user_interaction_signals",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_user_signals_user_type",
        "user_interaction_signals",
        ["user_id", "signal_type"],
    )

    # ==========================================================================
    # Session Preferences (Ephemeral)
    # ==========================================================================
    op.create_table(
        "session_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("user_id", sa.String(160), nullable=True, index=True),
        sa.Column("dimension_affinities", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("auteur_affinities", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("session_embedding", postgresql.ARRAY(sa.Float), nullable=True),  # 768 dim
        sa.Column("interaction_count", sa.Integer, server_default="0"),
        sa.Column("last_interaction_at", sa.DateTime, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()"), onupdate=sa.text("now()")),
    )

    # Index for cleanup job
    op.create_index(
        "ix_session_prefs_expires",
        "session_preferences",
        ["expires_at"],
    )

    # ==========================================================================
    # GraphRAG Community Reports
    # ==========================================================================
    op.create_table(
        "graphrag_community_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("community_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("level", sa.Integer, nullable=False),  # 0=leaf, higher=abstract
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("summary_embedding", postgresql.ARRAY(sa.Float), nullable=True),  # 768 dim
        sa.Column("key_findings", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("entity_ids", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("auteur_keys", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("rank", sa.Float, server_default="0.5"),  # Importance score
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()"), onupdate=sa.text("now()")),
    )

    # Index for level-based queries
    op.create_index(
        "ix_community_reports_level",
        "graphrag_community_reports",
        ["level"],
    )

    # ==========================================================================
    # GraphRAG Entity Store (Cached entities from graph)
    # ==========================================================================
    op.create_table(
        "graphrag_entities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_id", sa.String(128), nullable=False, unique=True, index=True),
        sa.Column("entity_type", sa.String(32), nullable=False),  # Auteur, Film, Technique, Collaborator, etc.
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("name_embedding", postgresql.ARRAY(sa.Float), nullable=True),  # 768 dim
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("description_embedding", postgresql.ARRAY(sa.Float), nullable=True),  # 768 dim
        sa.Column("properties", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("auteur_key", sa.String(64), nullable=True, index=True),
        sa.Column("community_id", sa.String(64), nullable=True, index=True),
        sa.Column("degree", sa.Integer, server_default="0"),  # Number of relationships
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()"), onupdate=sa.text("now()")),
    )

    # Index for type-based queries
    op.create_index(
        "ix_graphrag_entities_type",
        "graphrag_entities",
        ["entity_type"],
    )

    # ==========================================================================
    # GraphRAG Relationships
    # ==========================================================================
    op.create_table(
        "graphrag_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_entity_id", sa.String(128), nullable=False, index=True),
        sa.Column("target_entity_id", sa.String(128), nullable=False, index=True),
        sa.Column("relationship_type", sa.String(64), nullable=False),  # DIRECTED, USES_TECHNIQUE, etc.
        sa.Column("weight", sa.Float, server_default="1.0"),
        sa.Column("properties", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("auteur_key", sa.String(64), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
    )

    # Composite index for graph traversal
    op.create_index(
        "ix_graphrag_rel_source_type",
        "graphrag_relationships",
        ["source_entity_id", "relationship_type"],
    )
    op.create_index(
        "ix_graphrag_rel_target_type",
        "graphrag_relationships",
        ["target_entity_id", "relationship_type"],
    )

    # Unique constraint for relationship (prevent duplicates)
    op.create_unique_constraint(
        "uq_graphrag_relationship",
        "graphrag_relationships",
        ["source_entity_id", "target_entity_id", "relationship_type"],
    )


def downgrade() -> None:
    """Drop personalization tables."""
    op.drop_table("graphrag_relationships")
    op.drop_table("graphrag_entities")
    op.drop_table("graphrag_community_reports")
    op.drop_table("session_preferences")
    op.drop_table("user_interaction_signals")
    op.drop_table("user_preference_profiles")
