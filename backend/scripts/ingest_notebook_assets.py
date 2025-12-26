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
from app.models import NotebookAsset
from app.routers.ingest import NotebookAssetRequest


def _load_payload(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _extract_rows(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("assets", "notebook_assets", "items", "data", "results"):
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
        "notebook_id": _pick(row, "notebook_id", "notebookId"),
        "asset_id": _pick(row, "asset_id", "assetId", "id"),
        "asset_type": _pick(row, "asset_type", "assetType"),
        "asset_ref": _pick(row, "asset_ref", "assetRef", "ref", "url"),
        "title": _pick(row, "title"),
        "tags": tags or [],
        "notes": _pick(row, "notes"),
    }


async def _upsert_assets(rows: Iterable[Dict[str, Any]], *, dry_run: bool) -> int:
    if dry_run:
        return 0
    created = 0
    async with AsyncSessionLocal() as session:
        for row in rows:
            result = await session.execute(
                select(NotebookAsset).where(
                    NotebookAsset.notebook_id == row["notebook_id"],
                    NotebookAsset.asset_id == row["asset_id"],
                    NotebookAsset.asset_type == row["asset_type"],
                )
            )
            record = result.scalars().first()
            if not record:
                record = NotebookAsset(
                    notebook_id=row["notebook_id"],
                    asset_id=row["asset_id"],
                    asset_type=row["asset_type"],
                )
                session.add(record)
                created += 1

            record.asset_ref = row.get("asset_ref") or record.asset_ref
            record.title = row.get("title") or record.title
            record.tags = row.get("tags") or record.tags
            record.notes = row.get("notes") or record.notes

        await session.commit()
    return created


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest notebook assets into DB.")
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
            validated = NotebookAssetRequest.model_validate(normalized)
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
