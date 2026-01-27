"""Constellation API Router.

REST API for Constellation (별자리) - Multi-scene projects:
- List/filter constellations
- Get constellation details
- Create/update/delete constellations
- Manage star points (scenes)
"""
from typing import Optional, List, Any, Literal
from uuid import UUID
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator, ConfigDict
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.database import get_db
from app.utils.error_sanitize import safe_error_detail
from app.models_constellation import Constellation
from app.models_singularity import BlackholeTemplate
from app.dependencies import get_optional_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/constellation", tags=["constellation"])

# Valid status values for stars
VALID_STAR_STATUSES = {"pending", "generating", "done", "error"}


# =============================================================================
# STATUS ENDPOINT
# =============================================================================

@router.get("/status")
async def get_constellation_status(db: AsyncSession = Depends(get_db)):
    """Get constellation service status.
    
    Returns system health and basic statistics.
    """
    try:
        # Count total constellations
        count_result = await db.execute(select(func.count()).select_from(Constellation))
        total_count = count_result.scalar() or 0
        
        # Count public constellations
        public_result = await db.execute(
            select(func.count()).select_from(Constellation).where(Constellation.is_public == True)
        )
        public_count = public_result.scalar() or 0
        
        return {
            "status": "healthy",
            "service": "constellation",
            "statistics": {
                "total_constellations": total_count,
                "public_constellations": public_count,
            },
        }
    except Exception as e:
        logger.error(f"Constellation status check failed: {e}")
        return {
            "status": "degraded",
            "service": "constellation",
            "error": str(e),
        }


# =============================================================================
# SCHEMAS
# =============================================================================

class StarPointSchema(BaseModel):
    """A star (scene) in the constellation."""
    scene_number: int
    singularity_id: str
    singularity_name: str
    status: str = "pending"  # pending, generating, done, error
    thumbnail_url: Optional[str] = None
    overrides: dict = {}
    output_ref: Optional[str] = None
    created_at: Optional[str] = None


class SharedContextSchema(BaseModel):
    """Shared context across scenes."""
    characters: dict = {}
    visual_style: Optional[str] = None
    audio_style: Optional[str] = None
    custom_params: dict = {}


class ConstellationListItem(BaseModel):
    """Constellation summary for list view."""
    id: UUID
    name: str
    description: str
    thumbnail_url: Optional[str] = None
    preset: str
    target_scene_count: int
    scene_count: int
    completed_count: int
    progress_percent: float
    creator_id: str
    creator_name: str
    is_public: bool
    use_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConstellationDetail(ConstellationListItem):
    """Full constellation details."""
    shared_context: dict = {}
    star_points: List[StarPointSchema] = []


class ConstellationCreate(BaseModel):
    """Create a new constellation."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=2000)
    preset: str = Field("short_drama", pattern="^(short_drama|medium|feature_film)$")
    target_scene_count: int = Field(5, ge=1, le=100)
    shared_context: dict = {}
    # First star (optional - can add later)
    first_singularity_id: Optional[str] = None

    @field_validator("first_singularity_id")
    @classmethod
    def validate_uuid(cls, v: Optional[str]) -> Optional[str]:
        """Validate first_singularity_id is a valid UUID if provided."""
        if v is None:
            return v
        try:
            UUID(v)
        except (ValueError, AttributeError):
            raise ValueError("Invalid UUID format for first_singularity_id")
        return v


class ConstellationUpdate(BaseModel):
    """Update constellation metadata."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    preset: Optional[str] = Field(None, pattern="^(short_drama|medium|feature_film)$")
    target_scene_count: Optional[int] = Field(None, ge=1, le=100)
    shared_context: Optional[dict] = None
    is_public: Optional[bool] = None


