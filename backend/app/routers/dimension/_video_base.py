"""
Video Dimension Base Module - Common Utilities

Shared utilities for video-related dimension routers (veo.py, kling.py).
Extracted for P1.2 consolidation.

Contents:
- XSS sanitization helpers
- Trace ID generation
- evidence_refs building
- Common enums and models
- Platform capabilities

Security:
- XSS sanitization patterns
- Input validation helpers

2026 Best Practices:
- RAG Protocol v2: trace_id, evidence_refs (List[str])
- Platform capabilities (Veo 3.1, Kling 2.6, Sora 2)
- Native audio integration
- Character consistency support
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

def sanitize_video_text(value: str, default: str = "") -> str:
    """Sanitize text fields to prevent XSS.

    Used for: prompt, negative_prompt, style

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

def generate_video_trace_id(prefix: str = "video") -> str:
    """Generate a trace ID for RAG Protocol v2.

    Args:
        prefix: Trace ID prefix (e.g., "veo", "kling", "veos" for veo stream)

    Returns:
        Unique trace ID (e.g., "veo-abc123def456")
    """
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# =============================================================================
# Evidence Refs Building
# =============================================================================

def build_video_evidence_refs(
    *,
    operation: str,
    model: str | None = None,
    style: str | None = None,
    aspect_ratio: str | None = None,
    duration: int | str | None = None,
    character_ids: List[str] | None = None,
    extra_refs: List[str] | None = None,
) -> List[str]:
    """Build evidence_refs list for RAG Protocol v2.

    Args:
        operation: Operation name (e.g., "veo_generate", "kling_generate")
        model: AI model used
        style: Visual style
        aspect_ratio: Aspect ratio setting
        duration: Video duration
        character_ids: Character UUIDs for consistency tracking
        extra_refs: Additional references to include

    Returns:
        List of evidence reference strings
    """
    refs: List[str] = []

    if operation:
        refs.append(f"rag:{operation}")

    if model:
        refs.append(f"config:model:{model}")

    if style:
        refs.append(f"rag:video:style:{style}")

    if aspect_ratio:
        refs.append(f"config:aspect_ratio:{aspect_ratio}")

    if duration:
        refs.append(f"config:duration:{duration}s" if isinstance(duration, int) else f"config:duration:{duration}")

    if character_ids:
        for char_id in character_ids[:3]:  # Max 3 characters
            refs.append(f"db:character:{char_id}")

    if extra_refs:
        refs.extend(extra_refs)

    return refs


# =============================================================================
# Common Enums (2026 Video Platforms)
# =============================================================================

class VideoGenerationPlatform(str, Enum):
    """Supported video generation platforms (2026)."""
    VEO = "veo"  # Google Veo 3.1
    KLING = "kling"  # Kling 2.6 (native audio)
    SORA = "sora"  # OpenAI Sora 2
    HAILUO = "hailuo"  # Hailuo T2V-01
    SEEDANCE = "seedance"  # Seedance 1.5 Pro (budget)
    RUNWAY = "runway"  # Runway Gen-4


class VideoOutputQuality(str, Enum):
    """Video output quality levels (2026 standards)."""
    SD = "sd"  # 480p
    HD = "hd"  # 720p
    FHD = "fhd"  # 1080p (most common)
    UHD = "uhd"  # 4K (Runway Gen-4)


class AudioIntegrationMode(str, Enum):
    """Audio integration modes (2026 trend: native audio)."""
    NONE = "none"  # No audio
    NATIVE = "native"  # Platform-native audio generation
    SYNC = "sync"  # Synced audio from external source
    DIALOGUE = "dialogue"  # Lip-synced dialogue (Kling 2.6)


class CameraMovement(str, Enum):
    """Common camera movements supported by video platforms."""
    STATIC = "static"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    ORBIT = "orbit"
    TRACKING = "tracking"


class MotionIntensity(str, Enum):
    """Motion intensity presets."""
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"
    DRAMATIC = "dramatic"


# =============================================================================
# Common Validation Sets
# =============================================================================

