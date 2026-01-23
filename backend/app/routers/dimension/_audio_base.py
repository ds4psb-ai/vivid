"""
Audio Dimension Base Module - Common Utilities

Shared utilities for audio-related dimension routers (sound.py, suno.py).
Extracted for P1.2 consolidation.

Contents:
- XSS sanitization helpers
- Trace ID generation
- evidence_refs building
- Common enums and models

Security:
- XSS sanitization patterns
- Input validation helpers

2026 Best Practices:
- RAG Protocol v2: trace_id, evidence_refs (List[str])
- Platform capabilities (Suno v5, Udio, MiniMax)
"""
from __future__ import annotations

import html
import re
import uuid
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


# =============================================================================
# XSS Sanitization
# =============================================================================

def sanitize_audio_text(value: str, default: str = "") -> str:
    """Sanitize text fields to prevent XSS.

    Used for: concept, storyboard, mood, topic, prompt, title, style

    Args:
        value: Raw text input
        default: Default value if empty

    Returns:
        Sanitized string
    """
    if not value:
        return default
    value = value.strip()
    if not value:
        return default
    # Remove HTML tags
    value = re.sub(r"<[^>]+>", "", value)
    # Escape HTML entities
    value = html.escape(value)
    # Remove script/javascript patterns
    value = re.sub(r"(?i)javascript\s*:", "", value)
    value = re.sub(r"(?i)on\w+\s*=", "", value)
    return value or default


# =============================================================================
# Trace ID Generation
# =============================================================================

def generate_audio_trace_id(prefix: str = "audio") -> str:
    """Generate a trace ID for RAG Protocol v2.

    Args:
        prefix: Trace ID prefix (e.g., "sc" for sound craft, "suno", "lyr" for lyrics)

    Returns:
        Unique trace ID (e.g., "sc-abc123def456")
    """
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# =============================================================================
# Evidence Refs Building
# =============================================================================

def build_audio_evidence_refs(
    *,
    operation: str,
    platform: str | None = None,
    genre: str | None = None,
    tempo: str | None = None,
    sound_type: str | None = None,
    model: str | None = None,
    extra_refs: List[str] | None = None,
) -> List[str]:
    """Build evidence_refs list for RAG Protocol v2.

    Args:
        operation: Operation name (e.g., "sound_craft", "lyrics", "suno_generate")
        platform: Target platform (e.g., "suno", "udio")
        genre: Music genre
        tempo: Tempo setting
        sound_type: Type of sound (e.g., "bgm", "narration")
        model: AI model used
        extra_refs: Additional references to include

    Returns:
        List of evidence reference strings
    """
    refs: List[str] = []

    if operation:
        refs.append(f"rag:{operation}")

    if platform:
        refs.append(f"config:platform:{platform}")

    if genre:
        refs.append(f"config:genre:{genre}")

    if tempo:
        refs.append(f"config:tempo:{tempo}")

    if sound_type:
        refs.append(f"config:sound_type:{sound_type}")

    if model:
        refs.append(f"db:model:{model}")

    if extra_refs:
        refs.extend(extra_refs)

    return refs


# =============================================================================
# Common Enums (2026 Audio Platforms)
# =============================================================================

class AudioPlatform(str, Enum):
    """Supported audio generation platforms (2026)."""
    SUNO = "suno"
    UDIO = "udio"
    ELEVENLABS = "elevenlabs"
    MINIMAX = "minimax"  # MiniMax Music-2.0


class AudioQuality(str, Enum):
    """Audio quality levels (2026 industry standards)."""
    STANDARD = "standard"  # 32 kHz
    HIGH = "high"  # 44.1 kHz (CD quality)
    STUDIO = "studio"  # 48 kHz (broadcast quality)


class StemExportFormat(str, Enum):
    """Stem export formats (Suno v5 feature)."""
    WAV = "wav"
    MIDI = "midi"
    MP3 = "mp3"


# =============================================================================
# Common Validation Sets
# =============================================================================

ALLOWED_TEMPOS = frozenset({"slow", "medium", "fast", "very-slow", "very-fast"})
ALLOWED_AUDIO_PLATFORMS = frozenset({"suno", "udio", "elevenlabs", "minimax"})
ALLOWED_LANGUAGE_MIX = frozenset({"korean", "english", "japanese", "mixed"})
ALLOWED_SONG_STRUCTURES = frozenset({
    "verse-chorus-verse-chorus-bridge-chorus",
    "verse-chorus-verse-chorus",
    "intro-verse-chorus-verse-chorus-outro",
    "aaba",
    "ababcb",
    "custom",
})


# =============================================================================
# Validation Helpers
# =============================================================================

def validate_tempo(value: str) -> str:
    """Validate tempo is in allowed list.

    Args:
        value: Raw tempo

    Returns:
        Validated tempo

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip().lower()
    if value not in ALLOWED_TEMPOS:
        raise ValueError(
            f"지원하지 않는 템포: {value}. Allowed: {sorted(ALLOWED_TEMPOS)}"
        )
    return value


def validate_audio_platform(value: str) -> str:
    """Validate target_platform is in allowed audio platform list.

    Args:
        value: Raw platform

    Returns:
        Validated platform

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip().lower()
    if value not in ALLOWED_AUDIO_PLATFORMS:
        raise ValueError(
            f"지원하지 않는 오디오 플랫폼: {value}. Allowed: {sorted(ALLOWED_AUDIO_PLATFORMS)}"
        )
    return value


# =============================================================================
# Platform Capability Models
# =============================================================================

class SunoV5Capabilities(BaseModel):
    """Suno v5 (2026) platform capabilities.

    Reference: Studio-grade 44.1 kHz, 12-stem export, MIDI, 8-min tracks.
    """
    max_duration_seconds: int = Field(480, description="8-minute extended tracks")
    sample_rate_khz: float = Field(44.1, description="Studio-grade 44.1 kHz")
    max_stems: int = Field(12, description="12 time-aligned WAV stems")
    supports_midi_export: bool = Field(True, description="MIDI export capability")
    supports_audio_upload: bool = Field(True, description="Audio clip input")
    supports_vocals_upload: bool = Field(True, description="Vocal upload for guidance")


class UdioCapabilities(BaseModel):
    """Udio (2026) platform capabilities.

    Reference: Higher audio fidelity (48 kHz), complex song structures.
    """
    max_duration_seconds: int = Field(300, description="5-minute tracks")
    sample_rate_khz: float = Field(48.0, description="Broadcast-grade 48 kHz")
    supports_detailed_remixing: bool = Field(True, description="Detailed remix control")
    supports_song_extensions: bool = Field(True, description="Iterative extension")
    vocal_quality: str = Field("human-like", description="More realistic vocal synthesis")


# =============================================================================
# Common Response Models
# =============================================================================

class AudioGenerationTraceInfo(BaseModel):
    """RAG Protocol v2 trace information for audio generation."""
    trace_id: str = Field("", description="Trace ID for auditability")
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="RAG evidence references"
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="AI confidence score")
