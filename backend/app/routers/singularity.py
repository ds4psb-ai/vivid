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
from app.dependencies import get_optional_user_id, get_current_user, require_admin

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
    dimension_source: str  # AI, 4D, STORY, AD, 2D, SOUND, 1D, 3D, VEO, QC
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
# CONSTANTS
# =============================================================================

# Dimension code to display name mapping
DIMENSION_NAMES = {
    "AI": "심연의 거울",
    "4D": "레퍼런스 해석기",
    "STORY": "시나리오 생성기",
    "AD": "미학디렉터",
    "2D": "스토리보드 스케치",
    "SOUND": "사운드 크래프터",
    "1D": "프롬프트 디렉터",
    "3D": "비주얼 리얼라이저",
    "VEO": "비디오 메이커",
    "QC": "크리에이티브 에디터",
}


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    dimension: Optional[str] = Query(None),
    category: Optional[str] = None,
    tag: Optional[str] = None,  # Tag filter for frontend
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
    # Tag filter: check if tag exists in tags array
    if tag:
        query = query.where(BlackholeTemplate.tags.contains([tag]))

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
            dimension_sequence=t.tool_sequence or [t.dimension_source],
            tags=t.tags or [],
            use_count=t.use_count,
            rating_avg=t.rating_avg,
            creator_name=t.creator_name,
            is_featured=t.is_featured,
            tool_names=[DIMENSION_NAMES.get(d, d) for d in (t.tool_sequence or [])],
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
        dimension_sequence=template.tool_sequence or [template.dimension_source],
        tags=template.tags or [],
        use_count=template.use_count,
        rating_avg=template.rating_avg,
        creator_name=template.creator_name,
        is_featured=template.is_featured,
        tool_sequence=template.tool_sequence or [],
        tool_names=[DIMENSION_NAMES.get(d, d) for d in (template.tool_sequence or [])],
        input_preset=template.input_preset or {},
        output_example=template.output_example or {},
        category=template.category,
    )


