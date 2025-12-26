"""Promote NotebookLM/Opal Sheets data into DB SoR."""
from __future__ import annotations

import asyncio
import csv
import io
import json
import os
import re
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.ingest_rules import (
    DERIVED_EVIDENCE_REF_RE,
    GUIDE_SCOPE_ALLOWLIST,
    GUIDE_TYPE_ALLOWLIST,
    NOTEBOOK_ASSET_TYPE_ALLOWLIST,
    OUTPUT_TYPE_ALLOWLIST,
    PATTERN_NAME_RE,
    PATTERN_TYPE_ALLOWLIST,
    RAW_SOURCE_TYPE_ALLOWLIST,
    VIDEO_EVIDENCE_REF_RE,
    ensure_label,
    is_mega_notebook_notes,
)
from app.models import (
    EvidenceRecord,
    NotebookLibrary,
    NotebookAsset,
    Pattern,
    PatternCandidate,
    PatternTrace,
    PatternVersion,
    CapsuleSpec,
    RawAsset,
    SourcePack,
    VideoSegment,
    Template,
    TemplateVersion,
)


SHEETS_MODE = os.getenv("SHEETS_MODE", "csv").lower()
SHEETS_API_BASE = os.getenv("SHEETS_API_BASE", "https://sheets.googleapis.com/v4")
SHEETS_API_KEY = os.getenv("SHEETS_API_KEY", "")
SHEETS_SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID", "")

NOTEBOOK_CSV_URL = os.getenv("VIVID_NOTEBOOK_LIBRARY_CSV_URL", "")
NOTEBOOK_ASSETS_CSV_URL = os.getenv("VIVID_NOTEBOOK_ASSETS_CSV_URL", "")
RAW_CSV_URL = os.getenv("VIVID_RAW_ASSETS_CSV_URL", "")
VIDEO_STRUCTURED_CSV_URL = os.getenv("VIVID_VIDEO_STRUCTURED_CSV_URL", "")
DERIVED_CSV_URL = os.getenv("VIVID_DERIVED_INSIGHTS_CSV_URL", "")
CANDIDATES_CSV_URL = os.getenv("VIVID_PATTERN_CANDIDATES_CSV_URL", "")
TRACE_CSV_URL = os.getenv("VIVID_PATTERN_TRACE_CSV_URL", "")

NOTEBOOK_RANGE = os.getenv("VIVID_NOTEBOOK_LIBRARY_RANGE", "VIVID_NOTEBOOK_LIBRARY")
NOTEBOOK_ASSETS_RANGE = os.getenv("VIVID_NOTEBOOK_ASSETS_RANGE", "VIVID_NOTEBOOK_ASSETS")
RAW_RANGE = os.getenv("VIVID_RAW_ASSETS_RANGE", "VIVID_RAW_ASSETS")
VIDEO_STRUCTURED_RANGE = os.getenv("VIVID_VIDEO_STRUCTURED_RANGE", "VIVID_VIDEO_STRUCTURED")
DERIVED_RANGE = os.getenv("VIVID_DERIVED_INSIGHTS_RANGE", "VIVID_DERIVED_INSIGHTS")
CANDIDATES_RANGE = os.getenv("VIVID_PATTERN_CANDIDATES_RANGE", "VIVID_PATTERN_CANDIDATES")
TRACE_RANGE = os.getenv("VIVID_PATTERN_TRACE_RANGE", "VIVID_PATTERN_TRACE")
QUARANTINE_RANGE = os.getenv("VIVID_QUARANTINE_RANGE", "VIVID_QUARANTINE")

CONFIDENCE_THRESHOLD = float(os.getenv("PATTERN_CONFIDENCE_THRESHOLD", "0.6"))
SHEETS_RETRY_COUNT = int(os.getenv("SHEETS_RETRY_COUNT", "3"))
SHEETS_RETRY_BASE_SECONDS = float(os.getenv("SHEETS_RETRY_BASE_SECONDS", "0.5"))
QUARANTINE_CSV_PATH = os.getenv("VIVID_QUARANTINE_CSV_PATH", "")
PATTERN_VERSION_RE = re.compile(r"^v(\d+)$", re.IGNORECASE)


def _fetch_url(url: str) -> str:
    if not url:
        raise RuntimeError("Sheet URL is missing")
    if url.startswith("file://"):
        path = url.replace("file://", "", 1)
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    if os.path.exists(url):
        with open(url, "r", encoding="utf-8") as handle:
            return handle.read()
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


