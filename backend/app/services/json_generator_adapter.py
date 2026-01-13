"""JSON Generator Adapter - 11 categories → ShotContract.

Converts JSON Generator tool output (11 categories) to Vivid's ShotContract format.
"""
from __future__ import annotations

import re
from typing import Any, Dict

from app.generation_client import ShotContract


def json_generator_to_shot_contract(
    json_blocks: Dict[str, Any],
    shot_id: str,
    sequence_id: str = "seq-01",
    scene_id: str = "scene-01",
) -> ShotContract:
    """Convert JSON Generator output to ShotContract.
    
    Args:
        json_blocks: JSON Generator output with 11 categories:
            - meta: {styleName, aspectRatio, duration}
            - camera: {model, focalLength, framing, movement, angle}
            - subject: {description, action, pose}
            - character: {name, age, appearance, outfit}
            - setting: {location, environment, timeOfDay, weather}
            - lighting: {type, direction, intensity, temperature}
            - colorGrading: {mood, palette, contrast}
            - fx: {vfx, sfx}
            - sound: {music, ambience}
            - dialogue: {line, speaker}
            - notes: {director, technical}
        shot_id: Shot identifier (e.g., "seq-01-shot-001")
        sequence_id: Sequence identifier
        scene_id: Scene identifier
    
    Returns:
        ShotContract object
    """
    meta = json_blocks.get("meta", {})
    camera = json_blocks.get("camera", {})
    subject = json_blocks.get("subject", {})
    character_block = json_blocks.get("character", {})
    setting = json_blocks.get("setting", {})
    lighting = json_blocks.get("lighting", {})
    color = json_blocks.get("colorGrading", {})
    dialogue_block = json_blocks.get("dialogue", {})
    
    return ShotContract(
        shot_id=shot_id,
        sequence_id=sequence_id,
        scene_id=scene_id,
        shot_type=_normalize_shot_type(camera.get("framing", "medium")),
        aspect_ratio=meta.get("aspectRatio", "16:9"),
        lens=_normalize_lens(camera.get("focalLength", "50mm")),
        film_stock="Kodak Vision3",
        lighting=lighting.get("type", "natural"),
        time_of_day=setting.get("timeOfDay", "day"),
        mood=color.get("mood", "neutral"),
        character={
            "name": character_block.get("name", ""),
            "age": character_block.get("age", ""),
            "wardrobe": character_block.get("outfit", ""),
            "notes": character_block.get("appearance", ""),
        },
        pose_motion=_build_pose_motion(subject),
        dialogue=dialogue_block.get("line", ""),
        environment_layers={
            "foreground": "",
            "midground": setting.get("environment", ""),
            "background": setting.get("location", ""),
        },
        continuity_tags=[],
        seed_image_ref=None,
        duration_sec=_parse_duration(meta.get("duration", "4s")),
    )


def _normalize_shot_type(raw: str) -> str:
    """Normalize free-text framing to canonical shot_type.
    
    Reference: generation_client.infer_shot_type()
    """
    raw_lower = raw.lower().strip()
    
    # Order matters: check specific terms first
    if any(k in raw_lower for k in ["extreme", "ecu", "detail"]):
        return "extreme-close-up"
    elif any(k in raw_lower for k in ["wide", "establishing", "master"]):
        return "wide"
    elif any(k in raw_lower for k in ["close", "closeup", "cu", "tight"]):
        return "close-up"
    elif any(k in raw_lower for k in ["full", "body"]):
        return "full"
    elif any(k in raw_lower for k in ["over", "ots"]):
        return "over-the-shoulder"
    return "medium"  # Default


def _normalize_lens(raw: str) -> str:
    """Normalize lens to mm format."""
    match = re.search(r"(\d+)", raw)
    return f"{match.group(1)}mm" if match else "50mm"


def _parse_duration(raw: str) -> int:
    """Parse duration string to seconds (e.g., '4s' → 4)."""
    match = re.search(r"(\d+)", str(raw))
    return int(match.group(1)) if match else 4


def _build_pose_motion(subject: Dict[str, Any]) -> str:
    """Combine subject.action and subject.pose."""
    parts = [subject.get("action", ""), subject.get("pose", "")]
    return " ".join(p for p in parts if p).strip()
