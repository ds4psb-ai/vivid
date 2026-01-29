"""Storyboard Schemas - Multi-shot video generation for Veo 4/Kling 3.0/Sora 2.

Storyboard mode enables:
- Multi-shot sequences with coherent transitions
- Character/style consistency across shots
- First/last frame control for shot-to-shot continuity
- Total duration up to 25-120 seconds (provider-dependent)

2026 Provider Support:
- Sora 2 Pro: Native storyboard (1s segments, 25s max)
- Veo 4: Extended duration (30-60s chunks) - Coming soon
- Kling 3.0: Extended duration (30-120s) - Coming soon

Architecture:
    StoryboardRequest
           ↓
    StoryboardOrchestrator.execute()
           ↓
    [Shot 1] → [Shot 2] → [Shot 3] → ...
           ↓           ↓           ↓
    last_frame → first_frame (coherence chain)
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from app.schemas.base import StrictBaseModel


class TransitionType(str, Enum):
    """Shot-to-shot transition types."""

    CUT = "cut"  # Hard cut (default)
    DISSOLVE = "dissolve"  # Cross-dissolve
    FADE = "fade"  # Fade to/from black
    WIPE = "wipe"  # Wipe transition
    MATCH_CUT = "match_cut"  # Match action cut
    JUMP_CUT = "jump_cut"  # Jump cut
    MORPH = "morph"  # Morph/blend (AI-native)


class CoherenceLevel(str, Enum):
    """Shot-to-shot coherence requirements."""

    CHARACTER = "character"  # Maintain character consistency
    STYLE = "style"  # Maintain visual style
    BOTH = "both"  # Character + style consistency
    NONE = "none"  # No coherence requirement


class StoryboardProvider(str, Enum):
    """Providers supporting storyboard mode."""

    SORA = "sora"  # Native storyboard
    VEO = "veo"  # Chained generation
    KLING = "kling"  # Chained generation


class ShotPhase(str, Enum):
    """Narrative phase for shot."""

    HOOK = "hook"  # Opening hook (0-3s)
    DEVELOPMENT = "development"  # Story development
    PAYOFF = "payoff"  # Conclusion/CTA


# =============================================================================
# Shot Models
# =============================================================================


class ShotCameraInfo(BaseModel):
    """Camera information for a single shot."""

    shot_type: Optional[str] = Field(None, description="wide, medium, close_up, etc.")
    movement: Optional[str] = Field(None, description="static, pan, dolly, tracking, etc.")
    angle: Optional[str] = Field(None, description="eye_level, low_angle, high_angle")


class ShotMiseEnScene(BaseModel):
    """Visual elements for a single shot."""

    lighting: Optional[str] = Field(None, description="Lighting style")
    color_palette: Optional[List[str]] = Field(None, description="Color palette")
    composition: Optional[str] = Field(None, description="Frame composition")


class StoryboardShot(BaseModel):
    """Single shot definition in a storyboard.

    Each shot represents a continuous segment that will be generated
    as a single video clip.
    """

    # Core
    index: int = Field(..., ge=0, description="Shot index (0-based)")
    prompt: str = Field(..., min_length=5, description="Shot prompt/description")

    # Timing
    duration_seconds: float = Field(
        default=3.0,
        ge=1.0,
        le=30.0,
        description="Shot duration in seconds",
    )
    start_ms: Optional[int] = Field(None, description="Start time in sequence (ms)")
    end_ms: Optional[int] = Field(None, description="End time in sequence (ms)")

    # Narrative
    phase: ShotPhase = Field(default=ShotPhase.DEVELOPMENT, description="Narrative phase")
    what_to_see: Optional[str] = Field(None, description="Key action/visual to capture")

    # Camera
    camera: Optional[ShotCameraInfo] = Field(None, description="Camera info")

    # Visual
    mise_en_scene: Optional[ShotMiseEnScene] = Field(None, description="Visual elements")

    # Transition
    transition_to_next: TransitionType = Field(
        default=TransitionType.CUT,
        description="Transition to next shot",
    )

    # Coherence
    reference_from_previous: bool = Field(
        default=True,
        description="Use last frame of previous shot as first frame reference",
    )

    # Reference images (character/style)
    reference_images: List[str] = Field(
        default_factory=list,
        description="Reference image URLs for consistency",
    )

    # Frame control
    first_frame_url: Optional[str] = Field(
        None,
        description="URL of first frame (for continuity from previous shot)",
    )
    last_frame_url: Optional[str] = Field(
        None,
        description="URL of last frame (for continuity to next shot)",
    )


# =============================================================================
# Storyboard Request/Response Models
# =============================================================================


class StoryboardRequest(StrictBaseModel):
    """Request to generate a multi-shot storyboard video (strict mode for type safety).

    Example:
        request = StoryboardRequest(
            shots=[
                StoryboardShot(index=0, prompt="Wide establishing shot of city", phase="hook"),
                StoryboardShot(index=1, prompt="Medium shot of character walking", phase="development"),
                StoryboardShot(index=2, prompt="Close-up of character's face", phase="payoff"),
            ],
            total_duration_seconds=15,
            coherence_level=CoherenceLevel.BOTH,
        )
    """

    # Shots
    shots: List[StoryboardShot] = Field(
        ...,
        min_length=2,
        max_length=25,  # Sora 2 Pro max segments
        description="Ordered list of shots",
    )

    # Timing
    total_duration_seconds: int = Field(
        ...,
        ge=2,
        le=120,  # Kling 3.0 max
        description="Total video duration in seconds",
    )

    # Coherence
    coherence_level: CoherenceLevel = Field(
        default=CoherenceLevel.BOTH,
        description="Shot-to-shot coherence requirements",
    )

    # Character references (apply to all shots)
    global_reference_images: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="Global reference images for character/style consistency",
    )

    # Provider
    provider: StoryboardProvider = Field(
        default=StoryboardProvider.SORA,
        description="Target provider for generation",
    )

    # Generation options
    aspect_ratio: str = Field(default="16:9", description="Video aspect ratio")
    resolution: str = Field(default="1080p", description="Video resolution")
    include_audio: bool = Field(default=True, description="Generate audio")

    # Style
    visual_style: Optional[str] = Field(
        None,
        description="Global visual style (e.g., 'cinematic', 'anime', 'documentary')",
    )
    negative_prompt: Optional[str] = Field(
        None,
        description="Global negative prompt",
    )

    @field_validator("shots")
    @classmethod
    def validate_shot_indices(cls, shots: List[StoryboardShot]) -> List[StoryboardShot]:
        """Ensure shot indices are sequential."""
        for i, shot in enumerate(shots):
            if shot.index != i:
                shot.index = i  # Auto-fix indices
        return shots

    def get_shot_by_phase(self, phase: ShotPhase) -> List[StoryboardShot]:
        """Get shots by narrative phase."""
        return [s for s in self.shots if s.phase == phase]


class ShotGenerationResult(BaseModel):
    """Result of generating a single shot."""

    shot_index: int
    success: bool
    media_uri: Optional[str] = None
    first_frame_uri: Optional[str] = None  # Extracted for continuity
    last_frame_uri: Optional[str] = None  # Extracted for continuity
    duration_ms: int = 0
    error: Optional[str] = None
    provider: str = ""
    trace_id: str = ""


class StoryboardResult(BaseModel):
    """Result of storyboard generation.

    Contains individual shot results and final composite (if available).
    """

    # Overall status
    success: bool
    provider: str
    trace_id: str

    # Timing
    total_duration_ms: int = 0
    generation_latency_ms: int = 0

    # Shot results
    shot_results: List[ShotGenerationResult] = Field(default_factory=list)
    shots_completed: int = 0
    shots_failed: int = 0

    # Final output
    composite_media_uri: Optional[str] = Field(
        None,
        description="Combined video URI (if provider supports native storyboard)",
    )
    individual_clips: List[str] = Field(
        default_factory=list,
        description="Individual clip URIs (for manual assembly)",
    )

    # Coherence tracking
    coherence_chain: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Frame chain for shot-to-shot coherence",
    )

    # Cost
    credits_used: int = 0
    evidence_refs: List[str] = Field(default_factory=list)

    # Errors
    error: Optional[str] = None
    error_code: Optional[str] = None


# =============================================================================
# Storyboard Progress
# =============================================================================


class StoryboardProgress(BaseModel):
    """Progress update during storyboard generation."""

    status: str  # "pending", "processing", "completed", "failed"
    current_shot: int = 0
    total_shots: int = 0
    progress: float = 0.0  # 0.0 to 1.0
    message: str = ""
    elapsed_seconds: float = 0.0
    estimated_remaining_seconds: Optional[float] = None


# =============================================================================
# API Models
# =============================================================================


class CreateStoryboardRequest(StrictBaseModel):
    """POST /production/storyboard - Create storyboard generation request (strict mode)."""

    storyboard: StoryboardRequest
    webhook_url: Optional[str] = Field(
        None,
        description="URL to POST completion notification",
    )
    priority: str = Field(default="normal", description="Queue priority")


class StoryboardStatusResponse(BaseModel):
    """GET /production/storyboard/{job_id} - Get storyboard status."""

    job_id: str
    status: str
    progress: StoryboardProgress
    result: Optional[StoryboardResult] = None
    created_at: str
    updated_at: str


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "TransitionType",
    "CoherenceLevel",
    "StoryboardProvider",
    "ShotPhase",
    # Shot models
    "ShotCameraInfo",
    "ShotMiseEnScene",
    "StoryboardShot",
    # Request/Response
    "StoryboardRequest",
    "ShotGenerationResult",
    "StoryboardResult",
    "StoryboardProgress",
    # API
    "CreateStoryboardRequest",
    "StoryboardStatusResponse",
]
