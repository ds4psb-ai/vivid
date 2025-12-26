import argparse
import asyncio
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import func, select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import AsyncSessionLocal, init_db
from app.models import (
    CapsuleRun,
    CapsuleSpec,
    Canvas,
    EvidenceRecord,
    GenerationRun,
    NotebookAsset,
    NotebookLibrary,
    Pattern,
    PatternCandidate,
    PatternTrace,
    PatternVersion,
    RawAsset,
    Template,
    TemplateVersion,
    VideoSegment,
)


async def _count(session, model) -> int:
    result = await session.execute(select(func.count()).select_from(model))
    return int(result.scalar() or 0)


async def _max_time(session, model, field_name: str = "updated_at") -> Optional[datetime]:
    field = getattr(model, field_name)
    result = await session.execute(select(func.max(field)))
    return result.scalar()


async def _group_counts(session, model, field_name: str) -> Dict[str, int]:
    field = getattr(model, field_name)
    result = await session.execute(select(field, func.count()).group_by(field))
    return {str(row[0]): int(row[1]) for row in result.all()}


async def _pattern_version(session) -> Tuple[Optional[str], Optional[datetime]]:
    result = await session.execute(
        select(PatternVersion).order_by(PatternVersion.created_at.desc()).limit(1)
    )
    record = result.scalars().first()
    if not record:
        return None, None
    return record.version, record.created_at


def _fmt_date(value: Optional[datetime]) -> str:
    if not value:
        return "-"
    return value.isoformat(timespec="seconds") + "Z"


async def _report() -> str:
    async with AsyncSessionLocal() as session:
        raw_total = await _count(session, RawAsset)
        raw_restricted = await session.execute(
            select(func.count()).select_from(RawAsset).where(RawAsset.rights_status == "restricted")
        )
        raw_restricted_count = int(raw_restricted.scalar() or 0)
        raw_latest = await _max_time(session, RawAsset)

        video_total = await _count(session, VideoSegment)
        video_latest = await _max_time(session, VideoSegment)

        notebooks_total = await _count(session, NotebookLibrary)
        notebook_assets_total = await _count(session, NotebookAsset)
        notebooks_latest = await _max_time(session, NotebookLibrary)

        evidence_total = await _count(session, EvidenceRecord)
        evidence_latest = await _max_time(session, EvidenceRecord)
        evidence_missing_pack_result = await session.execute(
            select(func.count())
            .select_from(EvidenceRecord)
            .where(
                (EvidenceRecord.source_pack_id.is_(None))
                | (EvidenceRecord.source_pack_id == "")
            )
        )
        evidence_missing_pack = int(evidence_missing_pack_result.scalar() or 0)
        evidence_ops_only = 0
        labels_result = await session.execute(select(EvidenceRecord.labels))
        for (labels,) in labels_result.all():
            if not isinstance(labels, list):
                continue
            for item in labels:
                if isinstance(item, str) and item.strip().lower() == "ops_only":
                    evidence_ops_only += 1
                    break

        candidate_total = await _count(session, PatternCandidate)
        candidate_status = await _group_counts(session, PatternCandidate, "status")

        pattern_total = await _count(session, Pattern)
        pattern_status = await _group_counts(session, Pattern, "status")
        trace_total = await _count(session, PatternTrace)
        pattern_version, pattern_version_at = await _pattern_version(session)
        version_result = await session.execute(
            select(PatternVersion).order_by(PatternVersion.created_at.desc()).limit(5)
        )
        version_history = version_result.scalars().all()

        capsule_specs_total = await _count(session, CapsuleSpec)
        templates_total = await _count(session, Template)
        templates_public = await session.execute(
            select(func.count()).select_from(Template).where(Template.is_public.is_(True))
        )
        templates_public_count = int(templates_public.scalar() or 0)
        template_versions_total = await _count(session, TemplateVersion)
        templates_missing_provenance = 0
        templates_meta_result = await session.execute(select(Template.graph_data))
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

        canvases_total = await _count(session, Canvas)
        capsule_runs_total = await _count(session, CapsuleRun)
        capsule_run_status = await _group_counts(session, CapsuleRun, "status")
        generation_runs_total = await _count(session, GenerationRun)
        generation_run_status = await _group_counts(session, GenerationRun, "status")

    quarantine_path = os.getenv("VIVID_QUARANTINE_CSV_PATH", "")
    quarantine_total = 0
    quarantine_summary: Dict[str, int] = {}
    if quarantine_path:
        path = Path(quarantine_path).expanduser()
        if path.exists() and path.is_file():
            with path.open("r", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    reason = (row.get("reason") or "unknown").strip()
                    quarantine_total += 1
                    quarantine_summary[reason] = quarantine_summary.get(reason, 0) + 1

    lines = [
        "=== Vivid Pipeline Status ===",
        "",
        f"Stage 0 RawAsset: {raw_total} total, {raw_restricted_count} restricted, latest { _fmt_date(raw_latest) }",
        f"Stage 2 VideoSegment: {video_total} total, latest { _fmt_date(video_latest) }",
        f"Stage 3 NotebookLibrary: {notebooks_total} total, assets {notebook_assets_total}, latest { _fmt_date(notebooks_latest) }",
        f"Stage 4 EvidenceRecord: {evidence_total} total, latest { _fmt_date(evidence_latest) }, missing source_pack_id {evidence_missing_pack}, ops_only {evidence_ops_only}",
        f"Stage 5 PatternCandidate: {candidate_total} total, status {candidate_status}",
        f"Stage 6 Pattern: {pattern_total} total, status {pattern_status}, trace {trace_total}, version {pattern_version or '-'} ({_fmt_date(pattern_version_at)})",
        "Pattern versions: "
        + ", ".join(
            [
                f"{item.version} ({_fmt_date(item.created_at)})"
                + (f" - {item.note}" if item.note else "")
                for item in version_history
            ]
        )
        if version_history
        else "Pattern versions: -",
        "Stage 8 Templates: "
        f"{templates_total} total ({templates_public_count} public, "
        f"{templates_missing_provenance} missing provenance), versions {template_versions_total}",
        f"Stage 9 Canvas: {canvases_total} total",
        f"Stage 9 CapsuleRun: {capsule_runs_total} total, status {capsule_run_status}",
        f"Stage 10 GenerationRun: {generation_runs_total} total, status {generation_run_status}",
        f"Quarantine: {quarantine_total} rows, reasons {quarantine_summary}" if quarantine_path else "Quarantine: -",
        "",
    ]
    return "\n".join(lines)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Report pipeline status for Vivid.")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text.")
    args = parser.parse_args()

    await init_db()
    report = await _report()
    if args.json:
        import json

        payload = {"report": report}
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(report)


if __name__ == "__main__":
    asyncio.run(main())
