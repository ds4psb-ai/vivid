"""Ingestion endpoints for raw assets and derived evidence."""
from __future__ import annotations

from datetime import datetime
import re
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_is_admin
from app.config import settings
from app.database import get_db
from app.models import (
    EvidenceRecord,
    NotebookLibrary,
    NotebookAsset,
    Pattern,
    PatternCandidate,
    PatternTrace,
    PatternVersion,
    RawAsset,
    VideoSegment,
)

router = APIRouter()

_GUIDE_TYPE_ALLOWLIST = {
    "summary",
    "homage",
    "variation",
    "template_fit",
    "persona",
    "synapse",
    "story",
    "beat_sheet",
    "storyboard",
    "study_guide",
    "briefing_doc",
    "table",
}
_GUIDE_SCOPE_ALLOWLIST = {
    "auteur",
    "genre",
    "format",
    "creator",
    "mixed",
}
_OUTPUT_TYPE_ALLOWLIST = {
    "video_overview",
    "audio_overview",
    "mind_map",
    "report",
    "data_table",
}
_PATTERN_TYPE_ALLOWLIST = {
    "hook",
    "scene",
    "subtitle",
    "audio",
    "pacing",
}
_PATTERN_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_RAW_SOURCE_TYPE_ALLOWLIST = {"video", "image", "doc"}
_NOTEBOOK_ASSET_TYPE_ALLOWLIST = {
    "video",
    "image",
    "doc",
    "script",
    "still",
    "scene",
    "segment",
    "link",
}


def _is_mega_notebook_notes(notes: Optional[str]) -> bool:
    if not notes:
        return False
    lowered = notes.lower()
    return any(
        token in lowered
        for token in ("mega_notebook", "mega-notebook", "mega notebook", "ops_only", "ops-only")
    )

class RawAssetRequest(BaseModel):
    source_id: str
    source_url: str
    source_type: str
    title: Optional[str] = None
    director: Optional[str] = None
    year: Optional[int] = None
    duration_sec: Optional[int] = None
    language: Optional[str] = None
    tags: List[str] = []
    scene_ranges: Optional[str] = None
    notes: Optional[str] = None
    rights_status: Optional[str] = None
    created_by: Optional[str] = None

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("source_type is required")
        if "/" in cleaned:
            prefix = cleaned.split("/", 1)[0]
            if prefix in {"text", "application"}:
                cleaned = "doc"
            else:
                cleaned = prefix
        if cleaned in {"text", "application"}:
            cleaned = "doc"
        if cleaned not in _RAW_SOURCE_TYPE_ALLOWLIST:
            raise ValueError(f"source_type must be one of {sorted(_RAW_SOURCE_TYPE_ALLOWLIST)}")
        return cleaned


