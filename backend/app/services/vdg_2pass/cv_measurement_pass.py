"""
CV Measurement Pass (VDG Pass 2)

Deterministic computer vision measurement based on Pass 1 analysis plan.

Metrics (MVP):
- center_offset: Subject center offset from frame center (0-1)
- brightness: Frame brightness (0-255)
- blur: Laplacian variance (higher = sharper)

Architecture:
- Uses ffmpeg for frame extraction
- Uses OpenCV for CV measurements
- Fallback to stub values if CV unavailable
"""
from __future__ import annotations

import logging
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.vdg_unified_pass import (
    AnalysisPlanLLM,
    AnalysisPointSeedLLM,
    CVMeasurementResult,
    CVPassProvenance,
    MetricResult,
    PointMeasurement,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

DEFAULT_EXTRACTION_FPS = 10.0
CV_AVAILABLE = False
OPENCV_VERSION = "N/A"

# Try to import OpenCV
try:
    import cv2
    import numpy as np
    CV_AVAILABLE = True
    OPENCV_VERSION = cv2.__version__
except ImportError:
    logger.warning("OpenCV not available, CV measurements will use stub values")


# =============================================================================
# Exports from vdg_unified_pass (for backward compatibility)
# =============================================================================

# Re-export for backward compatibility with vdg_unified_pipeline imports
__all__ = [
    "CVMeasurementPass",
    "CVMeasurementResult",
    "CVPassProvenance",
    "PointMeasurement",
    "MetricResult",
]


# =============================================================================
# Frame Extraction
# =============================================================================


def extract_frame_at_time(
    video_path: str,
    t_ms: int,
    output_dir: str,
) -> Optional[str]:
    """
    Extract a single frame at specified time using ffmpeg.

    Args:
        video_path: Path to video file
        t_ms: Timestamp in milliseconds
        output_dir: Directory to save frame

    Returns:
        Path to extracted frame JPEG, or None on failure
    """
    t_sec = t_ms / 1000.0
    output_path = Path(output_dir) / f"frame_{t_ms:06d}.jpg"

    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-ss", str(t_sec),
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                "-y",
                str(output_path),
            ],
            capture_output=True,
            timeout=10,
        )
        if result.returncode == 0 and output_path.exists():
            return str(output_path)
    except Exception as e:
        logger.warning(f"Failed to extract frame at {t_ms}ms: {e}")

    return None


# =============================================================================
# CV Metrics
# =============================================================================


def measure_brightness(frame) -> float:
    """
    Measure average brightness of frame.

    Returns:
        Brightness value 0-255
    """
    if not CV_AVAILABLE:
        return 128.0  # Stub

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gray))


def measure_blur(frame) -> float:
    """
    Measure sharpness using Laplacian variance.

    Higher values = sharper image.

    Returns:
        Laplacian variance (typically 0-1000+)
    """
    if not CV_AVAILABLE:
        return 100.0  # Stub

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return float(laplacian.var())


