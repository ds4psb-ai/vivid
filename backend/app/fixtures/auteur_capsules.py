"""Fixture data for auteur capsule specs."""
from __future__ import annotations

import copy

COMMON_INPUTS = {
    "emotion_curve": {"type": "float[]", "required": True},
    "scene_summary": {"type": "string", "required": True},
    "duration_sec": {"type": "number", "required": True},
}

COMMON_OUTPUTS = {
    "style_vector": {"type": "float[]"},
    "palette": {"type": "string[]"},
    "composition_hints": {"type": "string[]"},
    "pacing_hints": {"type": "string[]"},
}

COMMON_PARAM_DEFS = {
    "style_intensity": {"type": "number", "min": 0.4, "max": 1.0, "step": 0.05},
    "pacing": {"type": "enum", "options": ["slow", "medium", "fast"]},
    "color_bias": {"type": "enum", "options": ["cool", "neutral", "warm"]},
    "camera_motion": {"type": "enum", "options": ["static", "controlled", "dynamic"]},
}

POLICY = {"evidence": "summary_only", "allowRawLogs": False}


def build_exposed_params(defaults: dict, signature: dict) -> dict:
    exposed = copy.deepcopy(COMMON_PARAM_DEFS)
    for key, value in defaults.items():
        exposed[key]["default"] = value
        exposed[key]["visibility"] = "public"
    for key, value in signature.items():
        exposed[key] = {
            "type": "number",
            "min": 0.0,
            "max": 1.0,
            "step": 0.1,
            "default": value,
            "visibility": "public",
        }
    return exposed


CAPSULE_SPECS = [
    {
        "capsule_key": "auteur.bong-joon-ho",
        "version": "1.0.0",
        "display_name": "Bong Joon-ho Style Capsule",
        "description": "Structured tension and genre-mixing rhythms.",
        "spec": {
            "inputs": COMMON_INPUTS,
            "outputs": COMMON_OUTPUTS,
            "exposedParams": build_exposed_params(
                {
                    "style_intensity": 0.7,
                    "pacing": "medium",
                    "color_bias": "cool",
                    "camera_motion": "controlled",
                },
                {"tension_bias": 0.7},
            ),
            "policy": POLICY,
            "adapter": {
                "type": "hybrid",
                "internalGraphRef": "private-dag://auteur/bong/v1",
            },
        },
    },
    {
        "capsule_key": "auteur.park-chan-wook",
        "version": "1.0.0",
        "display_name": "Park Chan-wook Style Capsule",
        "description": "Symmetry-driven mise-en-scene and bold contrast.",
        "spec": {
            "inputs": COMMON_INPUTS,
            "outputs": COMMON_OUTPUTS,
            "exposedParams": build_exposed_params(
                {
                    "style_intensity": 0.75,
                    "pacing": "medium",
                    "color_bias": "warm",
                    "camera_motion": "controlled",
                },
                {"symmetry_bias": 0.8},
            ),
            "policy": POLICY,
            "adapter": {
                "type": "hybrid",
                "internalGraphRef": "private-dag://auteur/park/v1",
            },
        },
    },
    {
        "capsule_key": "auteur.shinkai",
        "version": "1.0.0",
        "display_name": "Makoto Shinkai Style Capsule",
        "description": "Emotive light diffusion and lyrical color transitions.",
        "spec": {
            "inputs": COMMON_INPUTS,
            "outputs": COMMON_OUTPUTS,
            "exposedParams": build_exposed_params(
                {
                    "style_intensity": 0.7,
                    "pacing": "slow",
                    "color_bias": "warm",
                    "camera_motion": "controlled",
                },
                {"light_diffusion": 0.75},
            ),
            "policy": POLICY,
            "adapter": {
                "type": "hybrid",
                "internalGraphRef": "private-dag://auteur/shinkai/v1",
            },
        },
    },
    {
        "capsule_key": "auteur.lee-junho",
        "version": "1.0.0",
        "display_name": "Lee Jun-ho Style Capsule",
        "description": "Rhythmic pacing and music-synced beats.",
        "spec": {
            "inputs": COMMON_INPUTS,
            "outputs": COMMON_OUTPUTS,
            "exposedParams": build_exposed_params(
                {
                    "style_intensity": 0.68,
                    "pacing": "medium",
                    "color_bias": "neutral",
                    "camera_motion": "dynamic",
                },
                {"music_sync": 0.7},
            ),
            "policy": POLICY,
            "adapter": {
                "type": "hybrid",
                "internalGraphRef": "private-dag://auteur/leejunho/v1",
            },
        },
    },
    {
        "capsule_key": "auteur.na-hongjin",
        "version": "1.0.0",
        "display_name": "Na Hong-jin Style Capsule",
        "description": "High-velocity suspense with raw realism.",
        "spec": {
            "inputs": COMMON_INPUTS,
            "outputs": COMMON_OUTPUTS,
            "exposedParams": build_exposed_params(
                {
                    "style_intensity": 0.8,
                    "pacing": "fast",
                    "color_bias": "cool",
                    "camera_motion": "dynamic",
                },
                {"chaos_bias": 0.8},
            ),
            "policy": POLICY,
            "adapter": {
                "type": "hybrid",
                "internalGraphRef": "private-dag://auteur/na/v1",
            },
        },
    },
    {
        "capsule_key": "auteur.hong-sangsoo",
        "version": "1.0.0",
        "display_name": "Hong Sang-soo Style Capsule",
        "description": "Minimal camera and conversational stillness.",
        "spec": {
            "inputs": COMMON_INPUTS,
            "outputs": COMMON_OUTPUTS,
            "exposedParams": build_exposed_params(
                {
                    "style_intensity": 0.65,
                    "pacing": "slow",
                    "color_bias": "neutral",
                    "camera_motion": "static",
                },
                {"stillness": 0.85},
            ),
            "policy": POLICY,
            "adapter": {
                "type": "hybrid",
                "internalGraphRef": "private-dag://auteur/hong/v1",
            },
        },
    },
]
