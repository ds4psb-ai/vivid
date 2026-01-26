"""Story Engine Service - Unified Story + Prompt Orchestration.

Mega app combining:
- Story Architect: Scenario generation from concepts
- Prompt Alchemy: Platform-specific prompt translation
- System Prompt Generator: Logic Vector → Shot Grammar

Features:
- DNA Lab Logic Vector integration
- Multi-platform prompt generation
- Shot list breakdown with tool recommendations
- SSE progress streaming

Usage:
    from app.services.story_engine_service import StoryEngineService

    service = StoryEngineService()
    result = await service.generate_story(
        concept="dark thriller in abandoned factory",
        logic_vector=lv,
        target_platform="veo",
    )
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from app.schemas.vpe import LogicVector

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

class StoryEngineComponent(str, Enum):
    """Story Engine components."""
    STORY = "story"
    PROMPT = "prompt"
    SYSTEM_PROMPT = "system_prompt"
    SHOT_LIST = "shot_list"


# Component credit costs
STORY_ENGINE_CREDITS = {
    StoryEngineComponent.STORY: 15,
    StoryEngineComponent.PROMPT: 5,
    StoryEngineComponent.SYSTEM_PROMPT: 3,
    StoryEngineComponent.SHOT_LIST: 10,
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class StoryScenario:
    """Generated story scenario."""
    title: str = ""
    logline: str = ""
    genre: str = ""
    structure: str = ""
    duration_seconds: int = 60
    scenes: List[Dict[str, Any]] = field(default_factory=list)
    characters: List[Dict[str, Any]] = field(default_factory=list)
    visual_style: str = ""
    mood: str = ""
    setting: str = ""
    raw_content: str = ""


@dataclass
class TranslatedPrompt:
    """Platform-specific translated prompt."""
    platform: str = ""
    prompt: str = ""
    negative_prompt: str = ""
    audio_notes: str = ""
    duration_seconds: int = 8
    quality_score: float = 0.0


@dataclass
class ShotListItem:
    """Single shot in the shot list."""
    shot_number: int = 0
    time_range: str = ""
    start_seconds: float = 0.0
    end_seconds: float = 0.0
    duration: float = 0.0
    shot_type: str = "medium"
    description: str = ""
    camera_movement: str = "static"
    recommended_tool: str = "veo"
    tool_reason: str = ""
    audio_notes: str = ""
    system_prompt: Optional[str] = None


@dataclass
class StoryEngineResult:
    """Result from Story Engine orchestration."""
    success: bool = False
    trace_id: str = ""
    components_run: List[str] = field(default_factory=list)
    scenario: Optional[StoryScenario] = None
    translated_prompts: List[TranslatedPrompt] = field(default_factory=list)
    system_prompt: Optional[str] = None
    shot_list: List[ShotListItem] = field(default_factory=list)
    logic_vector_used: bool = False
    confidence: float = 0.0
    credits_used: int = 0
    evidence_refs: List[str] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)


# =============================================================================
# Story Engine Service
# =============================================================================

class StoryEngineService:
    """Orchestrates Story Architect, Prompt Alchemy, and System Prompt generation."""

    def __init__(self, gemini_api_key: Optional[str] = None):
        """Initialize the Story Engine service.

        Args:
            gemini_api_key: Optional Gemini API key (uses settings if not provided)
        """
        self._gemini_key = gemini_api_key

    def calculate_total_credits(self, components: List[str]) -> int:
        """Calculate total credits for selected components.

        Args:
            components: List of component names to run

        Returns:
            Total credits needed
        """
        total = 0
        for comp_name in components:
            try:
                comp = StoryEngineComponent(comp_name.lower())
                total += STORY_ENGINE_CREDITS.get(comp, 0)
            except ValueError:
                continue
        return total

    async def generate_story(
        self,
        concept: str,
        logic_vector: Optional[LogicVector] = None,
        auteur_key: Optional[str] = None,
        genre: str = "drama",
        structure: str = "3-act",
        duration_seconds: int = 60,
        persona_data: Optional[str] = None,
        reference_analysis: Optional[str] = None,
        target_platforms: Optional[List[str]] = None,
        generate_shot_list: bool = False,
        language: str = "ko",
        model: str = "gemini-3-flash-preview",
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> StoryEngineResult:
        """Generate a complete story with optional prompts and shot list.

        Args:
            concept: Story concept or idea
            logic_vector: DNA Lab Logic Vector for style guidance
            auteur_key: Auteur key for RAG (used if no logic_vector)
            genre: Story genre
            structure: Narrative structure (3-act, etc.)
            duration_seconds: Target video duration
            persona_data: Creator persona data
            reference_analysis: Reference analysis results
            target_platforms: Platforms to generate prompts for
            generate_shot_list: Whether to generate shot list
            language: Output language
            model: AI model to use
            progress_callback: Optional callback for progress updates

        Returns:
            StoryEngineResult with scenario, prompts, and shot list
        """
        trace_id = f"story-engine-{uuid.uuid4().hex[:12]}"
        result = StoryEngineResult(trace_id=trace_id)
        components_run = []
        evidence_refs = []
        credits_used = 0

        try:
            # 1. Generate scenario using Story Architect
            if progress_callback:
                progress_callback("시나리오 생성 중...", 0.1)

            scenario = await self._run_story_architect(
                concept=concept,
                genre=genre,
                structure=structure,
                duration_seconds=duration_seconds,
                persona_data=persona_data,
                reference_analysis=reference_analysis,
                logic_vector=logic_vector,
                language=language,
                model=model,
            )
            result.scenario = scenario
            components_run.append("story")
            credits_used += STORY_ENGINE_CREDITS[StoryEngineComponent.STORY]
            evidence_refs.append(f"db:story_engine:scenario:{trace_id}")

            # 2. Generate system prompt if Logic Vector provided
            if logic_vector:
                if progress_callback:
                    progress_callback("시스템 프롬프트 생성 중...", 0.3)

                system_prompt = await self._generate_system_prompt(
                    logic_vector=logic_vector,
                    scenario=scenario,
                    target_platform=target_platforms[0] if target_platforms else "veo",
                )
                result.system_prompt = system_prompt
                result.logic_vector_used = True
                components_run.append("system_prompt")
                credits_used += STORY_ENGINE_CREDITS[StoryEngineComponent.SYSTEM_PROMPT]
                evidence_refs.append(f"db:story_engine:system_prompt:{trace_id}")

            # 3. Generate platform-specific prompts if requested
            if target_platforms:
                if progress_callback:
                    progress_callback("플랫폼별 프롬프트 변환 중...", 0.5)

                scene_description = scenario.raw_content or self._scenario_to_description(scenario)

                prompts = await self._run_prompt_alchemy(
                    scene_description=scene_description,
                    target_platforms=target_platforms,
                    style=scenario.visual_style or "cinematic",
                    auteur_key=auteur_key or (logic_vector.auteur_id if logic_vector else None),
                    language=language,
                    model=model,
                )
                result.translated_prompts = prompts
                components_run.append("prompt")
                credits_used += STORY_ENGINE_CREDITS[StoryEngineComponent.PROMPT] * len(target_platforms)
                evidence_refs.extend([f"db:story_engine:prompt:{p.platform}:{trace_id}" for p in prompts])

            # 4. Generate shot list if requested
            if generate_shot_list and scenario:
                if progress_callback:
                    progress_callback("샷 리스트 생성 중...", 0.7)

                shot_list = await self._generate_shot_list(
                    scenario=scenario,
                    logic_vector=logic_vector,
                    duration_seconds=duration_seconds,
                    model=model,
                )
                result.shot_list = shot_list
                components_run.append("shot_list")
                credits_used += STORY_ENGINE_CREDITS[StoryEngineComponent.SHOT_LIST]
                evidence_refs.append(f"db:story_engine:shot_list:{trace_id}")

            if progress_callback:
                progress_callback("완료", 1.0)

            result.success = True
            result.components_run = components_run
            result.credits_used = credits_used
            result.evidence_refs = evidence_refs
            result.confidence = self._calculate_confidence(result)

        except Exception as e:
            logger.error(f"[STORY_ENGINE] Error in generate_story: {e}")
            result.errors["general"] = str(e)
            result.components_run = components_run
            result.credits_used = credits_used
            result.evidence_refs = evidence_refs

        return result

    async def generate_system_prompt_only(
        self,
        logic_vector: LogicVector,
        story_description: Optional[str] = None,
        target_platform: str = "veo",
    ) -> str:
        """Generate only the system prompt from Logic Vector.

        Args:
            logic_vector: DNA Lab Logic Vector
            story_description: Optional story/scene description
            target_platform: Target video generation platform

        Returns:
            System prompt string
        """
        from app.routers.story_engine.system_prompt import (
            SystemPromptGenerator,
            StoryStructure,
        )

        generator = SystemPromptGenerator()
        story_structure = None

        if story_description:
            story_structure = StoryStructure(shot_description=story_description)

        result = generator.generate(
            logic_vector=logic_vector,
            story_structure=story_structure,
            target_platform=target_platform,
        )

        return result.system_prompt

    async def translate_prompts_only(
        self,
        scene_description: str,
        target_platforms: List[str],
        style: str = "cinematic",
        auteur_key: Optional[str] = None,
        language: str = "ko",
        model: str = "gemini-3-flash-preview",
    ) -> List[TranslatedPrompt]:
        """Translate scene description to platform-specific prompts.

        Args:
            scene_description: Scene description to translate
            target_platforms: List of target platforms
            style: Visual style
            auteur_key: Optional auteur key for RAG
            language: Output language
            model: AI model

        Returns:
            List of translated prompts
        """
        return await self._run_prompt_alchemy(
            scene_description=scene_description,
            target_platforms=target_platforms,
            style=style,
            auteur_key=auteur_key,
            language=language,
            model=model,
        )

    async def generate_shot_list_only(
        self,
        scenario_text: str,
        duration_seconds: int = 60,
        logic_vector: Optional[LogicVector] = None,
        model: str = "gemini-3-flash-preview",
    ) -> List[ShotListItem]:
        """Generate only the shot list from scenario.

        Args:
            scenario_text: Scenario text
            duration_seconds: Total duration
            logic_vector: Optional Logic Vector for style guidance
            model: AI model

        Returns:
            List of shot items
        """
        scenario = StoryScenario(raw_content=scenario_text, duration_seconds=duration_seconds)
        return await self._generate_shot_list(
            scenario=scenario,
            logic_vector=logic_vector,
            duration_seconds=duration_seconds,
            model=model,
        )

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def _run_story_architect(
        self,
        concept: str,
        genre: str,
        structure: str,
        duration_seconds: int,
        persona_data: Optional[str],
        reference_analysis: Optional[str],
        logic_vector: Optional[LogicVector],
        language: str,
        model: str,
    ) -> StoryScenario:
        """Run Story Architect to generate scenario."""
        from google import genai
        from google.genai import types
        from app.config import settings
        import json

        # Build system prompt with Logic Vector guidance if available
        style_guidance = ""
        if logic_vector:
            style_guidance = f"""
