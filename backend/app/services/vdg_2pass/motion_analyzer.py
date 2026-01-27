"""
Motion Analyzer for VDG Pipeline

Uses OpenCV for motion analysis:
- Optical flow analysis
- Dominant movement detection
- Motion segmentation

Graceful degradation:
- Returns stub values if OpenCV unavailable
- Logs warnings but continues processing
"""
from __future__ import annotations

import logging
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# Check OpenCV availability
# =============================================================================

CV2_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    logger.warning("OpenCV not available, motion analysis will use stub values")


# =============================================================================
# Enums
# =============================================================================


class MovementType(str, Enum):
    """Types of camera/subject movement."""
    STATIC = "static"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    TRACKING = "tracking"
    HANDHELD = "handheld"
    CRANE = "crane"
    MIXED = "mixed"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class MotionSegment:
    """Motion segment detected in video."""
    t_start_ms: int
    t_end_ms: int
    movement_type: MovementType
    intensity: float = 0.0  # 0-1 scale
    confidence: float = 1.0


@dataclass
class MotionAnalysis:
    """Complete motion analysis result."""
    has_motion: bool = False
    dominant_movement: Optional[MovementType] = None
    segments: List[MotionSegment] = field(default_factory=list)
    avg_flow_magnitude: float = 0.0
    peak_flow_magnitude: float = 0.0
    static_ratio: float = 0.0  # Ratio of static frames


# =============================================================================
# Frame Extraction
# =============================================================================


def extract_frames_for_motion(
    video_path: str,
    output_dir: str,
    fps: float = 5.0,
    max_frames: int = 60,
) -> List[str]:
    """
    Extract frames from video for motion analysis.

    Args:
        video_path: Path to video file
        output_dir: Directory for extracted frames
        fps: Frames per second to extract
        max_frames: Maximum number of frames

    Returns:
        List of frame paths
    """
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i", video_path,
                "-vf", f"fps={fps}",
                "-frames:v", str(max_frames),
                "-q:v", "2",
                f"{output_dir}/frame_%04d.jpg",
            ],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []

        # Get list of extracted frames
        frames = sorted(Path(output_dir).glob("frame_*.jpg"))
        return [str(f) for f in frames]

    except Exception as e:
        logger.warning(f"Frame extraction for motion failed: {e}")
        return []


# =============================================================================
# Motion Analysis
# =============================================================================


def compute_optical_flow(
    prev_gray,
    curr_gray,
) -> Tuple[float, float, float]:
    """
    Compute optical flow between two frames.

    Returns:
        Tuple of (avg_magnitude, avg_dx, avg_dy)
    """
    if not CV2_AVAILABLE:
        return (0.0, 0.0, 0.0)

    # Farneback optical flow
    flow = cv2.calcOpticalFlowFarneback(
        prev_gray, curr_gray,
        None,
        pyr_scale=0.5,
        levels=3,
        winsize=15,
        iterations=3,
        poly_n=5,
        poly_sigma=1.2,
        flags=0,
    )

    # Get horizontal and vertical components
    dx = flow[..., 0]
    dy = flow[..., 1]

    # Compute magnitude
    magnitude = np.sqrt(dx**2 + dy**2)

    return (
        float(np.mean(magnitude)),
        float(np.mean(dx)),
        float(np.mean(dy)),
    )


def classify_movement(dx: float, dy: float, magnitude: float) -> MovementType:
    """
    Classify movement type based on optical flow.

    Args:
        dx: Average horizontal flow
        dy: Average vertical flow
        magnitude: Average flow magnitude

    Returns:
        MovementType classification
    """
    # Threshold for static
    if magnitude < 1.0:
        return MovementType.STATIC

    # Horizontal movement
    if abs(dx) > abs(dy) * 1.5:
        if dx > 0:
            return MovementType.PAN_RIGHT
        else:
            return MovementType.PAN_LEFT

    # Vertical movement
    if abs(dy) > abs(dx) * 1.5:
        if dy > 0:
            return MovementType.TILT_DOWN
        else:
            return MovementType.TILT_UP

    # Mixed or complex
    if magnitude > 5.0:
        return MovementType.HANDHELD

    return MovementType.MIXED


