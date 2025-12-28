"""Shared helpers for graph metadata."""
from __future__ import annotations

from typing import Iterable, List, Optional

from app.storyboard_utils import build_shot_id


def collect_storyboard_refs(storyboard_cards: Iterable[dict]) -> List[str]:
    refs: List[str] = []
    for idx, card in enumerate(storyboard_cards, start=1):
        raw_ref: Optional[object] = None
        if isinstance(card, dict):
            raw_ref = (
                card.get("shot_id")
                or card.get("card_id")
                or card.get("id")
                or card.get("shot")
            )
        if raw_ref is None:
            raw_ref = idx
        refs.append(build_shot_id(raw_ref, idx))
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


def ensure_pattern_version(graph_data: dict, pattern_version: str) -> dict:
    """Attach patternVersion to capsule nodes if missing."""
    if not isinstance(graph_data, dict):
        return graph_data

    nodes = graph_data.get("nodes")
    if not isinstance(nodes, list):
        return graph_data

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
        if data.get("patternVersion"):
            next_nodes.append(node)
            continue
        if data.get("capsuleId") and data.get("capsuleVersion"):
            patched = {**data, "patternVersion": pattern_version}
            next_nodes.append({**node, "data": patched})
            updated = True
        else:
            next_nodes.append(node)

    if not updated:
        return graph_data

    return {**graph_data, "nodes": next_nodes}
