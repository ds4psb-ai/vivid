"""Pattern promotion helpers shared across CLI and API."""
from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Set, Tuple

from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db
from app.models import (
    CapsuleSpec,
    EvidenceRecord,
    Pattern,
    PatternCandidate,
    PatternTrace,
    PatternVersion,
    RawAsset,
    Template,
    TemplateVersion,
)

PATTERN_VERSION_RE = re.compile(r"^v(\d+)$", re.IGNORECASE)
DEFAULT_MIN_CONFIDENCE = float(os.getenv("PATTERN_CONFIDENCE_THRESHOLD", "0.6"))


def _next_pattern_version(current: Optional[str]) -> str:
    if not current:
        return "v1"
    match = PATTERN_VERSION_RE.match(current.strip())
    if not match:
        return "v1"
    return f"v{int(match.group(1)) + 1}"


async def _bump_pattern_version(note: str) -> str:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PatternVersion).order_by(PatternVersion.created_at.desc()).limit(1)
        )
        latest = result.scalars().first()
        next_version = _next_pattern_version(latest.version if latest else None)
        snapshot = PatternVersion(version=next_version, note=note)
        session.add(snapshot)
        await session.commit()
        return next_version


async def _update_capsule_specs(pattern_version: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(CapsuleSpec))
        specs = result.scalars().all()
        for spec in specs:
            payload = spec.spec or {}
            current = payload.get("patternVersion") or payload.get("pattern_version")
            if current == pattern_version:
                continue
            payload["patternVersion"] = pattern_version
            spec.spec = payload
        await session.commit()


def _apply_pattern_version_to_graph(graph_data: dict, pattern_version: str) -> Optional[dict]:
    if not isinstance(graph_data, dict):
        return None
    nodes = graph_data.get("nodes")
    if not isinstance(nodes, list):
        return None
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
        if data.get("capsuleId") and data.get("capsuleVersion"):
            current = data.get("patternVersion")
            if current != pattern_version:
                patched = {**data, "patternVersion": pattern_version}
                next_nodes.append({**node, "data": patched})
                updated = True
                continue
        next_nodes.append(node)
    if not updated:
        return None
    return {**graph_data, "nodes": next_nodes}


async def _update_template_versions(pattern_version: str, note: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Template))
        templates = result.scalars().all()
        for template in templates:
            updated_graph = _apply_pattern_version_to_graph(
                template.graph_data or {}, pattern_version
            )
            if not updated_graph:
                continue
            template.graph_data = updated_graph
            template.version = (template.version or 1) + 1
            session.add(
                TemplateVersion(
                    template_id=template.id,
                    version=template.version,
                    graph_data=updated_graph,
                    notes=note,
                    creator_id=template.creator_id,
                )
            )
        await session.commit()


async def _derive_candidates_from_evidence(session) -> int:
    result = await session.execute(
        select(EvidenceRecord).where(EvidenceRecord.key_patterns != [])
    )
    records = result.scalars().all()
    created = 0
    for record in records:
        if not record.key_patterns:
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


async def _promote_candidates(
    *,
    min_confidence: float,
    min_sources: int,
    require_evidence_ref: bool,
    allow_missing_raw: bool,
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
        source_ids = {candidate.source_id for candidate in candidates}
        rights_map = await _load_rights_map(session, source_ids)

        pattern_sources: Dict[Tuple[str, str], Set[str]] = {}
        for candidate in candidates:
            key = (candidate.pattern_name, candidate.pattern_type)
            pattern_sources.setdefault(key, set()).add(candidate.source_id)

        for candidate in candidates:
            rights_status = rights_map.get(candidate.source_id)
            if rights_status == "restricted":
                stats["skipped_rights"] += 1
                continue
            if rights_status is None and not allow_missing_raw:
                stats["skipped_rights"] += 1
                continue

            if require_evidence_ref and not (candidate.evidence_ref or "").strip():
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

            evidence_ref = (candidate.evidence_ref or "").strip()
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
    allow_empty_evidence: bool = False,
    allow_missing_raw: bool = False,
    note: str = "",
    dry_run: bool = False,
) -> Dict[str, object]:
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
        dry_run=dry_run,
    )

    pattern_version = None
    if changed and not dry_run:
        resolved_note = note.strip() or f"manual promotion {datetime.utcnow().isoformat()}Z"
        pattern_version = await _bump_pattern_version(resolved_note)
        await _update_capsule_specs(pattern_version)
        await _update_template_versions(pattern_version, f"{resolved_note} (patternVersion)")
    else:
        resolved_note = note.strip()

    return {
        "changed": changed,
        "stats": stats,
        "pattern_version": pattern_version,
        "note": resolved_note,
        "derived_candidates": derived_candidates,
    }
