#!/usr/bin/env python3
"""Ingest image grid data into source_packs and Qdrant.

Converts image grid JSON (from splitter tool) to SourcePack records.
Indexes tile labels to Qdrant with dataset_id=image_grid for RAG search.

Usage:
    python scripts/ingest_image_grid.py --input data/source_packs/image_grid_sample.json
    python scripts/ingest_image_grid.py --input data/source_packs/image_grid_sample.json --dry-run
    python scripts/ingest_image_grid.py --input data/source_packs/image_grid_sample.json --no-qdrant
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent to path for imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db
from app.models import SourcePack

# Qdrant RAG Dimension (3D = Image Style)
QDRANT_DIMENSION = "3D"
DATASET_ID = "image_grid"
TILE_STORAGE_DIR = Path(ROOT_DIR).parent / "data" / "source_packs" / "image_grid_tiles"


def save_tile_image(
    pack_id: str,
    row: int,
    col: int,
    data_url: Optional[str],
    dry_run: bool = False,
) -> Optional[str]:
    """Save base64 tile image to file.
    
    Args:
        pack_id: Pack identifier
        row: Tile row
        col: Tile column
        data_url: Base64 data URL (data:image/png;base64,...)
        dry_run: If True, skip actual save
    
    Returns:
        Relative path to saved file, or None if no data_url
    """
    if not data_url or not data_url.startswith("data:image"):
        return None
    
    # Extract base64 content
    try:
        header, b64_content = data_url.split(",", 1)
        extension = "png"
        if "jpeg" in header or "jpg" in header:
            extension = "jpg"
        elif "webp" in header:
            extension = "webp"
        
        # Create directory
        pack_dir = TILE_STORAGE_DIR / pack_id
        if not dry_run:
            pack_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        filename = f"tile_r{row}_c{col}.{extension}"
        file_path = pack_dir / filename
        
        if not dry_run:
            image_data = base64.b64decode(b64_content)
            with open(file_path, "wb") as f:
                f.write(image_data)
            print(f"  💾 Saved: {file_path}")
        
        return f"image_grid_tiles/{pack_id}/{filename}"
    except Exception as e:
        print(f"  ⚠️  Failed to save tile r{row}c{col}: {e}")
        return None


def index_to_qdrant(
    grids: List[Dict[str, Any]],
    dry_run: bool = False,
) -> int:
    """Index image grid tiles to Qdrant with dataset_id metadata.
    
    Args:
        grids: List of grid objects with tiles
        dry_run: If True, skip actual indexing
    
    Returns:
        Number of documents indexed
    """
    if dry_run:
        total_tiles = sum(len(g.get("tiles", [])) for g in grids)
        print(f"[DRY RUN] Would index {total_tiles} tiles to Qdrant")
        return 0
    
    try:
        from app.rag.tier1_dimension_rag import get_dimension_rag
        
        rag = get_dimension_rag(QDRANT_DIMENSION)
        indexed = 0
        
        for grid in grids:
            source_id = grid.get("source_id")
            if not source_id:
                continue
            
            pack_id = f"image_grid_{source_id}"
            title = grid.get("title", "")
            
            for tile in grid.get("tiles", []):
                row = tile.get("row", 0)
                col = tile.get("col", 0)
                label = tile.get("label", f"Tile {row},{col}")
                
                doc_id = f"{pack_id}_r{row}_c{col}"
                
                # Build searchable content
                content_parts = [
                    label,
                    f"Grid: {title}",
                    f"Position: row {row}, column {col}",
                    grid.get("notes", ""),
                ]
                content = " | ".join(filter(None, content_parts))
                
                # Metadata for RAG filtering
                metadata = {
                    "dataset_id": DATASET_ID,
                    "source_id": source_id,
                    "pack_id": pack_id,
                    "row": row,
                    "col": col,
                    "tile_label": label,
                    "tier": "source_pack",
                }
                
                success = rag.index_document(doc_id, content, metadata)
                if success:
                    indexed += 1
                    print(f"🔍 Indexed: {doc_id}")
                else:
                    print(f"⚠️  Index failed: {doc_id}")
        
        return indexed
    except Exception as e:
        print(f"⚠️  Qdrant indexing skipped: {e}")
        return 0


async def ingest_image_grid(
    data: List[Dict[str, Any]],
    dry_run: bool = False,
    skip_qdrant: bool = False,
) -> Dict[str, int]:
    """Convert image grid JSON to SourcePack records.
    
    Args:
        data: List of grid objects
        dry_run: If True, don't commit changes
        skip_qdrant: If True, skip Qdrant indexing
    
    Returns:
        Dict with created/updated/skipped/indexed counts
    """
    await init_db()
    
    created = 0
    updated = 0
    skipped = 0
    tiles_saved = 0
    
    async with AsyncSessionLocal() as session:
        for grid in data:
            source_id = grid.get("source_id")
            if not source_id:
                print(f"⚠️  Skipping grid without source_id: {grid.get('title', 'unknown')}")
                skipped += 1
                continue
            
            pack_id = f"image_grid_{source_id}"
            
            # Process tiles
            tiles = grid.get("tiles", [])
            tile_manifest = []
            
            for tile in tiles:
                row = tile.get("row", 0)
                col = tile.get("col", 0)
                label = tile.get("label", "")
                data_url = tile.get("data_url")
                
                # Save tile image if present
                tile_path = save_tile_image(pack_id, row, col, data_url, dry_run)
                if tile_path:
                    tiles_saved += 1
                
                tile_manifest.append({
                    "row": row,
                    "col": col,
                    "label": label,
                    "tile_path": tile_path,
                    "ingested_at": datetime.utcnow().isoformat(),
                })
            
            # Generate bundle hash
            bundle_hash = hashlib.sha256(
                json.dumps(grid, sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest()[:32]
            
            # Check for existing record
            result = await session.execute(
                select(SourcePack).where(SourcePack.pack_id == pack_id)
            )
            existing = result.scalar_one_or_none()
            
            # Grid metadata
            grid_info = grid.get("grid", {})
            
            if existing:
                # Update existing record
                existing.source_manifest = tile_manifest
                existing.metrics_snapshot = {
                    "rows": grid_info.get("rows"),
                    "cols": grid_info.get("cols"),
                    "tile_count": len(tiles),
                }
                existing.bundle_hash = bundle_hash
                existing.notes = grid.get("notes")
                existing.source_count = len(tiles)
                updated += 1
                print(f"📝 Updated: {pack_id}")
            else:
                # Create new record
                pack = SourcePack(
                    pack_id=pack_id,
                    cluster_id="image_grid",
                    temporal_phase="reference",
                    source_count=len(tiles),
                    source_ids=[source_id],
                    source_manifest=tile_manifest,
                    segment_refs=[],
                    metrics_snapshot={
                        "rows": grid_info.get("rows"),
                        "cols": grid_info.get("cols"),
                        "tile_count": len(tiles),
                    },
                    bundle_hash=bundle_hash,
                    notes=grid.get("notes"),
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
        print(f"Tiles saved: {tiles_saved}")
        print(f"Qdrant: Indexed: {indexed}")
    else:
        print(f"\n=== Dry Run Summary ===")
        print(f"DB: Would create: {created}, Would update: {updated}, Skipped: {skipped}")
        print(f"Tiles: Would save: {tiles_saved}")
    
    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "tiles_saved": tiles_saved,
        "indexed": indexed,
    }


async def main():
    parser = argparse.ArgumentParser(description="Ingest image grids into source_packs + Qdrant")
    parser.add_argument("--input", required=True, help="JSON file path or directory")
    parser.add_argument("--dry-run", action="store_true", help="Don't commit changes")
    parser.add_argument("--no-qdrant", action="store_true", help="Skip Qdrant indexing")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if input_path.is_dir():
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
        
        await ingest_image_grid(all_data, dry_run=args.dry_run, skip_qdrant=args.no_qdrant)
    else:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            data = [data]
        
        await ingest_image_grid(data, dry_run=args.dry_run, skip_qdrant=args.no_qdrant)


if __name__ == "__main__":
    asyncio.run(main())
