"""AD Studio Prompt Engine — Shot Grammar to engine-optimized prompts.

Transforms cinematic analysis results into engine-specific prompts
with cross-scene continuity tokens.

Usage:
    from app.services.ad_prompt_engine import ADPromptEngine

    engine = ADPromptEngine()
    prompts = engine.generate_all(scenes, sequence)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.services.adapters.kling_adapter import (
    generate_kling_prompt,
    get_kling_camera_preset,
    get_kling_motion_intensity,
)
from app.services.adapters.seedance_adapter import generate_seedance_prompt
from app.services.adapters.veo_adapter import generate_veo_prompt

logger = logging.getLogger(__name__)


class ADPromptEngine:
    """Generates engine-optimized prompts from AD Studio analysis."""

    def generate_all(
        self,
        scenes: List[Dict[str, Any]],
        sequence: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate prompts for all scenes with sequence context.

        Args:
            scenes: List of scene analysis dicts
            sequence: Optional sequence intelligence data

        Returns:
            List of dicts with engine prompts per scene
        """
        results = []
        emotional_arc = {}

        if sequence:
            for beat in sequence.get("emotional_arc", []):
                emotional_arc[beat.get("scene_number", 0)] = beat.get("intensity", 0.5)

        for i, scene in enumerate(scenes):
            scene_num = scene.get("scene_number", i + 1)
            techniques = scene.get("techniques", {})

            # Build sequence context for this scene
            seq_ctx = self._build_prompt_context(
                scene_index=i,
                scenes=scenes,
                sequence=sequence,
            )

            # Generate per-engine prompts
            kling_prompt = generate_kling_prompt(scene, seq_ctx)
            seedance_prompt = generate_seedance_prompt(scene, seq_ctx)
            veo_prompt = generate_veo_prompt(scene, seq_ctx)

            # Get engine-specific metadata
            camera_preset = get_kling_camera_preset(techniques)
            intensity = emotional_arc.get(scene_num, 0.5)
            motion_preset = get_kling_motion_intensity(intensity)

            results.append({
                "scene_number": scene_num,
                "kling_3_0": kling_prompt,
                "seedance_2_0": seedance_prompt,
                "veo_3_1": veo_prompt,
                "kling_metadata": {
                    "camera_preset": camera_preset,
                    "motion_intensity": motion_preset,
                },
            })

        return results

    def _build_prompt_context(
        self,
        scene_index: int,
        scenes: List[Dict[str, Any]],
        sequence: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build cross-scene context for prompt generation."""
        ctx: Dict[str, Any] = {}

        # Previous scene exit
        if scene_index > 0:
            prev = scenes[scene_index - 1]
            ctx["previous_description"] = prev.get("description_en", "")
            prev_anchors = prev.get("continuity_anchors", {})
            if isinstance(prev_anchors, dict):
                ctx["previous_style"] = prev_anchors.get("style", "")

        # Next scene setup
        if scene_index < len(scenes) - 1:
            next_scene = scenes[scene_index + 1]
            ctx["next_description"] = next_scene.get("description_en", "")

        # Sequence-level continuity
        if sequence:
            anchors = sequence.get("continuity_anchors", {})
            if isinstance(anchors, dict):
                ctx["global_style_anchors"] = anchors.get("style_anchors", [])
                ctx["global_character_anchors"] = anchors.get("character_anchors", [])

        return ctx
