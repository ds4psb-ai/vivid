"""Nanobanana Editor Adapter - Lighting/Camera → ShotContract.

Converts Nanobanana Editor state (16 lighting presets + camera parameters)
to Vivid's ShotContract format.
"""
from __future__ import annotations

from typing import Any, Dict

from app.generation_client import ShotContract


# === LIGHTING STYLES (Nanobanana presets.ts 원본) ===
LIGHTING_STYLES = {
    "none": "balanced lighting, natural exposure",
    "natural": "Natural, basic sunlight",
    "golden-hour": "Warm, soft light from just before sunrise or after sunset",
    "blue-hour": "Dreamy, blue-toned light from just after sunset",
    "backlight": "Strong backlight to create a silhouette effect",
    "softbox": "The soft, even lighting of a professional photo studio",
    "cinematic": "A cinematic atmosphere with high contrast and rich, movie-like colors",
    "moody": "A dark and emotional atmosphere with deep shadows and soft light",
    "high-key": "Bright, low-contrast lighting with minimal shadows",
    "low-key": "Dark, high-contrast lighting, often used in thrillers or dramatic scenes",
    "volumetric": "A dramatic style where rays of light are visible, as if streaming through a hazy atmosphere",
    "amber": "A warm, vintage atmosphere created by a soft amber-colored light",
    "crimson": "Intense and dramatic mood with crimson red tones",
    "emerald": "Mysterious and dreamlike atmosphere with emerald green light",
    "fuchsia": "Fuchsia and violet tones, often used in music videos or fashion shoots",
    "bw": "Classic mood emphasizing black and white contrast",
}

# === LIGHTING DIRECTIONS (Nanobanana presets.ts 원본) ===
LIGHTING_DIRECTIONS = {
    "top": "lighting from above",
    "bottom": "lighting from below",
    "left": "lighting from left",
    "right": "lighting from right",
    "tl": "lighting from top-left",
    "tr": "lighting from top-right",
    "bl": "lighting from bottom-left",
    "br": "lighting from bottom-right",
}


def nanobanana_to_shot_contract(
    editor_state: Dict[str, Any],
    shot_id: str,
    sequence_id: str = "seq-01",
    scene_id: str = "scene-01",
) -> ShotContract:
    """Convert Nanobanana Editor state to ShotContract.
    
    UI Default values (from page.tsx):
    - lightingPreset: "none"
    - cameraDistance: 50
    - cameraLens: 35
    - selectedRatio: null → "16:9"
    - lightingDirection: {x: 0, y: 0}
    - cubeRotation: {x: 0, y: 0}
    """
    # Extract values with UI defaults
    lighting_preset = editor_state.get("lightingPreset", "none")
    lighting_direction = editor_state.get("lightingDirection", {"x": 0, "y": 0})
    camera_distance = editor_state.get("cameraDistance", 50)
    camera_lens = editor_state.get("cameraLens", 35)
    cube_rotation = editor_state.get("cubeRotation", {"x": 0, "y": 0})
    aspect_ratio = editor_state.get("selectedRatio") or "16:9"
    
    # Build full lighting description (not just key)
    lighting_desc = LIGHTING_STYLES.get(lighting_preset, LIGHTING_STYLES["none"])
    dir_suffix = _get_direction_string(lighting_direction)
    if dir_suffix:
        lighting_desc = f"{lighting_desc}, {dir_suffix}"
    
    # Build camera description for pose_motion field
    camera_desc = _build_camera_description(cube_rotation, camera_distance)
    
    return ShotContract(
        shot_id=shot_id,
        sequence_id=sequence_id,
        scene_id=scene_id,
        shot_type=_distance_to_shot_type(camera_distance),
        aspect_ratio=aspect_ratio,
        lens=f"{camera_lens}mm",
        lighting=lighting_desc,
        film_stock="Kodak Vision3",
        time_of_day="day",
        mood="neutral",
        character={},
        pose_motion=camera_desc,  # Camera angle/direction stored here
        dialogue="",
        environment_layers={},
        continuity_tags=[],
        seed_image_ref=None,
        duration_sec=4,
    )


def _distance_to_shot_type(d: int) -> str:
    """Camera distance (0-100) → shot_type (Nanobanana promptBuilder style)."""
    if d <= 15:
        return "extreme-close-up"
    if d <= 30:
        return "close-up"
    if d <= 45:
        return "medium-close-up"
    if d <= 60:
        return "medium"
    if d <= 75:
        return "medium-full"
    if d <= 90:
        return "full"
    return "wide"


def _get_direction_string(direction: Dict[str, int]) -> str:
    """Lighting direction → LIGHTING_DIRECTIONS string."""
    x = direction.get("x", 0)
    y = direction.get("y", 0)
    
    if x == 0 and y == 0:
        return ""
    
    key = ""
    if y == -1:
        key = "top"
    elif y == 1:
        key = "bottom"
    
    if x == -1:
        key = f"{key}l" if key else "left"
    elif x == 1:
        key = f"{key}r" if key else "right"
    
    # Map combined keys to preset keys
    key_map = {
        "top": "top", "bottom": "bottom", "left": "left", "right": "right",
        "topl": "tl", "topr": "tr", "bottoml": "bl", "bottomr": "br"
    }
    
    return LIGHTING_DIRECTIONS.get(key_map.get(key, ""), "")


def _build_camera_description(cube_rotation: Dict[str, int], distance: int) -> str:
    """Build camera angle/direction description (Nanobanana promptBuilder style).
    
    Preserves camera angle/direction info that would otherwise be lost.
    Stored in pose_motion field for prompt building.
    """
    x = cube_rotation.get("x", 0)
    y = cube_rotation.get("y", 0)
    
    # Angle (vertical) - from getAngleText()
    if x >= 60:
        angle = "extreme high angle, bird's eye view"
    elif x >= 35:
        angle = "high angle, from above"
    elif x >= 15:
        angle = "slight high angle"
    elif x <= -60:
        angle = "extreme low angle, worm's eye view"
    elif x <= -35:
        angle = "low angle, from below"
    elif x <= -15:
        angle = "slight low angle"
    else:
        angle = "eye level"
    
    # Direction (horizontal) - from getDirectionText()
    t = y % 360
    if t > 180:
        t -= 360
    if t < -180:
        t += 360
    a = abs(t)
    
    if a >= 160:
        direction = "back view"
    elif a >= 120:
        direction = "rear three-quarter view"
    elif a >= 70:
        direction = "side profile view"
    elif a >= 35:
        direction = "three-quarter view"
    elif a >= 10:
        direction = "slight angle from side"
    else:
        direction = "front view"
    
    return f"{angle}, {direction}"
