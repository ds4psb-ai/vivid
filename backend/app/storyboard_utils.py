"""Helpers for normalizing storyboard-derived data."""
from __future__ import annotations

import re
from typing import Any, Iterable, List, Optional


_SHOT_PREFIXES = ("shot-", "shot_")
_DEFAULT_PALETTE = ("#333333", "#555555", "#777777")
_DEFAULT_COMPOSITIONS = ("wide shot", "medium shot", "close-up")


def _extract_int(value: str) -> Optional[int]:
    matches = re.findall(r"\d+", value)
    if not matches:
        return None
    try:
        return int(matches[-1])
    except ValueError:
        return None


def _extract_sequence_label(sequence_id: Optional[str]) -> Optional[str]:
    if not isinstance(sequence_id, str):
        return None
    cleaned = sequence_id.strip()
    if not cleaned:
        return None
    digits = _extract_int(cleaned)
    if digits is None:
        return None
    return f"{digits:02d}"


def build_shot_id(raw_shot: Any, index: int, sequence_id: Optional[str] = None) -> str:
    seq_label = _extract_sequence_label(sequence_id)

    def _format(num: int) -> str:
        if seq_label:
            return f"shot-{seq_label}-{num:02d}"
        return f"shot-{num:02d}"

    if isinstance(raw_shot, int):
        return _format(raw_shot)
    if isinstance(raw_shot, str):
        cleaned = raw_shot.strip()
        if cleaned:
            lowered = cleaned.lower()
            if lowered.startswith(_SHOT_PREFIXES):
                return cleaned
            digits = _extract_int(cleaned)
            if digits is not None:
                return _format(digits)
    return _format(index)


def infer_shot_type(raw_value: Any) -> str:
    if not isinstance(raw_value, str):
        return "medium"
    lowered = raw_value.lower()
    if "wide" in lowered or "establish" in lowered or lowered.startswith("ws"):
        return "wide"
    if "close" in lowered or lowered.startswith("cu"):
        return "close-up"
    if "overhead" in lowered or "top" in lowered:
        return "overhead"
    if "medium" in lowered or lowered.startswith("ms"):
        return "medium"
    return "medium"


def normalize_storyboard_cards(
    cards: Iterable[Any],
    *,
    palette: Optional[Iterable[str]] = None,
    composition_hints: Optional[Iterable[str]] = None,
    sequence_id: Optional[str] = None,
    default_duration: int = 4,
) -> List[dict]:
    if not isinstance(cards, list):
        return []
    palette_items = palette if isinstance(palette, (list, tuple)) else []
    cleaned_palette = [c for c in palette_items if isinstance(c, str) and c.strip()]
    if not cleaned_palette:
        cleaned_palette = list(_DEFAULT_PALETTE)
    composition_items = composition_hints if isinstance(composition_hints, (list, tuple)) else []
    cleaned_compositions = [c for c in composition_items if isinstance(c, str) and c.strip()]
    if not cleaned_compositions:
        cleaned_compositions = list(_DEFAULT_COMPOSITIONS)
    normalized: List[dict] = []
    for idx, card in enumerate(cards, start=1):
        entry = dict(card) if isinstance(card, dict) else {"note": str(card)}
        raw_id = (
            entry.get("shot_id")
            or entry.get("card_id")
            or entry.get("id")
            or entry.get("shot")
            or idx
        )
        shot_id = build_shot_id(raw_id, idx, sequence_id=sequence_id)
        if not entry.get("shot_id"):
            entry["shot_id"] = shot_id

        raw_shot = entry.get("shot_type") or entry.get("shot") or entry.get("composition")
        if not entry.get("shot_type"):
            entry["shot_type"] = infer_shot_type(raw_shot)

        description = entry.get("description") or entry.get("note") or entry.get("summary")
        if not isinstance(description, str) or not description.strip():
            if isinstance(raw_shot, str) and raw_shot.strip():
                description = raw_shot.strip()
            else:
                description = f"Shot {idx}"
        if not entry.get("description"):
            entry["description"] = description
        if not entry.get("note"):
            entry["note"] = description

        if not entry.get("composition"):
            if isinstance(raw_shot, str) and raw_shot.strip():
                entry["composition"] = raw_shot.strip()
            else:
                entry["composition"] = cleaned_compositions[(idx - 1) % len(cleaned_compositions)]

        if not entry.get("dominant_color"):
            entry["dominant_color"] = cleaned_palette[(idx - 1) % len(cleaned_palette)]
        if not entry.get("accent_color"):
            entry["accent_color"] = cleaned_palette[idx % len(cleaned_palette)]

        if not isinstance(entry.get("duration_sec"), (int, float)):
            entry["duration_sec"] = default_duration

        normalized.append(entry)
    return normalized
