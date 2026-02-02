"""Shot Grammar Transpiler.

Converts common Shot Grammar (PromptCards) to engine-specific optimal formats.
Implements 2026 best practices for Veo 3.1, Kling 2.6, and Sora 2.

Each engine has unique strengths:
- Veo 3.1: "Rendering Engine" - JSON schemas, reference images, scene extension
- Kling 2.6: "Audio-Visual Choreographer" - beat markers, motion intensity, lip sync
- Sora 2: "Physics Simulator" - causal chains, storyboard cards, timeline prompting

Usage:
    from app.routers.production.providers.adapters.transpiler import ShotGrammarTranspiler

    transpiler = ShotGrammarTranspiler()
    veo_format = await transpiler.transpile(prompt_cards, "veo", logic_vector)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Transpiler Input Schema
# =============================================================================

class CameraShotCard(BaseModel):
    """Camera shot specification."""
    shot_type: str = "medium"  # wide, medium, close-up, extreme-close-up
    movement: str = "static"  # pan_left, pan_right, dolly_in, zoom_in, tracking, etc.
    angle: str = "eye_level"  # low_angle, high_angle, dutch, bird_eye, worm_eye
    duration_sec: float = 3.0
    lens: Optional[str] = None  # wide, telephoto, anamorphic


class SubjectEntityCard(BaseModel):
    """Subject specification."""
    main_subject: str = ""
    secondary_subjects: List[str] = Field(default_factory=list)
    subject_position: str = "center"  # center, left_third, right_third, foreground, background


class ActionMotionCard(BaseModel):
    """Action/motion specification."""
    action: str = ""
    motion_intensity: str = "moderate"  # subtle, moderate, intense, dramatic
    motion_direction: Optional[str] = None  # left_to_right, ascending, circular


class SettingContextCard(BaseModel):
    """Setting/environment specification."""
    location: str = ""
    time_of_day: str = "day"
    weather: Optional[str] = None
    atmosphere: Optional[str] = None


class LightingStyleCard(BaseModel):
    """Lighting specification."""
    key_light: str = "natural"
    color_temperature: int = 5600  # Kelvin
    contrast: str = "medium"  # low, medium, high
    mood: Optional[str] = None


class AudioPacingCard(BaseModel):
    """Audio/pacing specification."""
    tempo: str = "moderate"  # slow, moderate, fast
    duration_ms: int = 5000
    beat_markers: List[Dict[str, Any]] = Field(default_factory=list)
    kick_intervals: List[Dict[str, Any]] = Field(default_factory=list)


class PromptCards(BaseModel):
    """Complete prompt card collection."""
    camera_shot: CameraShotCard = Field(default_factory=CameraShotCard)
    subject_entity: SubjectEntityCard = Field(default_factory=SubjectEntityCard)
    action_motion: ActionMotionCard = Field(default_factory=ActionMotionCard)
    setting_context: SettingContextCard = Field(default_factory=SettingContextCard)
    lighting_style: LightingStyleCard = Field(default_factory=LightingStyleCard)
    audio_pacing: AudioPacingCard = Field(default_factory=AudioPacingCard)
    negative_prompt: Optional[str] = None
    style_reference: Optional[str] = None


# =============================================================================
# Shot Grammar Transpiler
# =============================================================================

class ShotGrammarTranspiler:
    """Converts common Shot Grammar to engine-specific optimal formats.

    2026 Best Practices:
    - Veo 3.1: Structured prompts with [Cinematography] + [Subject] + [Action] + [Context] + [Style]
    - Kling 2.6: Subject-first for lip sync accuracy, motion_intensity, beat markers
    - Sora 2: Timeline prompting with storyboard cards, physics-aware descriptions
    """

    # Engine-specific capabilities
    ENGINE_CAPABILITIES = {
        "veo": {
            "max_duration": 8,
            "supports_first_frame": True,
            "supports_last_frame": True,
            "supports_scene_extension": True,
            "supports_negative_prompt": True,
            "max_reference_images": 3,
        },
        "kling": {
            "max_duration": 10,
            "supports_first_frame": False,
            "supports_last_frame": False,
            "supports_lip_sync": True,
            "supports_motion_intensity": True,
            "supports_beat_markers": True,
            "max_elements": 4,
        },
        "sora": {
            "max_duration": 20,
            "supports_storyboard": True,
            "supports_timeline": True,
            "supports_physics_hints": True,
            "max_storyboard_cards": 5,
        },
    }

    async def transpile(
        self,
        prompt_cards: PromptCards,
        target_engine: Literal["veo", "kling", "sora"],
        logic_vector: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Convert PromptCards to engine-optimal format.

        Args:
            prompt_cards: Common prompt card format
            target_engine: Target video generation engine
            logic_vector: Optional Logic Vector for style context

        Returns:
            Engine-specific optimized payload
        """
        if target_engine == "veo":
            return self._to_veo_optimal(prompt_cards, logic_vector)
        elif target_engine == "kling":
            return self._to_kling_optimal(prompt_cards, logic_vector)
        elif target_engine == "sora":
            return self._to_sora_optimal(prompt_cards, logic_vector)
        else:
            raise ValueError(f"Unsupported engine: {target_engine}")

    def _to_veo_optimal(
        self,
        cards: PromptCards,
        lv: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Veo 3.1 optimal format.

        Structure: [Cinematography] + [Subject] + [Action] + [Context] + [Style]
        Features: first_frame/last_frame references, scene_extension, negative_prompt
        """
        camera = cards.camera_shot
        subject = cards.subject_entity
        action = cards.action_motion
        setting = cards.setting_context
        lighting = cards.lighting_style

        # Build structured prompt
        cinematography = self._veo_cinematography(camera)
        subject_desc = self._veo_subject(subject)
        action_desc = action.action if action.action else ""
        context_desc = self._veo_context(setting)
        style_desc = self._veo_style(lighting, lv)

        # Compose final prompt
        prompt_parts = [cinematography]
        if subject_desc:
            prompt_parts.append(f"of {subject_desc}")
        if action_desc:
            prompt_parts.append(action_desc)
        if context_desc:
            prompt_parts.append(f"in {context_desc}")
        if style_desc:
            prompt_parts.append(style_desc)

        prompt = " ".join(prompt_parts)

        # Calculate duration
        target_duration = min(
            cards.audio_pacing.duration_ms // 1000,
            self.ENGINE_CAPABILITIES["veo"]["max_duration"],
        )

        return {
            "prompt": prompt,
            "first_frame": self._extract_keyframe(cards, "first"),
            "last_frame": self._extract_keyframe(cards, "last"),
            "scene_extension": {
                "target_duration": target_duration,
                "extend_mode": "smooth",
            },
            "negative_prompt": self._build_veo_negative(cards),
            "reference_images": [],
            "aspect_ratio": "16:9",
            # Metadata for debugging
            "_transpiler_version": "1.0",
            "_source_cards": cards.model_dump(),
        }

    def _to_kling_optimal(
        self,
        cards: PromptCards,
        lv: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Kling 2.6 optimal format.

        Structure: Subject-first for lip sync accuracy
        Features: motion_intensity, camera_preset, beat_markers, elements
        """
        subject = cards.subject_entity
        action = cards.action_motion
        camera = cards.camera_shot
        audio = cards.audio_pacing

        # Subject-first prompt for lip sync accuracy
        prompt_parts = []
        if subject.main_subject:
            prompt_parts.append(subject.main_subject)
        if action.action:
            prompt_parts.append(action.action)
        if action.motion_direction:
            prompt_parts.append(f"moving {action.motion_direction.replace('_', ' ')}")

        prompt = " ".join(prompt_parts)

        # Build beat markers from kick_intervals
        beat_markers = []
        for kick in audio.kick_intervals[:8]:  # Limit to 8 markers
            beat_markers.append({
                "timestamp_ms": kick.get("beat", 0) * 1000 if isinstance(kick.get("beat"), (int, float)) else 0,
                "intensity": kick.get("intensity", "medium"),
                "action_hint": kick.get("action", ""),
            })

        # Map motion intensity
        motion_intensity = self._map_motion_intensity(action.motion_intensity)

        # Map camera preset
        camera_preset = self._map_camera_preset(camera)

        return {
            "prompt": prompt,
            "motion_intensity": motion_intensity,
            "camera_preset": camera_preset,
            "elements": [],  # Reference images (max 4)
            "beat_markers": beat_markers,
            "enable_audio": len(beat_markers) > 0,
            "negative_prompt": self._build_kling_negative(cards),
            "duration": min(
                audio.duration_ms // 1000,
                self.ENGINE_CAPABILITIES["kling"]["max_duration"],
            ),
            # Metadata
            "_transpiler_version": "1.0",
            "_source_cards": cards.model_dump(),
        }

    def _to_sora_optimal(
        self,
        cards: PromptCards,
        lv: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Sora 2 optimal format.

        Structure: Timeline prompting with storyboard cards
        Features: Causal chains, physics-aware descriptions, multi-card storyboard
        """
        audio = cards.audio_pacing

        # Calculate total duration
        total_duration = min(
            audio.duration_ms // 1000,
            self.ENGINE_CAPABILITIES["sora"]["max_duration"],
        )

        # Segment into storyboard cards
        segments = self._segment_by_pacing(cards, total_duration)

        storyboard_cards = []
        for i, segment in enumerate(segments[:5]):  # Max 5 cards
            storyboard_cards.append({
                "card_index": i,
                "text": segment["prompt"],
                "duration": segment["duration"],
                "timing_hint": segment.get("timing", ""),
                "transition": segment.get("transition", "cut"),
            })

        # Extract physics hints (Sora's strength)
        world_logic = self._extract_physics_hints(cards, lv)

        return {
            "storyboard": {
                "cards": storyboard_cards,
                "total_duration": total_duration,
                "aspect_ratio": "16:9",
            },
            "world_logic": world_logic,
            "narrative_coherence": True,
            # Metadata
            "_transpiler_version": "1.0",
            "_source_cards": cards.model_dump(),
        }

    # =========================================================================
    # Veo Helpers
    # =========================================================================

    def _veo_cinematography(self, camera: CameraShotCard) -> str:
        """Build Veo cinematography description."""
        parts = []

        # Shot type
        shot_map = {
            "wide": "Wide shot",
            "medium": "Medium shot",
            "close-up": "Close-up",
            "extreme-close-up": "Extreme close-up",
        }
        parts.append(shot_map.get(camera.shot_type, "Medium shot"))

        # Movement
        if camera.movement != "static":
            movement_map = {
                "pan_left": "panning left",
                "pan_right": "panning right",
                "tilt_up": "tilting up",
                "tilt_down": "tilting down",
                "dolly_in": "dollying in",
                "dolly_out": "dollying out",
                "zoom_in": "zooming in",
                "zoom_out": "zooming out",
                "tracking": "tracking",
                "handheld": "handheld",
            }
            movement = movement_map.get(camera.movement)
            if movement:
                parts.append(f"with {movement}")

        # Angle
        if camera.angle != "eye_level":
            angle_map = {
                "low_angle": "from low angle",
                "high_angle": "from high angle",
                "dutch": "with dutch tilt",
                "bird_eye": "from bird's eye view",
                "worm_eye": "from worm's eye view",
            }
            angle = angle_map.get(camera.angle)
            if angle:
                parts.append(angle)

        return " ".join(parts)

    def _veo_subject(self, subject: SubjectEntityCard) -> str:
        """Build Veo subject description."""
        parts = []
        if subject.main_subject:
            parts.append(subject.main_subject)
        if subject.secondary_subjects:
            parts.append(f"with {', '.join(subject.secondary_subjects[:2])}")
        return " ".join(parts)

    def _veo_context(self, setting: SettingContextCard) -> str:
        """Build Veo context description."""
        parts = []
        if setting.location:
            parts.append(setting.location)
        if setting.time_of_day:
            parts.append(f"during {setting.time_of_day}")
        if setting.weather:
            parts.append(f"with {setting.weather} weather")
        if setting.atmosphere:
            parts.append(f"({setting.atmosphere})")
        return ", ".join(parts)

    def _veo_style(
        self,
        lighting: LightingStyleCard,
        lv: Optional[Dict[str, Any]],
    ) -> str:
        """Build Veo style description."""
        parts = []

        # Lighting
        if lighting.key_light != "natural":
            parts.append(f"{lighting.key_light} lighting")

        if lighting.mood:
            parts.append(f"{lighting.mood} mood")

        # From Logic Vector
        if lv:
            color_science = lv.get("color_science", {})
            if color_science.get("lut_reference"):
                parts.append(f"graded like {color_science['lut_reference']}")
            if color_science.get("saturation_level"):
                parts.append(f"{color_science['saturation_level']} saturation")

        return ", ".join(parts) if parts else ""

    def _build_veo_negative(self, cards: PromptCards) -> str:
        """Build Veo negative prompt."""
        defaults = [
            "blurry", "low quality", "distorted", "artifacts",
            "watermark", "text overlay", "cropped",
        ]
        if cards.negative_prompt:
            return f"{cards.negative_prompt}, {', '.join(defaults)}"
        return ", ".join(defaults)

    def _extract_keyframe(
        self,
        cards: PromptCards,
        position: Literal["first", "last"],
    ) -> Optional[Dict[str, Any]]:
        """Extract keyframe reference if available."""
        # In a real implementation, this would extract from cards or references
        return None

    # =========================================================================
    # Kling Helpers
    # =========================================================================

    def _map_motion_intensity(self, intensity: str) -> str:
        """Map PromptCards intensity to Kling preset."""
        mapping = {
            "subtle": "slow",
            "moderate": "normal",
            "intense": "fast",
            "dramatic": "dramatic",
        }
        return mapping.get(intensity, "normal")

    def _map_camera_preset(self, camera: CameraShotCard) -> str:
        """Map PromptCards camera to Kling camera_preset."""
        movement_map = {
            "pan_left": "pan_left",
            "pan_right": "pan_right",
            "tilt_up": "tilt_up",
            "tilt_down": "tilt_down",
            "dolly_in": "dolly_in",
            "dolly_out": "dolly_out",
            "zoom_in": "zoom_in",
            "zoom_out": "zoom_out",
            "tracking": "orbit",
            "handheld": "static",  # Kling doesn't have handheld preset
            "static": "static",
        }
        return movement_map.get(camera.movement, "static")

    def _build_kling_negative(self, cards: PromptCards) -> str:
        """Build Kling negative prompt."""
        defaults = [
            "blurry", "distorted face", "extra limbs",
            "watermark", "low resolution",
        ]
        if cards.negative_prompt:
            return f"{cards.negative_prompt}, {', '.join(defaults)}"
        return ", ".join(defaults)

    # =========================================================================
    # Sora Helpers
    # =========================================================================

    def _segment_by_pacing(
        self,
        cards: PromptCards,
        total_duration: int,
    ) -> List[Dict[str, Any]]:
        """Segment content into storyboard cards based on pacing."""
        segments = []

        # If we have beat markers, use them for segmentation
        beats = cards.audio_pacing.beat_markers or cards.audio_pacing.kick_intervals
        if beats and len(beats) > 1:
            for i, beat in enumerate(beats[:4]):
                segment_prompt = self._build_segment_prompt(cards, i, beat)
                segments.append({
                    "prompt": segment_prompt,
                    "duration": beat.get("duration", total_duration // len(beats)),
                    "timing": beat.get("timing", ""),
                    "transition": "cut" if i < len(beats) - 1 else "fade",
                })
        else:
            # Single segment
            segments.append({
                "prompt": self._build_full_prompt(cards),
                "duration": total_duration,
                "timing": "",
                "transition": "fade",
            })

        return segments

    def _build_segment_prompt(
        self,
        cards: PromptCards,
        segment_index: int,
        beat: Dict[str, Any],
    ) -> str:
        """Build prompt for a single storyboard segment."""
        subject = cards.subject_entity
        action = cards.action_motion
        setting = cards.setting_context

        parts = []
        if subject.main_subject:
            parts.append(subject.main_subject)
        if beat.get("action"):
            parts.append(beat["action"])
        elif action.action:
            parts.append(action.action)
        if setting.location:
            parts.append(f"in {setting.location}")

        return " ".join(parts)

    def _build_full_prompt(self, cards: PromptCards) -> str:
        """Build full prompt for single-card storyboard."""
        subject = cards.subject_entity
        action = cards.action_motion
        setting = cards.setting_context

        parts = []
        if subject.main_subject:
            parts.append(subject.main_subject)
        if action.action:
            parts.append(action.action)
        if setting.location:
            parts.append(f"in {setting.location}")
        if setting.time_of_day:
            parts.append(f"during {setting.time_of_day}")

        return " ".join(parts)

    def _extract_physics_hints(
        self,
        cards: PromptCards,
        lv: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Extract physics-aware hints for Sora."""
        hints = {}

        # Motion physics
        if cards.action_motion.motion_intensity == "dramatic":
            hints["motion_blur"] = True
            hints["physics_mode"] = "dynamic"
        else:
            hints["physics_mode"] = "realistic"

        # Lighting physics
        if cards.lighting_style.key_light == "chiaroscuro":
            hints["shadow_softness"] = 0.3
            hints["light_falloff"] = "inverse_square"

        # From Logic Vector
        if lv:
            composition = lv.get("composition", {})
            if composition.get("depth_staging") == "deep_focus":
                hints["depth_of_field"] = "deep"
            elif composition.get("depth_staging") == "shallow":
                hints["depth_of_field"] = "shallow"

        return hints


# =============================================================================
# Module-level convenience
# =============================================================================

def get_transpiler() -> ShotGrammarTranspiler:
    """Get transpiler instance."""
    return ShotGrammarTranspiler()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "ShotGrammarTranspiler",
    "PromptCards",
    "CameraShotCard",
    "SubjectEntityCard",
    "ActionMotionCard",
    "SettingContextCard",
    "LightingStyleCard",
    "AudioPacingCard",
    "get_transpiler",
]