VISUAL STYLE GUIDANCE (From Logic Vector):
- Auteur: {logic_vector.auteur_id}
- Composition: {logic_vector.composition.primary_strategy}
- Camera Style: Dolly {int(logic_vector.camera_grammar.dolly * 100)}%, Handheld {int(logic_vector.camera_grammar.handheld * 100)}%
- Lighting: {logic_vector.lighting_physics.key_light}
- Color: {logic_vector.color_science.lut_reference or 'natural'}
- Pacing: {logic_vector.cadence.tempo or 'moderate'}
"""

        system_prompt = f"""You are a Professional Video Scenario Writer.

Create a detailed video scenario for AI video generation.

OUTPUT FORMAT (JSON):
{{
    "title": "시나리오 제목",
    "logline": "한 줄 요약",
    "genre": "{genre}",
    "structure": "{structure}",
    "duration_seconds": {duration_seconds},
    "visual_style": "시각적 스타일 설명",
    "mood": "분위기",
    "setting": "장소/시대",
    "scenes": [
        {{
            "scene_number": 1,
            "duration_seconds": 15,
            "description": "씬 설명",
            "visual_notes": "비주얼 노트",
            "audio_notes": "오디오 노트"
        }}
    ],
    "characters": [
        {{
            "name": "캐릭터명",
            "description": "설명",
            "visual_appearance": "외모"
        }}
    ]
}}
{style_guidance}
Language: {language}"""

        user_prompt = f"""Create a video scenario for:

CONCEPT: {concept}

GENRE: {genre}
STRUCTURE: {structure}
DURATION: {duration_seconds} seconds

{"PERSONA DATA: " + persona_data if persona_data else ""}
{"REFERENCE ANALYSIS: " + reference_analysis if reference_analysis else ""}

Generate a complete scenario with scenes covering the full duration."""

        try:
            api_key = self._gemini_key or settings.GEMINI_API_KEY
            client = genai.Client(api_key=api_key)

            response = await client.aio.models.generate_content(
                model=model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.8,
                    response_mime_type="application/json",
                ),
            )

            text = response.text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
                if text.startswith("json"):
                    text = text[4:].strip()

            data = json.loads(text)

            return StoryScenario(
                title=data.get("title", ""),
                logline=data.get("logline", ""),
                genre=data.get("genre", genre),
                structure=data.get("structure", structure),
                duration_seconds=data.get("duration_seconds", duration_seconds),
                scenes=data.get("scenes", []),
                characters=data.get("characters", []),
                visual_style=data.get("visual_style", ""),
                mood=data.get("mood", ""),
                setting=data.get("setting", ""),
                raw_content=text,
            )

        except Exception as e:
            logger.error(f"[STORY_ENGINE] Story Architect error: {e}")
            raise

    async def _generate_system_prompt(
        self,
        logic_vector: LogicVector,
        scenario: StoryScenario,
        target_platform: str,
    ) -> str:
        """Generate system prompt from Logic Vector."""
        from app.routers.story_engine.system_prompt import (
            SystemPromptGenerator,
            StoryStructure,
        )

        generator = SystemPromptGenerator()
        story_structure = StoryStructure(
            title=scenario.title,
            logline=scenario.logline,
            genre=scenario.genre,
            mood=scenario.mood,
            setting=scenario.setting,
            shot_description=scenario.raw_content[:500] if scenario.raw_content else None,
        )

        result = generator.generate(
            logic_vector=logic_vector,
            story_structure=story_structure,
            target_platform=target_platform,
        )

        return result.system_prompt

    async def _run_prompt_alchemy(
        self,
        scene_description: str,
        target_platforms: List[str],
        style: str,
        auteur_key: Optional[str],
        language: str,
        model: str,
    ) -> List[TranslatedPrompt]:
        """Run Prompt Alchemy for each platform."""
        from google import genai
        from google.genai import types
        from app.config import settings
        import json

        platform_prompts = []

        for platform in target_platforms:
            try:
                system_prompt = f"""You are a Professional AI Video Prompt Engineer.

