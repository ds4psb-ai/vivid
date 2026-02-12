"""AD Studio Brain — Core cinematic analysis service.

Analyzes scenarios or video references and produces:
1. Per-scene cinematic technique breakdown
2. Sequence intelligence (emotional arc, transitions, continuity)
3. Engine-optimized prompts (Kling 3.0, Seedance 2.0)

Usage:
    from app.services.ad_brain import ADStudioBrain

    brain = ADStudioBrain(model="gemini-3-pro-preview")
    result = await brain.analyze_scenario(
        scenario="한 남자가 빈 거리를 걷다가...",
        target_engines=["kling", "seedance"],
    )
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)

# Lazy import to avoid circular dependencies
_generation_client = None


def _get_gemini_client(model: str, byok_key: Optional[str] = None):
    """Get Gemini generation client (lazy)."""
    try:
        from google import genai

        api_key = byok_key or settings.GEMINI_API_KEY
        client = genai.Client(api_key=api_key)
        return client
    except ImportError:
        raise RuntimeError("google-genai package required for AD Studio")


# ============================================================================
# Constants
# ============================================================================

SCENE_ANALYSIS_SYSTEM_PROMPT = """You are an expert cinematic analyst and assistant director.
Your task is to analyze a scenario and break it into scenes, then for each scene:
1. Identify the cinematic techniques (composition, camera movement, angle, lighting, color)
2. Describe the emotional tone
3. Suggest transitions between scenes
4. Generate optimized prompts for AI video generation engines

IMPORTANT RULES:
- All Korean description fields (설명, 감정_위치, etc.) MUST be in Korean
- All prompt fields (kling_3_0, seedance_2_0) MUST be in English
- Do NOT mention any real director or artist names in any output field
- Focus on atomic cinematic techniques, not auteur styles
- Be specific about camera distances: EWS, WS, FS, MS, MCU, CU, ECU
- Include continuity anchors (character appearance, style constants)
"""

SCENE_ANALYSIS_USER_TEMPLATE = """Analyze this scenario and generate cinematic scene breakdown:

SCENARIO:
{scenario}

{style_hint_section}

Generate a JSON response with this exact structure:
{{
  "scenes": [
    {{
      "scene_number": 1,
      "description": "Korean scene description",
      "description_en": "English scene summary",
      "techniques": {{
        "composition": ["technique_id1", "technique_id2"],
        "camera_movement": ["technique_id"],
        "camera_angle": ["technique_id"],
        "lighting": ["technique_id"],
        "color": ["technique_id"]
      }},
      "sequence_context": {{
        "emotional_position": "Korean: where on the emotional arc",
        "camera_distance_flow": "Korean: e.g., 이전 WS → 현재 CU → 다음 MS",
        "transition_in": "Korean: how we enter this scene",
        "transition_out_setup": "Korean: setup for next scene transition"
      }},
      "continuity_anchors": {{
        "character": "Korean: character appearance constants",
        "style": "English: visual style constants"
      }},
      "prompts": {{
        "kling_3_0": "English prompt optimized for Kling 3.0. Subject-first structure. Include camera_preset, motion hints, composition details. 30-50 words.",
        "seedance_2_0": "English prompt optimized for Seedance 2.0. Cinematic description style. Include visual atmosphere and motion flow. 40-60 words."
      }}
    }}
  ],
  "sequence": {{
    "emotional_arc": [
      {{"scene_number": 1, "emotion": "Korean emotion", "intensity": 0.3, "description": "Korean description"}}
    ],
    "visual_rhythm": {{
      "camera_distance_curve": ["WS", "MS", "CU"],
      "edit_tempo": "Korean: edit rhythm description"
    }},
    "color_progression": [
      {{"scene_number": 1, "temperature": "warm", "palette": "Korean palette desc"}}
    ],
    "continuity_anchors": {{
      "character_anchors": ["Korean: constant character elements"],
      "style_anchors": ["English: constant style elements"],
      "lighting_anchors": ["Korean: constant lighting elements"]
    }}
  }}
}}

