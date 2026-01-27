"""
Unified Pass (VDG Pass 1)

LLM-based semantic analysis with audio/motion context integration.

Architecture:
- Hook clip: 10fps (precise microbeat analysis)
- Full video: 1fps (overall causal structure)
- Audio context: BPM, onset timestamps
- Motion context: Dominant movement, segments

Output:
- UnifiedPassLLMOutput (analysis plan for CV pass)
- UnifiedPassProvenance (tracking metadata)
"""
from __future__ import annotations

import json
import logging
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings
from app.schemas.vdg_unified_pass import (
    AnalysisPlanLLM,
    AnalysisPointSeedLLM,
    CapsuleBriefLLM,
    EntityHintLLM,
    HookAttributesLLM,
    HookGenomeLLM,
    MeasurementSpecLLM,
    MicrobeatLLM,
    SceneLLM,
    UnifiedPassLLMOutput,
    UnifiedPassProvenance,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

DEFAULT_MODEL_ID = "gemini-2.0-flash-exp"
DEFAULT_MEDIA_RESOLUTION = "low"
DEFAULT_HOOK_CLIP_SECONDS = 4.0
DEFAULT_HOOK_CLIP_FPS = 10.0
DEFAULT_FULL_VIDEO_FPS = 1.0


# =============================================================================
# Video Duration Utility
# =============================================================================


def get_video_duration_ms(video_path: str) -> int:
    """
    Get video duration in milliseconds using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        Duration in milliseconds, or 0 if unable to determine
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            duration_sec = float(result.stdout.strip())
            return int(duration_sec * 1000)
    except Exception as e:
        logger.warning(f"Failed to get video duration: {e}")

    return 0


# =============================================================================
# Unified Pass System Prompt
# =============================================================================

UNIFIED_PASS_SYSTEM_PROMPT = """You are a professional video analyst specializing in viral content structure.

Your task is to analyze a video and produce a structured analysis plan for computer vision measurement.

## Context Provided
- Hook clip: First 4 seconds at 10fps (precise microbeat analysis)
- Full video: At 1fps (overall structure)
- Platform: {platform}
- Duration: {duration_ms}ms
- Audio context: {audio_summary}
- Motion context: {motion_summary}
- Caption: {caption}
- Hashtags: {hashtags}
- Top comments: {top_comments}

## Output Requirements (JSON)

1. **hook_genome**: Analyze the hook (first 3-5 seconds)
   - pattern: question/shock/promise/curiosity_gap/conflict/transformation/emotion
   - strength: 0.0-1.0
   - microbeats: Time-coded beats with roles
   - audio_sync_score: How well visual hook syncs with audio beats
   - **hook_attributes** (REQUIRED - 3-Axis Classification):
     - format: pov/skit/listicle/tutorial/challenge/duet/vlog/meme_remix/reaction/storytime/unknown
     - trigger: curiosity_gap/shock/relatability/satisfaction/educational/humor/nostalgia/fear/aspiration/unknown
     - device: text_on_screen/visual_hook/loud_noise/question/countdown/insert_clip/direct_address/cliffhanger/misdirection/unknown
     - secondary_triggers: Array of additional triggers (optional, max 2)
     - format_confidence: 0.0-1.0 (how confident in format classification)
     - trigger_confidence: 0.0-1.0 (how confident in trigger classification)
     - device_confidence: 0.0-1.0 (how confident in device classification)
     - classification_reasoning: Brief 1-sentence explanation for choices

2. **scenes**: Time-coded scene breakdown
   - Each scene: scene_id, t_start_ms, t_end_ms, role, description, key_elements
   - Roles: hook, setup, development, climax, resolution, cta

3. **entity_hints**: Entities to track in CV pass
   - key: Stable identifier (e.g., "main_person", "product_a")
   - entity_type: person/object/text/scene
   - description: Visual description for detection

4. **analysis_plan**: Points for CV measurement
   - points: List of AnalysisPointSeedLLM
     - t_center_ms: Center timestamp
     - t_window_ms: Window size (default 1000ms)
     - priority: critical/high/medium/low
     - reason: Why analyze this point
     - target_entity_keys: Entities to track
     - measurement_specs: Metrics to measure (center_offset, brightness, blur)

5. **capsule_brief**: High-level brief
   - dos: Techniques to replicate
   - donts: Things to avoid
   - key_insight: Main takeaway

Focus on:
- Hook effectiveness (first 3-5 seconds)
- Visual-audio synchronization (especially at beat/onset times)
- Key moments that drive engagement
- Composition and framing at critical points
"""


UNIFIED_PASS_USER_PROMPT = """Analyze this video and generate the structured analysis plan.

Return valid JSON matching the UnifiedPassLLMOutput schema.

Focus on:
1. Hook analysis with microbeat breakdown
2. Scene structure with time codes
3. Entity hints for CV tracking
4. Analysis points for CV measurement (prioritize hook and key moments)
5. Brief summary of techniques"""


# =============================================================================
# Unified Pass Class
# =============================================================================


class UnifiedPass:
    """
    VDG Pass 1: Unified semantic analysis with audio/motion context.

    Combines:
    - Gemini vision analysis (hook clip + full video)
    - Audio context (BPM, onsets)
    - Motion context (dominant movement, segments)

    Produces AnalysisPlan for CV pass.
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        media_resolution: str = DEFAULT_MEDIA_RESOLUTION,
        hook_clip_seconds: float = DEFAULT_HOOK_CLIP_SECONDS,
        hook_clip_fps: float = DEFAULT_HOOK_CLIP_FPS,
        full_video_fps: float = DEFAULT_FULL_VIDEO_FPS,
    ):
        """
        Initialize UnifiedPass.

        Args:
            model_id: Gemini model ID (default: gemini-2.0-flash-exp)
            media_resolution: Video resolution for LLM ("low" or "high")
            hook_clip_seconds: Duration of hook clip to analyze
            hook_clip_fps: FPS for hook clip extraction
            full_video_fps: FPS for full video extraction
        """
        self.model_id = model_id or DEFAULT_MODEL_ID
        self.media_resolution = media_resolution
        self.hook_clip_seconds = hook_clip_seconds
        self.hook_clip_fps = hook_clip_fps
        self.full_video_fps = full_video_fps

        # Lazy-loaded Gemini client
        self._client = None

    def _get_client(self):
        """Get or create Gemini client."""
        if self._client is None:
            try:
                from app.services.genai_utils import get_genai_client
                self._client = get_genai_client()
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                raise
        return self._client

    def run(
        self,
        video_path: str,
        duration_ms: int,
        platform: str,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        top_comments: Optional[List[str]] = None,
        audio_summary: str = "",
        motion_summary: str = "",
    ) -> Tuple[UnifiedPassLLMOutput, UnifiedPassProvenance]:
        """
        Execute unified semantic analysis.

        Args:
            video_path: Path to video file
            duration_ms: Video duration in milliseconds
            platform: Platform (tiktok/youtube/instagram)
            caption: Video caption
            hashtags: List of hashtags
            top_comments: Top comments for context
            audio_summary: Summary from audio analysis
            motion_summary: Summary from motion analysis

        Returns:
            Tuple of (UnifiedPassLLMOutput, UnifiedPassProvenance)
        """
        start_time = datetime.now(timezone.utc)
        provenance = UnifiedPassProvenance(
            model_id=self.model_id,
            media_resolution=self.media_resolution,
            hook_clip_seconds=self.hook_clip_seconds,
            hook_clip_fps=self.hook_clip_fps,
            full_video_fps=self.full_video_fps,
            start_time=start_time,
            audio_context_injected=bool(audio_summary),
            motion_context_injected=bool(motion_summary),
        )

        try:
            # 1. Extract video frames for LLM
            video_parts = self._prepare_video_parts(video_path, duration_ms)

            # 2. Build prompts
            system_prompt = UNIFIED_PASS_SYSTEM_PROMPT.format(
                platform=platform,
                duration_ms=duration_ms,
                audio_summary=audio_summary or "No audio data available",
                motion_summary=motion_summary or "No motion data available",
                caption=caption or "N/A",
                hashtags=", ".join(hashtags) if hashtags else "N/A",
                top_comments="\n".join(top_comments[:5]) if top_comments else "N/A",
            )

            # 3. Call LLM
            result = self._call_llm(
                system_prompt=system_prompt,
                user_prompt=UNIFIED_PASS_USER_PROMPT,
                video_parts=video_parts,
            )

            # 4. Parse result
            output = self._parse_llm_output(result)

            # 5. Ensure analysis plan has at least hook point
            if not output.analysis_plan.points:
                output.analysis_plan.points = self._generate_default_points(duration_ms)

            # Update provenance
            provenance.end_time = datetime.now(timezone.utc)
            output.audio_context_used = bool(audio_summary)
            output.motion_context_used = bool(motion_summary)

            logger.info(
                f"✅ UnifiedPass complete: "
                f"scenes={len(output.scenes)}, "
                f"entities={len(output.entity_hints)}, "
                f"analysis_points={len(output.analysis_plan.points)}"
            )

            return output, provenance

        except Exception as e:
            logger.error(f"UnifiedPass failed: {e}", exc_info=True)
            # Return minimal output on error
            provenance.end_time = datetime.now(timezone.utc)
            output = UnifiedPassLLMOutput(
                analysis_plan=AnalysisPlanLLM(
                    points=self._generate_default_points(duration_ms)
                )
            )
            return output, provenance

    def _prepare_video_parts(
        self,
        video_path: str,
        duration_ms: int,
    ) -> List[Any]:
        """
        Prepare video parts for LLM input.

        Extracts:
        - Hook clip (first N seconds at high FPS)
        - Full video at low FPS

        Returns:
            List of Part objects for Gemini
        """
        try:
            from google.genai import types
        except ImportError:
            logger.error("google.genai not available")
            return []

        parts = []

        # Read video bytes
        with open(video_path, "rb") as f:
            video_bytes = f.read()

        # For now, use full video as single part
        # TODO: Implement hook clip extraction with ffmpeg
        video_part = types.Part.from_bytes(
            data=video_bytes,
            mime_type="video/mp4"
        )
        parts.append(video_part)

        return parts

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        video_parts: List[Any],
    ) -> Dict[str, Any]:
        """
        Call Gemini LLM with video and prompts.

        Returns:
            Parsed JSON response
        """
        from app.services.vdg_2pass.gemini_utils import robust_generate_content
        from app.services.genai_utils import GenaiModelAdapter
        import asyncio

        client = self._get_client()

        # Build model adapter
        model = GenaiModelAdapter(
            client,
            self.model_id,
            system_instruction=system_prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.2,
                "top_p": 0.95,
                "max_output_tokens": 8192,
            },
        )

        # Build contents
        contents = video_parts + [user_prompt]

        # Run async generation in sync context
        async def _generate():
            return await robust_generate_content(
                model=model,
                contents=contents,
                result_schema=None,  # We'll parse manually
                max_retries=3,
                initial_backoff=1.0,
            )

        # Check if we're in async context
        try:
            loop = asyncio.get_running_loop()
            # We're in async context, need to run differently
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _generate())
                result = future.result(timeout=180)
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            result = asyncio.run(_generate())

        # Parse JSON response
        if hasattr(result, "model_dump"):
            return result.model_dump()
        elif isinstance(result, dict):
            return result
        elif isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM response as JSON")
                return {}
        else:
            return {}

    def _parse_llm_output(self, data: Dict[str, Any]) -> UnifiedPassLLMOutput:
        """
        Parse LLM output dict into UnifiedPassLLMOutput.

        Handles missing fields gracefully.
        """
        try:
            # Parse hook_genome
            hook_genome = None
            if data.get("hook_genome"):
                hg = data["hook_genome"]
                microbeats = []
                for mb in hg.get("microbeats", []):
                    microbeats.append(MicrobeatLLM(
                        beat_id=mb.get("beat_id", "beat_000"),
                        t_start_ms=mb.get("t_start_ms", 0),
                        t_end_ms=mb.get("t_end_ms", 0),
                        role=mb.get("role", ""),
                        description=mb.get("description", ""),
                        visual_element=mb.get("visual_element"),
                        audio_element=mb.get("audio_element"),
                    ))
                # Parse hook_attributes (3-axis classification)
                hook_attributes = None
                if hg.get("hook_attributes"):
                    ha = hg["hook_attributes"]
                    hook_attributes = HookAttributesLLM(
                        format=ha.get("format", "unknown"),
                        trigger=ha.get("trigger", "unknown"),
                        device=ha.get("device", "unknown"),
                        secondary_triggers=ha.get("secondary_triggers", []),
                        format_confidence=float(ha.get("format_confidence", 0.7)),
                        trigger_confidence=float(ha.get("trigger_confidence", 0.7)),
                        device_confidence=float(ha.get("device_confidence", 0.7)),
                        classification_reasoning=ha.get("classification_reasoning"),
                    )

                hook_genome = HookGenomeLLM(
                    pattern=hg.get("pattern", "unknown"),
                    strength=float(hg.get("strength", 0.5)),
                    microbeats=microbeats,
                    trigger_element=hg.get("trigger_element"),
                    emotional_target=hg.get("emotional_target"),
                    audio_sync_score=hg.get("audio_sync_score"),
                    hook_attributes=hook_attributes,
                )

            # Parse scenes
            scenes = []
            for s in data.get("scenes", []):
                scenes.append(SceneLLM(
                    scene_id=s.get("scene_id", f"scene_{len(scenes)}"),
                    t_start_ms=s.get("t_start_ms", 0),
                    t_end_ms=s.get("t_end_ms", 0),
                    role=s.get("role", "development"),
                    description=s.get("description", ""),
                    key_elements=s.get("key_elements", []),
                    dominant_movement=s.get("dominant_movement"),
                ))

            # Parse entity_hints
            entity_hints = []
            for eh in data.get("entity_hints", []):
                entity_hints.append(EntityHintLLM(
                    key=eh.get("key", f"entity_{len(entity_hints)}"),
                    entity_type=eh.get("entity_type", "object"),
                    description=eh.get("description", ""),
                    first_seen_ms=eh.get("first_seen_ms"),
                    last_seen_ms=eh.get("last_seen_ms"),
                ))

            # Parse analysis_plan
            plan_data = data.get("analysis_plan", {})
            points = []
            for p in plan_data.get("points", []):
                specs = []
                for spec in p.get("measurement_specs", []):
                    specs.append(MeasurementSpecLLM(
                        metric_id=spec.get("metric_id", "brightness"),
                        priority=spec.get("priority", "medium"),
                    ))
                points.append(AnalysisPointSeedLLM(
                    t_center_ms=p.get("t_center_ms", 0),
                    t_window_ms=p.get("t_window_ms", 1000),
                    priority=p.get("priority", "medium"),
                    reason=p.get("reason", ""),
                    target_entity_keys=p.get("target_entity_keys", []),
                    measurement_specs=specs,
                    evidence_note=p.get("evidence_note"),
                ))

            analysis_plan = AnalysisPlanLLM(
                points=points,
                total_points=len(points),
            )

            # Parse capsule_brief
            capsule_brief = None
            if data.get("capsule_brief"):
                cb = data["capsule_brief"]
                capsule_brief = CapsuleBriefLLM(
                    dos=cb.get("dos", []),
                    donts=cb.get("donts", []),
                    key_insight=cb.get("key_insight"),
                )

            return UnifiedPassLLMOutput(
                hook_genome=hook_genome,
                scenes=scenes,
                entity_hints=entity_hints,
                analysis_plan=analysis_plan,
                mise_en_scene_signals=data.get("mise_en_scene_signals", []),
                capsule_brief=capsule_brief,
                narrative_summary=data.get("narrative_summary"),
                comment_evidence_top5=data.get("comment_evidence_top5", []),
            )

        except Exception as e:
            logger.error(f"Failed to parse LLM output: {e}")
            return UnifiedPassLLMOutput()

    def _generate_default_points(self, duration_ms: int) -> List[AnalysisPointSeedLLM]:
        """
        Generate default analysis points when LLM fails.

        Creates points at:
        - Hook (0-3s) - critical
        - 25% mark - medium
        - 50% mark - medium
        - 75% mark - medium
        """
        points = []

        # Hook point (critical)
        points.append(AnalysisPointSeedLLM(
            t_center_ms=1500,
            t_window_ms=3000,
            priority="critical",
            reason="Hook analysis (default)",
            measurement_specs=[
                MeasurementSpecLLM(metric_id="center_offset"),
                MeasurementSpecLLM(metric_id="brightness"),
                MeasurementSpecLLM(metric_id="blur"),
            ],
        ))

        # Additional points at 25%, 50%, 75%
        for pct in [0.25, 0.5, 0.75]:
            t_ms = int(duration_ms * pct)
            points.append(AnalysisPointSeedLLM(
                t_center_ms=t_ms,
                t_window_ms=1000,
                priority="medium",
                reason=f"Default point at {int(pct * 100)}%",
                measurement_specs=[
                    MeasurementSpecLLM(metric_id="brightness"),
                ],
            ))

        return points


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "UnifiedPass",
    "UnifiedPassProvenance",
    "get_video_duration_ms",
]
