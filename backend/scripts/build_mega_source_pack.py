import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Set

from sqlalchemy import or_, select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import AsyncSessionLocal, init_db
from app.models import NotebookLibrary, RawAsset, VideoSegment
from app.source_pack import hash_source_pack


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a Mega-Notebook source pack for discovery/ops usage."
    )
    parser.add_argument("--cluster-id", action="append", dest="cluster_ids")
    parser.add_argument("--notebook-id", action="append", dest="notebook_ids")
    parser.add_argument("--guide-scope", action="append", dest="guide_scopes")
    parser.add_argument("--max-sources", type=int, default=600)
    parser.add_argument("--max-segments", type=int, default=1000)
    parser.add_argument("--source-snapshot-at", help="ISO timestamp for source snapshot")
    parser.add_argument("--source-sync-at", help="ISO timestamp for last source sync")
    parser.add_argument("--notes", help="Optional notes for this mega pack")
    parser.add_argument("--output", help="Write JSON to file instead of stdout")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def _parse_datetime(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned.endswith("Z"):
        cleaned = cleaned.replace("Z", "+00:00")
    datetime.fromisoformat(cleaned)
    return value.strip()


def _collect_source_ids(notebooks: Iterable[NotebookLibrary]) -> List[str]:
    seen: Set[str] = set()
    ordered: List[str] = []
    for notebook in notebooks:
        source_ids = notebook.source_ids or []
        if not isinstance(source_ids, list):
            continue
        for source_id in source_ids:
            if not source_id or source_id in seen:
                continue
            seen.add(source_id)
            ordered.append(source_id)
    return ordered


def _segment_ref(segment: VideoSegment) -> dict:
    return {
        "segment_id": segment.segment_id,
        "source_id": segment.source_id,
        "work_id": segment.work_id,
        "sequence_id": segment.sequence_id,
        "scene_id": segment.scene_id,
        "shot_id": segment.shot_id,
        "time_start": segment.time_start,
        "time_end": segment.time_end,
    }


async def _load_notebooks(args: argparse.Namespace) -> List[NotebookLibrary]:
    filters = []
    if args.cluster_ids:
        filters.append(NotebookLibrary.cluster_id.in_(args.cluster_ids))
    if args.notebook_ids:
        filters.append(NotebookLibrary.notebook_id.in_(args.notebook_ids))
    if args.guide_scopes:
        filters.append(NotebookLibrary.guide_scope.in_(args.guide_scopes))
    if not filters:
        raise ValueError("Provide at least one of --cluster-id, --notebook-id, or --guide-scope")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(NotebookLibrary).where(or_(*filters)))
        return result.scalars().all()


async def _load_assets(source_ids: List[str]) -> List[RawAsset]:
    if not source_ids:
        return []
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(RawAsset).where(RawAsset.source_id.in_(source_ids))
        )
        return result.scalars().all()


async def _load_segments(source_ids: List[str], max_segments: int) -> List[VideoSegment]:
    if not source_ids:
        return []
    async with AsyncSessionLocal() as session:
        query = (
            select(VideoSegment)
            .where(VideoSegment.source_id.in_(source_ids))
            .order_by(VideoSegment.source_id.asc(), VideoSegment.time_start.asc())
        )
        if max_segments > 0:
            query = query.limit(max_segments)
        result = await session.execute(query)
        return result.scalars().all()


def _build_manifest(assets: List[RawAsset], source_ids: List[str]) -> List[dict]:
    source_lookup = {source_id: True for source_id in source_ids}
    manifest: List[dict] = []
    for asset in assets:
        if asset.source_id not in source_lookup:
            continue
        manifest.append(
            {
                "source_id": asset.source_id,
                "source_url": asset.source_url,
                "title": asset.title,
                "director": asset.director,
                "year": asset.year,
                "rights_status": asset.rights_status,
            }
        )
    return manifest


async def _run(args: argparse.Namespace) -> int:
    await init_db()
    notebooks = await _load_notebooks(args)
    if not notebooks:
        print("No notebooks found for the given filters.")
        return 1

    source_ids = _collect_source_ids(notebooks)
    if args.max_sources > 0:
        source_ids = source_ids[: args.max_sources]

    assets = await _load_assets(source_ids)
    segments = await _load_segments(source_ids, args.max_segments)
    segment_refs = [_segment_ref(segment) for segment in segments]

    notebook_ids = sorted({nb.notebook_id for nb in notebooks})
    cluster_ids = sorted({nb.cluster_id for nb in notebooks if nb.cluster_id})
    guide_scopes = sorted({nb.guide_scope for nb in notebooks if nb.guide_scope})
    source_manifest = _build_manifest(assets, source_ids)

    metrics_snapshot = {
        "segment_count": len(segment_refs),
        "source_count": len(source_ids),
        "notebook_count": len(notebook_ids),
        "cluster_count": len(cluster_ids),
        "source_limit": args.max_sources,
        "segment_limit": args.max_segments,
    }

    payload = {
        "cluster_ids": cluster_ids,
        "notebook_ids": notebook_ids,
        "guide_scopes": guide_scopes,
        "source_ids": source_ids,
        "segment_refs": segment_refs,
        "metrics_snapshot": metrics_snapshot,
    }
    bundle_hash = hash_source_pack(payload)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    pack_id = f"mega_{timestamp}_{bundle_hash[:8]}"

    pack = {
        "pack_id": pack_id,
        "pack_kind": "mega_ops",
        "temporal_phase": "ALL",
        "capsule_eligible": False,
        "cluster_ids": cluster_ids,
        "notebook_ids": notebook_ids,
        "guide_scopes": guide_scopes,
        "source_snapshot_at": _parse_datetime(args.source_snapshot_at) or datetime.utcnow().isoformat() + "Z",
        "source_sync_at": _parse_datetime(args.source_sync_at),
        "source_ids": source_ids,
        "source_manifest": source_manifest,
        "segment_refs": segment_refs,
        "metrics_snapshot": metrics_snapshot,
        "bundle_hash": bundle_hash,
        "notes": args.notes,
    }

    output = json.dumps(pack, ensure_ascii=False, indent=2)
    if args.output and not args.dry_run:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Mega pack saved: {args.output}")
    else:
        print(output)
    return 0


def main() -> None:
    args = _parse_args()
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
