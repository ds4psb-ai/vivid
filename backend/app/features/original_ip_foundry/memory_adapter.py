"""OpenClaw-style memory normalization for Foundry."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


_CHARACTER_PATTERN = re.compile(r"@([A-Za-z0-9_\-]{1,32})")
_INTENT_PATTERN = re.compile(r"(?:#intent:|\[intent=)([a-zA-Z0-9_\-]+)\]?")

_MISE_KEYWORDS = {
    "low-angle": "low_angle",
    "low angle": "low_angle",
    "high-angle": "high_angle",
    "high angle": "high_angle",
    "close-up": "close_up",
    "close up": "close_up",
    "long take": "long_take",
    "handheld": "handheld",
    "dolly": "dolly",
    "tracking": "tracking",
    "silhouette": "silhouette",
    "backlight": "backlight",
}


@dataclass
class MemoryEntry:
    project_id: str
    scene_id: str | None
    source_channel: str
    note: str
    attachments: List[str] = field(default_factory=list)
    characters: List[str] = field(default_factory=list)
    intent_tags: List[str] = field(default_factory=list)
    mise_en_scene_tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "scene_id": self.scene_id,
            "source_channel": self.source_channel,
            "note": self.note,
            "attachments": self.attachments,
            "characters": self.characters,
            "intent_tags": self.intent_tags,
            "mise_en_scene_tags": self.mise_en_scene_tags,
            "created_at": self.created_at.isoformat(),
        }


class OpenClawMemoryAdapter:
    """Normalize free-form inspiration into Foundry memory schema."""

    def normalize(
        self,
        *,
        project_id: str,
        scene_id: str | None,
        source_channel: str,
        note: str,
        attachments: List[str] | None = None,
    ) -> MemoryEntry:
        text = note.strip()
        lower = text.lower()

        characters = sorted({token.lower() for token in _CHARACTER_PATTERN.findall(text)})
        intents = sorted({token.lower() for token in _INTENT_PATTERN.findall(text)})

        mise_tags = sorted(
            {
                normalized
                for keyword, normalized in _MISE_KEYWORDS.items()
                if keyword in lower
            }
        )

        if not intents:
            intents = self._infer_intent_tags(lower)

        return MemoryEntry(
            project_id=project_id,
            scene_id=scene_id,
            source_channel=source_channel,
            note=text,
            attachments=list(attachments or []),
            characters=characters,
            intent_tags=intents,
            mise_en_scene_tags=mise_tags,
        )

    def _infer_intent_tags(self, text: str) -> List[str]:
        inferred = []
        if any(k in text for k in ("fear", "panic", "불안", "공포")):
            inferred.append("anxiety")
        if any(k in text for k in ("power", "권력", "압박")):
            inferred.append("power")
        if any(k in text for k in ("intimate", "친밀", "로맨스")):
            inferred.append("intimacy")
        if any(k in text for k in ("lonely", "고독", "외로움")):
            inferred.append("isolation")
        return sorted(set(inferred))


class InMemoryDirectorMemoryStore:
    """Simple project memory store used by Foundry dual-retrieval path."""

    def __init__(self):
        self._items: Dict[str, List[MemoryEntry]] = {}

    def put(self, entry: MemoryEntry) -> None:
        self._items.setdefault(entry.project_id, []).append(entry)

    def search(self, project_id: str, query: str, limit: int = 5) -> List[dict]:
        query_terms = [term for term in query.lower().split() if term]
        items = self._items.get(project_id, [])
        if not items:
            return []

        scored = []
        for entry in reversed(items):
            haystack = " ".join(
                [
                    entry.note.lower(),
                    " ".join(entry.intent_tags),
                    " ".join(entry.characters),
                    " ".join(entry.mise_en_scene_tags),
                ]
            )
            if not query_terms:
                score = 0.0
            else:
                matched = sum(1 for term in query_terms if term in haystack)
                score = matched / max(len(query_terms), 1)
            if score > 0:
                scored.append((score, entry))

        if not scored:
            return [entry.to_dict() for entry in reversed(items[-limit:])]

        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry.to_dict() for _, entry in scored[:limit]]

