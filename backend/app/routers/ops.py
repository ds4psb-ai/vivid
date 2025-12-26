"""Operational endpoints for pipeline monitoring."""
from __future__ import annotations

import csv
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_is_admin, get_user_id
from app.database import get_db
from app.models import (
    CapsuleRun,
    CapsuleSpec,
    Canvas,
    EvidenceRecord,
    GenerationRun,
    NotebookAsset,
    NotebookLibrary,
    OpsActionLog,
    Pattern,
    PatternCandidate,
    PatternTrace,
    PatternVersion,
    RawAsset,
    Template,
    TemplateVersion,
    VideoSegment,
)
from app.pattern_promotion import DEFAULT_MIN_CONFIDENCE, run_pattern_promotion
from app.sheets_sync import run_sheets_sync

router = APIRouter()


class StageSummary(BaseModel):
    total: int
    latest: Optional[str] = None


class QuarantineSummaryItem(BaseModel):
    sheet: str
    reason: str
    count: int


class PatternVersionSummary(BaseModel):
    id: str
    version: str
    note: Optional[str] = None
    created_at: str


class PipelineStatusResponse(BaseModel):
    raw_assets: StageSummary
    raw_restricted: int
    video_segments: StageSummary
    notebook_library: StageSummary
    notebook_assets: StageSummary
    evidence_records: StageSummary
    evidence_missing_source_pack: int = 0
    pattern_candidates: StageSummary
    pattern_candidate_status: Dict[str, int]
    patterns: StageSummary
    pattern_status: Dict[str, int]
    pattern_trace: StageSummary
    pattern_version: Optional[str] = None
    pattern_version_at: Optional[str] = None
    pattern_versions: List[PatternVersionSummary] = []
    capsule_specs: StageSummary
    templates: StageSummary
    templates_public: int
    templates_missing_provenance: int = 0
    template_versions: StageSummary
    canvases: StageSummary
    capsule_runs: StageSummary
    capsule_run_status: Dict[str, int]
    generation_runs: StageSummary
    generation_run_status: Dict[str, int]
    quarantine_total: int = 0
    quarantine_by_sheet: Dict[str, int] = {}
    quarantine_by_reason: Dict[str, int] = {}
    quarantine_items: List[QuarantineSummaryItem] = []
    quarantine_sample: List[Dict[str, str]] = []


class PatternPromotionRequest(BaseModel):
    derive_from_evidence: bool = False
    min_confidence: Optional[float] = None
    min_sources: Optional[int] = None
    allow_empty_evidence: bool = False
    allow_missing_raw: bool = False
    note: str = ""
    dry_run: bool = False


class PatternPromotionResponse(BaseModel):
    changed: bool
    stats: Dict[str, int]
    derived_candidates: int = 0
    pattern_version: Optional[str] = None
    note: Optional[str] = None


class SheetsSyncResponse(BaseModel):
    status: str
    duration_ms: int
    quarantine_total: int
    quarantine_by_sheet: Dict[str, int]
    quarantine_by_reason: Dict[str, int]


class OpsActionLogItem(BaseModel):
    id: str
    action_type: str
    status: str
    note: Optional[str] = None
    payload: Dict[str, object]
    stats: Dict[str, object]
    duration_ms: Optional[int] = None
    actor_id: Optional[str] = None
    created_at: str


def _format_date(value: Optional[datetime]) -> Optional[str]:
    if not value:
        return None
    return value.isoformat(timespec="seconds") + "Z"


def _load_quarantine_summary() -> Tuple[int, Dict[str, int], Dict[str, int], List[QuarantineSummaryItem]]:
    path_value = os.getenv("VIVID_QUARANTINE_CSV_PATH", "")
    if not path_value:
        return 0, {}, {}, []
    path = Path(path_value).expanduser()
    if not path.exists() or not path.is_file():
        return 0, {}, {}, []

    total = 0
    by_sheet: Dict[str, int] = {}
    by_reason: Dict[str, int] = {}
    counts: Dict[Tuple[str, str], int] = {}

    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            sheet = (row.get("sheet") or "unknown").strip()
            reason = (row.get("reason") or "unknown").strip()
            total += 1
            by_sheet[sheet] = by_sheet.get(sheet, 0) + 1
            by_reason[reason] = by_reason.get(reason, 0) + 1
            key = (sheet, reason)
            counts[key] = counts.get(key, 0) + 1

    items = [
        QuarantineSummaryItem(sheet=sheet, reason=reason, count=count)
        for (sheet, reason), count in sorted(counts.items(), key=lambda item: item[1], reverse=True)
    ]
    return total, by_sheet, by_reason, items