def _post_json(url: str, payload: Dict[str, Any]) -> None:
    req = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "User-Agent": "vivid-sheets-sync/1.0",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    last_error: Optional[Exception] = None
    for attempt in range(SHEETS_RETRY_COUNT + 1):
        try:
            with urlopen(req, timeout=30) as response:
                response.read()
                return
        except Exception as exc:
            last_error = exc
            if attempt < SHEETS_RETRY_COUNT:
                time.sleep(SHEETS_RETRY_BASE_SECONDS * (2 ** attempt))
                continue
            raise
    raise last_error or RuntimeError("Failed to post payload")


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


def _parse_story_list(value: str) -> Optional[List[Dict[str, Any]]]:
    if not value:
        return []
    parsed = _parse_json(value)
    if parsed is None:
        return None
    if not isinstance(parsed, list):
        return None
    normalized: List[Dict[str, Any]] = []
    for item in parsed:
        if isinstance(item, dict):
            normalized.append(item)
            continue
        if isinstance(item, str):
            normalized.append({"text": item})
            continue
        return None
    return normalized


def _append_quarantine(
    quarantine: List[Dict[str, str]],
    sheet: str,
    reason: str,
    row: Dict[str, str],
) -> None:
    payload = json.dumps(row, ensure_ascii=True, separators=(",", ":"))
    created_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    quarantine.append(
        {"sheet": sheet, "reason": reason, "row": payload, "created_at": created_at}
    )


def _write_quarantine(quarantine: List[Dict[str, str]]) -> None:
    if not quarantine:
        return
    wrote_any = False
    if QUARANTINE_CSV_PATH:
        with open(QUARANTINE_CSV_PATH, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["sheet", "reason", "row", "created_at"])
            writer.writeheader()
            writer.writerows(quarantine)
        print(f"Wrote quarantine rows: {len(quarantine)} -> {QUARANTINE_CSV_PATH}")
        wrote_any = True
    if SHEETS_MODE == "api_key":
        if not SHEETS_SPREADSHEET_ID or not SHEETS_API_KEY:
            print("Quarantine sheet append skipped: missing SHEETS_SPREADSHEET_ID or SHEETS_API_KEY")
        else:
            params = urlencode(
                {
                    "valueInputOption": "RAW",
                    "insertDataOption": "INSERT_ROWS",
                    "key": SHEETS_API_KEY,
                }
            )
            target = quote(QUARANTINE_RANGE, safe="")
            url = f"{SHEETS_API_BASE}/spreadsheets/{SHEETS_SPREADSHEET_ID}/values/{target}:append?{params}"
            values = [
                [
                    row.get("sheet", ""),
                    row.get("reason", ""),
                    row.get("row", ""),
                    row.get("created_at", ""),
                ]
                for row in quarantine
            ]
            try:
                _post_json(url, {"values": values})
                print(f"Appended quarantine rows: {len(quarantine)} -> {QUARANTINE_RANGE}")
                wrote_any = True
            except Exception as exc:
                print(f"Quarantine sheet append failed: {exc}")
    if not wrote_any:
        print(f"Quarantine rows: {len(quarantine)} (set VIVID_QUARANTINE_CSV_PATH or api_key mode)")


def _parse_list(value: str) -> List[Any]:
    parsed = _parse_json(value)
    if isinstance(parsed, list):
        return parsed
    return _split_list(value)


def _collect_mega_notebook_ids(rows: Iterable[Dict[str, str]]) -> set[str]:
    mega_ids: set[str] = set()
    for row in rows:
        notebook_id = row.get("notebook_id")
        if not notebook_id:
            continue
        notes = row.get("curator_notes") or ""
        if is_mega_notebook_notes(notes):
            mega_ids.add(notebook_id)
    return mega_ids


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
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            from datetime import timezone
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except ValueError:
        return None


def _normalize_source_type(value: str) -> Optional[str]:
    if not value:
        return None
    cleaned = str(value).strip().lower()
    if not cleaned:
        return None
    if "/" in cleaned:
        prefix = cleaned.split("/", 1)[0]
        if prefix in {"text", "application"}:
            cleaned = "doc"
        else:
            cleaned = prefix
    if cleaned in {"text", "application"}:
        cleaned = "doc"
    if cleaned not in RAW_SOURCE_TYPE_ALLOWLIST:
        return None
    return cleaned


def _parse_uuid(value: str) -> Optional[uuid.UUID]:
    if not value:
        return None
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


def _parse_pattern_id(value: str, pattern_map: Dict[str, uuid.UUID]) -> Optional[uuid.UUID]:
    if not value:
        return None
    parsed = _parse_uuid(value)
    if parsed:
        return parsed
    key = value.strip().lower()
    return pattern_map.get(key)


