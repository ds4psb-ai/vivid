"""Reference Analysis SQLAlchemy Models (4D Reference Decoder).

Database models for the 2026 Expert Workflow reference analysis system:
- Style presets for reusable visual styles
- Reference library for uploaded media with analysis
- Reference scenes for RAG and cross-modal search

Tables:
- style_presets: Reusable visual style configurations
- reference_items: Uploaded references (video/image) with analysis
- reference_scenes: Indexed scenes for similarity search

Best Practices (2026):
- SQLAlchemy 2.0 Mapped style
- PostgreSQL JSONB with GIN indexes
- evidence_refs as List[str]
- Qdrant integration via point IDs

References:
- docs/research/02_REFERENCE_DECODER_RESEARCH.md
- Part 9: Multi-Modal Embedding
- Part 10: Multi-RAG Router
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Boolean,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    pass


# =============================================================================
# Enums
# =============================================================================


class ReferenceType(str, Enum):
    """Type of reference media."""
    VIDEO = "video"
    IMAGE = "image"


class AnalysisDepth(str, Enum):
    """Analysis depth level."""
    QUICK = "quick"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


# =============================================================================
# StylePreset Model
# =============================================================================


class StylePreset(Base):
    """Reusable visual style extracted from references.

    Stores StyleExtractionResult data for consistent style application
    across multiple generations (Expert Workflow: "스타일 프롬프트라고 따로 둬요").

    Key JSONB Fields:
        style_data: Full StyleExtractionResult
            - style_tags: List[str]
            - style_prompt: str (50-100 words, reusable)
            - color_palette: List[str] (hex codes)
            - lighting: str (dramatic, soft, neon, etc.)
            - composition: str (centered, rule-of-thirds, etc.)
            - mood: str (energetic, melancholic, etc.)
            - camera_angle: Optional[str]
            - reference_artists: List[str]
            - confidence: float

    Attributes:
        id: Unique preset identifier
        user_id: Owner user ID
        name: Display name for the preset
        description: Optional description
        tags: Searchable tags for filtering
        style_data: Full StyleExtractionResult as JSONB
        color_palette: Extracted colors (denormalized for fast filtering)
        thumbnail_url: Preview thumbnail
        source_reference_id: Original reference this was extracted from
        is_public: Whether the preset is shared publicly
        usage_count: How many times this preset was used
    """
    __tablename__ = "style_presets"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Ownership
    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    # Metadata
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    tags: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment='["anime", "cinematic", "neon-noir", ...]',
    )

    # Style data (Full StyleExtractionResult)
    style_data: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Full StyleExtractionResult from style_extractor.py",
    )

    # Denormalized for fast filtering
    color_palette: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment='["#FF5733", "#33FF57", ...] - dominant colors',
    )
    lighting: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="dramatic, soft, neon, natural, etc.",
    )
    mood: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="energetic, melancholic, mysterious, etc.",
    )

    # Preview
    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )

    # Source reference
    source_reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reference_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Sharing & usage
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    usage_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Qdrant reference for style embedding
    qdrant_point_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        comment="Qdrant point ID for style embedding vector",
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
    source_reference: Mapped[Optional["ReferenceItem"]] = relationship(
        "ReferenceItem",
        back_populates="extracted_style",
        foreign_keys=[source_reference_id],
    )

    # Indexes
    __table_args__ = (
        Index("ix_style_presets_user_id", "user_id"),
        Index("ix_style_presets_tags", "tags", postgresql_using="gin"),
        Index("ix_style_presets_lighting", "lighting"),
        Index("ix_style_presets_mood", "mood"),
        Index("ix_style_presets_public", "is_public"),
        Index(
            "ix_style_presets_name_search",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<StylePreset(id={self.id}, name={self.name})>"

    @property
    def style_prompt(self) -> str:
        """Reusable style prompt for AI generation."""
        return self.style_data.get("style_prompt", "")

    @property
    def style_tags(self) -> list:
        """Style tags from extraction."""
        return self.style_data.get("style_tags", [])

    @property
    def confidence(self) -> float:
        """Extraction confidence score."""
        return self.style_data.get("confidence", 0.0)


# =============================================================================
# ReferenceItem Model
# =============================================================================


class ReferenceItem(Base):
    """Uploaded reference media with analysis results.

    Stores video or image references with their complete analysis
    (VideoReferenceAnalysis or ImageReferenceAnalysis).

    Key JSONB Fields:
        analysis_result: Full analysis result
            For videos:
                - total_duration, frame_count, fps
                - frames: List[FrameAnalysis]
                - scenes: List[SceneSegment]
                - suggested_shots: List[ShotSuggestion]
            For images:
                - description, objects, composition_analysis
                - recreation_prompt, similar_references

        moodboard_frames: List[str] (base64 encoded key frames)

    Attributes:
        id: Unique reference identifier
        user_id: Owner user ID
        project_id: Optional project association
        name: Display name
        reference_type: "video" or "image"
        source_url: URL to the uploaded media
        file_size_bytes: File size
        mime_type: MIME type of the media
        analysis_depth: quick/detailed/comprehensive
        analysis_result: Full analysis as JSONB
        moodboard_frames: Key frames for moodboard
        extracted_style_id: Link to extracted StylePreset
        qdrant_point_id: Qdrant vector reference
        evidence_refs: References used in analysis
    """
    __tablename__ = "reference_items"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Ownership
    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # Metadata
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    tags: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    # Media info
    reference_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="video or image",
    )
    source_url: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )
    file_size_bytes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    mime_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    duration_seconds: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Video duration in seconds",
    )
    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )

    # Analysis
    analysis_depth: Mapped[str] = mapped_column(
        String(20),
        default="detailed",
        nullable=False,
        comment="quick, detailed, comprehensive",
    )
    analysis_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment="pending, processing, completed, failed",
    )
    analysis_result: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="VideoReferenceAnalysis or ImageReferenceAnalysis",
    )
    analysis_confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Overall analysis confidence (0.0-1.0)",
    )

    # Moodboard
    moodboard_frames: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment="Base64 encoded key frames for moodboard",
    )

    # Style extraction link
    extracted_style_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Link to StylePreset extracted from this reference",
    )

    # Multimodal embedding references (Qdrant)
    qdrant_point_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        comment="ImageBind/Vertex embedding in Qdrant",
    )

    # Evidence refs (RAG sources used in analysis)
    evidence_refs: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment='["rag:cinematography:technique_id", "db:famous_scenes:scene_id"]',
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
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When analysis was completed",
    )

    # Relationships
    extracted_style: Mapped[Optional["StylePreset"]] = relationship(
        "StylePreset",
        back_populates="source_reference",
        foreign_keys="StylePreset.source_reference_id",
    )

    # Indexes
    __table_args__ = (
        Index("ix_reference_items_user_project", "user_id", "project_id"),
        Index("ix_reference_items_tags", "tags", postgresql_using="gin"),
        Index("ix_reference_items_type", "reference_type"),
        Index("ix_reference_items_status", "analysis_status"),
        Index("ix_reference_items_created", "created_at"),
        Index(
            "ix_reference_items_name_search",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        CheckConstraint(
            "reference_type IN ('video', 'image')",
            name="ck_reference_items_type",
        ),
        CheckConstraint(
            "analysis_status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_reference_items_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<ReferenceItem(id={self.id}, name={self.name}, type={self.reference_type})>"

    @property
    def is_video(self) -> bool:
        """Check if reference is video."""
        return self.reference_type == ReferenceType.VIDEO.value

    @property
    def is_image(self) -> bool:
        """Check if reference is image."""
        return self.reference_type == ReferenceType.IMAGE.value

    @property
    def is_analyzed(self) -> bool:
        """Check if analysis is complete."""
        return self.analysis_status == "completed"

    @property
    def frame_count(self) -> int:
        """Number of analyzed frames (video only)."""
        return self.analysis_result.get("frame_count", 0)

    @property
    def scene_count(self) -> int:
        """Number of detected scenes (video only)."""
        scenes = self.analysis_result.get("scenes", [])
        return len(scenes)

    @property
    def suggested_shots(self) -> list:
        """Suggested shots for recreation (video only)."""
        return self.analysis_result.get("suggested_shots", [])


# =============================================================================
# ReferenceScene Model (for RAG)
# =============================================================================


class ReferenceScene(Base):
    """Indexed scene for RAG and cross-modal similarity search.

    Stores famous scenes and their analysis for retrieval.
    Based on famous_scene_analysis dataset from research doc.

    Key JSONB Fields:
        cinematography: Camera, composition, lighting analysis
        color_analysis: Dominant colors, grading style
        auteur_tags: Associated director/cinematographer styles
        recreation_guide: How to recreate this scene

    Attributes:
        id: Unique scene identifier
        scene_key: Unique key (e.g., "parasite_stairs_sequence")
        film_title: Movie title
        film_year: Release year
        director: Director name
        cinematographer: Cinematographer name
        timestamp: Scene timestamp in film
        description: Scene description
        cinematography: Camera and lighting analysis
        color_analysis: Color palette and grading
        auteur_tags: Style tags
        recreation_guide: Recreation instructions
        qdrant_point_id: Vector embedding reference
    """
    __tablename__ = "reference_scenes"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Unique identifier
    scene_key: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        nullable=False,
        comment="Unique key like 'parasite_stairs_sequence'",
    )

    # Film metadata
    film_title: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )
    film_year: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    director: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        index=True,
    )
    cinematographer: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        index=True,
    )

    # Scene info
    timestamp: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Timestamp range like '1:23:45 - 1:25:30'",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    thematic_significance: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Analysis data
    cinematography: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="shot_types, movements, lens, composition, lighting",
    )
    color_analysis: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="dominant_colors, color_meaning, grading_style",
    )
    mise_en_scene: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="set_design, props, blocking, costume",
    )
    sound_design: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="diegetic, score, silence",
    )

    # Tags and categorization
    auteur_tags: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment='["bong_joon_ho", "roger_deakins", ...]',
    )
    technique_tags: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment='["dolly_zoom", "rembrandt_lighting", ...]',
    )
    mood_tags: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment='["tense", "mysterious", "intimate", ...]',
    )
    genre_tags: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment='["thriller", "drama", "noir", ...]',
    )

    # Recreation guide
    recreation_guide: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="key_elements, ai_prompt_suggestion, recommended_tool, difficulty",
    )

    # Preview
    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )
    video_clip_url: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )

    # Multimodal embedding (Qdrant)
    qdrant_point_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        comment="ImageBind/Vertex embedding for cross-modal search",
    )

    # Source tracking
    source: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="every_frame_a_painting, studiobinder, academic, etc.",
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

    # Indexes
    __table_args__ = (
        Index("ix_reference_scenes_director", "director"),
        Index("ix_reference_scenes_film", "film_title"),
        Index("ix_reference_scenes_year", "film_year"),
        Index("ix_reference_scenes_auteur_tags", "auteur_tags", postgresql_using="gin"),
        Index("ix_reference_scenes_technique_tags", "technique_tags", postgresql_using="gin"),
        Index("ix_reference_scenes_mood_tags", "mood_tags", postgresql_using="gin"),
        Index("ix_reference_scenes_genre_tags", "genre_tags", postgresql_using="gin"),
        Index(
            "ix_reference_scenes_description_search",
            "description",
            postgresql_using="gin",
            postgresql_ops={"description": "gin_trgm_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<ReferenceScene(scene_key={self.scene_key}, film={self.film_title})>"

    @property
    def ai_recreation_prompt(self) -> str:
        """AI prompt suggestion from recreation guide."""
        return self.recreation_guide.get("ai_prompt_suggestion", "")

    @property
    def recommended_tool(self) -> str:
        """Recommended AI tool for recreation."""
        return self.recreation_guide.get("recommended_tool", "veo")

    @property
    def dominant_colors(self) -> list:
        """Dominant colors from color analysis."""
        return self.color_analysis.get("dominant_colors", [])


# =============================================================================
# CinematographyTechnique Model (for RAG)
# =============================================================================


class CinematographyTechnique(Base):
    """Cinematography technique reference for RAG.

    Based on cinematography_techniques dataset from research doc.

    Attributes:
        technique_id: Unique key (e.g., "dolly_zoom")
        category: shot_type, camera_movement, lighting, composition, lens, color
        name_en: English name
        name_ko: Korean name
        description: Detailed description
        emotional_effect: List of emotional effects
        narrative_use: When to use narratively
        famous_examples: Example usages
        ai_reproducibility: How to reproduce with AI
    """
    __tablename__ = "cinematography_techniques"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Unique identifier
    technique_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="Unique key like 'dolly_zoom'",
    )

    # Categorization
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="shot_type, camera_movement, lighting, composition, lens, color",
    )

    # Names
    name_en: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    name_ko: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    aliases: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment='["Vertigo effect", "Zolly", "Contra-zoom"]',
    )

    # Description
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Effects and usage
    emotional_effect: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment='["disorientation", "realization", "dread"]',
    )
    narrative_use: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment='["character epiphany", "horror reveal"]',
    )

    # Examples
    famous_examples: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment='[{film, scene, director, year, description}]',
    )

    # Execution details
    execution_details: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="equipment, difficulty, duration_typical",
    )

    # AI reproducibility
    ai_reproducibility: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="reproducible, platforms, prompt_keywords, limitations",
    )

    # Related techniques
    related_techniques: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment='["push_in", "zoom_in", ...]',
    )

    # Source tracking
    source: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
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

    # Indexes
    __table_args__ = (
        Index("ix_cine_techniques_category", "category"),
        Index("ix_cine_techniques_aliases", "aliases", postgresql_using="gin"),
        Index("ix_cine_techniques_emotional", "emotional_effect", postgresql_using="gin"),
        Index("ix_cine_techniques_narrative", "narrative_use", postgresql_using="gin"),
        Index(
            "ix_cine_techniques_name_search",
            "name_en",
            postgresql_using="gin",
            postgresql_ops={"name_en": "gin_trgm_ops"},
        ),
        CheckConstraint(
            "category IN ('shot_type', 'camera_movement', 'lighting', 'composition', 'lens', 'color')",
            name="ck_cine_techniques_category",
        ),
    )

    def __repr__(self) -> str:
        return f"<CinematographyTechnique(id={self.technique_id}, name={self.name_en})>"

    @property
    def is_ai_reproducible(self) -> bool:
        """Check if technique can be reproduced with AI."""
        return self.ai_reproducibility.get("reproducible", False)

    @property
    def ai_prompt_keywords(self) -> list:
        """Keywords for AI prompts."""
        return self.ai_reproducibility.get("prompt_keywords", [])

    @property
    def supported_platforms(self) -> list:
        """AI platforms that support this technique."""
        return self.ai_reproducibility.get("platforms", [])
