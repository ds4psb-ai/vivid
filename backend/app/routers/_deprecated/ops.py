"""Operational endpoints for pipeline monitoring."""
from __future__ import annotations

import csv
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
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
from app.pattern_versioning import refresh_capsule_specs
from app.sheets_sync import run_sheets_sync
from app.utils.error_sanitize import SAFE_MESSAGES

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
    evidence_ops_only: int = 0
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
    min_fitness_score: Optional[float] = None
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


class CapsuleRefreshRequest(BaseModel):
    pattern_version: Optional[str] = None
    dry_run: bool = False
    only_active: bool = True


class CapsuleRefreshResponse(BaseModel):
    pattern_version: str
    updated: int
    dry_run: bool
    only_active: bool


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
    path_value = os.getenv("CREBIT_QUARANTINE_CSV_PATH", "")
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
    path_value = os.getenv("CREBIT_QUARANTINE_CSV_PATH", "")
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
    evidence_ops_only = 0
    labels_result = await db.execute(select(EvidenceRecord.labels))
    for (labels,) in labels_result.all():
        if not isinstance(labels, list):
            continue
        for item in labels:
            if isinstance(item, str) and item.strip().lower() == "ops_only":
                evidence_ops_only += 1
                break

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
        evidence_ops_only=evidence_ops_only,
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
            min_fitness_score=payload.min_fitness_score,
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
                "min_fitness_score": payload.min_fitness_score,
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