def _normalize_pattern_name(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _normalize_pattern_entry(pattern: Any) -> Optional[Dict[str, str]]:
    if isinstance(pattern, str):
        cleaned = pattern.strip()
        if not cleaned or ":" not in cleaned:
            return None
        name_part, type_part = cleaned.split(":", 1)
        pattern_name = name_part.strip()
        pattern_type = type_part.strip()
        if not pattern_name or not pattern_type:
            return None
        if not PATTERN_NAME_RE.match(pattern_name) or pattern_type not in PATTERN_TYPE_ALLOWLIST:
            return None
        return {
            "pattern_name": pattern_name,
            "pattern_type": pattern_type,
            "description": "",
            "weight": "",
        }
    if isinstance(pattern, dict):
        pattern_name = pattern.get("pattern_name") or pattern.get("name")
        pattern_type = pattern.get("pattern_type") or pattern.get("type")
        if not pattern_name or not pattern_type:
            return None
        pattern_name = str(pattern_name).strip()
        pattern_type = str(pattern_type).strip()
        if not PATTERN_NAME_RE.match(pattern_name) or pattern_type not in PATTERN_TYPE_ALLOWLIST:
            return None
        return {
            "pattern_name": pattern_name,
            "pattern_type": pattern_type,
            "description": str(pattern.get("description") or ""),
            "weight": str(pattern.get("weight") or ""),
        }
    return None


def _parse_key_patterns(value: str) -> Optional[List[Dict[str, str]]]:
    patterns = _parse_list(value)
    if not patterns:
        return []
    normalized: List[Dict[str, str]] = []
    for pattern in patterns:
        entry = _normalize_pattern_entry(pattern)
        if not entry:
            return None
        normalized.append(entry)
    return normalized


def _candidate_base_key(row: Dict[str, str]) -> tuple[str, str, str]:
    source_id = (row.get("source_id") or "").strip()
    pattern_name = row.get("pattern_name") or ""
    pattern_type = (row.get("pattern_type") or "").strip()
    normalized = _normalize_pattern_name(pattern_name) if pattern_name else ""
    return source_id, normalized, pattern_type


def _derive_candidate_rows(rows: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    derived_candidates: List[Dict[str, str]] = []
    for row in rows:
        source_id = (row.get("source_id") or "").strip()
        if not source_id:
            continue
        patterns = _parse_key_patterns(row.get("key_patterns") or "")
        if not patterns:
            continue
        for pattern in patterns:
            derived_candidates.append(
                {
                    "source_id": source_id,
                    "pattern_name": pattern["pattern_name"],
                    "pattern_type": pattern["pattern_type"],
                    "description": pattern.get("description") or "",
                    "weight": pattern.get("weight") or "",
                    "evidence_ref": "",
                    "confidence": str(row.get("confidence") or ""),
                    "status": "proposed",
                }
            )
    return derived_candidates


def _merge_candidate_rows(
    explicit_rows: Iterable[Dict[str, str]],
    derived_rows: Iterable[Dict[str, str]],
) -> List[Dict[str, str]]:
    merged = list(explicit_rows)
    existing = set()
    for row in merged:
        base = _candidate_base_key(row)
        if all(base):
            existing.add(base)
    for row in derived_rows:
        base = _candidate_base_key(row)
        if not all(base):
            continue
        if base in existing:
            continue
        merged.append(row)
        existing.add(base)
    return merged


def _apply_pattern_version_to_graph(graph_data: dict, pattern_version: str) -> Optional[dict]:
    if not isinstance(graph_data, dict):
        return None
    nodes = graph_data.get("nodes")
    if not isinstance(nodes, list):
        return None
    updated = False
    next_nodes = []
    for node in nodes:
        if not isinstance(node, dict):
            next_nodes.append(node)
            continue
        data = node.get("data")
        if not isinstance(data, dict):
            next_nodes.append(node)
            continue
        if data.get("capsuleId") and data.get("capsuleVersion"):
            current = data.get("patternVersion")
            if current != pattern_version:
                patched = {**data, "patternVersion": pattern_version}
                next_nodes.append({**node, "data": patched})
                updated = True
                continue
        next_nodes.append(node)
    if not updated:
        return None
    return {**graph_data, "nodes": next_nodes}


def _fetch_csv_rows(url: str) -> List[Dict[str, str]]:
    if not url:
        return []
    return _rows_from_csv(_fetch_url(url))


def _fetch_batch_rows(spreadsheet_id: str, api_key: str) -> Dict[str, List[Dict[str, str]]]:
    ranges = [
        ("notebooks", NOTEBOOK_RANGE),
        ("notebook_assets", NOTEBOOK_ASSETS_RANGE),
        ("raw", RAW_RANGE),
        ("video_structured", VIDEO_STRUCTURED_RANGE),
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
        "notebooks": _fetch_csv_rows(NOTEBOOK_CSV_URL),
        "notebook_assets": _fetch_csv_rows(NOTEBOOK_ASSETS_CSV_URL),
        "raw": _fetch_csv_rows(RAW_CSV_URL),
        "video_structured": _fetch_csv_rows(VIDEO_STRUCTURED_CSV_URL),
        "derived": _fetch_csv_rows(DERIVED_CSV_URL),
        "candidates": _fetch_csv_rows(CANDIDATES_CSV_URL),
        "trace": _fetch_csv_rows(TRACE_CSV_URL),
    }


async def _upsert_notebook_library(
    rows: Iterable[Dict[str, str]],
    quarantine: List[Dict[str, str]],
) -> None:
    async with AsyncSessionLocal() as session:
        for row in rows:
            notebook_id = row.get("notebook_id")
            if not notebook_id:
                _append_quarantine(quarantine, "VIVID_NOTEBOOK_LIBRARY", "missing_notebook_id", row)
                continue
            result = await session.execute(
                select(NotebookLibrary).where(NotebookLibrary.notebook_id == notebook_id)
            )
            record = result.scalars().first()
            if not record:
                record = NotebookLibrary(
                    notebook_id=notebook_id,
                    title=row.get("title") or "",
                    notebook_ref=row.get("notebook_ref") or "",
                )
                session.add(record)

            record.title = row.get("title") or record.title
            record.notebook_ref = row.get("notebook_ref") or record.notebook_ref
            record.owner_id = row.get("owner_id") or record.owner_id
            record.cluster_id = row.get("cluster_id") or record.cluster_id
            record.cluster_label = row.get("cluster_label") or record.cluster_label
            record.cluster_tags = _split_list(row.get("cluster_tags") or "") or record.cluster_tags
            guide_scope = row.get("guide_scope") or ""
            if guide_scope and guide_scope not in GUIDE_SCOPE_ALLOWLIST:
                _append_quarantine(quarantine, "VIVID_NOTEBOOK_LIBRARY", "invalid_guide_scope", row)
                continue
            record.guide_scope = guide_scope or record.guide_scope
            record.source_ids = _split_list(row.get("source_ids") or "") or record.source_ids
            record.source_count = _parse_int(row.get("source_count") or "") or record.source_count
            record.curator_notes = row.get("curator_notes") or record.curator_notes
            record.created_at = _parse_datetime(row.get("created_at") or "") or record.created_at
            record.updated_at = _parse_datetime(row.get("updated_at") or "") or record.updated_at

        await session.commit()


async def _upsert_notebook_assets(
    rows: Iterable[Dict[str, str]],
    quarantine: List[Dict[str, str]],
) -> None:
    async with AsyncSessionLocal() as session:
        for row in rows:
            notebook_id = (row.get("notebook_id") or "").strip()
            asset_id = (row.get("asset_id") or "").strip()
            asset_type = (row.get("asset_type") or "").strip().lower()
            if not notebook_id or not asset_id or not asset_type:
                _append_quarantine(quarantine, "VIVID_NOTEBOOK_ASSETS", "missing_asset_fields", row)
                continue
            if asset_type not in NOTEBOOK_ASSET_TYPE_ALLOWLIST:
                _append_quarantine(quarantine, "VIVID_NOTEBOOK_ASSETS", "invalid_asset_type", row)
                continue

            result = await session.execute(
                select(NotebookAsset).where(
                    NotebookAsset.notebook_id == notebook_id,
                    NotebookAsset.asset_id == asset_id,
                    NotebookAsset.asset_type == asset_type,
                )
            )
            record = result.scalars().first()
            if not record:
                record = NotebookAsset(
                    notebook_id=notebook_id,
                    asset_id=asset_id,
                    asset_type=asset_type,
                )
                session.add(record)

            record.asset_ref = row.get("asset_ref") or record.asset_ref
            record.title = row.get("title") or record.title
            tags = _split_list(row.get("tags") or "")
            if tags:
                record.tags = tags
            record.notes = row.get("notes") or record.notes

        await session.commit()


async def _upsert_raw_assets(
    rows: Iterable[Dict[str, str]],
    quarantine: List[Dict[str, str]],
) -> Dict[str, str]:
    rights_map: Dict[str, str] = {}
    async with AsyncSessionLocal() as session:
        for row in rows:
            source_id = row.get("source_id") or row.get("sourceid")
            if not source_id:
                _append_quarantine(quarantine, "VIVID_RAW_ASSETS", "missing_source_id", row)
                continue
            result = await session.execute(select(RawAsset).where(RawAsset.source_id == source_id))
            asset = result.scalars().first()
            if not asset:
                asset = RawAsset(
                    source_id=source_id,
                    source_url=row.get("source_url") or "",
                    source_type="video",
                )
                session.add(asset)

            asset.source_url = row.get("source_url") or asset.source_url
            raw_source_type = row.get("source_type") or asset.source_type or "video"
            normalized_type = _normalize_source_type(raw_source_type)
            if not normalized_type:
                _append_quarantine(quarantine, "VIVID_RAW_ASSETS", "invalid_source_type", row)
                continue
            asset.source_type = normalized_type
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


async def _upsert_video_segments(
    rows: Iterable[Dict[str, str]],
    rights_map: Dict[str, str],
    quarantine: List[Dict[str, str]],
) -> None:
    async with AsyncSessionLocal() as session:
        for row in rows:
            segment_id = row.get("segment_id")
            source_id = row.get("source_id")
            work_id = row.get("work_id") or row.get("workId")
            scene_id = row.get("scene_id") or row.get("sceneId")
            shot_id = row.get("shot_id") or row.get("shotId")
            sequence_id = row.get("sequence_id") or row.get("sequenceId")
            time_start = row.get("time_start")
            time_end = row.get("time_end")
            missing_fields = []
            if not segment_id:
                missing_fields.append("segment_id")
            if not source_id:
                missing_fields.append("source_id")
            if not work_id:
                missing_fields.append("work_id")
            if not scene_id:
                missing_fields.append("scene_id")
            if not shot_id:
                missing_fields.append("shot_id")
            if not time_start:
                missing_fields.append("time_start")
            if not time_end:
                missing_fields.append("time_end")
            if missing_fields:
                reason = "missing_video_required_fields:" + ",".join(missing_fields)
                _append_quarantine(quarantine, "VIVID_VIDEO_STRUCTURED", reason, row)
                continue
            if rights_map.get(source_id) == "restricted":
                _append_quarantine(quarantine, "VIVID_VIDEO_STRUCTURED", "restricted_rights", row)
                continue

            result = await session.execute(
                select(VideoSegment).where(VideoSegment.segment_id == segment_id)
            )
            segment = result.scalars().first()
            if not segment:
                segment = VideoSegment(
                    segment_id=segment_id,
                    source_id=source_id,
                    work_id=work_id,
                    sequence_id=sequence_id,
                    scene_id=scene_id,
                    shot_id=shot_id,
                    time_start=time_start,
                    time_end=time_end,
                    prompt_version=row.get("prompt_version") or "",
                    model_version=row.get("model_version") or "",
                )
                session.add(segment)

            segment.source_id = source_id
            segment.work_id = work_id
            segment.sequence_id = sequence_id or segment.sequence_id
            segment.scene_id = scene_id
            segment.shot_id = shot_id
            segment.time_start = time_start
            segment.time_end = time_end
            segment.shot_index = _parse_int(row.get("shot_index") or "") or segment.shot_index
            segment.keyframes = _parse_list(row.get("keyframes") or "") or segment.keyframes
            segment.transcript = row.get("transcript") or segment.transcript
            segment.visual_schema = _parse_dict(row.get("visual_schema_json") or "") or segment.visual_schema
            segment.audio_schema = _parse_dict(row.get("audio_schema_json") or "") or segment.audio_schema
            segment.motifs = _parse_list(row.get("motifs") or "") or segment.motifs
            evidence_refs = _parse_list(row.get("evidence_refs") or "")
            if evidence_refs:
                invalid_refs = [
                    ref for ref in evidence_refs if not VIDEO_EVIDENCE_REF_RE.match(ref)
                ]
                if invalid_refs:
                    _append_quarantine(
                        quarantine,
                        "VIVID_VIDEO_STRUCTURED",
                        "invalid_video_evidence_refs",
                        row,
                    )
                    continue
                segment.evidence_refs = evidence_refs
            segment.confidence = _parse_float(row.get("confidence") or "") or segment.confidence
            segment.prompt_version = row.get("prompt_version") or segment.prompt_version
            segment.model_version = row.get("model_version") or segment.model_version
            segment.generated_at = _parse_datetime(row.get("generated_at") or "") or segment.generated_at

        await session.commit()


async def _upsert_evidence_records(
    rows: Iterable[Dict[str, str]],
    rights_map: Dict[str, str],
    quarantine: List[Dict[str, str]],
    mega_notebook_ids: Optional[set[str]] = None,
) -> None:
    mega_notebook_ids = mega_notebook_ids or set()
    async with AsyncSessionLocal() as session:
        for row in rows:
            source_id = row.get("source_id")
            if not source_id or rights_map.get(source_id) == "restricted":
                reason = "missing_source_id" if not source_id else "restricted_rights"
                _append_quarantine(quarantine, "VIVID_DERIVED_INSIGHTS", reason, row)
                continue
            source_pack_id = row.get("source_pack_id") or row.get("sourcePackId") or ""
            if not source_pack_id:
                _append_quarantine(quarantine, "VIVID_DERIVED_INSIGHTS", "missing_source_pack_id", row)
                continue
            pack_result = await session.execute(
                select(SourcePack).where(SourcePack.pack_id == source_pack_id)
            )
            if not pack_result.scalars().first():
                _append_quarantine(quarantine, "VIVID_DERIVED_INSIGHTS", "unknown_source_pack_id", row)
                continue
            key = (
                source_id,
                row.get("prompt_version") or "",
                row.get("model_version") or "",
                row.get("output_type") or "",
                row.get("output_language") or "",
            )
            if not all(key):
                _append_quarantine(quarantine, "VIVID_DERIVED_INSIGHTS", "missing_evidence_key", row)
                continue
            if key[3] not in OUTPUT_TYPE_ALLOWLIST:
                _append_quarantine(quarantine, "VIVID_DERIVED_INSIGHTS", "invalid_output_type", row)
                continue
            guide_type = row.get("guide_type") or ""
            if guide_type and guide_type not in GUIDE_TYPE_ALLOWLIST:
                _append_quarantine(quarantine, "VIVID_DERIVED_INSIGHTS", "invalid_guide_type", row)
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
                    source_pack_id=source_pack_id,
                )
                session.add(record)

            record.summary = row.get("summary") or record.summary
            record.guide_type = row.get("guide_type") or record.guide_type
            record.homage_guide = row.get("homage_guide") or record.homage_guide
            record.variation_guide = row.get("variation_guide") or record.variation_guide
            record.template_recommendations = (
                _parse_list(row.get("template_recommendations") or "")
                or record.template_recommendations
            )
            record.user_fit_notes = row.get("user_fit_notes") or record.user_fit_notes
            record.persona_profile = row.get("persona_profile") or record.persona_profile
            record.synapse_logic = row.get("synapse_logic") or record.synapse_logic
            record.origin_notebook_id = row.get("origin_notebook_id") or record.origin_notebook_id
            record.filter_notebook_id = row.get("filter_notebook_id") or record.filter_notebook_id
            record.cluster_id = row.get("cluster_id") or record.cluster_id
            record.cluster_label = row.get("cluster_label") or record.cluster_label
            record.cluster_confidence = _parse_float(row.get("cluster_confidence") or "") or record.cluster_confidence
            record.style_logic = row.get("style_logic") or record.style_logic
            record.mise_en_scene = row.get("mise_en_scene") or record.mise_en_scene
            record.director_intent = row.get("director_intent") or record.director_intent
            labels = _parse_list(row.get("labels") or "")
            notebook_id = row.get("notebook_id") or ""
            if notebook_id and notebook_id in mega_notebook_ids:
                labels = ensure_label(labels, "ops_only")
            record.labels = labels or record.labels
            record.signature_motifs = _parse_list(row.get("signature_motifs") or "") or record.signature_motifs
            record.camera_motion = _parse_dict(row.get("camera_motion") or "") or record.camera_motion
            record.color_palette = _parse_dict(row.get("color_palette") or "") or record.color_palette
            record.pacing = _parse_dict(row.get("pacing") or "") or record.pacing
            record.sound_design = row.get("sound_design") or record.sound_design
            record.editing_rhythm = row.get("editing_rhythm") or record.editing_rhythm
            raw_story_beats = row.get("story_beats") or ""
            parsed_story_beats = _parse_story_list(raw_story_beats)
            if parsed_story_beats is None:
                _append_quarantine(
                    quarantine,
                    "VIVID_DERIVED_INSIGHTS",
                    "invalid_story_beats",
                    row,
                )
                continue
            if parsed_story_beats:
                record.story_beats = parsed_story_beats
            raw_storyboard_cards = row.get("storyboard_cards") or ""
            parsed_storyboard_cards = _parse_story_list(raw_storyboard_cards)
            if parsed_storyboard_cards is None:
                _append_quarantine(
                    quarantine,
                    "VIVID_DERIVED_INSIGHTS",
                    "invalid_storyboard_cards",
                    row,
                )
                continue
            if parsed_storyboard_cards:
                record.storyboard_cards = parsed_storyboard_cards
            raw_key_patterns = row.get("key_patterns") or ""
            parsed_key_patterns = _parse_key_patterns(raw_key_patterns)
            if parsed_key_patterns is None:
                _append_quarantine(
                    quarantine,
                    "VIVID_DERIVED_INSIGHTS",
                    "invalid_key_patterns",
                    row,
                )
                continue
            if parsed_key_patterns:
                record.key_patterns = parsed_key_patterns
            record.studio_output_id = row.get("studio_output_id") or record.studio_output_id
            record.adapter = row.get("adapter") or record.adapter
            record.opal_workflow_id = row.get("opal_workflow_id") or record.opal_workflow_id
            record.confidence = _parse_float(row.get("confidence") or "") or record.confidence
            record.notebook_id = row.get("notebook_id") or record.notebook_id
            record.notebook_ref = row.get("notebook_ref") or record.notebook_ref
            record.source_pack_id = source_pack_id or record.source_pack_id
            evidence_refs = _parse_list(row.get("evidence_refs") or "")
            if evidence_refs:
                invalid_refs = [
                    ref for ref in evidence_refs if not DERIVED_EVIDENCE_REF_RE.match(ref)
                ]
                if invalid_refs:
                    _append_quarantine(
                        quarantine,
                        "VIVID_DERIVED_INSIGHTS",
                        "invalid_evidence_refs",
                        row,
                    )
                    continue
                record.evidence_refs = evidence_refs
            record.generated_at = _parse_datetime(row.get("generated_at") or "") or record.generated_at
        await session.commit()


async def _upsert_pattern_candidates(
    rows: Iterable[Dict[str, str]],
    rights_map: Dict[str, str],
    quarantine: List[Dict[str, str]],
) -> List[PatternCandidate]:
    candidates: List[PatternCandidate] = []
    async with AsyncSessionLocal() as session:
        for row in rows:
            source_id = row.get("source_id")
            if not source_id or rights_map.get(source_id) == "restricted":
                reason = "missing_source_id" if not source_id else "restricted_rights"
                _append_quarantine(quarantine, "VIVID_PATTERN_CANDIDATES", reason, row)
                continue
            pattern_name = row.get("pattern_name")
            pattern_type = row.get("pattern_type")
            if not pattern_name or not pattern_type:
                _append_quarantine(quarantine, "VIVID_PATTERN_CANDIDATES", "missing_pattern_fields", row)
                continue
            cleaned_name = pattern_name.strip()
            cleaned_type = pattern_type.strip()
            if not PATTERN_NAME_RE.match(cleaned_name):
                _append_quarantine(quarantine, "VIVID_PATTERN_CANDIDATES", "invalid_pattern_name", row)
                continue
            if cleaned_type not in PATTERN_TYPE_ALLOWLIST:
                _append_quarantine(quarantine, "VIVID_PATTERN_CANDIDATES", "invalid_pattern_type", row)
                continue
            evidence_ref = row.get("evidence_ref") or ""
            if evidence_ref and not VIDEO_EVIDENCE_REF_RE.match(evidence_ref):
                _append_quarantine(
                    quarantine,
                    "VIVID_PATTERN_CANDIDATES",
                    "invalid_evidence_ref",
                    row,
                )
                continue
            result = await session.execute(
                select(PatternCandidate).where(
                    PatternCandidate.source_id == source_id,
                    PatternCandidate.pattern_name == cleaned_name,
                    PatternCandidate.pattern_type == cleaned_type,
                    PatternCandidate.evidence_ref == evidence_ref,
                )
            )
            candidate = result.scalars().first()
            if not candidate:
                candidate = PatternCandidate(
                    source_id=source_id,
                    pattern_name=cleaned_name,
                    pattern_type=cleaned_type,
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
    changed = False
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
                await session.flush()
                changed = True
            else:
                if candidate.description and not pattern.description:
                    pattern.description = candidate.description
                    changed = True
                if candidate.status == "promoted":
                    if pattern.status != "promoted":
                        pattern.status = "promoted"
                        changed = True
            pattern_map[f"{normalized}:{candidate.pattern_type}"] = pattern.id
        await session.commit()
    return pattern_map, changed


async def _upsert_pattern_trace(
    rows: Iterable[Dict[str, str]],
    pattern_map: Dict[str, uuid.UUID],
    rights_map: Dict[str, str],
    quarantine: List[Dict[str, str]],
 ) -> bool:
    changed = False
    async with AsyncSessionLocal() as session:
        for row in rows:
            source_id = row.get("source_id")
            pattern_id = _parse_pattern_id(row.get("pattern_id") or "", pattern_map)
            if not source_id or not pattern_id:
                reason = "missing_source_id" if not source_id else "pattern_id_unresolved"
                _append_quarantine(quarantine, "VIVID_PATTERN_TRACE", reason, row)
                continue
            if rights_map.get(source_id) == "restricted":
                _append_quarantine(quarantine, "VIVID_PATTERN_TRACE", "restricted_rights", row)
                continue
            evidence_ref = row.get("evidence_ref") or ""
            if evidence_ref and not VIDEO_EVIDENCE_REF_RE.match(evidence_ref):
                _append_quarantine(
                    quarantine,
                    "VIVID_PATTERN_TRACE",
                    "invalid_evidence_ref",
                    row,
                )
                continue
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
                changed = True
            parsed_weight = _parse_float(row.get("weight") or "")
            if parsed_weight is not None:
                if trace.weight != parsed_weight:
                    trace.weight = parsed_weight
                    changed = True
        await session.commit()
    return changed


def _next_pattern_version(current: Optional[str]) -> str:
    if not current:
        return "v1"
    match = PATTERN_VERSION_RE.match(current.strip())
    if not match:
        return "v1"
    return f"v{int(match.group(1)) + 1}"


async def _bump_pattern_version(note: str) -> str:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PatternVersion).order_by(PatternVersion.created_at.desc()).limit(1)
        )
        latest = result.scalars().first()
        next_version = _next_pattern_version(latest.version if latest else None)
        snapshot = PatternVersion(version=next_version, note=note)
        session.add(snapshot)
        await session.commit()
        return next_version


