#!/usr/bin/env python3
"""Ingest video reference data into source_packs and Qdrant.

Converts video reference JSON exports to SourcePack records for RAG routing.
Also indexes to Qdrant with dataset_id metadata for RAG search.

Usage:
    python scripts/ingest_video_reference.py --input data/source_packs/video_refs.json
    python scripts/ingest_video_reference.py --input data/source_packs/video_refs.json --dry-run
    python scripts/ingest_video_reference.py --input data/source_packs/video_refs.json --no-qdrant
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add parent to path for imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db
from app.models import SourcePack

# Qdrant RAG Dimension (4D = Reference Analyze)
QDRANT_DIMENSION = "4D"
DATASET_ID = "video_ref"


def index_to_qdrant(references: List[Dict[str, Any]], dry_run: bool = False) -> int:
    """Index video references to Qdrant with dataset_id metadata.
    
    Args:
        references: List of video reference objects
        dry_run: If True, skip actual indexing
    
    Returns:
        Number of documents indexed
    """
    if dry_run:
        print(f"[DRY RUN] Would index {len(references)} documents to Qdrant")
        return 0
    
    try:
        from app.rag.tier1_dimension_rag import get_dimension_rag
        
        rag = get_dimension_rag(QDRANT_DIMENSION)
        indexed = 0
        
        for ref in references:
            source_id = ref.get("source_id")
            if not source_id:
                continue
            
            doc_id = f"video_ref_{source_id}"
            
            # Build searchable content
            content_parts = [
                ref.get("title", ""),
                f"Director: {ref.get('director', 'Unknown')}",
                f"Year: {ref.get('year', '')}",
                ref.get("notes", ""),
            ]
            content = " | ".join(filter(None, content_parts))
            
            # Metadata for RAG filtering
            metadata = {
                "dataset_id": DATASET_ID,
                "app_key": "teaching.reference.analyze",  # P3: required for RAG routing
                "source_id": source_id,
                "pack_id": doc_id,
                "director": ref.get("director"),
                "year": ref.get("year"),
                "tier": "source_pack",
            }
            
            success = rag.index_document(doc_id, content, metadata)
            if success:
                indexed += 1
                print(f"🔍 Indexed to Qdrant: {doc_id}")
            else:
                print(f"⚠️  Qdrant indexing failed: {doc_id}")
        
        return indexed
    except Exception as e:
        print(f"⚠️  Qdrant indexing skipped: {e}")
        return 0


async def ingest_video_reference(
    data: List[Dict[str, Any]],
    dry_run: bool = False,
    skip_qdrant: bool = False,
) -> Dict[str, int]:
    """Convert video reference JSON to SourcePack records.
    
    Args:
        data: List of video reference objects
        dry_run: If True, don't commit changes
        skip_qdrant: If True, skip Qdrant indexing
    
    Returns:
        Dict with created/updated/skipped/indexed counts
    """
    await init_db()
    
    created = 0
    updated = 0
    skipped = 0
    
    async with AsyncSessionLocal() as session:
        for ref in data:
            source_id = ref.get("source_id")
            if not source_id:
                print(f"⚠️  Skipping entry without source_id: {ref.get('title', 'unknown')}")
                skipped += 1
                continue
            
            pack_id = f"video_ref_{source_id}"
            
            # Generate stable bundle hash
            bundle_hash = hashlib.sha256(
                json.dumps(ref, sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest()[:32]
            
            # Check for existing record
            result = await session.execute(
                select(SourcePack).where(SourcePack.pack_id == pack_id)
            )
            existing = result.scalar_one_or_none()
            
            # Build source manifest entry
            manifest_entry = {
                "id": source_id,
                "title": ref.get("title"),
                "director": ref.get("director"),
                "year": ref.get("year"),
                "duration_sec": ref.get("duration_sec"),
                "ingested_at": datetime.utcnow().isoformat(),
            }
            
            if existing:
                # Update existing record
                existing.source_manifest = [manifest_entry]
                existing.segment_refs = ref.get("segments", [])
                existing.metrics_snapshot = ref.get("metrics", {})
                existing.bundle_hash = bundle_hash
                existing.notes = ref.get("notes")
                existing.source_count = len(ref.get("segments", [])) or 1
                updated += 1
                print(f"📝 Updated: {pack_id}")
            else:
                # Create new record
                pack = SourcePack(
                    pack_id=pack_id,
                    cluster_id="video_reference",
                    temporal_phase="reference",
                    source_count=len(ref.get("segments", [])) or 1,
                    source_ids=[source_id],
                    source_manifest=[manifest_entry],
                    segment_refs=ref.get("segments", []),
                    metrics_snapshot=ref.get("metrics", {}),
                    bundle_hash=bundle_hash,
                    notes=ref.get("notes"),
                )
                session.add(pack)
                created += 1
                print(f"✅ Created: {pack_id}")
        
        if not dry_run:
            await session.commit()
        
    # Qdrant indexing (after DB commit)
    indexed = 0
    if not skip_qdrant:
        indexed = index_to_qdrant(data, dry_run=dry_run)
    
    # Summary
    if not dry_run:
        print(f"\n=== Summary ===")
        print(f"DB: Created: {created}, Updated: {updated}, Skipped: {skipped}")
        print(f"Qdrant: Indexed: {indexed}")
    else:
        print(f"\n=== Dry Run Summary ===")
        print(f"DB: Would create: {created}, Would update: {updated}, Skipped: {skipped}")
    
    return {"created": created, "updated": updated, "skipped": skipped, "indexed": indexed}


async def main():
    parser = argparse.ArgumentParser(description="Ingest video references into source_packs + Qdrant")
    parser.add_argument("--input", required=True, help="JSON file path or directory")
    parser.add_argument("--dry-run", action="store_true", help="Don't commit changes")
    parser.add_argument("--no-qdrant", action="store_true", help="Skip Qdrant indexing")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if input_path.is_dir():
        # Process all JSON files in directory
        json_files = list(input_path.glob("*.json"))
        if not json_files:
            print(f"No JSON files found in {input_path}")
            sys.exit(1)
        
        all_data = []
        for json_file in json_files:
            with open(json_file, "r", encoding="utf-8") as f:
                file_data = json.load(f)
                if isinstance(file_data, list):
                    all_data.extend(file_data)
                else:
                    all_data.append(file_data)
        
        await ingest_video_reference(all_data, dry_run=args.dry_run, skip_qdrant=args.no_qdrant)
    else:
        # Process single file
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            data = [data]
        
        await ingest_video_reference(data, dry_run=args.dry_run, skip_qdrant=args.no_qdrant)


if __name__ == "__main__":
    asyncio.run(main())

