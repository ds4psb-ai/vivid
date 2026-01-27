"""Kling Adapter - Kuaishou Kling 2.6/3.0 prompt optimization.

Kling-specific features:
- Best-in-class lip synchronization
- Beat timestamp alignment for music videos
- Strong character consistency
- Image-to-video with reference preservation

Best Practices for Kling prompts:
1. Use structured, concise descriptions
2. Specify beat/timing information for music content
3. Include clear subject descriptions for lip sync
4. Focus on action rather than atmosphere
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


class KlingAdapter(BaseProviderAdapter):
    """Kuaishou Kling 2.6/3.0 adapter.

    Optimized for:
    - Lip sync accuracy
    - Beat-aligned content
    - Character consistency
    - Action-focused videos
    """

    @property
    def provider_name(self) -> str:
        return "kling"

    @property
    def supported_features(self) -> Dict[str, bool]:
        return {
            "storyboard_mode": False,  # Kling 3.0 may support
            "reference_images": True,  # Character consistency
            "frame_control": False,  # Not supported
            "audio_generation": True,  # Kling 2.6+
            "lip_sync": True,  # Best in class
            "beat_timestamps": True,  # Music video support
        }

    @property
    def max_prompt_length(self) -> int:
        return 1500  # Kling prefers shorter prompts

    @property
    def max_duration_seconds(self) -> int:
        return 10  # Kling 2.6 limit; 3.0 will support 30-120s

    def translate_logic_vector(
        self,
        logic_vector: LogicVector,
        config: Optional[ProviderPromptConfig] = None,
    ) -> AdapterResult:
        """Translate LogicVector to Kling-optimized prompt.

        Kling works best with:
        1. Clear subject description (for lip sync)
        2. Specific action descriptions
        3. Concise, structured prompts
        4. Beat timing information (if available)
        """
        cfg = config or ProviderPromptConfig()
        notes: List[str] = []

        # Build prompt - Kling prefers subject-first structure
        sections: List[str] = []

        # 1. Subject First (critical for lip sync)
        if logic_vector.main_subject:
            subject_desc = logic_vector.main_subject
            if logic_vector.subject_action:
                subject_desc += f" {logic_vector.subject_action}"
            sections.append(subject_desc)
            notes.append("Subject-first structure for Kling optimization")

        # 2. Camera Work (concise)
        if cfg.include_camera_direction:
            camera_parts = []
            if logic_vector.shot_type:
                camera_parts.append(self._kling_shot_term(logic_vector.shot_type))
            if logic_vector.camera_movement:
                camera_parts.append(self._kling_movement_term(logic_vector.camera_movement))
            if camera_parts:
                sections.append(", ".join(camera_parts))

        # 3. Setting (brief)
        if logic_vector.location:
            location_desc = logic_vector.location
            if logic_vector.time_of_day:
                location_desc += f", {logic_vector.time_of_day}"
            sections.append(location_desc)

        # 4. Lighting (if high visual spectacle)
        if cfg.include_lighting and logic_vector.visual_spectacle > 6:
            if logic_vector.lighting_style:
                sections.append(f"{logic_vector.lighting_style} lighting")

        # 5. Style based on hook (Kling-specific mapping)
        if logic_vector.hook_pattern:
            style = self._hook_pattern_to_kling_style(logic_vector.hook_pattern)
            if style:
                sections.append(style)
                notes.append(f"Kling style mapping: {logic_vector.hook_pattern} -> {style}")

        # 6. Audio/Rhythm hints (Kling strength)
        if logic_vector.audio_stimulation > 7:
            sections.append("rhythmic, beat-synchronized movement")
            notes.append("High audio stimulation - added beat sync hint")

        # Combine
        prompt = ", ".join(filter(None, sections))

        # Build negative prompt (Kling-specific)
        negative_prompt = None
        if cfg.include_negative and logic_vector.do_not:
            kling_negatives = logic_vector.do_not + [
                "lip sync errors",
                "audio desync",
                "unnatural mouth movement",
            ]
            negative_prompt = self.build_negative_prompt(kling_negatives)

        # Kling-specific config
        duration = min(logic_vector.duration_ms // 1000, self.max_duration_seconds)
        provider_config = {
            "aspect_ratio": "16:9",
            "duration": str(duration),
            "mode": "std",  # or "pro" for higher quality
            "enable_audio": True,
        }

        # Truncate if needed
        prompt = self._truncate_prompt(prompt, self.max_prompt_length)

        return AdapterResult(
            prompt=prompt,
            negative_prompt=negative_prompt,
            system_prompt=None,  # Kling doesn't use system prompts
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
        """Compile PromptCards to Kling-optimized prompt.

        Kling benefits from structured, action-focused descriptions.
        """
        cfg = config or ProviderPromptConfig()
        notes: List[str] = []
        sections: List[str] = []

        # 1. Subject Card → Primary focus
        if cards.subject:
            subject_parts = []
            if cards.subject.main_subject:
                subject_parts.append(cards.subject.main_subject)
            if cards.subject.subject_description:
                subject_parts.append(cards.subject.subject_description)
            if subject_parts:
                sections.append(" ".join(subject_parts))

        # 2. Action Card → Motion description
        if cards.action:
            if cards.action.action:
                sections.append(cards.action.action)
            # Kling timing beats (for music videos)
            if cards.action.timing_beats:
                beats = ", ".join(cards.action.timing_beats[:3])
                sections.append(f"timing: {beats}")
                notes.append("Added Kling timing beats")

        # 3. Camera Card → Concise shot info
        if cards.camera and cfg.include_camera_direction:
            camera_parts = []
            if cards.camera.shot_type:
                camera_parts.append(self._kling_shot_term(cards.camera.shot_type))
            if cards.camera.movement:
                camera_parts.append(self._kling_movement_term(cards.camera.movement))
            if camera_parts:
                sections.append(", ".join(camera_parts))

        # 4. Setting Card → Brief location
        if cards.setting:
            if cards.setting.location:
                sections.append(cards.setting.location)

        # 5. Audio Card → Pacing info (Kling strength)
        if cards.audio:
            if cards.audio.pacing:
                pacing_map = {
                    "fast": "quick, energetic pace",
                    "medium": "moderate pace",
                    "slow": "slow, deliberate pace",
                }
                if cards.audio.pacing in pacing_map:
                    sections.append(pacing_map[cards.audio.pacing])
            if cards.audio.bpm:
                sections.append(f"{cards.audio.bpm} BPM")
                notes.append(f"Added BPM hint: {cards.audio.bpm}")

        # Combine
        prompt = ", ".join(filter(None, sections))

        # Negative prompt
        negative_prompt = None
        if cfg.include_negative and cards.negative:
            negatives = []
            if cards.negative.do_not:
                negatives.extend(cards.negative.do_not)
            if cards.negative.quality_issues:
                negatives.extend(cards.negative.quality_issues)
            # Add Kling-specific negatives
            negatives.extend(["lip sync errors", "audio desync"])
            if negatives:
                negative_prompt = self.build_negative_prompt(negatives)

        # Duration
        duration_seconds = 5
        if cards.audio and cards.audio.duration_ms:
            duration_seconds = min(cards.audio.duration_ms // 1000, self.max_duration_seconds)

        provider_config = {
            "aspect_ratio": "16:9",
            "duration": str(duration_seconds),
            "mode": "std",
            "enable_audio": True,
        }

        prompt = self._truncate_prompt(prompt, self.max_prompt_length)

        return AdapterResult(
            prompt=prompt,
            negative_prompt=negative_prompt,
            system_prompt=None,
            provider_config=provider_config,
            source_type="prompt_cards",
            translation_notes=notes,
            confidence=0.85,
        )

    def _kling_shot_term(self, shot_type: str) -> str:
        """Map shot types to Kling-preferred terms."""
        # Kling works well with simple, direct terms
        shot_map = {
            "wide": "wide shot",
            "medium": "medium shot",
            "close_up": "close-up",
            "extreme_close_up": "extreme close-up",
            "pov": "POV",
            "overhead": "top-down view",
            "selfie": "selfie angle",
            "two_shot": "two-shot",
        }
        return shot_map.get(shot_type, shot_type)

    def _kling_movement_term(self, movement: str) -> str:
        """Map camera movements to Kling-preferred terms."""
        movement_map = {
            "static": "static",
            "pan_left": "pan left",
            "pan_right": "pan right",
            "tilt_up": "tilt up",
            "tilt_down": "tilt down",
            "dolly_in": "push in",
            "dolly_out": "pull out",
            "tracking": "tracking",
            "handheld": "handheld",
            "zoom_in": "zoom in",
            "zoom_out": "zoom out",
        }
        return movement_map.get(movement, movement)

    def _hook_pattern_to_kling_style(self, hook_pattern: str) -> Optional[str]:
        """Map hook patterns to Kling visual styles."""
        # Kling excels at action and character-focused content
        pattern_styles = {
            "curiosity_gap": "intriguing expression",
            "shock_reveal": "dramatic reaction",
            "satisfying_loop": "smooth, looping motion",
            "emotional_hook": "expressive, emotional",
            "visual_wow": "dynamic action",
            "transformation": "transformation sequence",
            "tutorial_tease": "demonstrating action",
            "dance_challenge": "dance choreography",  # Kling specialty
        }
        return pattern_styles.get(hook_pattern)

    def _calculate_confidence(self, logic_vector: LogicVector) -> float:
        """Calculate translation confidence for Kling."""
        score = 0.5

        # Kling prioritizes subject and action
        if logic_vector.main_subject:
            score += 0.2  # Higher weight for Kling
        if logic_vector.subject_action:
            score += 0.15
        if logic_vector.shot_type:
            score += 0.1
        if logic_vector.audio_stimulation > 5:
            score += 0.05  # Kling is good with audio-driven content

        return min(1.0, score)


__all__ = ["KlingAdapter"]
