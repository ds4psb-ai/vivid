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
        # =============================================================================
        # AI 애니메이션 워크플로우
        # =============================================================================
        {
            "title": "AI 애니메이션 마스터",
            "description": "프롬프트 → 스토리보드 → 이미지 → 영상까지. 아이디어 하나로 완성하는 풀 파이프라인 애니메이션 워크플로우.",
            "thumbnail_url": "/images/portfolio_anime.png",
            "dimension_source": "1D",
            "tool_sequence": ["1D", "2D", "3D", "VEO"],
            "input_preset": {
                "style": "anime",
                "mood": "vibrant",
                "duration": "30 seconds",
                "aspect_ratio": "16:9",
            },
            "output_example": {
                "prompt": "A young hero awakens magical powers in a neon-lit cyberpunk city...",
                "scenes": 6,
                "video_duration": "8s",
            },
            "tags": ["애니메이션", "풀파이프라인", "VEO", "콘텐츠"],
            "category": "animation",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },
        {
            "title": "캐릭터 중심 애니메이션",
            "description": "심연해석기로 캐릭터 DNA를 분석하고, 그에 맞는 스토리와 비주얼을 자동 생성합니다.",
            "thumbnail_url": "/images/portfolio_character.png",
            "dimension_source": "AI",
            "tool_sequence": ["AI", "1D", "2D", "3D"],
            "input_preset": {
                "depth": "deep",
                "style": "anime",
                "focus": "character_development",
            },
            "output_example": {
                "archetype": "영웅의 여정",
                "character_traits": ["용감한", "내성적", "성장형"],
            },
            "tags": ["캐릭터", "페르소나", "애니메이션", "스토리"],
            "category": "animation",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },

        # =============================================================================
        # AI 광고 워크플로우
        # =============================================================================
        {
            "title": "AI 광고 제작 풀패키지",
            "description": "브랜드 컨셉부터 스토리보드, 비주얼, 품질검수까지. 광고 대행사 수준의 결과물을 AI가 자동으로 생성합니다.",
            "thumbnail_url": "/images/portfolio_ad.png",
            "dimension_source": "AD",
            "tool_sequence": ["AD", "1D", "2D", "3D", "QC"],
            "input_preset": {
                "style": "commercial",
                "mood": "uplifting",
                "target_audience": "2030",
                "duration": "15 seconds",
            },
            "output_example": {
                "color_palette": ["#FF6B6B", "#4ECDC4", "#45B7D1"],
                "key_message": "당신의 일상을 특별하게",
                "cta": "지금 시작하세요",
            },
            "tags": ["광고", "마케팅", "브랜딩", "커머셜"],
            "category": "advertising",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },
        {
            "title": "제품 소개 영상 자동화",
            "description": "제품 설명만 입력하면 광고 프롬프트, 씬 구성, 키비주얼까지 자동 생성. SNS 광고 최적화.",
            "thumbnail_url": "/images/portfolio_product.png",
            "dimension_source": "1D",
            "tool_sequence": ["1D", "2D", "3D", "QC", "VEO"],
            "input_preset": {
                "style": "minimal",
                "mood": "professional",
                "duration": "15 seconds",
                "aspect_ratio": "9:16",  # 세로형 숏폼 광고
            },
            "output_example": {
                "hook": "3초 내 시선 집중",
                "benefit_points": 3,
                "cta_position": "end",
            },
            "tags": ["제품", "SNS", "숏폼", "광고"],
            "category": "advertising",
            "creator_name": "Crebit Studio",
            "is_featured": False,
            "is_approved": True,
        },
        {
            "title": "감성 브랜드 필름",
            "description": "미학디렉터가 브랜드 무드를 분석하고, 레퍼런스 해석기가 참고 영상을 분석하여 감성적인 브랜드 필름을 제작합니다.",
            "thumbnail_url": "/images/portfolio_brand.png",
            "dimension_source": "4D",
            "tool_sequence": ["4D", "AD", "1D", "2D", "VEO"],
            "input_preset": {
                "style": "cinematic",
                "mood": "emotional",
                "analysis_focus": ["color", "mood", "pacing"],
            },
            "output_example": {
                "visual_style": "Wes Anderson meets Apple",
                "emotional_arc": "호기심 → 공감 → 영감",
            },
            "tags": ["브랜드", "감성", "시네마틱", "비주얼"],
            "category": "advertising",
            "creator_name": "Crebit Studio",
            "is_featured": False,
            "is_approved": True,
        },

        # =============================================================================
        # AI 숏폼 워크플로우
        # =============================================================================
        {
            "title": "3분 숏폼 콘텐츠",
            "description": "유튜브 쇼츠, 틱톡, 릴스에 최적화된 3분 미만 숏폼 콘텐츠를 기획부터 영상까지 원스톱으로 제작합니다.",
            "thumbnail_url": "/images/portfolio_shortform.png",
            "dimension_source": "1D",
            "tool_sequence": ["1D", "2D", "3D", "VEO"],
            "input_preset": {
                "style": "dynamic",
                "mood": "energetic",
                "duration": "60 seconds",
                "aspect_ratio": "9:16",
                "scene_count": 12,  # 5초당 1씬
            },
            "output_example": {
                "hook_duration": "3s",
                "scene_transitions": "fast_cuts",
                "engagement_points": ["0s", "15s", "45s"],
            },
            "tags": ["숏폼", "유튜브", "틱톡", "릴스", "콘텐츠"],
            "category": "shortform",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },
        {
            "title": "바이럴 숏폼 메이커",
            "description": "트렌드 분석 + 후킹 포인트 자동 생성. 알고리즘에 최적화된 바이럴 숏폼 콘텐츠를 만듭니다.",
            "thumbnail_url": "/images/portfolio_viral.png",
            "dimension_source": "1D",
            "tool_sequence": ["1D", "2D", "QC", "VEO"],
            "input_preset": {
                "style": "trendy",
                "mood": "exciting",
                "duration": "30 seconds",
                "aspect_ratio": "9:16",
                "hook_style": "question",  # 질문형 훅
            },
            "output_example": {
                "hook_type": "curiosity_gap",
                "retention_curve": "exponential",
                "share_trigger": "emotional",
            },
            "tags": ["바이럴", "트렌드", "숏폼", "SNS"],
            "category": "shortform",
            "creator_name": "Crebit Studio",
            "is_featured": False,
            "is_approved": True,
        },
        {
            "title": "교육 콘텐츠 숏폼",
            "description": "복잡한 개념을 3분 안에 쉽게 설명하는 교육용 숏폼. 인포그래픽 스타일 비주얼과 명확한 구조.",
            "thumbnail_url": "/images/portfolio_edu.png",
            "dimension_source": "1D",
            "tool_sequence": ["1D", "2D", "3D", "QC"],
            "input_preset": {
                "style": "infographic",
                "mood": "informative",
                "duration": "90 seconds",
                "structure": "problem_solution",
            },
            "output_example": {
                "sections": ["문제 제기", "핵심 개념", "적용 방법", "요약"],
                "visual_style": "flat_design",
            },
            "tags": ["교육", "인포그래픽", "숏폼", "설명"],
            "category": "shortform",
            "creator_name": "Crebit Studio",
            "is_featured": False,
            "is_approved": True,
        },

        # =============================================================================
        # 크리에이터 특화 워크플로우
        # =============================================================================
        {
            "title": "시네마틱 뮤직비디오",
            "description": "레퍼런스 분석 → 미학 디렉팅 → 스토리보드 → 영상. 거장급 뮤직비디오 연출을 AI가 도와드립니다.",
            "thumbnail_url": "/images/portfolio_mv.png",
            "dimension_source": "4D",
            "tool_sequence": ["4D", "AD", "2D", "3D", "VEO"],
            "input_preset": {
                "style": "cinematic",
                "mood": "atmospheric",
                "reference_focus": ["lighting", "movement", "color_grading"],
            },
            "output_example": {
                "visual_motifs": ["shadow_play", "neon_glow", "slow_motion"],
                "color_grade": "teal_and_orange",
            },
            "tags": ["뮤직비디오", "시네마틱", "아티스트", "비주얼"],
            "category": "creative",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },
        {
            "title": "다큐멘터리 스타일 영상",
            "description": "진정성 있는 다큐멘터리 스타일 영상 제작. 내러티브 구조와 감성적 연출을 자동으로 설계합니다.",
            "thumbnail_url": "/images/portfolio_docu.png",
            "dimension_source": "AI",
            "tool_sequence": ["AI", "1D", "2D", "4D", "VEO"],
            "input_preset": {
                "style": "documentary",
                "mood": "authentic",
                "narrative_structure": "hero_journey",
            },
            "output_example": {
                "act_structure": ["setup", "confrontation", "resolution"],
                "interview_style": "intimate",
            },
            "tags": ["다큐멘터리", "스토리텔링", "진정성", "내러티브"],
            "category": "creative",
            "creator_name": "Crebit Studio",
            "is_featured": False,
            "is_approved": True,
        },

        # =============================================================================
        # 4-Stage Workflow 템플릿 (신규 차원 활용)
        # =============================================================================
        {
            "title": "프로덕션 풀스택",
            "description": "기획(STORY)부터 사전제작(SOUND), 제작(VIS), 완성(QC)까지. 전문 프로덕션 팀의 4단계 워크플로우를 AI로 자동화합니다.",
            "thumbnail_url": "/images/portfolio_production.png",
            "dimension_source": "STORY",
            "tool_sequence": ["STORY", "2D", "SOUND", "VIS", "VEO", "QC"],
            "input_preset": {
                "genre": "drama",
                "duration": "60s",
                "structure": "3act",
                "sound_type": "full",
            },
            "output_example": {
                "story_structure": {"acts": 3, "scenes": 6},
                "sound_design": {"bgm": True, "sfx": True, "narration": False},
                "quality_score": 92,
            },
            "tags": ["프로덕션", "4단계", "풀스택", "전문가"],
            "category": "production",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },
        {
            "title": "뮤직비디오 사운드 디자인",
            "description": "스토리보드에 맞는 BGM 프롬프트와 효과음 타이밍을 자동 생성. Suno, Udio 호환 출력.",
            "thumbnail_url": "/images/portfolio_sound.png",
            "dimension_source": "2D",
            "tool_sequence": ["2D", "SOUND", "3D", "VEO"],
            "input_preset": {
                "sound_type": "bgm",
                "genre": "cinematic",
                "tempo": "dynamic",
                "target_platform": "suno",
            },
            "output_example": {
                "music_prompt": "Cinematic orchestral, building tension, 120 BPM...",
                "style_tags": ["epic", "emotional", "crescendo"],
                "sfx_cues": 8,
            },
            "tags": ["사운드", "BGM", "뮤직비디오", "Suno"],
            "category": "creative",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },
        {
            "title": "시나리오 중심 영상 기획",
            "description": "심연해석기로 캐릭터 DNA를 분석하고, 시나리오 생성기가 3막 구조의 시나리오를 자동 작성합니다.",
            "thumbnail_url": "/images/portfolio_scenario.png",
            "dimension_source": "AI",
            "tool_sequence": ["AI", "STORY", "2D", "SOUND"],
            "input_preset": {
                "depth": "deep",
                "genre": "drama",
                "structure": "3act",
                "sound_type": "narration",
            },
            "output_example": {
                "archetype": "영웅의 여정",
                "logline": "한 문장으로 정리된 스토리",
                "voice_direction": {"tone": "warm", "pace": "moderate"},
            },
            "tags": ["시나리오", "기획", "캐릭터", "내러티브"],
            "category": "production",
            "creator_name": "Crebit Studio",
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
            input_preset=data.get("input_preset", {}),
            output_example=data.get("output_example", {}),
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
