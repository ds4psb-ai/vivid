"""IP Catalog API router for IP-First UX.

Provides endpoints for:
- IP catalog browsing and search
- IP detail with presets
- IP workflow preset management
- Home rail data
"""

import json
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_, desc, asc, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_user_id, get_user_id
from app.models_ip import IPCatalog, IPWorkflowPreset, IPRights, IPGeneration
from app.redis_client import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ip"])


# --- Pydantic Schemas ---

class IPCatalogItem(BaseModel):
    """IP Catalog item for list views."""
    id: str
    slug: str
    name_ko: str
    name_en: str
    thumbnail_url: Optional[str] = None
    genre: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    preset_count: int = 0
    generation_count: int = 0
    license_status: str = "allowed"
    is_featured: bool = False

    model_config = {"from_attributes": True}


class IPCatalogListResponse(BaseModel):
    """Response for IP catalog list."""
    items: list[IPCatalogItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class PresetItem(BaseModel):
    """Workflow preset item."""
    id: str
    name_ko: str
    name_en: str
    description_ko: Optional[str] = None
    description_en: Optional[str] = None
    thumbnail_url: Optional[str] = None
    preset_type: str
    estimated_credits: int
    estimated_duration_seconds: int
    is_featured: bool = False

    model_config = {"from_attributes": True}


class IPDetailResponse(BaseModel):
    """Full IP detail with presets."""
    id: str
    slug: str
    name_ko: str
    name_en: str
    description_ko: Optional[str] = None
    description_en: Optional[str] = None
    thumbnail_url: Optional[str] = None
    banner_url: Optional[str] = None
    genre: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    worldbuilding: dict = Field(default_factory=dict)
    license_status: str = "allowed"
    preset_count: int = 0
    generation_count: int = 0
    presets: list[PresetItem] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class RailItem(BaseModel):
    """Item for home rail display."""
    id: str
    slug: str
    name_ko: str
    name_en: str
    thumbnail_url: Optional[str] = None
    license_status: str = "allowed"
    preset_count: int = 0


class HomeRailSection(BaseModel):
    """Section for home rail."""
    section_id: str
    title_ko: str
    title_en: str
    items: list[RailItem]
    has_more: bool = False


class HomeRailResponse(BaseModel):
    """Response for home rails."""
    sections: list[HomeRailSection]


# --- API Endpoints ---

@router.get("/home/rails", response_model=HomeRailResponse)
async def get_home_rails(
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_user_id),
):
    """Get home page rails (popular IPs, new presets, etc.).

    Optimized: Single query + Python grouping instead of 5+ separate queries.
    Before: 5+ queries (featured + new + 3 genres), After: 1 query
    """
    # Single query: fetch all active IPs we might need
    # Sort by generation_count to prioritize popular ones
    all_result = await db.execute(
        select(IPCatalog)
        .where(IPCatalog.is_active == True)
        .order_by(desc(IPCatalog.generation_count))
        .limit(100)  # Enough for all rails
    )
    all_ips = all_result.scalars().all()

    # Python-side classification
    sections = []

    # Helper to convert IP to RailItem
    def to_rail_item(ip: IPCatalog) -> RailItem:
        return RailItem(
            id=str(ip.id),
            slug=ip.slug,
            name_ko=ip.name_ko,
            name_en=ip.name_en,
            thumbnail_url=ip.thumbnail_url,
            license_status=ip.license_status,
            preset_count=ip.preset_count,
        )

    # Section 1: Featured/Popular IPs (sorted by featured_order)
    featured_ips = sorted(
        [ip for ip in all_ips if ip.is_featured],
        key=lambda x: x.featured_order or 999
    )[:10]
    if featured_ips:
        sections.append(HomeRailSection(
            section_id="featured",
            title_ko="인기 IP",
            title_en="Popular IPs",
            items=[to_rail_item(ip) for ip in featured_ips],
            has_more=len(featured_ips) >= 10,
        ))

    # Section 2: Newly Added IPs (sorted by created_at)
    new_ips = sorted(all_ips, key=lambda x: x.created_at, reverse=True)[:10]
    if new_ips:
        sections.append(HomeRailSection(
            section_id="new",
            title_ko="새로운 IP",
            title_en="New IPs",
            items=[to_rail_item(ip) for ip in new_ips],
            has_more=len(new_ips) >= 10,
        ))

    # Section 3: Genre-based sections (already sorted by generation_count from query)
    genre_sections = [
        ("kdrama", "K-드라마", "K-Drama"),
        ("movie", "영화", "Movies"),
        ("anime", "애니메이션", "Anime"),
    ]
    for genre_key, title_ko, title_en in genre_sections:
        genre_ips = [
            ip for ip in all_ips
            if ip.genre and genre_key in ip.genre
        ][:10]
        if genre_ips:
            sections.append(HomeRailSection(
                section_id=f"genre_{genre_key}",
                title_ko=title_ko,
                title_en=title_en,
                items=[to_rail_item(ip) for ip in genre_ips],
                has_more=len(genre_ips) >= 10,
            ))

    return HomeRailResponse(sections=sections)