Translate the scene description into an optimized prompt for {platform}.

Platform-specific rules:
- veo_31: Use [Dialogue]: format, add "No subtitles"
- kling_26: Use Beat timestamp format, emphasize lip sync
- sora_max_2pro: Use style references, force-reaction physics

OUTPUT FORMAT (JSON):
{{
    "platform": "{platform}",
    "prompt": "optimized prompt text",
    "negative_prompt": "things to avoid",
    "audio_notes": "audio/dialogue instructions",
    "duration_seconds": 8,
    "quality_score": 0.85
}}

Language: {language}"""

                user_prompt = f"""Translate this scene for {platform}:

SCENE: {scene_description[:2000]}

STYLE: {style}
{"AUTEUR REFERENCE: " + auteur_key if auteur_key else ""}

Generate an optimized prompt."""

                api_key = self._gemini_key or settings.GEMINI_API_KEY
                client = genai.Client(api_key=api_key)

                response = await client.aio.models.generate_content(
                    model=model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.7,
                        response_mime_type="application/json",
                    ),
                )

                text = response.text.strip()
                if text.startswith("```"):
                    lines = text.split("\n")
                    text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
                    if text.startswith("json"):
                        text = text[4:].strip()

                data = json.loads(text)

                platform_prompts.append(TranslatedPrompt(
                    platform=data.get("platform", platform),
                    prompt=data.get("prompt", ""),
                    negative_prompt=data.get("negative_prompt", ""),
                    audio_notes=data.get("audio_notes", ""),
                    duration_seconds=data.get("duration_seconds", 8),
                    quality_score=data.get("quality_score", 0.0),
                ))

            except Exception as e:
                logger.warning(f"[STORY_ENGINE] Prompt translation failed for {platform}: {e}")
                platform_prompts.append(TranslatedPrompt(
                    platform=platform,
                    prompt=scene_description[:500],
                    quality_score=0.0,
                ))

        return platform_prompts

    async def _generate_shot_list(
        self,
        scenario: StoryScenario,
        logic_vector: Optional[LogicVector],
        duration_seconds: int,
        model: str,
    ) -> List[ShotListItem]:
        """Generate shot list from scenario."""
        from google import genai
        from google.genai import types
        from app.config import settings
        import json

        # Build camera guidance from Logic Vector
        camera_guidance = ""
        if logic_vector:
            camera_guidance = f"""
