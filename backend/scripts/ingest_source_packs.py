#!/usr/bin/env python3
"""Ingest source packs from JSON file into database."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db
from app.models import SourcePack


async def ingest_source_packs(data: List[Dict[str, Any]], dry_run: bool = False) -> int:
    """Ingest source packs into database."""
    await init_db()
    created = 0
    updated = 0
    
    async with AsyncSessionLocal() as session:
        for row in data:
            pack_id = row.get("pack_id")
            if not pack_id:
                print(f"Skipping row without pack_id: {row}")
                continue
            
            result = await session.execute(
                select(SourcePack).where(SourcePack.pack_id == pack_id)
            )
            existing = result.scalars().first()
            
            if existing:
                # Update existing
                existing.cluster_id = row.get("cluster_id", existing.cluster_id)
                existing.temporal_phase = row.get("temporal_phase", existing.temporal_phase)
                existing.source_count = row.get("source_count", existing.source_count)
                existing.source_ids = row.get("source_ids", existing.source_ids)
                existing.segment_refs = row.get("segment_refs", existing.segment_refs)
                existing.bundle_hash = row.get("bundle_hash", existing.bundle_hash)
                existing.notes = row.get("notes", existing.notes)
                if row.get("source_manifest"):
                    existing.source_manifest = row["source_manifest"]
                updated += 1
            else:
                # Create new
                pack = SourcePack(
                    pack_id=pack_id,
                    cluster_id=row.get("cluster_id", ""),
                    temporal_phase=row.get("temporal_phase", ""),
                    source_count=row.get("source_count", 0),
                    source_ids=row.get("source_ids", []),
                    segment_refs=row.get("segment_refs", []),
                    source_manifest=row.get("source_manifest", []),
                    metrics_snapshot=row.get("metrics_snapshot", {}),
                    bundle_hash=row.get("bundle_hash", ""),
                    notes=row.get("notes"),
                )
                session.add(pack)
                created += 1
        
        if not dry_run:
            await session.commit()
    
    print(f"Source packs: {created} created, {updated} updated")
    return created + updated


async def main():
    parser = argparse.ArgumentParser(description="Ingest source packs")
    parser.add_argument("--input", required=True, help="JSON file path")
    parser.add_argument("--dry-run", action="store_true", help="Don't commit changes")
    args = parser.parse_args()
    
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        print("Input must be a JSON array")
        sys.exit(1)
    
    await ingest_source_packs(data, dry_run=args.dry_run)


if __name__ == "__main__":
    asyncio.run(main())
