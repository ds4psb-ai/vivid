"""Template catalog endpoints."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_user_id
from app.config import settings
from app.database import get_db
from app.models import Template, TemplateVersion
from app.seed import seed_auteur_data

router = APIRouter()


class TemplateCreate(BaseModel):
    slug: str
    title: str
    description: str
    tags: List[str] = []
    graph_data: dict
    is_public: bool = True
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
    notes: Optional[str] = None


class TemplateResponse(BaseModel):
    id: str
    slug: str
    title: str
    description: str
    tags: List[str]
    graph_data: dict
    is_public: bool
    creator_id: Optional[str]
    version: int

    class Config:
        from_attributes = True


def _to_response(template: Template) -> TemplateResponse:
    return TemplateResponse(
        id=str(template.id),
        slug=template.slug,
        title=template.title,
        description=template.description,
        tags=template.tags,
        graph_data=template.graph_data,
        is_public=template.is_public,
        creator_id=template.creator_id,
        version=template.version,
    )


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
    template = Template(
        slug=data.slug,
        title=data.title,
        description=data.description,
        tags=data.tags,
        graph_data=data.graph_data,
        is_public=data.is_public,
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
        template.graph_data = data.graph_data
        graph_changed = True
    if data.is_public is not None:
        template.is_public = data.is_public

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
