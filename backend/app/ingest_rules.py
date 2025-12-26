"""Shared ingest rules and allowlists."""
from __future__ import annotations

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
