"""Style Presets API Router.

CRUD API for Style Library management:
- Create/save style presets from extracted styles
- List/search presets with filtering (GIN indexes)
- Apply presets to generations (3D Visual Realizer)
- Discover popular public presets

Endpoints:
- POST /style-presets: Create new preset
- GET /style-presets: List/search presets
- GET /style-presets/discover: Browse public presets
- GET /style-presets/{id}: Get single preset
- PATCH /style-presets/{id}: Update preset
- DELETE /style-presets/{id}: Delete preset
- POST /style-presets/{id}/apply: Apply preset (increment usage)
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.style_preset_schemas import (
    StylePresetCreateRequest,
    StylePresetUpdateRequest,
    StylePresetSearchParams,
    StylePresetResponse,
    StylePresetListResponse,
    StylePresetApplyResponse,
    StylePresetDiscoverResponse,
)
from app.services import style_preset_service
from app.services.style_preset_service import (
    StylePresetNotFoundError,
    StylePresetAccessDeniedError,
    StylePresetError,
)
from app.utils.error_sanitize import safe_error_detail

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/style-presets", tags=["Style Presets"])


# =============================================================================
# Create
# =============================================================================


@router.post("", response_model=StylePresetResponse, status_code=201)
async def create_style_preset(
    request: StylePresetCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new style preset.

    Save a style extraction result for future reuse.
    Typically called after `/4d/extract-style` returns data.

    Request body:
    - name: Display name (required)
    - description: Optional description
    - tags: Searchable tags (anime, cinematic, etc.)
    - style_data: Full StyleExtractionResult (required)
    - is_public: Share publicly (default: false)
    """
    user_id = current_user["id"]

    try:
        preset = await style_preset_service.create_preset(db, user_id, request)
        return StylePresetResponse.from_model(preset, current_user_id=user_id)
    except StylePresetError as e:
        logger.error(f"Failed to create preset: {e}")
        raise HTTPException(status_code=400, detail=safe_error_detail(str(e)))
    except Exception as e:
        logger.error(f"Unexpected error creating preset: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# List / Search
# =============================================================================


@router.get("", response_model=StylePresetListResponse)
async def list_style_presets(
    q: Optional[str] = Query(None, max_length=100, description="Search query"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    lighting: Optional[str] = Query(None, max_length=50),
    mood: Optional[str] = Query(None, max_length=50),
    is_public: Optional[bool] = Query(None, description="Filter by public visibility"),
    include_public: bool = Query(True, description="Include public presets"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List style presets with search and filtering.

    Returns user's own presets plus (optionally) public presets.

    Query parameters:
    - q: Text search in name (uses GIN trigram index)
    - tags: Comma-separated tag filter (any match)
    - lighting: Filter by lighting type
    - mood: Filter by mood
    - is_public: Filter by visibility
    - include_public: Include other users' public presets
    - sort_by: created_at, name, usage_count
    - sort_order: asc, desc
    """
    user_id = current_user["id"]

    # Parse comma-separated tags
    tag_list = None
    if tags:
        tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]

    params = StylePresetSearchParams(
        q=q,
        tags=tag_list,
        lighting=lighting,
        mood=mood,
        is_public=is_public,
        include_public=include_public,
        sort_by=sort_by,
        sort_order=sort_order,
        offset=offset,
        limit=limit,
    )

    try:
        presets, total = await style_preset_service.list_presets(db, user_id, params)

        items = [
            StylePresetResponse.from_model(p, current_user_id=user_id)
            for p in presets
        ]

        return StylePresetListResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
            has_more=(offset + len(items)) < total,
        )
    except Exception as e:
        logger.error(f"Error listing presets: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# Discover Public
# =============================================================================


@router.get("/discover", response_model=StylePresetDiscoverResponse)
async def discover_public_presets(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("usage_count", description="Sort: usage_count or created_at"),
    db: AsyncSession = Depends(get_db),
):
    """Discover popular public style presets.

    Browse community-shared styles sorted by popularity.
    No authentication required.

    Returns presets with tag statistics for filtering.
    """
    try:
        return await style_preset_service.discover_public(
            db, limit=limit, offset=offset, sort_by=sort_by
        )
    except Exception as e:
        logger.error(f"Error discovering presets: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# Get Single
# =============================================================================


@router.get("/{preset_id}", response_model=StylePresetResponse)
async def get_style_preset(
    preset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single style preset by ID.

    Users can view their own presets and public presets.
    """
    user_id = current_user["id"]

    try:
        return await style_preset_service.get_preset_with_response(
            db, preset_id, user_id
        )
    except StylePresetNotFoundError:
        raise HTTPException(status_code=404, detail="Style preset not found")
    except StylePresetAccessDeniedError:
        raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        logger.error(f"Error getting preset: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# Update
# =============================================================================


@router.patch("/{preset_id}", response_model=StylePresetResponse)
async def update_style_preset(
    preset_id: UUID,
    request: StylePresetUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update an existing style preset.

    Only the owner can update their presets.
    Supports partial updates (only provided fields are changed).
    """
    user_id = current_user["id"]

    try:
        preset = await style_preset_service.update_preset(
            db, preset_id, user_id, request
        )
        return StylePresetResponse.from_model(preset, current_user_id=user_id)
    except StylePresetNotFoundError:
        raise HTTPException(status_code=404, detail="Style preset not found")
    except StylePresetAccessDeniedError:
        raise HTTPException(status_code=403, detail="Only the owner can update")
    except StylePresetError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(str(e)))
    except Exception as e:
        logger.error(f"Error updating preset: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# Delete
# =============================================================================


@router.delete("/{preset_id}", status_code=204)
async def delete_style_preset(
    preset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a style preset.

    Only the owner or admin can delete presets.
    """
    user_id = current_user["id"]
    is_admin = current_user.get("is_admin", False)

    try:
        await style_preset_service.delete_preset(db, preset_id, user_id, is_admin)
        return None
    except StylePresetNotFoundError:
        raise HTTPException(status_code=404, detail="Style preset not found")
    except StylePresetAccessDeniedError:
        raise HTTPException(status_code=403, detail="Only the owner can delete")
    except StylePresetError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(str(e)))
    except Exception as e:
        logger.error(f"Error deleting preset: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# Apply
# =============================================================================


@router.post("/{preset_id}/apply", response_model=StylePresetApplyResponse)
async def apply_style_preset(
    preset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Apply a style preset for generation.

    Returns the style_prompt and metadata for use in 3D Visual Realizer.
    Increments the usage_count.

    Response includes:
    - style_prompt: Reusable prompt for AI generation
    - style_tags: Style tags for reference
    - color_palette: Colors for reference
    - evidence_refs: Vivid evidence references (db:style_presets:{uuid})
    """
    user_id = current_user["id"]

    try:
        return await style_preset_service.apply_preset(db, preset_id, user_id)
    except StylePresetNotFoundError:
        raise HTTPException(status_code=404, detail="Style preset not found")
    except StylePresetAccessDeniedError:
        raise HTTPException(status_code=403, detail="Access denied")
    except StylePresetError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(str(e)))
    except Exception as e:
        logger.error(f"Error applying preset: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
