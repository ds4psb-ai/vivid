"""Style Preset Schemas for Style Library CRUD API.

Pydantic models for the Style Library management system,
enabling save/search/apply of reusable visual styles extracted
from references via 4D Reference Decoder.

Based on: docs/research/02_REFERENCE_DECODER_RESEARCH.md
Model: backend/app/models_reference.py:StylePreset
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Request Schemas
# =============================================================================


class StylePresetCreateRequest(BaseModel):
    """Request to create a new style preset.

    Typically called after `/4d/extract-style` returns StyleExtractionResult.
    User provides a name and optional metadata.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Display name for the style preset",
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional description of the style",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Searchable tags (anime, cinematic, noir, etc.)",
    )
    style_data: Dict[str, Any] = Field(
        ...,
        description="Full StyleExtractionResult from style_extractor.py",
    )
    color_palette: List[str] = Field(
        default_factory=list,
        description="Dominant colors as hex codes (#FF5733)",
    )
    lighting: Optional[str] = Field(
        None,
        max_length=50,
        description="Lighting type (dramatic, soft, neon, natural)",
    )
    mood: Optional[str] = Field(
        None,
        max_length=50,
        description="Overall mood (energetic, melancholic, mysterious)",
    )
    thumbnail_url: Optional[str] = Field(
        None,
        max_length=2000,
        description="Preview thumbnail URL",
    )
    source_reference_id: Optional[UUID] = Field(
        None,
        description="Original reference this was extracted from",
    )
    is_public: bool = Field(
        False,
        description="Whether to share this preset publicly",
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Normalize and validate tags."""
        if not v:
            return v
        # Lowercase, strip whitespace, remove duplicates
        normalized = list(dict.fromkeys(tag.strip().lower() for tag in v if tag.strip()))
        return normalized[:20]  # Limit to 20 tags

    @field_validator("color_palette")
    @classmethod
    def validate_colors(cls, v: List[str]) -> List[str]:
        """Validate hex color codes."""
        import re
        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
        validated = []
        for color in v:
            color = color.strip().upper()
            if not color.startswith("#"):
                color = f"#{color}"
            if hex_pattern.match(color):
                validated.append(color)
        return validated[:10]  # Limit to 10 colors


class StylePresetUpdateRequest(BaseModel):
    """Request to update an existing style preset (partial update).

    Only provided fields will be updated.
    """
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="New display name",
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="New description",
    )
    tags: Optional[List[str]] = Field(
        None,
        description="New tags (replaces existing)",
    )
    is_public: Optional[bool] = Field(
        None,
        description="Update public visibility",
    )
    thumbnail_url: Optional[str] = Field(
        None,
        max_length=2000,
        description="New thumbnail URL",
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Normalize and validate tags."""
        if v is None:
            return v
        normalized = list(dict.fromkeys(tag.strip().lower() for tag in v if tag.strip()))
        return normalized[:20]


class StylePresetSearchParams(BaseModel):
    """Search and filter parameters for listing style presets."""
    q: Optional[str] = Field(
        None,
        max_length=100,
        description="Search query for name (trigram search)",
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Filter by tags (any match)",
    )
    lighting: Optional[str] = Field(
        None,
        max_length=50,
        description="Filter by lighting type",
    )
    mood: Optional[str] = Field(
        None,
        max_length=50,
        description="Filter by mood",
    )
    is_public: Optional[bool] = Field(
        None,
        description="Filter by public visibility",
    )
    include_public: bool = Field(
        True,
        description="Include public presets from other users",
    )
    sort_by: str = Field(
        "created_at",
        description="Sort field (created_at, name, usage_count)",
    )
    sort_order: str = Field(
        "desc",
        description="Sort order (asc, desc)",
    )
    offset: int = Field(
        0,
        ge=0,
        description="Pagination offset",
    )
    limit: int = Field(
        20,
        ge=1,
        le=100,
        description="Pagination limit",
    )


# =============================================================================
# Response Schemas
# =============================================================================


class StylePresetResponse(BaseModel):
    """Single style preset response."""
    id: UUID
    user_id: str
    name: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    style_data: Dict[str, Any] = Field(default_factory=dict)
    color_palette: List[str] = Field(default_factory=list)
    lighting: Optional[str] = None
    mood: Optional[str] = None
    thumbnail_url: Optional[str] = None
    source_reference_id: Optional[UUID] = None
    is_public: bool = False
    usage_count: int = 0
    qdrant_point_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Computed properties
    style_prompt: Optional[str] = Field(
        None,
        description="Reusable style prompt (from style_data)",
    )
    style_tags: List[str] = Field(
        default_factory=list,
        description="Style tags from extraction (from style_data)",
    )
    confidence: float = Field(
        0.0,
        description="Extraction confidence (from style_data)",
    )

    # Ownership indicator for UI
    is_owner: bool = Field(
        False,
        description="Whether current user owns this preset",
    )

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, preset: Any, current_user_id: Optional[str] = None) -> "StylePresetResponse":
        """Create response from StylePreset model with computed fields."""
        style_data = preset.style_data or {}
        return cls(
            id=preset.id,
            user_id=preset.user_id,
            name=preset.name,
            description=preset.description,
            tags=preset.tags or [],
            style_data=style_data,
            color_palette=preset.color_palette or [],
            lighting=preset.lighting,
            mood=preset.mood,
            thumbnail_url=preset.thumbnail_url,
            source_reference_id=preset.source_reference_id,
            is_public=preset.is_public,
            usage_count=preset.usage_count,
            qdrant_point_id=preset.qdrant_point_id,
            created_at=preset.created_at,
            updated_at=preset.updated_at,
            style_prompt=style_data.get("style_prompt", ""),
            style_tags=style_data.get("style_tags", []),
            confidence=style_data.get("confidence", 0.0),
            is_owner=current_user_id == preset.user_id if current_user_id else False,
        )


class StylePresetListResponse(BaseModel):
    """Paginated list of style presets."""
    items: List[StylePresetResponse] = Field(
        default_factory=list,
        description="List of style presets",
    )
    total: int = Field(
        0,
        description="Total count matching the query",
    )
    offset: int = Field(
        0,
        description="Current offset",
    )
    limit: int = Field(
        20,
        description="Current limit",
    )
    has_more: bool = Field(
        False,
        description="Whether more results exist",
    )


class StylePresetApplyResponse(BaseModel):
    """Response when applying a style preset.

    Returns the style_prompt for use in 3D Visual Realizer
    and increments usage_count.
    """
    id: UUID
    name: str
    style_prompt: str = Field(
        ...,
        description="Reusable style prompt for AI generation",
    )
    style_tags: List[str] = Field(
        default_factory=list,
        description="Style tags for reference",
    )
    color_palette: List[str] = Field(
        default_factory=list,
        description="Color palette for reference",
    )
    lighting: Optional[str] = None
    mood: Optional[str] = None
    usage_count: int = Field(
        0,
        description="Updated usage count after this application",
    )
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="Evidence references (db:style_presets:{uuid})",
    )


class StylePresetDiscoverResponse(BaseModel):
    """Response for discovering public style presets."""
    items: List[StylePresetResponse] = Field(
        default_factory=list,
        description="Popular public style presets",
    )
    total: int = Field(
        0,
        description="Total public presets available",
    )
    categories: Dict[str, int] = Field(
        default_factory=dict,
        description="Tag counts for filtering (tag -> count)",
    )
