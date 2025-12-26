"""Shared helpers for graph metadata."""
from __future__ import annotations

from typing import Iterable, List, Optional


def collect_storyboard_refs(storyboard_cards: Iterable[dict]) -> List[str]:
    refs: List[str] = []
    for idx, card in enumerate(storyboard_cards, start=1):
        raw_ref: Optional[object] = None
        if isinstance(card, dict):
            raw_ref = card.get("shot_id") or card.get("shot") or card.get("id")
        if raw_ref is None:
            raw_ref = idx
        if isinstance(raw_ref, int):
            refs.append(f"shot-{raw_ref:02d}")
        else:
            cleaned = str(raw_ref).strip()
            if cleaned:
                refs.append(cleaned)
    return refs


def merge_graph_meta(graph_data: dict, existing_graph: dict) -> dict:
    if not isinstance(graph_data, dict):
        return graph_data
    meta = graph_data.get("meta")
    if isinstance(meta, dict):
        return graph_data
    existing_meta = existing_graph.get("meta") if isinstance(existing_graph, dict) else None
    if isinstance(existing_meta, dict):
        return {**graph_data, "meta": existing_meta}
    return graph_data
