"""Reference Library Service for 4D Reference Decoder.

CRUD operations for user reference library:
- Reference items (videos/images with analysis)
- Style presets extracted from references
- Cross-modal search integration

2026 Best Practices:
- SQLAlchemy 2.0 async patterns
- Pydantic v2 validation
- evidence_refs as List[str]
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import and_, or_, select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB

# Generic type for paginated responses
T = TypeVar("T")

from app.models_reference import (
    ReferenceItem,
    StylePreset,
    ReferenceType,
    AnalysisDepth,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DTOs (Pydantic v2)
# =============================================================================


class ReferenceItemCreate(BaseModel):
    """DTO for creating a reference item."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    reference_type: str = Field(..., pattern="^(video|image)$")
    source_url: str = Field(..., max_length=2000)
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    duration_seconds: Optional[float] = None
    thumbnail_url: Optional[str] = None
    project_id: Optional[str] = None
    analysis_depth: str = Field(default="detailed", pattern="^(quick|detailed|comprehensive)$")


class ReferenceItemUpdate(BaseModel):
    """DTO for updating a reference item."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class ReferenceItemResponse(BaseModel):
    """Response DTO for reference item."""

    id: str
    user_id: str
    project_id: Optional[str]
    name: str
    description: Optional[str]
    tags: List[str]
    reference_type: str
    source_url: str
    file_size_bytes: Optional[int]
    mime_type: Optional[str]
    duration_seconds: Optional[float]
    thumbnail_url: Optional[str]
    analysis_depth: str
    analysis_status: str
    analysis_result: Dict[str, Any]
    analysis_confidence: Optional[float]
    moodboard_frames: List[str]
    extracted_style_id: Optional[str]
    evidence_refs: List[str]
    created_at: datetime
    updated_at: Optional[datetime]
    analyzed_at: Optional[datetime]

    model_config = {"from_attributes": True}

    @field_validator("id", "user_id", "project_id", "extracted_style_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID to string if needed."""
        if v is not None and hasattr(v, "hex"):
            return str(v)
        return v


class StylePresetCreate(BaseModel):
    """DTO for creating a style preset."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    style_data: Dict[str, Any] = Field(default_factory=dict)
    style_vector: Optional[List[float]] = None
    color_palette: List[str] = Field(default_factory=list)
    lighting: Optional[str] = None
    mood: Optional[str] = None
    thumbnail_url: Optional[str] = None
    source_reference_id: Optional[str] = None
    auteur_references: List[str] = Field(default_factory=list)
    is_public: bool = False


class StylePresetUpdate(BaseModel):
    """DTO for updating a style preset."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    style_data: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None


