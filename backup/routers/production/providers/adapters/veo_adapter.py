"""VEO Adapter - Google VEO 3.1/4 prompt optimization.

VEO-specific features:
- Strong natural language understanding
- Reference image support (up to 3)
- First/last frame control for transitions
- Native audio generation
- High quality cinematic output

Best Practices for VEO prompts:
1. Use detailed, cinematic descriptions
2. Include lighting and atmosphere details
3. Specify camera movements clearly
4. Keep negative prompts concise
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


class VeoAdapter(BaseProviderAdapter):
    """Google VEO 3.1/4 adapter.

    Optimized for:
    - Cinematic quality output
    - Natural language prompts
    - Reference image consistency
    - Transition generation (first/last frame)
    """

    @property
    def provider_name(self) -> str:
        return "veo"

    @property
    def supported_features(self) -> Dict[str, bool]:
        return {
            "storyboard_mode": False,  # VEO 4 will support this
            "reference_images": True,  # Up to 3 images
            "frame_control": True,  # First/last frame
            "audio_generation": True,  # Native audio
            "lip_sync": False,  # Not specialized
            "beat_timestamps": False,  # Not supported
        }

    @property
    def max_prompt_length(self) -> int:
        return 2000

    @property
    def max_duration_seconds(self) -> int:
        return 8  # VEO 3.1 limit; VEO 4 will support 30-60s

    def translate_logic_vector(
        self,
        logic_vector: LogicVector,
        config: Optional[ProviderPromptConfig] = None,
    ) -> AdapterResult:
        """Translate LogicVector to VEO-optimized prompt.

        VEO excels with detailed, cinematic descriptions that paint
        a clear visual picture. The adapter prioritizes:
        1. Visual atmosphere and lighting
        2. Camera work and composition
        3. Subject action and emotion
        4. Environment details
        """
        cfg = config or ProviderPromptConfig()
        notes: List[str] = []

        # Build prompt sections
        sections: List[str] = []

        # 1. Opening - Set the scene
        if logic_vector.location or logic_vector.environment:
            scene_parts = []
            if logic_vector.location:
                scene_parts.append(logic_vector.location)
            if logic_vector.environment:
                scene_parts.append(logic_vector.environment)
            if logic_vector.time_of_day:
                scene_parts.append(f"during {logic_vector.time_of_day}")
            sections.append(" ".join(scene_parts))

        # 2. Lighting and Atmosphere (VEO strength)
        if cfg.include_lighting:
            lighting_desc = self._format_lighting_instruction(
                logic_vector.lighting_style,
                logic_vector.color_palette,
            )
            if lighting_desc:
                sections.append(lighting_desc)
                notes.append("Added VEO-optimized lighting description")

        # 3. Camera Work
        if cfg.include_camera_direction:
            camera_desc = self._format_camera_instruction(
                logic_vector.shot_type,
                logic_vector.camera_movement,
                logic_vector.camera_angle,
            )
            if camera_desc:
                sections.append(camera_desc)

        # 4. Subject and Action
        if logic_vector.main_subject:
            subject_desc = logic_vector.main_subject
            if logic_vector.subject_action:
                subject_desc += f", {logic_vector.subject_action}"
            sections.append(subject_desc)

        # 5. Hook Element (if high visual spectacle)
        if logic_vector.visual_spectacle > 7:
            sections.append("visually striking and dynamic")
            notes.append(f"High visual spectacle ({logic_vector.visual_spectacle}/10)")

        # 6. Style hints based on hook pattern
        if logic_vector.hook_pattern:
            style_hint = self._hook_pattern_to_veo_style(logic_vector.hook_pattern)
            if style_hint:
                sections.append(style_hint)
                notes.append(f"Applied hook pattern: {logic_vector.hook_pattern}")

        # Combine into final prompt
        prompt = ". ".join(filter(None, sections))
        if not prompt.endswith("."):
            prompt += "."

        # Build negative prompt
        negative_prompt = None
        if cfg.include_negative and logic_vector.do_not:
            negative_prompt = self.build_negative_prompt(
                logic_vector.do_not,
                quality_issues=["blurry", "low resolution", "artifacts"],
            )

        # VEO-specific config
        provider_config = {
            "aspect_ratio": "16:9",  # Default
            "duration_seconds": min(logic_vector.duration_ms // 1000, self.max_duration_seconds),
            "include_audio": True,
        }

        # Truncate if needed
        prompt = self._truncate_prompt(prompt, self.max_prompt_length)

        return AdapterResult(
            prompt=prompt,
            negative_prompt=negative_prompt,
            system_prompt=None,  # VEO doesn't use system prompts
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
        """Compile PromptCards to VEO-optimized prompt.

        PromptCards provide a structured representation that maps well
        to VEO's natural language understanding.
        """
        cfg = config or ProviderPromptConfig()
        notes: List[str] = []
        sections: List[str] = []

        # 1. Setting Card → Scene description
        if cards.setting:
            setting_parts = []
            if cards.setting.location:
                setting_parts.append(cards.setting.location)
            if cards.setting.environment:
                setting_parts.append(cards.setting.environment)
            if cards.setting.time_of_day:
                setting_parts.append(f"during {cards.setting.time_of_day}")
            if setting_parts:
                sections.append(" ".join(setting_parts))

        # 2. Lighting Card → Atmosphere
        if cards.lighting and cfg.include_lighting:
            lighting_parts = []
            if cards.lighting.lighting:
                lighting_parts.append(f"{cards.lighting.lighting} lighting")
            if cards.lighting.mood:
                lighting_parts.append(f"{cards.lighting.mood} mood")
            if cards.lighting.color_palette:
                colors = ", ".join(cards.lighting.color_palette[:3])
                lighting_parts.append(f"colors: {colors}")
            if lighting_parts:
                sections.append(", ".join(lighting_parts))

        # 3. Camera Card → Shot description
        if cards.camera and cfg.include_camera_direction:
            camera_desc = self._format_camera_instruction(
                cards.camera.shot_type,
                cards.camera.movement,
                cards.camera.angle,
            )
            if camera_desc:
                sections.append(camera_desc)

        # 4. Subject Card → Main subject
        if cards.subject:
            subject_parts = []
            if cards.subject.main_subject:
                subject_parts.append(cards.subject.main_subject)
            if cards.subject.subject_description:
                subject_parts.append(cards.subject.subject_description)
            if subject_parts:
                sections.append(", ".join(subject_parts))

        # 5. Action Card → Motion
        if cards.action:
            if cards.action.action:
                sections.append(cards.action.action)
            if cards.action.motion_intensity:
                intensity_map = {
                    "subtle": "gentle, subtle movement",
                    "moderate": "smooth, natural motion",
                    "intense": "dynamic, energetic action",
                }
                if cards.action.motion_intensity in intensity_map:
                    sections.append(intensity_map[cards.action.motion_intensity])

        # 6. Visual Style
        if cards.lighting and cards.lighting.visual_style:
            sections.append(f"{cards.lighting.visual_style} visual style")
            notes.append(f"Applied visual style: {cards.lighting.visual_style}")

        # Combine
        prompt = ". ".join(filter(None, sections))
        if prompt and not prompt.endswith("."):
            prompt += "."

        # Negative prompt from Card 7
        negative_prompt = None
        if cfg.include_negative and cards.negative:
            negatives = []
            if cards.negative.do_not:
                negatives.extend(cards.negative.do_not)
            if cards.negative.quality_issues:
                negatives.extend(cards.negative.quality_issues)
            if negatives:
                negative_prompt = self.build_negative_prompt(negatives)

        # Duration from audio card
        duration_seconds = 8
        if cards.audio and cards.audio.duration_ms:
            duration_seconds = min(cards.audio.duration_ms // 1000, self.max_duration_seconds)

        provider_config = {
            "aspect_ratio": "16:9",
            "duration_seconds": duration_seconds,
            "include_audio": True,
        }

        prompt = self._truncate_prompt(prompt, self.max_prompt_length)

        return AdapterResult(
            prompt=prompt,
            negative_prompt=negative_prompt,
            system_prompt=None,
            provider_config=provider_config,
            source_type="prompt_cards",
            translation_notes=notes,
            confidence=0.9,  # PromptCards are well-structured
        )

    def _hook_pattern_to_veo_style(self, hook_pattern: str) -> Optional[str]:
        """Map hook patterns to VEO visual styles."""
        pattern_styles = {
            "curiosity_gap": "mysterious, intriguing atmosphere",
            "shock_reveal": "dramatic reveal with high contrast",
            "satisfying_loop": "smooth, satisfying motion",
            "emotional_hook": "emotionally evocative, warm tones",
            "visual_wow": "stunning visuals, cinematic quality",
            "transformation": "dynamic transformation sequence",
            "tutorial_tease": "clear, instructional framing",
        }
        return pattern_styles.get(hook_pattern)

    def _calculate_confidence(self, logic_vector: LogicVector) -> float:
        """Calculate translation confidence based on available data."""
        score = 0.5  # Base score

        # Add points for available data
        if logic_vector.main_subject:
            score += 0.15
        if logic_vector.shot_type:
            score += 0.1
        if logic_vector.lighting_style:
            score += 0.1
        if logic_vector.location:
            score += 0.1
        if logic_vector.subject_action:
            score += 0.05

        return min(1.0, score)


__all__ = ["VeoAdapter"]