@router.get("/catalog", response_model=IPCatalogListResponse)
async def list_ip_catalog(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    search: Optional[str] = Query(None, description="Search by name"),
    license_status: Optional[str] = Query(None, description="Filter by license status"),
    sort_by: str = Query("popular", description="Sort: popular, new, name"),
):
    """List IP catalog with filtering and pagination."""
    query = select(IPCatalog).where(IPCatalog.is_active == True)

    # Apply filters
    if genre:
        query = query.where(IPCatalog.genre.contains([genre]))
    if license_status:
        query = query.where(IPCatalog.license_status == license_status)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                IPCatalog.name_ko.ilike(search_pattern),
                IPCatalog.name_en.ilike(search_pattern),
            )
        )

    # Sorting
    if sort_by == "popular":
        query = query.order_by(desc(IPCatalog.generation_count))
    elif sort_by == "new":
        query = query.order_by(desc(IPCatalog.created_at))
    elif sort_by == "name":
        query = query.order_by(asc(IPCatalog.name_ko))
    else:
        query = query.order_by(desc(IPCatalog.generation_count))

    # Single query with window function for count + pagination
    # Before: 2 queries (count + select), After: 1 query
    offset = (page - 1) * page_size
    query_with_count = query.add_columns(
        func.count().over().label("total_count")
    ).offset(offset).limit(page_size)

    result = await db.execute(query_with_count)
    rows = result.all()

    # Extract items and total count
    items = [row[0] for row in rows]
    total = rows[0].total_count if rows else 0

    return IPCatalogListResponse(
        items=[
            IPCatalogItem(
                id=str(item.id),
                slug=item.slug,
                name_ko=item.name_ko,
                name_en=item.name_en,
                thumbnail_url=item.thumbnail_url,
                genre=item.genre or [],
                tags=item.tags or [],
                preset_count=item.preset_count,
                generation_count=item.generation_count,
                license_status=item.license_status,
                is_featured=item.is_featured,
            )
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(items)) < total,
    )