Target engines: {engines}
Respond ONLY with valid JSON. No markdown code blocks."""

VIDEO_ANALYSIS_SYSTEM_PROMPT = """You are an expert cinematic analyst. Analyze video scenes based on timestamps and visual descriptions.
For each scene segment, identify cinematic techniques and generate prompts for AI video recreation.
Follow the same output format as scenario analysis."""


# ============================================================================
# AD Studio Brain
# ============================================================================

class ADStudioBrain:
    """Core AD Studio analysis service."""

    def __init__(
        self,
        model: str = "gemini-3-pro-preview",
        byok_key: Optional[str] = None,
    ):
        self.model = model
        self.byok_key = byok_key

    async def analyze_scenario(
        self,
        scenario: str,
        style_hint: Optional[str] = None,
        target_engines: List[str] = None,
        language: str = "ko",
        user: Optional[dict] = None,
        db: Optional[AsyncSession] = None,
        progress_callback: Optional[Callable] = None,
    ):
        """Analyze a text scenario and generate cinematic prompts.

        Steps:
        1. Send scenario to Gemini for scene breakdown
        2. Enrich with technique RAG data
        3. Build sequence intelligence
        4. Generate engine-optimized prompts
        """
        from app.routers.dimension.ad_studio import (
            ADStudioResponse,
            SequenceAnalysis,
            SceneAnalysis,
            SequenceContext,
            SceneTechniques,
            TechniqueTag,
            EnginePrompts,
            EmotionalBeat,
            ColorBeat,
            VisualRhythm,
            ContinuityAnchors,
        )

        target_engines = target_engines or ["kling", "seedance"]

        # Step 1: Gemini scene breakdown
        if progress_callback:
            progress_callback(0.1, "Gemini로 씬 분석 중...")

        raw_analysis = await self._call_gemini_analysis(
            scenario=scenario,
            style_hint=style_hint,
            target_engines=target_engines,
        )

        if progress_callback:
            progress_callback(0.4, "시네마틱 기법 매칭 중...")

        # Step 2: Enrich with technique RAG
        scenes_data = raw_analysis.get("scenes", [])
        sequence_data = raw_analysis.get("sequence", {})

        enriched_scenes: List[SceneAnalysis] = []
        evidence_refs: List[str] = []

        for scene_raw in scenes_data:
            scene = self._build_scene_analysis(scene_raw)
            enriched_scenes.append(scene)

        if progress_callback:
            progress_callback(0.7, "시퀀스 인텔리전스 구축 중...")

        # Step 3: Build sequence analysis
        sequence = self._build_sequence_analysis(sequence_data, enriched_scenes)

        # Step 4: Compile evidence refs
        evidence_refs = [
            f"db:ad_studio:analysis:{len(enriched_scenes)}_scenes",
            f"model:{self.model}",
        ]

        if progress_callback:
            progress_callback(0.9, "결과 정리 중...")

        return ADStudioResponse(
            success=True,
            sequence=sequence,
            scenes=enriched_scenes,
            evidence_refs=evidence_refs,
        )

    async def analyze_video(
        self,
        video_url: str,
        scene_timestamps: List[str],
        style_hint: Optional[str] = None,
        target_engines: List[str] = None,
        language: str = "ko",
        user: Optional[dict] = None,
        db: Optional[AsyncSession] = None,
    ):
        """Analyze a video reference using scene timestamps."""
        from app.routers.dimension.ad_studio import ADStudioResponse

        target_engines = target_engines or ["kling", "seedance"]

        # Build a scenario description from video context
        video_scenario = (
            f"[Video Reference Analysis]\n"
            f"Video URL: {video_url}\n"
            f"Scene timestamps: {', '.join(scene_timestamps)}\n"
            f"Analyze each scene segment for cinematic techniques."
        )

        # Reuse scenario analysis with video context
        raw_analysis = await self._call_gemini_analysis(
            scenario=video_scenario,
            style_hint=style_hint,
            target_engines=target_engines,
            system_prompt=VIDEO_ANALYSIS_SYSTEM_PROMPT,
        )

        scenes_data = raw_analysis.get("scenes", [])
        sequence_data = raw_analysis.get("sequence", {})

        enriched_scenes = [self._build_scene_analysis(s) for s in scenes_data]
        sequence = self._build_sequence_analysis(sequence_data, enriched_scenes)

        evidence_refs = [
            f"db:ad_studio:video_analysis:{video_url[:50]}",
            f"model:{self.model}",
        ]

        return ADStudioResponse(
            success=True,
            sequence=sequence,
            scenes=enriched_scenes,
            evidence_refs=evidence_refs,
        )

    # ========================================================================
    # Private Helpers
    # ========================================================================

    async def _call_gemini_analysis(
        self,
        scenario: str,
        style_hint: Optional[str],
        target_engines: List[str],
        system_prompt: str = SCENE_ANALYSIS_SYSTEM_PROMPT,
    ) -> Dict[str, Any]:
        """Call Gemini for cinematic analysis."""
        style_section = ""
        if style_hint:
            style_section = f"STYLE HINT: {style_hint}"

        user_prompt = SCENE_ANALYSIS_USER_TEMPLATE.format(
            scenario=scenario,
            style_hint_section=style_section,
            engines=", ".join(target_engines),
        )

        try:
            client = _get_gemini_client(self.model, self.byok_key)
            response = await client.aio.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config={
                    "system_instruction": system_prompt,
                    "temperature": 0.3,
                    "response_mime_type": "application/json",
                },
            )

            raw_text = response.text.strip()

            # Clean markdown code blocks if present
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\n?", "", raw_text)
                raw_text = re.sub(r"\n?```$", "", raw_text)

            return json.loads(raw_text)

        except json.JSONDecodeError as e:
            logger.error(f"[ad-brain] JSON parse error: {e}, raw: {raw_text[:500]}")
            raise ValueError(f"AI 응답을 파싱할 수 없습니다: {e}")
        except Exception as e:
            logger.error(f"[ad-brain] Gemini call failed: {e}", exc_info=True)
            raise

    def _build_scene_analysis(self, scene_raw: Dict[str, Any]):
        """Build a SceneAnalysis from raw Gemini output, enriched with technique RAG."""
        from app.routers.dimension.ad_studio import (
            SceneAnalysis,
            SequenceContext,
            SceneTechniques,
            TechniqueTag,
            EnginePrompts,
        )

        # Load techniques for enrichment
        technique_tags = self._enrich_techniques(scene_raw.get("techniques", {}))

        seq_ctx_raw = scene_raw.get("sequence_context", {})
        prompts_raw = scene_raw.get("prompts", {})

        return SceneAnalysis(
            scene_number=scene_raw.get("scene_number", 0),
            description=scene_raw.get("description", ""),
            description_en=scene_raw.get("description_en", ""),
            techniques=technique_tags,
            sequence_context=SequenceContext(
                previous_exit=seq_ctx_raw.get("previous_exit"),
                transition_in=seq_ctx_raw.get("transition_in"),
                transition_out_setup=seq_ctx_raw.get("transition_out_setup"),
                emotional_position=seq_ctx_raw.get("emotional_position", ""),
                camera_distance_flow=seq_ctx_raw.get("camera_distance_flow", ""),
            ),
            prompts=EnginePrompts(
                kling_3_0=prompts_raw.get("kling_3_0", ""),
                seedance_2_0=prompts_raw.get("seedance_2_0", ""),
            ),
            continuity_anchors=scene_raw.get("continuity_anchors"),
        )

    def _enrich_techniques(self, techniques_raw: Dict[str, Any]) -> "SceneTechniques":
        """Enrich technique IDs with full technique data from RAG corpus."""
        from app.routers.dimension.ad_studio import SceneTechniques, TechniqueTag

        result = SceneTechniques()

        try:
            from app.rag.cinematic_techniques import get_technique_by_id
        except ImportError:
            logger.warning("[ad-brain] cinematic_techniques not available, using raw IDs")
            return result

        for category in ["composition", "camera_movement", "camera_angle", "lighting", "color"]:
            ids = techniques_raw.get(category, [])
            tags = []
            for tid in ids:
                if isinstance(tid, str):
                    technique = get_technique_by_id(tid)
                    if technique:
                        tags.append(TechniqueTag(
                            technique_id=technique.technique_id,
                            category=technique.category,
                            name_ko=technique.name_ko,
                            name_en=technique.name_en,
                            description_ko=technique.description_ko,
                        ))
                    else:
                        # Fallback: use the ID as-is
                        tags.append(TechniqueTag(
                            technique_id=tid,
                            category=category,
                            name_ko=tid.replace("_", " "),
                            name_en=tid.replace("_", " ").title(),
                            description_ko="",
                        ))
            setattr(result, category, tags)

        return result

    def _build_sequence_analysis(
        self,
        sequence_raw: Dict[str, Any],
        scenes: List,
    ):
        """Build SequenceAnalysis from raw data."""
        from app.routers.dimension.ad_studio import (
            SequenceAnalysis,
            EmotionalBeat,
            ColorBeat,
            VisualRhythm,
            ContinuityAnchors,
        )

        emotional_arc = []
        for beat in sequence_raw.get("emotional_arc", []):
            emotional_arc.append(EmotionalBeat(
                scene_number=beat.get("scene_number", 0),
                emotion=beat.get("emotion", ""),
                intensity=max(0.0, min(1.0, float(beat.get("intensity", 0.5)))),
                description=beat.get("description", ""),
            ))

        color_progression = []
        for cb in sequence_raw.get("color_progression", []):
            color_progression.append(ColorBeat(
                scene_number=cb.get("scene_number", 0),
                temperature=cb.get("temperature", "neutral"),
                palette=cb.get("palette", ""),
                hex_hint=cb.get("hex_hint"),
            ))

        rhythm_raw = sequence_raw.get("visual_rhythm", {})
        visual_rhythm = VisualRhythm(
            camera_distance_curve=rhythm_raw.get("camera_distance_curve", []),
            edit_tempo=rhythm_raw.get("edit_tempo", ""),
        ) if rhythm_raw else None

        anchors_raw = sequence_raw.get("continuity_anchors", {})
        continuity = ContinuityAnchors(
            character_anchors=anchors_raw.get("character_anchors", []),
            style_anchors=anchors_raw.get("style_anchors", []),
            lighting_anchors=anchors_raw.get("lighting_anchors", []),
        ) if anchors_raw else None

        return SequenceAnalysis(
            emotional_arc=emotional_arc,
            visual_rhythm=visual_rhythm,
            color_progression=color_progression,
            continuity_anchors=continuity,
        )
