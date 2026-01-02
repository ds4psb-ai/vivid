"""Canvas CRUD endpoints."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_user_id
from app.database import get_db
from app.models import Canvas, Template
from app.graph_utils import merge_graph_meta, ensure_pattern_version
from app.patterns import get_latest_pattern_version

router = APIRouter()

MAX_GRAPH_DATA_BYTES = 1024 * 1024  # 1MB
MAX_NODES = 120
MAX_EDGES = 240


class CanvasCreate(BaseModel):
    title: str
    graph_data: dict
    is_public: bool = False
    owner_id: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        if not value or len(value.strip()) < 1:
            raise ValueError("Title cannot be empty")
        if len(value) > 120:
            raise ValueError("Title must be 120 characters or less")
        return value.strip()

    @field_validator("graph_data")
    @classmethod
    def validate_graph_data(cls, value: dict) -> dict:
        if not isinstance(value, dict):
            raise ValueError("graph_data must be a dictionary")
        if "nodes" not in value or "edges" not in value:
            raise ValueError("graph_data must include nodes and edges")
        if not isinstance(value.get("nodes"), list):
            raise ValueError("nodes must be a list")
        if not isinstance(value.get("edges"), list):
            raise ValueError("edges must be a list")
        if len(value.get("nodes", [])) > MAX_NODES:
            raise ValueError(f"Maximum {MAX_NODES} nodes allowed")
        if len(value.get("edges", [])) > MAX_EDGES:
            raise ValueError(f"Maximum {MAX_EDGES} edges allowed")
        if len(json.dumps(value)) > MAX_GRAPH_DATA_BYTES:
            raise ValueError("graph_data exceeds size limit")
        return value


class CanvasUpdate(BaseModel):
    title: Optional[str] = None
    graph_data: Optional[dict] = None
    is_public: Optional[bool] = None
    owner_id: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if len(value.strip()) < 1:
            raise ValueError("Title cannot be empty")
        if len(value) > 120:
            raise ValueError("Title must be 120 characters or less")
        return value.strip()

    @field_validator("graph_data")
    @classmethod
    def validate_graph_data(cls, value: Optional[dict]) -> Optional[dict]:
        if value is None:
            return value
        if not isinstance(value, dict):
            raise ValueError("graph_data must be a dictionary")
        if "nodes" not in value or "edges" not in value:
            raise ValueError("graph_data must include nodes and edges")
        if len(value.get("nodes", [])) > MAX_NODES:
            raise ValueError(f"Maximum {MAX_NODES} nodes allowed")
        if len(value.get("edges", [])) > MAX_EDGES:
            raise ValueError(f"Maximum {MAX_EDGES} edges allowed")
        if len(json.dumps(value)) > MAX_GRAPH_DATA_BYTES:
            raise ValueError("graph_data exceeds size limit")
        return value


class CanvasResponse(BaseModel):
    id: str
    title: str
    graph_data: dict
    is_public: bool
    version: int
    owner_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CanvasFromTemplate(BaseModel):
    template_id: str
    title: Optional[str] = None
    is_public: bool = False
    owner_id: Optional[str] = None


def _validate_uuid(canvas_id: str) -> UUID:
    try:
        return UUID(canvas_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid canvas ID format")


def _to_response(canvas: Canvas) -> CanvasResponse:
    return CanvasResponse(
        id=str(canvas.id),
        title=canvas.title,
        graph_data=canvas.graph_data,
        is_public=canvas.is_public,
        version=canvas.version,
        owner_id=canvas.owner_id,
        created_at=canvas.created_at,
        updated_at=canvas.updated_at,
    )


def _ensure_graph_meta_defaults(graph_data: dict) -> dict:
    if not isinstance(graph_data, dict):
        return graph_data
    meta = graph_data.get("meta")
    if not isinstance(meta, dict):
        meta = {}
    updated = False

    if "guide_sources" not in meta or not isinstance(meta.get("guide_sources"), list):
        meta["guide_sources"] = []
        updated = True
    if "evidence_refs" not in meta or not isinstance(meta.get("evidence_refs"), list):
        meta["evidence_refs"] = []
        updated = True

    narrative = meta.get("narrative_seeds")
    if not isinstance(narrative, dict):
        narrative = {}
    if "story_beats" not in narrative or not isinstance(narrative.get("story_beats"), list):
        narrative["story_beats"] = []
        updated = True
    if "storyboard_cards" not in narrative or not isinstance(narrative.get("storyboard_cards"), list):
        narrative["storyboard_cards"] = []
        updated = True
    meta["narrative_seeds"] = narrative

    production = meta.get("production_contract")
    if not isinstance(production, dict):
        production = {}
    if "shot_contracts" not in production or not isinstance(production.get("shot_contracts"), list):
        production["shot_contracts"] = []
        updated = True
    if "prompt_contract_version" not in production or not isinstance(
        production.get("prompt_contract_version"), str
    ):
        production["prompt_contract_version"] = "v1"
        updated = True
    if "storyboard_refs" not in production or not isinstance(production.get("storyboard_refs"), list):
        production["storyboard_refs"] = []
        updated = True
    meta["production_contract"] = production

    if not updated and graph_data.get("meta") is meta:
        return graph_data
    return {**graph_data, "meta": meta}


def _apply_template_origin(graph_data: dict, template: Template) -> dict:
    if not isinstance(graph_data, dict):
        return graph_data
    meta = graph_data.get("meta")
    if not isinstance(meta, dict):
        meta = {}
    origin = meta.get("template_origin")
    if not isinstance(origin, dict):
        origin = {}
    origin["template_id"] = str(template.id)
    origin["template_version"] = int(template.version or 1)
    origin["template_slug"] = template.slug
    meta["template_origin"] = origin
    return {**graph_data, "meta": meta}


@router.post("/", response_model=CanvasResponse, status_code=status.HTTP_201_CREATED)
async def create_canvas(
    data: CanvasCreate,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> CanvasResponse:
    pattern_version = await get_latest_pattern_version(db)
    canvas = Canvas(
        title=data.title,
        graph_data=_ensure_graph_meta_defaults(
            ensure_pattern_version(data.graph_data, pattern_version)
        ),
        is_public=data.is_public,
        owner_id=data.owner_id or user_id,
    )
    db.add(canvas)
    await db.commit()
    await db.refresh(canvas)
    return _to_response(canvas)


@router.post("/from-template", response_model=CanvasResponse, status_code=status.HTTP_201_CREATED)
async def create_canvas_from_template(
    data: CanvasFromTemplate,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> CanvasResponse:
    try:
        template_uuid = UUID(data.template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    result = await db.execute(select(Template).where(Template.id == template_uuid))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if not template.is_public and (not user_id or template.creator_id != user_id):
        raise HTTPException(status_code=403, detail="Not authorized to use this template")

    title = data.title or f"{template.title} (Copy)"
    pattern_version = await get_latest_pattern_version(db)
    canvas = Canvas(
        title=title,
        graph_data=_apply_template_origin(
            _ensure_graph_meta_defaults(
                ensure_pattern_version(template.graph_data or {}, pattern_version)
            ),
            template,
        ),
        is_public=data.is_public,
        owner_id=data.owner_id or user_id,
    )
    db.add(canvas)
    await db.commit()
    await db.refresh(canvas)
    return _to_response(canvas)


@router.get("/", response_model=List[CanvasResponse])
async def list_canvases(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[CanvasResponse]:
    query = select(Canvas).order_by(Canvas.updated_at.desc()).offset(skip).limit(limit)
    if user_id:
        query = query.where(
            or_(
                Canvas.is_public.is_(True),
                Canvas.owner_id == user_id,
                Canvas.owner_id.is_(None),
            )
        )
    else:
        query = query.where(or_(Canvas.is_public.is_(True), Canvas.owner_id.is_(None)))
    result = await db.execute(query)
    return [_to_response(canvas) for canvas in result.scalars().all()]


@router.get("/{canvas_id}", response_model=CanvasResponse)
async def get_canvas(
    canvas_id: str,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> CanvasResponse:
    canvas_uuid = _validate_uuid(canvas_id)
    result = await db.execute(select(Canvas).where(Canvas.id == canvas_uuid))
    canvas = result.scalar_one_or_none()
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    if not canvas.is_public and canvas.owner_id is not None:
        if not user_id or canvas.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this canvas")
    return _to_response(canvas)


@router.patch("/{canvas_id}", response_model=CanvasResponse)
async def update_canvas(
    canvas_id: str,
    data: CanvasUpdate,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> CanvasResponse:
    canvas_uuid = _validate_uuid(canvas_id)
    result = await db.execute(select(Canvas).where(Canvas.id == canvas_uuid))
    canvas = result.scalar_one_or_none()
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    if not canvas.is_public and canvas.owner_id is not None:
        if not user_id or canvas.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this canvas")

    version_bump = False
    if data.title is not None:
        canvas.title = data.title
        version_bump = True
    if data.graph_data is not None:
        pattern_version = await get_latest_pattern_version(db)
        merged_graph = merge_graph_meta(data.graph_data, canvas.graph_data or {})
        canvas.graph_data = _ensure_graph_meta_defaults(
            ensure_pattern_version(merged_graph, pattern_version)
        )
        version_bump = True
    if data.is_public is not None:
        canvas.is_public = data.is_public
    if data.owner_id is not None:
        canvas.owner_id = data.owner_id
    if version_bump:
        canvas.version += 1

    await db.commit()
    await db.refresh(canvas)
    return _to_response(canvas)
