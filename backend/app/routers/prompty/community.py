"""Prompty Community API.

Public project gallery for community sharing and discovery.
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models_prompty import PromptyProject
from app.dependencies import get_current_user_id, get_optional_user_id

router = APIRouter(prefix="/community", tags=["prompty-community"])


# =============================================================================
# SCHEMAS
# =============================================================================

class CommunityProjectItem(BaseModel):
    """Public project for community display."""
    id: UUID
    name: str
    description: Optional[str]
    thumbnail_url: Optional[str]
    user_id: str
    user_name: Optional[str] = None  # TODO: Join with user table
    current_stage: str
    progress_percent: int
    status: str
    visibility: str
    avg_score: Optional[float]
    fork_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommunityProjectListResponse(BaseModel):
    """Paginated community project list."""
    items: List[CommunityProjectItem]
    total: int
    page: int
    page_size: int


class CommunityProjectDetail(BaseModel):
    """Detailed public project view."""
    id: UUID
    name: str
    description: Optional[str]
    thumbnail_url: Optional[str]
    user_id: str
    user_name: Optional[str] = None
    template_id: Optional[UUID]
    # State is only shown for 'full' visibility
    state: Optional[dict] = None
    current_stage: str
    current_step: str
    progress_percent: int
    status: str
    visibility: str
    forked_from_id: Optional[UUID]
    avg_score: Optional[float]
    fork_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    # Whether current user can see prompts
    can_see_prompts: bool = False

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("", response_model=CommunityProjectListResponse)
async def list_community_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("recent", pattern="^(recent|top-scores|most-forked)$"),
    status: Optional[str] = Query(None, pattern="^(active|completed)$"),
    db: AsyncSession = Depends(get_db),
):
    """List public community projects.

    Only returns projects with visibility != 'private'.
    """
    # Base query: non-private projects
    query = select(PromptyProject).where(
        PromptyProject.visibility != "private"
    )

    # Optional status filter
    if status:
        query = query.where(PromptyProject.status == status)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Sort
    if sort == "recent":
        query = query.order_by(desc(PromptyProject.updated_at))
    elif sort == "top-scores":
        query = query.order_by(
            desc(PromptyProject.avg_score.isnot(None)),
            desc(PromptyProject.avg_score),
            desc(PromptyProject.updated_at),
        )
    elif sort == "most-forked":
        query = query.order_by(
            desc(PromptyProject.fork_count),
            desc(PromptyProject.updated_at),
        )

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    projects = result.scalars().all()

    return CommunityProjectListResponse(
        items=[CommunityProjectItem.model_validate(p) for p in projects],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{project_id}", response_model=CommunityProjectDetail)
async def get_community_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """Get public project details.

    - Private projects return 404
    - prompts-only projects hide state (prompts)
    - full projects show everything
    """
    result = await db.execute(
        select(PromptyProject).where(PromptyProject.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check visibility
    if project.visibility == "private":
        # Only owner can see private projects
        if user_id != project.user_id:
            raise HTTPException(status_code=404, detail="Project not found")

    # Determine what to show
    is_owner = user_id == project.user_id
    can_see_prompts = is_owner or project.visibility == "full"

    # Build response
    response_data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "thumbnail_url": project.thumbnail_url,
        "user_id": project.user_id,
        "template_id": project.template_id,
        "state": project.state if can_see_prompts else None,
        "current_stage": project.current_stage,
        "current_step": project.current_step,
        "progress_percent": project.progress_percent,
        "status": project.status,
        "visibility": project.visibility,
        "forked_from_id": project.forked_from_id,
        "avg_score": project.avg_score,
        "fork_count": project.fork_count,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "completed_at": project.completed_at,
        "can_see_prompts": can_see_prompts,
    }

    return CommunityProjectDetail(**response_data)


# =============================================================================
# INSTRUCTOR ACCESS (Hardcoded IDs)
# =============================================================================

# Hardcoded instructor IDs - can see all student projects
INSTRUCTOR_IDS = [
    "ted@example.com",
    "admin@prompty.co.kr",
]


@router.get("/instructor/all", response_model=CommunityProjectListResponse)
async def list_all_projects_for_instructor(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    sort: str = Query("recent", pattern="^(recent|user|score)$"),
    user_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """[Instructor Only] List all student projects.

    Requires instructor privileges (hardcoded IDs).
    """
    if user_id not in INSTRUCTOR_IDS:
        raise HTTPException(status_code=403, detail="Instructor access required")

    # Query all projects (regardless of visibility)
    query = select(PromptyProject)

    # Optional user filter
    if user_filter:
        query = query.where(PromptyProject.user_id == user_filter)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Sort
    if sort == "recent":
        query = query.order_by(desc(PromptyProject.updated_at))
    elif sort == "user":
        query = query.order_by(
            PromptyProject.user_id,
            desc(PromptyProject.updated_at),
        )
    elif sort == "score":
        query = query.order_by(
            desc(PromptyProject.avg_score.isnot(None)),
            desc(PromptyProject.avg_score),
        )

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    projects = result.scalars().all()

    return CommunityProjectListResponse(
        items=[CommunityProjectItem.model_validate(p) for p in projects],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/instructor/students")
async def list_students_for_instructor(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """[Instructor Only] List all unique student IDs.

    Returns list of user_ids who have created projects.
    """
    if user_id not in INSTRUCTOR_IDS:
        raise HTTPException(status_code=403, detail="Instructor access required")

    result = await db.execute(
        select(PromptyProject.user_id)
        .distinct()
        .order_by(PromptyProject.user_id)
    )
    students = [row[0] for row in result.all()]

    return {"students": students, "total": len(students)}
