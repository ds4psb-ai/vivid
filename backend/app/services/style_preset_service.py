"""Style Preset Service for Style Library CRUD.

Business logic for managing style presets (save, search, apply).
Uses SQLAlchemy 2.0 async patterns with PostgreSQL GIN indexes.

Based on: docs/research/02_REFERENCE_DECODER_RESEARCH.md
Model: backend/app/models_reference.py:StylePreset
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_reference import StylePreset
from app.schemas.style_preset_schemas import (
    StylePresetCreateRequest,
    StylePresetUpdateRequest,
    StylePresetSearchParams,
    StylePresetResponse,
    StylePresetListResponse,
    StylePresetApplyResponse,
    StylePresetDiscoverResponse,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Errors
# =============================================================================


class StylePresetError(Exception):
    """Base error for style preset operations."""
    pass


class StylePresetNotFoundError(StylePresetError):
    """Preset not found."""
    pass


class StylePresetAccessDeniedError(StylePresetError):
    """User does not have permission to access this preset."""
    pass


# =============================================================================
# Service Functions
# =============================================================================


async def create_preset(
    db: AsyncSession,
    user_id: str,
    request: StylePresetCreateRequest,
) -> StylePreset:
    """Create a new style preset.

    Args:
        db: Database session
        user_id: Owner user ID
        request: Create request with style data

    Returns:
        Created StylePreset model

    Raises:
        StylePresetError: If creation fails
    """
    try:
        # Extract denormalized fields from style_data if not provided
        style_data = request.style_data or {}
        lighting = request.lighting or style_data.get("lighting")
        mood = request.mood or style_data.get("mood")
        color_palette = request.color_palette or style_data.get("color_palette", [])

        preset = StylePreset(
            user_id=user_id,
            name=request.name,
            description=request.description,
            tags=request.tags,
            style_data=style_data,
            color_palette=color_palette,
            lighting=lighting,
            mood=mood,
            thumbnail_url=request.thumbnail_url,
            source_reference_id=request.source_reference_id,
            is_public=request.is_public,
            usage_count=0,
        )

        db.add(preset)
        await db.commit()
        await db.refresh(preset)

        logger.info(
            f"Created style preset: id={preset.id}, name={preset.name}, "
            f"user={user_id}, tags={preset.tags}"
        )
        return preset

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create style preset: {e}")
        raise StylePresetError(f"Failed to create style preset: {e}") from e


async def get_preset(
    db: AsyncSession,
    preset_id: UUID,
    user_id: Optional[str] = None,
    check_access: bool = True,
) -> StylePreset:
    """Get a single style preset by ID.

    Args:
        db: Database session
        preset_id: Preset UUID
        user_id: Current user ID (for access check)
        check_access: Whether to enforce access control

    Returns:
        StylePreset model

    Raises:
        StylePresetNotFoundError: If preset doesn't exist
        StylePresetAccessDeniedError: If user can't access
    """
    result = await db.execute(
        select(StylePreset).where(StylePreset.id == preset_id)
    )
    preset = result.scalar_one_or_none()

    if not preset:
        raise StylePresetNotFoundError(f"Style preset not found: {preset_id}")

    if check_access and user_id:
        # User can access if: owner OR preset is public
        if preset.user_id != user_id and not preset.is_public:
            raise StylePresetAccessDeniedError(
                f"Access denied to preset {preset_id}"
            )

    return preset


async def list_presets(
    db: AsyncSession,
    user_id: str,
    params: StylePresetSearchParams,
) -> Tuple[List[StylePreset], int]:
    """List style presets with search and filtering.

    Args:
        db: Database session
        user_id: Current user ID
        params: Search/filter parameters

    Returns:
        Tuple of (presets list, total count)
    """
    # Base query: user's own presets OR public presets
    conditions = []

    if params.include_public:
        conditions.append(
            or_(
                StylePreset.user_id == user_id,
                StylePreset.is_public == True,
            )
        )
    else:
        conditions.append(StylePreset.user_id == user_id)

    # Public visibility filter
    if params.is_public is not None:
        conditions.append(StylePreset.is_public == params.is_public)

    # Text search (trigram via GIN index)
    if params.q:
        # Use ilike for simple search (GIN trigram index will be used)
        conditions.append(
            StylePreset.name.ilike(f"%{params.q}%")
        )

    # Tag filter (GIN index on JSONB)
    if params.tags:
        # Match any of the provided tags
        tag_conditions = []
        for tag in params.tags:
            tag_conditions.append(
                StylePreset.tags.op("?")(tag.lower())
            )
        if tag_conditions:
            conditions.append(or_(*tag_conditions))

    # Lighting filter
    if params.lighting:
        conditions.append(StylePreset.lighting == params.lighting)

    # Mood filter
    if params.mood:
        conditions.append(StylePreset.mood == params.mood)

    # Build query
    query = select(StylePreset).where(and_(*conditions))

    # Count query
    count_query = select(func.count()).select_from(
        select(StylePreset.id).where(and_(*conditions)).subquery()
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Sorting
    sort_column = {
        "created_at": StylePreset.created_at,
        "name": StylePreset.name,
        "usage_count": StylePreset.usage_count,
        "updated_at": StylePreset.updated_at,
    }.get(params.sort_by, StylePreset.created_at)

    if params.sort_order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # Pagination
    query = query.offset(params.offset).limit(params.limit)

    result = await db.execute(query)
    presets = list(result.scalars().all())

    return presets, total


async def update_preset(
    db: AsyncSession,
    preset_id: UUID,
    user_id: str,
    request: StylePresetUpdateRequest,
) -> StylePreset:
    """Update an existing style preset.

    Only the owner can update their presets.

    Args:
        db: Database session
        preset_id: Preset UUID
        user_id: Current user ID
        request: Update request (partial)

    Returns:
        Updated StylePreset model

    Raises:
        StylePresetNotFoundError: If preset doesn't exist
        StylePresetAccessDeniedError: If user is not owner
    """
    preset = await get_preset(db, preset_id, check_access=False)

    # Only owner can update
    if preset.user_id != user_id:
        raise StylePresetAccessDeniedError(
            f"Only the owner can update preset {preset_id}"
        )

    # Apply partial update
    update_data = request.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(preset, field):
            setattr(preset, field, value)

    preset.updated_at = datetime.utcnow()

    try:
        await db.commit()
        await db.refresh(preset)
        logger.info(f"Updated style preset: id={preset_id}, fields={list(update_data.keys())}")
        return preset
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update style preset: {e}")
        raise StylePresetError(f"Failed to update style preset: {e}") from e


async def delete_preset(
    db: AsyncSession,
    preset_id: UUID,
    user_id: str,
    is_admin: bool = False,
) -> bool:
    """Delete a style preset.

    Only owner or admin can delete.

    Args:
        db: Database session
        preset_id: Preset UUID
        user_id: Current user ID
        is_admin: Whether user is admin

    Returns:
        True if deleted

    Raises:
        StylePresetNotFoundError: If preset doesn't exist
        StylePresetAccessDeniedError: If user can't delete
    """
    preset = await get_preset(db, preset_id, check_access=False)

    # Only owner or admin can delete
    if preset.user_id != user_id and not is_admin:
        raise StylePresetAccessDeniedError(
            f"Only the owner can delete preset {preset_id}"
        )

    try:
        await db.delete(preset)
        await db.commit()
        logger.info(f"Deleted style preset: id={preset_id}, user={user_id}")
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete style preset: {e}")
        raise StylePresetError(f"Failed to delete style preset: {e}") from e


async def increment_usage(
    db: AsyncSession,
    preset_id: UUID,
) -> int:
    """Increment usage count for a preset.

    Called when a preset is applied to a generation.

    Args:
        db: Database session
        preset_id: Preset UUID

    Returns:
        New usage count
    """
    preset = await get_preset(db, preset_id, check_access=False)

    preset.usage_count = (preset.usage_count or 0) + 1
    preset.updated_at = datetime.utcnow()

    try:
        await db.commit()
        await db.refresh(preset)
        return preset.usage_count
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to increment usage: {e}")
        raise StylePresetError(f"Failed to increment usage: {e}") from e


async def apply_preset(
    db: AsyncSession,
    preset_id: UUID,
    user_id: str,
) -> StylePresetApplyResponse:
    """Apply a style preset and return the style_prompt.

    Increments usage_count and returns data needed for generation.

    Args:
        db: Database session
        preset_id: Preset UUID
        user_id: Current user ID

    Returns:
        StylePresetApplyResponse with style_prompt
    """
    preset = await get_preset(db, preset_id, user_id, check_access=True)

    # Increment usage
    new_count = await increment_usage(db, preset_id)

    style_data = preset.style_data or {}

    # Build evidence_refs in Vivid format (List[str])
    evidence_refs = [f"db:style_presets:{preset.id}"]

    return StylePresetApplyResponse(
        id=preset.id,
        name=preset.name,
        style_prompt=style_data.get("style_prompt", ""),
        style_tags=style_data.get("style_tags", []),
        color_palette=preset.color_palette or [],
        lighting=preset.lighting,
        mood=preset.mood,
        usage_count=new_count,
        evidence_refs=evidence_refs,
    )


async def discover_public(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "usage_count",
) -> StylePresetDiscoverResponse:
    """Discover popular public style presets.

    Returns public presets sorted by popularity with tag statistics.

    Args:
        db: Database session
        limit: Max results
        offset: Pagination offset
        sort_by: Sort field (usage_count, created_at)

    Returns:
        StylePresetDiscoverResponse with items and categories
    """
    # Query public presets
    conditions = [StylePreset.is_public == True]

    query = select(StylePreset).where(and_(*conditions))

    # Count total
    count_query = select(func.count()).select_from(
        select(StylePreset.id).where(and_(*conditions)).subquery()
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Sorting
    if sort_by == "usage_count":
        query = query.order_by(desc(StylePreset.usage_count))
    else:
        query = query.order_by(desc(StylePreset.created_at))

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    presets = list(result.scalars().all())

    # Build tag statistics
    tag_counts: Dict[str, int] = {}
    for preset in presets:
        for tag in (preset.tags or []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    items = [
        StylePresetResponse.from_model(p, current_user_id=None)
        for p in presets
    ]

    return StylePresetDiscoverResponse(
        items=items,
        total=total,
        categories=tag_counts,
    )


async def get_preset_with_response(
    db: AsyncSession,
    preset_id: UUID,
    user_id: Optional[str] = None,
) -> StylePresetResponse:
    """Get preset and return as response model.

    Args:
        db: Database session
        preset_id: Preset UUID
        user_id: Current user ID for is_owner field

    Returns:
        StylePresetResponse
    """
    preset = await get_preset(db, preset_id, user_id, check_access=True)
    return StylePresetResponse.from_model(preset, current_user_id=user_id)
