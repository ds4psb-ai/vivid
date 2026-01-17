"""Character Consistency Schemas.

Pydantic models for StoryMem-based character consistency system.

Features:
- Character CRUD schemas
- Memory keyframe schemas
- Platform sync schemas
- Embedding metadata schemas

References:
- StoryMem Paper: arXiv:2512.19539
- DIMENSION_APP_MACRO_PLANNING_2026.md Part 11
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


# ============================================================================
# Enums
# ============================================================================

class PlatformType(str, Enum):
    """Supported video generation platforms."""
    VEO = "veo"
    KLING = "kling"
    RUNWAY = "runway"
    HAILUO = "hailuo"


class CharacterRole(str, Enum):
    """Character role in scene."""
    PROTAGONIST = "protagonist"
    SUPPORTING = "supporting"
    BACKGROUND = "background"


# ============================================================================
# Nested Schemas
# ============================================================================

class SourceImage(BaseModel):
    """Source image metadata."""
    url: str
    timestamp: Optional[datetime] = None
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_primary: bool = False


class MemoryKeyframe(BaseModel):
    """StoryMem-style memory keyframe.

    Stores keyframe data with quality metrics for character consistency.
    """
    frame_url: str
    timestamp: float = Field(..., ge=0.0, description="Timestamp in seconds")
    clip_score: float = Field(..., ge=0.0, le=1.0, description="CLIP similarity to character embedding")
    hps_score: float = Field(..., ge=0.0, le=1.0, description="HPSv3 aesthetic score")
    face_confidence: float = Field(..., ge=0.0, le=1.0, description="Face detection confidence")
    is_long_term: bool = Field(False, description="True if selected for long-term memory")


class PlatformRef(BaseModel):
    """Platform-specific reference data."""
    platform: PlatformType
    ref_id: Optional[str] = None
    last_sync: Optional[datetime] = None
    style_strength: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CharacterRef(BaseModel):
    """Character reference for video generation."""
    character_id: UUID
    platform_ref: Optional[PlatformRef] = None
    role: CharacterRole = CharacterRole.PROTAGONIST


# ============================================================================
# Request Schemas
# ============================================================================

class CharacterCreateRequest(BaseModel):
    """Create a new character.

    Supports both base64 image data and URL references.
    """
    name: str = Field(..., min_length=1, max_length=100, description="Character name")
    description: Optional[str] = Field(None, max_length=1000, description="Character description")
    tags: List[str] = Field(default_factory=list, max_length=20, description="Character tags")
    project_id: Optional[UUID] = Field(None, description="Associated project ID")

    # Initial reference image (mutually exclusive)
    reference_image: Optional[str] = Field(None, description="Base64 encoded image")
    reference_image_url: Optional[str] = Field(None, description="Image URL")

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip() if v else v

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, v: List[str]) -> List[str]:
        if not v:
            return []
        return [tag.strip().lower() for tag in v if tag.strip()][:20]


class CharacterUpdateRequest(BaseModel):
    """Update character metadata."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, max_length=20)
    primary_image_url: Optional[str] = None


class AddReferenceRequest(BaseModel):
    """Add reference images to existing character."""
    image_urls: List[str] = Field(default_factory=list, max_length=10)
    images_base64: List[str] = Field(default_factory=list, max_length=10)


class PlatformSyncRequest(BaseModel):
    """Request to sync character to a platform."""
    platform: PlatformType
    style_strength: Optional[float] = Field(0.8, ge=0.0, le=1.0)
    auto_update_memory: bool = Field(True, description="Update memory bank after generation")


class MemoryBankUpdateRequest(BaseModel):
    """Update memory bank from generated video."""
    video_url: str = Field(..., description="URL of the generated video")
    max_keyframes: int = Field(10, ge=1, le=50, description="Maximum keyframes to extract")
    long_term_count: int = Field(5, ge=1, le=20, description="Number of long-term keyframes to keep")


class CharacterSearchRequest(BaseModel):
    """Search characters by various criteria."""
    query: Optional[str] = Field(None, max_length=200)
    tags: Optional[List[str]] = None
    project_id: Optional[UUID] = None
    platform: Optional[PlatformType] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


# ============================================================================
# Response Schemas
# ============================================================================

class CharacterResponse(BaseModel):
    """Full character response."""
    id: UUID
    name: str
    description: Optional[str]
    tags: List[str]
    primary_image_url: Optional[str]
    source_images: List[SourceImage]
    memory_keyframes: List[MemoryKeyframe]
    platform_refs: Dict[str, PlatformRef]
    qdrant_point_id: Optional[str]
    project_id: Optional[UUID]
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime]
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="Evidence references: [\"db:characters:uuid\", \"qdrant:character_embeddings:point_id\"]",
    )

    model_config = {"from_attributes": True}


class CharacterSummaryResponse(BaseModel):
    """Lightweight character summary for lists."""
    id: UUID
    name: str
    primary_image_url: Optional[str]
    tags: List[str]
    keyframe_count: int
    platforms_synced: List[str]


class CharacterSimilarity(BaseModel):
    """Similar character search result."""
    character: CharacterSummaryResponse
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    match_type: Literal["face", "clip", "combined"]


class PlatformSyncResponse(BaseModel):
    """Platform synchronization response."""
    platform: PlatformType
    status: Literal["success", "pending", "failed"]
    platform_ref_id: Optional[str] = None
    message: Optional[str] = None


class MemoryBankResponse(BaseModel):
    """Memory bank update response."""
    character_id: UUID
    keyframes_extracted: int
    long_term_updated: int
    sliding_window_updated: int
    new_keyframes: List[MemoryKeyframe]
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="Evidence references: [\"db:characters:uuid\", \"qdrant:character_embeddings:point_id\"]",
    )


class CharacterListResponse(BaseModel):
    """Paginated character list."""
    items: List[CharacterSummaryResponse]
    total: int
    limit: int
    offset: int


# ============================================================================
# Embedding Schemas (Internal)
# ============================================================================

class EmbeddingMetadata(BaseModel):
    """Metadata for character embeddings stored in Qdrant."""
    character_id: str
    user_id: str
    project_id: Optional[str] = None
    name: str
    tags: List[str] = Field(default_factory=list)
    source_image_urls: List[str] = Field(default_factory=list)
    keyframe_timestamps: List[float] = Field(default_factory=list)
    platform_refs: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: Optional[str] = None


class KeyframeSelectionConfig(BaseModel):
    """Configuration for StoryMem keyframe selection."""
    clip_weight: float = Field(0.4, ge=0.0, le=1.0)
    hps_weight: float = Field(0.3, ge=0.0, le=1.0)
    face_weight: float = Field(0.3, ge=0.0, le=1.0)
    min_clip_score: float = Field(0.7, ge=0.0, le=1.0)
    min_hps_score: float = Field(0.5, ge=0.0, le=1.0)
    min_face_confidence: float = Field(0.8, ge=0.0, le=1.0)
    diversity_threshold: float = Field(0.15, ge=0.0, le=1.0, description="Minimum CLIP distance between keyframes")
