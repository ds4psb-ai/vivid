"""Singularity Template API Router.

REST API for the Singularity Template Gallery (차원의 특이점):
- List/filter templates
- Get template details
- Apply template (increment usage)
- Rate template
- Create/update templates (admin)
"""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models_singularity import BlackholeTemplate, BlackholeUsage
from app.dependencies import get_optional_user_id

router = APIRouter(prefix="/singularity", tags=["singularity"])


# =============================================================================
# SCHEMAS
# =============================================================================

class TemplateListItem(BaseModel):
    """Template summary for list view."""
    id: UUID
    title: str
    description: str
    thumbnail_url: Optional[str] = None
    dimension_source: str
    dimension_sequence: List[str] = []  # 차원 조합 (1D→2D→3D)
    tags: List[str] = []
    use_count: int
    rating_avg: float
    creator_name: str
    is_featured: bool
    tool_names: List[str] = []  # 사용된 도구 이름들
    
    class Config:
        from_attributes = True


class TemplateDetail(TemplateListItem):
    """Full template details."""
    tool_sequence: List[str] = []
    input_preset: dict = {}
    output_example: dict = {}
    category: str
    

class TemplateCreate(BaseModel):
    """Create a new template."""
    title: str = Field(..., max_length=200)
    description: str
    thumbnail_url: Optional[str] = None
    dimension_source: str = Field(..., pattern="^[1-4]D$")
    tool_sequence: List[str] = []
    input_preset: dict = {}
    output_example: dict = {}
    tags: List[str] = []
    category: str = "general"


class TemplateRating(BaseModel):
    """Rate a template after use."""
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