def _load_quarantine_sample(limit: int = 20) -> List[Dict[str, str]]:
    path_value = os.getenv("VIVID_QUARANTINE_CSV_PATH", "")
    if not path_value:
        return []
    path = Path(path_value).expanduser()
    if not path.exists() or not path.is_file():
        return []
    rows: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            cleaned = {
                "sheet": (row.get("sheet") or "").strip(),
                "reason": (row.get("reason") or "").strip(),
                "row": (row.get("row") or "").strip(),
                "created_at": (row.get("created_at") or "").strip(),
            }
            rows.append(cleaned)
            if len(rows) >= limit:
                break
    return rows


def _build_pattern_versions(rows: List[PatternVersion]) -> List[PatternVersionSummary]:
    items: List[PatternVersionSummary] = []
    for row in rows:
        items.append(
            PatternVersionSummary(
                id=str(row.id),
                version=row.version,
                note=row.note,
                created_at=_format_date(row.created_at) or "-",
            )
        )
    return items


async def _count(db: AsyncSession, model) -> int:
    result = await db.execute(select(func.count()).select_from(model))
    return int(result.scalar() or 0)


async def _latest(db: AsyncSession, model, field_name: str = "updated_at") -> Optional[datetime]:
    field = getattr(model, field_name)
    result = await db.execute(select(func.max(field)))
    return result.scalar()


async def _status_counts(db: AsyncSession, model, field_name: str) -> Dict[str, int]:
    field = getattr(model, field_name)
    result = await db.execute(select(field, func.count()).group_by(field))
    return {str(row[0]): int(row[1]) for row in result.all()}