ALLOWED_ASPECT_RATIOS = frozenset({"16:9", "9:16", "1:1", "4:3", "3:4"})
ALLOWED_RESOLUTIONS = frozenset({"720p", "1080p", "4k"})
ALLOWED_DURATIONS_VEO = frozenset({4, 5, 6, 7, 8})  # Veo: 4-8 seconds
ALLOWED_DURATIONS_KLING = frozenset({"5", "10"})  # Kling: 5 or 10 seconds

# Camera movement keywords for prompt quality detection
CAMERA_MOVEMENT_KEYWORDS = frozenset([
    "pan", "tilt", "zoom", "dolly", "track", "orbit", "crane", "steady",
    "aerial", "handheld", "close-up", "wide shot", "static", "following"
])


# =============================================================================
# Validation Helpers
# =============================================================================

def validate_aspect_ratio(value: str, allowed: frozenset | None = None) -> str:
    """Validate aspect ratio is in allowed list.

    Args:
        value: Raw aspect ratio
        allowed: Optional custom allowed set

    Returns:
        Validated aspect ratio

    Raises:
        ValueError: If not in allowed list
    """
    allowed = allowed or ALLOWED_ASPECT_RATIOS
    value = value.strip()
    if value not in allowed:
        raise ValueError(
            f"지원하지 않는 화면 비율: {value}. Allowed: {sorted(allowed)}"
        )
    return value


def validate_resolution(value: str, allowed: frozenset | None = None) -> str:
    """Validate resolution is in allowed list.

    Args:
        value: Raw resolution
        allowed: Optional custom allowed set

    Returns:
        Validated resolution

    Raises:
        ValueError: If not in allowed list
    """
    allowed = allowed or ALLOWED_RESOLUTIONS
    value = value.strip().lower()
    if value not in allowed:
        raise ValueError(
            f"지원하지 않는 해상도: {value}. Allowed: {sorted(allowed)}"
        )
    return value


# =============================================================================
# Platform Capability Models
# =============================================================================

class Veo31Capabilities(BaseModel):
    """Veo 3.1 (Oct 2025) platform capabilities.

    Reference: Native audio, multi-image consistency, 60s max, 1080p.
    Pricing: $0.15-0.40/sec
    """
    max_duration_seconds: int = Field(60, description="60-second max")
    resolution: VideoOutputQuality = Field(VideoOutputQuality.FHD, description="1080p FHD")
    supports_native_audio: bool = Field(True, description="Native audio generation")
    supports_multi_image: bool = Field(True, description="Multi-image consistency")
    supports_camera_control: bool = Field(True, description="Camera control (Oct 2025)")
    pricing_per_second: float = Field(0.25, description="Average $0.15-0.40/sec")


class Kling26Capabilities(BaseModel):
    """Kling 2.6 (Dec 2025) platform capabilities.

    Reference: Native audio + dialogue sync, 2-minute duration, high action.
    """
    max_duration_seconds: int = Field(120, description="2-minute max")
    resolution: VideoOutputQuality = Field(VideoOutputQuality.FHD, description="1080p FHD")
    supports_native_audio: bool = Field(True, description="Native audio + SFX")
    supports_dialogue_sync: bool = Field(True, description="Lip-synced dialogue")
    supports_high_action: bool = Field(True, description="High action scenes")
    frame_rate: int = Field(48, description="Up to 48 FPS")


class Sora2Capabilities(BaseModel):
    """Sora 2 (OpenAI, 2026) platform capabilities.

    Reference: Social integration, narrative coherence.
    """
    max_duration_seconds: int = Field(60, description="60-second max")
    resolution: VideoOutputQuality = Field(VideoOutputQuality.FHD, description="1080p FHD")
    supports_native_audio: bool = Field(True, description="Native audio generation")
    supports_narrative: bool = Field(True, description="Narrative coherence")
    supports_social_integration: bool = Field(True, description="Social platform integration")


# =============================================================================
# Common Response Models
# =============================================================================

class VideoGenerationTraceInfo(BaseModel):
    """RAG Protocol v2 trace information for video generation."""
    trace_id: str = Field("", description="Trace ID for auditability")
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="RAG evidence references"
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="AI confidence score")


