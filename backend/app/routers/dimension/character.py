"""Character Consistency Dimension Endpoints.

API endpoints for StoryMem-based character consistency system.

Features:
- Character CRUD (create, read, update, delete)
- Reference image management
- Memory bank management
- Platform synchronization
- Similarity search

Security:
- User authentication required
- Ownership validation
- XSS sanitization for text fields

References:
- StoryMem Paper: arXiv:2512.19539
- DIMENSION_APP_MACRO_PLANNING_2026.md Part 11
"""
from __future__ import annotations

import html
import logging
import re
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from ._base import (
    get_db,
    get_current_user,
    get_byok_key,
    DimensionResponse,
    DimensionErrorResponse,
    get_sse_headers,
    sse_progress,
    sse_complete,
    sse_error,
)
from app.schemas.character_schemas import (
    CharacterCreateRequest,
    CharacterResponse,
    CharacterSummaryResponse,
    CharacterSimilarity,
    CharacterUpdateRequest,
    CharacterListResponse,
    PlatformSyncRequest,
    PlatformSyncResponse,
    MemoryBankUpdateRequest,
    MemoryBankResponse,
    PlatformType,
)
from app.services.character_service import (
    create_character,
    get_character,
    update_character,
    delete_character,
    list_characters,
    add_reference_images,
    update_memory_bank,
    sync_to_platform,
    find_similar_characters,
)

router = APIRouter()
character_logger = logging.getLogger(__name__)


# ============================================================================
# Sanitization Helpers
# ============================================================================

def _sanitize_text(value: str, default: str = "") -> str:
    """Sanitize text field to prevent XSS."""
    if not value:
        return default
    value = value.strip()
    if not value:
        return default
    value = re.sub(r"<[^>]+>", "", value)
    value = html.escape(value)
    value = re.sub(r"(?i)javascript\s*:", "", value)
    value = re.sub(r"(?i)on\w+\s*=", "", value)
    return value or default


# ============================================================================
# Character CRUD Endpoints
# ============================================================================

