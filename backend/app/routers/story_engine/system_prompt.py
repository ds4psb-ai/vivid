"""System Prompt Generator - Converts Logic Vector to Shot Grammar Prompts.

Transforms DNA Lab's Logic Vector into platform-specific system prompts
for video generation (VEO, Kling, etc.).

Features:
- Logic Vector → Shot Grammar conversion
- Platform-specific optimizations
- Multi-language support
- Prompt length management

Usage:
    from app.routers.story_engine.system_prompt import SystemPromptGenerator

    generator = SystemPromptGenerator()
    prompt = generator.generate(
        logic_vector=lv,
        story_structure=story,
        target_platform="veo",
    )
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from app.schemas.vpe import LogicVector

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

class TargetPlatform(str, Enum):
    """Supported video generation platforms."""
    VEO = "veo"
    KLING = "kling"
    RUNWAY = "runway"
    PIKA = "pika"
    SUNO = "suno"  # Audio
    GENERIC = "generic"


# Platform-specific prompt templates
PLATFORM_TEMPLATES = {
    TargetPlatform.VEO: {
        "max_length": 1500,
        "style_prefix": "Cinematic video in the style of {auteur}.",
        "camera_prefix": "Camera: ",
        "lighting_prefix": "Lighting: ",
        "composition_prefix": "Composition: ",
        "pacing_prefix": "Pacing: ",
        "color_prefix": "Color grade: ",
        "supports_negative": True,
        "negative_prefix": "Avoid: ",
    },
    TargetPlatform.KLING: {
        "max_length": 1000,
        "style_prefix": "{auteur} style cinematic shot.",
        "camera_prefix": "Movement: ",
        "lighting_prefix": "Light: ",
        "composition_prefix": "Frame: ",
        "pacing_prefix": "Tempo: ",
        "color_prefix": "Grade: ",
        "supports_negative": True,
        "negative_prefix": "No: ",
    },
    TargetPlatform.RUNWAY: {
        "max_length": 1200,
        "style_prefix": "Director style: {auteur}.",
        "camera_prefix": "Camera movement: ",
        "lighting_prefix": "Lighting style: ",
        "composition_prefix": "Composition: ",
        "pacing_prefix": "Rhythm: ",
        "color_prefix": "Color palette: ",
        "supports_negative": False,
        "negative_prefix": "",
    },
    TargetPlatform.GENERIC: {
        "max_length": 2000,
        "style_prefix": "Following the visual style of {auteur}.",
        "camera_prefix": "Camera: ",
        "lighting_prefix": "Lighting: ",
        "composition_prefix": "Composition: ",
        "pacing_prefix": "Pacing: ",
        "color_prefix": "Color: ",
        "supports_negative": True,
        "negative_prefix": "Avoid: ",
    },
}


# Auteur style descriptions
AUTEUR_STYLE_HINTS = {
    "bong": "Bong Joon-ho's signature style with vertical blocking, stark class contrasts, and deliberate camera movements",
    "nolan": "Christopher Nolan's precise cinematography with IMAX-scale compositions and practical lighting",
    "kubrick": "Stanley Kubrick's symmetrical framing, one-point perspective, and methodical pacing",
    "wong": "Wong Kar-wai's neon-drenched visuals, step-printing, and romantic melancholy",
    "tarantino": "Quentin Tarantino's dynamic angles, trunk shots, and pop culture aesthetics",
    "park": "Park Chan-wook's baroque compositions, rich colors, and operatic visual storytelling",
    "spielberg": "Steven Spielberg's accessible framing, warm lighting, and emotional depth",
    "fincher": "David Fincher's precise compositions, desaturated palette, and clinical atmosphere",
    "villeneuve": "Denis Villeneuve's vast landscapes, minimal dialogue, and contemplative pacing",
    "wes_anderson": "Wes Anderson's symmetrical framing, pastel palette, and whimsical tableaux",
    "coen": "Coen Brothers' wide-angle lenses, dark humor, and regional authenticity",
    "scorsese": "Martin Scorsese's tracking shots, freeze frames, and urban energy",
    "lynch": "David Lynch's surreal imagery, dreamlike transitions, and uncanny atmosphere",
    "shinkai": "Makoto Shinkai's photorealistic backgrounds, lens flares, and emotional skyscapes",
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class StoryStructure:
    """Story structure information for prompt generation."""
    title: Optional[str] = None
    logline: Optional[str] = None
    genre: Optional[str] = None
    mood: Optional[str] = None
    setting: Optional[str] = None
    time_period: Optional[str] = None
    key_visual_elements: List[str] = field(default_factory=list)
    shot_description: Optional[str] = None  # Current shot/scene description


@dataclass
class SystemPromptResult:
    """Result from system prompt generation."""
    system_prompt: str
    negative_prompt: Optional[str] = None
    platform: str = "generic"
    character_count: int = 0
    truncated: bool = False
    logic_vector_summary: Optional[str] = None


# =============================================================================
# System Prompt Generator
# =============================================================================

class SystemPromptGenerator:
    """Generates platform-specific system prompts from Logic Vectors."""

    def __init__(self, default_language: str = "en"):
        """Initialize the generator.

        Args:
            default_language: Default output language (en, ko)
        """
        self.default_language = default_language

    def generate(
        self,
        logic_vector: LogicVector,
        story_structure: Optional[StoryStructure] = None,
        target_platform: str = "veo",
        language: str = "en",
        include_negative: bool = True,
        custom_additions: Optional[str] = None,
    ) -> SystemPromptResult:
        """Generate a system prompt from Logic Vector and story structure.

        Args:
            logic_vector: DNA Lab's Logic Vector
            story_structure: Optional story/scene context
            target_platform: Target platform (veo, kling, runway, generic)
            language: Output language
            include_negative: Whether to include negative prompt
            custom_additions: Custom text to append

        Returns:
            SystemPromptResult with generated prompts
        """
        # Get platform template
        try:
            platform = TargetPlatform(target_platform.lower())
        except ValueError:
            platform = TargetPlatform.GENERIC

        template = PLATFORM_TEMPLATES.get(platform, PLATFORM_TEMPLATES[TargetPlatform.GENERIC])

        # Build prompt sections
        sections = []

        # 1. Style prefix with auteur
        auteur_hint = AUTEUR_STYLE_HINTS.get(
            logic_vector.auteur_id.lower(),
            f"the visual style of {logic_vector.auteur_id}"
        )
        style_line = template["style_prefix"].format(auteur=auteur_hint)
        sections.append(style_line)

        # 2. Story context (if provided)
        if story_structure:
            story_context = self._build_story_context(story_structure, language)
            if story_context:
                sections.append(story_context)

        # 3. Camera grammar
        camera_section = self._build_camera_section(logic_vector, template)
        if camera_section:
            sections.append(camera_section)

        # 4. Composition
        composition_section = self._build_composition_section(logic_vector, template)
        if composition_section:
            sections.append(composition_section)

        # 5. Lighting
        lighting_section = self._build_lighting_section(logic_vector, template)
        if lighting_section:
            sections.append(lighting_section)

        # 6. Color science
        color_section = self._build_color_section(logic_vector, template)
        if color_section:
            sections.append(color_section)

        # 7. Pacing/cadence
        pacing_section = self._build_pacing_section(logic_vector, template)
        if pacing_section:
            sections.append(pacing_section)

        # 8. Custom additions
        if custom_additions:
            sections.append(custom_additions)

        # Combine sections
        system_prompt = " ".join(sections)

        # Truncate if needed
        max_length = template["max_length"]
        truncated = False
        if len(system_prompt) > max_length:
            system_prompt = system_prompt[:max_length - 3] + "..."
            truncated = True

        # Build negative prompt
        negative_prompt = None
        if include_negative and template["supports_negative"]:
            negative_prompt = self._build_negative_prompt(logic_vector, template)

        # Generate Logic Vector summary for reference
        lv_summary = logic_vector.to_system_prompt_context()

        return SystemPromptResult(
            system_prompt=system_prompt,
            negative_prompt=negative_prompt,
            platform=platform.value,
            character_count=len(system_prompt),
            truncated=truncated,
            logic_vector_summary=lv_summary,
        )

    def generate_for_shot(
        self,
        logic_vector: LogicVector,
        shot_description: str,
        shot_number: int = 1,
        target_platform: str = "veo",
    ) -> SystemPromptResult:
        """Generate a system prompt for a specific shot.

        Args:
            logic_vector: DNA Lab's Logic Vector
            shot_description: Description of the shot
            shot_number: Shot number in sequence
            target_platform: Target platform

        Returns:
            SystemPromptResult with shot-specific prompt
        """
        story = StoryStructure(shot_description=shot_description)

        result = self.generate(
            logic_vector=logic_vector,
            story_structure=story,
            target_platform=target_platform,
            custom_additions=f"Shot {shot_number}.",
        )

        return result

    def _build_story_context(
        self,
        story: StoryStructure,
        language: str,
    ) -> str:
        """Build story context section."""
        parts = []

        if story.shot_description:
            parts.append(f"Scene: {story.shot_description}")
        if story.genre:
            parts.append(f"Genre: {story.genre}")
        if story.mood:
            parts.append(f"Mood: {story.mood}")
        if story.setting:
            parts.append(f"Setting: {story.setting}")
        if story.key_visual_elements:
            parts.append(f"Visual elements: {', '.join(story.key_visual_elements[:5])}")

        return " | ".join(parts) if parts else ""

    def _build_camera_section(
        self,
        lv: LogicVector,
        template: Dict,
    ) -> str:
        """Build camera grammar section."""
        movements = []
        grammar = lv.camera_grammar.model_dump()

        # Sort by percentage, take top 4
        sorted_movements = sorted(grammar.items(), key=lambda x: -x[1])

        for movement, ratio in sorted_movements:
            if ratio >= 0.05:  # Only include >= 5%
                percentage = int(ratio * 100)
                movements.append(f"{percentage}% {movement.replace('_', ' ')}")

        if movements:
            return template["camera_prefix"] + ", ".join(movements[:4])
        return ""

    def _build_composition_section(
        self,
        lv: LogicVector,
        template: Dict,
    ) -> str:
        """Build composition section."""
        parts = []

        # Primary strategy
        strategy = lv.composition.primary_strategy.replace("_", " ")
        parts.append(strategy)

        # Symmetry
        if lv.composition.symmetry_score >= 0.7:
            parts.append("high symmetry")
        elif lv.composition.symmetry_score <= 0.3:
            parts.append("asymmetric framing")

        # Depth staging
        if lv.composition.depth_staging:
            parts.append(lv.composition.depth_staging.replace("_", " "))

        if parts:
            return template["composition_prefix"] + ", ".join(parts)
        return ""

    def _build_lighting_section(
        self,
        lv: LogicVector,
        template: Dict,
    ) -> str:
        """Build lighting section."""
        parts = []

        # Key light style
        key = lv.lighting_physics.key_light.replace("_", " ")
        parts.append(key)

        # Color temperature
        temp_range = lv.lighting_physics.color_temp_range
        if temp_range:
            parts.append(f"{temp_range[0]}-{temp_range[1]}K")

        # Shadow quality
        if lv.lighting_physics.shadow_quality:
            parts.append(f"{lv.lighting_physics.shadow_quality} shadows")

        if parts:
            return template["lighting_prefix"] + ", ".join(parts)
        return ""

    def _build_color_section(
        self,
        lv: LogicVector,
        template: Dict,
    ) -> str:
        """Build color science section."""
        parts = []

        # LUT reference
        if lv.color_science.lut_reference:
            parts.append(lv.color_science.lut_reference.replace("_", " "))

        # Palette
        if lv.color_science.palette:
            parts.extend(lv.color_science.palette[:3])

        # Saturation
        if lv.color_science.saturation_level:
            parts.append(lv.color_science.saturation_level)

        if parts:
            return template["color_prefix"] + ", ".join(parts)
        return ""

    def _build_pacing_section(
        self,
        lv: LogicVector,
        template: Dict,
    ) -> str:
        """Build pacing/cadence section."""
        parts = []

        if lv.cadence.tempo:
            parts.append(lv.cadence.tempo)

        if lv.cadence.rhythm_pattern:
            parts.append(lv.cadence.rhythm_pattern.replace("_", " "))

        if lv.cadence.avg_shot_length:
            parts.append(f"~{lv.cadence.avg_shot_length:.1f}s shots")

        if parts:
            return template["pacing_prefix"] + ", ".join(parts)
        return ""

    def _build_negative_prompt(
        self,
        lv: LogicVector,
        template: Dict,
    ) -> str:
        """Build negative prompt based on Logic Vector."""
        avoid = []

        # Avoid opposite camera movements
        grammar = lv.camera_grammar.model_dump()
        for movement, ratio in grammar.items():
            if ratio < 0.05:
                avoid.append(f"excessive {movement.replace('_', ' ')}")

        # Avoid opposing lighting
        if lv.lighting_physics.key_light == "low_key":
            avoid.append("bright overexposed lighting")
        elif lv.lighting_physics.key_light == "high_key":
            avoid.append("dark underexposed shots")

        # Avoid opposing composition
        if lv.composition.symmetry_score >= 0.7:
            avoid.append("chaotic asymmetric framing")
        elif lv.composition.symmetry_score <= 0.3:
            avoid.append("rigid symmetry")

        # General quality issues
        avoid.extend(["blurry", "distorted", "watermark", "text overlay"])

        if avoid:
            return template["negative_prefix"] + ", ".join(avoid[:8])
        return ""


# =============================================================================
# Module-level convenience functions
# =============================================================================

_default_generator: Optional[SystemPromptGenerator] = None


def get_system_prompt_generator() -> SystemPromptGenerator:
    """Get or create the default generator instance."""
    global _default_generator
    if _default_generator is None:
        _default_generator = SystemPromptGenerator()
    return _default_generator


def generate_system_prompt(
    logic_vector: LogicVector,
    story_structure: Optional[StoryStructure] = None,
    target_platform: str = "veo",
) -> SystemPromptResult:
    """Convenience function for system prompt generation."""
    generator = get_system_prompt_generator()
    return generator.generate(
        logic_vector=logic_vector,
        story_structure=story_structure,
        target_platform=target_platform,
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "SystemPromptGenerator",
    "SystemPromptResult",
    "StoryStructure",
    "TargetPlatform",
    "AUTEUR_STYLE_HINTS",
    "get_system_prompt_generator",
    "generate_system_prompt",
]
