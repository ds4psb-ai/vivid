import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import AsyncSessionLocal, init_db
from app.models import RawAsset
from app.routers.ingest import RawAssetRequest


def _load_payload(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _extract_rows(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("raw_assets", "assets", "items", "data", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        return [payload]
    raise ValueError("Input JSON must be an object or list.")


def _pick(row: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return None


def _parse_list_field(value: Any) -> Optional[List[str]]:
    if value in (None, ""):
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        items = [item.strip() for item in value.split(",") if item.strip()]
        return items or None
    return value


def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    tags = _parse_list_field(_pick(row, "tags", "tag_list", "tagList"))
    return {
        "source_id": _pick(row, "source_id", "sourceId", "id"),
        "source_url": _pick(row, "source_url", "sourceUrl", "url"),
        "source_type": _pick(row, "source_type", "sourceType", "mime_type", "mimeType"),
        "title": _pick(row, "title"),
        "director": _pick(row, "director"),
        "year": _pick(row, "year"),
        "duration_sec": _pick(row, "duration_sec", "durationSec"),
        "language": _pick(row, "language"),
        "tags": tags or [],
        "scene_ranges": _pick(row, "scene_ranges", "sceneRanges"),
        "notes": _pick(row, "notes"),
        "rights_status": _pick(row, "rights_status", "rightsStatus"),
        "created_by": _pick(row, "created_by", "createdBy"),
    }


async def _upsert_assets(rows: Iterable[Dict[str, Any]], *, dry_run: bool) -> int:
    if dry_run:
        return 0
    created = 0
    async with AsyncSessionLocal() as session:
        for row in rows:
            result = await session.execute(
                select(RawAsset).where(RawAsset.source_id == row["source_id"])
            )
            asset = result.scalars().first()
            if not asset:
                asset = RawAsset(
                    source_id=row["source_id"],
                    source_url=row["source_url"],
                    source_type=row["source_type"],
                )
                session.add(asset)
                created += 1

            asset.source_url = row["source_url"]
            asset.source_type = row["source_type"]
            asset.title = row.get("title")
            asset.director = row.get("director")
            asset.year = row.get("year")
            asset.duration_sec = row.get("duration_sec")
            asset.language = row.get("language")
            asset.tags = row.get("tags") or []
            asset.scene_ranges = row.get("scene_ranges")
            asset.notes = row.get("notes")
            asset.rights_status = row.get("rights_status")
            asset.created_by = row.get("created_by")

        await session.commit()
    return created


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest raw assets into DB.")
    parser.add_argument("--input", required=True, help="Path to JSON file.")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, no DB writes.")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        raise SystemExit(f"Input file not found: {path}")

    payload = _load_payload(path)
    raw_rows = _extract_rows(payload)

    normalized_rows: List[Dict[str, Any]] = []
    errors: List[str] = []
    for idx, row in enumerate(raw_rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"Row {idx}: must be an object.")
            continue
        try:
            normalized = _normalize_row(row)
            validated = RawAssetRequest.model_validate(normalized)
            normalized_rows.append(validated.model_dump())
        except Exception as exc:
            errors.append(f"Row {idx}: {exc}")

    if errors:
        for error in errors:
            print(error)
        raise SystemExit(f"Validation failed for {len(errors)} rows.")

    await init_db()
    created = await _upsert_assets(normalized_rows, dry_run=args.dry_run)
    action = "validated" if args.dry_run else "upserted"
    print(f"Rows {action}: {len(normalized_rows)} (created {created})")


if __name__ == "__main__":
    asyncio.run(main())
