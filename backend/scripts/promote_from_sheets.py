"""Promote NotebookLM/Opal Sheets data into DB SoR."""
from __future__ import annotations

import asyncio
import csv
import io
import json
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import (
    EvidenceRecord,
    Pattern,
    PatternCandidate,
    PatternTrace,
    RawAsset,
)


SHEETS_MODE = os.getenv("SHEETS_MODE", "csv").lower()
SHEETS_API_BASE = os.getenv("SHEETS_API_BASE", "https://sheets.googleapis.com/v4")
SHEETS_API_KEY = os.getenv("SHEETS_API_KEY", "")
SHEETS_SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID", "")

RAW_CSV_URL = os.getenv("VIVID_RAW_ASSETS_CSV_URL", "")
DERIVED_CSV_URL = os.getenv("VIVID_DERIVED_INSIGHTS_CSV_URL", "")
CANDIDATES_CSV_URL = os.getenv("VIVID_PATTERN_CANDIDATES_CSV_URL", "")
TRACE_CSV_URL = os.getenv("VIVID_PATTERN_TRACE_CSV_URL", "")

RAW_RANGE = os.getenv("VIVID_RAW_ASSETS_RANGE", "VIVID_RAW_ASSETS")
DERIVED_RANGE = os.getenv("VIVID_DERIVED_INSIGHTS_RANGE", "VIVID_DERIVED_INSIGHTS")
CANDIDATES_RANGE = os.getenv("VIVID_PATTERN_CANDIDATES_RANGE", "VIVID_PATTERN_CANDIDATES")
TRACE_RANGE = os.getenv("VIVID_PATTERN_TRACE_RANGE", "VIVID_PATTERN_TRACE")

CONFIDENCE_THRESHOLD = float(os.getenv("PATTERN_CONFIDENCE_THRESHOLD", "0.6"))
SHEETS_RETRY_COUNT = int(os.getenv("SHEETS_RETRY_COUNT", "3"))
SHEETS_RETRY_BASE_SECONDS = float(os.getenv("SHEETS_RETRY_BASE_SECONDS", "0.5"))


def _fetch_url(url: str) -> str:
    req = Request(url, headers={"User-Agent": "vivid-sheets-sync/1.0"})
    last_error: Optional[Exception] = None
    for attempt in range(SHEETS_RETRY_COUNT + 1):
        try:
            with urlopen(req, timeout=30) as response:
                return response.read().decode("utf-8", errors="ignore")
        except Exception as exc:
            last_error = exc
            if attempt < SHEETS_RETRY_COUNT:
                time.sleep(SHEETS_RETRY_BASE_SECONDS * (2 ** attempt))
                continue
            raise
    raise last_error or RuntimeError("Failed to fetch URL")


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace(" ", "_")


def _rows_from_csv(text: str) -> List[Dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text))
    rows: List[Dict[str, str]] = []
    for raw in reader:
        row: Dict[str, str] = {}
        for key, value in raw.items():
            if key is None:
                continue
            norm_key = _normalize_key(key)
            if not norm_key:
                continue
            row[norm_key] = value.strip() if isinstance(value, str) else value
        rows.append(row)
    return rows


def _rows_from_values(values: List[List[str]]) -> List[Dict[str, str]]:
    if not values:
        return []
    headers = [_normalize_key(h) for h in values[0]]
    rows: List[Dict[str, str]] = []
    for raw in values[1:]:
        row: Dict[str, str] = {}
        for idx, header in enumerate(headers):
            if not header:
                continue
            row[header] = raw[idx].strip() if idx < len(raw) and isinstance(raw[idx], str) else ""
        rows.append(row)
    return rows


def _split_list(value: str) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_json(value: str) -> Optional[Any]:
    if not value:
        return None
    trimmed = value.strip()
    if not trimmed.startswith(("{", "[")):
        return None
    try:
        return json.loads(trimmed)
    except json.JSONDecodeError:
        return None


def _parse_dict(value: str) -> Dict[str, Any]:
    parsed = _parse_json(value)
    if isinstance(parsed, dict):
        return parsed
    if value:
        return {"raw": value}
    return {}


def _parse_list(value: str) -> List[Any]:
    parsed = _parse_json(value)
    if isinstance(parsed, list):
        return parsed
    return _split_list(value)


def _parse_int(value: str) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def _parse_float(value: str) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_uuid(value: str) -> Optional[uuid.UUID]:
    if not value:
        return None
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


