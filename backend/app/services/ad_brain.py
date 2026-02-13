"""AD Studio Brain — Core cinematic analysis service.

Analyzes scenarios or video references and produces:
1. 5-Domain cinematic decomposition (VGoT-inspired)
2. Beat structure + emotional arc + pacing profile
3. Character-bound, engine-optimized multi-shot prompts

Usage:
    from app.services.ad_brain import ADStudioBrain

    brain = ADStudioBrain(model="gemini-3-pro-preview")
    result = await brain.analyze_scenario(
        scenario="한 남자가 빈 거리를 걷다가...",
        target_engines=["kling", "seedance", "veo"],
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
# Constants & Prompts
# ============================================================================

# Import the v2 Director prompts from the dedicated module
from app.services.cinematic_director_prompts import (
    DIRECTOR_SYSTEM_V2,
    DECOMPOSITION_USER_TEMPLATE,
    SHOT_TYPE_GUIDELINES,
    PACING_PROFILES,
    FEW_SHOT_EXAMPLES,
)

# Legacy v1 aliases (kept for video analysis which still uses simpler format)
SCENE_ANALYSIS_SYSTEM_PROMPT = DIRECTOR_SYSTEM_V2
SCENE_ANALYSIS_USER_TEMPLATE = DECOMPOSITION_USER_TEMPLATE

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
        """Analyze a text scenario via 5-Domain cinematic decomposition.

        Pipeline (VGoT-inspired):
        1. LLM Director decomposes scenario → beat structure + characters + shots
        2. Enrich shot techniques with RAG corpus data
        3. Build sequence intelligence (emotional arc, pacing, continuity)
        4. Return structured result with engine-ready outputs
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

        target_engines = target_engines or ["kling", "seedance", "veo"]

        # Step 1: 5-Domain Decomposition via Director LLM
        if progress_callback:
            progress_callback(0.1, "시네마틱 디렉터가 시나리오 분해 중...")

        raw_analysis = await self._call_gemini_analysis(
            scenario=scenario,
            style_hint=style_hint,
            target_engines=target_engines,
        )

        # Step 1.5: Validate and fix quality issues
        raw_analysis = await self._validate_and_fix(
            raw_analysis, scenario, style_hint, target_engines
        )

        if progress_callback:
            progress_callback(0.3, "캐릭터·비트 구조 추출 중...")

        # Step 2: Extract new 5-Domain fields
        characters_data = raw_analysis.get("characters", [])
        beat_structure = raw_analysis.get("beat_structure", {})
        shots_data = raw_analysis.get("shots", raw_analysis.get("scenes", []))
        sequence_data = raw_analysis.get("sequence", {})

        if progress_callback:
            progress_callback(0.5, "기법 RAG 매칭 중...")

        # Step 3: Enrich with technique RAG
        enriched_scenes: List[SceneAnalysis] = []
        for shot_raw in shots_data:
            scene = self._build_scene_analysis(shot_raw)
            enriched_scenes.append(scene)

        if progress_callback:
            progress_callback(0.7, "시퀀스 인텔리전스 구축 중...")

        # Step 4: Build sequence analysis (now with 5-domain data)
        sequence = self._build_sequence_analysis(sequence_data, enriched_scenes)

        # Step 5: Compile evidence + metadata
        evidence_refs = [
            f"db:ad_studio:analysis:{len(enriched_scenes)}_shots",
            f"model:{self.model}",
            f"decomposition:5-domain",
            f"beat_structure:{beat_structure.get('type', 'auto')}",
            f"pacing:{beat_structure.get('pacing_profile', 'dramatic')}",
        ]

        if progress_callback:
            progress_callback(0.9, "결과 정리 중...")

        return ADStudioResponse(
            success=True,
            sequence=sequence,
            scenes=enriched_scenes,
            evidence_refs=evidence_refs,
            characters=characters_data,
            beat_structure=beat_structure,
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
        """Call Gemini for cinematic analysis with few-shot and schema enforcement."""
        from app.routers.dimension.ad_studio import DecompositionOutput

        style_section = ""
        if style_hint:
            style_section = f"STYLE HINT: {style_hint}"

        # Select and inject few-shot example based on pacing/scenario
        few_shot_key = self._select_few_shot(style_hint, scenario)
        few_shot_json = json.dumps(
            FEW_SHOT_EXAMPLES[few_shot_key], ensure_ascii=False, indent=2
        )

        user_prompt = SCENE_ANALYSIS_USER_TEMPLATE.format(
            scenario=scenario,
            style_hint_section=style_section,
            engines=", ".join(target_engines),
        )
        # Inject few-shot (separate from .format() to avoid JSON brace conflicts)
        user_prompt = user_prompt.replace("__FEW_SHOT_PLACEHOLDER__", few_shot_json)

        try:
            client = _get_gemini_client(self.model, self.byok_key)
            response = await client.aio.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config={
                    "system_instruction": system_prompt,
                    "temperature": 0.7,
                    "response_mime_type": "application/json",
                    "response_schema": DecompositionOutput,
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
        """Build a SceneAnalysis from raw Gemini 5-Domain output, enriched with technique RAG.

        Handles both legacy format (scenes) and new format (shots with beat/action/audio).
        """
        from app.routers.dimension.ad_studio import (
            SceneAnalysis,
            SequenceContext,
            SceneTechniques,
            TechniqueTag,
            EnginePrompts,
        )

        # Load techniques for enrichment (expanded categories)
        technique_tags = self._enrich_techniques(scene_raw.get("techniques", {}))

        # Build sequence_context from new or legacy format
        seq_ctx_raw = scene_raw.get("sequence_context", {})
        beat = scene_raw.get("beat", "")
        transition = scene_raw.get("transition_to_next", "")

        # Extract prompts — legacy or build from new fields
        prompts_raw = scene_raw.get("prompts", {})
        if not prompts_raw and scene_raw.get("description_en"):
            # Auto-build prompts from 5-Domain shot data
            prompts_raw = self._auto_build_prompts(scene_raw)

        # Build continuity anchors (expanded format)
        anchors = scene_raw.get("continuity_anchors", {})

        return SceneAnalysis(
            scene_number=scene_raw.get("shot_number", scene_raw.get("scene_number", 0)),
            description=scene_raw.get("description", ""),
            description_en=scene_raw.get("description_en", ""),
            techniques=technique_tags,
            sequence_context=SequenceContext(
                previous_exit=seq_ctx_raw.get("previous_exit"),
                transition_in=seq_ctx_raw.get("transition_in", transition),
                transition_out_setup=seq_ctx_raw.get("transition_out_setup", transition),
                emotional_position=seq_ctx_raw.get("emotional_position", beat),
                camera_distance_flow=seq_ctx_raw.get("camera_distance_flow", ""),
            ),
            prompts=EnginePrompts(
                kling_3_0=prompts_raw.get("kling_3_0", ""),
                seedance_2_0=prompts_raw.get("seedance_2_0", ""),
                veo_3_1=prompts_raw.get("veo_3_1", ""),
            ),
            continuity_anchors=anchors,
        )

    def _auto_build_prompts(self, shot_raw: Dict[str, Any]) -> Dict[str, str]:
        """Auto-build engine prompts from 5-Domain shot fields.

        When the LLM returns the new format (shots with action, audio, characters),
        we synthesize per-engine prompts from the structured data.
        """
        desc_en = shot_raw.get("description_en", "")
        action_en = shot_raw.get("action_en", "")
        audio = shot_raw.get("audio", {})
        characters = shot_raw.get("characters_in_shot", [])
        techniques = shot_raw.get("techniques", {})

        # Extract technique names for prompt building
        camera_moves = techniques.get("camera_movement", [])
        shot_scales = techniques.get("shot_scale", techniques.get("camera_angle", []))
        lighting = techniques.get("lighting", [])

        # Build camera text
        camera_text = ""
        if shot_scales:
            scale = shot_scales[0] if isinstance(shot_scales[0], str) else ""
            camera_text = scale.replace("_", " ")
        if camera_moves:
            move = camera_moves[0] if isinstance(camera_moves[0], str) else ""
            camera_text += f" with {move.replace('_', ' ')}"

        # Build character text
        char_text = ""
        if characters:
            char_text = ", ".join(str(c) for c in characters[:2])

        # Audio hint
        audio_text = ""
        if audio:
            ambient = audio.get("ambient", "")
            music = audio.get("music", "")
            if ambient:
                audio_text = f"Sound: {ambient}."
            if music:
                audio_text += f" Music: {music}."

        # Kling: Subject-first, 5-Layer (Scene → Characters → Action → Camera → Style)
        kling_parts = []
        if desc_en:
            kling_parts.append(desc_en.rstrip("."))
        if char_text:
            kling_parts.append(char_text)
        if action_en:
            kling_parts.append(action_en.rstrip("."))
        if camera_text:
            kling_parts.append(camera_text.strip())
        kling_prompt = ". ".join(kling_parts)[:200]

        # Seedance: Cinematic atmosphere, motion-focused
        seedance_parts = []
        if desc_en:
            seedance_parts.append(desc_en)
        if action_en:
            seedance_parts.append(action_en)
        if camera_text:
            seedance_parts.append(f"Shot: {camera_text.strip()}.")
        if audio_text:
            seedance_parts.append(audio_text)
        seedance_prompt = " ".join(seedance_parts)[:300]

        return {
            "kling_3_0": kling_prompt,
            "seedance_2_0": seedance_prompt,
        }

    def _select_few_shot(self, style_hint: Optional[str], scenario: str) -> str:
        """Select best few-shot example based on style hint and scenario keywords."""
        text = f"{style_hint or ''} {scenario}".lower()

        explosive_kw = {
            "action", "chase", "explosion", "fight", "horror", "fast", "rapid",
            "intense", "battle", "war", "sprint", "crash", "punch",
            "추격", "전투", "폭발", "액션", "공포", "격투",
        }
        contemplative_kw = {
            "peaceful", "quiet", "slow", "art", "meditation", "nature",
            "romantic", "gentle", "serene", "calm", "dawn", "lake", "ocean",
            "평화", "고요", "느린", "자연", "명상", "새벽", "호수",
        }

        explosive_score = sum(1 for kw in explosive_kw if kw in text)
        contemplative_score = sum(1 for kw in contemplative_kw if kw in text)

        if explosive_score > contemplative_score and explosive_score > 0:
            return "explosive"
        if contemplative_score > explosive_score and contemplative_score > 0:
            return "contemplative"
        return "dramatic"

    async def _validate_and_fix(
        self,
        raw_analysis: Dict[str, Any],
        scenario: str,
        style_hint: Optional[str],
        target_engines: List[str],
    ) -> Dict[str, Any]:
        """Post-process validation with auto-retry on failure."""
        issues: List[str] = []

        # 1. ANTI-LAZY pattern check
        anti_lazy = re.compile(
            r"(위와 동일|이하 생략|similar to|same as (scene|shot)|같은 방식|생략|skip|\.{3,})",
            re.IGNORECASE,
        )
        for shot in raw_analysis.get("shots", []):
            shot_num = shot.get("shot_number", "?")
            for field in ("description", "description_en", "action_en"):
                val = shot.get(field, "")
                if val and anti_lazy.search(val):
                    issues.append(f"Shot {shot_num}: ANTI-LAZY in {field}")
            # Also check engine prompts
            prompts = shot.get("prompts", {})
            if isinstance(prompts, dict):
                for engine_key, prompt_val in prompts.items():
                    if prompt_val and anti_lazy.search(prompt_val):
                        issues.append(f"Shot {shot_num}: ANTI-LAZY in prompts.{engine_key}")

        # 2. Engine prompt length check (too short = likely placeholder)
        for shot in raw_analysis.get("shots", []):
            shot_num = shot.get("shot_number", "?")
            prompts = shot.get("prompts", {})
            if isinstance(prompts, dict):
                for engine in ("kling_3_0", "seedance_2_0", "veo_3_1"):
                    p = prompts.get(engine, "")
                    if p and len(p) < 20:
                        issues.append(
                            f"Shot {shot_num}: {engine} prompt too short ({len(p)} chars)"
                        )

        # 3. Beat structure completeness
        beats = raw_analysis.get("beat_structure", {}).get("beats", [])
        found_beats = {b.get("beat") for b in beats if isinstance(b, dict)}
        required_beats = {"OPENER", "CLIMAX", "RESOLVE"}
        missing = required_beats - found_beats
        if missing:
            issues.append(f"Missing required beats: {missing}")

        # 4. Character binding consistency
        chars = raw_analysis.get("characters", [])
        char_names = set()
        for c in chars:
            if isinstance(c, dict):
                char_names.add(c.get("name", ""))
        for shot in raw_analysis.get("shots", []):
            for c in shot.get("characters_in_shot", []):
                token = c if isinstance(c, str) else c.get("name", "") if isinstance(c, dict) else ""
                # Extract name from binding token: [Character A: desc] → Character A
                clean = re.sub(r"\[([^:]+):.*\]", r"\1", token).strip()
                if clean and clean not in char_names and not any(
                    clean in name for name in char_names
                ):
                    issues.append(
                        f"Shot {shot.get('shot_number', '?')}: unbound character '{clean}'"
                    )

        # 5. Retry once if issues found
        if issues:
            logger.warning(f"[ad-brain] Validation found {len(issues)} issues: {issues}")
            return await self._retry_with_fixes(
                raw_analysis, issues, scenario, style_hint, target_engines
            )

        return raw_analysis

    async def _retry_with_fixes(
        self,
        original: Dict[str, Any],
        issues: List[str],
        scenario: str,
        style_hint: Optional[str],
        target_engines: List[str],
    ) -> Dict[str, Any]:
        """Retry Gemini with fix instructions for validation issues."""
        from app.routers.dimension.ad_studio import DecompositionOutput

        issues_text = "\n".join(f"- {issue}" for issue in issues)
        fix_prompt = (
            "The following JSON was generated for a cinematic decomposition but has quality issues.\n\n"
            f"## ISSUES TO FIX\n{issues_text}\n\n"
            "## ORIGINAL JSON\n"
            f"{json.dumps(original, ensure_ascii=False, indent=2)}\n\n"
            "## INSTRUCTIONS\n"
            "Fix ALL listed issues. For ANTI-LAZY issues, rewrite the text with unique, specific content. "
            "For short prompts, expand with cinematic detail (30-80 words). "
            "For missing beats, add the required beat entries. "
            "For unbound characters, ensure they match the characters list.\n"
            "Return the COMPLETE fixed JSON."
        )

        try:
            client = _get_gemini_client(self.model, self.byok_key)
            response = await client.aio.models.generate_content(
                model=self.model,
                contents=fix_prompt,
                config={
                    "system_instruction": "You are a JSON fixer for cinematic decomposition outputs. Fix the issues and return valid JSON.",
                    "temperature": 0.4,
                    "response_mime_type": "application/json",
                    "response_schema": DecompositionOutput,
                },
            )

            raw_text = response.text.strip()
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\n?", "", raw_text)
                raw_text = re.sub(r"\n?```$", "", raw_text)

            fixed = json.loads(raw_text)
            logger.info(f"[ad-brain] Retry fix successful, {len(issues)} issues addressed")
            return fixed

        except Exception as e:
            logger.warning(f"[ad-brain] Retry fix failed: {e}, returning original")
            return original

    def _enrich_techniques(self, techniques_raw: Dict[str, Any]) -> "SceneTechniques":
        """Enrich technique IDs with full technique data from RAG corpus.

        Now supports all 12 categories from the expanded corpus.
        """
        from app.routers.dimension.ad_studio import SceneTechniques, TechniqueTag

        result = SceneTechniques()

        try:
            from app.rag.cinematic_techniques import get_technique_by_id
        except ImportError:
            logger.warning("[ad-brain] cinematic_techniques not available, using raw IDs")
            return result

        # All 12 categories from the expanded corpus
        all_categories = [
            "composition", "camera_movement", "camera_angle", "lighting", "color",
            "shot_scale", "focus_technique", "lens_character", "editing_rhythm",
            "transition_type", "aesthetic_style", "physics_motion",
        ]

        for category in all_categories:
            ids = techniques_raw.get(category, [])
            if not ids:
                continue
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
        """Build SequenceAnalysis from raw data, including 5-Domain analysis."""
        from app.routers.dimension.ad_studio import (
            SequenceAnalysis,
            EmotionalBeat,
            ColorBeat,
            VisualRhythm,
            ContinuityAnchors,
            FiveDomains,
        )

        emotional_arc = []
        for beat in sequence_raw.get("emotional_arc", []):
            # Support both shot_number (v2) and scene_number (v1)
            num = beat.get("shot_number", beat.get("scene_number", 0))
            emotional_arc.append(EmotionalBeat(
                scene_number=num,
                emotion=beat.get("emotion", ""),
                intensity=max(0.0, min(1.0, float(beat.get("intensity", 0.5)))),
                description=beat.get("description", ""),
            ))

        color_progression = []
        for cb in sequence_raw.get("color_progression", []):
            num = cb.get("shot_number", cb.get("scene_number", 0))
            color_progression.append(ColorBeat(
                scene_number=num,
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

        # v2: 5-Domain analysis (VGoT-inspired)
        five_raw = sequence_raw.get("five_domains", {})
        five_domains = FiveDomains(
            character_dynamics=five_raw.get("character_dynamics", ""),
            background_continuity=five_raw.get("background_continuity", ""),
            relationship_evolution=five_raw.get("relationship_evolution", ""),
            camera_evolution=five_raw.get("camera_evolution", ""),
            lighting_evolution=five_raw.get("lighting_evolution", ""),
        ) if five_raw else None

        continuity_score = self._calculate_continuity_score(
            sequence_raw=sequence_raw,
            scenes_count=len(scenes or []),
        )

        return SequenceAnalysis(
            emotional_arc=emotional_arc,
            visual_rhythm=visual_rhythm,
            color_progression=color_progression,
            continuity_anchors=continuity,
            five_domains=five_domains,
            continuity_score=continuity_score,
        )

    def _calculate_continuity_score(
        self,
        sequence_raw: Dict[str, Any],
        scenes_count: int,
    ) -> float:
        """Compute a normalized continuity score (0.0~1.0) for sequence quality checks."""
        anchors_raw = sequence_raw.get("continuity_anchors", {}) or {}
        emotional_arc = sequence_raw.get("emotional_arc", []) or []
        rhythm_raw = sequence_raw.get("visual_rhythm", {}) or {}
        five_raw = sequence_raw.get("five_domains", {}) or {}

        def _as_non_empty_str_list(values: Any) -> List[str]:
            if not isinstance(values, list):
                return []
            return [str(v).strip() for v in values if str(v).strip()]

        character_anchors = _as_non_empty_str_list(anchors_raw.get("character_anchors"))
        style_anchors = _as_non_empty_str_list(anchors_raw.get("style_anchors"))
        lighting_anchors = _as_non_empty_str_list(anchors_raw.get("lighting_anchors"))
        total_anchors = len(character_anchors) + len(style_anchors) + len(lighting_anchors)

        anchor_baseline = max(3, scenes_count)
        anchor_density = min(total_anchors / anchor_baseline, 1.0) if total_anchors else 0.0

        if scenes_count > 0:
            arc_coverage = min(len(emotional_arc) / scenes_count, 1.0)
        else:
            arc_coverage = 1.0 if emotional_arc else 0.0

        camera_curve = []
        if isinstance(rhythm_raw, dict):
            camera_curve = _as_non_empty_str_list(rhythm_raw.get("camera_distance_curve"))
        if scenes_count > 0:
            curve_coverage = min(len(camera_curve) / scenes_count, 1.0)
        else:
            curve_coverage = 1.0 if camera_curve else 0.0

        domain_fields = (
            "character_dynamics",
            "background_continuity",
            "relationship_evolution",
            "camera_evolution",
            "lighting_evolution",
        )
        if isinstance(five_raw, dict):
            filled_domains = sum(
                1 for key in domain_fields if str(five_raw.get(key, "")).strip()
            )
            five_domains_score = filled_domains / len(domain_fields)
        else:
            five_domains_score = 0.0

        score = (
            0.35 * anchor_density
            + 0.25 * arc_coverage
            + 0.20 * curve_coverage
            + 0.20 * five_domains_score
        )
        return round(max(0.0, min(score, 1.0)), 3)