async def _update_capsule_specs(pattern_version: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(CapsuleSpec))
        specs = result.scalars().all()
        for spec in specs:
            payload = spec.spec or {}
            current = payload.get("patternVersion") or payload.get("pattern_version")
            if current == pattern_version:
                continue
            payload["patternVersion"] = pattern_version
            spec.spec = payload
        await session.commit()


async def _update_template_versions(pattern_version: str, note: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Template))
        templates = result.scalars().all()
        for template in templates:
            updated_graph = _apply_pattern_version_to_graph(
                template.graph_data or {}, pattern_version
            )
            if not updated_graph:
                continue
            template.graph_data = updated_graph
            template.version = (template.version or 1) + 1
            session.add(
                TemplateVersion(
                    template_id=template.id,
                    version=template.version,
                    graph_data=updated_graph,
                    notes=note,
                    creator_id=template.creator_id,
                )
            )
        await session.commit()

async def main() -> None:
    quarantine: List[Dict[str, str]] = []
    sheets = _load_sheet_rows()
    notebook_rows = sheets.get("notebooks", [])
    notebook_asset_rows = sheets.get("notebook_assets", [])
    raw_rows = sheets.get("raw", [])
    video_rows = sheets.get("video_structured", [])
    derived_rows = sheets.get("derived", [])
    candidate_rows = sheets.get("candidates", [])
    trace_rows = sheets.get("trace", [])

    mega_notebook_ids = _collect_mega_notebook_ids(notebook_rows)
    await _upsert_notebook_library(notebook_rows, quarantine)
    await _upsert_notebook_assets(notebook_asset_rows, quarantine)
    rights_map = await _upsert_raw_assets(raw_rows, quarantine)
    await _upsert_video_segments(video_rows, rights_map, quarantine)
    await _upsert_evidence_records(derived_rows, rights_map, quarantine, mega_notebook_ids)
    derived_candidates = _derive_candidate_rows(derived_rows)
    merged_candidates = _merge_candidate_rows(candidate_rows, derived_candidates)
    candidates = await _upsert_pattern_candidates(merged_candidates, rights_map, quarantine)
    pattern_map, pattern_changed = await _promote_patterns(candidates)
    trace_changed = await _upsert_pattern_trace(trace_rows, pattern_map, rights_map, quarantine)
    if pattern_changed or trace_changed:
        note = f"auto-promotion {datetime.utcnow().isoformat()}Z"
        next_version = await _bump_pattern_version(note)
        await _update_capsule_specs(next_version)
        await _update_template_versions(next_version, f"{note} (patternVersion)")
    _write_quarantine(quarantine)


if __name__ == "__main__":
    asyncio.run(main())
