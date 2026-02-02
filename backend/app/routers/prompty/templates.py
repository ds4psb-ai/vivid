"""Prompty Template Marketplace API.

Template discovery and management.
"""
import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models_prompty import PromptyTemplate, PromptyProject
from app.dependencies import get_current_user, get_current_user_id, get_optional_user_id, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["prompty-templates"])


# =============================================================================
# SCHEMAS
# =============================================================================

class TemplateListItem(BaseModel):
    """Template summary for marketplace."""
    id: UUID
    title: str
    description: str
    thumbnail_url: Optional[str]
    category: str
    tags: List[str]
    use_count: int
    rating_avg: float
    creator_name: str
    is_featured: bool

    model_config = ConfigDict(from_attributes=True)


class TemplateDetail(TemplateListItem):
    """Full template details."""
    workflow_config: dict
    critique_config: dict
    example_project_url: Optional[str]


class TemplateCreate(BaseModel):
    """Create template (admin only)."""
    title: str = Field(..., max_length=200)
    description: str
    thumbnail_url: Optional[str] = None
    category: str = "video"
    workflow_config: dict = Field(default_factory=dict)
    critique_config: dict = Field(default_factory=dict)
    example_project_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_featured: bool = False


class TemplateRating(BaseModel):
    """Rate a template."""
    rating: int = Field(..., ge=1, le=5)


class TemplateListResponse(BaseModel):
    """Paginated template list."""
    items: List[TemplateListItem]
    total: int
    page: int
    page_size: int


class UseTemplateResponse(BaseModel):
    """Response after using a template to create project."""
    project_id: UUID
    template_title: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("", response_model=TemplateListResponse)
async def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    featured_only: bool = Query(False),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """List available templates in the marketplace."""
    query = select(PromptyTemplate).where(PromptyTemplate.is_public == True)

    if category:
        query = query.where(PromptyTemplate.category == category)

    if featured_only:
        query = query.where(PromptyTemplate.is_featured == True)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            PromptyTemplate.title.ilike(search_pattern) |
            PromptyTemplate.description.ilike(search_pattern)
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Sort and paginate
    query = query.order_by(
        desc(PromptyTemplate.is_featured),
        desc(PromptyTemplate.use_count),
    )
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    templates = result.scalars().all()

    items = []
    for t in templates:
        item = TemplateListItem(
            id=t.id,
            title=t.title,
            description=t.description,
            thumbnail_url=t.thumbnail_url,
            category=t.category,
            tags=t.tags or [],
            use_count=t.use_count,
            rating_avg=t.rating_avg,
            creator_name=t.creator_name,
            is_featured=t.is_featured,
        )
        items.append(item)

    return TemplateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{template_id}", response_model=TemplateDetail)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get template details."""
    result = await db.execute(
        select(PromptyTemplate).where(
            PromptyTemplate.id == template_id,
            PromptyTemplate.is_public == True,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return TemplateDetail(
        id=template.id,
        title=template.title,
        description=template.description,
        thumbnail_url=template.thumbnail_url,
        category=template.category,
        tags=template.tags or [],
        use_count=template.use_count,
        rating_avg=template.rating_avg,
        creator_name=template.creator_name,
        is_featured=template.is_featured,
        workflow_config=template.workflow_config or {},
        critique_config=template.critique_config or {},
        example_project_url=template.example_project_url,
    )


@router.post("/{template_id}/use", response_model=UseTemplateResponse)
async def use_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Use a template to create a new project.

    Creates a project with the template's workflow config applied.
    """
    result = await db.execute(
        select(PromptyTemplate).where(
            PromptyTemplate.id == template_id,
            PromptyTemplate.is_public == True,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Initialize state from template workflow
    workflow = template.workflow_config or {}
    stages = workflow.get("stages", ["analysis", "image", "video", "assembly"])

    initial_state = {
        "stages": {stage: {"status": "pending", "files": []} for stage in stages},
        "current_step": "",
        "last_activity": None,
    }

    # Create project
    project = PromptyProject(
        name=f"{template.title} - New Project",
        description=f"Based on: {template.title}",
        user_id=current_user["id"],
        template_id=template.id,
        state=initial_state,
        current_stage=stages[0] if stages else "analysis",
    )

    # Increment use count
    template.use_count += 1

    db.add(project)
    await db.commit()
    await db.refresh(project)

    logger.info(f"Template used: template_id={template_id}, project_id={project.id}, user_id={current_user['id']}")
    return UseTemplateResponse(
        project_id=project.id,
        template_title=template.title,
    )


@router.post("/{template_id}/rate", status_code=204)
async def rate_template(
    template_id: UUID,
    data: TemplateRating,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Rate a template after using it."""
    result = await db.execute(
        select(PromptyTemplate).where(PromptyTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Update rating (simple cumulative average)
    template.rating_sum += data.rating
    template.rating_count += 1

    await db.commit()


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@router.post("", response_model=TemplateDetail, status_code=201)
async def create_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(require_admin),
):
    """Create a new template (admin only)."""
    template = PromptyTemplate(
        title=data.title,
        description=data.description,
        thumbnail_url=data.thumbnail_url,
        creator_id=admin_user["user_id"],
        creator_name=admin_user.get("name", "Prompty Team"),
        category=data.category,
        workflow_config=data.workflow_config,
        critique_config=data.critique_config,
        example_project_url=data.example_project_url,
        tags=data.tags,
        is_featured=data.is_featured,
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    logger.info(f"Template created: id={template.id}, title={data.title}, creator={admin_user['user_id']}")
    return TemplateDetail(
        id=template.id,
        title=template.title,
        description=template.description,
        thumbnail_url=template.thumbnail_url,
        category=template.category,
        tags=template.tags or [],
        use_count=template.use_count,
        rating_avg=template.rating_avg,
        creator_name=template.creator_name,
        is_featured=template.is_featured,
        workflow_config=template.workflow_config or {},
        critique_config=template.critique_config or {},
        example_project_url=template.example_project_url,
    )
