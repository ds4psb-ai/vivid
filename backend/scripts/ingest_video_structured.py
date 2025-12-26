import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import AsyncSessionLocal, init_db
from app.models import RawAsset, VideoSegment
from app.routers.ingest import VideoStructuredRequest


def _load_payload(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _extract_rows(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("segments", "items", "data", "results"):
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


def _parse_json_field(value: Any, field_name: str) -> Optional[Dict[str, Any]]:
    if value in (None, ""):
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{field_name} must be valid JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError(f"{field_name} must be a JSON object")
        return parsed
    raise ValueError(f"{field_name} must be a JSON object")


def _parse_list_field(value: Any) -> Optional[List[str]]:
    if value in (None, ""):
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        items = [item.strip() for item in value.split(",") if item.strip()]
        return items or None
    return value


def _normalize_row(
    row: Dict[str, Any],
    *,
    default_source_id: Optional[str],
    default_prompt_version: Optional[str],
    default_model_version: Optional[str],
) -> Dict[str, Any]:
    source_id = _pick(row, "source_id", "sourceId") or default_source_id
    work_id = _pick(row, "work_id", "workId", "work") or source_id
    visual_schema = _parse_json_field(
        _pick(row, "visual_schema_json", "visual_schema", "visualSchema"),
        "visual_schema_json",
    )
    audio_schema = _parse_json_field(
        _pick(row, "audio_schema_json", "audio_schema", "audioSchema"),
        "audio_schema_json",
    )
    keyframes = _parse_list_field(_pick(row, "keyframes", "keyframe_ids", "keyframeIds"))
    motifs = _parse_list_field(_pick(row, "motifs"))
    evidence_refs = _parse_list_field(_pick(row, "evidence_refs", "evidenceRefs", "evidence"))

    return {
        "segment_id": _pick(row, "segment_id", "segmentId"),
        "source_id": source_id,
        "work_id": work_id,
        "sequence_id": _pick(row, "sequence_id", "sequenceId", "sequence"),
        "scene_id": _pick(row, "scene_id", "sceneId"),
        "shot_id": _pick(row, "shot_id", "shotId", "shot"),
        "time_start": _pick(row, "time_start", "timeStart"),
        "time_end": _pick(row, "time_end", "timeEnd"),
        "shot_index": _pick(row, "shot_index", "shotIndex"),
        "keyframes": keyframes,
        "transcript": _pick(row, "transcript", "asr", "dialogue"),
        "visual_schema_json": visual_schema or {},
        "audio_schema_json": audio_schema or {},
        "motifs": motifs,
        "evidence_refs": evidence_refs,
        "confidence": _pick(row, "confidence"),
        "prompt_version": _pick(row, "prompt_version", "promptVersion") or default_prompt_version,
        "model_version": _pick(row, "model_version", "modelVersion") or default_model_version,
        "generated_at": _pick(row, "generated_at", "generatedAt"),
    }


async def _upsert_segments(
    rows: Iterable[Dict[str, Any]],
    *,
    dry_run: bool,
    allow_missing_raw: bool,
) -> int:
    created = 0
    rights_cache: Dict[str, Optional[str]] = {}
    async with AsyncSessionLocal() as session:
        for row in rows:
            source_id = row["source_id"]
            if not source_id:
                raise ValueError("source_id is required (or pass --source-id)")

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

            result = await session.execute(
                select(VideoSegment).where(VideoSegment.segment_id == row["segment_id"])
            )
            segment = result.scalars().first()
            if not segment:
                segment = VideoSegment(
                    segment_id=row["segment_id"],
                    source_id=source_id,
                    work_id=row.get("work_id"),
                    sequence_id=row.get("sequence_id"),
                    scene_id=row.get("scene_id"),
                    shot_id=row.get("shot_id"),
                    time_start=row["time_start"],
                    time_end=row["time_end"],
                    prompt_version=row["prompt_version"],
                    model_version=row["model_version"],
                )
                session.add(segment)
                created += 1

            segment.source_id = source_id
            segment.work_id = row.get("work_id")
            segment.sequence_id = row.get("sequence_id")
            segment.scene_id = row.get("scene_id")
            segment.shot_id = row.get("shot_id")
            segment.time_start = row["time_start"]
            segment.time_end = row["time_end"]
            segment.prompt_version = row["prompt_version"]
            segment.model_version = row["model_version"]

            if row.get("shot_index") is not None:
                segment.shot_index = row["shot_index"]
            if row.get("keyframes") is not None:
                segment.keyframes = row["keyframes"]
            if row.get("transcript") is not None:
                segment.transcript = row["transcript"]
            if row.get("visual_schema_json"):
                segment.visual_schema = row["visual_schema_json"]
            if row.get("audio_schema_json"):
                segment.audio_schema = row["audio_schema_json"]
            if row.get("motifs") is not None:
                segment.motifs = row["motifs"]
            if row.get("evidence_refs") is not None:
                segment.evidence_refs = row["evidence_refs"]
            if row.get("confidence") is not None:
                segment.confidence = row["confidence"]
            if row.get("generated_at") is not None:
                segment.generated_at = row["generated_at"]

        if not dry_run:
            await session.commit()
    return created


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Gemini structured video outputs into DB.")
    parser.add_argument("--input", required=True, help="Path to JSON file.")
    parser.add_argument("--source-id", help="Fallback source_id for rows missing it.")
    parser.add_argument("--default-prompt-version", help="Fallback prompt_version.")
    parser.add_argument("--default-model-version", help="Fallback model_version.")
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
            normalized = _normalize_row(
                row,
                default_source_id=args.source_id,
                default_prompt_version=args.default_prompt_version,
                default_model_version=args.default_model_version,
            )
            required_fields = (
                "segment_id",
                "source_id",
                "work_id",
                "scene_id",
                "shot_id",
                "time_start",
                "time_end",
                "prompt_version",
                "model_version",
            )
            missing = [field for field in required_fields if not normalized.get(field)]
            if missing:
                errors.append(
                    f"Row {idx}: missing required fields: {', '.join(missing)}"
                )
                continue
            validated = VideoStructuredRequest.model_validate(normalized)
            payload = validated.model_dump()
            generated_at = payload.get("generated_at")
            if isinstance(generated_at, datetime) and generated_at.tzinfo is not None:
                payload["generated_at"] = (
                    generated_at.astimezone(timezone.utc).replace(tzinfo=None)
                )
            normalized_rows.append(payload)
        except Exception as exc:
            errors.append(f"Row {idx}: {exc}")

    if errors:
        for error in errors:
            print(error)
        raise SystemExit(f"Validation failed for {len(errors)} rows.")

    await init_db()
    created = await _upsert_segments(
        normalized_rows,
        dry_run=args.dry_run,
        allow_missing_raw=args.allow_missing_raw,
    )
    action = "validated" if args.dry_run else "upserted"
    print(f"Rows {action}: {len(normalized_rows)} (created {created})")


if __name__ == "__main__":
    asyncio.run(main())
