"""Fixture data for auteur templates."""
from __future__ import annotations

from typing import Dict, List


def build_graph(capsule_id: str, capsule_version: str, params: Dict) -> Dict:
    nodes = [
        {
            "id": "input-1",
            "type": "input",
            "position": {"x": 80, "y": 220},
            "data": {
                "label": "Story Inputs",
                "subtitle": "character, emotion, setting",
            },
        },
        {
            "id": "capsule-1",
            "type": "capsule",
            "position": {"x": 360, "y": 220},
            "data": {
                "label": "Auteur Capsule",
                "subtitle": capsule_id,
                "capsuleId": capsule_id,
                "capsuleVersion": capsule_version,
                "params": params,
                "locked": True,
            },
        },
        {
            "id": "output-1",
            "type": "output",
            "position": {"x": 640, "y": 220},
            "data": {
                "label": "Final Spec",
                "subtitle": "preview payload",
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
            "id": "e-capsule-output",
            "source": "capsule-1",
            "target": "output-1",
        },
    ]

    return {"nodes": nodes, "edges": edges}


TEMPLATES: List[Dict] = [
    {
        "slug": "tmpl-auteur-bong",
        "title": "Structural Tension",
        "description": "Precise blocking with sudden genre shifts.",
        "tags": ["thriller", "satire", "dynamic"],
        "preview_video_url": "/images/templates/bong_tension.png",
        "graph_data": build_graph(
            "auteur.bong-joon-ho",
            "1.0.0",
            {
                "style_intensity": 0.7,
                "pacing": "medium",
                "color_bias": "cool",
                "camera_motion": "controlled",
                "tension_bias": 0.7,
            },
        ),
    },
    {
        "slug": "tmpl-auteur-park",
        "title": "Symmetric Noir",
        "description": "Obsessive symmetry and high-contrast vengeance.",
        "tags": ["noir", "vivid", "stylized"],
        "preview_video_url": "/images/templates/park_symmetry.png",
        "graph_data": build_graph(
            "auteur.park-chan-wook",
            "1.0.0",
            {
                "style_intensity": 0.75,
                "pacing": "medium",
                "color_bias": "warm",
                "camera_motion": "controlled",
                "symmetry_bias": 0.8,
            },
        ),
    },
    {
        "slug": "tmpl-auteur-shinkai",
        "title": "Luminous Sky",
        "description": "Hyper-realistic light, clouds, and emotional longing.",
        "tags": ["anime", "romance", "scenic"],
        "preview_video_url": "/images/templates/shinkai_sky.png",
        "graph_data": build_graph(
            "auteur.shinkai",
            "1.0.0",
            {
                "style_intensity": 0.7,
                "pacing": "slow",
                "color_bias": "warm",
                "camera_motion": "controlled",
                "light_diffusion": 0.75,
            },
        ),
    },
    {
        "slug": "tmpl-auteur-leejunho",
        "title": "Stage Rhythm",
        "description": "Music-synced cuts and performance-driven energy.",
        "tags": ["music", "pop", "performance"],
        "preview_video_url": "/images/templates/lee_rhythm.png",
        "graph_data": build_graph(
            "auteur.lee-junho",
            "1.0.0",
            {
                "style_intensity": 0.68,
                "pacing": "medium",
                "color_bias": "neutral",
                "camera_motion": "dynamic",
                "music_sync": 0.7,
            },
        ),
    },
    {
        "slug": "tmpl-auteur-na",
        "title": "Gritty Pursuit",
        "description": "Relentless handheld camera and raw chaos.",
        "tags": ["action", "chase", "raw"],
        "preview_video_url": "/images/templates/na_chase.png",
        "graph_data": build_graph(
            "auteur.na-hongjin",
            "1.0.0",
            {
                "style_intensity": 0.8,
                "pacing": "fast",
                "color_bias": "cool",
                "camera_motion": "dynamic",
                "chaos_bias": 0.8,
            },
        ),
    },
    {
        "slug": "tmpl-auteur-hong",
        "title": "Static Conversation",
        "description": "Long takes, awkward pauses, and sudden zooms.",
        "tags": ["drama", "minimal", "dialogue"],
        "preview_video_url": "/images/templates/hong_static.png",
        "graph_data": build_graph(
            "auteur.hong-sangsoo",
            "1.0.0",
            {
                "style_intensity": 0.65,
                "pacing": "slow",
                "color_bias": "neutral",
                "camera_motion": "static",
                "stillness": 0.85,
            },
        ),
    },
]