async def _log_action(
    db: AsyncSession,
    *,
    action_type: str,
    status: str,
    note: Optional[str],
    payload: Dict[str, object],
    stats: Dict[str, object],
    duration_ms: Optional[int],
    actor_id: Optional[str] = None,
) -> OpsActionLog:
    log = OpsActionLog(
        action_type=action_type,
        status=status,
        note=note,
        payload=payload,
        stats=stats,
        duration_ms=duration_ms,
        actor_id=actor_id,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@router.get("/pipeline", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> PipelineStatusResponse:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    raw_total = await _count(db, RawAsset)
    raw_restricted_result = await db.execute(
        select(func.count()).select_from(RawAsset).where(RawAsset.rights_status == "restricted")
    )
    raw_restricted = int(raw_restricted_result.scalar() or 0)

    raw_latest = await _latest(db, RawAsset)
    video_total = await _count(db, VideoSegment)
    video_latest = await _latest(db, VideoSegment)

    notebook_total = await _count(db, NotebookLibrary)
    notebook_latest = await _latest(db, NotebookLibrary)
    notebook_assets_total = await _count(db, NotebookAsset)
    notebook_assets_latest = await _latest(db, NotebookAsset)

    evidence_total = await _count(db, EvidenceRecord)
    evidence_latest = await _latest(db, EvidenceRecord)
    evidence_missing_result = await db.execute(
        select(func.count())
        .select_from(EvidenceRecord)
        .where((EvidenceRecord.source_pack_id.is_(None)) | (EvidenceRecord.source_pack_id == ""))
    )
    evidence_missing_source_pack = int(evidence_missing_result.scalar() or 0)

    candidate_total = await _count(db, PatternCandidate)
    candidate_latest = await _latest(db, PatternCandidate)
    candidate_status = await _status_counts(db, PatternCandidate, "status")

    pattern_total = await _count(db, Pattern)
    pattern_latest = await _latest(db, Pattern)
    pattern_status = await _status_counts(db, Pattern, "status")
    trace_total = await _count(db, PatternTrace)
    trace_latest = await _latest(db, PatternTrace)

    version_result = await db.execute(
        select(PatternVersion).order_by(PatternVersion.created_at.desc()).limit(1)
    )
    version_row = version_result.scalars().first()
    pattern_version = version_row.version if version_row else None
    pattern_version_at = version_row.created_at if version_row else None
    version_history_result = await db.execute(
        select(PatternVersion).order_by(PatternVersion.created_at.desc()).limit(5)
    )
    version_history = _build_pattern_versions(version_history_result.scalars().all())

    capsule_specs_total = await _count(db, CapsuleSpec)
    capsule_specs_latest = await _latest(db, CapsuleSpec)

    templates_total = await _count(db, Template)
    templates_latest = await _latest(db, Template)
    templates_public_result = await db.execute(
        select(func.count()).select_from(Template).where(Template.is_public.is_(True))
    )
    templates_public = int(templates_public_result.scalar() or 0)
    templates_missing_provenance = 0
    templates_meta_result = await db.execute(select(Template.graph_data))
    for (graph_data,) in templates_meta_result.all():
        if not isinstance(graph_data, dict):
            templates_missing_provenance += 1
            continue
        meta = graph_data.get("meta")
        if not isinstance(meta, dict):
            templates_missing_provenance += 1
            continue
        guide_sources = meta.get("guide_sources")
        evidence_refs = meta.get("evidence_refs")
        has_guide_sources = isinstance(guide_sources, list) and len(guide_sources) > 0
        has_evidence_refs = isinstance(evidence_refs, list) and len(evidence_refs) > 0
        if not has_guide_sources and not has_evidence_refs:
            templates_missing_provenance += 1
    template_versions_total = await _count(db, TemplateVersion)
    template_versions_latest = await _latest(db, TemplateVersion)

    canvases_total = await _count(db, Canvas)
    canvases_latest = await _latest(db, Canvas)
    capsule_runs_total = await _count(db, CapsuleRun)
    capsule_runs_latest = await _latest(db, CapsuleRun)
    capsule_run_status = await _status_counts(db, CapsuleRun, "status")

    generation_runs_total = await _count(db, GenerationRun)
    generation_runs_latest = await _latest(db, GenerationRun)
    generation_run_status = await _status_counts(db, GenerationRun, "status")

    quarantine_total, quarantine_by_sheet, quarantine_by_reason, quarantine_items = _load_quarantine_summary()
    quarantine_sample = _load_quarantine_sample()

    return PipelineStatusResponse(
        raw_assets=StageSummary(total=raw_total, latest=_format_date(raw_latest)),
        raw_restricted=raw_restricted,
        video_segments=StageSummary(total=video_total, latest=_format_date(video_latest)),
        notebook_library=StageSummary(total=notebook_total, latest=_format_date(notebook_latest)),
        notebook_assets=StageSummary(total=notebook_assets_total, latest=_format_date(notebook_assets_latest)),
        evidence_records=StageSummary(total=evidence_total, latest=_format_date(evidence_latest)),
        evidence_missing_source_pack=evidence_missing_source_pack,
        pattern_candidates=StageSummary(total=candidate_total, latest=_format_date(candidate_latest)),
        pattern_candidate_status=candidate_status,
        patterns=StageSummary(total=pattern_total, latest=_format_date(pattern_latest)),
        pattern_status=pattern_status,
        pattern_trace=StageSummary(total=trace_total, latest=_format_date(trace_latest)),
        pattern_version=pattern_version,
        pattern_version_at=_format_date(pattern_version_at),
        pattern_versions=version_history,
        capsule_specs=StageSummary(total=capsule_specs_total, latest=_format_date(capsule_specs_latest)),
        templates=StageSummary(total=templates_total, latest=_format_date(templates_latest)),
        templates_public=templates_public,
        templates_missing_provenance=templates_missing_provenance,
        template_versions=StageSummary(total=template_versions_total, latest=_format_date(template_versions_latest)),
        canvases=StageSummary(total=canvases_total, latest=_format_date(canvases_latest)),
        capsule_runs=StageSummary(total=capsule_runs_total, latest=_format_date(capsule_runs_latest)),
        capsule_run_status=capsule_run_status,
        generation_runs=StageSummary(total=generation_runs_total, latest=_format_date(generation_runs_latest)),
        generation_run_status=generation_run_status,
        quarantine_total=quarantine_total,
        quarantine_by_sheet=quarantine_by_sheet,
        quarantine_by_reason=quarantine_by_reason,
        quarantine_items=quarantine_items,
        quarantine_sample=quarantine_sample,
    )


@router.get("/actions", response_model=List[OpsActionLogItem])
async def list_ops_actions(
    limit: int = 10,
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> List[OpsActionLogItem]:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    limit = max(1, min(limit, 50))
    result = await db.execute(
        select(OpsActionLog).order_by(OpsActionLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    return [
        OpsActionLogItem(
            id=str(log.id),
            action_type=log.action_type,
            status=log.status,
            note=log.note,
            payload=log.payload or {},
            stats=log.stats or {},
            duration_ms=log.duration_ms,
            actor_id=log.actor_id,
            created_at=_format_date(log.created_at) or "-",
        )
        for log in logs
    ]


@router.post("/patterns/promote", response_model=PatternPromotionResponse)
async def promote_patterns(
    payload: PatternPromotionRequest,
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_user_id),
) -> PatternPromotionResponse:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    started = time.perf_counter()
    min_confidence = (
        DEFAULT_MIN_CONFIDENCE
        if payload.min_confidence is None
        else float(payload.min_confidence)
    )
    min_sources = payload.min_sources if payload.min_sources is not None else 2

    try:
        result = await run_pattern_promotion(
            derive_from_evidence=payload.derive_from_evidence,
            min_confidence=min_confidence,
            min_sources=min_sources,
            allow_empty_evidence=payload.allow_empty_evidence,
            allow_missing_raw=payload.allow_missing_raw,
            note=payload.note,
            dry_run=payload.dry_run,
        )
        duration_ms = int((time.perf_counter() - started) * 1000)
        await _log_action(
            db,
            action_type="pattern_promotion",
            status="success",
            note=result.get("note"),
            payload={
                "min_confidence": min_confidence,
                "min_sources": min_sources,
                "derive_from_evidence": payload.derive_from_evidence,
                "allow_empty_evidence": payload.allow_empty_evidence,
                "allow_missing_raw": payload.allow_missing_raw,
                "dry_run": payload.dry_run,
            },
            stats=result.get("stats", {}),
            duration_ms=duration_ms,
            actor_id=user_id,
        )
        return PatternPromotionResponse(
            changed=bool(result.get("changed")),
            stats=result.get("stats", {}),
            derived_candidates=int(result.get("derived_candidates") or 0),
            pattern_version=result.get("pattern_version"),
            note=result.get("note"),
        )
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        await _log_action(
            db,
            action_type="pattern_promotion",
            status="failed",
            note=payload.note,
            payload={"error": str(exc)},
            stats={},
            duration_ms=duration_ms,
            actor_id=user_id,
        )
        raise


@router.post("/sheets/sync", response_model=SheetsSyncResponse)
async def sync_sheets(
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_user_id),
) -> SheetsSyncResponse:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    started = time.perf_counter()
    try:
        result = await run_sheets_sync()
        quarantine_total, quarantine_by_sheet, quarantine_by_reason, _ = _load_quarantine_summary()
        duration_ms = int(result.get("duration_ms") or (time.perf_counter() - started) * 1000)
        await _log_action(
            db,
            action_type="sheets_sync",
            status="success",
            note=None,
            payload={},
            stats={
                "quarantine_total": quarantine_total,
                "quarantine_by_sheet": quarantine_by_sheet,
                "quarantine_by_reason": quarantine_by_reason,
            },
            duration_ms=duration_ms,
            actor_id=user_id,
        )
        return SheetsSyncResponse(
            status="ok",
            duration_ms=duration_ms,
            quarantine_total=quarantine_total,
            quarantine_by_sheet=quarantine_by_sheet,
            quarantine_by_reason=quarantine_by_reason,
        )
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        await _log_action(
            db,
            action_type="sheets_sync",
            status="failed",
            note=None,
            payload={"error": str(exc)},
            stats={},
            duration_ms=duration_ms,
            actor_id=user_id,
        )
        raise
