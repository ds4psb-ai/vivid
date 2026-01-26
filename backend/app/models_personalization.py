"""Phase 8: Personalization Database Models.

User preference learning, session tracking, and GraphRAG persistence models.

Usage:
    from app.models_personalization import (
        UserPreferenceProfile,
        UserInteractionSignal,
        SessionPreference,
        GraphRAGCommunityReport,
        GraphRAGEntity,
        GraphRAGRelationship,
    )
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, Float, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.database import Base


# =============================================================================
# Constants
# =============================================================================

USER_EMBEDDING_DIM = 768  # text-embedding-004 dimension


# =============================================================================
# User Preference Models
# =============================================================================

class UserPreferenceProfile(Base):
    """User preference profile with embedding vector.

    Stores Netflix-style user embeddings and PersonaMem-v2 compact memory
    for personalized RAG retrieval.

    Attributes:
        user_id: Unique user identifier
        embedding: 768-dim user preference embedding
        dimension_affinities: {"4D": 0.85, "AD": 0.72} - Dimension preferences
        auteur_preferences: {"bong": 0.92, "epoch": 0.78} - Auteur preferences
        persona_memory: 2k-token compact persona summary (PersonaMem-v2 style)
        decay_factor: Preference decay rate (0-1), default 0.95
        total_signals: Total number of recorded signals
    """
    __tablename__ = "user_preference_profiles"
    __table_args__ = (
        Index("ix_user_pref_profiles_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)

    # User embedding (768-dim, text-embedding-004)
    embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)

    # Affinity scores (0.0 - 1.0)
    dimension_affinities: Mapped[dict] = mapped_column(JSONB, default=dict)
    auteur_preferences: Mapped[dict] = mapped_column(JSONB, default=dict)

    # PersonaMem-v2: Compact persona memory (max 2k tokens)
    persona_memory: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Preference decay settings
    decay_factor: Mapped[float] = mapped_column(Float, default=0.95)
    total_signals: Mapped[int] = mapped_column(Integer, default=0)
    last_embedding_update: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserInteractionSignal(Base):
    """Implicit/explicit interaction signals for preference learning.

    Records user interactions for building preference embeddings.
    Signal types based on REBECA paper (2025):
    - click: User clicked on content (weight: 1.0)
    - dwell_time: Time spent on content (weight: 0.5 per 10 seconds)
    - rating: Explicit rating (weight: 2.0 per star)
    - query: Search query (weight: 0.3)
    - generation_complete: Completed generation (weight: 1.5)
    - feedback: Explicit feedback (weight: 2.5)

    Attributes:
        user_id: User identifier
        session_id: Session identifier (for session-level tracking)
        signal_type: Type of signal
        dimension: Associated dimension (1D, 2D, etc.)
        auteur_key: Associated auteur
        value: Signal strength/weight
        query_embedding: Query embedding for query-type signals
    """
    __tablename__ = "user_interaction_signals"
    __table_args__ = (
        Index("ix_user_signals_user_created", "user_id", "created_at"),
        Index("ix_user_signals_user_type", "user_id", "signal_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # Signal details
    signal_type: Mapped[str] = mapped_column(String(32), nullable=False)
    dimension: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    auteur_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    value: Mapped[float] = mapped_column(Float, default=1.0)

    # Query context (for query-type signals)
    query_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    query_embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)

    # Evidence reference
    evidence_ref: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # Additional metadata
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SessionPreference(Base):
    """Session-level preferences (ephemeral).

    Stores real-time session state for immediate personalization.
    Expires after SESSION_TTL (default 1 hour).

    Attributes:
        session_id: Unique session identifier
        user_id: Optional linked user
        dimension_affinities: Session-specific dimension preferences
        auteur_affinities: Session-specific auteur preferences
        session_embedding: Real-time session embedding
        interaction_count: Number of interactions in session
        expires_at: Expiration timestamp
    """
    __tablename__ = "session_preferences"
    __table_args__ = (
        Index("ix_session_prefs_expires", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(160), nullable=True, index=True)

    # Session-level affinities
    dimension_affinities: Mapped[dict] = mapped_column(JSONB, default=dict)
    auteur_affinities: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Session embedding (computed from recent interactions)
    session_embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)

    # Session metrics
    interaction_count: Mapped[int] = mapped_column(Integer, default=0)
    last_interaction_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # TTL
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# GraphRAG Persistence Models
# =============================================================================

class GraphRAGCommunityReport(Base):
    """Pre-computed community summary for global search.

    Microsoft GraphRAG pattern: Hierarchical community summaries
    for map-reduce style global queries.

    Attributes:
        community_id: Unique community identifier
        level: Hierarchy level (0=leaf, higher=abstract)
        title: Community title
        summary: LLM-generated summary (200-500 tokens)
        key_findings: List of key findings
        entity_ids: Entity IDs belonging to this community
        auteur_keys: Auteur keys associated with this community
        rank: Importance score for ranking
    """
    __tablename__ = "graphrag_community_reports"
    __table_args__ = (
        Index("ix_community_reports_level", "level"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    community_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False)

    # Summary content
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    summary_embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)

    # Structured findings
    key_findings: Mapped[list] = mapped_column(JSONB, default=list)

    # Membership
    entity_ids: Mapped[list] = mapped_column(JSONB, default=list)
    auteur_keys: Mapped[list] = mapped_column(JSONB, default=list)

    # Ranking
    rank: Mapped[float] = mapped_column(Float, default=0.5)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GraphRAGEntity(Base):
    """Cached entities from knowledge graph.

    Persisted version of in-memory entities for efficient retrieval
    with vector embeddings for semantic search.

    Attributes:
        entity_id: Unique entity identifier (e.g., "auteur:bong")
        entity_type: Type (Auteur, Film, Technique, etc.)
        name: Display name
        name_embedding: Embedding of entity name
        description: Entity description
        description_embedding: Embedding of description
        properties: Additional properties (JSON)
        auteur_key: Associated auteur (if applicable)
        community_id: Assigned community
        degree: Number of relationships (connectivity)
    """
    __tablename__ = "graphrag_entities"
    __table_args__ = (
        Index("ix_graphrag_entities_type", "entity_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)

    # Name and description
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    name_embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)

    # Properties
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Association
    auteur_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    community_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # Graph metrics
    degree: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GraphRAGRelationship(Base):
    """Graph relationships between entities.

    Persisted version of in-memory relationships for efficient
    graph traversal queries.

    Attributes:
        source_entity_id: Source entity ID
        target_entity_id: Target entity ID
        relationship_type: Type (DIRECTED, USES_TECHNIQUE, etc.)
        weight: Relationship strength
        properties: Additional properties
        description: Relationship description
        auteur_key: Associated auteur
    """
    __tablename__ = "graphrag_relationships"
    __table_args__ = (
        Index("ix_graphrag_rel_source_type", "source_entity_id", "relationship_type"),
        Index("ix_graphrag_rel_target_type", "target_entity_id", "relationship_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_entity_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    target_entity_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False)

    # Weight and description
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Properties
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Association
    auteur_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "USER_EMBEDDING_DIM",
    "UserPreferenceProfile",
    "UserInteractionSignal",
    "SessionPreference",
    "GraphRAGCommunityReport",
    "GraphRAGEntity",
    "GraphRAGRelationship",
]
