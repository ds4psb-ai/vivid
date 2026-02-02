"""Base Provider Adapter - Abstract translation layer for LogicVector → Provider prompts.

Provides the foundation for translating VDG/VPE outputs into provider-specific formats:
- LogicVector: Semantic analysis from VDG unified pipeline
- PromptCards: 7-card structured shot grammar (IR)
- Provider formats: Veo, Kling, Sora native prompt formats

The adapter pattern allows:
1. Consistent interface across all providers
2. Provider-specific optimizations (shot grammar, negative prompts, etc.)
3. A/B testing of prompt strategies per provider
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.prompt_card import PromptCards


class PromptStyle(str, Enum):
    """Prompt generation style."""

    CONCISE = "concise"  # Minimal, key elements only
    DETAILED = "detailed"  # Full description with context
    CINEMATIC = "cinematic"  # Film-style shot descriptions
    TECHNICAL = "technical"  # Technical camera/lighting terms


@dataclass
class ProviderPromptConfig:
    """Configuration for prompt generation.

    Controls how LogicVector/PromptCards are translated to provider prompts.
    """

    style: PromptStyle = PromptStyle.DETAILED
    include_negative: bool = True
    include_camera_direction: bool = True
    include_lighting: bool = True
    include_audio_cues: bool = False  # Provider-specific
    max_prompt_length: int = 2000  # Character limit
    language: str = "en"  # en, ko supported
    # Provider-specific options
    extra_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AdapterResult:
    """Result of adapter translation.

    Contains the translated prompt and metadata.
    """

    prompt: str
    negative_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    # Structured data for provider API
    provider_config: Dict[str, Any] = field(default_factory=dict)
    # Audit trail
    source_type: str = ""  # "logic_vector", "prompt_cards", "raw"
    translation_notes: List[str] = field(default_factory=list)
    # Confidence score (0-1) for translation quality
    confidence: float = 1.0


@dataclass
class LogicVector:
    """Semantic analysis output from VDG/VPE pipeline.

    This is the core "DNA" extracted from viral video analysis.
    Each field represents a dimension of the video's success factors.
    """

    # Hook Genome - Why it grabs attention
    hook_pattern: Optional[str] = None  # e.g., "curiosity_gap", "shock_reveal"
    hook_delivery: Optional[str] = None  # e.g., "fast_cut", "slow_build"
    hook_strength: float = 0.0  # 0-1 score

    # Dopamine Radar - Engagement triggers (0-10 each)
    visual_spectacle: float = 0.0
    audio_stimulation: float = 0.0
    narrative_intrigue: float = 0.0
    emotional_resonance: float = 0.0
    comedy_shock: float = 0.0

    # Mise-en-Scene - Visual elements
    lighting_style: Optional[str] = None
    color_palette: List[str] = field(default_factory=list)
    composition: Optional[str] = None

    # Camera Work
    shot_type: Optional[str] = None
    camera_movement: Optional[str] = None
    camera_angle: Optional[str] = None

    # Subject/Action
    main_subject: Optional[str] = None
    subject_action: Optional[str] = None

    # Setting
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    environment: Optional[str] = None

    # Constraints
    do_not: List[str] = field(default_factory=list)

    # Duration (milliseconds)
    duration_ms: int = 8000

    def to_system_prompt_context(self) -> str:
        """Convert to system prompt context string.

        Used when passing to LLM for further processing.
        """
        parts = []

        if self.hook_pattern:
            parts.append(f"Hook: {self.hook_pattern} ({self.hook_delivery})")

        if self.visual_spectacle > 5:
            parts.append(f"High visual impact (score: {self.visual_spectacle}/10)")

        if self.lighting_style:
            parts.append(f"Lighting: {self.lighting_style}")

        if self.color_palette:
            parts.append(f"Colors: {', '.join(self.color_palette)}")

        if self.shot_type:
            parts.append(f"Shot: {self.shot_type}")

        if self.camera_movement:
            parts.append(f"Camera: {self.camera_movement}")

        if self.main_subject:
            parts.append(f"Subject: {self.main_subject}")

        if self.subject_action:
            parts.append(f"Action: {self.subject_action}")

        if self.location:
            parts.append(f"Location: {self.location}")

        return "\n".join(parts) if parts else ""


class BaseProviderAdapter(ABC):
    """Abstract base class for provider adapters.

    Each provider adapter implements:
    1. translate_logic_vector(): LogicVector → Provider prompt
    2. compile_prompt_cards(): PromptCards → Provider prompt
    3. Provider-specific optimizations and best practices

    Subclasses:
    - VeoAdapter: Google VEO 3.1/4 optimization
    - KlingAdapter: Kling 2.6/3.0 optimization (lip sync, beat timestamps)
    - SoraAdapter: OpenAI Sora 2 optimization (storyboard mode)
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider name (e.g., 'veo', 'kling', 'sora')."""
        pass

    @property
    @abstractmethod
    def supported_features(self) -> Dict[str, bool]:
        """Features supported by this provider.

        Returns:
            Dict with feature flags:
            - storyboard_mode: Multi-shot sequence support
            - reference_images: Character/style consistency
            - frame_control: First/last frame specification
            - audio_generation: Native audio support
            - lip_sync: Lip synchronization support
            - beat_timestamps: Audio beat alignment
        """
        pass

    @property
    def max_prompt_length(self) -> int:
        """Maximum prompt length in characters."""
        return 2000

    @property
    def max_duration_seconds(self) -> int:
        """Maximum video duration in seconds."""
        return 8

    @abstractmethod
    def translate_logic_vector(
        self,
        logic_vector: LogicVector,
        config: Optional[ProviderPromptConfig] = None,
    ) -> AdapterResult:
        """Translate LogicVector to provider-specific prompt.

        This is the primary translation method for VDG/VPE outputs.

        Args:
            logic_vector: Semantic analysis from VDG pipeline
            config: Optional prompt generation configuration

        Returns:
            AdapterResult with translated prompt
        """
        pass

    @abstractmethod
    def compile_prompt_cards(
        self,
        cards: "PromptCards",
        config: Optional[ProviderPromptConfig] = None,
    ) -> AdapterResult:
        """Compile PromptCards (7-card system) to provider-specific prompt.

        PromptCards serve as an intermediate representation (IR) that
        captures shot grammar in a structured format.

        Args:
            cards: 7-card structured shot grammar
            config: Optional prompt generation configuration

        Returns:
            AdapterResult with compiled prompt
        """
        pass

    def build_negative_prompt(
        self,
        do_not: List[str],
        quality_issues: Optional[List[str]] = None,
    ) -> str:
        """Build negative prompt from constraints.

        Common quality issues are added by default.

        Args:
            do_not: List of things to avoid
            quality_issues: Additional quality issues to avoid

        Returns:
            Formatted negative prompt string
        """
        # Common quality issues for all providers
        common_issues = [
            "blurry",
            "low quality",
            "distorted",
            "artifacts",
            "watermark",
            "text overlay",
        ]

        all_negatives = list(do_not)
        if quality_issues:
            all_negatives.extend(quality_issues)
        all_negatives.extend(common_issues)

        # Deduplicate while preserving order
        seen = set()
        unique_negatives = []
        for neg in all_negatives:
            neg_lower = neg.lower()
            if neg_lower not in seen:
                seen.add(neg_lower)
                unique_negatives.append(neg)

        return ", ".join(unique_negatives)

    def _truncate_prompt(self, prompt: str, max_length: Optional[int] = None) -> str:
        """Truncate prompt to maximum length while preserving meaning.

        Tries to truncate at sentence boundaries.
        """
        max_len = max_length or self.max_prompt_length
        if len(prompt) <= max_len:
            return prompt

        # Try to truncate at sentence boundary
        truncated = prompt[:max_len]
        last_period = truncated.rfind(".")
        if last_period > max_len * 0.7:
            return truncated[: last_period + 1]

        # Fall back to word boundary
        last_space = truncated.rfind(" ")
        if last_space > max_len * 0.8:
            return truncated[:last_space] + "..."

        return truncated + "..."

    def _format_camera_instruction(
        self,
        shot_type: Optional[str],
        movement: Optional[str],
        angle: Optional[str],
    ) -> str:
        """Format camera instruction in natural language."""
        parts = []

        if shot_type:
            shot_map = {
                "wide": "wide establishing shot",
                "medium": "medium shot",
                "close_up": "close-up shot",
                "extreme_close_up": "extreme close-up",
                "pov": "point-of-view shot",
                "overhead": "overhead/bird's eye view",
                "selfie": "selfie-style framing",
                "two_shot": "two-shot composition",
            }
            parts.append(shot_map.get(shot_type, shot_type))

        if movement:
            movement_map = {
                "static": "static camera",
                "pan_left": "panning left",
                "pan_right": "panning right",
                "tilt_up": "tilting up",
                "tilt_down": "tilting down",
                "dolly_in": "dolly in",
                "dolly_out": "dolly out",
                "tracking": "tracking shot",
                "handheld": "handheld camera",
                "zoom_in": "zooming in",
                "zoom_out": "zooming out",
            }
            parts.append(movement_map.get(movement, movement))

        if angle:
            angle_map = {
                "eye_level": "at eye level",
                "low_angle": "from low angle",
                "high_angle": "from high angle",
                "dutch_angle": "dutch/tilted angle",
            }
            parts.append(angle_map.get(angle, angle))

        return ", ".join(parts) if parts else ""

    def _format_lighting_instruction(
        self,
        lighting: Optional[str],
        color_palette: Optional[List[str]],
    ) -> str:
        """Format lighting and color instructions."""
        parts = []

        if lighting:
            parts.append(f"{lighting} lighting")

        if color_palette:
            colors = ", ".join(color_palette[:3])  # Limit to 3 colors
            parts.append(f"color palette: {colors}")

        return ", ".join(parts) if parts else ""


__all__ = [
    "BaseProviderAdapter",
    "AdapterResult",
    "ProviderPromptConfig",
    "PromptStyle",
    "LogicVector",
]