class StylePresetResponse(BaseModel):
    """Response DTO for style preset."""

    id: str
    user_id: str
    name: str
    description: Optional[str]
    tags: List[str]
    style_data: Dict[str, Any]
    style_vector: Optional[List[float]] = None
    color_palette: List[str]
    lighting: Optional[str]
    mood: Optional[str]
    thumbnail_url: Optional[str]
    source_reference_id: Optional[str]
    auteur_references: List[str] = []
    is_public: bool
    usage_count: int = 0
    style_prompt: str = ""
    confidence: float = 0.0
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}

    @field_validator("id", "user_id", "source_reference_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID to string if needed."""
        if v is not None and hasattr(v, "hex"):
            return str(v)
        return v


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper with generic type support."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ReferenceItemFilter(BaseModel):
    """Filters for reference library queries."""

    reference_type: Optional[str] = None
    analysis_status: Optional[str] = None
    tags: Optional[List[str]] = None
    project_id: Optional[str] = None
    search: Optional[str] = None


# Alias for backward compatibility
ReferenceLibraryFilters = ReferenceItemFilter


class StylePresetFilters(BaseModel):
    """Filters for style preset queries."""

    lighting: Optional[str] = None
    mood: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    search_query: Optional[str] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# =============================================================================
# Reference Library Service
# =============================================================================


class ReferenceLibraryService:
    """Service for managing user reference library.

    Provides CRUD operations for:
    - Reference items (uploaded videos/images)
    - Style presets (extracted visual styles)
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    # =========================================================================
    # Reference Items CRUD
    # =========================================================================

    async def create_reference_item(
        self,
        user_id: str,
        data: ReferenceItemCreate,
    ) -> ReferenceItem:
        """Create a new reference item.

        Args:
            user_id: Owner user ID
            data: Reference item creation data

        Returns:
            Created ReferenceItem
        """
        item = ReferenceItem(
            user_id=user_id,
            name=data.name,
            description=data.description,
            tags=data.tags,
            reference_type=data.reference_type,
            source_url=data.source_url,
            file_size_bytes=data.file_size_bytes,
            mime_type=data.mime_type,
            duration_seconds=data.duration_seconds,
            thumbnail_url=data.thumbnail_url,
            project_id=uuid.UUID(data.project_id) if data.project_id else None,
            analysis_depth=data.analysis_depth,
            analysis_status="pending",
            analysis_result={},
            moodboard_frames=[],
            evidence_refs=[],
        )

        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)

        logger.info(f"Created reference item: {item.id} for user {user_id}")
        return item

    async def get_reference_item(
        self,
        user_id: str,
        item_id: str,
    ) -> Optional[ReferenceItem]:
        """Get a reference item by ID.

        Args:
            user_id: Owner user ID (for authorization)
            item_id: Reference item ID

        Returns:
            ReferenceItem if found and owned by user, None otherwise
        """
        stmt = select(ReferenceItem).where(
            and_(
                ReferenceItem.id == uuid.UUID(item_id),
                ReferenceItem.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_reference_items(
        self,
        user_id: str,
        filters: Optional[ReferenceLibraryFilters] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ReferenceItem], int]:
        """Get paginated reference items for a user.

        Args:
            user_id: Owner user ID
            filters: Optional filters
            page: Page number (1-based)
            page_size: Items per page

        Returns:
            Tuple of (items, total_count)
        """
        conditions = [ReferenceItem.user_id == user_id]

        if filters:
            if filters.reference_type:
                conditions.append(ReferenceItem.reference_type == filters.reference_type)
            if filters.analysis_status:
                conditions.append(ReferenceItem.analysis_status == filters.analysis_status)
            if filters.project_id:
                conditions.append(ReferenceItem.project_id == uuid.UUID(filters.project_id))
            if filters.tags:
                # JSONB contains any of the tags
                conditions.append(
                    ReferenceItem.tags.contains(filters.tags)
                )
            if filters.search:
                # Trigram search on name
                conditions.append(
                    ReferenceItem.name.ilike(f"%{filters.search}%")
                )

        # Count query
        count_stmt = select(func.count()).select_from(ReferenceItem).where(and_(*conditions))
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Items query
        stmt = (
            select(ReferenceItem)
            .where(and_(*conditions))
            .order_by(ReferenceItem.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def update_reference_item(
        self,
        user_id: str,
        item_id: str,
        data: ReferenceItemUpdate,
    ) -> Optional[ReferenceItem]:
        """Update a reference item.

        Args:
            user_id: Owner user ID
            item_id: Reference item ID
            data: Update data

        Returns:
            Updated ReferenceItem if found, None otherwise
        """
        item = await self.get_reference_item(user_id, item_id)
        if not item:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)

        await self.db.flush()
        await self.db.refresh(item)

        logger.info(f"Updated reference item: {item_id}")
        return item

    async def delete_reference_item(
        self,
        user_id: str,
        item_id: str,
    ) -> bool:
        """Delete a reference item.

        Args:
            user_id: Owner user ID
            item_id: Reference item ID

        Returns:
            True if deleted, False if not found
        """
        stmt = delete(ReferenceItem).where(
            and_(
                ReferenceItem.id == uuid.UUID(item_id),
                ReferenceItem.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)

        if result.rowcount > 0:
            logger.info(f"Deleted reference item: {item_id}")
            return True
        return False

    async def update_analysis_result(
        self,
        item_id: str,
        analysis_result: Dict[str, Any],
        confidence: float,
        moodboard_frames: List[str],
        evidence_refs: List[str],
    ) -> Optional[ReferenceItem]:
        """Update analysis result for a reference item.

        Called after ReferenceAnalyzer completes analysis.

        Args:
            item_id: Reference item ID
            analysis_result: Analysis result dict
            confidence: Analysis confidence score
            moodboard_frames: Base64 encoded key frames
            evidence_refs: List of evidence references

        Returns:
            Updated ReferenceItem
        """
        stmt = (
            update(ReferenceItem)
            .where(ReferenceItem.id == uuid.UUID(item_id))
            .values(
                analysis_result=analysis_result,
                analysis_confidence=confidence,
                analysis_status="completed",
                moodboard_frames=moodboard_frames,
                evidence_refs=evidence_refs,
                analyzed_at=datetime.utcnow(),
            )
            .returning(ReferenceItem)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # =========================================================================
    # Style Presets CRUD
    # =========================================================================

    async def create_style_preset(
        self,
        user_id: str,
        data: StylePresetCreate,
    ) -> StylePreset:
        """Create a new style preset.

        Args:
            user_id: Owner user ID
            data: Style preset creation data

        Returns:
            Created StylePreset
        """
        preset = StylePreset(
            user_id=user_id,
            name=data.name,
            description=data.description,
            tags=data.tags,
            style_data=data.style_data,
            color_palette=data.color_palette,
            lighting=data.lighting,
            mood=data.mood,
            thumbnail_url=data.thumbnail_url,
            source_reference_id=uuid.UUID(data.source_reference_id) if data.source_reference_id else None,
            is_public=data.is_public,
            usage_count=0,
        )

        self.db.add(preset)
        await self.db.flush()
        await self.db.refresh(preset)

        logger.info(f"Created style preset: {preset.id} for user {user_id}")
        return preset

    async def get_style_preset(
        self,
        user_id: str,
        preset_id: str,
        allow_public: bool = True,
    ) -> Optional[StylePreset]:
        """Get a style preset by ID.

        Args:
            user_id: Requesting user ID
            preset_id: Style preset ID
            allow_public: Whether to allow access to public presets

        Returns:
            StylePreset if found and accessible, None otherwise
        """
        conditions = [StylePreset.id == uuid.UUID(preset_id)]

        if allow_public:
            conditions.append(
                or_(
                    StylePreset.user_id == user_id,
                    StylePreset.is_public == True,
                )
            )
        else:
            conditions.append(StylePreset.user_id == user_id)

        stmt = select(StylePreset).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_style_presets(
        self,
        user_id: str,
        filters: Optional[StylePresetFilters] = None,
        include_public: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[StylePreset], int]:
        """Get paginated style presets.

        Args:
            user_id: Requesting user ID
            filters: Optional filters
            include_public: Whether to include public presets
            page: Page number (1-based)
            page_size: Items per page

        Returns:
            Tuple of (presets, total_count)
        """
        if include_public:
            ownership_condition = or_(
                StylePreset.user_id == user_id,
                StylePreset.is_public == True,
            )
        else:
            ownership_condition = StylePreset.user_id == user_id

        conditions = [ownership_condition]

        if filters:
            if filters.lighting:
                conditions.append(StylePreset.lighting == filters.lighting)
            if filters.mood:
                conditions.append(StylePreset.mood == filters.mood)
            if filters.is_public is not None:
                conditions.append(StylePreset.is_public == filters.is_public)
            if filters.tags:
                conditions.append(StylePreset.tags.contains(filters.tags))
            if filters.search_query:
                conditions.append(
                    StylePreset.name.ilike(f"%{filters.search_query}%")
                )

        # Count query
        count_stmt = select(func.count()).select_from(StylePreset).where(and_(*conditions))
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Items query with usage_count ordering for popular presets
        stmt = (
            select(StylePreset)
            .where(and_(*conditions))
            .order_by(StylePreset.usage_count.desc(), StylePreset.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        presets = list(result.scalars().all())

        return presets, total

    async def update_style_preset(
        self,
        user_id: str,
        preset_id: str,
        data: StylePresetUpdate,
    ) -> Optional[StylePreset]:
        """Update a style preset.

        Args:
            user_id: Owner user ID
            preset_id: Style preset ID
            data: Update data

        Returns:
            Updated StylePreset if found and owned, None otherwise
        """
        # Only owner can update
        preset = await self.get_style_preset(user_id, preset_id, allow_public=False)
        if not preset:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preset, field, value)

        await self.db.flush()
        await self.db.refresh(preset)

        logger.info(f"Updated style preset: {preset_id}")
        return preset

    async def delete_style_preset(
        self,
        user_id: str,
        preset_id: str,
    ) -> bool:
        """Delete a style preset.

        Args:
            user_id: Owner user ID
            preset_id: Style preset ID

        Returns:
            True if deleted, False if not found or not owned
        """
        stmt = delete(StylePreset).where(
            and_(
                StylePreset.id == uuid.UUID(preset_id),
                StylePreset.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)

        if result.rowcount > 0:
            logger.info(f"Deleted style preset: {preset_id}")
            return True
        return False

    async def increment_preset_usage(
        self,
        preset_id: str,
    ) -> None:
        """Increment usage count for a style preset.

        Args:
            preset_id: Style preset ID
        """
        stmt = (
            update(StylePreset)
            .where(StylePreset.id == uuid.UUID(preset_id))
            .values(usage_count=StylePreset.usage_count + 1)
        )
        await self.db.execute(stmt)

    # =========================================================================
    # Style Extraction from Reference
    # =========================================================================

    async def create_style_from_reference(
        self,
        user_id: str,
        reference_id: str,
        name: str,
        is_public: bool = False,
    ) -> Optional[StylePreset]:
        """Create a style preset from an analyzed reference.

        Extracts style data from the reference's analysis result.

        Args:
            user_id: Owner user ID
            reference_id: Reference item ID
            name: Name for the style preset
            is_public: Whether to make the preset public

        Returns:
            Created StylePreset, or None if reference not found/not analyzed
        """
        item = await self.get_reference_item(user_id, reference_id)
        if not item or item.analysis_status != "completed":
            return None

        # Extract style data from analysis result
        analysis = item.analysis_result or {}
        style_data = analysis.get("style", {})

        if isinstance(style_data, dict):
            style_dict = style_data
        else:
            # Pydantic model - convert to dict
            style_dict = style_data.model_dump() if hasattr(style_data, "model_dump") else {}

        preset_data = StylePresetCreate(
            name=name,
            description=f"Extracted from: {item.name}",
            tags=style_dict.get("style_tags", []),
            style_data=style_dict,
            color_palette=style_dict.get("color_palette", []),
            lighting=style_dict.get("lighting"),
            mood=style_dict.get("mood"),
            thumbnail_url=item.thumbnail_url,
            source_reference_id=reference_id,
            is_public=is_public,
        )

        preset = await self.create_style_preset(user_id, preset_data)

        # Link back to reference
        item.extracted_style_id = preset.id
        await self.db.flush()

        return preset


# =============================================================================
# Factory Function
# =============================================================================


def get_reference_library_service(db: AsyncSession) -> ReferenceLibraryService:
    """Factory function for ReferenceLibraryService.

    Args:
        db: Database session

    Returns:
        ReferenceLibraryService instance
    """
    return ReferenceLibraryService(db)