class RawAssetResponse(BaseModel):
    id: str
    source_id: str
    source_url: str
    source_type: str
    title: Optional[str]
    director: Optional[str]
    year: Optional[int]
    duration_sec: Optional[int]
    language: Optional[str]
    tags: List[str]
    scene_ranges: Optional[str]
    notes: Optional[str]
    rights_status: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VisualSchema(BaseModel):
    composition: Optional[str] = None
    lighting: Optional[str] = None
    color_palette: List[str] = Field(default_factory=list)
    camera_motion: Optional[str] = None
    blocking: Optional[str] = None
    pacing: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class AudioSchema(BaseModel):
    sound_design: Optional[str] = None
    music_mood: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class VideoStructuredRequest(BaseModel):
    segment_id: str
    source_id: str
    work_id: str
    sequence_id: Optional[str] = None
    scene_id: str
    shot_id: str
    time_start: str
    time_end: str
    shot_index: Optional[int] = None
    keyframes: Optional[List[str]] = None
    transcript: Optional[str] = None
    visual_schema_json: dict = Field(default_factory=dict)
    audio_schema_json: dict = Field(default_factory=dict)
    motifs: Optional[List[str]] = None
    evidence_refs: Optional[List[str]] = None
    confidence: Optional[float] = None
    prompt_version: str
    model_version: str
    generated_at: Optional[datetime] = None

    @field_validator("segment_id", "source_id", "work_id", "scene_id", "shot_id", "prompt_version", "model_version")
    @classmethod
    def validate_required_string(cls, value: str, info) -> str:
        if not value or not value.strip():
            raise ValueError(f"{info.field_name} is required")
        return value.strip()

    @field_validator("sequence_id", mode="before")
    @classmethod
    def normalize_sequence_id(cls, value):
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("time_start", "time_end")
    @classmethod
    def validate_timecode(cls, value: str) -> str:
        _parse_timecode(value)
        return value

    @field_validator("prompt_version")
    @classmethod
    def validate_prompt_version(cls, value: str) -> str:
        allowlist = settings.ALLOWED_VIDEO_SCHEMA_VERSIONS
        if allowlist and value not in allowlist:
            raise ValueError(f"prompt_version must be one of {allowlist}")
        return value

    @field_validator("keyframes", "motifs", "evidence_refs", mode="before")
    @classmethod
    def validate_string_list(cls, value, info):
        if value is None:
            return None
        if isinstance(value, str):
            raise ValueError(f"{info.field_name} must be a list of strings")
        if not isinstance(value, list):
            raise ValueError(f"{info.field_name} must be a list of strings")
        cleaned: List[str] = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError(f"{info.field_name} must be a list of strings")
            stripped = item.strip()
            if not stripped:
                raise ValueError(f"{info.field_name} cannot contain empty strings")
            if info.field_name == "keyframes" and not _KEYFRAME_RE.match(stripped):
                raise ValueError("keyframes must match [A-Za-z0-9][A-Za-z0-9_-]{1,63}")
            if info.field_name == "evidence_refs" and not _EVIDENCE_REF_RE.match(stripped):
                raise ValueError("evidence_refs must include a scheme prefix")
            cleaned.append(stripped)
        if not cleaned:
            raise ValueError(f"{info.field_name} must contain at least one item")
        return cleaned

    @field_validator("visual_schema_json", mode="before")
    @classmethod
    def validate_visual_schema(cls, value):
        if value in (None, "", {}):
            return {}
        if not isinstance(value, dict):
            raise ValueError("visual_schema_json must be an object")
        schema = VisualSchema.model_validate(value)
        return schema.model_dump(exclude_none=True)

    @field_validator("audio_schema_json", mode="before")
    @classmethod
    def validate_audio_schema(cls, value):
        if value in (None, "", {}):
            return {}
        if not isinstance(value, dict):
            raise ValueError("audio_schema_json must be an object")
        schema = AudioSchema.model_validate(value)
        return schema.model_dump(exclude_none=True)

    @model_validator(mode="after")
    def validate_timecode_order(self):
        start_ms = _parse_timecode(self.time_start)
        end_ms = _parse_timecode(self.time_end)
        if end_ms <= start_ms:
            raise ValueError("time_end must be after time_start")
        return self


class VideoStructuredResponse(BaseModel):
    id: str
    segment_id: str
    source_id: str
    work_id: Optional[str]
    sequence_id: Optional[str]
    scene_id: Optional[str]
    shot_id: Optional[str]
    time_start: str
    time_end: str
    shot_index: Optional[int]
    keyframes: List[str]
    transcript: Optional[str]
    visual_schema_json: dict
    audio_schema_json: dict
    motifs: List[str]
    evidence_refs: List[str]
    confidence: Optional[float]
    prompt_version: str
    model_version: str
    generated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


_TIMECODE_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}$")
_KEYFRAME_RE = re.compile(settings.VIDEO_KEYFRAME_REGEX)
_EVIDENCE_REF_RE = re.compile(settings.VIDEO_EVIDENCE_REF_REGEX, re.IGNORECASE)
_DERIVED_EVIDENCE_REF_RE = re.compile(r"^(sheet:[^:]+:.+|db:[^:]+:.+)$", re.IGNORECASE)


def _parse_timecode(value: str) -> int:
    if not value or not _TIMECODE_RE.match(value):
        raise ValueError("timecode must be HH:MM:SS.mmm")
    hours_str, minutes_str, rest = value.split(":")
    seconds_str, millis_str = rest.split(".")
    hours = int(hours_str)
    minutes = int(minutes_str)
    seconds = int(seconds_str)
    millis = int(millis_str)
    if minutes >= 60 or seconds >= 60 or millis >= 1000:
        raise ValueError("timecode must be HH:MM:SS.mmm")
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + millis


def _segment_to_response(segment: VideoSegment) -> VideoStructuredResponse:
    return VideoStructuredResponse(
        id=str(segment.id),
        segment_id=segment.segment_id,
        source_id=segment.source_id,
        work_id=segment.work_id,
        sequence_id=segment.sequence_id,
        scene_id=segment.scene_id,
        shot_id=segment.shot_id,
        time_start=segment.time_start,
        time_end=segment.time_end,
        shot_index=segment.shot_index,
        keyframes=segment.keyframes or [],
        transcript=segment.transcript,
        visual_schema_json=segment.visual_schema or {},
        audio_schema_json=segment.audio_schema or {},
        motifs=segment.motifs or [],
        evidence_refs=segment.evidence_refs or [],
        confidence=segment.confidence,
        prompt_version=segment.prompt_version,
        model_version=segment.model_version,
        generated_at=segment.generated_at,
        created_at=segment.created_at,
        updated_at=segment.updated_at,
    )