def _normalize_pattern_name(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _fetch_csv_rows(url: str) -> List[Dict[str, str]]:
    if not url:
        return []
    return _rows_from_csv(_fetch_url(url))


def _fetch_batch_rows(spreadsheet_id: str, api_key: str) -> Dict[str, List[Dict[str, str]]]:
    ranges = [
        ("raw", RAW_RANGE),
        ("derived", DERIVED_RANGE),
        ("candidates", CANDIDATES_RANGE),
        ("trace", TRACE_RANGE),
    ]
    params = [("ranges", sheet_range) for _, sheet_range in ranges]
    params.append(("key", api_key))
    url = f"{SHEETS_API_BASE}/spreadsheets/{spreadsheet_id}/values:batchGet?{urlencode(params)}"
    payload = json.loads(_fetch_url(url))
    value_ranges = payload.get("valueRanges", [])
    result: Dict[str, List[Dict[str, str]]] = {}
    for (key, _), value_range in zip(ranges, value_ranges):
        rows = _rows_from_values(value_range.get("values", []))
        result[key] = rows
    return result


def _load_sheet_rows() -> Dict[str, List[Dict[str, str]]]:
    if SHEETS_MODE == "api_key":
        if not SHEETS_SPREADSHEET_ID or not SHEETS_API_KEY:
            raise RuntimeError("SHEETS_SPREADSHEET_ID and SHEETS_API_KEY are required for api_key mode")
        return _fetch_batch_rows(SHEETS_SPREADSHEET_ID, SHEETS_API_KEY)

    return {
        "raw": _fetch_csv_rows(RAW_CSV_URL),
        "derived": _fetch_csv_rows(DERIVED_CSV_URL),
        "candidates": _fetch_csv_rows(CANDIDATES_CSV_URL),
        "trace": _fetch_csv_rows(TRACE_CSV_URL),
    }


async def _upsert_raw_assets(rows: Iterable[Dict[str, str]]) -> Dict[str, str]:
    rights_map: Dict[str, str] = {}
    async with AsyncSessionLocal() as session:
        for row in rows:
            source_id = row.get("source_id") or row.get("sourceid")
            if not source_id:
                continue
            result = await session.execute(select(RawAsset).where(RawAsset.source_id == source_id))
            asset = result.scalars().first()
            if not asset:
                asset = RawAsset(source_id=source_id, source_url=row.get("source_url") or "", source_type=row.get("source_type") or "video")
                session.add(asset)

            asset.source_url = row.get("source_url") or asset.source_url
            asset.source_type = row.get("source_type") or asset.source_type
            asset.title = row.get("title") or asset.title
            asset.director = row.get("director") or asset.director
            asset.year = _parse_int(row.get("year") or "") or asset.year
            asset.duration_sec = _parse_int(row.get("duration_sec") or "") or asset.duration_sec
            asset.language = row.get("language") or asset.language
            asset.tags = _split_list(row.get("tags") or "") or asset.tags
            asset.scene_ranges = row.get("scene_ranges") or asset.scene_ranges
            asset.notes = row.get("notes") or asset.notes
            asset.rights_status = row.get("rights_status") or asset.rights_status
            asset.created_by = row.get("created_by") or asset.created_by

            rights_map[source_id] = asset.rights_status or ""
        await session.commit()
    return rights_map


async def _upsert_evidence_records(rows: Iterable[Dict[str, str]], rights_map: Dict[str, str]) -> None:
    async with AsyncSessionLocal() as session:
        for row in rows:
            source_id = row.get("source_id")
            if not source_id or rights_map.get(source_id) == "restricted":
                continue
            key = (
                source_id,
                row.get("prompt_version") or "",
                row.get("model_version") or "",
                row.get("output_type") or "",
                row.get("output_language") or "",
            )
            if not all(key):
                continue
            result = await session.execute(
                select(EvidenceRecord).where(
                    EvidenceRecord.source_id == key[0],
                    EvidenceRecord.prompt_version == key[1],
                    EvidenceRecord.model_version == key[2],
                    EvidenceRecord.output_type == key[3],
                    EvidenceRecord.output_language == key[4],
                )
            )
            record = result.scalars().first()
            if not record:
                record = EvidenceRecord(
                    source_id=source_id,
                    summary=row.get("summary") or "",
                    output_type=key[3],
                    output_language=key[4],
                    prompt_version=key[1],
                    model_version=key[2],
                )
                session.add(record)

            record.summary = row.get("summary") or record.summary
            record.style_logic = row.get("style_logic") or record.style_logic
            record.mise_en_scene = row.get("mise_en_scene") or record.mise_en_scene
            record.director_intent = row.get("director_intent") or record.director_intent
            record.labels = _parse_list(row.get("labels") or "") or record.labels
            record.signature_motifs = _parse_list(row.get("signature_motifs") or "") or record.signature_motifs
            record.camera_motion = _parse_dict(row.get("camera_motion") or "") or record.camera_motion
            record.color_palette = _parse_dict(row.get("color_palette") or "") or record.color_palette
            record.pacing = _parse_dict(row.get("pacing") or "") or record.pacing
            record.sound_design = row.get("sound_design") or record.sound_design
            record.editing_rhythm = row.get("editing_rhythm") or record.editing_rhythm
            record.key_patterns = _parse_list(row.get("key_patterns") or "") or record.key_patterns
            record.studio_output_id = row.get("studio_output_id") or record.studio_output_id
            record.adapter = row.get("adapter") or record.adapter
            record.opal_workflow_id = row.get("opal_workflow_id") or record.opal_workflow_id
            record.confidence = _parse_float(row.get("confidence") or "") or record.confidence
            record.notebook_ref = row.get("notebook_ref") or record.notebook_ref
            record.evidence_refs = _parse_list(row.get("evidence_refs") or "") or record.evidence_refs
            record.generated_at = _parse_datetime(row.get("generated_at") or "") or record.generated_at
        await session.commit()


async def _upsert_pattern_candidates(rows: Iterable[Dict[str, str]], rights_map: Dict[str, str]) -> List[PatternCandidate]:
    candidates: List[PatternCandidate] = []
    async with AsyncSessionLocal() as session:
        for row in rows:
            source_id = row.get("source_id")
            if not source_id or rights_map.get(source_id) == "restricted":
                continue
            pattern_name = row.get("pattern_name")
            pattern_type = row.get("pattern_type")
            if not pattern_name or not pattern_type:
                continue
            evidence_ref = row.get("evidence_ref") or ""
            result = await session.execute(
                select(PatternCandidate).where(
                    PatternCandidate.source_id == source_id,
                    PatternCandidate.pattern_name == pattern_name,
                    PatternCandidate.pattern_type == pattern_type,
                    PatternCandidate.evidence_ref == evidence_ref,
                )
            )
            candidate = result.scalars().first()
            if not candidate:
                candidate = PatternCandidate(
                    source_id=source_id,
                    pattern_name=pattern_name,
                    pattern_type=pattern_type,
                    evidence_ref=evidence_ref,
                )
                session.add(candidate)

            candidate.description = row.get("description") or candidate.description
            candidate.weight = _parse_float(row.get("weight") or "") or candidate.weight
            candidate.confidence = _parse_float(row.get("confidence") or "") or candidate.confidence
            candidate.status = row.get("status") or candidate.status or "proposed"
            candidates.append(candidate)
        await session.commit()
    return candidates


async def _promote_patterns(candidates: List[PatternCandidate]) -> Dict[str, uuid.UUID]:
    pattern_map: Dict[str, uuid.UUID] = {}
    async with AsyncSessionLocal() as session:
        for candidate in candidates:
            if candidate.status not in {"validated", "promoted"}:
                continue
            if candidate.status != "promoted":
                if candidate.confidence is not None and candidate.confidence < CONFIDENCE_THRESHOLD:
                    continue
            normalized = _normalize_pattern_name(candidate.pattern_name)
            result = await session.execute(
                select(Pattern).where(
                    Pattern.name == normalized,
                    Pattern.pattern_type == candidate.pattern_type,
                )
            )
            pattern = result.scalars().first()
            if not pattern:
                pattern = Pattern(
                    name=normalized,
                    pattern_type=candidate.pattern_type,
                    description=candidate.description,
                    status="promoted" if candidate.status == "promoted" else "validated",
                )
                session.add(pattern)
            else:
                if candidate.description and not pattern.description:
                    pattern.description = candidate.description
                if candidate.status == "promoted":
                    pattern.status = "promoted"
            pattern_map[f"{normalized}:{candidate.pattern_type}"] = pattern.id
        await session.commit()
    return pattern_map


async def _upsert_pattern_trace(rows: Iterable[Dict[str, str]]) -> None:
    async with AsyncSessionLocal() as session:
        for row in rows:
            source_id = row.get("source_id")
            pattern_id = _parse_uuid(row.get("pattern_id") or "")
            if not source_id or not pattern_id:
                continue
            evidence_ref = row.get("evidence_ref") or ""
            result = await session.execute(
                select(PatternTrace).where(
                    PatternTrace.source_id == source_id,
                    PatternTrace.pattern_id == pattern_id,
                    PatternTrace.evidence_ref == evidence_ref,
                )
            )
            trace = result.scalars().first()
            if not trace:
                trace = PatternTrace(
                    source_id=source_id,
                    pattern_id=pattern_id,
                    evidence_ref=evidence_ref,
                )
                session.add(trace)
            trace.weight = _parse_float(row.get("weight") or "") or trace.weight
        await session.commit()


async def main() -> None:
    sheets = _load_sheet_rows()
    rights_map = await _upsert_raw_assets(sheets.get("raw", []))
    await _upsert_evidence_records(sheets.get("derived", []), rights_map)
    candidates = await _upsert_pattern_candidates(sheets.get("candidates", []), rights_map)
    await _promote_patterns(candidates)
    await _upsert_pattern_trace(sheets.get("trace", []))


if __name__ == "__main__":
    asyncio.run(main())