class TemplateListResponse(BaseModel):
    """Paginated template list."""
    items: List[TemplateListItem]
    total: int
    page: int
    page_size: int


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    dimension: Optional[str] = Query(None, pattern="^[1-4]D$"),
    category: Optional[str] = None,
    featured_only: bool = False,
    sort_by: str = Query("use_count", pattern="^(use_count|rating|created_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """List all public templates with filtering and sorting."""
    query = select(BlackholeTemplate).where(
        BlackholeTemplate.is_public == True,
        BlackholeTemplate.is_approved == True,
    )
    
    # Filters
    if dimension:
        query = query.where(BlackholeTemplate.dimension_source == dimension)
    if category:
        query = query.where(BlackholeTemplate.category == category)
    if featured_only:
        query = query.where(BlackholeTemplate.is_featured == True)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Sorting
    sort_column = {
        "use_count": BlackholeTemplate.use_count,
        "rating": BlackholeTemplate.rating_sum,  # Approximate by sum
        "created_at": BlackholeTemplate.created_at,
    }[sort_by]
    
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    items = [
        TemplateListItem(
            id=t.id,
            title=t.title,
            description=t.description,
            thumbnail_url=t.thumbnail_url,
            dimension_source=t.dimension_source,
            dimension_sequence=t.tool_sequence or [t.dimension_source],  # 사용된 차원 조합
            tags=t.tags or [],
            use_count=t.use_count,
            rating_avg=t.rating_avg,
            creator_name=t.creator_name,
            is_featured=t.is_featured,
            tool_names=[],  # TODO: 실제 도구 이름 매핑
        )
        for t in templates
    ]
    
    return TemplateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/templates/{template_id}", response_model=TemplateDetail)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get template details by ID."""
    result = await db.execute(
        select(BlackholeTemplate).where(BlackholeTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return TemplateDetail(
        id=template.id,
        title=template.title,
        description=template.description,
        thumbnail_url=template.thumbnail_url,
        dimension_source=template.dimension_source,
        tags=template.tags or [],
        use_count=template.use_count,
        rating_avg=template.rating_avg,
        creator_name=template.creator_name,
        is_featured=template.is_featured,
        tool_sequence=template.tool_sequence or [],
        input_preset=template.input_preset or {},
        output_example=template.output_example or {},
        category=template.category,
    )


@router.post("/templates/{template_id}/use")
async def use_template(
    template_id: UUID,
    user_id: Optional[str] = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Record template usage and return template data for applying."""
    result = await db.execute(
        select(BlackholeTemplate).where(BlackholeTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Increment use count
    template.use_count += 1
    
    # Record usage
    usage = BlackholeUsage(
        template_id=template_id,
        user_id=user_id or "anonymous",
    )
    db.add(usage)
    await db.commit()
    
    return {
        "success": True,
        "template_id": str(template_id),
        "tool_sequence": template.tool_sequence,
        "input_preset": template.input_preset,
        "message": f"Template '{template.title}' applied successfully",
    }


@router.post("/templates/{template_id}/rate")
async def rate_template(
    template_id: UUID,
    rating_data: TemplateRating,
    user_id: Optional[str] = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Rate a template after using it."""
    result = await db.execute(
        select(BlackholeTemplate).where(BlackholeTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Update rating
    template.rating_sum += rating_data.rating
    template.rating_count += 1
    
    # Update usage record if exists
    usage_result = await db.execute(
        select(BlackholeUsage)
        .where(
            BlackholeUsage.template_id == template_id,
            BlackholeUsage.user_id == (user_id or "anonymous"),
        )
        .order_by(desc(BlackholeUsage.created_at))
        .limit(1)
    )
    usage = usage_result.scalar_one_or_none()
    
    if usage:
        usage.rating = rating_data.rating
        usage.feedback = rating_data.feedback
    
    await db.commit()
    
    return {
        "success": True,
        "template_id": str(template_id),
        "new_rating_avg": template.rating_avg,
    }


@router.post("/templates", response_model=TemplateDetail)
async def create_template(
    template_data: TemplateCreate,
    user_id: Optional[str] = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new template (requires approval for public visibility)."""
    template = BlackholeTemplate(
        title=template_data.title,
        description=template_data.description,
        thumbnail_url=template_data.thumbnail_url,
        dimension_source=template_data.dimension_source,
        tool_sequence=template_data.tool_sequence,
        input_preset=template_data.input_preset,
        output_example=template_data.output_example,
        tags=template_data.tags,
        category=template_data.category,
        creator_id=user_id or "anonymous",
        creator_name="Creator",  # TODO: Get from user profile
        is_public=True,
        is_approved=False,  # Requires admin approval
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return TemplateDetail(
        id=template.id,
        title=template.title,
        description=template.description,
        thumbnail_url=template.thumbnail_url,
        dimension_source=template.dimension_source,
        tags=template.tags or [],
        use_count=template.use_count,
        rating_avg=template.rating_avg,
        creator_name=template.creator_name,
        is_featured=template.is_featured,
        tool_sequence=template.tool_sequence or [],
        input_preset=template.input_preset or {},
        output_example=template.output_example or {},
        category=template.category,
    )


@router.post("/seed")
async def seed_templates(
    db: AsyncSession = Depends(get_db),
):
    """Seed initial templates for development/demo purposes."""
    seed_data = [
        {
            "title": "시네마틱 프롬프트 마스터",
            "description": "영화급 시네마틱 프롬프트를 생성하는 완성형 워크플로우. VEO 2에 최적화된 영화적 연출 기법을 자동으로 적용합니다.",
            "thumbnail_url": "/images/portfolio_noir.png",
            "dimension_source": "1D",
            "tool_sequence": ["prompt_generator"],
            "input_preset": {"style": "cinematic", "mood": "dramatic"},
            "tags": ["영화", "VEO", "프롬프트", "시네마틱"],
            "category": "film",
            "creator_name": "김태은",
            "is_featured": True,
            "is_approved": True,
        },
        {
            "title": "사주 기반 캐릭터 생성",
            "description": "사주(Four Pillars) 분석을 통한 고유 캐릭터 아이덴티티 생성. 당신만의 운명적 캐릭터를 발견하세요.",
            "thumbnail_url": "/images/portfolio_anime.png",
            "dimension_source": "3D",
            "tool_sequence": ["saju_analyzer", "character_generator"],
            "input_preset": {},
            "tags": ["캐릭터", "사주", "AI", "페르소나"],
            "category": "character",
            "creator_name": "하소이",
            "is_featured": True,
            "is_approved": True,
        },
        {
            "title": "황금비 구도 분석기",
            "description": "거장들의 촬영 기법을 수치화하여 적용. 황금비, 3분할법, 대칭/비대칭 구도를 자동으로 분석하고 권장합니다.",
            "thumbnail_url": "/images/mentor_1.png",
            "dimension_source": "2D",
            "tool_sequence": ["composition_analyzer", "prompt_generator"],
            "input_preset": {"analysis_mode": "golden_ratio"},
            "tags": ["구도", "분석", "레퍼런스", "황금비"],
            "category": "analysis",
            "creator_name": "박지수",
            "is_featured": False,
            "is_approved": True,
        },
    ]
    
    created = []
    for data in seed_data:
        # Check if already exists
        existing = await db.execute(
            select(BlackholeTemplate).where(BlackholeTemplate.title == data["title"])
        )
        if existing.scalar_one_or_none():
            continue
        
        template = BlackholeTemplate(
            title=data["title"],
            description=data["description"],
            thumbnail_url=data["thumbnail_url"],
            dimension_source=data["dimension_source"],
            tool_sequence=data["tool_sequence"],
            input_preset=data["input_preset"],
            tags=data["tags"],
            category=data["category"],
            creator_id="system",
            creator_name=data["creator_name"],
            is_featured=data["is_featured"],
            is_approved=data["is_approved"],
            is_public=True,
        )
        db.add(template)
        created.append(data["title"])
    
    await db.commit()
    
    return {
        "success": True,
        "created": created,
        "count": len(created),
    }