@router.get("/catalog/{slug}", response_model=IPDetailResponse)
async def get_ip_detail(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get full IP detail with presets."""
    # Get IP
    result = await db.execute(
        select(IPCatalog)
        .where(IPCatalog.slug == slug)
        .where(IPCatalog.is_active == True)
    )
    ip = result.scalar_one_or_none()

    if not ip:
        raise HTTPException(status_code=404, detail="IP not found")

    # Get presets
    presets_result = await db.execute(
        select(IPWorkflowPreset)
        .where(IPWorkflowPreset.ip_id == ip.id)
        .where(IPWorkflowPreset.is_active == True)
        .order_by(asc(IPWorkflowPreset.sort_order))
    )
    presets = presets_result.scalars().all()

    return IPDetailResponse(
        id=str(ip.id),
        slug=ip.slug,
        name_ko=ip.name_ko,
        name_en=ip.name_en,
        description_ko=ip.description_ko,
        description_en=ip.description_en,
        thumbnail_url=ip.thumbnail_url,
        banner_url=ip.banner_url,
        genre=ip.genre or [],
        tags=ip.tags or [],
        worldbuilding=ip.worldbuilding or {},
        license_status=ip.license_status,
        preset_count=ip.preset_count,
        generation_count=ip.generation_count,
        presets=[
            PresetItem(
                id=str(preset.id),
                name_ko=preset.name_ko,
                name_en=preset.name_en,
                description_ko=preset.description_ko,
                description_en=preset.description_en,
                thumbnail_url=preset.thumbnail_url,
                preset_type=preset.preset_type,
                estimated_credits=preset.estimated_credits,
                estimated_duration_seconds=preset.estimated_duration_seconds,
                is_featured=preset.is_featured,
            )
            for preset in presets
        ],
    )


@router.get("/catalog/{slug}/rights")
async def get_ip_rights(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get IP rights information for license gating."""
    # Get IP
    result = await db.execute(
        select(IPCatalog)
        .where(IPCatalog.slug == slug)
    )
    ip = result.scalar_one_or_none()

    if not ip:
        raise HTTPException(status_code=404, detail="IP not found")

    # Get rights
    rights_result = await db.execute(
        select(IPRights)
        .where(IPRights.ip_id == ip.id)
    )
    rights = rights_result.scalar_one_or_none()

    if not rights:
        # Return default rights if not configured
        return {
            "license_status": ip.license_status,
            "territory": [],
            "blocked_territory": [],
            "scope": "fan_creation",
            "commercial_ok": False,
        }

    return {
        "license_status": rights.license_status,
        "territory": rights.territory or [],
        "blocked_territory": rights.blocked_territory or [],
        "scope": rights.scope,
        "commercial_ok": rights.commercial_ok,
        "expiry": rights.expiry.isoformat() if rights.expiry else None,
    }


@router.get("/presets/{preset_id}")
async def get_preset_detail(
    preset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get preset detail (for generation)."""
    result = await db.execute(
        select(IPWorkflowPreset)
        .where(IPWorkflowPreset.id == preset_id)
        .where(IPWorkflowPreset.is_active == True)
    )
    preset = result.scalar_one_or_none()

    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    return {
        "id": str(preset.id),
        "ip_id": str(preset.ip_id),
        "name_ko": preset.name_ko,
        "name_en": preset.name_en,
        "description_ko": preset.description_ko,
        "description_en": preset.description_en,
        "preset_type": preset.preset_type,
        "estimated_credits": preset.estimated_credits,
        "estimated_duration_seconds": preset.estimated_duration_seconds,
        # Note: workflow_steps is sealed and not exposed
    }


@router.get("/genres")
async def list_genres(
    db: AsyncSession = Depends(get_db),
):
    """List available genres with counts.

    Optimized:
    - Redis cache with 1 hour TTL (genre counts rarely change)
    - Single query with unnest instead of N+1 queries

    Reference: 2026 PostgreSQL best practice for JSONB array aggregation.
    """
    CACHE_KEY = "ip:genres:list"
    CACHE_TTL = 3600  # 1 hour

    # Try cache first
    try:
        redis = get_redis_client()
        cached = await redis.get(CACHE_KEY)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Redis cache read failed: {e}")

    # Genre definitions
    GENRE_DEFINITIONS = [
        {"key": "kdrama", "label_ko": "K-드라마", "label_en": "K-Drama"},
        {"key": "movie", "label_ko": "영화", "label_en": "Movie"},
        {"key": "anime", "label_ko": "애니메이션", "label_en": "Anime"},
        {"key": "fantasy", "label_ko": "판타지", "label_en": "Fantasy"},
        {"key": "romance", "label_ko": "로맨스", "label_en": "Romance"},
        {"key": "action", "label_ko": "액션", "label_en": "Action"},
        {"key": "thriller", "label_ko": "스릴러", "label_en": "Thriller"},
        {"key": "scifi", "label_ko": "SF", "label_en": "Sci-Fi"},
    ]

    # Single query: unnest genre array and count all genres at once
    genre_counts_result = await db.execute(
        select(
            func.unnest(IPCatalog.genre).label("genre_key"),
            func.count().label("count"),
        )
        .where(IPCatalog.is_active == True)
        .group_by(text("genre_key"))
    )
    count_map = {row.genre_key: row.count for row in genre_counts_result}

    # Merge with genre definitions
    genres = [
        {
            **genre_def,
            "count": count_map.get(genre_def["key"], 0),
        }
        for genre_def in GENRE_DEFINITIONS
    ]

    result = {"genres": genres}

    # Cache result
    try:
        await redis.set(CACHE_KEY, json.dumps(result), ex=CACHE_TTL)
    except Exception as e:
        logger.warning(f"Redis cache write failed: {e}")

    return result


class PopularIPItem(BaseModel):
    """Popular IP item for generateStaticParams."""
    id: str
    slug: str
    name_ko: str
    name_en: str


@router.get("/popular", response_model=list[PopularIPItem])
async def get_popular_ips(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100, description="Max number of IPs to return"),
):
    """Get popular IPs for static generation.

    Used by Next.js generateStaticParams to pre-render popular IP pages at build time.
    Returns IPs sorted by generation count (popularity).

    Phase 6: ISR + generateStaticParams integration
    """
    result = await db.execute(
        select(IPCatalog)
        .where(IPCatalog.is_active == True)
        .order_by(
            desc(IPCatalog.is_featured),  # Featured first
            desc(IPCatalog.generation_count),  # Then by popularity
        )
        .limit(limit)
    )
    ips = result.scalars().all()

    return [
        PopularIPItem(
            id=str(ip.id),
            slug=ip.slug,
            name_ko=ip.name_ko,
            name_en=ip.name_en,
        )
        for ip in ips
    ]
