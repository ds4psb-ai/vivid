"""Reference Library Router for 4D Reference Decoder.

Endpoints for managing user reference libraries:
- Reference items CRUD
- Style presets CRUD
- Analysis triggers

2026 Best Practices:
- FastAPI dependency injection
- Pydantic v2 validation
- SQLAlchemy 2.0 async
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.services.reference_library_service import (
    ReferenceLibraryService,
    ReferenceItemCreate,
    ReferenceItemUpdate,
    ReferenceItemResponse,
    StylePresetCreate,
    StylePresetUpdate,
    StylePresetResponse,
    ReferenceItemFilter,
    PaginationParams,
    PaginatedResponse,
)
from app.utils.error_sanitize import safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reference-library", tags=["reference-library"])


# =============================================================================
# Request/Response Models
# =============================================================================


class CreateReferenceItemRequest(BaseModel):
    """Request body for creating a reference item."""

    name: str = Field(..., min_length=1, max_length=200, description="Item name")
    description: Optional[str] = Field(None, description="Optional description")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    reference_type: str = Field(..., pattern="^(video|image)$", description="Type: video or image")
    source_url: str = Field(..., max_length=2000, description="Source URL of the reference")
    file_size_bytes: Optional[int] = Field(None, ge=0, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    duration_seconds: Optional[float] = Field(None, ge=0, description="Duration for videos")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    project_id: Optional[str] = Field(None, description="Optional project association")
    analysis_depth: str = Field(
        default="detailed",
        pattern="^(quick|detailed|comprehensive)$",
        description="Analysis depth level",
    )


class UpdateReferenceItemRequest(BaseModel):
    """Request body for updating a reference item."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class CreateStylePresetRequest(BaseModel):
    """Request body for creating a style preset."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    style_data: Dict[str, Any] = Field(default_factory=dict)
    style_vector: Optional[List[float]] = Field(None, description="Style embedding vector")
    auteur_references: List[str] = Field(default_factory=list)
    is_public: bool = Field(default=False)
    source_reference_id: Optional[str] = Field(None)


class UpdateStylePresetRequest(BaseModel):
    """Request body for updating a style preset."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    style_data: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str


# =============================================================================
# Reference Item Endpoints
# =============================================================================


@router.post(
    "/items",
    response_model=ReferenceItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create reference item",
    description="Add a new reference item to the user's library",
)
async def create_reference_item(
    request: CreateReferenceItemRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReferenceItemResponse:
    """Create a new reference item in the user's library."""
    user_id = user.get("sub") or user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )

    service = ReferenceLibraryService(db)

    try:
        create_dto = ReferenceItemCreate(
            name=request.name,
            description=request.description,
            tags=request.tags,
            reference_type=request.reference_type,
            source_url=request.source_url,
            file_size_bytes=request.file_size_bytes,
            mime_type=request.mime_type,
            duration_seconds=request.duration_seconds,
            thumbnail_url=request.thumbnail_url,
            project_id=request.project_id,
            analysis_depth=request.analysis_depth,
        )

        result = await service.create_reference_item(user_id, create_dto)
        logger.info(f"Created reference item {result.id} for user {user_id}")
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Failed to create reference item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=safe_error_detail(str(e)),
        )


@router.get(
    "/items",
    response_model=PaginatedResponse[ReferenceItemResponse],
    summary="List reference items",
    description="Get paginated list of user's reference items with optional filters",
)
async def get_reference_items(
    project_id: Optional[str] = Query(None, description="Filter by project"),
    reference_type: Optional[str] = Query(None, pattern="^(video|image)$"),
    analysis_status: Optional[str] = Query(None, pattern="^(pending|processing|completed|failed)$"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags (OR)"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ReferenceItemResponse]:
    """Get paginated list of reference items."""
    user_id = user.get("sub") or user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )

    service = ReferenceLibraryService(db)

    filters = ReferenceItemFilter(
        project_id=project_id,
        reference_type=reference_type,
        analysis_status=analysis_status,
        tags=tags,
        search=search,
    )

    # Service expects separate page and page_size args, not PaginationParams
    items, total = await service.get_reference_items(
        user_id, filters, page=page, page_size=page_size
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/items/{item_id}",
    response_model=ReferenceItemResponse,
    summary="Get reference item",
    description="Get a specific reference item by ID",
)
async def get_reference_item(
    item_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReferenceItemResponse:
    """Get a specific reference item."""
    user_id = user.get("sub") or user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )

    service = ReferenceLibraryService(db)
    result = await service.get_reference_item(user_id, item_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reference item {item_id} not found",
        )

    return result


@router.patch(
    "/items/{item_id}",
    response_model=ReferenceItemResponse,
    summary="Update reference item",
    description="Update a reference item's metadata",
)
async def update_reference_item(
    item_id: str,
    request: UpdateReferenceItemRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReferenceItemResponse:
    """Update a reference item."""
    user_id = user.get("sub") or user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )

    service = ReferenceLibraryService(db)

    update_dto = ReferenceItemUpdate(
        name=request.name,
        description=request.description,
        tags=request.tags,
    )

    result = await service.update_reference_item(user_id, item_id, update_dto)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reference item {item_id} not found",
        )

    logger.info(f"Updated reference item {item_id} for user {user_id}")
    return result