@router.post("/capsules/refresh", response_model=CapsuleRefreshResponse)
async def refresh_capsules(
    payload: CapsuleRefreshRequest,
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_user_id),
) -> CapsuleRefreshResponse:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    started = time.perf_counter()
    try:
        pattern_version, updated = await refresh_capsule_specs(
            payload.pattern_version,
            dry_run=payload.dry_run,
            only_active=payload.only_active,
        )
        duration_ms = int((time.perf_counter() - started) * 1000)
        await _log_action(
            db,
            action_type="capsule_refresh",
            status="success",
            note=pattern_version,
            payload={
                "pattern_version": payload.pattern_version,
                "dry_run": payload.dry_run,
                "only_active": payload.only_active,
            },
            stats={"updated": updated},
            duration_ms=duration_ms,
            actor_id=user_id,
        )
        return CapsuleRefreshResponse(
            pattern_version=pattern_version,
            updated=updated,
            dry_run=payload.dry_run,
            only_active=payload.only_active,
        )
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        await _log_action(
            db,
            action_type="capsule_refresh",
            status="failed",
            note=payload.pattern_version,
            payload={
                "error": str(exc),
                "pattern_version": payload.pattern_version,
                "dry_run": payload.dry_run,
                "only_active": payload.only_active,
            },
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


# --- Pattern Lift Report API (Phase 2.1) ---


class PatternLiftItem(BaseModel):
    pattern_id: str
    pattern_name: str
    pattern_type: str
    parent_metric: float
    variant_metric: float
    lift: float
    lift_pct: float
    sample_size: int
    source_ids: List[str]
    calculated_at: str


class PatternLiftReportResponse(BaseModel):
    items: List[PatternLiftItem]
    total: int
    avg_lift_pct: float
    max_lift_pct: float
    min_lift_pct: float


@router.get("/patterns/lift-report", response_model=PatternLiftReportResponse)
async def get_pattern_lift_report(
    min_sample: int = Query(3, ge=1, le=100),
    limit: int = Query(20, ge=1, le=100),
    min_lift: Optional[float] = Query(None),
    is_admin: bool = Depends(get_is_admin),
) -> PatternLiftReportResponse:
    """Get Pattern Lift Report for Phase 2 optimization.
    
    Calculates lift metrics for all promoted patterns.
    Lift formula: Lift = (variant - parent) / parent
    
    Reference: 07_EXECUTION_PLAN_2025-12.md Phase 2.1
    """
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.pattern_lift import calculate_pattern_lift_report

    results = await calculate_pattern_lift_report(min_sample_size=min_sample)
    
    if min_lift is not None:
        results = [r for r in results if r.lift >= min_lift]
    
    results = results[:limit]

    if not results:
        return PatternLiftReportResponse(
            items=[],
            total=0,
            avg_lift_pct=0.0,
            max_lift_pct=0.0,
            min_lift_pct=0.0,
        )

    items = [
        PatternLiftItem(
            pattern_id=r.pattern_id,
            pattern_name=r.pattern_name,
            pattern_type=r.pattern_type,
            parent_metric=r.parent_metric,
            variant_metric=r.variant_metric,
            lift=r.lift,
            lift_pct=r.lift_pct,
            sample_size=r.sample_size,
            source_ids=r.source_ids,
            calculated_at=r.calculated_at.isoformat() + "Z",
        )
        for r in results
    ]

    avg_lift = sum(r.lift_pct for r in results) / len(results)
    max_lift = max(r.lift_pct for r in results)
    min_lift_val = min(r.lift_pct for r in results)

    return PatternLiftReportResponse(
        items=items,
        total=len(items),
        avg_lift_pct=round(avg_lift, 2),
        max_lift_pct=round(max_lift, 2),
        min_lift_pct=round(min_lift_val, 2),
    )


# --- Evidence Coverage API (Phase 2.3) ---


class EvidenceCoverageByTypeItem(BaseModel):
    claim_type: str
    total_claims: int
    claims_with_evidence: int
    coverage_rate: float


class EvidenceCoverageResponse(BaseModel):
    total_claims: int
    claims_with_evidence: int
    claims_without_evidence: int
    coverage_rate: float
    avg_evidence_per_claim: float
    min_evidence_count: int
    max_evidence_count: int
    coverage_by_type: List[EvidenceCoverageByTypeItem]
    calculated_at: str


class UncoveredClaimItem(BaseModel):
    claim_id: str
    claim_type: str
    statement: str
    cluster_id: str


class UncoveredClaimsResponse(BaseModel):
    items: List[UncoveredClaimItem]
    total: int


@router.get("/evidence-coverage", response_model=EvidenceCoverageResponse)
async def get_evidence_coverage(
    cluster_id: Optional[str] = Query(None),
    min_evidence: int = Query(1, ge=1, le=10),
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> EvidenceCoverageResponse:
    """Get Evidence Coverage metrics for monitoring.
    
    Calculates the ratio of claims backed by evidence.
    Coverage = claims_with_evidence / total_claims
    
    Reference: 07_EXECUTION_PLAN_2025-12.md Phase 2.3
               32_CLAIM_EVIDENCE_TRACE_SPEC_V1.md
    """
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.evidence_coverage import calculate_evidence_coverage

    result = await calculate_evidence_coverage(
        db,
        cluster_id=cluster_id,
        min_evidence_count=min_evidence,
    )

    return EvidenceCoverageResponse(
        total_claims=result.total_claims,
        claims_with_evidence=result.claims_with_evidence,
        claims_without_evidence=result.claims_without_evidence,
        coverage_rate=result.coverage_rate,
        avg_evidence_per_claim=result.avg_evidence_per_claim,
        min_evidence_count=result.min_evidence_count,
        max_evidence_count=result.max_evidence_count,
        coverage_by_type=[
            EvidenceCoverageByTypeItem(
                claim_type=item.claim_type,
                total_claims=item.total_claims,
                claims_with_evidence=item.claims_with_evidence,
                coverage_rate=round(item.coverage_rate, 4),
            )
            for item in result.coverage_by_type
        ],
        calculated_at=result.calculated_at.isoformat() + "Z",
    )


@router.get("/evidence-coverage/uncovered", response_model=UncoveredClaimsResponse)
async def get_uncovered_claims(
    limit: int = Query(50, ge=1, le=200),
    cluster_id: Optional[str] = Query(None),
    is_admin: bool = Depends(get_is_admin),
) -> UncoveredClaimsResponse:
    """Get list of claims without evidence.
    
    Useful for identifying gaps in evidence coverage.
    """
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.evidence_coverage import get_claims_without_evidence

    items = await get_claims_without_evidence(limit=limit, cluster_id=cluster_id)

    return UncoveredClaimsResponse(
        items=[
            UncoveredClaimItem(
                claim_id=item["claim_id"],
                claim_type=item["claim_type"],
                statement=item["statement"],
                cluster_id=item["cluster_id"],
            )
            for item in items
        ],
        total=len(items),
    )


# --- Pattern Version History API (P2) ---


class PatternVersionItem(BaseModel):
    id: str
    pattern_id: str
    version: int
    snapshot: Dict[str, Any]
    note: Optional[str] = None
    created_at: str


@router.get("/patterns/versions", response_model=List[PatternVersionItem])
async def list_pattern_versions(
    limit: int = Query(5, le=50),
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> List[PatternVersionItem]:
    """List recent pattern versions for admin UI.

    Returns the most recent pattern version changes.
    """
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.models import PatternVersion

    result = await db.execute(
        select(PatternVersion)
        .order_by(PatternVersion.created_at.desc())
        .limit(limit)
    )
    versions = result.scalars().all()

    return [
        PatternVersionItem(
            id=str(v.id),
            pattern_id=str(v.pattern_id),
            version=v.version,
            snapshot=v.snapshot or {},
            note=v.note,
            created_at=v.created_at.isoformat() if v.created_at else "",
        )
        for v in versions
    ]


# --- Pattern Similarity API (Phase B) ---


class PatternSimilarRequest(BaseModel):
    query: str
    limit: int = 10
    score_threshold: float = 0.7
    pattern_type: Optional[str] = None


class PatternSimilarItem(BaseModel):
    pattern_id: Optional[str] = None
    pattern_name: str
    pattern_type: str
    description: Optional[str] = None
    score: float


class PatternSimilarResponse(BaseModel):
    query: str
    results: List[PatternSimilarItem]
    total: int


class PatternSeedRequest(BaseModel):
    status_filter: Optional[str] = None
    batch_size: int = 50


class PatternSeedResponse(BaseModel):
    total: int
    embedded: int
    errors: int
    collection: str


@router.post("/patterns/similar", response_model=PatternSimilarResponse)
async def search_similar_patterns_api(
    payload: PatternSimilarRequest,
    is_admin: bool = Depends(get_is_admin),
) -> PatternSimilarResponse:
    """Search for semantically similar patterns.

    Uses Gemini embeddings and Qdrant vector search.
    """
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.pattern_embeddings import search_similar_patterns

        results = await search_similar_patterns(
            query_text=payload.query,
            limit=payload.limit,
            score_threshold=payload.score_threshold,
            pattern_type=payload.pattern_type,
        )

        return PatternSimilarResponse(
            query=payload.query,
            results=[
                PatternSimilarItem(
                    pattern_id=r.get("pattern_id"),
                    pattern_name=r.get("pattern_name", ""),
                    pattern_type=r.get("pattern_type", ""),
                    description=r.get("description"),
                    score=r.get("score", 0.0),
                )
                for r in results
            ],
            total=len(results),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail=SAFE_MESSAGES["search"])


@router.post("/patterns/seed-embeddings", response_model=PatternSeedResponse)
async def seed_pattern_embeddings(
    payload: PatternSeedRequest,
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_user_id),
) -> PatternSeedResponse:
    """Seed all PatternCandidates to Qdrant for similarity search.

    Generates embeddings using Gemini and stores in Qdrant.
    """
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    started = time.perf_counter()
    try:
        from app.pattern_embeddings import PATTERNS_COLLECTION, seed_patterns_collection

        stats = await seed_patterns_collection(
            db,
            batch_size=payload.batch_size,
            status_filter=payload.status_filter,
        )

        duration_ms = int((time.perf_counter() - started) * 1000)
        await _log_action(
            db,
            action_type="pattern_seed_embeddings",
            status="success",
            note=f"Embedded {stats['embedded']} patterns",
            payload={
                "status_filter": payload.status_filter,
                "batch_size": payload.batch_size,
            },
            stats=stats,
            duration_ms=duration_ms,
            actor_id=user_id,
        )

        return PatternSeedResponse(
            total=stats["total"],
            embedded=stats["embedded"],
            errors=stats["errors"],
            collection=PATTERNS_COLLECTION,
        )
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        await _log_action(
            db,
            action_type="pattern_seed_embeddings",
            status="failed",
            note=None,
            payload={"error": str(exc)},
            stats={},
            duration_ms=duration_ms,
            actor_id=user_id,
        )
        raise HTTPException(status_code=500, detail=SAFE_MESSAGES["seeding"])


# --- Evidence Similarity API (P1) ---


class EvidenceSimilarRequest(BaseModel):
    query: str
    limit: int = 10
    score_threshold: float = 0.7
    cluster_id: Optional[str] = None
    output_type: Optional[str] = None


class EvidenceSimilarItem(BaseModel):
    evidence_id: Optional[str] = None
    source_id: str
    summary: Optional[str] = None
    cluster_label: Optional[str] = None
    score: float


class EvidenceSimilarResponse(BaseModel):
    query: str
    results: List[EvidenceSimilarItem]
    total: int


class EvidenceSeedRequest(BaseModel):
    output_type_filter: Optional[str] = None
    batch_size: int = 50


class EvidenceSeedResponse(BaseModel):
    total: int
    embedded: int
    errors: int
    collection: str


@router.post("/evidence/similar", response_model=EvidenceSimilarResponse)
async def search_similar_evidence_api(
    payload: EvidenceSimilarRequest,
    is_admin: bool = Depends(get_is_admin),
) -> EvidenceSimilarResponse:
    """Search for semantically similar evidence records.

    Uses Gemini embeddings and Qdrant vector search.
    """
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from app.evidence_embeddings import search_similar_evidence

        results = await search_similar_evidence(
            query_text=payload.query,
            limit=payload.limit,
            score_threshold=payload.score_threshold,
            cluster_id=payload.cluster_id,
            output_type=payload.output_type,
        )

        return EvidenceSimilarResponse(
            query=payload.query,
            results=[
                EvidenceSimilarItem(
                    evidence_id=r.get("evidence_id"),
                    source_id=r.get("source_id", ""),
                    summary=r.get("summary"),
                    cluster_label=r.get("cluster_label"),
                    score=r.get("score", 0.0),
                )
                for r in results
            ],
            total=len(results),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail=SAFE_MESSAGES["search"])


@router.post("/evidence/seed-embeddings", response_model=EvidenceSeedResponse)
async def seed_evidence_embeddings(
    payload: EvidenceSeedRequest,
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_user_id),
) -> EvidenceSeedResponse:
    """Seed all EvidenceRecords to Qdrant for similarity search.

    Generates embeddings using Gemini and stores in Qdrant.
    """
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    started = time.perf_counter()
    try:
        from app.evidence_embeddings import EVIDENCE_COLLECTION, seed_evidence_collection

        stats = await seed_evidence_collection(
            db,
            batch_size=payload.batch_size,
            output_type_filter=payload.output_type_filter,
        )

        duration_ms = int((time.perf_counter() - started) * 1000)
        await _log_action(
            db,
            action_type="evidence_seed_embeddings",
            status="success",
            note=f"Embedded {stats['embedded']} evidence records",
            payload={
                "output_type_filter": payload.output_type_filter,
                "batch_size": payload.batch_size,
            },
            stats=stats,
            duration_ms=duration_ms,
            actor_id=user_id,
        )

        return EvidenceSeedResponse(
            total=stats["total"],
            embedded=stats["embedded"],
            errors=stats["errors"],
            collection=EVIDENCE_COLLECTION,
        )
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        await _log_action(
            db,
            action_type="evidence_seed_embeddings",
            status="failed",
            note=None,
            payload={"error": str(exc)},
            stats={},
            duration_ms=duration_ms,
            actor_id=user_id,
        )
        raise HTTPException(status_code=500, detail=SAFE_MESSAGES["seeding"])


# --- Pilot Metrics API (NotebookLM Loading Gate) ---


class PilotMetricsResponse(BaseModel):
    """Pilot metrics for Go/No-Go decision."""
    evidence_gate_pass_rate: Optional[float] = None
    avg_evidence_refs_per_claim: Optional[float] = None
    template_seed_success_rate: Optional[float] = None
    template_run_success_rate: Optional[float] = None
    evidence_click_rate: Optional[float] = None
    go_nogo_status: str  # "GO" | "NO_GO" | "CONDITIONAL" | "INSUFFICIENT_DATA"
    blockers: List[str] = []
    warnings: List[str] = []
    measured_at: str


@router.get("/pilot-metrics", response_model=PilotMetricsResponse)
async def get_pilot_metrics(
    days: int = Query(7, le=30),
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> PilotMetricsResponse:
    """Get pilot metrics for Go/No-Go decision.

    Calculates:
    - Evidence Gate pass rate (claims with >= 2 evidence_refs)
    - Average evidence refs per claim
    - Template seed success rate (story + beat + storyboard)
    - Template run success rate
    - Evidence click rate (from analytics events)
    """
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    from datetime import timedelta
    from app.models import Claim, ClaimEvidenceMap, AnalyticsEvent

    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=days)

    blockers = []
    warnings = []

    # 1. Evidence Gate: claims with >= 2 evidence refs
    claims_result = await db.execute(
        select(Claim).where(Claim.created_at >= period_start)
    )
    claims = claims_result.scalars().all()

    if claims:
        claims_with_2_refs = 0
        total_refs = 0
        for claim in claims:
            # Count evidence mappings for this claim
            refs_result = await db.execute(
                select(func.count()).select_from(ClaimEvidenceMap).where(
                    ClaimEvidenceMap.claim_id == claim.id
                )
            )
            ref_count = int(refs_result.scalar() or 0)
            total_refs += ref_count
            if ref_count >= 2:
                claims_with_2_refs += 1

        evidence_gate_pass_rate = claims_with_2_refs / len(claims)
        avg_evidence_refs = total_refs / len(claims)
    else:
        evidence_gate_pass_rate = None
        avg_evidence_refs = None

    # 2. Template seed success rate
    templates_result = await db.execute(select(Template))
    templates = templates_result.scalars().all()

    if templates:
        valid_templates = 0
        for t in templates:
            graph_data = t.graph_data or {}
            meta = graph_data.get("meta", {})
            has_story = bool(meta.get("story") or graph_data.get("story"))
            has_beat = bool(meta.get("beat_sheet") or meta.get("story_beats"))
            has_storyboard = bool(meta.get("storyboard") or meta.get("storyboard_cards"))
            if has_story and has_beat and has_storyboard:
                valid_templates += 1
        template_seed_rate = valid_templates / len(templates)
    else:
        template_seed_rate = None

    # 3. Template run success rate
    runs_result = await db.execute(
        select(CapsuleRun.status, func.count()).where(
            CapsuleRun.created_at >= period_start
        ).group_by(CapsuleRun.status)
    )
    run_counts = {row[0]: row[1] for row in runs_result.all()}
    total_runs = sum(run_counts.values())

    if total_runs > 0:
        done_runs = run_counts.get("done", 0)
        template_run_success_rate = done_runs / total_runs
    else:
        template_run_success_rate = None

    # 4. Evidence click rate from analytics
    analytics_result = await db.execute(
        select(AnalyticsEvent.event_type, func.count()).where(
            AnalyticsEvent.created_at >= period_start
        ).group_by(AnalyticsEvent.event_type)
    )
    event_counts = {row[0]: row[1] for row in analytics_result.all()}

    evidence_clicks = event_counts.get("evidence_ref_opened", 0)
    template_views = (
        event_counts.get("template_seeded", 0) +
        event_counts.get("template_version_swapped", 0)
    )

    if template_views > 0:
        evidence_click_rate = evidence_clicks / template_views
    else:
        evidence_click_rate = None

    # Determine Go/No-Go
    if evidence_gate_pass_rate is None or template_seed_rate is None:
        go_nogo_status = "INSUFFICIENT_DATA"
        blockers.append("Not enough data to evaluate")
    else:
        if evidence_gate_pass_rate < 0.95:
            blockers.append(f"Evidence Gate: {evidence_gate_pass_rate*100:.1f}% < 95%")
        if template_seed_rate < 0.90:
            blockers.append(f"Template Seed: {template_seed_rate*100:.1f}% < 90%")
        if template_run_success_rate is not None and template_run_success_rate < 0.98:
            blockers.append(f"Template Run: {template_run_success_rate*100:.1f}% < 98%")

        if evidence_click_rate is not None and evidence_click_rate < 0.15:
            warnings.append(f"Evidence Click Rate: {evidence_click_rate*100:.1f}% < 15%")

        if blockers:
            go_nogo_status = "NO_GO"
        elif warnings:
            go_nogo_status = "CONDITIONAL"
        else:
            go_nogo_status = "GO"

    return PilotMetricsResponse(
        evidence_gate_pass_rate=round(evidence_gate_pass_rate, 4) if evidence_gate_pass_rate else None,
        avg_evidence_refs_per_claim=round(avg_evidence_refs, 2) if avg_evidence_refs else None,
        template_seed_success_rate=round(template_seed_rate, 4) if template_seed_rate else None,
        template_run_success_rate=round(template_run_success_rate, 4) if template_run_success_rate else None,
        evidence_click_rate=round(evidence_click_rate, 4) if evidence_click_rate else None,
        go_nogo_status=go_nogo_status,
        blockers=blockers,
        warnings=warnings,
        measured_at=period_end.isoformat(),
    )


# --- Run Trace Dashboard API (Phase 2.3) ---


class RunTraceSummaryItem(BaseModel):
    date: str
    run_count: int
    avg_latency_ms: Optional[float] = None
    avg_cost_usd: Optional[float] = None
    total_cost_usd: Optional[float] = None
    status_breakdown: Dict[str, int]


class RunTraceSummaryResponse(BaseModel):
    items: List[RunTraceSummaryItem]
    total_runs: int
    period_start: str
    period_end: str
    overall_avg_latency_ms: Optional[float] = None
    overall_avg_cost_usd: Optional[float] = None
    overall_total_cost_usd: Optional[float] = None


@router.get("/run-trace-summary", response_model=RunTraceSummaryResponse)
async def get_run_trace_summary(
    days: int = Query(7, ge=1, le=90),
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> RunTraceSummaryResponse:
    """Get Run Trace summary for cost/latency monitoring dashboard.
    
    Returns daily aggregated metrics for CapsuleRuns:
    - Run count per day
    - Average latency
    - Cost breakdown
    - Status distribution
    
    Reference: 07_EXECUTION_PLAN_2025-12.md Phase 2.3
    """
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    from datetime import timedelta

    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=days)

    # Get all runs in period
    result = await db.execute(
        select(CapsuleRun).where(CapsuleRun.created_at >= period_start)
    )
    runs = result.scalars().all()

    if not runs:
        return RunTraceSummaryResponse(
            items=[],
            total_runs=0,
            period_start=period_start.isoformat() + "Z",
            period_end=period_end.isoformat() + "Z",
        )

    # Group by date
    daily_data: Dict[str, Dict[str, Any]] = {}
    
    for run in runs:
        date_str = run.created_at.strftime("%Y-%m-%d") if run.created_at else "unknown"
        
        if date_str not in daily_data:
            daily_data[date_str] = {
                "run_count": 0,
                "latencies": [],
                "costs": [],
                "statuses": {},
            }
        
        daily_data[date_str]["run_count"] += 1
        
        if run.latency_ms is not None:
            daily_data[date_str]["latencies"].append(run.latency_ms)
        
        if run.cost_usd_est is not None:
            daily_data[date_str]["costs"].append(run.cost_usd_est)
        
        status = run.status or "unknown"
        daily_data[date_str]["statuses"][status] = daily_data[date_str]["statuses"].get(status, 0) + 1

    # Build response items
    items: List[RunTraceSummaryItem] = []
    all_latencies: List[float] = []
    all_costs: List[float] = []

    for date_str in sorted(daily_data.keys()):
        data = daily_data[date_str]
        latencies = data["latencies"]
        costs = data["costs"]
        
        avg_latency = sum(latencies) / len(latencies) if latencies else None
        avg_cost = sum(costs) / len(costs) if costs else None
        total_cost = sum(costs) if costs else None
        
        if avg_latency:
            all_latencies.extend(latencies)
        if costs:
            all_costs.extend(costs)
        
        items.append(
            RunTraceSummaryItem(
                date=date_str,
                run_count=data["run_count"],
                avg_latency_ms=round(avg_latency, 2) if avg_latency else None,
                avg_cost_usd=round(avg_cost, 6) if avg_cost else None,
                total_cost_usd=round(total_cost, 4) if total_cost else None,
                status_breakdown=data["statuses"],
            )
        )

    overall_avg_latency = sum(all_latencies) / len(all_latencies) if all_latencies else None
    overall_avg_cost = sum(all_costs) / len(all_costs) if all_costs else None
    overall_total_cost = sum(all_costs) if all_costs else None

    return RunTraceSummaryResponse(
        items=items,
        total_runs=len(runs),
        period_start=period_start.isoformat() + "Z",
        period_end=period_end.isoformat() + "Z",
        overall_avg_latency_ms=round(overall_avg_latency, 2) if overall_avg_latency else None,
        overall_avg_cost_usd=round(overall_avg_cost, 6) if overall_avg_cost else None,
        overall_total_cost_usd=round(overall_total_cost, 4) if overall_total_cost else None,
    )


# --- LLMOps Evaluation Harness API (Phase 2.4) ---


class EvalMetricItem(BaseModel):
    metric_type: str
    score: float
    confidence: float
    details: Dict[str, Any]


class EvalRunResponse(BaseModel):
    run_id: str
    run_type: str
    metrics: List[EvalMetricItem]
    overall_score: float
    evidence_count: int
    token_usage: int
    latency_ms: int
    evaluated_at: str


class EvalHarnessSummaryResponse(BaseModel):
    total_runs: int
    avg_groundedness: float
    avg_relevancy: float
    avg_completeness: float
    avg_overall: float
    runs_with_human_feedback: int
    human_feedback_avg: float
    period_start: str
    period_end: str


class HumanFeedbackRequest(BaseModel):
    run_id: str
    feedback_type: str  # thumbs_up | thumbs_down | rating | comment
    value: Any
    user_id: Optional[str] = None


class HumanFeedbackResponse(BaseModel):
    success: bool
    run_id: str
    feedback_type: str


@router.get("/eval-harness/summary", response_model=EvalHarnessSummaryResponse)
async def get_eval_harness_summary(
    days: int = Query(7, ge=1, le=90),
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> EvalHarnessSummaryResponse:
    """Get LLMOps Evaluation Harness summary.
    
    Returns aggregated metrics for groundedness, relevancy, completeness.
    
    Reference: 07_EXECUTION_PLAN_2025-12.md Phase 2.4
    """
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.llm_eval_harness import get_eval_harness_summary as get_summary

    result = await get_summary(days=days, session=db)

    return EvalHarnessSummaryResponse(
        total_runs=result.total_runs,
        avg_groundedness=result.avg_groundedness,
        avg_relevancy=result.avg_relevancy,
        avg_completeness=result.avg_completeness,
        avg_overall=result.avg_overall,
        runs_with_human_feedback=result.runs_with_human_feedback,
        human_feedback_avg=result.human_feedback_avg,
        period_start=result.period_start,
        period_end=result.period_end,
    )


@router.get("/eval-harness/run/{run_id}", response_model=EvalRunResponse)
async def evaluate_run(
    run_id: str,
    is_admin: bool = Depends(get_is_admin),
) -> EvalRunResponse:
    """Evaluate a specific capsule run.
    
    Returns groundedness, relevancy, completeness metrics.
    """
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.llm_eval_harness import evaluate_capsule_run

    result = await evaluate_capsule_run(run_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Run not found")

    return EvalRunResponse(
        run_id=result.run_id,
        run_type=result.run_type,
        metrics=[
            EvalMetricItem(
                metric_type=m.metric_type,
                score=m.score,
                confidence=m.confidence,
                details=m.details,
            )
            for m in result.metrics
        ],
        overall_score=result.overall_score,
        evidence_count=result.evidence_count,
        token_usage=result.token_usage,
        latency_ms=result.latency_ms,
        evaluated_at=result.evaluated_at.isoformat() + "Z",
    )


@router.post("/eval-harness/feedback", response_model=HumanFeedbackResponse)
async def submit_human_feedback(
    payload: HumanFeedbackRequest,
    is_admin: bool = Depends(get_is_admin),
) -> HumanFeedbackResponse:
    """Submit human feedback for a run.
    
    Feedback types:
    - thumbs_up: Positive signal
    - thumbs_down: Negative signal
    - rating: 1-5 scale
    - comment: Text feedback
    """
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.llm_eval_harness import record_human_feedback

    success = await record_human_feedback(
        run_id=payload.run_id,
        feedback_type=payload.feedback_type,
        value=payload.value,
        user_id=payload.user_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Learning run not found for this run_id")

    return HumanFeedbackResponse(
        success=True,
        run_id=payload.run_id,
        feedback_type=payload.feedback_type,
    )
