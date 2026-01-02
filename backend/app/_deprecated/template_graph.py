"""Template graph builder for seeded canvases."""
from __future__ import annotations

from typing import Dict, List, Optional


def build_template_graph(
    capsule_id: str,
    capsule_version: str,
    params: Dict,
    *,
    pattern_version: str,
    story_beats: Optional[List[Dict]] = None,
    storyboard_cards: Optional[List[Dict]] = None,
    meta: Optional[Dict] = None,
    capsule_label: str = "거장 캡슐",
    input_label: str = "스토리 입력",
    input_subtitle: str = "캐릭터, 감정, 배경",
    script_label: str = "스크립트 / 비트",
    script_subtitle: str = "스토리 비트",
    storyboard_label: str = "스토리보드",
    storyboard_subtitle: str = "씬 카드",
    output_label: str = "최종 스펙",
    output_subtitle: str = "프리뷰 페이로드",
) -> Dict:
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
