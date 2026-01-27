"""Sora Adapter - OpenAI Sora 2 prompt optimization.

Sora-specific features:
- Native storyboard mode (multi-shot sequences)
- 1-second segments with transitions
- Up to 25 seconds total duration
- Strong cinematic understanding
- Shot-to-shot coherence

Best Practices for Sora prompts:
1. Use storyboard format for multi-shot content
2. Specify transitions between shots
3. Include detailed cinematic descriptions
4. Leverage GPT-4 prompt understanding
"""
from __future__ import annotations

from typing import Dict, List, Optional, TYPE_CHECKING

from .base_adapter import (
    BaseProviderAdapter,
    AdapterResult,
    ProviderPromptConfig,
    PromptStyle,
    LogicVector,
)

if TYPE_CHECKING:
    from app.schemas.prompt_card import PromptCards


class SoraAdapter(BaseProviderAdapter):
    """OpenAI Sora 2 adapter.

    Optimized for:
    - Storyboard mode (multi-shot)
    - Cinematic quality
    - Strong prompt understanding
    - Shot coherence
    """

    @property
    def provider_name(self) -> str:
        return "sora"

    @property
    def supported_features(self) -> Dict[str, bool]:
        return {
            "storyboard_mode": True,  # Native support
            "reference_images": True,  # Style/character reference
            "frame_control": True,  # First/last frame
            "audio_generation": False,  # External audio needed
            "lip_sync": False,  # Not specialized
            "beat_timestamps": False,  # Not supported natively
        }

    @property
    def max_prompt_length(self) -> int:
        return 4000  # Sora leverages GPT-4's long context

    @property
    def max_duration_seconds(self) -> int:
        return 25  # Sora 2 Pro limit

    def translate_logic_vector(
        self,
        logic_vector: LogicVector,
        config: Optional[ProviderPromptConfig] = None,
    ) -> AdapterResult:
        """Translate LogicVector to Sora-optimized prompt.

        Sora excels with detailed, cinematic prompts that leverage
        GPT-4's language understanding. The adapter creates rich
        narrative descriptions.
        """
        cfg = config or ProviderPromptConfig()
        notes: List[str] = []

        # Sora benefits from narrative structure
        sections: List[str] = []

        # 1. Scene Setting (cinematic opener)
        scene_opener = self._build_scene_opener(logic_vector)
        if scene_opener:
            sections.append(scene_opener)

        # 2. Visual Style & Atmosphere
        if cfg.include_lighting:
            atmosphere = self._build_atmosphere_desc(logic_vector)
            if atmosphere:
                sections.append(atmosphere)

        # 3. Camera Work (cinematic detail)
        if cfg.include_camera_direction:
            camera_desc = self._build_sora_camera_desc(logic_vector)
            if camera_desc:
                sections.append(camera_desc)
                notes.append("Added Sora-optimized camera description")

        # 4. Subject & Action (narrative)
        if logic_vector.main_subject:
            subject_narrative = self._build_subject_narrative(logic_vector)
            sections.append(subject_narrative)

        # 5. Hook Pattern Style
        if logic_vector.hook_pattern:
            style = self._hook_pattern_to_sora_style(logic_vector.hook_pattern)
            if style:
                sections.append(style)
                notes.append(f"Applied Sora style: {logic_vector.hook_pattern}")

        # 6. Composition hints
        if logic_vector.composition:
            sections.append(f"Composed using {logic_vector.composition}")

        # Combine with full sentences for Sora's GPT-4 understanding
        prompt = " ".join(filter(None, sections))

        # Build negative prompt
        negative_prompt = None
        if cfg.include_negative and logic_vector.do_not:
            sora_negatives = logic_vector.do_not + [
                "inconsistent style",
                "abrupt cuts",
                "character morphing",
            ]
            negative_prompt = self.build_negative_prompt(sora_negatives)

        # Sora-specific config (storyboard-ready)
        duration = min(logic_vector.duration_ms // 1000, self.max_duration_seconds)
        provider_config = {
            "aspect_ratio": "16:9",
            "duration_seconds": duration,
            "mode": "single_shot",  # vs "storyboard" for multi-shot
            "resolution": "1080p",
        }

        prompt = self._truncate_prompt(prompt, self.max_prompt_length)

        return AdapterResult(
            prompt=prompt,
            negative_prompt=negative_prompt,
            system_prompt=None,
            provider_config=provider_config,
            source_type="logic_vector",
            translation_notes=notes,
            confidence=self._calculate_confidence(logic_vector),
        )

    def compile_prompt_cards(
        self,
        cards: "PromptCards",
        config: Optional[ProviderPromptConfig] = None,
    ) -> AdapterResult:
        """Compile PromptCards to Sora-optimized prompt.

        Sora benefits from detailed, narrative-style prompts.
        """
        cfg = config or ProviderPromptConfig()
        notes: List[str] = []

        # Build narrative prompt
        narrative_parts: List[str] = []

        # 1. Scene setting
        if cards.setting:
            setting_narrative = []
            if cards.setting.location:
                setting_narrative.append(f"In {cards.setting.location}")
            if cards.setting.time_of_day:
                setting_narrative.append(f"during {cards.setting.time_of_day}")
            if cards.setting.environment:
                setting_narrative.append(cards.setting.environment)
            if setting_narrative:
                narrative_parts.append(", ".join(setting_narrative) + ".")

        # 2. Lighting & Style
        if cards.lighting and cfg.include_lighting:
            style_parts = []
            if cards.lighting.lighting:
                style_parts.append(f"The scene is lit with {cards.lighting.lighting}")
            if cards.lighting.mood:
                style_parts.append(f"creating a {cards.lighting.mood} atmosphere")
            if cards.lighting.color_palette:
                colors = ", ".join(cards.lighting.color_palette[:3])
                style_parts.append(f"with a color palette of {colors}")
            if cards.lighting.visual_style:
                style_parts.append(f"in {cards.lighting.visual_style} style")
            if style_parts:
                narrative_parts.append(" ".join(style_parts) + ".")

        # 3. Camera Work
        if cards.camera and cfg.include_camera_direction:
            camera_narrative = self._cards_to_sora_camera(cards.camera)
            if camera_narrative:
                narrative_parts.append(camera_narrative)

        # 4. Subject
        if cards.subject:
            subject_narrative = []
            if cards.subject.main_subject:
                subject_narrative.append(cards.subject.main_subject)
            if cards.subject.subject_description:
                subject_narrative.append(cards.subject.subject_description)
            if subject_narrative:
                narrative_parts.append(" ".join(subject_narrative) + ".")

        # 5. Action
        if cards.action:
            action_narrative = []
            if cards.action.action:
                action_narrative.append(cards.action.action)
            if cards.action.motion_intensity:
                intensity_desc = {
                    "subtle": "with subtle, nuanced movement",
                    "moderate": "with natural, fluid motion",
                    "intense": "with dynamic, energetic action",
                }
                if cards.action.motion_intensity in intensity_desc:
                    action_narrative.append(intensity_desc[cards.action.motion_intensity])
            if action_narrative:
                narrative_parts.append(" ".join(action_narrative) + ".")

        # Combine
        prompt = " ".join(narrative_parts)

        # Negative prompt
        negative_prompt = None
        if cfg.include_negative and cards.negative:
            negatives = []
            if cards.negative.do_not:
                negatives.extend(cards.negative.do_not)
            if cards.negative.quality_issues:
                negatives.extend(cards.negative.quality_issues)
            negatives.extend(["inconsistent style", "character morphing"])
            if negatives:
                negative_prompt = self.build_negative_prompt(negatives)

        # Duration
        duration_seconds = 8
        if cards.audio and cards.audio.duration_ms:
            duration_seconds = min(cards.audio.duration_ms // 1000, self.max_duration_seconds)

        provider_config = {
            "aspect_ratio": "16:9",
            "duration_seconds": duration_seconds,
            "mode": "single_shot",
            "resolution": "1080p",
        }

        prompt = self._truncate_prompt(prompt, self.max_prompt_length)

        return AdapterResult(
            prompt=prompt,
            negative_prompt=negative_prompt,
            system_prompt=None,
            provider_config=provider_config,
            source_type="prompt_cards",
            translation_notes=notes,
            confidence=0.9,
        )

    def compile_storyboard(
        self,
        shots: List[Dict],
        total_duration_seconds: int = 25,
    ) -> AdapterResult:
        """Compile multi-shot storyboard for Sora's native storyboard mode.

        This is a Sora-specific feature for multi-shot sequences.

        Args:
            shots: List of shot definitions with prompts and durations
            total_duration_seconds: Total video duration

        Returns:
            AdapterResult with storyboard-formatted prompt
        """
        notes: List[str] = ["Storyboard mode compilation"]

        # Build storyboard segments
        segments = []
        for i, shot in enumerate(shots):
            segment = f"[Shot {i + 1}]"
            if shot.get("duration"):
                segment += f" ({shot['duration']}s):"
            else:
                segment += ":"
            if shot.get("prompt"):
                segment += f" {shot['prompt']}"
            if shot.get("transition"):
                segment += f" [Transition: {shot['transition']}]"
            segments.append(segment)

        prompt = "\n".join(segments)
        notes.append(f"Compiled {len(shots)} shots")

        provider_config = {
            "aspect_ratio": "16:9",
            "duration_seconds": min(total_duration_seconds, self.max_duration_seconds),
            "mode": "storyboard",  # Sora storyboard mode
            "resolution": "1080p",
        }

        return AdapterResult(
            prompt=prompt,
            negative_prompt="inconsistent characters, style shifts, abrupt transitions",
            system_prompt=None,
            provider_config=provider_config,
            source_type="storyboard",
            translation_notes=notes,
            confidence=0.95,
        )

    def _build_scene_opener(self, lv: LogicVector) -> Optional[str]:
        """Build cinematic scene opener for Sora."""
        parts = []
        if lv.location:
            parts.append(f"In {lv.location}")
        if lv.time_of_day:
            parts.append(f"during {lv.time_of_day}")
        if lv.environment:
            parts.append(lv.environment)
        return ", ".join(parts) + "." if parts else None

    def _build_atmosphere_desc(self, lv: LogicVector) -> Optional[str]:
        """Build atmospheric description for Sora."""
        parts = []
        if lv.lighting_style:
            parts.append(f"{lv.lighting_style} lighting")
        if lv.color_palette:
            colors = ", ".join(lv.color_palette[:3])
            parts.append(f"color palette of {colors}")
        return "The scene features " + " and ".join(parts) + "." if parts else None

    def _build_sora_camera_desc(self, lv: LogicVector) -> Optional[str]:
        """Build detailed camera description for Sora."""
        parts = []
        if lv.shot_type:
            shot_desc = {
                "wide": "a sweeping wide shot",
                "medium": "a balanced medium shot",
                "close_up": "an intimate close-up",
                "extreme_close_up": "a detailed extreme close-up",
                "pov": "a first-person POV shot",
                "overhead": "a dramatic overhead shot",
            }
            parts.append(shot_desc.get(lv.shot_type, f"a {lv.shot_type} shot"))

        if lv.camera_movement:
            movement_desc = {
                "static": "held steady",
                "pan_left": "slowly panning left",
                "pan_right": "slowly panning right",
                "dolly_in": "pushing forward",
                "dolly_out": "pulling back",
                "tracking": "tracking the subject",
                "handheld": "with handheld energy",
            }
            parts.append(movement_desc.get(lv.camera_movement, lv.camera_movement))

        if lv.camera_angle:
            parts.append(f"from {lv.camera_angle.replace('_', ' ')}")

        return "The camera captures " + ", ".join(parts) + "." if parts else None

    def _build_subject_narrative(self, lv: LogicVector) -> str:
        """Build narrative subject description for Sora."""
        parts = [lv.main_subject]
        if lv.subject_action:
            parts.append(lv.subject_action)
        return " ".join(parts)

    def _cards_to_sora_camera(self, camera) -> Optional[str]:
        """Convert camera card to Sora narrative."""
        parts = []
        if camera.shot_type:
            parts.append(f"Captured in a {camera.shot_type.replace('_', ' ')}")
        if camera.movement:
            parts.append(f"with {camera.movement.replace('_', ' ')} movement")
        if camera.angle:
            parts.append(f"from {camera.angle.replace('_', ' ')}")
        return ", ".join(parts) + "." if parts else None

    def _hook_pattern_to_sora_style(self, hook_pattern: str) -> Optional[str]:
        """Map hook patterns to Sora cinematic styles."""
        pattern_styles = {
            "curiosity_gap": "Building intrigue through visual mystery.",
            "shock_reveal": "A dramatic reveal with high cinematic impact.",
            "satisfying_loop": "Smooth, seamlessly looping motion.",
            "emotional_hook": "Emotionally resonant with expressive visuals.",
            "visual_wow": "Stunning, jaw-dropping cinematography.",
            "transformation": "A captivating transformation sequence.",
            "tutorial_tease": "Clear, instructional framing with visual clarity.",
        }
        return pattern_styles.get(hook_pattern)

    def _calculate_confidence(self, lv: LogicVector) -> float:
        """Calculate translation confidence for Sora."""
        score = 0.5

        # Sora benefits from rich descriptions
        if lv.main_subject:
            score += 0.1
        if lv.shot_type:
            score += 0.1
        if lv.camera_movement:
            score += 0.1
        if lv.lighting_style:
            score += 0.1
        if lv.location:
            score += 0.05
        if lv.color_palette:
            score += 0.05

        return min(1.0, score)


__all__ = ["SoraAdapter"]
