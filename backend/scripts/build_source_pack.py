import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import List

from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import AsyncSessionLocal, init_db
from app.models import SourcePack, VideoSegment
from app.source_pack import build_source_pack


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
    parser.add_argument("--pack-id", help="Override generated pack_id")
    parser.add_argument("--notes", help="Optional notes for the pack")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


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

    pack = build_source_pack(
        segments,
        cluster_id=args.cluster_id,
        temporal_phase=args.temporal_phase,
        pack_id=args.pack_id,
        notes=args.notes,
    )
    if args.dry_run:
        print(json.dumps(pack, ensure_ascii=False, indent=2))
        return 0

    async with AsyncSessionLocal() as session:
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

        record.source_ids = pack["source_ids"]
        record.segment_refs = pack["segment_refs"]
        record.metrics_snapshot = pack["metrics_snapshot"]
        record.bundle_hash = pack["bundle_hash"]
        record.notes = pack.get("notes")
        await session.commit()

    print(f"Source pack saved: {pack['pack_id']}")
    return 0


def main() -> None:
    args = _parse_args()
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