class StarAdd(BaseModel):
    """Add a star (scene) to constellation."""
    singularity_id: str
    overrides: dict = {}
    scene_number: Optional[int] = Field(None, ge=1, le=1000)  # Auto-increment if not specified

    @field_validator("singularity_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """Validate singularity_id is a valid UUID."""
        try:
            UUID(v)
        except (ValueError, AttributeError):
            raise ValueError("Invalid UUID format for singularity_id")
        return v


class StarUpdate(BaseModel):
    """Update a star's properties."""
    overrides: Optional[dict] = None
    status: Optional[Literal["pending", "generating", "done", "error"]] = None
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    output_ref: Optional[str] = Field(None, max_length=200)


class ConstellationListResponse(BaseModel):
    """Paginated constellation list."""
    items: List[ConstellationListItem]
    total: int
    page: int
    page_size: int


# =============================================================================
# HELPERS
# =============================================================================

def _build_detail_response(c: Constellation) -> ConstellationDetail:
    """Build ConstellationDetail response from model instance."""
    return ConstellationDetail(
        id=c.id,
        name=c.name,
        description=c.description,
        thumbnail_url=c.thumbnail_url,
        preset=c.preset,
        target_scene_count=c.target_scene_count,
        scene_count=c.scene_count,
        completed_count=c.completed_count,
        progress_percent=c.progress_percent,
        creator_id=c.creator_id,
        creator_name=c.creator_name,
        is_public=c.is_public,
        use_count=c.use_count,
        created_at=c.created_at,
        updated_at=c.updated_at,
        shared_context=c.shared_context or {},
        star_points=[
            StarPointSchema(**star) for star in (c.star_points or [])
        ],
    )


def _build_list_item(c: Constellation) -> ConstellationListItem:
    """Build ConstellationListItem response from model instance."""
    return ConstellationListItem(
        id=c.id,
        name=c.name,
        description=c.description,
        thumbnail_url=c.thumbnail_url,
        preset=c.preset,
        target_scene_count=c.target_scene_count,
        scene_count=c.scene_count,
        completed_count=c.completed_count,
        progress_percent=c.progress_percent,
        creator_id=c.creator_id,
        creator_name=c.creator_name,
        is_public=c.is_public,
        use_count=c.use_count,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


async def _get_constellation_or_404(
    db: AsyncSession,
    constellation_id: UUID,
    user_id: Optional[str] = None,
    require_owner: bool = False,
) -> Constellation:
    """Fetch constellation with optional access checks."""
    result = await db.execute(
        select(Constellation).where(Constellation.id == constellation_id)
    )
    constellation = result.scalar_one_or_none()

    if not constellation:
        raise HTTPException(status_code=404, detail="Constellation not found")

    if require_owner and constellation.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Only the creator can perform this action")

    if not require_owner and not constellation.is_public and constellation.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return constellation


# =============================================================================
# ENDPOINTS - CONSTELLATION CRUD
# =============================================================================

@router.get("", response_model=ConstellationListResponse)
async def list_constellations(
    preset: Optional[str] = Query(None, pattern="^(short_drama|medium|feature_film)$"),
    creator_id: Optional[str] = None,
    public_only: bool = True,
    sort_by: str = Query("created_at", pattern="^(created_at|use_count|name)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """List constellations with filtering and pagination."""
    query = select(Constellation)

    # Filter by visibility
    if public_only:
        if user_id:
            query = query.where(
                (Constellation.is_public == True) | (Constellation.creator_id == user_id)
            )
        else:
            query = query.where(Constellation.is_public == True)
    elif creator_id:
        query = query.where(Constellation.creator_id == creator_id)

    # Filter by preset
    if preset:
        query = query.where(Constellation.preset == preset)

    # Sort
    sort_column = getattr(Constellation, sort_by)
    query = query.order_by(desc(sort_column) if sort_order == "desc" else asc(sort_column))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return ConstellationListResponse(
        items=[_build_list_item(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{constellation_id}", response_model=ConstellationDetail)
async def get_constellation(
    constellation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """Get constellation details by ID."""
    constellation = await _get_constellation_or_404(db, constellation_id, user_id)
    return _build_detail_response(constellation)


@router.post("", response_model=ConstellationDetail)
async def create_constellation(
    data: ConstellationCreate,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """Create a new constellation."""
    if not user_id:
        user_id = "anonymous"

    constellation = Constellation(
        name=data.name.strip(),
        description=data.description.strip() if data.description else "",
        preset=data.preset,
        target_scene_count=data.target_scene_count,
        shared_context=data.shared_context or {},
        star_points=[],
        creator_id=user_id,
        creator_name="Creator",  # TODO: Get from user profile
        is_public=False,
    )

    # Add first star if singularity_id provided
    if data.first_singularity_id:
        singularity_result = await db.execute(
            select(BlackholeTemplate).where(
                BlackholeTemplate.id == UUID(data.first_singularity_id)
            )
        )
        singularity = singularity_result.scalar_one_or_none()
        if not singularity:
            raise HTTPException(status_code=404, detail="Singularity not found")

        constellation.add_star(
            singularity_id=data.first_singularity_id,
            singularity_name=singularity.title,
        )

    db.add(constellation)
    await db.commit()
    await db.refresh(constellation)

    logger.info(f"Created constellation {constellation.id} by user {user_id}")
    return _build_detail_response(constellation)


@router.put("/{constellation_id}", response_model=ConstellationDetail)
async def update_constellation(
    constellation_id: UUID,
    data: ConstellationUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """Update constellation metadata."""
    constellation = await _get_constellation_or_404(db, constellation_id, user_id, require_owner=True)

    # Update fields (strip strings)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(constellation, key, value)

    constellation.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(constellation)

    return _build_detail_response(constellation)


@router.delete("/{constellation_id}")
async def delete_constellation(
    constellation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """Delete a constellation."""
    constellation = await _get_constellation_or_404(db, constellation_id, user_id, require_owner=True)

    await db.delete(constellation)
    await db.commit()

    logger.info(f"Deleted constellation {constellation_id} by user {user_id}")
    return {"success": True, "message": "Constellation deleted"}


# =============================================================================
# ENDPOINTS - STAR MANAGEMENT
# =============================================================================

@router.post("/{constellation_id}/stars", response_model=StarPointSchema)
async def add_star(
    constellation_id: UUID,
    data: StarAdd,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """Add a star (scene) to the constellation."""
    constellation = await _get_constellation_or_404(db, constellation_id, user_id, require_owner=True)

    # Fetch and validate singularity
    singularity_result = await db.execute(
        select(BlackholeTemplate).where(BlackholeTemplate.id == UUID(data.singularity_id))
    )
    singularity = singularity_result.scalar_one_or_none()
    if not singularity:
        raise HTTPException(status_code=404, detail="Singularity not found")

    # Add star (catches duplicate scene_number)
    try:
        star = constellation.add_star(
            singularity_id=data.singularity_id,
            singularity_name=singularity.title,
            overrides=data.overrides,
            scene_number=data.scene_number,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Constellation operation"))

    flag_modified(constellation, "star_points")
    constellation.updated_at = datetime.utcnow()
    await db.commit()

    return StarPointSchema(**star)


@router.put("/{constellation_id}/stars/{scene_number}", response_model=StarPointSchema)
async def update_star(
    constellation_id: UUID,
    scene_number: int,
    data: StarUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """Update a star's properties."""
    constellation = await _get_constellation_or_404(db, constellation_id, user_id, require_owner=True)

    # Update star
    updates = data.model_dump(exclude_unset=True)
    star = constellation.update_star(scene_number, updates)

    if not star:
        raise HTTPException(status_code=404, detail=f"Star {scene_number} not found")

    flag_modified(constellation, "star_points")
    constellation.updated_at = datetime.utcnow()
    await db.commit()

    return StarPointSchema(**star)


@router.delete("/{constellation_id}/stars/{scene_number}")
async def delete_star(
    constellation_id: UUID,
    scene_number: int,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """Remove a star from the constellation."""
    constellation = await _get_constellation_or_404(db, constellation_id, user_id, require_owner=True)

    removed = constellation.remove_star(scene_number)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Star {scene_number} not found")

    flag_modified(constellation, "star_points")
    constellation.updated_at = datetime.utcnow()
    await db.commit()

    return {"success": True, "message": f"Star {scene_number} removed"}


@router.post("/{constellation_id}/stars/{scene_number}/generate")
async def generate_star(
    constellation_id: UUID,
    scene_number: int,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """Get redirect URL to Flow page for generating a star's content.

    Returns the URL with singularity template pre-loaded.
    The actual generation happens on the Flow page.
    """
    # Allow both owner and users with read access
    constellation = await _get_constellation_or_404(db, constellation_id, user_id)

    star = constellation.get_star(scene_number)
    if not star:
        raise HTTPException(status_code=404, detail=f"Star {scene_number} not found")

    singularity_id = star.get("singularity_id")
    if not singularity_id:
        raise HTTPException(status_code=400, detail="Star has no singularity assigned")

    return {
        "redirect_url": f"/flow?template={singularity_id}&constellation={constellation_id}&scene={scene_number}",
        "singularity_id": singularity_id,
        "constellation_id": str(constellation_id),
        "scene_number": scene_number,
        "overrides": star.get("overrides", {}),
    }
