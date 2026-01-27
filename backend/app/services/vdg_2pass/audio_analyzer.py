"""
Audio Analyzer for VDG Pipeline

Uses librosa for audio analysis:
- BPM detection
- Onset detection (beat timestamps)
- Basic audio features

Graceful degradation:
- Returns stub values if librosa unavailable
- Logs warnings but continues processing
"""
from __future__ import annotations

import logging
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Check librosa availability
# =============================================================================

LIBROSA_AVAILABLE = False

try:
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    logger.warning("librosa not available, audio analysis will use stub values")


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class AudioAnalysis:
    """Audio analysis result."""
    has_audio: bool = False
    bpm: Optional[float] = None
    onset_timestamps: List[float] = field(default_factory=list)
    beat_timestamps: List[float] = field(default_factory=list)
    rms_db: Optional[float] = None
    spectral_centroid: Optional[float] = None
    duration_seconds: float = 0.0


# =============================================================================
# Audio Extraction
# =============================================================================


def extract_audio_from_video(video_path: str, output_path: str) -> bool:
    """
    Extract audio track from video using ffmpeg.

    Args:
        video_path: Path to video file
        output_path: Path for output WAV file

    Returns:
        True if extraction successful
    """
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i", video_path,
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # WAV format
                "-ar", "22050",  # Sample rate
                "-ac", "1",  # Mono
                "-y",  # Overwrite
                output_path,
            ],
            capture_output=True,
            timeout=30,
        )
        return result.returncode == 0 and Path(output_path).exists()
    except Exception as e:
        logger.warning(f"Audio extraction failed: {e}")
        return False


# =============================================================================
# Audio Analysis
# =============================================================================


def analyze_audio(video_path: str) -> AudioAnalysis:
    """
    Analyze audio from video file.

    Extracts:
    - BPM (beats per minute)
    - Onset timestamps (where sound events start)
    - Beat timestamps
    - RMS loudness
    - Spectral centroid (brightness)

    Args:
        video_path: Path to video file

    Returns:
        AudioAnalysis with extracted features
    """
    if not LIBROSA_AVAILABLE:
        logger.warning("librosa not available, returning stub audio analysis")
        return AudioAnalysis(has_audio=False)

    analysis = AudioAnalysis()

    with tempfile.TemporaryDirectory() as temp_dir:
        audio_path = Path(temp_dir) / "audio.wav"

        # Extract audio from video
        if not extract_audio_from_video(video_path, str(audio_path)):
            logger.info("No audio track found or extraction failed")
            return analysis

        try:
            # Load audio
            y, sr = librosa.load(str(audio_path), sr=22050, mono=True)

            if len(y) == 0:
                logger.info("Audio track is empty")
                return analysis

            analysis.has_audio = True
            analysis.duration_seconds = float(len(y) / sr)

            # BPM detection
            try:
                tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
                # Handle both scalar and array returns
                if hasattr(tempo, "__len__"):
                    analysis.bpm = float(tempo[0]) if len(tempo) > 0 else None
                else:
                    analysis.bpm = float(tempo) if tempo > 0 else None
                analysis.beat_timestamps = librosa.frames_to_time(beat_frames, sr=sr).tolist()
            except Exception as e:
                logger.warning(f"BPM detection failed: {e}")

            # Onset detection
            try:
                onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
                analysis.onset_timestamps = librosa.frames_to_time(onset_frames, sr=sr).tolist()
            except Exception as e:
                logger.warning(f"Onset detection failed: {e}")

            # RMS loudness
            try:
                rms = librosa.feature.rms(y=y)[0]
                avg_rms = float(np.mean(rms))
                # Convert to dB (avoid log(0))
                if avg_rms > 0:
                    analysis.rms_db = float(20 * np.log10(avg_rms))
            except Exception as e:
                logger.warning(f"RMS calculation failed: {e}")

            # Spectral centroid (brightness)
            try:
                cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
                analysis.spectral_centroid = float(np.mean(cent))
            except Exception as e:
                logger.warning(f"Spectral centroid failed: {e}")

            logger.info(
                f"Audio analysis complete: "
                f"duration={analysis.duration_seconds:.1f}s, "
                f"BPM={analysis.bpm}, "
                f"onsets={len(analysis.onset_timestamps)}"
            )

        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            analysis.has_audio = False

    return analysis


def get_audio_summary(analysis: AudioAnalysis) -> str:
    """
    Generate text summary of audio analysis for LLM context.

    Args:
        analysis: AudioAnalysis result

    Returns:
        Summary string for LLM prompt
    """
    if not analysis.has_audio:
        return "No audio track detected."

    parts = [f"Duration: {analysis.duration_seconds:.1f}s"]

    if analysis.bpm:
        parts.append(f"BPM: {analysis.bpm:.1f}")

    if analysis.onset_timestamps:
        # First 5 onsets
        first_onsets = analysis.onset_timestamps[:5]
        onset_str = ", ".join([f"{t:.2f}s" for t in first_onsets])
        parts.append(f"First onsets at: {onset_str}")

        # Average onset density
        if analysis.duration_seconds > 0:
            density = len(analysis.onset_timestamps) / analysis.duration_seconds
            parts.append(f"Onset density: {density:.1f}/sec")

    if analysis.beat_timestamps:
        # First 5 beats
        first_beats = analysis.beat_timestamps[:5]
        beat_str = ", ".join([f"{t:.2f}s" for t in first_beats])
        parts.append(f"First beats at: {beat_str}")

    if analysis.rms_db is not None:
        # Loudness level
        if analysis.rms_db > -20:
            level = "loud"
        elif analysis.rms_db > -40:
            level = "moderate"
        else:
            level = "quiet"
        parts.append(f"Loudness: {level} ({analysis.rms_db:.1f} dB)")

    return " | ".join(parts)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "AudioAnalysis",
    "analyze_audio",
    "get_audio_summary",
    "LIBROSA_AVAILABLE",
]