def measure_center_offset(frame) -> float:
    """
    Measure subject center offset from frame center.

    Uses simple brightness/contrast-based saliency.

    Returns:
        Normalized offset 0-1 (0 = perfectly centered)
    """
    if not CV_AVAILABLE:
        return 0.0  # Stub - perfectly centered

    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Simple saliency: find brightest region
    blur = cv2.GaussianBlur(gray, (21, 21), 0)
    (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(blur)

    # Calculate offset from center
    center_x, center_y = w / 2, h / 2
    bright_x, bright_y = maxLoc

    # Normalized distance from center
    dx = abs(bright_x - center_x) / (w / 2)
    dy = abs(bright_y - center_y) / (h / 2)

    return float(min(1.0, (dx + dy) / 2))


def compute_all_metrics(frame_path: str) -> Dict[str, MetricResult]:
    """
    Compute all MVP metrics for a frame.

    Args:
        frame_path: Path to frame JPEG

    Returns:
        Dict of metric_id -> MetricResult
    """
    metrics = {}

    if CV_AVAILABLE:
        try:
            frame = cv2.imread(frame_path)
            if frame is None:
                logger.warning(f"Failed to read frame: {frame_path}")
                return _stub_metrics()

            metrics["brightness"] = MetricResult(
                metric_id="brightness",
                value=measure_brightness(frame),
                unit="0-255",
                confidence=1.0,
            )

            metrics["blur"] = MetricResult(
                metric_id="blur",
                value=measure_blur(frame),
                unit="laplacian_variance",
                confidence=1.0,
            )

            metrics["center_offset"] = MetricResult(
                metric_id="center_offset",
                value=measure_center_offset(frame),
                unit="0-1",
                confidence=0.8,  # Lower confidence for saliency-based
            )

        except Exception as e:
            logger.warning(f"CV metrics failed: {e}")
            return _stub_metrics()
    else:
        return _stub_metrics()

    return metrics


def _stub_metrics() -> Dict[str, MetricResult]:
    """Return stub metrics when CV is unavailable."""
    return {
        "brightness": MetricResult(
            metric_id="brightness",
            value=128.0,
            unit="0-255",
            confidence=0.0,
            missing_reason="cv_unavailable",
        ),
        "blur": MetricResult(
            metric_id="blur",
            value=100.0,
            unit="laplacian_variance",
            confidence=0.0,
            missing_reason="cv_unavailable",
        ),
        "center_offset": MetricResult(
            metric_id="center_offset",
            value=0.0,
            unit="0-1",
            confidence=0.0,
            missing_reason="cv_unavailable",
        ),
    }


# =============================================================================
# CV Measurement Pass
# =============================================================================


class CVMeasurementPass:
    """
    VDG Pass 2: Deterministic CV measurement.

    Takes analysis plan from Pass 1 and measures:
    - center_offset: Subject centering
    - brightness: Frame brightness
    - blur: Sharpness (Laplacian variance)

    Fallback:
    - Returns stub values if OpenCV unavailable
    - Logs warnings but continues processing
    """

    def __init__(
        self,
        extraction_fps: float = DEFAULT_EXTRACTION_FPS,
        save_evidence_frames: bool = False,
        evidence_output_dir: Optional[str] = None,
    ):
        """
        Initialize CVMeasurementPass.

        Args:
            extraction_fps: FPS for frame extraction
            save_evidence_frames: Whether to save evidence frames
            evidence_output_dir: Directory for evidence frames
        """
        self.extraction_fps = extraction_fps
        self.save_evidence_frames = save_evidence_frames
        self.evidence_output_dir = evidence_output_dir

    def run(
        self,
        video_path: str,
        analysis_plan: AnalysisPlanLLM,
    ) -> Tuple[CVMeasurementResult, CVPassProvenance]:
        """
        Execute CV measurement pass.

        Args:
            video_path: Path to video file
            analysis_plan: Analysis plan from Pass 1

        Returns:
            Tuple of (CVMeasurementResult, CVPassProvenance)
        """
        start_time = datetime.now(timezone.utc)
        start_ts = time.time()

        provenance = CVPassProvenance(
            extraction_fps=self.extraction_fps,
            opencv_version=OPENCV_VERSION,
            start_time=start_time,
        )

        result = CVMeasurementResult()
        errors = []

        # Create temp directory for frames
        with tempfile.TemporaryDirectory() as temp_dir:
            frames_extracted = 0
            metrics_computed = 0

            for point in analysis_plan.points:
                try:
                    measurement = self._process_point(
                        video_path=video_path,
                        point=point,
                        temp_dir=temp_dir,
                    )
                    result.measurements.append(measurement)
                    frames_extracted += measurement.frames_analyzed
                    metrics_computed += len(measurement.metrics)

                except Exception as e:
                    logger.warning(f"Failed to process point at {point.t_center_ms}ms: {e}")
                    errors.append(f"Point {point.t_center_ms}ms: {str(e)}")

            result.total_frames_processed = frames_extracted
            result.errors = errors

        # Finalize provenance
        provenance.end_time = datetime.now(timezone.utc)
        provenance.frames_extracted = result.total_frames_processed
        provenance.metrics_computed = metrics_computed

        result.processing_time_ms = int((time.time() - start_ts) * 1000)

        logger.info(
            f"✅ CVMeasurementPass complete: "
            f"points={len(result.measurements)}, "
            f"frames={result.total_frames_processed}, "
            f"metrics={metrics_computed}, "
            f"errors={len(errors)}"
        )

        return result, provenance

    def _process_point(
        self,
        video_path: str,
        point: AnalysisPointSeedLLM,
        temp_dir: str,
    ) -> PointMeasurement:
        """
        Process a single analysis point.

        Args:
            video_path: Path to video file
            point: Analysis point to process
            temp_dir: Temp directory for frames

        Returns:
            PointMeasurement with metrics
        """
        # Extract frame at center time
        frame_path = extract_frame_at_time(
            video_path=video_path,
            t_ms=point.t_center_ms,
            output_dir=temp_dir,
        )

        if frame_path:
            metrics = compute_all_metrics(frame_path)
            frames_analyzed = 1

            # Add timestamp to metrics
            for m in metrics.values():
                m.t_ms = point.t_center_ms

            # Handle evidence frame
            evidence_path = None
            if self.save_evidence_frames and self.evidence_output_dir:
                import shutil
                evidence_path = Path(self.evidence_output_dir) / f"ev_{point.t_center_ms}.jpg"
                shutil.copy(frame_path, evidence_path)
                evidence_path = str(evidence_path)

        else:
            # Frame extraction failed
            metrics = _stub_metrics()
            for m in metrics.values():
                m.missing_reason = "frame_extraction_failed"
                m.t_ms = point.t_center_ms
            frames_analyzed = 0
            evidence_path = None

        return PointMeasurement(
            t_center_ms=point.t_center_ms,
            t_window_ms=point.t_window_ms,
            metrics=metrics,
            evidence_frame_path=evidence_path,
            frames_analyzed=frames_analyzed,
        )


# =============================================================================
# Convenience Functions
# =============================================================================


def is_cv_available() -> bool:
    """Check if OpenCV is available."""
    return CV_AVAILABLE


def get_opencv_version() -> str:
    """Get OpenCV version string."""
    return OPENCV_VERSION