CAMERA STYLE GUIDANCE:
- Dolly shots: {int(logic_vector.camera_grammar.dolly * 100)}%
- Handheld: {int(logic_vector.camera_grammar.handheld * 100)}%
- Push-in: {int(logic_vector.camera_grammar.push_in * 100)}%
- Static: {int(logic_vector.camera_grammar.static * 100)}%
- Composition: {logic_vector.composition.primary_strategy}
- Symmetry: {"high" if logic_vector.composition.symmetry_score > 0.7 else "low"}
"""

        system_prompt = f"""You are a Professional Storyboard Director.

Break down the scenario into precise SHOT SEGMENTS for AI video generation.

RULES:
1. Each shot must be ≤8 seconds (AI video limit)
2. Cover the ENTIRE {duration_seconds} second duration
3. Use precise time ranges: "0:00-0:03", "0:04-0:08", etc.

TOOL SELECTION:
- kling: Close-ups, static shots, high facial fidelity
- sora: High motion, action, complex transitions
- veo: Cinematic narrative, atmosphere, audio sync
{camera_guidance}
OUTPUT FORMAT (JSON array):
[
  {{
    "shot_number": 1,
    "time_range": "0:00-0:03",
    "start_seconds": 0,
    "end_seconds": 3,
    "duration": 3,
    "shot_type": "wide",
    "description": "Visual description",
    "camera_movement": "static",
    "recommended_tool": "veo",
    "tool_reason": "Establishing shot",
    "audio_notes": "Ambient sounds"
  }}
]"""

        scenario_text = scenario.raw_content or self._scenario_to_description(scenario)

        user_prompt = f"""Break down this scenario into shots:

SCENARIO:
{scenario_text[:3000]}

DURATION: {duration_seconds} seconds

