"""Kling 3.0 Prompt Adapter — Subject-first optimized prompts.

Generates Kling 3.0 compatible prompts from SceneTechniques + SequenceContext.

Kling 3.0 best practices:
- Subject-first structure (proven to improve lip-sync and coherence)
- Multi-shot scene format: 2-6 scenes per generation
- camera_preset, motion_intensity, negative_prompt
- Transition setup phrases at scene boundaries
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Camera preset mapping from technique IDs
TECHNIQUE_TO_CAMERA_PRESET = {
    "dolly_in": "dolly_in",
    "dolly_out": "dolly_out",
    "tracking_shot": "tracking",
    "pan_left": "pan_left",
    "pan_right": "pan_right",
    "tilt_up": "tilt_up",
    "tilt_down": "tilt_down",
    "crane_up": "crane_up",
    "crane_down": "crane_down",
    "steadicam": "orbit",
    "arc_orbit": "orbit",
    "static_hold": "static",
    "whip_pan": "pan_left",  # Approximation
    "push_in": "zoom_in",
    "pull_back": "zoom_out",
}

# Motion intensity mapping from emotional intensity
INTENSITY_TO_MOTION = {
    (0.0, 0.3): "slow",
    (0.3, 0.6): "normal",
    (0.6, 0.8): "fast",
    (0.8, 1.0): "dramatic",
}


def generate_kling_prompt(
    scene: Dict[str, Any],
    sequence_context: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a Kling 3.0 optimized prompt from scene analysis.

    Structure: Subject-first → Environment → Camera → Lighting → Style

    Args:
        scene: Scene analysis data with techniques and description
        sequence_context: Cross-scene context for continuity

    Returns:
        English prompt optimized for Kling 3.0
    """
    # If a pre-generated prompt exists, use it (from Gemini)
    prompts = scene.get("prompts", {})
    if isinstance(prompts, dict) and prompts.get("kling_3_0"):
        return prompts["kling_3_0"]

    # Build from techniques
    parts = []

    # Subject (from description_en or description)
    desc = scene.get("description_en") or scene.get("description", "")
    if desc:
        parts.append(desc)

    # Camera movement
    techniques = scene.get("techniques", {})
    camera_moves = techniques.get("camera_movement", [])
    if camera_moves:
        move_names = [_technique_to_text(t) for t in camera_moves]
        parts.append(", ".join(move_names))

    # Composition
    composition = techniques.get("composition", [])
    if composition:
        comp_names = [_technique_to_text(t) for t in composition]
        parts.append(", ".join(comp_names))

    # Lighting
    lighting = techniques.get("lighting", [])
    if lighting:
        light_names = [_technique_to_text(t) for t in lighting]
        parts.append(", ".join(light_names))

    # Color
    color = techniques.get("color", [])
    if color:
        color_names = [_technique_to_text(t) for t in color]
        parts.append(", ".join(color_names))

    return ". ".join(parts) if parts else desc


def get_kling_camera_preset(techniques: Dict[str, Any]) -> Optional[str]:
    """Extract Kling camera preset from techniques."""
    camera_moves = techniques.get("camera_movement", [])
    for move in camera_moves:
        tid = _extract_technique_id(move)
        if tid in TECHNIQUE_TO_CAMERA_PRESET:
            return TECHNIQUE_TO_CAMERA_PRESET[tid]
    return None


def get_kling_motion_intensity(emotional_intensity: float) -> str:
    """Map emotional intensity to Kling motion preset."""
    for (low, high), preset in INTENSITY_TO_MOTION.items():
        if low <= emotional_intensity < high:
            return preset
    return "normal"


def _technique_to_text(technique) -> str:
    """Convert a technique (str or dict) to English text."""
    if isinstance(technique, str):
        return technique.replace("_", " ")
    if isinstance(technique, dict):
        return technique.get("name_en", technique.get("technique_id", "")).replace("_", " ")
    return str(technique)


def _extract_technique_id(technique) -> str:
    """Extract technique_id from str or dict."""
    if isinstance(technique, str):
        return technique
    if isinstance(technique, dict):
        return technique.get("technique_id", "")
    return ""
