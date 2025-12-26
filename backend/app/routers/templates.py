"""Template catalog endpoints."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_is_admin, get_user_id
from app.config import settings
from app.database import get_db
from app.models import Template, TemplateVersion
from app.template_seeding import seed_template_from_evidence
from app.graph_utils import merge_graph_meta
from app.patterns import get_latest_pattern_version
from app.seed import seed_auteur_data

router = APIRouter()


class TemplateCreate(BaseModel):
    slug: str
    title: str
    description: str
    tags: List[str] = []
    graph_data: dict
    is_public: bool = True
    preview_video_url: Optional[str] = None
    creator_id: Optional[str] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        if not value or len(value.strip()) < 3:
            raise ValueError("slug must be at least 3 characters")
        return value.strip()

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        if not value or len(value.strip()) < 1:
            raise ValueError("title cannot be empty")
        return value.strip()


class TemplateUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    graph_data: Optional[dict] = None
    is_public: Optional[bool] = None
    preview_video_url: Optional[str] = None
    notes: Optional[str] = None


class TemplateSeedFromEvidence(BaseModel):
    notebook_id: str
    slug: str
    title: str
    description: Optional[str] = "Seeded template"
    capsule_key: str
    capsule_version: str
    tags: List[str] = []
    is_public: bool = False
    creator_id: Optional[str] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        if not value or len(value.strip()) < 3:
            raise ValueError("slug must be at least 3 characters")
        return value.strip()

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        if not value or len(value.strip()) < 1:
            raise ValueError("title cannot be empty")
        return value.strip()


class TemplateResponse(BaseModel):
    id: str
    slug: str
    title: str
    description: str
    tags: List[str]
    graph_data: dict
    is_public: bool
    preview_video_url: Optional[str]
    creator_id: Optional[str]
    version: int

    model_config = ConfigDict(from_attributes=True)


def _to_response(template: Template) -> TemplateResponse:
    return TemplateResponse(
        id=str(template.id),
        slug=template.slug,
        title=template.title,
        description=template.description,
        tags=template.tags,
        graph_data=template.graph_data,
        is_public=template.is_public,
        preview_video_url=template.preview_video_url,
        creator_id=template.creator_id,
        version=template.version,
    )


def _ensure_pattern_version(graph_data: dict, pattern_version: str) -> dict:
    nodes = graph_data.get("nodes")
    if not isinstance(nodes, list):
        return graph_data
    updated = False
    next_nodes = []
    for node in nodes:
        if not isinstance(node, dict):
            next_nodes.append(node)
            continue
        data = node.get("data")
        if not isinstance(data, dict):
            next_nodes.append(node)
            continue
        if data.get("patternVersion"):
            next_nodes.append(node)
            continue
        if data.get("capsuleId") and data.get("capsuleVersion"):
            patched = {**data, "patternVersion": pattern_version}
            next_nodes.append({**node, "data": patched})
            updated = True
        else:
            next_nodes.append(node)
    if not updated:
        return graph_data
    return {**graph_data, "nodes": next_nodes}



def _has_provenance(graph_data: dict) -> bool:
    if not isinstance(graph_data, dict):
        return False
    meta = graph_data.get("meta")
    if not isinstance(meta, dict):
        return False
    guide_sources = meta.get("guide_sources")
    evidence_refs = meta.get("evidence_refs")
    has_guide_sources = isinstance(guide_sources, list) and len(guide_sources) > 0
    has_evidence_refs = isinstance(evidence_refs, list) and len(evidence_refs) > 0
    return has_guide_sources or has_evidence_refs


class TemplateVersionResponse(BaseModel):
    id: str
    template_id: str
    version: int
    graph_data: dict
    notes: Optional[str]
    creator_id: Optional[str]
    created_at: str


def _to_version_response(version: TemplateVersion) -> TemplateVersionResponse:
    return TemplateVersionResponse(
        id=str(version.id),
        template_id=str(version.template_id),
        version=version.version,
        graph_data=version.graph_data,
        notes=version.notes,
        creator_id=version.creator_id,
        created_at=version.created_at.isoformat(),
    )


@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    public_only: bool = Query(True),
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[TemplateResponse]:
    query = select(Template)
    if public_only:
        query = query.where(Template.is_public.is_(True))
    else:
        if user_id:
            query = query.where(or_(Template.is_public.is_(True), Template.creator_id == user_id))
        else:
            query = query.where(Template.is_public.is_(True))
    result = await db.execute(query.order_by(Template.updated_at.desc()))
    return [_to_response(t) for t in result.scalars().all()]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    try:
        template_uuid = UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    result = await db.execute(select(Template).where(Template.id == template_uuid))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if not template.is_public and (not user_id or template.creator_id != user_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this template")
    return _to_response(template)


@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    pattern_version = await get_latest_pattern_version(db)
    graph_data = _ensure_pattern_version(data.graph_data, pattern_version)
    if data.is_public and not _has_provenance(graph_data):
        raise HTTPException(
            status_code=400,
            detail="Public templates require guide_sources or evidence_refs in graph_data.meta",
        )
    template = Template(
        slug=data.slug,
        title=data.title,
        description=data.description,
        tags=data.tags,
        graph_data=graph_data,
        is_public=data.is_public,
        preview_video_url=data.preview_video_url,
        creator_id=data.creator_id or user_id,
        version=1,
    )
    db.add(template)
    await db.flush()
    db.add(
        TemplateVersion(
            template_id=template.id,
            version=template.version,
            graph_data=template.graph_data,
            notes="initial",
            creator_id=template.creator_id,
        )
    )
    await db.commit()
    await db.refresh(template)
    return _to_response(template)


@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_templates(db: AsyncSession = Depends(get_db)) -> dict:
    if settings.ENVIRONMENT != "development":
        raise HTTPException(status_code=403, detail="Seeding only allowed in development")
    return await seed_auteur_data(db)


@router.post("/seed/from-evidence", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def seed_from_evidence(
    data: TemplateSeedFromEvidence,
    is_admin: bool = Depends(get_is_admin),
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        template = await seed_template_from_evidence(
            db,
            slug=data.slug,
            title=data.title,
            description=data.description or "Seeded template",
            capsule_key=data.capsule_key,
            capsule_version=data.capsule_version,
            notebook_id=data.notebook_id,
            tags=data.tags or None,
            is_public=data.is_public,
            creator_id=data.creator_id or user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(template)


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    data: TemplateUpdate,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    try:
        template_uuid = UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    result = await db.execute(select(Template).where(Template.id == template_uuid))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.creator_id is not None:
        if not user_id or template.creator_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this template")
    elif not user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this template")
    else:
        template.creator_id = user_id

    graph_changed = False
    if data.title is not None:
        template.title = data.title
    if data.description is not None:
        template.description = data.description
    if data.tags is not None:
        template.tags = data.tags
    if data.graph_data is not None:
        pattern_version = await get_latest_pattern_version(db)
        merged_graph = merge_graph_meta(data.graph_data, template.graph_data or {})
        template.graph_data = _ensure_pattern_version(merged_graph, pattern_version)
        graph_changed = True
    if data.is_public is not None:
        template.is_public = data.is_public
    if data.preview_video_url is not None:
        template.preview_video_url = data.preview_video_url

    if graph_changed:
        template.version += 1
        db.add(
            TemplateVersion(
                template_id=template.id,
                version=template.version,
                graph_data=template.graph_data,
                notes=data.notes or "update",
                creator_id=template.creator_id,
            )
        )

    next_is_public = template.is_public
    if (data.is_public is True) or (data.graph_data is not None):
        if next_is_public and not _has_provenance(template.graph_data or {}):
            raise HTTPException(
                status_code=400,
                detail="Public templates require guide_sources or evidence_refs in graph_data.meta",
            )

    await db.commit()
    await db.refresh(template)
    return _to_response(template)


@router.get("/{template_id}/versions", response_model=List[TemplateVersionResponse])
async def list_template_versions(
    template_id: str,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[TemplateVersionResponse]:
    try:
        template_uuid = UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    result = await db.execute(select(Template).where(Template.id == template_uuid))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if not template.is_public and (not user_id or template.creator_id != user_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this template")

    result = await db.execute(
        select(TemplateVersion)
        .where(TemplateVersion.template_id == template_uuid)
        .order_by(TemplateVersion.version.desc())
    )
    versions = result.scalars().all()
    if not versions:
        seed_version = TemplateVersion(
            template_id=template.id,
            version=template.version,
            graph_data=template.graph_data,
            notes="auto-seeded",
            creator_id=template.creator_id,
        )
        db.add(seed_version)
        await db.commit()
        await db.refresh(seed_version)
        versions = [seed_version]
    return [_to_version_response(item) for item in versions]
