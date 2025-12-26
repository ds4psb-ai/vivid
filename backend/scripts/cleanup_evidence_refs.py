import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import AsyncSessionLocal, init_db
from app.models import CapsuleRun, Canvas, Template, TemplateVersion
from app.routers.capsules import _filter_evidence_refs


def _extract_meta(graph_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    meta = graph_data.get("meta")
    if not isinstance(meta, dict):
        return graph_data, {}
    return graph_data, meta


async def _clean_refs(
    refs: List[str],
    session: AsyncSessionLocal,
) -> Tuple[List[str], List[str]]:
    return await _filter_evidence_refs(list(refs), session)


async def _clean_graph_evidence(
    graph_data: Dict[str, Any],
    session: AsyncSessionLocal,
) -> Tuple[Dict[str, Any], bool, List[str]]:
    if not isinstance(graph_data, dict):
        return graph_data, False, []
    graph_data, meta = _extract_meta(graph_data)
    refs = meta.get("evidence_refs")
    if not isinstance(refs, list):
        return graph_data, False, []
    filtered, warnings = await _clean_refs(refs, session)
    if filtered == refs and not warnings:
        return graph_data, False, []
    next_meta = dict(meta)
    next_meta["evidence_refs"] = filtered
    return {**graph_data, "meta": next_meta}, True, warnings


async def _clean_runs(session: AsyncSessionLocal, execute: bool) -> Dict[str, int]:
    result = await session.execute(select(CapsuleRun))
    runs = result.scalars().all()
    stats = {"checked": 0, "cleaned": 0, "filtered_refs": 0, "warnings": 0}
    for run in runs:
        stats["checked"] += 1
        refs = run.evidence_refs or []
        filtered, warnings = await _clean_refs(refs, session)
        if filtered != refs or warnings:
            stats["cleaned"] += 1
            stats["filtered_refs"] += max(0, len(refs) - len(filtered))
            stats["warnings"] += len(warnings)
            if execute:
                run.evidence_refs = filtered
    return stats


async def _clean_graph_table(
    session: AsyncSessionLocal,
    table,
    execute: bool,
) -> Dict[str, int]:
    result = await session.execute(select(table))
    rows = result.scalars().all()
    stats = {"checked": 0, "cleaned": 0, "warnings": 0}
    for row in rows:
        stats["checked"] += 1
        graph_data = row.graph_data or {}
        updated_graph, changed, warnings = await _clean_graph_evidence(graph_data, session)
        if changed:
            stats["cleaned"] += 1
            stats["warnings"] += len(warnings)
            if execute:
                row.graph_data = updated_graph
    return stats


async def main() -> None:
    parser = argparse.ArgumentParser(description="Clean evidence_refs in runs/templates/canvases.")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Apply updates to the database (default: dry-run).",
    )
    args = parser.parse_args()

    await init_db()
    async with AsyncSessionLocal() as session:
        run_stats = await _clean_runs(session, args.execute)
        template_stats = await _clean_graph_table(session, Template, args.execute)
        version_stats = await _clean_graph_table(session, TemplateVersion, args.execute)
        canvas_stats = await _clean_graph_table(session, Canvas, args.execute)
        if args.execute:
            await session.commit()

    mode = "EXECUTE" if args.execute else "DRY-RUN"
    print(f"[{mode}] CapsuleRun: {run_stats}")
    print(f"[{mode}] Template: {template_stats}")
    print(f"[{mode}] TemplateVersion: {version_stats}")
    print(f"[{mode}] Canvas: {canvas_stats}")


if __name__ == "__main__":
    asyncio.run(main())
