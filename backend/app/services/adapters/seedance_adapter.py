"""Seedance 2.0 Prompt Adapter — Cinematic description style prompts.

Generates Seedance 2.0 compatible prompts from SceneTechniques + SequenceContext.

Seedance 2.0 preferences:
- Cinematic description style (narrative flow)
- Visual atmosphere emphasis
- Motion flow descriptions
- Longer, more detailed prompts (40-60 words)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def generate_seedance_prompt(
    scene: Dict[str, Any],
    sequence_context: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a Seedance 2.0 optimized prompt from scene analysis.

    Structure: Cinematic style → Subject → Atmosphere → Motion → Technique details

    Args:
        scene: Scene analysis data with techniques and description
        sequence_context: Cross-scene context for continuity

    Returns:
        English prompt optimized for Seedance 2.0
    """
    # If a pre-generated prompt exists, use it
    prompts = scene.get("prompts", {})
    if isinstance(prompts, dict) and prompts.get("seedance_2_0"):
        return prompts["seedance_2_0"]

    # Build from techniques
    parts = []

    # Opening with cinematic style cue
    parts.append("Cinematic")

    # Camera angle/movement (leads the visual style)
    techniques = scene.get("techniques", {})
    camera_angle = techniques.get("camera_angle", [])
    camera_movement = techniques.get("camera_movement", [])

    if camera_angle:
        angle_str = " ".join(_technique_to_text(t) for t in camera_angle)
        parts.append(angle_str + " shot")

    if camera_movement:
        move_str = " with " + " and ".join(_technique_to_text(t) for t in camera_movement)
        parts.append(move_str)

    # Subject description
    desc = scene.get("description_en") or scene.get("description", "")
    if desc:
        parts.append("of " + desc)

    # Lighting atmosphere
    lighting = techniques.get("lighting", [])
    if lighting:
        light_str = ", ".join(_technique_to_text(t) for t in lighting)
        parts.append(f"Lit with {light_str}")

    # Color palette
    color = techniques.get("color", [])
    if color:
        color_str = ", ".join(_technique_to_text(t) for t in color)
        parts.append(f"{color_str} color palette")

    # Composition details
    composition = techniques.get("composition", [])
    if composition:
        comp_str = ", ".join(_technique_to_text(t) for t in composition)
        parts.append(f"{comp_str} composition")

    # Continuity anchors for consistency
    anchors = scene.get("continuity_anchors", {})
    if isinstance(anchors, dict) and anchors.get("style"):
        parts.append(anchors["style"])

    return ". ".join(p for p in parts if p) if parts else desc


def _technique_to_text(technique) -> str:
    """Convert a technique (str or dict) to English text."""
    if isinstance(technique, str):
        return technique.replace("_", " ")
    if isinstance(technique, dict):
        return technique.get("name_en", technique.get("technique_id", "")).replace("_", " ")
    return str(technique)