@router.post("/templates/{template_id}/use")
async def use_template(
    template_id: UUID,
    user: dict = Depends(get_current_user),  # P1: Auth required - prevent abuse
    db: AsyncSession = Depends(get_db),
):
    """Record template usage and return template data for applying."""
    user_id = user.get("id") or user.get("sub")
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
    user: dict = Depends(get_current_user),  # P1: Auth required - prevent abuse
    db: AsyncSession = Depends(get_db),
):
    """Rate a template after using it."""
    user_id = user.get("id") or user.get("sub")
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
    user: dict = Depends(get_current_user),  # P1: Auth required
    db: AsyncSession = Depends(get_db),
):
    """Create a new template (requires approval for public visibility)."""
    user_id = user.get("id") or user.get("sub")
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
    user: dict = Depends(require_admin),  # P1: Admin only
    db: AsyncSession = Depends(get_db),
):
    """Seed initial templates for development/demo purposes.

    Templates follow the actual capsule connection graph:
    - AI (abyss-mirror) → 4D, STORY, AD
    - 4D (reference-decoder) → STORY, 2D
    - STORY (story-architect) → 2D, SOUND, 1D
    - AD (aesthetic-director) → STORY, 3D
    - 2D (storyboard-sketch) → SOUND, 1D
    - SOUND (sound-crafter) → VEO
    - 1D (prompt-alchemy) → 3D, VEO
    - 3D (visual-realizer) → VEO, QC
    - VEO (video-maker) → QC
    - QC (quality-director) → terminal
    """
    seed_data = [
        # =============================================================================
        # 요청된 신규 워크플로우 (최상단 배치) - Intent-based Migration
        # =============================================================================
        {
            "title": "시네마틱 프롬프트 마스터",
            "description": "영화급 시네마틱 프롬프트를 생성하는 완성형 워크플로우. VEO 2에 최적화된 영화적 연출 기법을 자동으로 적용합니다.",
            "thumbnail_url": "/images/portfolio_cinematic_prompt.png",
            "dimension_source": "1D",
            "tool_sequence": ["1D", "VEO"],
            # Phase 3: Intent-based input_preset (신규 형식)
            "input_preset": {
                "intent": {
                    "mood": "cinematic",
                    "pace": "slow",
                    "target": "expert",
                    "domain_sources": [],
                    "output_format": "video",
                    "keywords": ["dramatic-lighting", "anamorphic"]
                },
                
                "schema_version": "2.0"
            },
            "output_example": {
                "prompt": "Cinematic shot of...",
                "direction": "Low angle, heavy contrast",
                "video_uri": "generated_video.mp4"
            },
            "tags": ["영화", "VEO", "프롬프트", "시네마틱"],
            "category": "creative",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },
        {
            "title": "황금비 구도 분석기",
            "description": "거장들의 촬영 기법을 수치화하여 적용. 황금비, 3분할법, 대칭/비대칭 구도를 자동으로 분석하고 권장합니다.",
            "thumbnail_url": "/images/portfolio_golden.png",
            "dimension_source": "4D",
            "tool_sequence": ["4D", "1D", "VEO"],
            # Phase 3: Intent-based input_preset
            "input_preset": {
                "intent": {
                    "mood": "cinematic",
                    "pace": "contemplative",
                    "target": "expert",
                    "domain_sources": [],
                    "output_format": "video",
                    "aesthetic_hints": {
                        "composition_style": "golden-ratio"
                    },
                    "keywords": ["composition", "golden-ratio"]
                },
                
                "schema_version": "2.0"
            },
            "output_example": {
                "composition_score": 95,
                "grid_overlay": "visualized",
                "suggestion": "Rule of thirds alignment"
            },
            "tags": ["비주얼", "구도", "분석", "3분할"],
            "category": "creative",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },
        # =============================================================================
        # 풀 프로덕션 워크플로우 (4+ 연결) - Intent-based Migration
        # =============================================================================
        {
            "title": "크리에이터 DNA 풀스택",
            "description": "나만의 창작 DNA 분석부터 시나리오, 스토리보드, 프롬프트, 비주얼, 영상까지. 7단계 완전 자동화 워크플로우.",
            "thumbnail_url": "/images/portfolio_anime.png",
            "dimension_source": "AI",
            "tool_sequence": ["AI", "STORY", "2D", "1D", "3D", "VEO", "QC"],
            # Phase 3: Intent-based input_preset
            "input_preset": {
                "intent": {
                    "mood": "cinematic",
                    "pace": "dynamic",
                    "target": "general",
                    "domain_sources": ["drama"],
                    "output_format": "video",
                    "keywords": ["full-production", "dna-analysis"]
                },
                
                "schema_version": "2.0"
            },
            "output_example": {
                "persona": "창작 DNA 프로필",
                "story_structure": {"acts": 3, "scenes": 6},
                "video_uri": "generated_video.mp4",
            },
            "tags": ["풀스택", "DNA분석", "7단계", "완전자동화"],
            "category": "production",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },
        {
            "title": "레퍼런스 기반 프로덕션",
            "description": "참고 영상 분석 → 시나리오 → 스토리보드 → 사운드 → 영상. 레퍼런스 스타일을 완벽 재현하는 6단계 워크플로우.",
            "thumbnail_url": "/images/portfolio_mv.png",
            "dimension_source": "4D",
            "tool_sequence": ["4D", "STORY", "2D", "SOUND", "VEO", "QC"],
            "input_preset": {
                "analysis_focus": ["color", "lighting", "pacing", "movement"],
                "genre": "cinematic",
                "sound_type": "full",
            },
            "output_example": {
                "reference_analysis": "시네마틱 스타일 분석 결과",
                "music_prompt": "Suno/Udio 호환 프롬프트",
                "video_uri": "generated_video.mp4",
            },
            "tags": ["레퍼런스", "시네마틱", "사운드", "6단계"],
            "category": "creative",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },
        {
            "title": "미학 중심 비주얼 워크플로우",
            "description": "AI DNA → 미학 디렉터 → 시나리오 → 스토리보드 → 프롬프트 → 비주얼. 감독 스타일 기반 비주얼 생성.",
            "thumbnail_url": "/images/portfolio_brand.png",
            "dimension_source": "AI",
            "tool_sequence": ["AI", "AD", "STORY", "2D", "1D", "3D"],
            "input_preset": {
                "depth": "deep",
                "reference_style": "bong",
                "mood": "atmospheric",
                "target_medium": "video",
            },
            "output_example": {
                "visual_guidelines": "봉준호 스타일 가이드",
                "color_palette": ["#2D3436", "#636E72", "#B2BEC3"],
                "image_prompts": ["Scene 1 prompt", "Scene 2 prompt"],
            },
            "tags": ["미학", "감독스타일", "비주얼", "6단계"],
            "category": "creative",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },

        # =============================================================================
        # 프로덕션 워크플로우 (5연결)
        # =============================================================================
        {
            "title": "프로덕션 풀스택",
            "description": "시나리오 → 스토리보드 → 사운드 → 비주얼 → 영상 → 품질검수. 전문 프로덕션 5단계 워크플로우.",
            "thumbnail_url": "/images/portfolio_production.png",
            "dimension_source": "STORY",
            "tool_sequence": ["STORY", "2D", "SOUND", "VEO", "QC"],
            "input_preset": {
                "genre": "drama",
                "duration": "60s",
                "structure": "3act",
                "sound_type": "full",
            },
            "output_example": {
                "story_structure": {"acts": 3, "scenes": 6},
                "sound_design": {"bgm": True, "sfx": True},
                "quality_score": 92,
            },
            "tags": ["프로덕션", "5단계", "풀스택", "전문가"],
            "category": "production",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },
        {
            "title": "비주얼 중심 프로덕션",
            "description": "시나리오 → 스토리보드 → 프롬프트 → 비주얼 → 영상. 이미지 품질에 집중한 5단계 워크플로우.",
            "thumbnail_url": "/images/portfolio_character.png",
            "dimension_source": "STORY",
            "tool_sequence": ["STORY", "2D", "1D", "3D", "VEO"],
            "input_preset": {
                "genre": "ad",
                "style": "photorealistic",
                "duration": "30s",
            },
            "output_example": {
                "image_count": 6,
                "video_duration": "8s",
                "visual_quality": "high",
            },
            "tags": ["비주얼", "이미지", "광고", "5단계"],
            "category": "advertising",
            "creator_name": "Crebit Studio",
            "is_featured": False,
            "is_approved": True,
        },

        # =============================================================================
        # 광고/마케팅 워크플로우 (4연결)
        # =============================================================================
        {
            "title": "광고 제작 파이프라인",
            "description": "시나리오 → 스토리보드 → 프롬프트 → 영상. 광고 대행사 스타일 4단계 워크플로우.",
            "thumbnail_url": "/images/portfolio_ad.png",
            "dimension_source": "STORY",
            "tool_sequence": ["STORY", "2D", "1D", "VEO"],
            "input_preset": {
                "genre": "ad",
                "duration": "15s",
                "mood": "uplifting",
                "target_audience": "2030",
            },
            "output_example": {
                "key_message": "당신의 일상을 특별하게",
                "cta": "지금 시작하세요",
                "video_duration": "8s",
            },
            "tags": ["광고", "마케팅", "브랜딩", "4단계"],
            "category": "advertising",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },
        {
            "title": "제품 소개 영상",
            "description": "스토리보드 → 프롬프트 → 비주얼 → 품질검수. SNS 광고 최적화 4단계 워크플로우.",
            "thumbnail_url": "/images/portfolio_product.png",
            "dimension_source": "2D",
            "tool_sequence": ["2D", "1D", "3D", "QC"],
            "input_preset": {
                "style": "minimal",
                "mood": "professional",
                "aspect_ratio": "9:16",
            },
            "output_example": {
                "hook": "3초 내 시선 집중",
                "benefit_points": 3,
                "quality_score": 88,
            },
            "tags": ["제품", "SNS", "숏폼", "광고"],
            "category": "advertising",
            "creator_name": "Crebit Studio",
            "is_featured": False,
            "is_approved": True,
        },

        # =============================================================================
        # 숏폼 콘텐츠 워크플로우 (4연결)
        # =============================================================================
        {
            "title": "숏폼 콘텐츠 메이커",
            "description": "스토리보드 → 사운드 → 영상 → 품질검수. 틱톡/릴스 최적화 4단계 숏폼 워크플로우.",
            "thumbnail_url": "/images/portfolio_shortform.png",
            "dimension_source": "2D",
            "tool_sequence": ["2D", "SOUND", "VEO", "QC"],
            "input_preset": {
                "style": "dynamic",
                "mood": "energetic",
                "duration": "60s",
                "aspect_ratio": "9:16",
                "sound_type": "bgm",
            },
            "output_example": {
                "hook_duration": "3s",
                "music_prompt": "Upbeat electronic, 120 BPM",
                "quality_score": 90,
            },
            "tags": ["숏폼", "틱톡", "릴스", "사운드"],
            "category": "shortform",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },
        {
            "title": "바이럴 비주얼 숏폼",
            "description": "스토리보드 → 프롬프트 → 비주얼 → 영상. 알고리즘 최적화 비주얼 중심 숏폼.",
            "thumbnail_url": "/images/portfolio_viral.png",
            "dimension_source": "2D",
            "tool_sequence": ["2D", "1D", "3D", "VEO"],
            "input_preset": {
                "style": "trendy",
                "mood": "exciting",
                "duration": "30s",
                "aspect_ratio": "9:16",
            },
            "output_example": {
                "hook_type": "curiosity_gap",
                "image_style": "vibrant",
                "video_duration": "8s",
            },
            "tags": ["바이럴", "트렌드", "비주얼", "숏폼"],
            "category": "shortform",
            "creator_name": "Crebit Studio",
            "is_featured": False,
            "is_approved": True,
        },

        # =============================================================================
        # 뮤직비디오/사운드 워크플로우 (4연결)
        # =============================================================================
        {
            "title": "뮤직비디오 사운드 디자인",
            "description": "시나리오 → 스토리보드 → 사운드 → 영상. Suno/Udio 호환 BGM 프롬프트 생성.",
            "thumbnail_url": "/images/portfolio_sound.png",
            "dimension_source": "STORY",
            "tool_sequence": ["STORY", "2D", "SOUND", "VEO"],
            "input_preset": {
                "genre": "mv",
                "sound_type": "bgm",
                "tempo": "dynamic",
                "target_platform": "suno",
            },
            "output_example": {
                "music_prompt": "Cinematic orchestral, building tension, 120 BPM",
                "style_tags": ["epic", "emotional", "crescendo"],
                "sfx_cues": 8,
            },
            "tags": ["뮤직비디오", "사운드", "BGM", "Suno"],
            "category": "creative",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },
        {
            "title": "내레이션 다큐 스타일",
            "description": "시나리오 → 스토리보드 → 내레이션 사운드 → 영상. ElevenLabs 호환 내레이션 스크립트 생성.",
            "thumbnail_url": "/images/portfolio_docu.png",
            "dimension_source": "STORY",
            "tool_sequence": ["STORY", "2D", "SOUND", "VEO"],
            "input_preset": {
                "genre": "documentary",
                "sound_type": "narration",
                "mood": "authentic",
                "target_platform": "elevenlabs",
            },
            "output_example": {
                "narration_script": "내레이션 스크립트...",
                "voice_direction": {"tone": "warm", "pace": "moderate"},
                "video_duration": "8s",
            },
            "tags": ["다큐멘터리", "내레이션", "스토리텔링", "ElevenLabs"],
            "category": "creative",
            "creator_name": "Crebit Studio",
            "is_featured": False,
            "is_approved": True,
        },

        # =============================================================================
        # 교육/설명 콘텐츠 워크플로우 (3연결)
        # =============================================================================
        {
            "title": "교육 콘텐츠 메이커",
            "description": "스토리보드 → 프롬프트 → 품질검수. 인포그래픽 스타일 교육 콘텐츠 3단계 워크플로우.",
            "thumbnail_url": "/images/portfolio_edu.png",
            "dimension_source": "2D",
            "tool_sequence": ["2D", "1D", "QC"],
            "input_preset": {
                "style": "infographic",
                "mood": "informative",
                "structure": "problem_solution",
            },
            "output_example": {
                "sections": ["문제 제기", "핵심 개념", "적용 방법", "요약"],
                "quality_score": 85,
            },
            "tags": ["교육", "인포그래픽", "설명", "3단계"],
            "category": "education",
            "creator_name": "Crebit Studio",
            "is_featured": False,
            "is_approved": True,
        },

        # =============================================================================
        # 기획 단계 워크플로우 (3연결)
        # =============================================================================
        {
            "title": "시나리오 중심 기획",
            "description": "DNA 분석 → 시나리오 → 스토리보드. 창작 기획의 기초를 다지는 3단계 워크플로우.",
            "thumbnail_url": "/images/portfolio_scenario.png",
            "dimension_source": "AI",
            "tool_sequence": ["AI", "STORY", "2D"],
            "input_preset": {
                "depth": "deep",
                "genre": "drama",
                "structure": "3act",
            },
            "output_example": {
                "archetype": "영웅의 여정",
                "logline": "한 문장으로 정리된 스토리",
                "scenes": 6,
            },
            "tags": ["시나리오", "기획", "DNA분석", "3단계"],
            "category": "production",
            "creator_name": "Crebit Studio",
            "is_featured": False,
            "is_approved": True,
        },
        {
            "title": "레퍼런스 분석 기획",
            "description": "레퍼런스 분석 → 시나리오 → 스토리보드. 참고 영상 기반 기획 3단계 워크플로우.",
            "thumbnail_url": "/images/portfolio_brand.png",
            "dimension_source": "4D",
            "tool_sequence": ["4D", "STORY", "2D"],
            "input_preset": {
                "analysis_focus": ["color", "lighting", "pacing"],
                "genre": "cinematic",
            },
            "output_example": {
                "visual_style": "참조 영상 스타일 분석",
                "story_structure": {"acts": 3},
                "scenes": 6,
            },
            "tags": ["레퍼런스", "분석", "기획", "3단계"],
            "category": "production",
            "creator_name": "Crebit Studio",
            "is_featured": False,
            "is_approved": True,
        },

        # =============================================================================
        # 추가 워크플로우 - 직관적 이름
        # =============================================================================
        {
            "title": "감독 스타일 뮤비",
            "description": "나의 창작 DNA + 거장 감독 스타일 + BGM까지. 봉준호/박찬욱 등 6인 감독 스타일로 뮤직비디오 완성.",
            "thumbnail_url": "/images/portfolio_mv.png",
            "dimension_source": "AI",
            "tool_sequence": ["AI", "AD", "STORY", "2D", "SOUND", "VEO"],
            "input_preset": {
                "depth": "deep",
                "reference_style": "bong",
                "sound_type": "bgm",
                "genre": "cinematic",
            },
            "output_example": {
                "auteur_style": "봉준호 - 긴장감 있는 미장센",
                "music_prompt": "Suno/Udio 호환 프롬프트",
                "video_uri": "generated_video.mp4",
            },
            "tags": ["감독스타일", "뮤직비디오", "사운드", "6단계"],
            "category": "creative",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },
        {
            "title": "3분 완성 영상",
            "description": "스토리보드만 있으면 끝! 프롬프트 생성부터 영상까지 초고속 3단계 워크플로우.",
            "thumbnail_url": "/images/portfolio_shortform.png",
            "dimension_source": "2D",
            "tool_sequence": ["2D", "1D", "VEO"],
            "input_preset": {
                "style": "dynamic",
                "duration": "30s",
                "aspect_ratio": "16:9",
            },
            "output_example": {
                "prompt": "최적화된 Veo 프롬프트",
                "video_duration": "8s",
            },
            "tags": ["초스피드", "간편", "영상", "3단계"],
            "category": "shortform",
            "creator_name": "Crebit Studio",
            "is_featured": True,
            "is_approved": True,
        },
        {
            "title": "참고영상 완벽 재현",
            "description": "좋아하는 영상 스타일 그대로! 레퍼런스 분석 → 고품질 이미지 → 영상 생성까지.",
            "thumbnail_url": "/images/portfolio_brand.png",
            "dimension_source": "4D",
            "tool_sequence": ["4D", "STORY", "2D", "1D", "3D", "VEO"],
            "input_preset": {
                "analysis_focus": ["color", "lighting", "pacing", "composition"],
                "style": "photorealistic",
            },
            "output_example": {
                "reference_analysis": "완벽한 스타일 분석",
                "image_count": 6,
                "video_uri": "generated_video.mp4",
            },
            "tags": ["레퍼런스", "재현", "비주얼", "6단계"],
            "category": "creative",
            "creator_name": "Crebit Studio",
            "is_featured": False,
            "is_approved": True,
        },
        {
            "title": "출시 전 품질검수",
            "description": "영상 만들기 전에 먼저 검증! 시나리오 → 스토리보드 → 프롬프트 → AI 에디터 피드백.",
            "thumbnail_url": "/images/portfolio_edu.png",
            "dimension_source": "STORY",
            "tool_sequence": ["STORY", "2D", "1D", "QC"],
            "input_preset": {
                "genre": "drama",
                "persona": "Senior Editor",
                "use_rag": True,
            },
            "output_example": {
                "quality_score": 88,
                "critique": {"narrative": 90, "visual": 85, "pacing": 88},
                "improvements": ["더 강한 오프닝 훅 필요", "3막 전환 보강"],
            },
            "tags": ["품질검수", "피드백", "에디터", "4단계"],
            "category": "production",
            "creator_name": "Crebit Studio",
            "is_featured": False,
            "is_approved": True,
        },
    ]
    
    created = []
    updated = []
    
    for data in seed_data:
        # Check if already exists
        existing = await db.execute(
            select(BlackholeTemplate).where(BlackholeTemplate.title == data["title"])
        )
        template = existing.scalar_one_or_none()
        
        if template:
            # Update existing
            template.description = data["description"]
            template.thumbnail_url = data["thumbnail_url"]
            template.dimension_source = data["dimension_source"]
            template.tool_sequence = data["tool_sequence"]
            template.input_preset = data.get("input_preset", {})
            template.output_example = data.get("output_example", {})
            template.tags = data["tags"]
            template.category = data["category"]
            template.is_featured = data["is_featured"]
            updated.append(data["title"])
        else:
            # Create new
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
        "updated": updated,
        "count": len(created) + len(updated),
    }
