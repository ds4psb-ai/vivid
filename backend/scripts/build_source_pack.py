import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import AsyncSessionLocal, init_db
from app.models import SourcePack, VideoSegment
from app.source_pack import build_source_packs


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a NotebookLM source pack from video segments."
    )
    parser.add_argument("--cluster-id", required=True)
    parser.add_argument("--temporal-phase", required=True)
    parser.add_argument("--source-id", help="Filter segments by source_id")
    parser.add_argument(
        "--segment-id",
        action="append",
        dest="segment_ids",
        help="Specific segment_id(s) to include (repeatable)",
    )
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument(
        "--max-sources",
        type=int,
        default=50,
        help="Maximum unique sources per pack (NotebookLM limit).",
    )
    parser.add_argument("--pack-id", help="Override generated pack_id")
    parser.add_argument("--notes", help="Optional notes for the pack")
    parser.add_argument("--source-snapshot-at", help="ISO timestamp for source snapshot")
    parser.add_argument("--source-sync-at", help="ISO timestamp for last source sync")
    parser.add_argument("--source-manifest", help="JSON array or file path for source manifest")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned.endswith("Z"):
        cleaned = cleaned.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        raise ValueError(f"Invalid datetime format: {value}")


def _load_manifest(value: Optional[str]) -> Optional[List[dict]]:
    if not value:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    path = Path(candidate)
    if path.exists():
        raw = path.read_text(encoding="utf-8")
    else:
        raw = candidate
    data = json.loads(raw)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("sources", "items", "data"):
            if isinstance(data.get(key), list):
                return data[key]
    raise ValueError("source_manifest must be a JSON array or contain a list under sources/items/data")


async def _load_segments(args: argparse.Namespace) -> List[VideoSegment]:
    async with AsyncSessionLocal() as session:
        if args.segment_ids:
            result = await session.execute(
                select(VideoSegment).where(VideoSegment.segment_id.in_(args.segment_ids))
            )
            return result.scalars().all()
        if args.source_id:
            result = await session.execute(
                select(VideoSegment)
                .where(VideoSegment.source_id == args.source_id)
                .order_by(VideoSegment.time_start.asc())
                .limit(args.limit)
            )
            return result.scalars().all()
    return []


async def _run(args: argparse.Namespace) -> int:
    await init_db()
    segments = await _load_segments(args)
    if not segments:
        print("No video segments found for the given filters.")
        return 1

    packs = build_source_packs(
        segments,
        cluster_id=args.cluster_id,
        temporal_phase=args.temporal_phase,
        pack_id=args.pack_id,
        notes=args.notes,
        max_sources=args.max_sources,
        source_snapshot_at=args.source_snapshot_at,
        source_sync_at=args.source_sync_at,
        source_manifest=_load_manifest(args.source_manifest),
    )
    if args.dry_run:
        print(json.dumps(packs, ensure_ascii=False, indent=2))
        return 0

    async with AsyncSessionLocal() as session:
        for pack in packs:
            result = await session.execute(
                select(SourcePack).where(SourcePack.pack_id == pack["pack_id"])
            )
            record = result.scalars().first()
            if not record:
                record = SourcePack(
                    pack_id=pack["pack_id"],
                    cluster_id=pack["cluster_id"],
                    temporal_phase=pack["temporal_phase"],
                    bundle_hash=pack["bundle_hash"],
                )
                session.add(record)

            record.source_snapshot_at = _parse_datetime(pack.get("source_snapshot_at"))
            record.source_sync_at = _parse_datetime(pack.get("source_sync_at"))
            record.source_count = int(pack.get("source_count") or 0)
            record.source_manifest = pack.get("source_manifest") or []
            record.source_ids = pack["source_ids"]
            record.segment_refs = pack["segment_refs"]
            record.metrics_snapshot = pack["metrics_snapshot"]
            record.bundle_hash = pack["bundle_hash"]
            record.notes = pack.get("notes")
        await session.commit()

    for pack in packs:
        print(f"Source pack saved: {pack['pack_id']}")
    return 0


def main() -> None:
    args = _parse_args()
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
