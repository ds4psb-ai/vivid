"""Normalize narrative seed payloads for derived outputs."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


_DEFAULT_SHOTS = ("wide shot", "medium shot", "close-up")


def _coerce_text(value: Any) -> Optional[str]:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    if isinstance(value, (int, float)):
        return str(value)
    return None


def _pick_text(entry: Dict[str, Any], keys: Iterable[str]) -> Optional[str]:
    for key in keys:
        text = _coerce_text(entry.get(key))
        if text:
            return text
    return None


def normalize_story_beats(beats: Any) -> List[Dict[str, Any]]:
    if not isinstance(beats, list):
        return []
    normalized: List[Dict[str, Any]] = []
    for idx, item in enumerate(beats, start=1):
        if isinstance(item, dict):
            entry = dict(item)
            summary = _pick_text(entry, ("summary", "note", "text", "description"))
            if not summary:
                summary = _pick_text(entry, ("beat", "beat_id", "id")) or f"Beat {idx}"
            entry.setdefault("beat_id", f"b{idx}")
            if not _coerce_text(entry.get("beat_id")):
                entry["beat_id"] = f"b{idx}"
            entry["summary"] = summary
            tension = _coerce_text(entry.get("tension"))
            tension = tension.lower() if tension else "medium"
            entry["tension"] = tension if tension in {"low", "medium", "high"} else "medium"
            normalized.append(entry)
            continue
        if isinstance(item, str):
            cleaned = item.strip()
            if cleaned:
                normalized.append(
                    {"beat_id": f"b{idx}", "summary": cleaned, "tension": "medium"}
                )
    return normalized


def normalize_storyboard_cards(cards: Any) -> List[Dict[str, Any]]:
    if not isinstance(cards, list):
        return []
    normalized: List[Dict[str, Any]] = []
    for idx, item in enumerate(cards, start=1):
        if isinstance(item, dict):
            entry = dict(item)
            card_id = _pick_text(entry, ("card_id", "id"))
            if not card_id:
                card_id = f"c{idx}"
            entry["card_id"] = card_id
            note = _pick_text(entry, ("note", "description", "summary", "text"))
            shot = _pick_text(entry, ("shot", "composition", "shot_type"))
            if not shot:
                shot = _DEFAULT_SHOTS[(idx - 1) % len(_DEFAULT_SHOTS)]
            if not note:
                note = shot if shot else f"Shot {idx}"
            entry["shot"] = shot
            entry["note"] = note
            normalized.append(entry)
            continue
        if isinstance(item, str):
            cleaned = item.strip()
            if cleaned:
                normalized.append(
                    {
                        "card_id": f"c{idx}",
                        "shot": _DEFAULT_SHOTS[(idx - 1) % len(_DEFAULT_SHOTS)],
                        "note": cleaned,
                    }
                )
    return normalized