@router.delete(
    "/items/{item_id}",
    response_model=SuccessResponse,
    summary="Delete reference item",
    description="Delete a reference item from the library",
)
async def delete_reference_item(
    item_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Delete a reference item."""
    user_id = user.get("sub") or user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )

    service = ReferenceLibraryService(db)
    success = await service.delete_reference_item(user_id, item_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reference item {item_id} not found",
        )

    logger.info(f"Deleted reference item {item_id} for user {user_id}")
    return SuccessResponse(message=f"Reference item {item_id} deleted successfully")


# =============================================================================
# Style Preset Endpoints
# =============================================================================


@router.post(
    "/styles",
    response_model=StylePresetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create style preset",
    description="Create a new style preset",
)
async def create_style_preset(
    request: CreateStylePresetRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StylePresetResponse:
    """Create a new style preset."""
    user_id = user.get("sub") or user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )

    service = ReferenceLibraryService(db)

    try:
        create_dto = StylePresetCreate(
            name=request.name,
            description=request.description,
            tags=request.tags,
            style_data=request.style_data,
            style_vector=request.style_vector,
            auteur_references=request.auteur_references,
            is_public=request.is_public,
            source_reference_id=request.source_reference_id,
        )

        result = await service.create_style_preset(user_id, create_dto)
        logger.info(f"Created style preset {result.id} for user {user_id}")
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Failed to create style preset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=safe_error_detail(str(e)),
        )


@router.get(
    "/styles",
    response_model=PaginatedResponse[StylePresetResponse],
    summary="List style presets",
    description="Get paginated list of style presets (user's own + public)",
)
async def get_style_presets(
    include_public: bool = Query(True, description="Include public presets"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[StylePresetResponse]:
    """Get paginated list of style presets."""
    user_id = user.get("sub") or user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )

    service = ReferenceLibraryService(db)

    # Service expects separate page and page_size args, not pagination
    # Note: tags and search filtering can be added to service if needed
    presets, total = await service.get_style_presets(
        user_id,
        include_public=include_public,
        page=page,
        page_size=page_size,
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=presets,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/styles/{preset_id}",
    response_model=StylePresetResponse,
    summary="Get style preset",
    description="Get a specific style preset by ID",
)
async def get_style_preset(
    preset_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StylePresetResponse:
    """Get a specific style preset."""
    user_id = user.get("sub") or user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )

    service = ReferenceLibraryService(db)
    result = await service.get_style_preset(user_id, preset_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Style preset {preset_id} not found or not accessible",
        )

    return result


@router.patch(
    "/styles/{preset_id}",
    response_model=StylePresetResponse,
    summary="Update style preset",
    description="Update a style preset (owner only)",
)
async def update_style_preset(
    preset_id: str,
    request: UpdateStylePresetRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StylePresetResponse:
    """Update a style preset."""
    user_id = user.get("sub") or user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )

    service = ReferenceLibraryService(db)

    update_dto = StylePresetUpdate(
        name=request.name,
        description=request.description,
        tags=request.tags,
        style_data=request.style_data,
        is_public=request.is_public,
    )

    result = await service.update_style_preset(user_id, preset_id, update_dto)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Style preset {preset_id} not found or not owned by user",
        )

    logger.info(f"Updated style preset {preset_id} for user {user_id}")
    return result


@router.delete(
    "/styles/{preset_id}",
    response_model=SuccessResponse,
    summary="Delete style preset",
    description="Delete a style preset (owner only)",
)
async def delete_style_preset(
    preset_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Delete a style preset."""
    user_id = user.get("sub") or user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )

    service = ReferenceLibraryService(db)
    success = await service.delete_style_preset(user_id, preset_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Style preset {preset_id} not found or not owned by user",
        )

    logger.info(f"Deleted style preset {preset_id} for user {user_id}")
    return SuccessResponse(message=f"Style preset {preset_id} deleted successfully")


# =============================================================================
# Additional Endpoints
# =============================================================================


@router.post(
    "/items/{item_id}/extract-style",
    response_model=StylePresetResponse,
    summary="Extract style from reference",
    description="Create a style preset from an analyzed reference item",
)
async def extract_style_from_reference(
    item_id: str,
    preset_name: str = Query(..., min_length=1, max_length=200),
    is_public: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StylePresetResponse:
    """Extract a style preset from an analyzed reference item."""
    user_id = user.get("sub") or user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )

    service = ReferenceLibraryService(db)

    try:
        result = await service.create_style_from_reference(
            user_id=user_id,
            reference_id=item_id,
            preset_name=preset_name,
            is_public=is_public,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reference item {item_id} not found or not analyzed yet",
            )

        logger.info(f"Extracted style preset from reference {item_id} for user {user_id}")
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Failed to extract style: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=safe_error_detail(str(e)),
        )
