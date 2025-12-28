"""Pattern promotion helpers shared across CLI and API."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Set, Tuple

from sqlalchemy import select

from app.ingest_rules import PATTERN_NAME_RE, PATTERN_TYPE_ALLOWLIST, VIDEO_EVIDENCE_REF_RE, has_label
from app.database import AsyncSessionLocal, init_db
from app.models import (
    EvidenceRecord,
    Pattern,
    PatternCandidate,
    PatternTrace,
    RawAsset,
)
from app.pattern_versioning import (
    bump_pattern_version,
    update_capsule_specs,
    update_template_versions,
)

DEFAULT_MIN_CONFIDENCE = float(os.getenv("PATTERN_CONFIDENCE_THRESHOLD", "0.6"))
MIN_PROMOTED_TRACE = int(os.getenv("PATTERN_PROMOTION_MIN_TRACE", "5") or 5)
MIN_EVIDENCE_COVERAGE = float(os.getenv("PATTERN_PROMOTION_MIN_EVIDENCE_COVERAGE", "0.6") or 0.6)

async def _derive_candidates_from_evidence(session) -> int:
    result = await session.execute(
        select(EvidenceRecord).where(EvidenceRecord.key_patterns != [])
    )
    records = result.scalars().all()
    created = 0
    for record in records:
        if not record.key_patterns:
            continue
        if has_label(record.labels or [], "ops_only"):
            continue
        evidence_ref = ""
        if record.evidence_refs:
            for ref in record.evidence_refs:
                if isinstance(ref, str):
                    cleaned = ref.strip()
                    if cleaned:
                        evidence_ref = cleaned
                        break
        for pattern in record.key_patterns:
            if not isinstance(pattern, dict):
                continue
            name = pattern.get("pattern_name")
            ptype = pattern.get("pattern_type")
            if not name or not ptype:
                continue
            result = await session.execute(
                select(PatternCandidate).where(
                    PatternCandidate.source_id == record.source_id,
                    PatternCandidate.pattern_name == name,
                    PatternCandidate.pattern_type == ptype,
                    PatternCandidate.evidence_ref == evidence_ref,
                )
            )
            candidate = result.scalars().first()
            if not candidate:
                candidate = PatternCandidate(
                    source_id=record.source_id,
                    pattern_name=name,
                    pattern_type=ptype,
                    evidence_ref=evidence_ref,
                    status="proposed",
                )
                session.add(candidate)
                created += 1
            candidate.description = pattern.get("description") or candidate.description
            candidate.weight = (
                pattern.get("weight") if pattern.get("weight") is not None else candidate.weight
            )
            candidate.confidence = (
                record.confidence if record.confidence is not None else candidate.confidence
            )
    await session.commit()
    return created


async def _load_rights_map(session, source_ids: Iterable[str]) -> Dict[str, Optional[str]]:
    ids = list({sid for sid in source_ids if sid})
    if not ids:
        return {}
    result = await session.execute(select(RawAsset).where(RawAsset.source_id.in_(ids)))
    return {asset.source_id: asset.rights_status for asset in result.scalars().all()}


def _is_valid_evidence_ref(value: Optional[str]) -> bool:
    if not value:
        return False
    cleaned = value.strip()
    if not cleaned:
        return False
    return bool(VIDEO_EVIDENCE_REF_RE.match(cleaned))


def _is_valid_pattern_name_type(name: Optional[str], pattern_type: Optional[str]) -> bool:
    if not name or not pattern_type:
        return False
    if not PATTERN_NAME_RE.match(name):
        return False
    return pattern_type in PATTERN_TYPE_ALLOWLIST


async def _promote_candidates(
    *,
    min_confidence: float,
    min_sources: int,
    require_evidence_ref: bool,
    allow_missing_raw: bool,
    min_fitness_score: Optional[float],
    dry_run: bool,
) -> Tuple[bool, Dict[str, int]]:
    stats = {
        "candidates": 0,
        "promoted_patterns": 0,
        "traces_upserted": 0,
        "skipped_rights": 0,
        "skipped_confidence": 0,
        "skipped_sources": 0,
        "skipped_evidence": 0,
        "skipped_trace_min": 0,
        "skipped_coverage": 0,
        "skipped_taxonomy": 0,
        "skipped_fitness": 0,
    }
    changed = False
    async with AsyncSessionLocal() as session:
        pattern_cache: Dict[Tuple[str, str], Pattern] = {}
        result = await session.execute(
            select(PatternCandidate).where(
                PatternCandidate.status.in_(["validated", "promoted"])
            )
        )
        candidates = result.scalars().all()
        stats["candidates"] = len(candidates)
        valid_candidates = [
            candidate
            for candidate in candidates
            if _is_valid_pattern_name_type(candidate.pattern_name, candidate.pattern_type)
        ]
        stats["skipped_taxonomy"] = len(candidates) - len(valid_candidates)
        source_ids = {candidate.source_id for candidate in valid_candidates}
        rights_map = await _load_rights_map(session, source_ids)

        pattern_sources: Dict[Tuple[str, str], Set[str]] = {}
        fitness_totals: Dict[Tuple[str, str], float] = {}
        fitness_counts: Dict[Tuple[str, str], int] = {}
        for candidate in valid_candidates:
            key = (candidate.pattern_name, candidate.pattern_type)
            pattern_sources.setdefault(key, set()).add(candidate.source_id)
            if candidate.weight is not None:
                fitness_totals[key] = fitness_totals.get(key, 0.0) + float(candidate.weight)
                fitness_counts[key] = fitness_counts.get(key, 0) + 1
        fitness_scores = {
            key: fitness_totals[key] / fitness_counts[key]
            for key in fitness_counts
            if fitness_counts.get(key)
        }

        eligible_counts: Dict[Tuple[str, str], int] = {}
        evidence_counts: Dict[Tuple[str, str], int] = {}
        for candidate in valid_candidates:
            rights_status = rights_map.get(candidate.source_id)
            if rights_status == "restricted":
                continue
            if rights_status is None and not allow_missing_raw:
                continue
            if candidate.status == "validated":
                if candidate.confidence is not None and candidate.confidence < min_confidence:
                    continue
            key = (candidate.pattern_name, candidate.pattern_type)
            if len(pattern_sources.get(key, set())) < min_sources:
                continue
            evidence_ref = (candidate.evidence_ref or "").strip()
            valid_evidence = _is_valid_evidence_ref(evidence_ref)
            if require_evidence_ref and not valid_evidence:
                continue
            eligible_counts[key] = eligible_counts.get(key, 0) + 1
            if valid_evidence:
                evidence_counts[key] = evidence_counts.get(key, 0) + 1

        for candidate in valid_candidates:
            rights_status = rights_map.get(candidate.source_id)
            if rights_status == "restricted":
                stats["skipped_rights"] += 1
                continue
            if rights_status is None and not allow_missing_raw:
                stats["skipped_rights"] += 1
                continue

            evidence_ref = (candidate.evidence_ref or "").strip()
            valid_evidence = _is_valid_evidence_ref(evidence_ref)
            if require_evidence_ref and not valid_evidence:
                stats["skipped_evidence"] += 1
                continue

            source_count = len(pattern_sources.get((candidate.pattern_name, candidate.pattern_type), set()))
            if source_count < min_sources:
                stats["skipped_sources"] += 1
                continue

            if candidate.status == "validated":
                if candidate.confidence is not None and candidate.confidence < min_confidence:
                    stats["skipped_confidence"] += 1
                    continue

            key = (candidate.pattern_name, candidate.pattern_type)
            pattern = pattern_cache.get(key)
            if not pattern:
                result = await session.execute(
                    select(Pattern).where(
                        Pattern.name == candidate.pattern_name,
                        Pattern.pattern_type == candidate.pattern_type,
                    )
                )
                pattern = result.scalars().first()
                if pattern:
                    pattern_cache[key] = pattern
            desired_status = "promoted" if candidate.status == "promoted" else "validated"
            if desired_status == "promoted":
                total_traces = eligible_counts.get(key, 0)
                evidence_traces = evidence_counts.get(key, 0)
                coverage = (
                    evidence_traces / total_traces
                    if total_traces > 0
                    else 0.0
                )
                if total_traces < MIN_PROMOTED_TRACE:
                    stats["skipped_trace_min"] += 1
                    if not (pattern and pattern.status == "promoted"):
                        desired_status = "validated"
                elif coverage < MIN_EVIDENCE_COVERAGE:
                    stats["skipped_coverage"] += 1
                    if not (pattern and pattern.status == "promoted"):
                        desired_status = "validated"
                elif min_fitness_score is not None:
                    avg_fitness = fitness_scores.get(key)
                    if avg_fitness is None or avg_fitness < min_fitness_score:
                        stats["skipped_fitness"] += 1
                        if not (pattern and pattern.status == "promoted"):
                            desired_status = "validated"
            if not pattern:
                pattern = Pattern(
                    name=candidate.pattern_name,
                    pattern_type=candidate.pattern_type,
                    status=desired_status,
                )
                session.add(pattern)
                pattern_cache[key] = pattern
                changed = True
                stats["promoted_patterns"] += 1
            elif pattern.status != desired_status:
                pattern.status = desired_status
                changed = True

            if pattern.id is None:
                await session.flush()

            if valid_evidence:
                result = await session.execute(
                    select(PatternTrace).where(
                        PatternTrace.source_id == candidate.source_id,
                        PatternTrace.pattern_id == pattern.id,
                        PatternTrace.evidence_ref == evidence_ref,
                    )
                )
                trace = result.scalars().first()
                if not trace:
                    trace = PatternTrace(
                        source_id=candidate.source_id,
                        pattern_id=pattern.id,
                        evidence_ref=evidence_ref,
                    )
                    session.add(trace)
                    changed = True
                    stats["traces_upserted"] += 1
                if candidate.weight is not None and trace.weight != candidate.weight:
                    trace.weight = candidate.weight
                    changed = True

        if not dry_run:
            await session.commit()
    return changed, stats


async def run_pattern_promotion(
    *,
    derive_from_evidence: bool = False,
    min_confidence: Optional[float] = None,
    min_sources: int = 2,
    min_fitness_score: Optional[float] = None,
    allow_empty_evidence: bool = False,
    allow_missing_raw: bool = False,
    note: str = "",
    dry_run: bool = False,
) -> Dict[str, object]:
    """Run pattern promotion with optional fitness threshold.
    
    Args:
        derive_from_evidence: Whether to derive candidates from evidence records.
        min_confidence: Minimum confidence score for promotion.
        min_sources: Minimum number of sources required.
        min_fitness_score: Optional fitness score threshold (from GA).
            If provided, only patterns with avg fitness >= threshold will promote.
        allow_empty_evidence: Allow patterns without evidence refs.
        allow_missing_raw: Allow patterns from missing raw assets.
        note: Note for the pattern version.
        dry_run: If True, don't commit changes.
    """
    await init_db()
    derived_candidates = 0
    if derive_from_evidence and not dry_run:
        async with AsyncSessionLocal() as session:
            derived_candidates = await _derive_candidates_from_evidence(session)

    resolved_confidence = (
        DEFAULT_MIN_CONFIDENCE if min_confidence is None else float(min_confidence)
    )

    changed, stats = await _promote_candidates(
        min_confidence=resolved_confidence,
        min_sources=min_sources,
        require_evidence_ref=not allow_empty_evidence,
        allow_missing_raw=allow_missing_raw,
        min_fitness_score=min_fitness_score,
        dry_run=dry_run,
    )

    pattern_version = None
    if changed and not dry_run:
        resolved_note = note.strip() or f"manual promotion {datetime.utcnow().isoformat()}Z"
        pattern_version = await bump_pattern_version(resolved_note)
        await update_capsule_specs(pattern_version)
        await update_template_versions(pattern_version, f"{resolved_note} (patternVersion)")
    else:
        resolved_note = note.strip()

    return {
        "changed": changed,
        "stats": stats,
        "pattern_version": pattern_version,
        "note": resolved_note,
        "derived_candidates": derived_candidates,
    }
