"""Veo 3.1 Prompt Adapter — 7-layer structured prompts.

Generates Veo 3.1 compatible prompts from SceneTechniques + SequenceContext.

Veo 3.1 best practices (7-layer structure):
1. Camera + Lens — framing, movement, focal length
2. Subject — appearance, identity, material cues
3. Action + Physics — force-based verbs, single dominant action
4. Setting + Atmosphere — environment, time of day, weather
5. Lighting — named source, direction, quality
6. Style — texture, film stock, finish
7. Audio — dialogue, SFX, ambience (optional)

Target: 50-100 words per prompt.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Lens focal length suggestions per shot scale / angle
_LENS_HINTS = {
    "extreme_wide_shot": "16mm",
    "wide_shot": "24mm",
    "full_shot": "35mm",
    "medium_wide_shot": "35mm",
    "medium_shot_standard": "50mm",
    "medium_closeup_shot": "85mm",
    "closeup_shot": "85mm",
    "big_closeup": "100mm",
    "extreme_closeup": "100mm macro",
    "insert_shot": "100mm macro",
    "eye_level": "50mm",
    "low_angle": "35mm",
    "high_angle": "35mm",
    "bird_eye": "24mm",
    "worm_eye": "16mm",
    "over_the_shoulder": "85mm",
}


def generate_veo_prompt(
    scene: Dict[str, Any],
    sequence_context: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a Veo 3.1 optimized prompt from scene analysis.

    Structure: Camera+Lens → Subject → Action → Setting → Lighting → Style → Audio

    Args:
        scene: Scene analysis data with techniques and description
        sequence_context: Cross-scene context for continuity

    Returns:
        English prompt optimized for Veo 3.1 (50-100 words, 7-layer)
    """
    # If a pre-generated prompt exists, use it (from Gemini)
    prompts = scene.get("prompts", {})
    if isinstance(prompts, dict) and prompts.get("veo_3_1"):
        return prompts["veo_3_1"]

    techniques = scene.get("techniques", {})
    layers: List[str] = []

    # Layer 1: Camera + Lens
    camera_desc = _build_camera_layer(techniques)
    if camera_desc:
        layers.append(camera_desc)

    # Layer 2: Subject
    desc = scene.get("description_en") or scene.get("description", "")
    if desc:
        layers.append(desc)

    # Layer 3: Action + Physics (embedded in description usually)
    # Veo needs force-based verbs — we rely on Gemini's description_en

    # Layer 4: Setting + Atmosphere
    setting = _build_setting_layer(techniques, sequence_context)
    if setting:
        layers.append(setting)

    # Layer 5: Lighting
    lighting_desc = _build_lighting_layer(techniques)
    if lighting_desc:
        layers.append(lighting_desc)

    # Layer 6: Style
    style_desc = _build_style_layer(techniques, sequence_context)
    if style_desc:
        layers.append(style_desc)

    # Layer 7: Audio (scene-level if available)
    audio = scene.get("audio_hint", "")
    if audio:
        layers.append(f"Audio: {audio}")

    return ". ".join(layers) if layers else desc


def _build_camera_layer(techniques: Dict[str, Any]) -> str:
    """Layer 1: Camera movement + lens + angle."""
    parts: List[str] = []

    # Shot scale / angle → lens hint
    angles = techniques.get("camera_angle", [])
    shot_scale = techniques.get("shot_scale", [])
    lens = "35mm lens"

    for item in angles + shot_scale:
        tid = _extract_id(item)
        if tid in _LENS_HINTS:
            lens = f"{_LENS_HINTS[tid]} lens"
            break

    # Lens character override
    lens_chars = techniques.get("lens_character", [])
    if lens_chars:
        tid = _extract_id(lens_chars[0])
        lens = _technique_to_text(lens_chars[0]) + " lens"

    # Camera movement
    movements = techniques.get("camera_movement", [])
    if movements:
        move_text = " with " + ", ".join(
            _technique_to_text(m) for m in movements[:2]
        )
    else:
        move_text = ""

    # Angle
    if angles:
        angle_text = _technique_to_text(angles[0])
    elif shot_scale:
        angle_text = _technique_to_text(shot_scale[0])
    else:
        angle_text = "Medium shot"

    parts.append(f"{angle_text} on {lens}{move_text}")

    # Focus technique
    focus = techniques.get("focus_technique", [])
    if focus:
        parts.append(_technique_to_text(focus[0]))

    return ", ".join(parts)


def _build_setting_layer(
    techniques: Dict[str, Any],
    seq_ctx: Optional[Dict[str, Any]],
) -> str:
    """Layer 4: Setting + atmosphere."""
    parts: List[str] = []

    if seq_ctx:
        prev_desc = seq_ctx.get("previous_description", "")
        if prev_desc:
            parts.append(f"following from {prev_desc[:50]}")

    # Color palette as atmosphere cue
    colors = techniques.get("color", [])
    if colors:
        color_text = ", ".join(_technique_to_text(c) for c in colors)
        parts.append(f"{color_text} atmosphere")

    return ", ".join(parts) if parts else ""


def _build_lighting_layer(techniques: Dict[str, Any]) -> str:
    """Layer 5: Lighting with source and quality."""
    lighting = techniques.get("lighting", [])
    if not lighting:
        return ""

    light_descs = [_technique_to_text(lt) for lt in lighting[:2]]
    return "Lit by " + " and ".join(light_descs)


def _build_style_layer(
    techniques: Dict[str, Any],
    seq_ctx: Optional[Dict[str, Any]],
) -> str:
    """Layer 6: Style, texture, finish."""
    parts: List[str] = []

    # Composition as style element
    comp = techniques.get("composition", [])
    if comp:
        parts.append(_technique_to_text(comp[0]) + " composition")

    # Editing rhythm hint
    editing = techniques.get("editing_rhythm", [])
    if editing:
        parts.append(_technique_to_text(editing[0]) + " pacing")

    # Style anchors from sequence
    if seq_ctx:
        style_anchors = seq_ctx.get("global_style_anchors", [])
        if style_anchors and isinstance(style_anchors, list):
            parts.append(", ".join(str(a) for a in style_anchors[:2]))

    return "Style: " + ", ".join(parts) if parts else ""


def _technique_to_text(technique: Any) -> str:
    """Convert a technique (str or dict) to English text."""
    if isinstance(technique, str):
        return technique.replace("_", " ")
    if isinstance(technique, dict):
        return technique.get("name_en", technique.get("technique_id", "")).replace("_", " ")
    return str(technique)


def _extract_id(technique: Any) -> str:
    """Extract technique_id from str or dict."""
    if isinstance(technique, str):
        return technique
    if isinstance(technique, dict):
        return technique.get("technique_id", "")
    return ""
