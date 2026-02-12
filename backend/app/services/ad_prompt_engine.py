"""AD Studio Prompt Engine — Shot Grammar to engine-optimized prompts.

Transforms cinematic analysis results into engine-specific prompts
with cross-scene continuity tokens and native multi-scene formats.

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
from app.services.adapters.sequence_assembler import (
    assemble_kling_multishot,
    assemble_seedance_narrative,
    assemble_veo_timeline,
)

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

        # ── Multi-Shot Native Formats ──
        # After individual scenes are generated, assemble multi-scene formats
        if len(results) > 1:
            multi_shot = self._build_multi_shot(results, sequence)
            # Attach multi_shot at the sequence level (not per-scene)
            for r in results:
                r["multi_shot"] = multi_shot

        return results

    def _build_multi_shot(
        self,
        results: List[Dict[str, Any]],
        sequence: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build native multi-scene formats from per-scene results.

        v2: Uses character binding tokens and beat/duration metadata.
        Returns dict with kling_sequence, seedance_narrative, veo_timeline.
        """
        # Prepare scene dicts with prompt fields for assemblers
        assembler_scenes = []
        for r in results:
            assembler_scenes.append({
                "kling_3_0": r.get("kling_3_0", ""),
                "seedance_2_0": r.get("seedance_2_0", ""),
                "veo_3_1": r.get("veo_3_1", ""),
                "description_en": r.get("description_en", ""),
                "techniques": r.get("techniques", {}),
                # v2 fields for duration/pacing
                "duration_weight": r.get("duration_weight", 1.0),
                "beat": r.get("beat", ""),
                "action_en": r.get("action_en", ""),
            })

        # Extract character references for Seedance @tag binding
        references = {}
        if sequence:
            # v2: Use character binding tokens from 5-Domain decomposition
            characters = sequence.get("characters", [])
            if characters:
                for i, char in enumerate(characters[:SEEDANCE_MAX_REFS]):
                    tag = f"@Character{i + 1}"
                    if isinstance(char, dict):
                        references[tag] = char.get(
                            "binding_token",
                            char.get("description_en", str(char)),
                        )
                    elif isinstance(char, str):
                        references[tag] = char

            # v1 fallback: character_anchors
            if not references:
                char_anchors = sequence.get("continuity_anchors", {}).get(
                    "character_anchors", []
                )
                for i, anchor in enumerate(char_anchors[:SEEDANCE_MAX_REFS]):
                    tag = f"@Character{i + 1}"
                    if isinstance(anchor, str):
                        references[tag] = anchor
                    elif isinstance(anchor, dict):
                        references[tag] = anchor.get("description", str(anchor))

        try:
            kling_seq = assemble_kling_multishot(assembler_scenes)
            seedance_narr = assemble_seedance_narrative(
                assembler_scenes, references=references
            )
            veo_tl = assemble_veo_timeline(assembler_scenes)
        except Exception as e:
            logger.warning("Multi-shot assembly failed: %s", e)
            return {}

        return {
            "kling_sequence": kling_seq,
            "seedance_narrative": seedance_narr,
            "veo_timeline": veo_tl,
        }

    def _build_prompt_context(
        self,
        scene_index: int,
        scenes: List[Dict[str, Any]],
        sequence: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build cross-scene context for prompt generation.

        v2: Injects beat type, action_en, audio cues, and character bindings.
        """
        ctx: Dict[str, Any] = {}

        # Current scene v2 fields
        current = scenes[scene_index]
        ctx["beat"] = current.get("beat", "")
        ctx["action_en"] = current.get("action_en", "")
        ctx["audio"] = current.get("audio", {})
        ctx["duration_weight"] = current.get("duration_weight", 1.0)

        # Previous scene exit
        if scene_index > 0:
            prev = scenes[scene_index - 1]
            ctx["previous_description"] = prev.get("description_en", "")
            prev_anchors = prev.get("continuity_anchors", {})
            if isinstance(prev_anchors, dict):
                ctx["previous_style"] = prev_anchors.get("style", "")
                ctx["end_frame_hint"] = prev_anchors.get("end_frame_hint", "")

        # Next scene setup
        if scene_index < len(scenes) - 1:
            next_scene = scenes[scene_index + 1]
            ctx["next_description"] = next_scene.get("description_en", "")

        # End-frame visuals for Extend continuity
        if scene_index > 0:
            prev = scenes[scene_index - 1]
            prev_desc = prev.get("description_en", "")
            if prev_desc:
                sentences = prev_desc.split(".")
                ctx["end_frame_visuals"] = (
                    sentences[-2].strip() + "." if len(sentences) > 1
                    else prev_desc[:100]
                )

        # Sequence-level continuity
        if sequence:
            anchors = sequence.get("continuity_anchors", {})
            if isinstance(anchors, dict):
                ctx["global_style_anchors"] = anchors.get("style_anchors", [])
                ctx["global_character_anchors"] = anchors.get("character_anchors", [])

            # v2: 5-Domain data for cross-shot continuity
            five_domains = sequence.get("five_domains", {})
            if five_domains:
                ctx["camera_evolution"] = five_domains.get("camera_evolution", "")
                ctx["lighting_evolution"] = five_domains.get("lighting_evolution", "")

        return ctx


# Max Seedance references (used in _build_multi_shot)
SEEDANCE_MAX_REFS = 12
