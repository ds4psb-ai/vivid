"""Character Consistency SQLAlchemy Models.

Database models for StoryMem-based character consistency system.

Tables:
- characters: Character metadata and memory bank
- character_appearances: Shot-level character tracking

References:
- StoryMem Paper: arXiv:2512.19539
- DIMENSION_APP_MACRO_PLANNING_2026.md Part 11
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models import User


class Character(Base):
    """Character entity with StoryMem memory bank.

    Stores character metadata, reference images, and memory keyframes
    for cross-shot consistency in video generation.

    Attributes:
        id: Unique character identifier
        user_id: Owner user ID
        project_id: Optional associated project
        name: Character display name
        description: Character description
        tags: Searchable tags (e.g., ["protagonist", "human", "female"])
        source_images: List of reference images with metadata
        primary_image_url: Main display image
        qdrant_point_id: Reference to Qdrant vector (face/clip embeddings)
        platform_refs: Platform-specific references (Veo, Kling, Runway)
        memory_keyframes: StoryMem keyframe bank
    """
    __tablename__ = "characters"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Ownership
    user_id: Mapped[str] = mapped_column(
        String(255),
        # ForeignKey("users.id", ondelete="CASCADE"),  # TODO: Re-enable when users table exists
        nullable=False,
        index=True,
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("projects.id", ondelete="SET NULL"),  # TODO: Re-enable when projects table exists
        nullable=True,
        index=True,
    )

    # Metadata
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Reference images
    source_images: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment="[{url, timestamp, quality_score, is_primary}]",
    )
    primary_image_url: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    # Qdrant reference (embeddings stored externally)
    qdrant_point_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        comment="Qdrant point ID for face/clip embeddings",
    )

    # Platform-specific references
    platform_refs: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment='{"veo": {...}, "kling": {...}, "runway": {...}}',
    )

    # StoryMem Memory Bank
    memory_keyframes: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment="StoryMem keyframes: [{frame_url, timestamp, clip_score, hps_score, face_confidence, is_long_term}]",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        onupdate=datetime.utcnow,
        nullable=True,
    )

    # Relationships
    appearances: Mapped[List["CharacterAppearance"]] = relationship(
        "CharacterAppearance",
        back_populates="character",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("ix_characters_user_project", "user_id", "project_id"),
        Index("ix_characters_tags", "tags", postgresql_using="gin"),
        Index("ix_characters_name_search", "name", postgresql_using="gin",
              postgresql_ops={"name": "gin_trgm_ops"}),
    )

    def __repr__(self) -> str:
        return f"<Character(id={self.id}, name={self.name})>"

    @property
    def keyframe_count(self) -> int:
        """Number of keyframes in memory bank."""
        return len(self.memory_keyframes) if self.memory_keyframes else 0

    @property
    def long_term_keyframes(self) -> list:
        """Long-term memory keyframes."""
        if not self.memory_keyframes:
            return []
        return [kf for kf in self.memory_keyframes if kf.get("is_long_term")]

    @property
    def sliding_window_keyframes(self) -> list:
        """Recent (sliding window) keyframes."""
        if not self.memory_keyframes:
            return []
        return [kf for kf in self.memory_keyframes if not kf.get("is_long_term")]

    @property
    def platforms_synced(self) -> list:
        """List of platforms with active sync."""
        if not self.platform_refs:
            return []
        return [k for k, v in self.platform_refs.items() if v.get("ref_id")]


class CharacterAppearance(Base):
    """Character appearance tracking per shot/video.

    Records each time a character appears in generated content,
    enabling consistency analysis and quality tracking.

    Attributes:
        id: Unique appearance identifier
        character_id: Reference to character
        shot_id: Optional shot reference (from storyboard)
        video_generation_id: Video generation run ID
        scene_description: Description of the scene
        pose_description: Character pose in this shot
        emotion: Character emotion/expression
        consistency_score: Auto-computed consistency (0.0-1.0)
        user_rating: User feedback (1-5 stars)
    """
    __tablename__ = "character_appearances"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # References
    character_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("shots.id", ondelete="SET NULL"),  # TODO: Re-enable when shots table exists
        nullable=True,
        index=True,
    )
    video_generation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # Appearance context
    scene_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pose_description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    emotion: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Quality metrics
    consistency_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Auto-computed CLIP/Face similarity (0.0-1.0)",
    )
    user_rating: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="User feedback (1-5 stars)",
    )

    # Generated frame reference
    generated_frame_url: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
        comment="Best frame from this appearance",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    character: Mapped["Character"] = relationship(
        "Character",
        back_populates="appearances",
    )

    # Indexes
    __table_args__ = (
        Index("ix_appearances_character_video", "character_id", "video_generation_id"),
    )

    def __repr__(self) -> str:
        return f"<CharacterAppearance(id={self.id}, character_id={self.character_id})>"
