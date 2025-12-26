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
from app.models import PatternCandidate, RawAsset
from app.routers.ingest import PatternCandidateRequest


def _load_payload(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _extract_rows(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("pattern_candidates", "candidates", "items", "data", "results"):
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


def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_id": _pick(row, "source_id", "sourceId"),
        "pattern_name": _pick(row, "pattern_name", "patternName", "name"),
        "pattern_type": _pick(row, "pattern_type", "patternType", "type"),
        "description": _pick(row, "description"),
        "weight": _pick(row, "weight"),
        "evidence_ref": _pick(row, "evidence_ref", "evidenceRef"),
        "confidence": _pick(row, "confidence"),
        "status": _pick(row, "status") or "proposed",
    }


async def _upsert_candidates(
    rows: Iterable[Dict[str, Any]],
    *,
    dry_run: bool,
    allow_missing_raw: bool,
) -> int:
    if dry_run:
        return 0
    created = 0
    rights_cache: Dict[str, Optional[str]] = {}
    async with AsyncSessionLocal() as session:
        for row in rows:
            source_id = row["source_id"]
            if source_id not in rights_cache:
                result = await session.execute(
                    select(RawAsset).where(RawAsset.source_id == source_id)
                )
                asset = result.scalars().first()
                rights_cache[source_id] = asset.rights_status if asset else None
            rights_status = rights_cache[source_id]
            if rights_status == "restricted":
                continue
            if rights_status is None and not allow_missing_raw:
                continue

            evidence_ref = row.get("evidence_ref") or ""
            result = await session.execute(
                select(PatternCandidate).where(
                    PatternCandidate.source_id == source_id,
                    PatternCandidate.pattern_name == row["pattern_name"],
                    PatternCandidate.pattern_type == row["pattern_type"],
                    PatternCandidate.evidence_ref == evidence_ref,
                )
            )
            candidate = result.scalars().first()
            if not candidate:
                candidate = PatternCandidate(
                    source_id=source_id,
                    pattern_name=row["pattern_name"],
                    pattern_type=row["pattern_type"],
                    evidence_ref=evidence_ref,
                )
                session.add(candidate)
                created += 1

            candidate.description = row.get("description") or candidate.description
            candidate.weight = row.get("weight")
            candidate.confidence = row.get("confidence")
            candidate.status = row.get("status") or candidate.status or "proposed"

        await session.commit()
    return created


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest pattern candidates into DB.")
    parser.add_argument("--input", required=True, help="Path to JSON file.")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, no DB writes.")
    parser.add_argument("--allow-missing-raw", action="store_true", help="Allow missing RawAsset records.")
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
            validated = PatternCandidateRequest.model_validate(normalized)
            normalized_rows.append(validated.model_dump())
        except Exception as exc:
            errors.append(f"Row {idx}: {exc}")

    if errors:
        for error in errors:
            print(error)
        raise SystemExit(f"Validation failed for {len(errors)} rows.")

    await init_db()
    created = await _upsert_candidates(
        normalized_rows,
        dry_run=args.dry_run,
        allow_missing_raw=args.allow_missing_raw,
    )
    action = "validated" if args.dry_run else "upserted"
    print(f"Rows {action}: {len(normalized_rows)} (created {created})")


if __name__ == "__main__":
    asyncio.run(main())