def analyze_motion(video_path: str) -> MotionAnalysis:
    """
    Analyze motion in video using optical flow.

    Args:
        video_path: Path to video file

    Returns:
        MotionAnalysis with motion segments and statistics
    """
    if not CV2_AVAILABLE:
        logger.warning("OpenCV not available, returning stub motion analysis")
        return MotionAnalysis(has_motion=False)

    analysis = MotionAnalysis()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract frames
        frame_paths = extract_frames_for_motion(
            video_path=video_path,
            output_dir=temp_dir,
            fps=5.0,
            max_frames=60,
        )

        if len(frame_paths) < 2:
            logger.info("Not enough frames for motion analysis")
            return analysis

        analysis.has_motion = True

        # Analyze consecutive frame pairs
        magnitudes = []
        movement_types = []
        static_count = 0

        prev_gray = None
        fps = 5.0  # Assumed extraction FPS

        for i, frame_path in enumerate(frame_paths):
            frame = cv2.imread(frame_path)
            if frame is None:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if prev_gray is not None:
                # Compute optical flow
                mag, dx, dy = compute_optical_flow(prev_gray, gray)
                magnitudes.append(mag)

                # Classify movement
                movement = classify_movement(dx, dy, mag)
                movement_types.append(movement)

                if movement == MovementType.STATIC:
                    static_count += 1

            prev_gray = gray

        if magnitudes:
            analysis.avg_flow_magnitude = float(np.mean(magnitudes))
            analysis.peak_flow_magnitude = float(np.max(magnitudes))
            analysis.static_ratio = static_count / len(magnitudes)

            # Determine dominant movement
            if movement_types:
                from collections import Counter
                counter = Counter(movement_types)
                most_common = counter.most_common(1)[0]
                analysis.dominant_movement = most_common[0]

            # Create motion segments
            analysis.segments = _create_segments(
                movement_types=movement_types,
                magnitudes=magnitudes,
                fps=fps,
            )

        logger.info(
            f"Motion analysis complete: "
            f"dominant={analysis.dominant_movement}, "
            f"avg_mag={analysis.avg_flow_magnitude:.2f}, "
            f"segments={len(analysis.segments)}"
        )

    return analysis


def _create_segments(
    movement_types: List[MovementType],
    magnitudes: List[float],
    fps: float,
) -> List[MotionSegment]:
    """
    Create motion segments from frame-by-frame analysis.

    Merges consecutive frames with same movement type.
    """
    if not movement_types:
        return []

    segments = []
    current_type = movement_types[0]
    start_idx = 0
    intensities = [magnitudes[0]] if magnitudes else []

    for i in range(1, len(movement_types)):
        if movement_types[i] != current_type:
            # Save current segment
            t_start_ms = int(start_idx / fps * 1000)
            t_end_ms = int(i / fps * 1000)
            avg_intensity = float(np.mean(intensities)) if intensities else 0.0

            segments.append(MotionSegment(
                t_start_ms=t_start_ms,
                t_end_ms=t_end_ms,
                movement_type=current_type,
                intensity=min(1.0, avg_intensity / 10.0),  # Normalize
            ))

            # Start new segment
            current_type = movement_types[i]
            start_idx = i
            intensities = []

        if i < len(magnitudes):
            intensities.append(magnitudes[i])

    # Save final segment
    t_start_ms = int(start_idx / fps * 1000)
    t_end_ms = int(len(movement_types) / fps * 1000)
    avg_intensity = float(np.mean(intensities)) if intensities else 0.0

    segments.append(MotionSegment(
        t_start_ms=t_start_ms,
        t_end_ms=t_end_ms,
        movement_type=current_type,
        intensity=min(1.0, avg_intensity / 10.0),
    ))

    return segments


def get_motion_summary(analysis: MotionAnalysis) -> str:
    """
    Generate text summary of motion analysis for LLM context.

    Args:
        analysis: MotionAnalysis result

    Returns:
        Summary string for LLM prompt
    """
    if not analysis.has_motion:
        return "No motion data available."

    parts = []

    # Dominant movement
    if analysis.dominant_movement:
        movement_name = analysis.dominant_movement.value.replace("_", " ")
        parts.append(f"Dominant: {movement_name}")

    # Motion intensity
    if analysis.avg_flow_magnitude < 2.0:
        intensity = "low"
    elif analysis.avg_flow_magnitude < 5.0:
        intensity = "moderate"
    else:
        intensity = "high"
    parts.append(f"Intensity: {intensity} (avg={analysis.avg_flow_magnitude:.1f})")

    # Static ratio
    if analysis.static_ratio > 0.7:
        parts.append("Mostly static shots")
    elif analysis.static_ratio > 0.3:
        parts.append("Mix of static and moving shots")
    else:
        parts.append("Mostly dynamic camera work")

    # Segment summary
    if analysis.segments:
        segment_types = [s.movement_type.value for s in analysis.segments[:3]]
        parts.append(f"Segments: {', '.join(segment_types)}")

    return " | ".join(parts)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "MovementType",
    "MotionSegment",
    "MotionAnalysis",
    "analyze_motion",
    "get_motion_summary",
    "CV2_AVAILABLE",
]
