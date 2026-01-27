"""
VDG Vocabulary Normalization (P1 Stub)

Normalizes cinematography terms to canonical forms.

TODO (P2): Implement full vocabulary mapping from cinematography database.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Shot Type Normalization
# =============================================================================

SHOT_TYPE_ALIASES = {
    # Wide shots
    "wide": "wide_shot",
    "ws": "wide_shot",
    "extreme wide": "extreme_wide_shot",
    "ews": "extreme_wide_shot",
    "establishing": "establishing_shot",
    # Medium shots
    "medium": "medium_shot",
    "ms": "medium_shot",
    "mid": "medium_shot",
    # Close-ups
    "close": "close_up",
    "cu": "close_up",
    "closeup": "close_up",
    "extreme close": "extreme_close_up",
    "ecu": "extreme_close_up",
    # Two-shot
    "two": "two_shot",
    "2-shot": "two_shot",
    # Over-the-shoulder
    "ots": "over_the_shoulder",
    "over shoulder": "over_the_shoulder",
    # POV
    "pov": "point_of_view",
    "first person": "point_of_view",
}


def normalize_shot_type(raw: str) -> str:
    """
    Normalize shot type to canonical form.

    Args:
        raw: Raw shot type string

    Returns:
        Canonical shot type
    """
    if not raw:
        return "unknown"
    normalized = raw.lower().strip()
    return SHOT_TYPE_ALIASES.get(normalized, normalized)


# =============================================================================
# Composition Normalization
# =============================================================================

COMPOSITION_ALIASES = {
    "rot": "rule_of_thirds",
    "rule of thirds": "rule_of_thirds",
    "center": "centered",
    "centered frame": "centered",
    "symmetric": "symmetrical",
    "symmetry": "symmetrical",
    "golden": "golden_ratio",
    "golden ratio": "golden_ratio",
    "diagonal": "diagonal_lines",
    "leading": "leading_lines",
    "leading lines": "leading_lines",
    "frame within": "frame_within_frame",
    "framing": "frame_within_frame",
}


def normalize_composition(raw: str) -> str:
    """
    Normalize composition term to canonical form.

    Args:
        raw: Raw composition string

    Returns:
        Canonical composition type
    """
    if not raw:
        return "unknown"
    normalized = raw.lower().strip()
    return COMPOSITION_ALIASES.get(normalized, normalized)


# =============================================================================
# Lighting Normalization
# =============================================================================

LIGHTING_ALIASES = {
    "high key": "high_key",
    "highkey": "high_key",
    "low key": "low_key",
    "lowkey": "low_key",
    "natural": "natural_light",
    "daylight": "natural_light",
    "hard": "hard_light",
    "soft": "soft_light",
    "diffused": "soft_light",
    "rim": "rim_light",
    "back": "backlight",
    "backlit": "backlight",
    "silhouette": "silhouette",
    "three point": "three_point",
    "3-point": "three_point",
}


def normalize_lighting(raw: str) -> str:
    """
    Normalize lighting term to canonical form.

    Args:
        raw: Raw lighting string

    Returns:
        Canonical lighting type
    """
    if not raw:
        return "unknown"
    normalized = raw.lower().strip()
    return LIGHTING_ALIASES.get(normalized, normalized)


# =============================================================================
# Camera Angle Normalization
# =============================================================================

ANGLE_ALIASES = {
    "eye": "eye_level",
    "eye level": "eye_level",
    "straight on": "eye_level",
    "high": "high_angle",
    "bird": "birds_eye",
    "birds eye": "birds_eye",
    "overhead": "birds_eye",
    "low": "low_angle",
    "worm": "worms_eye",
    "worms eye": "worms_eye",
    "dutch": "dutch_angle",
    "tilted": "dutch_angle",
    "canted": "dutch_angle",
}


def normalize_camera_angle(raw: str) -> str:
    """
    Normalize camera angle to canonical form.

    Args:
        raw: Raw camera angle string

    Returns:
        Canonical camera angle
    """
    if not raw:
        return "unknown"
    normalized = raw.lower().strip()
    return ANGLE_ALIASES.get(normalized, normalized)


# =============================================================================
# Movement Normalization
# =============================================================================

MOVEMENT_ALIASES = {
    "static": "static",
    "still": "static",
    "locked": "static",
    "pan": "pan",
    "pan left": "pan_left",
    "pan right": "pan_right",
    "tilt": "tilt",
    "tilt up": "tilt_up",
    "tilt down": "tilt_down",
    "zoom": "zoom",
    "zoom in": "zoom_in",
    "zoom out": "zoom_out",
    "dolly": "dolly",
    "dolly in": "dolly_in",
    "dolly out": "dolly_out",
    "push in": "dolly_in",
    "pull out": "dolly_out",
    "track": "tracking",
    "tracking": "tracking",
    "follow": "tracking",
    "crane": "crane",
    "jib": "crane",
    "boom": "crane",
    "handheld": "handheld",
    "shaky": "handheld",
    "steadicam": "steadicam",
    "gimbal": "steadicam",
}


def normalize_movement(raw: str) -> str:
    """
    Normalize camera movement to canonical form.

    Args:
        raw: Raw movement string

    Returns:
        Canonical movement type
    """
    if not raw:
        return "unknown"
    normalized = raw.lower().strip()
    return MOVEMENT_ALIASES.get(normalized, normalized)


# =============================================================================
# Lens Normalization
# =============================================================================

LENS_ALIASES = {
    "wide angle": "wide_angle",
    "wide": "wide_angle",
    "ultra wide": "ultra_wide",
    "fisheye": "fisheye",
    "normal": "normal",
    "standard": "normal",
    "50mm": "normal",
    "telephoto": "telephoto",
    "tele": "telephoto",
    "long": "telephoto",
    "macro": "macro",
    "anamorphic": "anamorphic",
    "ana": "anamorphic",
}


def normalize_lens(raw: str) -> str:
    """
    Normalize lens type to canonical form.

    Args:
        raw: Raw lens string

    Returns:
        Canonical lens type
    """
    if not raw:
        return "unknown"
    normalized = raw.lower().strip()
    return LENS_ALIASES.get(normalized, normalized)


# =============================================================================
# Inference from Description (P2 TODO)
# =============================================================================


def infer_composition_from_description(desc: str) -> Optional[str]:
    """
    Infer composition type from a text description.

    P1 Stub: Returns None. Will be implemented in P2.

    Args:
        desc: Text description of the frame

    Returns:
        Inferred composition type or None
    """
    # TODO (P2): Implement NLP-based composition inference
    return None


def infer_lighting_from_description(desc: str) -> Optional[str]:
    """
    Infer lighting type from a text description.

    P1 Stub: Returns None. Will be implemented in P2.

    Args:
        desc: Text description of the frame

    Returns:
        Inferred lighting type or None
    """
    # TODO (P2): Implement NLP-based lighting inference
    return None


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "normalize_shot_type",
    "normalize_composition",
    "normalize_lighting",
    "normalize_camera_angle",
    "normalize_movement",
    "normalize_lens",
    "infer_composition_from_description",
    "infer_lighting_from_description",
]
