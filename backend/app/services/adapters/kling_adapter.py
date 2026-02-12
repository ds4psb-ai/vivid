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

    5-Layer Formula (2026 best practice):
      1. Scene — environment, location, time of day, atmosphere
      2. Characters — identities with consistent descriptors
      3. Action — sequential movement with motion verbs
      4. Camera — cinematic camera movement + lens detail
      5. Audio & Style — sound effects, dialogue, visual style

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

    techniques = scene.get("techniques", {})
    layers: List[str] = []

    # Layer 1: Scene (environment + atmosphere)
    desc = scene.get("description_en") or scene.get("description", "")
    color = techniques.get("color", [])
    lighting = techniques.get("lighting", [])
    scene_parts = []
    if desc:
        scene_parts.append(desc)
    if color:
        color_text = ", ".join(_technique_to_text(c) for c in color[:2])
        scene_parts.append(f"{color_text} atmosphere")
    if lighting:
        light_text = ", ".join(_technique_to_text(lt) for lt in lighting[:2])
        scene_parts.append(f"lit by {light_text}")
    if scene_parts:
        layers.append(". ".join(scene_parts))

    # Layer 2: Characters (with consistent binding descriptors)
    characters = scene.get("characters", [])
    if characters:
        char_descs = []
        for i, char in enumerate(characters):
            if isinstance(char, str):
                char_descs.append(f"[Character {chr(65+i)}: {char}]")
            elif isinstance(char, dict):
                name = char.get("name", f"Character {chr(65+i)}")
                appearance = char.get("description", char.get("appearance", ""))
                char_descs.append(f"[{name}: {appearance}]")
        layers.append(" ".join(char_descs))

    # Layer 3: Action (motion verbs, temporal flow)
    action = scene.get("action_en") or scene.get("action", "")
    if action:
        layers.append(action)

    # Layer 4: Camera (movement + composition)
    camera_parts = []
    camera_moves = techniques.get("camera_movement", [])
    if camera_moves:
        move_names = [_technique_to_text(t) for t in camera_moves[:2]]
        camera_parts.append(", ".join(move_names))
    composition = techniques.get("composition", [])
    if composition:
        comp_names = [_technique_to_text(t) for t in composition[:1]]
        camera_parts.append(", ".join(comp_names))
    shot_scale = techniques.get("shot_scale", [])
    if shot_scale:
        camera_parts.insert(0, _technique_to_text(shot_scale[0]))
    if camera_parts:
        layers.append(", ".join(camera_parts))

    # Layer 5: Audio & Style
    style_parts = []
    aesthetic = techniques.get("aesthetic_style", [])
    if aesthetic:
        style_parts.append(_technique_to_text(aesthetic[0]) + " style")
    audio = scene.get("audio_hint", "")
    if audio:
        style_parts.append(f"Audio: {audio}")
    # Style anchors from sequence
    if sequence_context:
        anchors = sequence_context.get("global_style_anchors", [])
        if anchors and isinstance(anchors, list):
            style_parts.append(", ".join(str(a) for a in anchors[:2]))
    if style_parts:
        layers.append(". ".join(style_parts))

    return ". ".join(layers) if layers else desc



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