Generate a complete shot list."""

        try:
            api_key = self._gemini_key or settings.GEMINI_API_KEY
            client = genai.Client(api_key=api_key)

            response = await client.aio.models.generate_content(
                model=model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    response_mime_type="application/json",
                ),
            )

            text = response.text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
                if text.startswith("json"):
                    text = text[4:].strip()

            shots_data = json.loads(text)
            shots = []

            for shot_data in shots_data:
                shot = ShotListItem(
                    shot_number=shot_data.get("shot_number", len(shots) + 1),
                    time_range=shot_data.get("time_range", ""),
                    start_seconds=shot_data.get("start_seconds", 0),
                    end_seconds=shot_data.get("end_seconds", 0),
                    duration=shot_data.get("duration", 0),
                    shot_type=shot_data.get("shot_type", "medium"),
                    description=shot_data.get("description", ""),
                    camera_movement=shot_data.get("camera_movement", "static"),
                    recommended_tool=shot_data.get("recommended_tool", "veo"),
                    tool_reason=shot_data.get("tool_reason", ""),
                    audio_notes=shot_data.get("audio_notes", ""),
                )
                shots.append(shot)

            return shots

        except Exception as e:
            logger.error(f"[STORY_ENGINE] Shot list generation error: {e}")
            raise

    def _scenario_to_description(self, scenario: StoryScenario) -> str:
        """Convert StoryScenario to description string."""
        parts = []

        if scenario.title:
            parts.append(f"Title: {scenario.title}")
        if scenario.logline:
            parts.append(f"Logline: {scenario.logline}")
        if scenario.visual_style:
            parts.append(f"Style: {scenario.visual_style}")
        if scenario.mood:
            parts.append(f"Mood: {scenario.mood}")
        if scenario.setting:
            parts.append(f"Setting: {scenario.setting}")

        if scenario.scenes:
            parts.append("\nScenes:")
            for scene in scenario.scenes[:5]:
                parts.append(f"- {scene.get('description', '')}")

        return "\n".join(parts)

    def _calculate_confidence(self, result: StoryEngineResult) -> float:
        """Calculate overall confidence score."""
        scores = []

        if result.scenario:
            # Scenario completeness
            scenario_score = 0.0
            if result.scenario.title:
                scenario_score += 0.2
            if result.scenario.scenes:
                scenario_score += 0.3
            if result.scenario.visual_style:
                scenario_score += 0.2
            if result.scenario.raw_content:
                scenario_score += 0.3
            scores.append(scenario_score)

        if result.translated_prompts:
            # Average prompt quality
            prompt_scores = [p.quality_score for p in result.translated_prompts if p.quality_score > 0]
            if prompt_scores:
                scores.append(sum(prompt_scores) / len(prompt_scores))

        if result.logic_vector_used:
            scores.append(0.9)  # Logic Vector adds confidence

        return sum(scores) / len(scores) if scores else 0.0


# =============================================================================
# Module-level convenience functions
# =============================================================================

_default_service: Optional[StoryEngineService] = None


def get_story_engine_service() -> StoryEngineService:
    """Get or create the default Story Engine service instance."""
    global _default_service
    if _default_service is None:
        _default_service = StoryEngineService()
    return _default_service


async def generate_story(
    concept: str,
    logic_vector: Optional[LogicVector] = None,
    target_platforms: Optional[List[str]] = None,
    generate_shot_list: bool = False,
) -> StoryEngineResult:
    """Convenience function for story generation."""
    service = get_story_engine_service()
    return await service.generate_story(
        concept=concept,
        logic_vector=logic_vector,
        target_platforms=target_platforms,
        generate_shot_list=generate_shot_list,
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "StoryEngineService",
    "StoryEngineResult",
    "StoryScenario",
    "TranslatedPrompt",
    "ShotListItem",
    "StoryEngineComponent",
    "STORY_ENGINE_CREDITS",
    "get_story_engine_service",
    "generate_story",
]