@router.post(
    "/character/create",
    response_model=CharacterResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        401: {"model": DimensionErrorResponse},
        500: {"model": DimensionErrorResponse},
    },
    summary="Create Character",
    description="Create a new character with optional reference image.",
    tags=["Character Consistency"],
)
async def create_character_endpoint(
    request: CharacterCreateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    """Create a new character for consistency tracking."""
    user_id = user.get("id", "unknown")
    character_logger.info(
        f"[CHARACTER_CREATE] user={user_id} name={request.name} "
        f"tags={request.tags} project={request.project_id}"
    )

    # Sanitize text fields
    request.name = _sanitize_text(request.name)
    if request.description:
        request.description = _sanitize_text(request.description)

    try:
        character = await create_character(db, user_id, request)
        return CharacterResponse.model_validate(character)
    except Exception as e:
        character_logger.error(f"[CHARACTER_CREATE] Failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/character/{character_id}",
    response_model=CharacterResponse,
    responses={
        404: {"model": DimensionErrorResponse},
    },
    summary="Get Character",
    description="Get character details by ID.",
    tags=["Character Consistency"],
)
async def get_character_endpoint(
    character_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    """Get character details."""
    user_id = user.get("id", "unknown")
    character_logger.info(f"[CHARACTER_GET] user={user_id} character={character_id}")

    character = await get_character(db, character_id, user_id)
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )

    return CharacterResponse.model_validate(character)


@router.patch(
    "/character/{character_id}",
    response_model=CharacterResponse,
    responses={
        404: {"model": DimensionErrorResponse},
    },
    summary="Update Character",
    description="Update character metadata.",
    tags=["Character Consistency"],
)
async def update_character_endpoint(
    character_id: UUID,
    request: CharacterUpdateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    """Update character metadata."""
    user_id = user.get("id", "unknown")
    character_logger.info(f"[CHARACTER_UPDATE] user={user_id} character={character_id}")

    # Sanitize text fields
    if request.name:
        request.name = _sanitize_text(request.name)
    if request.description:
        request.description = _sanitize_text(request.description)

    character = await update_character(db, character_id, user_id, request)
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )

    return CharacterResponse.model_validate(character)


@router.delete(
    "/character/{character_id}",
    responses={
        404: {"model": DimensionErrorResponse},
    },
    summary="Delete Character",
    description="Delete character and associated data.",
    tags=["Character Consistency"],
)
async def delete_character_endpoint(
    character_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete character."""
    user_id = user.get("id", "unknown")
    character_logger.info(f"[CHARACTER_DELETE] user={user_id} character={character_id}")

    success = await delete_character(db, character_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )

    return {"success": True, "message": "Character deleted"}


@router.get(
    "/character",
    response_model=CharacterListResponse,
    summary="List Characters",
    description="List characters with optional filters.",
    tags=["Character Consistency"],
)
async def list_characters_endpoint(
    project_id: Optional[UUID] = None,
    tags: Optional[str] = None,  # Comma-separated tags
    limit: int = 20,
    offset: int = 0,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CharacterListResponse:
    """List user's characters."""
    user_id = user.get("id", "unknown")
    character_logger.info(
        f"[CHARACTER_LIST] user={user_id} project={project_id} "
        f"tags={tags} limit={limit} offset={offset}"
    )

    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    characters, total = await list_characters(
        db, user_id, project_id, tag_list, limit, offset
    )

    items = [
        CharacterSummaryResponse(
            id=c.id,
            name=c.name,
            primary_image_url=c.primary_image_url,
            tags=c.tags or [],
            keyframe_count=c.keyframe_count,
            platforms_synced=c.platforms_synced,
        )
        for c in characters
    ]

    return CharacterListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


# ============================================================================
# Reference Image Management
# ============================================================================

@router.post(
    "/character/{character_id}/add-reference",
    response_model=CharacterResponse,
    responses={
        404: {"model": DimensionErrorResponse},
    },
    summary="Add Reference Images",
    description="Add reference images to existing character.",
    tags=["Character Consistency"],
)
async def add_reference_endpoint(
    character_id: UUID,
    image_urls: Optional[List[str]] = None,
    images_base64: Optional[List[str]] = None,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    """Add reference images to character."""
    user_id = user.get("id", "unknown")
    character_logger.info(
        f"[CHARACTER_ADD_REF] user={user_id} character={character_id} "
        f"urls={len(image_urls or [])} base64={len(images_base64 or [])}"
    )

    character = await add_reference_images(
        db, character_id, user_id, image_urls, images_base64
    )
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )

    return CharacterResponse.model_validate(character)


@router.post(
    "/character/{character_id}/upload-reference",
    response_model=CharacterResponse,
    responses={
        404: {"model": DimensionErrorResponse},
    },
    summary="Upload Reference Image",
    description="Upload reference image file to character.",
    tags=["Character Consistency"],
)
async def upload_reference_endpoint(
    character_id: UUID,
    files: List[UploadFile] = File(...),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    """Upload reference images via file upload."""
    user_id = user.get("id", "unknown")
    character_logger.info(
        f"[CHARACTER_UPLOAD_REF] user={user_id} character={character_id} "
        f"files={len(files)}"
    )

    # Read file contents as base64
    images_base64 = []
    for file in files:
        content = await file.read()
        import base64
        b64 = base64.b64encode(content).decode("utf-8")
        images_base64.append(b64)

    character = await add_reference_images(
        db, character_id, user_id, images_base64=images_base64
    )
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )

    return CharacterResponse.model_validate(character)


# ============================================================================
# Memory Bank Management
# ============================================================================

@router.post(
    "/character/{character_id}/memory-bank/update",
    response_model=MemoryBankResponse,
    responses={
        404: {"model": DimensionErrorResponse},
    },
    summary="Update Memory Bank",
    description="Update memory bank from generated video (StoryMem algorithm).",
    tags=["Character Consistency"],
)
async def update_memory_bank_endpoint(
    character_id: UUID,
    request: MemoryBankUpdateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MemoryBankResponse:
    """Update character memory bank from generated video."""
    user_id = user.get("id", "unknown")
    character_logger.info(
        f"[MEMORY_BANK_UPDATE] user={user_id} character={character_id} "
        f"video={request.video_url[:50]}... max_kf={request.max_keyframes}"
    )

    result = await update_memory_bank(
        db,
        character_id,
        user_id,
        request.video_url,
        request.max_keyframes,
        request.long_term_count,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )

    return result


@router.post(
    "/character/{character_id}/memory-bank/update/stream",
    responses={
        404: {"model": DimensionErrorResponse},
    },
    summary="Update Memory Bank (SSE Stream)",
    description="Update memory bank with progress streaming.",
    tags=["Character Consistency"],
)
async def update_memory_bank_stream_endpoint(
    character_id: UUID,
    request: MemoryBankUpdateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Update memory bank with SSE progress streaming."""
    user_id = user.get("id", "unknown")
    character_logger.info(
        f"[MEMORY_BANK_UPDATE_STREAM] user={user_id} character={character_id}"
    )

    async def stream_update():
        yield sse_progress(10, "비디오 프레임 추출 중...", "extracting")

        try:
            result = await update_memory_bank(
                db,
                character_id,
                user_id,
                request.video_url,
                request.max_keyframes,
                request.long_term_count,
            )

            if not result:
                yield sse_error("Character not found", code="NOT_FOUND")
                return

            yield sse_progress(80, "메모리 뱅크 업데이트 중...", "updating")
            yield sse_complete(
                data=result.model_dump(),
                metrics={"keyframes_extracted": result.keyframes_extracted},
            )

        except Exception as e:
            yield sse_error(str(e), code="UPDATE_FAILED")

    return StreamingResponse(
        stream_update(),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


# ============================================================================
# Platform Synchronization
# ============================================================================

@router.post(
    "/character/{character_id}/sync-platform",
    response_model=PlatformSyncResponse,
    responses={
        404: {"model": DimensionErrorResponse},
    },
    summary="Sync to Platform",
    description="Sync character to video generation platform (Veo, Kling, Runway).",
    tags=["Character Consistency"],
)
async def sync_platform_endpoint(
    character_id: UUID,
    request: PlatformSyncRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlatformSyncResponse:
    """Sync character to video generation platform."""
    user_id = user.get("id", "unknown")
    character_logger.info(
        f"[PLATFORM_SYNC] user={user_id} character={character_id} "
        f"platform={request.platform.value}"
    )

    result = await sync_to_platform(
        db, character_id, user_id, request.platform, request.style_strength
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )

    return result


@router.get(
    "/character/{character_id}/platform-status",
    summary="Get Platform Status",
    description="Get synchronization status for all platforms.",
    tags=["Character Consistency"],
)
async def get_platform_status_endpoint(
    character_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get platform sync status for character."""
    user_id = user.get("id", "unknown")

    character = await get_character(db, character_id, user_id)
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )

    return {
        "character_id": str(character_id),
        "platform_refs": character.platform_refs or {},
        "platforms_synced": character.platforms_synced,
    }


# ============================================================================
# Similarity Search
# ============================================================================

@router.get(
    "/character/{character_id}/similar",
    response_model=List[CharacterSimilarity],
    responses={
        404: {"model": DimensionErrorResponse},
    },
    summary="Find Similar Characters",
    description="Find similar characters using embedding similarity.",
    tags=["Character Consistency"],
)
async def find_similar_endpoint(
    character_id: UUID,
    limit: int = 5,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[CharacterSimilarity]:
    """Find similar characters."""
    user_id = user.get("id", "unknown")
    character_logger.info(
        f"[CHARACTER_SIMILAR] user={user_id} character={character_id} limit={limit}"
    )

    return await find_similar_characters(db, character_id, user_id, limit)


# ============================================================================
# Bulk Operations
# ============================================================================

@router.post(
    "/character/bulk-sync",
    summary="Bulk Platform Sync",
    description="Sync multiple characters to a platform.",
    tags=["Character Consistency"],
)
async def bulk_sync_endpoint(
    character_ids: List[UUID],
    platform: PlatformType,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Bulk sync characters to platform."""
    user_id = user.get("id", "unknown")
    character_logger.info(
        f"[BULK_SYNC] user={user_id} characters={len(character_ids)} "
        f"platform={platform.value}"
    )

    results = []
    for char_id in character_ids:
        result = await sync_to_platform(db, char_id, user_id, platform)
        results.append({
            "character_id": str(char_id),
            "status": result.status if result else "not_found",
            "platform_ref_id": result.platform_ref_id if result else None,
        })

    success_count = sum(1 for r in results if r["status"] == "success")
    return {
        "total": len(character_ids),
        "success": success_count,
        "failed": len(character_ids) - success_count,
        "results": results,
    }