class NotebookLibraryRequest(BaseModel):
    notebook_id: str
    title: str
    notebook_ref: str
    owner_id: Optional[str] = None
    cluster_id: Optional[str] = None
    cluster_label: Optional[str] = None
    cluster_tags: List[str] = []
    guide_scope: Optional[str] = None
    curator_notes: Optional[str] = None
    source_ids: List[str] = []
    source_count: Optional[int] = None

    @field_validator("guide_scope")
    @classmethod
    def validate_guide_scope(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        if cleaned not in _GUIDE_SCOPE_ALLOWLIST:
            raise ValueError(f"guide_scope must be one of {sorted(_GUIDE_SCOPE_ALLOWLIST)}")
        return cleaned


class NotebookLibraryResponse(BaseModel):
    id: str
    notebook_id: str
    title: str
    notebook_ref: str
    owner_id: Optional[str]
    cluster_id: Optional[str]
    cluster_label: Optional[str]
    cluster_tags: List[str]
    guide_scope: Optional[str]
    curator_notes: Optional[str]
    source_ids: List[str]
    source_count: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("/notebook", response_model=List[NotebookLibraryResponse])
async def list_notebook_library(
    search: Optional[str] = Query(None),
    cluster_id: Optional[str] = Query(None),
    guide_scope: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> List[NotebookLibraryResponse]:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    query = select(NotebookLibrary)
    if search:
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                NotebookLibrary.title.ilike(term),
                NotebookLibrary.notebook_id.ilike(term),
                NotebookLibrary.cluster_label.ilike(term),
            )
        )
    if cluster_id:
        query = query.where(NotebookLibrary.cluster_id == cluster_id)
    if guide_scope:
        cleaned = guide_scope.strip()
        if cleaned and cleaned not in _GUIDE_SCOPE_ALLOWLIST:
            raise HTTPException(
                status_code=400,
                detail=f"guide_scope must be one of {sorted(_GUIDE_SCOPE_ALLOWLIST)}",
            )
        if cleaned:
            query = query.where(NotebookLibrary.guide_scope == cleaned)

    query = query.order_by(NotebookLibrary.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


class NotebookAssetRequest(BaseModel):
    notebook_id: str
    asset_id: str
    asset_type: str
    asset_ref: Optional[str] = None
    title: Optional[str] = None
    tags: List[str] = []
    notes: Optional[str] = None

    @field_validator("notebook_id")
    @classmethod
    def validate_notebook_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("notebook_id is required")
        return cleaned

    @field_validator("asset_id")
    @classmethod
    def validate_asset_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("asset_id is required")
        return cleaned

    @field_validator("asset_type")
    @classmethod
    def validate_asset_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in _NOTEBOOK_ASSET_TYPE_ALLOWLIST:
            raise ValueError(
                f"asset_type must be one of {sorted(_NOTEBOOK_ASSET_TYPE_ALLOWLIST)}"
            )
        return cleaned


class NotebookAssetResponse(BaseModel):
    id: str
    notebook_id: str
    asset_id: str
    asset_type: str
    asset_ref: Optional[str]
    title: Optional[str]
    tags: List[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("/notebook-assets", response_model=List[NotebookAssetResponse])
async def list_notebook_assets(
    notebook_id: Optional[str] = Query(None),
    asset_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> List[NotebookAssetResponse]:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    query = select(NotebookAsset)
    if notebook_id:
        query = query.where(NotebookAsset.notebook_id == notebook_id.strip())
    if asset_type:
        cleaned = asset_type.strip().lower()
        if cleaned not in _NOTEBOOK_ASSET_TYPE_ALLOWLIST:
            raise HTTPException(
                status_code=400,
                detail=f"asset_type must be one of {sorted(_NOTEBOOK_ASSET_TYPE_ALLOWLIST)}",
            )
        query = query.where(NotebookAsset.asset_type == cleaned)
    if search:
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                NotebookAsset.title.ilike(term),
                NotebookAsset.asset_id.ilike(term),
            )
        )

    query = query.order_by(NotebookAsset.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/notebook-assets", response_model=NotebookAssetResponse, status_code=status.HTTP_201_CREATED)
async def upsert_notebook_asset(
    data: NotebookAssetRequest,
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> NotebookAssetResponse:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(
        select(NotebookAsset).where(
            NotebookAsset.notebook_id == data.notebook_id,
            NotebookAsset.asset_id == data.asset_id,
            NotebookAsset.asset_type == data.asset_type,
        )
    )
    record = result.scalars().first()
    if not record:
        record = NotebookAsset(
            notebook_id=data.notebook_id,
            asset_id=data.asset_id,
            asset_type=data.asset_type,
        )
        db.add(record)

    record.asset_ref = data.asset_ref or record.asset_ref
    record.title = data.title or record.title
    record.tags = data.tags or record.tags
    record.notes = data.notes or record.notes
    await db.commit()
    await db.refresh(record)
    return record


class EvidenceRecordRequest(BaseModel):
    source_id: str
    summary: str
    output_type: str
    output_language: str
    prompt_version: str
    model_version: str
    guide_type: Optional[str] = None
    homage_guide: Optional[str] = None
    variation_guide: Optional[str] = None
    template_recommendations: List[str] = []
    user_fit_notes: Optional[str] = None
    persona_profile: Optional[str] = None
    synapse_logic: Optional[str] = None
    origin_notebook_id: Optional[str] = None
    filter_notebook_id: Optional[str] = None
    cluster_id: Optional[str] = None
    cluster_label: Optional[str] = None
    cluster_confidence: Optional[float] = None
    style_logic: Optional[str] = None
    mise_en_scene: Optional[str] = None
    director_intent: Optional[str] = None
    labels: List[str] = []
    signature_motifs: List[str] = []
    camera_motion: dict = {}
    color_palette: dict = {}
    pacing: dict = {}
    sound_design: Optional[str] = None
    editing_rhythm: Optional[str] = None
    story_beats: List[dict] = []
    storyboard_cards: List[dict] = []
    key_patterns: List[dict] = []
    studio_output_id: Optional[str] = None
    adapter: Optional[str] = None
    opal_workflow_id: Optional[str] = None
    confidence: Optional[float] = None
    notebook_id: Optional[str] = None
    notebook_ref: Optional[str] = None
    evidence_refs: List[str] = []
    generated_at: Optional[datetime] = None

    @field_validator("guide_type")
    @classmethod
    def validate_guide_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        if cleaned not in _GUIDE_TYPE_ALLOWLIST:
            raise ValueError(f"guide_type must be one of {sorted(_GUIDE_TYPE_ALLOWLIST)}")
        return cleaned

    @field_validator("output_type")
    @classmethod
    def validate_output_type(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned not in _OUTPUT_TYPE_ALLOWLIST:
            raise ValueError(f"output_type must be one of {sorted(_OUTPUT_TYPE_ALLOWLIST)}")
        return cleaned

    @field_validator("evidence_refs", mode="before")
    @classmethod
    def validate_evidence_refs(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            raise ValueError("evidence_refs must be a list of strings")
        if not isinstance(value, list):
            raise ValueError("evidence_refs must be a list of strings")
        cleaned: List[str] = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError("evidence_refs must be a list of strings")
            stripped = item.strip()
            if not stripped:
                raise ValueError("evidence_refs cannot contain empty strings")
            if not _DERIVED_EVIDENCE_REF_RE.match(stripped):
                raise ValueError("evidence_refs must use sheet:{Sheet}:{RowId} or db:{table}:{id}")
            cleaned.append(stripped)
        return cleaned

    @field_validator("key_patterns", mode="before")
    @classmethod
    def validate_key_patterns(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            raise ValueError("key_patterns must be a list of objects")
        if not isinstance(value, list):
            raise ValueError("key_patterns must be a list of objects")
        normalized: List[dict] = []
        for item in value:
            if isinstance(item, str):
                cleaned = item.strip()
                if not cleaned or ":" not in cleaned:
                    raise ValueError("key_patterns entries must include pattern_name:pattern_type")
                name_part, type_part = cleaned.split(":", 1)
                pattern_name = name_part.strip()
                pattern_type = type_part.strip()
                if not _PATTERN_NAME_RE.match(pattern_name):
                    raise ValueError("key_patterns pattern_name must be snake_case")
                if pattern_type not in _PATTERN_TYPE_ALLOWLIST:
                    raise ValueError("key_patterns pattern_type must follow taxonomy")
                normalized.append(
                    {
                        "pattern_name": pattern_name,
                        "pattern_type": pattern_type,
                    }
                )
                continue
            if not isinstance(item, dict):
                raise ValueError("key_patterns must be a list of objects")
            pattern_name = item.get("pattern_name") or item.get("name")
            pattern_type = item.get("pattern_type") or item.get("type")
            if not pattern_name or not pattern_type:
                raise ValueError("key_patterns entries must include pattern_name and pattern_type")
            pattern_name = str(pattern_name).strip()
            pattern_type = str(pattern_type).strip()
            if not _PATTERN_NAME_RE.match(pattern_name):
                raise ValueError("key_patterns pattern_name must be snake_case")
            if pattern_type not in _PATTERN_TYPE_ALLOWLIST:
                raise ValueError("key_patterns pattern_type must follow taxonomy")
            normalized.append(
                {
                    "pattern_name": pattern_name,
                    "pattern_type": pattern_type,
                    "description": item.get("description"),
                    "weight": item.get("weight"),
                }
            )
        return normalized


class EvidenceRecordResponse(BaseModel):
    id: str
    source_id: str
    summary: str
    output_type: str
    output_language: str
    prompt_version: str
    model_version: str
    guide_type: Optional[str]
    homage_guide: Optional[str]
    variation_guide: Optional[str]
    template_recommendations: List[str]
    user_fit_notes: Optional[str]
    persona_profile: Optional[str]
    synapse_logic: Optional[str]
    origin_notebook_id: Optional[str]
    filter_notebook_id: Optional[str]
    cluster_id: Optional[str]
    cluster_label: Optional[str]
    cluster_confidence: Optional[float]
    style_logic: Optional[str]
    mise_en_scene: Optional[str]
    director_intent: Optional[str]
    labels: List[str]
    signature_motifs: List[str]
    camera_motion: dict
    color_palette: dict
    pacing: dict
    sound_design: Optional[str]
    editing_rhythm: Optional[str]
    story_beats: List[dict]
    storyboard_cards: List[dict]
    key_patterns: List[dict]
    studio_output_id: Optional[str]
    adapter: Optional[str]
    opal_workflow_id: Optional[str]
    confidence: Optional[float]
    notebook_id: Optional[str]
    notebook_ref: Optional[str]
    evidence_refs: List[str]
    generated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("/derive", response_model=List[EvidenceRecordResponse])
async def list_evidence_records(
    source_id: Optional[str] = Query(None),
    notebook_id: Optional[str] = Query(None),
    output_type: Optional[str] = Query(None),
    guide_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> List[EvidenceRecordResponse]:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    query = select(EvidenceRecord)
    if source_id:
        query = query.where(EvidenceRecord.source_id == source_id)
    if notebook_id:
        query = query.where(EvidenceRecord.notebook_id == notebook_id)
    if output_type:
        cleaned = output_type.strip()
        if cleaned and cleaned not in _OUTPUT_TYPE_ALLOWLIST:
            raise HTTPException(
                status_code=400,
                detail=f"output_type must be one of {sorted(_OUTPUT_TYPE_ALLOWLIST)}",
            )
        if cleaned:
            query = query.where(EvidenceRecord.output_type == cleaned)
    if guide_type:
        cleaned = guide_type.strip()
        if cleaned and cleaned not in _GUIDE_TYPE_ALLOWLIST:
            raise HTTPException(
                status_code=400,
                detail=f"guide_type must be one of {sorted(_GUIDE_TYPE_ALLOWLIST)}",
            )
        if cleaned:
            query = query.where(EvidenceRecord.guide_type == cleaned)

    query = query.order_by(EvidenceRecord.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


class PatternCandidateRequest(BaseModel):
    source_id: str
    pattern_name: str
    pattern_type: str
    description: Optional[str] = None
    weight: Optional[float] = None
    evidence_ref: Optional[str] = None
    confidence: Optional[float] = None
    status: Optional[str] = "proposed"

    @field_validator("evidence_ref")
    @classmethod
    def validate_evidence_ref(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        if not _EVIDENCE_REF_RE.match(stripped):
            raise ValueError("evidence_ref must match VIDEO_EVIDENCE_REF_PATTERN")
        return stripped

    @field_validator("pattern_name")
    @classmethod
    def validate_pattern_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not _PATTERN_NAME_RE.match(cleaned):
            raise ValueError("pattern_name must be snake_case (lowercase letters, numbers, underscores)")
        return cleaned

    @field_validator("pattern_type")
    @classmethod
    def validate_pattern_type(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned not in _PATTERN_TYPE_ALLOWLIST:
            raise ValueError(f"pattern_type must be one of {sorted(_PATTERN_TYPE_ALLOWLIST)}")
        return cleaned


class PatternCandidateResponse(BaseModel):
    id: str
    source_id: str
    pattern_name: str
    pattern_type: str
    description: Optional[str]
    weight: Optional[float]
    evidence_ref: Optional[str]
    confidence: Optional[float]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatternResponse(BaseModel):
    id: str
    name: str
    pattern_type: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatternTraceResponse(BaseModel):
    id: str
    source_id: str
    pattern_id: str
    pattern_name: Optional[str] = None
    pattern_type: Optional[str] = None
    weight: Optional[float]
    evidence_ref: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatternVersionResponse(BaseModel):
    id: str
    version: str
    note: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("/pattern-versions", response_model=List[PatternVersionResponse])
async def list_pattern_versions(
    limit: int = Query(10, ge=1, le=100),
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> List[PatternVersionResponse]:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(
        select(PatternVersion).order_by(PatternVersion.created_at.desc()).limit(limit)
    )
    return result.scalars().all()


@router.get("/patterns", response_model=List[PatternResponse])
async def list_patterns(
    search: Optional[str] = Query(None),
    pattern_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> List[PatternResponse]:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    query = select(Pattern)
    if search:
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Pattern.name.ilike(term),
                Pattern.description.ilike(term),
            )
        )
    if pattern_type:
        cleaned = pattern_type.strip()
        if cleaned and cleaned not in _PATTERN_TYPE_ALLOWLIST:
            raise HTTPException(
                status_code=400,
                detail=f"pattern_type must be one of {sorted(_PATTERN_TYPE_ALLOWLIST)}",
            )
        if cleaned:
            query = query.where(Pattern.pattern_type == cleaned)
    if status:
        cleaned = status.strip()
        if cleaned:
            query = query.where(Pattern.status == cleaned)

    query = query.order_by(Pattern.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/pattern-trace", response_model=List[PatternTraceResponse])
async def list_pattern_trace(
    search: Optional[str] = Query(None),
    source_id: Optional[str] = Query(None),
    pattern_id: Optional[str] = Query(None),
    pattern_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> List[PatternTraceResponse]:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    query = select(PatternTrace, Pattern).join(Pattern, PatternTrace.pattern_id == Pattern.id)

    if source_id:
        query = query.where(PatternTrace.source_id == source_id)
    if pattern_id:
        try:
            pattern_uuid = uuid.UUID(pattern_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid pattern_id") from exc
        query = query.where(PatternTrace.pattern_id == pattern_uuid)
    if pattern_type:
        cleaned = pattern_type.strip()
        if cleaned and cleaned not in _PATTERN_TYPE_ALLOWLIST:
            raise HTTPException(
                status_code=400,
                detail=f"pattern_type must be one of {sorted(_PATTERN_TYPE_ALLOWLIST)}",
            )
        if cleaned:
            query = query.where(Pattern.pattern_type == cleaned)
    if search:
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Pattern.name.ilike(term),
                PatternTrace.source_id.ilike(term),
            )
        )

    query = query.order_by(PatternTrace.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.all()
    return [
        PatternTraceResponse(
            id=str(trace.id),
            source_id=trace.source_id,
            pattern_id=str(trace.pattern_id),
            pattern_name=pattern.name,
            pattern_type=pattern.pattern_type,
            weight=trace.weight,
            evidence_ref=trace.evidence_ref,
            created_at=trace.created_at,
            updated_at=trace.updated_at,
        )
        for trace, pattern in rows
    ]


@router.post("/video-structured", response_model=VideoStructuredResponse, status_code=status.HTTP_201_CREATED)
async def upsert_video_structured(
    data: VideoStructuredRequest,
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> VideoStructuredResponse:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    raw_result = await db.execute(select(RawAsset).where(RawAsset.source_id == data.source_id))
    raw_asset = raw_result.scalars().first()
    if not raw_asset:
        raise HTTPException(status_code=404, detail="Raw asset not found")
    if raw_asset.rights_status == "restricted":
        raise HTTPException(status_code=403, detail="Restricted asset cannot be promoted")

    result = await db.execute(
        select(VideoSegment).where(VideoSegment.segment_id == data.segment_id)
    )
    segment = result.scalars().first()
    if not segment:
        segment = VideoSegment(
            segment_id=data.segment_id,
            source_id=data.source_id,
            work_id=data.work_id,
            sequence_id=data.sequence_id,
            scene_id=data.scene_id,
            shot_id=data.shot_id,
            time_start=data.time_start,
            time_end=data.time_end,
            prompt_version=data.prompt_version,
            model_version=data.model_version,
        )
        db.add(segment)

    segment.source_id = data.source_id
    segment.work_id = data.work_id
    segment.sequence_id = data.sequence_id
    segment.scene_id = data.scene_id
    segment.shot_id = data.shot_id
    segment.time_start = data.time_start
    segment.time_end = data.time_end
    segment.shot_index = data.shot_index
    segment.keyframes = data.keyframes or []
    segment.transcript = data.transcript
    segment.visual_schema = data.visual_schema_json or {}
    segment.audio_schema = data.audio_schema_json or {}
    segment.motifs = data.motifs or []
    segment.evidence_refs = data.evidence_refs or []
    segment.confidence = data.confidence
    segment.prompt_version = data.prompt_version
    segment.model_version = data.model_version
    segment.generated_at = data.generated_at

    await db.commit()
    await db.refresh(segment)

    return _segment_to_response(segment)


@router.get("/video-structured/{segment_id}", response_model=VideoStructuredResponse)
async def get_video_structured(
    segment_id: str,
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> VideoStructuredResponse:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await db.execute(select(VideoSegment).where(VideoSegment.segment_id == segment_id))
    segment = result.scalars().first()
    if not segment:
        raise HTTPException(status_code=404, detail="Video segment not found")
    return _segment_to_response(segment)


@router.get("/raw/{source_id}/video-structured", response_model=List[VideoStructuredResponse])
async def list_video_structured_by_source(
    source_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> List[VideoStructuredResponse]:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    query = (
        select(VideoSegment)
        .where(VideoSegment.source_id == source_id)
        .order_by(VideoSegment.shot_index.asc().nulls_last(), VideoSegment.time_start.asc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    segments = result.scalars().all()
    return [_segment_to_response(segment) for segment in segments]


@router.get("/video-structured", response_model=List[VideoStructuredResponse])
async def list_video_structured(
    source_id: Optional[str] = Query(None),
    segment_id: Optional[str] = Query(None),
    work_id: Optional[str] = Query(None),
    sequence_id: Optional[str] = Query(None),
    scene_id: Optional[str] = Query(None),
    shot_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> List[VideoStructuredResponse]:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    cleaned_source_id = source_id.strip() if source_id else None
    cleaned_segment_id = segment_id.strip() if segment_id else None
    cleaned_work_id = work_id.strip() if work_id else None
    cleaned_sequence_id = sequence_id.strip() if sequence_id else None
    cleaned_scene_id = scene_id.strip() if scene_id else None
    cleaned_shot_id = shot_id.strip() if shot_id else None
    if not any(
        [
            cleaned_source_id,
            cleaned_segment_id,
            cleaned_work_id,
            cleaned_sequence_id,
            cleaned_scene_id,
            cleaned_shot_id,
        ]
    ):
        raise HTTPException(
            status_code=400,
            detail="source_id, segment_id, work_id, scene_id, or shot_id is required",
        )
    query = select(VideoSegment)
    if cleaned_source_id:
        query = query.where(VideoSegment.source_id == cleaned_source_id)
    if cleaned_segment_id:
        query = query.where(VideoSegment.segment_id == cleaned_segment_id)
    if cleaned_work_id:
        query = query.where(VideoSegment.work_id == cleaned_work_id)
    if cleaned_sequence_id:
        query = query.where(VideoSegment.sequence_id == cleaned_sequence_id)
    if cleaned_scene_id:
        query = query.where(VideoSegment.scene_id == cleaned_scene_id)
    if cleaned_shot_id:
        query = query.where(VideoSegment.shot_id == cleaned_shot_id)
    query = query.order_by(VideoSegment.shot_index.asc().nulls_last(), VideoSegment.time_start.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    segments = result.scalars().all()
    return [_segment_to_response(segment) for segment in segments]


@router.post("/notebook", response_model=NotebookLibraryResponse, status_code=status.HTTP_201_CREATED)
async def upsert_notebook_library(
    data: NotebookLibraryRequest,
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> NotebookLibraryResponse:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await db.execute(
        select(NotebookLibrary).where(NotebookLibrary.notebook_id == data.notebook_id)
    )
    record = result.scalars().first()
    if not record:
        record = NotebookLibrary(
            notebook_id=data.notebook_id,
            title=data.title,
            notebook_ref=data.notebook_ref,
        )
        db.add(record)

    record.title = data.title
    record.notebook_ref = data.notebook_ref
    record.owner_id = data.owner_id
    record.cluster_id = data.cluster_id
    record.cluster_label = data.cluster_label
    record.cluster_tags = data.cluster_tags or []
    record.guide_scope = data.guide_scope
    record.curator_notes = data.curator_notes
    record.source_ids = data.source_ids or []
    record.source_count = data.source_count

    await db.commit()
    await db.refresh(record)
    return record


@router.post("/raw", response_model=RawAssetResponse, status_code=status.HTTP_201_CREATED)
async def upsert_raw_asset(
    data: RawAssetRequest,
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> RawAssetResponse:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await db.execute(select(RawAsset).where(RawAsset.source_id == data.source_id))
    asset = result.scalars().first()
    if not asset:
        asset = RawAsset(
            source_id=data.source_id,
            source_url=data.source_url,
            source_type=data.source_type,
        )
        db.add(asset)

    asset.source_url = data.source_url
    asset.source_type = data.source_type
    asset.title = data.title
    asset.director = data.director
    asset.year = data.year
    asset.duration_sec = data.duration_sec
    asset.language = data.language
    asset.tags = data.tags or []
    asset.scene_ranges = data.scene_ranges
    asset.notes = data.notes
    asset.rights_status = data.rights_status
    asset.created_by = data.created_by

    await db.commit()
    await db.refresh(asset)
    return asset


@router.get("/raw/{source_id}", response_model=RawAssetResponse)
async def get_raw_asset(
    source_id: str,
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> RawAssetResponse:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await db.execute(select(RawAsset).where(RawAsset.source_id == source_id))
    asset = result.scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail="Raw asset not found")
    return asset


@router.post("/derive", response_model=EvidenceRecordResponse, status_code=status.HTTP_201_CREATED)
async def upsert_evidence_record(
    data: EvidenceRecordRequest,
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> EvidenceRecordResponse:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    raw_result = await db.execute(select(RawAsset).where(RawAsset.source_id == data.source_id))
    raw_asset = raw_result.scalars().first()
    if not raw_asset:
        raise HTTPException(status_code=404, detail="Raw asset not found")
    if raw_asset.rights_status == "restricted":
        raise HTTPException(status_code=403, detail="Restricted asset cannot be promoted")

    result = await db.execute(
        select(EvidenceRecord).where(
            EvidenceRecord.source_id == data.source_id,
            EvidenceRecord.prompt_version == data.prompt_version,
            EvidenceRecord.model_version == data.model_version,
            EvidenceRecord.output_type == data.output_type,
            EvidenceRecord.output_language == data.output_language,
        )
    )
    record = result.scalars().first()
    if not record:
        record = EvidenceRecord(
            source_id=data.source_id,
            summary=data.summary,
            output_type=data.output_type,
            output_language=data.output_language,
            prompt_version=data.prompt_version,
            model_version=data.model_version,
        )
        db.add(record)

    record.summary = data.summary
    record.guide_type = data.guide_type
    record.homage_guide = data.homage_guide
    record.variation_guide = data.variation_guide
    record.template_recommendations = data.template_recommendations or []
    record.user_fit_notes = data.user_fit_notes
    record.persona_profile = data.persona_profile
    record.synapse_logic = data.synapse_logic
    record.origin_notebook_id = data.origin_notebook_id
    record.filter_notebook_id = data.filter_notebook_id
    record.cluster_id = data.cluster_id
    record.cluster_label = data.cluster_label
    record.cluster_confidence = data.cluster_confidence
    record.style_logic = data.style_logic
    record.mise_en_scene = data.mise_en_scene
    record.director_intent = data.director_intent
    labels = data.labels or []
    if data.notebook_id:
        notebook_result = await db.execute(
            select(NotebookLibrary).where(NotebookLibrary.notebook_id == data.notebook_id)
        )
        notebook = notebook_result.scalars().first()
        if notebook and _is_mega_notebook_notes(notebook.curator_notes):
            if "ops_only" not in labels:
                labels.append("ops_only")
    record.labels = labels
    record.signature_motifs = data.signature_motifs or []
    record.camera_motion = data.camera_motion or {}
    record.color_palette = data.color_palette or {}
    record.pacing = data.pacing or {}
    record.sound_design = data.sound_design
    record.editing_rhythm = data.editing_rhythm
    record.story_beats = data.story_beats or []
    record.storyboard_cards = data.storyboard_cards or []
    record.key_patterns = data.key_patterns or []
    record.studio_output_id = data.studio_output_id
    record.adapter = data.adapter
    record.opal_workflow_id = data.opal_workflow_id
    record.confidence = data.confidence
    record.notebook_id = data.notebook_id
    record.notebook_ref = data.notebook_ref
    record.evidence_refs = data.evidence_refs or []
    record.generated_at = data.generated_at

    await db.commit()
    await db.refresh(record)
    return record


@router.post("/pattern-candidate", response_model=PatternCandidateResponse, status_code=status.HTTP_201_CREATED)
async def upsert_pattern_candidate(
    data: PatternCandidateRequest,
    db: AsyncSession = Depends(get_db),
) -> PatternCandidateResponse:
    result = await db.execute(
        select(PatternCandidate).where(
            PatternCandidate.source_id == data.source_id,
            PatternCandidate.pattern_name == data.pattern_name,
            PatternCandidate.pattern_type == data.pattern_type,
            PatternCandidate.evidence_ref == (data.evidence_ref or ""),
        )
    )
    candidate = result.scalars().first()
    if not candidate:
        candidate = PatternCandidate(
            source_id=data.source_id,
            pattern_name=data.pattern_name,
            pattern_type=data.pattern_type,
            evidence_ref=data.evidence_ref or "",
        )
        db.add(candidate)

    candidate.description = data.description
    candidate.weight = data.weight
    candidate.confidence = data.confidence
    candidate.status = data.status or candidate.status

    await db.commit()
    await db.refresh(candidate)
    return candidate