class VideoGenerationResult(BaseModel):
    """Comprehensive video generation result (2026 pattern).

    Includes platform-specific metadata, character consistency tracking,
    and RAG Protocol v2 fields.
    """
    success: bool = Field(False, description="Generation success")
    video_uri: str = Field("", description="Generated video URI")
    duration_ms: int = Field(0, description="Generation time in ms")
    credit_cost: int = Field(0, description="Credits consumed")

    # Platform info
    platform: VideoGenerationPlatform = Field(
        VideoGenerationPlatform.VEO,
        description="Platform used"
    )
    output_quality: VideoOutputQuality = Field(
        VideoOutputQuality.FHD,
        description="Output quality"
    )
    audio_mode: AudioIntegrationMode = Field(
        AudioIntegrationMode.NATIVE,
        description="Audio integration mode"
    )

    # Character consistency (2026 trend)
    characters_used: List[str] = Field(
        default_factory=list,
        description="Character IDs used for consistency"
    )

    # RAG Protocol v2 fields
    trace_id: str = Field("", description="Trace ID for auditability")
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="RAG evidence references"
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="AI confidence score")


# =============================================================================
# Kling-specific: Tone Descriptors and Prompt Quality
# =============================================================================

class KlingToneDescriptor(str, Enum):
    """Tone descriptors for dialogue (2026 Best Practice).

    These influence both voice generation and facial expression.
    """
    WHISPERING = "whispering"
    SHOUTING = "shouting"
    BREATHY = "breathy"
    RESIGNED = "resigned"
    EXCITED = "excited"
    CALM = "calm"
    NERVOUS = "nervous"
    ANGRY = "angry"
    WEARY = "weary"
    PLAYFUL = "playful"


# Regex patterns for Kling prompt quality assessment
BEAT_TIMESTAMP_PATTERN = re.compile(r"Beat\s*\d+-\d+s:", re.IGNORECASE)
DIALOGUE_PATTERN = re.compile(r'\([^)]+\):\s*"[^"]*"', re.IGNORECASE)
TONE_DESCRIPTOR_PATTERN = re.compile(
    r"\((" + "|".join([t.value for t in KlingToneDescriptor]) + r")\)",
    re.IGNORECASE
)


def assess_video_prompt_quality(
    prompt: str,
    negative_prompt: str | None = None,
    platform: VideoGenerationPlatform = VideoGenerationPlatform.VEO,
) -> dict:
    """Assess video prompt quality based on platform best practices.

    Args:
        prompt: The main video generation prompt
        negative_prompt: Optional negative prompt
        platform: Target platform for platform-specific checks

    Returns:
        Dict with quality flags and overall score
    """
    prompt_lower = prompt.lower()
    neg_lower = (negative_prompt or "").lower()

    result = {
        "has_camera_movement": any(kw in prompt_lower for kw in CAMERA_MOVEMENT_KEYWORDS),
        "has_negative_prompt": bool(negative_prompt),
        "overall_score": 0.0,
    }

    # Platform-specific checks
    if platform == VideoGenerationPlatform.KLING:
        result["has_beat_timestamps"] = bool(BEAT_TIMESTAMP_PATTERN.search(prompt))
        result["has_dialogue"] = bool(DIALOGUE_PATTERN.search(prompt))
        result["has_tone_descriptors"] = bool(TONE_DESCRIPTOR_PATTERN.search(prompt))

        # Kling quality score
        score_components = [
            result["has_beat_timestamps"],  # 0.20
            result["has_dialogue"],  # 0.20
            result["has_tone_descriptors"],  # 0.15
            result["has_camera_movement"],  # 0.15
            result["has_negative_prompt"],  # 0.15
        ]
        weights = [0.20, 0.20, 0.15, 0.15, 0.15]
        result["overall_score"] = round(sum(w for w, c in zip(weights, score_components) if c), 2)

    elif platform == VideoGenerationPlatform.VEO:
        # Veo quality score (simpler)
        score_components = [
            result["has_camera_movement"],  # 0.30
            result["has_negative_prompt"],  # 0.30
            len(prompt) > 100,  # 0.20 - Detailed prompt
            len(prompt) < 2000,  # 0.20 - Not too long
        ]
        weights = [0.30, 0.30, 0.20, 0.20]
        result["overall_score"] = round(sum(w for w, c in zip(weights, score_components) if c), 2)

    return result
