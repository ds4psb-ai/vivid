"""Prompty Project API.

CRUD operations for user workflow projects.
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes

from app.database import get_db
from app.models_prompty import PromptyProject, PromptyTemplate
from app.dependencies import get_current_user_id
from app.middleware.rate_limit import limiter, RATE_LIMIT_PROMPTY_PROJECT_CREATE

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["prompty-projects"])


# =============================================================================
# SCHEMAS
# =============================================================================

class ProjectCreate(BaseModel):
    """Create a new project."""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    template_id: Optional[UUID] = None


class ProjectState(BaseModel):
    """Project state for Yjs sync."""
    stages: dict = Field(default_factory=dict)
    current_step: str = ""
    last_activity: Optional[datetime] = None


class ProjectUpdate(BaseModel):
    """Update project metadata or state."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    state: Optional[ProjectState] = None
    current_stage: Optional[str] = None
    current_step: Optional[str] = None
    progress_percent: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[str] = None
    visibility: Optional[str] = Field(None, pattern="^(private|prompts-only|full)$")


class ProjectResponse(BaseModel):
    """Project response."""
    id: UUID
    name: str
    description: Optional[str]
    thumbnail_url: Optional[str]
    template_id: Optional[UUID]
    state: dict
    current_stage: str
    current_step: str
    progress_percent: int
    status: str
    visibility: str
    forked_from_id: Optional[UUID]
    fork_count: int
    avg_score: Optional[float]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ProjectListItem(BaseModel):
    """Project summary for list view."""
    id: UUID
    name: str
    description: Optional[str]
    thumbnail_url: Optional[str]
    current_stage: str
    current_step: str
    progress_percent: int
    status: str
    visibility: str
    avg_score: Optional[float]
    fork_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    """Paginated project list."""
    items: List[ProjectListItem]
    total: int
    page: int
    page_size: int


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("", response_model=ProjectResponse, status_code=201)
@limiter.limit(RATE_LIMIT_PROMPTY_PROJECT_CREATE)
async def create_project(
    request: Request,
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new workflow project.

    Optionally based on a template from the marketplace.
    """
    logger.info(f"Creating project: name={data.name}, user_id={user_id}, template_id={data.template_id}")

    # Initialize state
    initial_state = {
        "stages": {
            "analysis": {"status": "pending", "files": []},
            "image": {},
            "video": {},
            "assembly": {},
        },
        "current_step": "",
        "last_activity": datetime.utcnow().isoformat(),
    }

    # If template provided, load workflow config
    if data.template_id:
        template_result = await db.execute(
            select(PromptyTemplate).where(PromptyTemplate.id == data.template_id)
        )
        template = template_result.scalar_one_or_none()

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Initialize state from template workflow
        workflow = template.workflow_config
        if workflow.get("stages"):
            initial_state["stages"] = {
                stage: {"status": "pending", "files": []}
                for stage in workflow["stages"]
            }

        # Increment template use count
        template.use_count += 1

    project = PromptyProject(
        name=data.name,
        description=data.description,
        user_id=user_id,
        template_id=data.template_id,
        state=initial_state,
        current_stage="analysis",
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    logger.info(f"Project created: id={project.id}, user_id={user_id}")
    return project


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List user's projects."""
    query = select(PromptyProject).where(PromptyProject.user_id == user_id)

    if status:
        query = query.where(PromptyProject.status == status)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(desc(PromptyProject.updated_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    projects = result.scalars().all()

    return ProjectListResponse(
        items=[ProjectListItem.model_validate(p) for p in projects],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get project details."""
    result = await db.execute(
        select(PromptyProject).where(
            PromptyProject.id == project_id,
            PromptyProject.user_id == user_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        logger.warning(f"Project not found: id={project_id}, user_id={user_id}")
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.put("/{project_id}/state", response_model=ProjectResponse)
async def update_project_state(
    project_id: UUID,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update project state (STATE.md sync).

    Primary endpoint for Yjs CRDT synchronization.
    """
    result = await db.execute(
        select(PromptyProject).where(
            PromptyProject.id == project_id,
            PromptyProject.user_id == user_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        logger.warning(f"Project not found for state update: id={project_id}, user_id={user_id}")
        raise HTTPException(status_code=404, detail="Project not found")

    logger.debug(f"Updating project state: id={project_id}")

    # Update fields
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    if data.thumbnail_url is not None:
        project.thumbnail_url = data.thumbnail_url
    if data.state is not None:
        project.state = data.state.model_dump()
        attributes.flag_modified(project, "state")
    if data.current_stage is not None:
        project.current_stage = data.current_stage
    if data.current_step is not None:
        project.current_step = data.current_step
    if data.progress_percent is not None:
        project.progress_percent = data.progress_percent
    if data.status is not None:
        project.status = data.status
        if data.status == "completed":
            project.completed_at = datetime.utcnow()
    if data.visibility is not None:
        project.visibility = data.visibility

    project.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(project)

    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a project."""
    result = await db.execute(
        select(PromptyProject).where(
            PromptyProject.id == project_id,
            PromptyProject.user_id == user_id,
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()

    logger.info(f"Project deleted: id={project_id}, user_id={user_id}")


# =============================================================================
# FORK ENDPOINT
# =============================================================================

class ForkRequest(BaseModel):
    """Fork request body."""
    name: Optional[str] = Field(None, max_length=200)


@router.post("/{project_id}/fork", response_model=ProjectResponse, status_code=201)
async def fork_project(
    project_id: UUID,
    data: ForkRequest = ForkRequest(),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Fork a public project.

    Creates a new project based on the source project.
    - Copies state/config from source
    - Sets visibility to 'private'
    - Tracks fork relationship
    - Increments source fork_count
    """
    # Get source project
    result = await db.execute(
        select(PromptyProject).where(PromptyProject.id == project_id)
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check visibility - can only fork non-private projects (or own projects)
    if source.visibility == "private" and source.user_id != user_id:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create forked project
    forked_name = data.name or f"{source.name} (Fork)"

    # Copy state - reset progress for new project
    forked_state = dict(source.state) if source.state else {}
    # Reset step statuses to pending
    if "stages" in forked_state:
        for stage_data in forked_state["stages"].values():
            if isinstance(stage_data, dict):
                stage_data["status"] = "pending"
    forked_state["last_activity"] = datetime.utcnow().isoformat()

    forked = PromptyProject(
        name=forked_name,
        description=source.description,
        user_id=user_id,
        template_id=source.template_id,
        state=forked_state,
        current_stage=source.current_stage or "analysis",
        current_step="",
        progress_percent=0,
        status="active",
        visibility="private",  # Forked projects start as private
        forked_from_id=source.id,
    )

    db.add(forked)

    # Increment source fork count
    source.fork_count += 1

    await db.commit()
    await db.refresh(forked)

    logger.info(f"Project forked: source_id={project_id}, forked_id={forked.id}, user_id={user_id}")
    return forked
