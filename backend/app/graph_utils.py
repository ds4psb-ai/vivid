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


def build_template_graph(
    capsule_id: str,
    capsule_version: str,
    params: dict,
    *,
    pattern_version: str,
    story_beats: Optional[List[dict]] = None,
    storyboard_cards: Optional[List[dict]] = None,
    meta: Optional[dict] = None,
    capsule_label: str = "거장 캡슐",
    input_label: str = "스토리 입력",
    input_subtitle: str = "캐릭터, 감정, 배경",
    script_label: str = "스크립트 / 비트",
    script_subtitle: str = "스토리 비트",
    storyboard_label: str = "스토리보드",
    storyboard_subtitle: str = "씬 카드",
    output_label: str = "최종 스펙",
    output_subtitle: str = "프리뷰 페이로드",
) -> dict:
    """Build a simple template graph for seeded canvases.

    Formerly in app._deprecated.template_graph; moved here as non-legacy utility.
    """
    story_beats = story_beats or []
    storyboard_cards = storyboard_cards or []
    nodes = [
        {
            "id": "input-1",
            "type": "input",
            "position": {"x": 80, "y": 220},
            "data": {
                "label": input_label,
                "subtitle": input_subtitle,
            },
        },
        {
            "id": "capsule-1",
            "type": "capsule",
            "position": {"x": 360, "y": 220},
            "data": {
                "label": capsule_label,
                "subtitle": capsule_id,
                "capsuleId": capsule_id,
                "capsuleVersion": capsule_version,
                "patternVersion": pattern_version,
                "params": params,
                "locked": True,
            },
        },
        {
            "id": "script-1",
            "type": "processing",
            "position": {"x": 640, "y": 200},
            "data": {
                "label": script_label,
                "subtitle": script_subtitle,
                "seed": {"story_beats": story_beats},
            },
        },
        {
            "id": "storyboard-1",
            "type": "processing",
            "position": {"x": 880, "y": 200},
            "data": {
                "label": storyboard_label,
                "subtitle": storyboard_subtitle,
                "seed": {"storyboard_cards": storyboard_cards},
            },
        },
        {
            "id": "output-1",
            "type": "output",
            "position": {"x": 1120, "y": 220},
            "data": {
                "label": output_label,
                "subtitle": output_subtitle,
            },
        },
    ]

    edges = [
        {
            "id": "e-input-capsule",
            "source": "input-1",
            "target": "capsule-1",
        },
        {
            "id": "e-capsule-script",
            "source": "capsule-1",
            "target": "script-1",
        },
        {
            "id": "e-script-storyboard",
            "source": "script-1",
            "target": "storyboard-1",
        },
        {
            "id": "e-storyboard-output",
            "source": "storyboard-1",
            "target": "output-1",
        },
    ]

    graph = {"nodes": nodes, "edges": edges}
    if isinstance(meta, dict):
        graph["meta"] = meta
    return graph
