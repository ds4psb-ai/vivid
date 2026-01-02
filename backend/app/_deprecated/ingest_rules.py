"""Shared ingest rules and allowlists."""
from __future__ import annotations

import hashlib
import os
import re
from typing import Iterable, List, Optional


GUIDE_TYPE_ALLOWLIST = {
    "summary",
    "homage",
    "variation",
    "template_fit",
    "persona",
    "synapse",
    "story",
    "beat_sheet",
    "storyboard",
    "study_guide",
    "briefing_doc",
    "table",
}
GUIDE_SCOPE_ALLOWLIST = {"auteur", "genre", "format", "creator", "mixed"}
OUTPUT_TYPE_ALLOWLIST = {
    "video_overview",
    "audio_overview",
    "mind_map",
    "report",
    "data_table",
}
PATTERN_TYPE_ALLOWLIST = {"hook", "scene", "subtitle", "audio", "pacing"}
RAW_SOURCE_TYPE_ALLOWLIST = {"video", "image", "doc"}
NOTEBOOK_ASSET_TYPE_ALLOWLIST = {
    "video",
    "image",
    "doc",
    "script",
    "still",
    "scene",
    "segment",
    "link",
}

PATTERN_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
DERIVED_EVIDENCE_REF_RE = re.compile(r"^(sheet:[^:]+:.+|db:[^:]+:.+)$", re.IGNORECASE)

VIDEO_EVIDENCE_REF_PATTERN = os.getenv("VIDEO_EVIDENCE_REF_PATTERN", r"^[a-z][a-z0-9_-]*:.+")
VIDEO_EVIDENCE_REF_RE = re.compile(VIDEO_EVIDENCE_REF_PATTERN, re.IGNORECASE)


def build_segment_id_fallback(
    source_id: Optional[str],
    time_start: Optional[str],
    time_end: Optional[str],
    prompt_version: Optional[str],
    model_version: Optional[str],
) -> Optional[str]:
    parts = [source_id, time_start, time_end, prompt_version, model_version]
    cleaned: list[str] = []
    for part in parts:
        if part is None:
            return None
        if isinstance(part, (int, float)):
            part = str(part)
        if not isinstance(part, str):
            return None
        value = part.strip()
        if not value:
            return None
        cleaned.append(value)
    digest = hashlib.sha1("|".join(cleaned).encode("utf-8")).hexdigest()[:16]
    return f"seg-auto-{digest}"


def ensure_label(labels: Iterable[str], label: str) -> List[str]:
    cleaned = [str(item).strip() for item in labels if str(item).strip()]
    if label not in cleaned:
        cleaned.append(label)
    return cleaned


def has_label(labels: Iterable[str], label: str) -> bool:
    if not label:
        return False
    target = label.strip().lower()
    if not target:
        return False
    for item in labels:
        if not isinstance(item, str):
            continue
        cleaned = item.strip().lower()
        if cleaned and cleaned == target:
            return True
    return False


def is_mega_notebook_notes(notes: Optional[str]) -> bool:
    if not notes:
        return False
    lowered = notes.lower()
    return any(
        token in lowered
        for token in ("mega_notebook", "mega-notebook", "mega notebook", "ops_only", "ops-only")
    )
