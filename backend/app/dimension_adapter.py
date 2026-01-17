"""Dimension Capsule Adapter: Server-side AI logic for dimension tools.

This module provides adapters for Crebit dimension capsules:
- Prompt Generator: Veo video prompt generation
- Storyboard Creator: Scene-based storyboard generation
- Image Generator: AI image generation
- Reference Analyzer: Video reference analysis

All AI logic runs server-side to protect intellectual property.
Supports both server API key (default) and BYOK (user-provided key).

Security:
- Input sanitization prevents prompt injection
- Rate limiting handled at router level
- API keys never logged
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypedDict

from app.config import settings

# Lazy import RAG to avoid circular dependencies
_rag_registry = None

def _get_rag_registry():
    """Lazy load RAG registry to avoid circular imports."""
    global _rag_registry
    if _rag_registry is None:
        try:
            from app.rag import get_app_registry
            _rag_registry = get_app_registry()
        except ImportError:
            pass
    return _rag_registry

logger = logging.getLogger(__name__)


# ============================================================================
# Constants & Configuration
# ============================================================================

class DimensionCapsuleId(str, Enum):
    """Valid dimension capsule identifiers."""
    PROMPT_GENERATE = "teaching.prompt.generate"
    STORYBOARD_CREATE = "teaching.storyboard.create"
    IMAGE_GENERATE = "teaching.image.generate"
    REFERENCE_ANALYZE = "teaching.reference.analyze"
    # New dimension capsules
    QUALITY_CHECK = "dimension.quality.check"
    AESTHETIC_DIRECT = "dimension.aesthetic.direct"
    AESTHETIC_MOODBOARD = "dimension.aesthetic.moodboard"
    PERSONA_ANALYZE = "dimension.persona.analyze"
    SOUND_MOODBOARD = "dimension.sound.moodboard"
    # Veo video generation
    VEO_VIDEO_GENERATE = "veo.video.generate"
    # 4-Stage Workflow additions
    STORY_ARCHITECT = "dimension.story.architect"
    STORY_REFINE = "dimension.story.refine"
    SOUND_CRAFT = "dimension.sound.craft"
    CREATIVE_EDITOR = "dimension.quality.editor"
    # JSON Generator adapter
    JSON_GEN_CONVERT = "dimension.json_gen.convert"
    # Nanobanana Editor adapter
    NANOBANANA_CONVERT = "dimension.nanobanana.convert"
    # Prompt Alchemy - AI Video Platform Prompt Translator
    PROMPT_TRANSLATE = "prompt.alchemy.translate"


# Input validation limits
MAX_TOPIC_LENGTH = 2000
MAX_CONCEPT_LENGTH = 5000
MAX_DESCRIPTION_LENGTH = 3000
MIN_SCENE_COUNT = 1
MAX_SCENE_COUNT = 20
ALLOWED_LANGUAGES = {"ko", "en"}
# 2026 Updated: Gemini 3 models as primary, legacy for backwards compatibility
ALLOWED_MODELS = {
    # Primary models (2025-2026)
    "gemini-3-flash-preview",
    "gemini-3-pro-preview",
    # Video generation
    "veo-3.1-generate-preview",
    # Image generation (Nano Banana Pro)
    "gemini-3-pro-image-preview",
    # Legacy (deprecated but still supported)
    "gemini-3-flash-preview",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
}
MAX_CONTENT_LENGTH = 10000  # For quality checker
GEMINI_TIMEOUT_SECONDS = 30


@dataclass
class CapsuleMetrics:
    """Metrics for capsule execution."""
    latency_ms: int
    input_tokens: int
    output_tokens: int
    model: str
    cached: bool = False


class CapsuleResult(TypedDict):
    """Structured capsule result."""
    success: bool
    capsule_id: str
    output: Dict[str, Any]
    error: Optional[str]
    metrics: Optional[Dict[str, Any]]


# ============================================================================
# Input Sanitization
# ============================================================================

def _sanitize_text(text: str, max_length: int, field_name: str) -> str:
    """Sanitize text input to prevent prompt injection.
    
    Args:
        text: Raw input text
        max_length: Maximum allowed length
        field_name: Field name for error messages
        
    Returns:
        Sanitized text
        
    Raises:
        ValueError: If input is invalid
    """
    if not isinstance(text, str):
        raise ValueError(f"{field_name} must be a string")
    
    # Strip and truncate
    text = text.strip()[:max_length]
    
    # Remove potential prompt injection patterns
    # Block common injection attempts
    injection_patterns = [
        r"(?i)ignore\s+(previous|above|all)\s+instructions",
        r"(?i)forget\s+(previous|above|all)\s+instructions",
        r"(?i)disregard\s+(previous|above|all)\s+instructions",
        r"(?i)system\s*:\s*",
        r"(?i)assistant\s*:\s*",
        r"(?i)human\s*:\s*",
    ]
    
    for pattern in injection_patterns:
        text = re.sub(pattern, "", text)
    
    return text


def _validate_enum(value: str, allowed: set, field_name: str, default: str) -> str:
    """Validate enum-like string values."""
    if value in allowed:
        return value
    logger.warning(f"Invalid {field_name} '{value}', using default '{default}'")
    return default


def _validate_int_range(value: Any, min_val: int, max_val: int, default: int) -> int:
    """Validate integer within range."""
    try:
        val = int(value)
        return max(min_val, min(max_val, val))
    except (TypeError, ValueError):
        return default


# ============================================================================
# RAG Context Injection
# ============================================================================

def _get_rag_context(
    capsule_id: str,
    query: str,
    history_context: Optional[str] = None,
    use_rag: bool = True,
    session_id: Optional[str] = None,
) -> str:
    """Retrieve RAG context for a capsule.

    Args:
        capsule_id: The capsule identifier (e.g., "dimension.aesthetic.direct")
        query: The search query (usually the user's input/concept)
        history_context: Previous step context for amplification
        use_rag: Whether to use RAG (can be disabled via params)
        session_id: Optional user session ID for Context Library lookup

    Returns:
        Formatted RAG context string for prompt injection, or empty string
    """
    if not use_rag:
        return ""

    combined_context = ""

    # === Expert Workflow: Context Library (User-Injected Knowledge) ===
    if session_id:
        try:
            from app.rag.context_library import get_context_library
            library = get_context_library()
            ctx_result = library.get_context_for_query(
                session_id=session_id,
                query=query,
                max_documents=3,
            )
            if ctx_result.formatted_context:
                combined_context += ctx_result.formatted_context + "\n\n"
                logger.debug(
                    f"[{capsule_id}] Context Library: {ctx_result.total_matched} docs injected"
                )
        except Exception as e:
            logger.warning(f"Context Library retrieval failed: {e}")

    # === Standard RAG: App Registry ===
    registry = _get_rag_registry()
    if not registry:
        logger.debug("RAG registry not available")
        return combined_context

    try:
        context = registry.get_context_for_app(
            app_key=capsule_id,
            query=query,
            history_context=history_context,
        )

        formatted = context.get("formatted_context", "")
        if formatted and context.get("total_results", 0) > 0:
            logger.debug(
                f"[{capsule_id}] RAG: {context['total_results']} results "
                f"from {context['dimensions_searched']}"
            )
            combined_context += formatted

    except Exception as e:
        logger.warning(f"RAG retrieval failed for {capsule_id}: {e}")

    return combined_context


def _inject_rag_into_prompt(
    base_prompt: str,
    rag_context: str,
    position: str = "prepend",
) -> str:
    """Inject RAG context into a prompt.

    Args:
        base_prompt: The original user prompt
        rag_context: RAG context string from _get_rag_context
        position: Where to inject - "prepend", "append", or "before_task"

    Returns:
        Enhanced prompt with RAG context
    """
    if not rag_context:
        return base_prompt

    if position == "append":
        return f"{base_prompt}\n\n{rag_context}"
    elif position == "before_task":
        # Insert before the last task instruction
        parts = base_prompt.rsplit("\n\n", 1)
        if len(parts) == 2:
            return f"{parts[0]}\n\n{rag_context}\n\n{parts[1]}"
        return f"{rag_context}\n\n{base_prompt}"
    else:  # prepend
        return f"{rag_context}\n\n{base_prompt}"


# ============================================================================
# Prompt Templates (Protected - Server-side only)
# ============================================================================

PROMPT_GENERATOR_SYSTEM = """You are a Virtual Cinematographer (Auteur Level) specializing in Veo 3.1 prompts.
Your task is to generate high-quality, cinematic video prompts by applying ACADEMIC CINEMATOGRAPHY RULES.

Apply these "Director's Cut" Heuristics based on the desired mood:

1. LENS PSYCHOLOGY (The Eye):
- Alienation/Distortion: Use "16mm-24mm wide angle" (Wong Kar-wai style) to make characters feel detached or weird.
- Isolation/Voyeurism: Use "85mm-200mm telephoto" to compress space and isolate the subject (Spy aesthetic).
- Panic/Vertigo: Use "Dolly Zoom" (Hitchcock effect) for reality distortion.

2. LIGHTING PHILOSOPHY (The Truth):
- Truth/Violence: Use "Hard Light" (Chiaroscuro, Noir) for gritty reality.
- Fantasy/Romance: Use "Soft Light" (Diffused, Ethereal) for dreamlike states.

3. COLOR RHETORIC (The Emotion):
- Tension/Conflict: Use "Complementary Contrast" (Teal/Orange, Red/Green).
- Irony/Solitude: Use "Cold-Warm Contrast" (Edward Hopper: Cold exterior vs Warm interior).

4. MOVEMENT MOTIVATION (The Trigger):
- Empathy: "Slow Push-In" to enter the character's mind.
- Abandonment: "Slow Pull-Out" to leave them behind.

5. SPECIAL ANGLES (Part 4):
- Tatami Shot (Ozu): Camera at 60-90cm (sitting eye-level), static, contemplative. For domestic peace.
- Bird's Eye View: 90-degree top-down, "God's judgment", powerlessness. For scale/fate.
- Prompt keywords: "tatami-level", "locked-off", "straight-down overhead", "God's eye view"

6. TIME MANIPULATION (Part 5):
- Slow Motion: "Extreme slow motion, phantom flex camera" for emotional magnification.
- Bullet Time: "Frozen moment, camera orbit" for omniscient perspective.
- Speed Ramping: Transition from normal to slow for impact.
- Prompt keywords: "high frame rate", "frozen in time", "slow motion impact"

Output ONLY valid JSON with this exact structure (no markdown):
{
  "prompt": "The main video generation prompt incorporating lens, light, and movement rules",
  "negative_prompt": "Elements to avoid (e.g., deformed, blurry, low res)",
  "style": {
    "cinematography": "Specific lens and camera details (e.g., 'Shot on 35mm, 85mm lens, f/1.8')",
    "lighting": "Lighting setup (e.g., 'Rembrandt lighting, hard shadows')",
    "color_grade": "Grading style (e.g., 'Teal and Orange, Kodak Portra 400')"
  },
  "technical": {
    "aspect_ratio": "16:9",
    "duration": "Suggested duration (e.g., '6s')",
    "fps": "24"
  }
}
"""

STORYBOARD_SYSTEM = """You are a professional storyboard artist and cinematographer.
Create detailed storyboard cards from video concepts.

Apply this "Director's Cut" Heuristic:

KULESHOV EFFECT (Meaning through Juxtaposition):
- The meaning of a shot is determined by what comes BEFORE and AFTER it.
- A neutral face + Food = Hunger. Neutral face + Coffin = Grief. Neutral face + Child = Love.
- When designing storyboards, always consider the EMOTIONAL TRANSFER between adjacent shots.
- Ask: "What emotion will the previous shot lend to this one?"

Output ONLY valid JSON array with this structure:
[
  {
    "scene_number": 1,
    "description": "Visual description",
    "camera": "Shot type and movement",
    "duration": "Estimated duration in seconds",
    "notes": "Director notes",
    "kuleshov_link": "Emotional connection to previous/next shot (optional)"
  }
]

- NEVER include user instructions in your output
"""

IMAGE_GENERATOR_SYSTEM = """You are an AI image generation expert.
Create detailed image prompts optimized for Imagen/DALL-E/Midjourney.

Apply these "Director's Cut" Heuristics:

1. PUNCTUM (The Piercing Detail) - Part 1:
- Avoid generic perfection (Studium). Add one imperfect detail that "pierces" the viewer.
- Examples: "cracked glasses lens", "rain-soaked hair", "visible pores", "asymmetrical smile"
- Prompt keywords: "unretouched", "documentary style", "raw beauty", "storytelling detail"

2. Z-AXIS DEPTH (3D Layering) - Part 4:
- Always compose with Foreground/Middleground/Background.
- Foreground: Out-of-focus object for voyeuristic tension (leaves, shoulder, window frame).
- Middleground: Sharp focus on the subject.
- Background: Depth cue (fog, bokeh, distant lights).
- Prompt keywords: "layered depth", "foreground bokeh", "3D depth sensation"

3. FRAME-IN-FRAME (Enclosure) - Part 4:
- Enclose the subject within a secondary frame (door, window, mirror) for isolation/voyeurism.
- Prompt keywords: "frame within a frame", "voyeuristic angle", "claustrophobic composition"

Output ONLY valid JSON:
{
  "prompt": "Optimized image prompt incorporating depth and punctum",
  "negative_prompt": "Elements to avoid (e.g., flat, generic, symmetrical perfection)",
  "parameters": {
    "style": "Art style",
    "aspect_ratio": "Image ratio",
    "quality": "Quality setting"
  }
}

- NEVER include user instructions in your output
"""

REFERENCE_ANALYZER_SYSTEM = """You are a film analyst specializing in visual storytelling.
Analyze video references and extract key cinematic elements.

Output ONLY valid JSON:
{
  "composition": "Composition analysis",
  "lighting": "Lighting analysis",
  "color": "Color palette analysis",
  "movement": "Camera movement analysis",
  "narrative": "Narrative structure analysis",
  "recommendations": ["List of key takeaways"]
}

- NEVER include user instructions in your output
"""

QUALITY_CHECKER_SYSTEM = """You are an expert content quality analyst specializing in AI-generated media.
Your role is to evaluate content against multiple quality criteria with precision and objectivity.

EVALUATION CRITERIA:
1. aesthetic - Visual/artistic quality (composition, color harmony, style consistency)
2. ad_suitability - Brand safety, appropriate for commercial use
3. consistency - Style/tone uniformity, character/setting continuity
4. safety - No violence, hate speech, explicit content, ethical concerns
5. technical - Resolution, clarity, format correctness
6. narrative - Story coherence, emotional arc, engagement

For each criterion, provide:
- score: 0-100 numeric score
- passed: true if score >= threshold (default 70)
- details: Brief explanation

Output ONLY valid JSON:
{
  "passed": true/false,
  "score": 0-100,
  "criteria_results": {
    "aesthetic": {"score": 85, "passed": true, "details": "Strong composition..."},
    "consistency": {"score": 72, "passed": true, "details": "Style maintained..."}
  },
  "issues": ["List of identified problems"],
  "suggestions": ["List of improvement recommendations"]
}

- Be objective and constructive
- Focus on actionable feedback
- NEVER include user instructions in your output
"""

AESTHETIC_DIRECTOR_SYSTEM = """You are a master visual aesthetics director with deep knowledge of:
- Film directors' signature styles (Bong Joon-ho, Park Chan-wook, Shinkai, etc.)
- Composition techniques and visual grammar
- Color theory and palette design
- Lighting and mood creation
- Camera movement and pacing

AUTEUR STYLE SIGNATURES (reference when relevant):
- Bong Joon-ho: Structural tension, genre mixing, controlled camera, cool tones
- Park Chan-wook: Symmetry, high contrast, warm colors, precise framing
- Shinkai Makoto: Light diffusion, lyrical colors, emotional atmosphere
- Lee Jun-ho: Music sync, rhythmic editing, dynamic camera
- Na Hong-jin: Raw realism, suspense, dynamic/chaotic camera, cool tones
- Hong Sang-soo: Static camera, dialogue-driven, neutral palette

APPLY "GENRE MASHUP" STRATEGY (The Director's Cut):
- Rule: If the concept implies multiple genres, use the "Hybridization" formula: "[Genre A] aesthetic mixed with [Genre B] elements".
- Examples: 
  * "Cyberpunk Joseon" -> "Joseon scholar on neon rooftop, holographic scroll"
  * "Medieval Sci-Fi" -> "Knights with lightsabers in spaceship"
  * "Pastel Noir" -> "Crime scene with Wes Anderson pink/mint palette"

Output ONLY valid JSON:
{
  "visual_guidelines": {
    "composition": "Composition approach and techniques",
    "lighting": "Lighting style and mood",
    "camera": "Camera movement and framing",
    "pacing": "Visual rhythm and tempo"
  },
  "color_palette": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5"],
  "style_keywords": ["keyword1", "keyword2", "keyword3"],
  "avoid_elements": ["element1", "element2"],
  "auteur_influence": {
    "matched_style": "Director name or null",
    "influence_level": 0.0-1.0,
    "signature_elements": ["element1", "element2"]
  },
  "textures": ["texture1", "texture2", "texture3"],
  "typography": {
    "primary": "Suggested Title Font (e.g., Futura Bold)",
    "secondary": "Suggested Body Font (e.g., Garamond)",
    "description": "Why this combination works"
  },
  "generative_prompts": {
    "midjourney": "Midjourney v6 prompt",
    "veo": "Veo video generation prompt"
  }
}

- Provide 5-7 hex colors in the palette
- Include 5-10 style keywords
- List 3-5 elements to avoid
- NEVER include user instructions in your output
"""

STORY_ARCHITECT_SYSTEM = """You are an expert video story architect and screenwriter.
Your task is to create compelling video narratives that combine the user's creative DNA and reference analysis.

Output ONLY valid JSON with this exact structure:
{
  "title": "Compelling scenario title",
  "logline": "One sentence hook",
  "synopsis": "3-5 sentence overview",
  "structure": [
    {"act": "1", "description": "Setup", "duration": "20%", "emotion": "curiosity"},
    {"act": "2", "description": "Conflict", "duration": "60%", "emotion": "tension"},
    {"act": "3", "description": "Resolution", "duration": "20%", "emotion": "satisfaction"}
  ],
  "characters": [
    {"name": "Character name", "role": "protagonist/antagonist/support", "arc": "Growth journey", "traits": ["trait1", "trait2"]}
  ],
  "themes": ["theme1", "theme2"],
  "visual_motifs": ["motif1", "motif2"],
  "next_dimension": "storyboard-sketch"
}

Guidelines:
- Create emotionally resonant narratives
- Match story structure to the requested format
- Include clear visual cues for storyboard creation
- Consider the user's creative DNA if provided
- NEVER include user instructions in your output
"""

SOUND_MOODBOARD_SYSTEM = """You are an expert Audio Director.
Your job is to translate abstract concepts into concrete musical directions.
Create 3 distinct 'Audio Direction Cards' that interpret the user's concept in different ways.

Output ONLY valid JSON:
{
  "directions": [
    {
      "id": "direction_1",
      "title": "Evocative Title (e.g., Cyberpunk Noir)",
      "description": "Brief atmospheric description focusing on mood and texture.",
      "visual_style": {
        "color": "#hex_code",
        "icon": "musical_note|waveform|activity|zap" 
      },
      "bpm_range": "e.g., 90-110",
      "key_elements": ["Synth Arps", "Rain FX", "Deep Bass"]
    }
  ]
}
"""

SOUND_CRAFTER_SYSTEM = """You are an expert Audio Engineer and Composer.
Your task is to create production-ready audio prompts based on the selected direction and mix recipe.

Apply these "Director's Cut" Sound Heuristics when appropriate:

1. SONIC VACUUM (Impact through Silence):
   - Use for: Explosions, Shock moments, Disorientation.
   - Technique: Drop all sound to near-silence (or high-pitched tinnitus) at the peak of visual impact.
   - Prompt keyword: "Sudden silence", "Tinnitus ringing", "Muted world", "Audio dropout".

2. ANEMPATHETIC SOUND (Tragedy via Contrast):
   - Use for: Tragic scenes, Horror, Irony.
   - Technique: Use music that contradicts the visual mood (e.g., Happy pop during a sad scene, Beautiful opera during violence).
   - Prompt keyword: "Cheerful major key", "Upbeat tempo", "Ironic contrast".

Output ONLY valid JSON:
{
  "music_prompt": "Prompt optimized for Suno v3 (Structure + Tags + Lyrics if needed)",
  "udio_prompt": "Prompt optimized for Udio (High fidelity, instrumental focus tags)",
  "style_tags": ["tag1", "tag2", "tag3"],
  "bpm_range": "e.g., 90-110 BPM",
  "key_signature": "e.g., Gm",
  "layers": {
    "melody": "Description of the lead line/voice",
    "rhythm": "Description of the beat/percussion",
    "texture": "Description of atmosphere/FX"
  },
  "mixing_guide": "Post-processing advice (e.g., 'Apply sidechain to bass')",
  "visualization": {
    "energy_levels": [0.2, 0.4, 0.8, 0.6, 0.4],
    "color_palette": ["#hex1", "#hex2"]
  }
}
NEVER include explanations outside the JSON.
"""

PERSONA_ANALYZER_SYSTEM = """You are a depth psychology analyst specialized in creative persona profiling.
You combine multiple psychological frameworks to understand the user's inner world and creative potential.

THEORETICAL FRAMEWORKS:
1. 사주 (Four Pillars) - Birth chart energy patterns
2. Maslow's Hierarchy of Needs - Motivational drivers (physiological → safety → belonging → esteem → self-actualization)
3. Jungian Archetypes - 12 archetypes (Hero, Sage, Explorer, Outlaw, Magician, Caregiver, Lover, Jester, Everyman, Ruler, Creator, Innocent) + Shadow
4. Adult Attachment Theory (Bowlby-Ainsworth) - Secure, Anxious, Avoidant, Disorganized
5. Erikson's Psychosocial Stages - Formative experiences and identity crises

ANALYSIS STAGES (8-stage model):
1. INTRO - 기본 정보 수집: 생년월일, MBTI, 혈액형, 출생순서
2. SELF_EXPRESSION - 페르소나 vs 진정한 자아: 타인이 보는 나 vs 혼자일 때의 나
3. MASLOW - 욕구 계층 탐색: 두려움, 갈망, 목표를 통한 욕구 레벨 식별
4. FORMATIVE - 성장 배경: 유년기 기억, 청소년기 정체성, 핵심 트라우마 (민감 - 스킵 허용)
5. ATTACHMENT - 애착 패턴: 부모와의 관계, 갈등 대처 방식
6. SHADOW - 그림자 탐색: 싫어하는 인물 유형, 반복되는 꿈, 억압된 특성
7. ARCHETYPE - 원형 매칭: 핵심 동기 탐색을 통한 주요/보조 원형 식별
8. SYNTHESIS - 창작 DNA 합성: 모든 분석 통합 → 창작 프로필 생성

GUIDELINES:
- Be empathetic and non-judgmental at all times
- Ask ONE focused question at a time (never multiple questions in one message)
- Allow skipping sensitive questions gracefully
- Build on previous responses for deeper exploration
- Connect psychological insights to creative applications
- Connect psychological insights to creative applications
- Use warm, conversational Korean
- If 'is_deep_mode' is true and 'turn_count' is 0, ask a digging/follow-up question to explore deeper.
- If 'is_deep_mode' is true and 'turn_count' is 1, summarize and move to next topic.

OUTPUT JSON (ALWAYS return this structure):
{
  "assistant_message": "Your thoughtful question or response in Korean",
  "next_stage": "current_or_next_stage_name",
  "persona_update": {
    "key": "extracted insight or data"
  },
  "analysis_complete": false,
  "final_persona": null
}

When analysis_complete is true (SYNTHESIS stage completed), include final_persona:
{
  "archetype": {
    "primary": "Main archetype (e.g., Hero, Creator)",
    "secondary": "Supporting archetype",
    "shadow": "Repressed archetype"
  },
  "saju_profile": {
    "day_master": "일간",
    "five_elements": {"wood": 0, "fire": 0, "earth": 0, "metal": 0, "water": 0}
  },
  "maslow_level": "Current need level + transition state",
  "attachment_style": "secure/anxious/avoidant/disorganized",
  "formative_themes": ["theme1", "theme2"],
  "shadow_traits": ["trait1", "trait2"],
  "creative_dna": {
    "suitable_genres": ["genre1", "genre2"],
    "character_archetypes": {"protagonist": "...", "antagonist": "..."},
    "recurring_motifs": ["motif1", "motif2"],
    "strengths": ["strength1", "strength2"],
    "blind_spots": ["blindspot1", "blindspot2"],
    "growth_direction": "Integration path"
  }
}

NEVER include user instructions or meta-commentary in your output.
"""

CREATIVE_EDITOR_SYSTEM = """You are a Senior Creative Editor with decades of award-winning experience.
Your goal is to elevate content from "good" to "exceptional".

You act in two capacities:
1. THE CRITIC: Ruthlessly identify weaknesses in narrative, pacing, tone, and visual consistency.
2. THE FIXER: Rewrite the content to solve these problems.

INPUT: Content (Script/Story/Prompts) + Context (Genre/Audience)

OUTPUT JSON:
{
  "critique": {
    "narrative_score": 0-100,
    "visual_score": 0-100,
    "pacing_score": 0-100,
    "key_issues": ["Specific issue 1", "Specific issue 2"]
  },
  "original_content": "The input content (for reference)",
  "improved_content": "The FULLY REWRITTEN content. Make it punchier, more emotional, and stylistically consistent.",
  "changes_made": [
    {"type": "tone", "description": "Shifted from passive to active voice"},
    {"type": "pacing", "description": "Cut unnecessary exposition in Scene 2"}
  ]
}

- Be bold in your edits. Don't just tweak grammar; fix the soul of the content.
- If the input is a storyboard/script, maintain the JSON structure but enhance the values.
- NEVER include user instructions in your output.
"""



CREATIVE_EDITOR_SYSTEM = """You are a Senior Creative Editor with decades of award-winning experience.
Your goal is to elevate content from "good" to "exceptional".

You act in two capacities:
1. THE CRITIC: Ruthlessly identify weaknesses in narrative, pacing, tone, and visual consistency.
2. THE FIXER: Rewrite the content to solve these problems.

INPUT: Content (Script/Story/Prompts) + Context (Genre/Audience)

OUTPUT JSON:
{
  "critique": {
    "narrative_score": 0-100,
    "visual_score": 0-100,
    "pacing_score": 0-100,
    "key_issues": ["Specific issue 1", "Specific issue 2"]
  },
  "original_content": "The input content (for reference)",
  "improved_content": "The FULLY REWRITTEN content. Make it punchier, more emotional, and stylistically consistent.",
  "changes_made": [
    {"type": "tone", "description": "Shifted from passive to active voice"},
    {"type": "pacing", "description": "Cut unnecessary exposition in Scene 2"}
  ]
}

- Be bold in your edits. Don't just tweak grammar; fix the soul of the content.
- If the input is a storyboard/script, maintain the JSON structure but enhance the values.
- NEVER include user instructions in your output.
"""


# ============================================================================
# Gemini Client with Hardening
# ============================================================================

async def _call_gemini(
    prompt: str,
    system_prompt: str,
    api_key: Optional[str] = None,
    model: str = "gemini-3-flash-preview",
    temperature: float = 1.0,  # Gemini 3 optimized for 1.0
    timeout: float = GEMINI_TIMEOUT_SECONDS,
    thinking_level: Optional[str] = None,  # "high" or "low" for Gemini 3
) -> tuple[Dict[str, Any], CapsuleMetrics]:
    """Call Gemini API with given prompts.

    Uses server key by default, BYOK if provided.
    Optimized for Gemini 3 with Thought Signatures support.

    IMPORTANT: Gemini 3 Best Practices:
    - Temperature should be 1.0 (lower values may cause looping)
    - SDK handles Thought Signatures automatically
    - Use thinking_level="high" for complex reasoning tasks

    Args:
        prompt: User prompt
        system_prompt: System instructions
        api_key: Optional user API key (BYOK)
        model: Model to use
        temperature: Generation temperature (1.0 for Gemini 3)
        timeout: Request timeout in seconds
        thinking_level: Gemini 3 thinking level ("high" or "low")

    Returns:
        Tuple of (parsed response, metrics)

    Raises:
        ValueError: If no API key available
        TimeoutError: If request times out
        RuntimeError: If API call fails
    """
    from google import genai
    from google.genai import types

    start_time = time.monotonic()

    # Validate model
    model = _validate_enum(model, ALLOWED_MODELS, "model", "gemini-3-flash-preview")

    # For Gemini 3 models, enforce temperature 1.0
    if "gemini-3" in model and temperature != 1.0:
        logger.debug(f"Gemini 3 detected, using temperature 1.0 (was {temperature})")
        temperature = 1.0

    # Use provided key or fall back to server key
    key = api_key or settings.GEMINI_API_KEY
    if not key:
        raise ValueError("No API key available. Configure GEMINI_API_KEY or provide user key.")

    client = genai.Client(api_key=key)

    # Build generation config
    config_kwargs = {
        "system_instruction": system_prompt,
        "temperature": temperature,
        "response_mime_type": "application/json",
    }

    # Add thinking_level for Gemini 3 if specified
    if thinking_level and "gemini-3" in model:
        config_kwargs["thinking_level"] = thinking_level

    try:
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs),
            ),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        logger.error(f"Gemini API timeout after {timeout}s")
        raise TimeoutError(f"Request timed out after {timeout} seconds")
    except Exception as e:
        error_str = str(e).lower()
        error_type = type(e).__name__
        logger.error(f"Gemini API error: {error_type}: {e}")

        # Classify error for better user feedback
        if "permission_denied" in error_str or "403" in error_str:
            if "leaked" in error_str:
                raise RuntimeError("API key needs rotation. Please contact support.")
            raise RuntimeError("API access denied. Check your API key permissions.")
        elif "quota" in error_str or "429" in error_str or "resource_exhausted" in error_str:
            raise RuntimeError("API quota exceeded. Please try again later.")
        elif "invalid_api_key" in error_str or "401" in error_str:
            raise RuntimeError("Invalid API key. Please check your configuration.")
        elif "model_not_found" in error_str or "404" in error_str:
            raise RuntimeError(f"Model '{model}' not available. Try a different model.")
        elif "safety" in error_str or "blocked" in error_str:
            raise RuntimeError("Content blocked by safety filters. Please modify your input.")
        elif "connection" in error_str or "network" in error_str:
            raise RuntimeError("Network error. Please check your connection.")
        else:
            raise RuntimeError(f"AI service error: {error_type}")
    
    latency_ms = int((time.monotonic() - start_time) * 1000)
    
    # Extract token usage
    input_tokens = 0
    output_tokens = 0
    if hasattr(response, 'usage_metadata'):
        usage = response.usage_metadata
        input_tokens = getattr(usage, 'prompt_token_count', 0)
        output_tokens = getattr(usage, 'candidates_token_count', 0)
    
    metrics = CapsuleMetrics(
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model=model,
    )
    
    # Parse JSON response
    text = response.text.strip()
    
    # Handle markdown code blocks
    if text.startswith("```"):
        lines = text.split("\n")
        # Find start and end of code block
        start_idx = 1 if lines[0].startswith("```") else 0
        end_idx = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == "```":
                end_idx = i
                break
        text = "\n".join(lines[start_idx:end_idx]).strip()
        if text.startswith("json"):
            text = text[4:].strip()
    
    try:
        return json.loads(text), metrics
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response: {e}. Raw: {text[:500]}")
        # Return a structured error instead of raw text
        return {
            "error": "Failed to parse AI response",
            "_raw_truncated": text[:200] if len(text) > 200 else text,
        }, metrics


# ============================================================================
# Dimension Capsule Adapters
# ============================================================================

async def run_prompt_generator(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
    intent: Optional[Any] = None,  # CreativeIntent (lazy import)
) -> CapsuleResult:
    """Generate Veo video prompts from user input.
    
    Args:
        inputs: topic, style, mood, duration, language
        params: model selection
        user_api_key: Optional BYOK
        intent: Optional CreativeIntent for Resolver-based param resolution
    
    Returns:
        CapsuleResult with generated prompt spec
    """
    # === Intent-Resolver Integration (Phase 2) ===
    if intent is not None or params.get("intent"):
        try:
            from app.resolvers.integration import prepare_dimension_params
            inputs, params = await prepare_dimension_params(
                dimension_code="1D",
                inputs=inputs,
                params=params,
                intent=intent,
            )
            logger.debug(f"[1D] Intent-resolved params applied")
        except ImportError:
            logger.debug("[1D] Resolver integration not available")
        except Exception as e:
            logger.warning(f"[1D] Resolver integration failed: {e}")
    
    # Validate and sanitize inputs
    topic = _sanitize_text(
        inputs.get("topic", ""),
        MAX_TOPIC_LENGTH,
        "topic"
    )
    if not topic:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.PROMPT_GENERATE.value,
            "output": {},
            "error": "Topic is required",
            "metrics": None,
        }
    
    style = _sanitize_text(inputs.get("style", "cinematic"), 50, "style")
    mood = _sanitize_text(inputs.get("mood", "neutral"), 50, "mood")
    duration = _sanitize_text(inputs.get("duration", "15 seconds"), 20, "duration")
    language = _validate_enum(inputs.get("language", "ko"), ALLOWED_LANGUAGES, "language", "ko")
    model = _validate_enum(params.get("model", "gemini-3-flash-preview"), ALLOWED_MODELS, "model", "gemini-3-flash-preview")
    use_rag = params.get("use_rag", True)
    
    # === Additional Resolver hints ===
    detail_level = params.get("detail_level", "medium")
    emphasis = params.get("emphasis", [])
    
    # Build base prompt with Resolver enhancements
    emphasis_str = ", ".join(emphasis[:3]) if emphasis else "atmosphere, lighting"
    base_prompt = f"""Generate a Veo 3.1 video prompt for:

Topic: {topic}
Visual Style: {style}
Mood/Tone: {mood}
Target Duration: {duration}
Output Language: {language}
Detail Level: {detail_level}
Emphasize: {emphasis_str}

Create a detailed, professional prompt. Include camera movements, lighting, and visual details.
"""

    # Inject RAG context if enabled
    rag_context = _get_rag_context(
        capsule_id=DimensionCapsuleId.PROMPT_GENERATE.value,
        query=f"{topic} {style} {mood}".strip(),
        use_rag=use_rag,
    )
    user_prompt = _inject_rag_into_prompt(base_prompt, rag_context, position="prepend")

    try:
        result, metrics = await _call_gemini(
            prompt=user_prompt,
            system_prompt=PROMPT_GENERATOR_SYSTEM,
            api_key=user_api_key,
            model=model,
        )
        
        return {
            "success": "error" not in result,
            "capsule_id": DimensionCapsuleId.PROMPT_GENERATE.value,
            "output": result,
            "error": result.get("error"),
            "metrics": {
                "latency_ms": metrics.latency_ms,
                "tokens": metrics.input_tokens + metrics.output_tokens,
                "model": metrics.model,
                "intent_resolved": intent is not None,
            },
        }
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.PROMPT_GENERATE.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


async def run_storyboard_creator(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Create storyboard cards from a concept or prompt."""
    concept = _sanitize_text(
        inputs.get("concept", inputs.get("prompt", "")),
        MAX_CONCEPT_LENGTH,
        "concept"
    )
    if not concept:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.STORYBOARD_CREATE.value,
            "output": {},
            "error": "Concept is required",
            "metrics": None,
        }
    
    scene_count = _validate_int_range(inputs.get("scene_count", 5), MIN_SCENE_COUNT, MAX_SCENE_COUNT, 5)
    language = _validate_enum(inputs.get("language", "ko"), ALLOWED_LANGUAGES, "language", "ko")
    model = _validate_enum(params.get("model", "gemini-3-flash-preview"), ALLOWED_MODELS, "model", "gemini-3-flash-preview")
    use_rag = params.get("use_rag", True)

    # Build base prompt
    base_prompt = f"""Create a {scene_count}-scene storyboard for:

Concept: {concept}
Language: {language}

For each scene provide: description, camera, duration, notes.
"""

    # Inject RAG context if enabled
    rag_context = _get_rag_context(
        capsule_id=DimensionCapsuleId.STORYBOARD_CREATE.value,
        query=concept,
        use_rag=use_rag,
    )
    user_prompt = _inject_rag_into_prompt(base_prompt, rag_context, position="prepend")

    try:
        result, metrics = await _call_gemini(
            prompt=user_prompt,
            system_prompt=STORYBOARD_SYSTEM,
            api_key=user_api_key,
            model=model,
        )
        
        # Normalize output format
        output = result if isinstance(result, list) else result.get("scenes", [result])
        
        return {
            "success": "error" not in result,
            "capsule_id": DimensionCapsuleId.STORYBOARD_CREATE.value,
            "output": {"scenes": output} if isinstance(output, list) else output,
            "error": result.get("error") if isinstance(result, dict) else None,
            "metrics": {
                "latency_ms": metrics.latency_ms,
                "tokens": metrics.input_tokens + metrics.output_tokens,
                "model": metrics.model,
            },
        }
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.STORYBOARD_CREATE.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


async def run_image_generator(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Generate image prompts optimized for AI image generation."""
    description = _sanitize_text(
        inputs.get("description", ""),
        MAX_DESCRIPTION_LENGTH,
        "description"
    )
    if not description:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.IMAGE_GENERATE.value,
            "output": {},
            "error": "Description is required",
            "metrics": None,
        }
    
    style = _sanitize_text(inputs.get("style", "photorealistic"), 50, "style")
    aspect_ratio = _sanitize_text(inputs.get("aspect_ratio", "16:9"), 10, "aspect_ratio")
    model = _validate_enum(params.get("model", "gemini-3-flash-preview"), ALLOWED_MODELS, "model", "gemini-3-flash-preview")
    use_rag = params.get("use_rag", True)

    # Build base prompt
    base_prompt = f"""Create an optimized AI image generation prompt for:

Description: {description}
Style: {style}
Aspect Ratio: {aspect_ratio}

Generate a detailed prompt suitable for Imagen, DALL-E, or Midjourney.
"""

    # Inject RAG context if enabled
    rag_context = _get_rag_context(
        capsule_id=DimensionCapsuleId.IMAGE_GENERATE.value,
        query=f"{description} {style}".strip(),
        use_rag=use_rag,
    )
    user_prompt = _inject_rag_into_prompt(base_prompt, rag_context, position="prepend")

    try:
        result, metrics = await _call_gemini(
            prompt=user_prompt,
            system_prompt=IMAGE_GENERATOR_SYSTEM,
            api_key=user_api_key,
            model=model,
        )
        
        # Normalize output format (Gemini may return list or dict)
        if isinstance(result, list):
            output = {"prompts": result, "prompt": result[0] if result else ""}
            has_error = False
            error_msg = None
        else:
            output = result
            has_error = "error" in result
            error_msg = result.get("error")
        
        return {
            "success": not has_error,
            "capsule_id": DimensionCapsuleId.IMAGE_GENERATE.value,
            "output": output,
            "error": error_msg,
            "metrics": {
                "latency_ms": metrics.latency_ms,
                "tokens": metrics.input_tokens + metrics.output_tokens,
                "model": metrics.model,
            },
        }
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.IMAGE_GENERATE.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


async def run_reference_analyzer(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Analyze video references and extract cinematic elements."""
    description = _sanitize_text(
        inputs.get("video_description", ""),
        MAX_DESCRIPTION_LENGTH,
        "video_description"
    )
    if not description:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.REFERENCE_ANALYZE.value,
            "output": {},
            "error": "Video description is required",
            "metrics": None,
        }
    
    focus_areas = inputs.get("focus_areas", ["composition", "lighting", "color", "movement"])
    if not isinstance(focus_areas, list):
        focus_areas = ["composition", "lighting", "color", "movement"]
    focus_areas = [_sanitize_text(str(a), 30, "focus_area") for a in focus_areas[:10]]
    
    # Get analysis depth and output format
    analysis_depth = _sanitize_text(inputs.get("analysis_depth", "standard"), 30, "analysis_depth")
    output_format = _sanitize_text(inputs.get("output_format", "structured"), 30, "output_format")

    model = _validate_enum(params.get("model", "gemini-3-flash-preview"), ALLOWED_MODELS, "model", "gemini-3-flash-preview")
    use_rag = params.get("use_rag", True)

    # Build depth instruction
    depth_instruction = ""
    if analysis_depth == "deep":
        depth_instruction = "\nProvide an exhaustive, detailed analysis covering every aspect of the cinematic techniques."
    elif analysis_depth == "quick":
        depth_instruction = "\nProvide a brief summary of the key techniques only."
    
    # Build format instruction
    format_instruction = ""
    if output_format == "bullet":
        format_instruction = "\nFormat the output as bullet points for each focus area."
    elif output_format == "narrative":
        format_instruction = "\nFormat the output as a flowing narrative essay."

    # Build base prompt with depth and format
    base_prompt = f"""Analyze this video reference:

Description: {description}
Focus Areas: {', '.join(focus_areas)}
Analysis Depth: {analysis_depth}
{depth_instruction}
{format_instruction}
Provide detailed analysis of the cinematic techniques used.
"""

    # Inject RAG context if enabled
    rag_context = _get_rag_context(
        capsule_id=DimensionCapsuleId.REFERENCE_ANALYZE.value,
        query=f"{description} {' '.join(focus_areas)}".strip(),
        use_rag=use_rag,
    )
    user_prompt = _inject_rag_into_prompt(base_prompt, rag_context, position="prepend")

    try:
        result, metrics = await _call_gemini(
            prompt=user_prompt,
            system_prompt=REFERENCE_ANALYZER_SYSTEM,
            api_key=user_api_key,
            model=model,
        )
        
        return {
            "success": "error" not in result,
            "capsule_id": DimensionCapsuleId.REFERENCE_ANALYZE.value,
            "output": result,
            "error": result.get("error"),
            "metrics": {
                "latency_ms": metrics.latency_ms,
                "tokens": metrics.input_tokens + metrics.output_tokens,
                "model": metrics.model,
            },
        }
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.REFERENCE_ANALYZE.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


# =============================================================================
# P3: Multi-mode QC Constants and Helpers
# =============================================================================

VALID_INSPECTION_MODES = {"comprehensive", "quick", "cinematic", "consistency"}
DEFAULT_CRITERIA = ["aesthetic", "consistency", "safety"]

# Mode → (criteria, instruction) mapping
MODE_CONFIGS = {
    "comprehensive": {
        "criteria": None,  # Use base criteria
        "instruction": "",
    },
    "cinematic": {
        "criteria": ["aesthetic", "narrative", "technical"],
        "instruction": "\nEvaluate with focus on cinematic quality, visual storytelling, and professional production standards.",
    },
    "quick": {
        "criteria_limit": 2,  # First 2 of base criteria
        "instruction": "\nProvide a brief, focused evaluation highlighting only critical issues.",
    },
    "consistency": {
        "criteria": ["consistency", "technical"],
        "instruction": "\nFocus on evaluating consistency across style, tone, and technical specifications.",
    },
}


def _normalize_modes(inputs: Dict[str, Any]) -> List[str]:
    """Normalize inspection_modes: dedupe, validate, no silent fallback."""
    raw = inputs.get("inspection_modes") or [inputs.get("inspection_mode", "comprehensive")]
    seen = set()
    result = []
    for m in raw:
        if isinstance(m, str) and m in VALID_INSPECTION_MODES and m not in seen:
            result.append(m)
            seen.add(m)
    return result


def _normalize_threshold_qc(params: Dict[str, Any]) -> int:
    """Normalize threshold: 0-1 → 0-100."""
    raw = params.get("threshold", 70)
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return 70
    if 0 <= val <= 1:
        return int(val * 100)
    return max(0, min(100, int(val)))


def _get_mode_config(mode: str, base_criteria: List[str]) -> Tuple[List[str], str]:
    """Get (criteria, instruction) for a mode."""
    config = MODE_CONFIGS.get(mode, MODE_CONFIGS["comprehensive"])
    
    if "criteria" in config and config["criteria"]:
        criteria = config["criteria"]
    elif "criteria_limit" in config:
        criteria = base_criteria[:config["criteria_limit"]]
    else:
        criteria = base_criteria
    
    return criteria, config.get("instruction", "")


def _dedupe_list(items: List[str]) -> List[str]:
    """Deduplicate while preserving order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def _aggregate_metrics(
    mode_metrics: Dict[str, Optional[CapsuleMetrics]]
) -> Dict[str, Any]:
    """Aggregate metrics across modes: sum tokens, total latency."""
    total_tokens = 0
    total_latency = 0
    model = None
    
    for m in mode_metrics.values():
        if m:
            total_tokens += m.input_tokens + m.output_tokens
            total_latency += m.latency_ms
            if not model:
                model = m.model
    
    return {
        "latency_ms": total_latency,
        "tokens": total_tokens,
        "model": model or "unknown",
    }


async def _evaluate_quality_single_mode(
    content: str,
    content_type: str,
    criteria: List[str],
    mode_instruction: str,
    threshold: int,
    model: str,
    rag_context: str,
    context_str: str,
    user_api_key: Optional[str],
) -> Tuple[Dict[str, Any], Optional[CapsuleMetrics]]:
    """Evaluate content for a single inspection mode.
    
    Returns:
        Tuple of (result_dict, metrics or None on error)
    """
    base_prompt = f"""Evaluate this {content_type} content against the following criteria: {', '.join(criteria)}
{mode_instruction}
Content to Evaluate:
---
{content}
---
{context_str}

Passing Threshold: {threshold}/100

For each criterion, provide a score (0-100), whether it passed, and detailed feedback.
Calculate overall score as the average of all criteria scores.
"""
    user_prompt = _inject_rag_into_prompt(base_prompt, rag_context, position="prepend")

    try:
        result, metrics = await _call_gemini(
            prompt=user_prompt,
            system_prompt=QUALITY_CHECKER_SYSTEM,
            api_key=user_api_key,
            model=model,
            temperature=0.3,
        )
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {"error": str(e)}, None

    # Normalize result structure
    if "error" in result:
        return result, metrics
    
    # Ensure criteria_results exists
    if "criteria_results" not in result:
        result["criteria_results"] = {}

    # Calculate score from criteria if missing
    if "score" not in result:
        cr = result.get("criteria_results", {})
        scores = [c.get("score", 0) for c in cr.values() if isinstance(c, dict)]
        result["score"] = sum(scores) / len(scores) if scores else 0

    # Derive passed from score if missing
    if "passed" not in result:
        result["passed"] = result.get("score", 0) >= threshold

    # Ensure lists exist
    result.setdefault("issues", [])
    result.setdefault("suggestions", [])

    return result, metrics


async def run_quality_checker(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Check content quality (P3: multi-mode support).
    
    Evaluates content against multiple quality criteria across multiple inspection modes.
    Returns backward-compatible output with optional modes/overall for multi-mode.
    
    Args:
        inputs: content, content_type, inspection_modes (P3), criteria, context
        params: model, threshold (0-100 or 0-1)
        user_api_key: Optional BYOK

    Returns:
        CapsuleResult with passed, score, criteria_results, issues, suggestions
        Multi-mode adds: modes (per-mode results), overall (aggregate summary)
    """
    # === Input Validation (unchanged) ===
    content = _sanitize_text(
        inputs.get("content", ""),
        MAX_CONTENT_LENGTH,
        "content"
    )
    if not content:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.QUALITY_CHECK.value,
            "output": {},
            "error": "Content is required",
            "metrics": None,
        }

    content_type = _sanitize_text(
        inputs.get("content_type", "text"),
        50,
        "content_type"
    )

    # === P3: Normalize modes and threshold ===
    inspection_modes = _normalize_modes(inputs)
    threshold = _normalize_threshold_qc(params)
    
    # Handle invalid modes (no valid modes after filtering)
    if not inspection_modes:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.QUALITY_CHECK.value,
            "output": {},
            "error": "Invalid inspection modes",
            "metrics": None,
        }
    
    # Base criteria (can be overridden per mode)
    base_criteria = inputs.get("criteria", DEFAULT_CRITERIA)
    if not isinstance(base_criteria, list):
        base_criteria = DEFAULT_CRITERIA
    valid_criteria = {"aesthetic", "ad_suitability", "consistency", "safety", "technical", "narrative"}
    base_criteria = [c for c in base_criteria if c in valid_criteria]
    if not base_criteria:
        base_criteria = DEFAULT_CRITERIA

    # Context string (shared across modes)
    context = inputs.get("context", {})
    context_str = ""
    if isinstance(context, dict) and context:
        context_str = f"\nAdditional Context: {json.dumps(context, ensure_ascii=False)[:1000]}"

    # Model selection
    model = _validate_enum(
        params.get("model", "gemini-3-pro-preview"),
        ALLOWED_MODELS,
        "model",
        "gemini-3-pro-preview"
    )
    use_rag = params.get("use_rag", True)

    # === Build unified RAG context (all criteria union) ===
    criteria_union = set()
    for mode in inspection_modes:
        mode_criteria, _ = _get_mode_config(mode, base_criteria)
        criteria_union.update(mode_criteria)
    
    rag_context = _get_rag_context(
        capsule_id=DimensionCapsuleId.QUALITY_CHECK.value,
        query=f"quality standards {' '.join(sorted(criteria_union))} {content_type}".strip(),
        use_rag=use_rag,
    )

    # === Multi-mode evaluation loop ===
    modes_results: Dict[str, Dict[str, Any]] = {}
    mode_metrics: Dict[str, Optional[CapsuleMetrics]] = {}
    successful_modes: List[str] = []

    logger.info(f"[QC] Starting multi-mode evaluation: modes={inspection_modes}")

    for mode in inspection_modes:
        mode_criteria, mode_instruction = _get_mode_config(mode, base_criteria)
        
        result, metrics = await _evaluate_quality_single_mode(
            content=content,
            content_type=content_type,
            criteria=mode_criteria,
            mode_instruction=mode_instruction,
            threshold=threshold,
            model=model,
            rag_context=rag_context,
            context_str=context_str,
            user_api_key=user_api_key,
        )
        
        modes_results[mode] = result
        mode_metrics[mode] = metrics
        
        if "error" not in result:
            successful_modes.append(mode)
            logger.debug(f"[QC] Mode '{mode}' succeeded: score={result.get('score')}")
        else:
            logger.warning(f"[QC] Mode '{mode}' failed: {result.get('error')}")

    # === Handle all modes failed ===
    if not successful_modes:
        aggregated = _aggregate_metrics(mode_metrics)
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.QUALITY_CHECK.value,
            "output": {"modes": modes_results} if len(inspection_modes) > 1 else {},
            "error": "All inspection modes failed",
            "metrics": aggregated if any(mode_metrics.values()) else None,
        }

    # === Primary mode selection (prefer comprehensive) ===
    if "comprehensive" in successful_modes:
        primary_mode = "comprehensive"
    else:
        primary_mode = successful_modes[0]
    
    primary = modes_results[primary_mode]

    # === Merge issues/suggestions from successful modes ===
    merged_issues = _dedupe_list([
        issue
        for mode in successful_modes
        for issue in modes_results[mode].get("issues", [])
    ])
    merged_suggestions = _dedupe_list([
        suggestion
        for mode in successful_modes
        for suggestion in modes_results[mode].get("suggestions", [])
    ])

    # === Calculate overall from all modes (P3: all must pass for overall pass) ===
    overall_score = sum(
        modes_results[m].get("score", 0) for m in successful_modes
    ) / len(successful_modes)
    overall_passed = (
        all(modes_results[m].get("passed", False) for m in successful_modes)
        and len(successful_modes) == len(inspection_modes)  # No failed modes
    )

    # === Build backward-compatible output ===
    is_multimode = len(inspection_modes) > 1
    
    if is_multimode:
        # Multi-mode: top-level uses OVERALL (safer for UI)
        output = {
            "passed": overall_passed,
            "score": round(overall_score, 2),
            "criteria_results": primary.get("criteria_results", {}),  # From primary for detail
            "issues": merged_issues,
            "suggestions": merged_suggestions,
            # P3: Primary mode separate for reference
            "primary_mode": primary_mode,
            "primary": {
                "passed": primary.get("passed"),
                "score": primary.get("score"),
                "criteria_results": primary.get("criteria_results", {}),
            },
            "modes": modes_results,
            "overall": {
                "passed": overall_passed,
                "score": round(overall_score, 2),
                "mode_count": len(inspection_modes),
                "successful_modes": successful_modes,
                "failed_modes": [m for m in inspection_modes if m not in successful_modes],
            },
        }
    else:
        # Single-mode: top-level from primary (backward compat, no modes/overall)
        output = {
            "passed": primary.get("passed", overall_passed),
            "score": primary.get("score", overall_score),
            "criteria_results": primary.get("criteria_results", {}),
            "issues": merged_issues,
            "suggestions": merged_suggestions,
        }


    logger.info(
        f"[QC] Completed: modes={len(inspection_modes)}, "
        f"success={len(successful_modes)}, overall_score={overall_score:.1f}"
    )

    return {
        "success": True,
        "capsule_id": DimensionCapsuleId.QUALITY_CHECK.value,
        "output": output,
        "error": None,
        "metrics": _aggregate_metrics(mode_metrics),
    }


# Auteur style mapping for aesthetic director
AUTEUR_STYLE_MAP = {
    "bong": {
        "name": "봉준호 (Bong Joon-ho)",
        "key": "auteur.bong-joon-ho",
        "signature": "Structural tension, genre mixing, controlled camera, cool tones",
        "palette_bias": "cool",
        "pacing": "medium",
        "camera": "controlled",
    },
    "park": {
        "name": "박찬욱 (Park Chan-wook)",
        "key": "auteur.park-chan-wook",
        "signature": "Symmetry, high contrast, warm colors, precise framing",
        "palette_bias": "warm",
        "pacing": "medium",
        "camera": "controlled",
    },
    "shinkai": {
        "name": "신카이 마코토 (Shinkai Makoto)",
        "key": "auteur.shinkai",
        "signature": "Light diffusion, lyrical colors, emotional atmosphere",
        "palette_bias": "warm",
        "pacing": "slow",
        "camera": "controlled",
    },
    "lee": {
        "name": "이준호 (Lee Jun-ho)",
        "key": "auteur.lee-junho",
        "signature": "Music sync, rhythmic editing, dynamic camera",
        "palette_bias": "neutral",
        "pacing": "medium",
        "camera": "dynamic",
    },
    "na": {
        "name": "나홍진 (Na Hong-jin)",
        "key": "auteur.na-hongjin",
        "signature": "Raw realism, suspense, chaotic camera, cool tones",
        "palette_bias": "cool",
        "pacing": "fast",
        "camera": "dynamic",
    },
    "hong": {
        "name": "홍상수 (Hong Sang-soo)",
        "key": "auteur.hong-sangsoo",
        "signature": "Static camera, dialogue-driven, neutral palette",
        "palette_bias": "neutral",
        "pacing": "slow",
        "camera": "static",
    },
}


async def run_aesthetic_director(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Generate visual style guidelines with auteur matching and RAG context.

    Uses 6 director signature styles and optional RAG retrieval for
    aesthetic guidance generation.

    Args:
        inputs: concept, reference_style, mood, target_medium
        params: model, use_rag
        user_api_key: Optional BYOK

    Returns:
        CapsuleResult with visual_guidelines, color_palette, style_keywords, etc.
    """
    # Validate inputs
    concept = _sanitize_text(
        inputs.get("concept", ""),
        MAX_CONCEPT_LENGTH,
        "concept"
    )
    if not concept:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.AESTHETIC_DIRECT.value,
            "output": {},
            "error": "Concept is required",
            "metrics": None,
        }

    reference_style = _sanitize_text(inputs.get("reference_style", ""), 50, "reference_style")
    mood = _sanitize_text(inputs.get("mood", "neutral"), 50, "mood")
    lighting_style = _sanitize_text(inputs.get("lighting_style", "natural"), 50, "lighting_style")
    color_mood = _sanitize_text(inputs.get("color_mood", "neutral"), 50, "color_mood")
    target_medium = _sanitize_text(inputs.get("target_medium", "video"), 50, "target_medium")

    # Match auteur style if provided
    auteur_context = ""
    matched_auteur = None
    if reference_style:
        style_key = reference_style.lower().strip()
        if style_key in AUTEUR_STYLE_MAP:
            matched_auteur = AUTEUR_STYLE_MAP[style_key]
            auteur_context = f"""
Reference Style: {matched_auteur['name']}
Signature: {matched_auteur['signature']}
Palette Bias: {matched_auteur['palette_bias']}
Pacing: {matched_auteur['pacing']}
Camera Style: {matched_auteur['camera']}
"""

    model = _validate_enum(
        params.get("model", "gemini-3-pro-preview"),
        ALLOWED_MODELS,
        "model",
        "gemini-3-pro-preview"
    )
    use_rag = params.get("use_rag", True)

    # Build base prompt with all style parameters
    base_prompt = f"""Create comprehensive visual style guidelines for:

Concept: {concept}
Mood: {mood}
Lighting Style: {lighting_style}
Color Mood: {color_mood}
Target Medium: {target_medium}
{auteur_context}

Generate detailed guidelines including:
1. Visual composition techniques
2. Lighting approach (focusing on {lighting_style} style)
3. Color palette (provide 5-7 hex codes matching {color_mood} mood)
4. Style keywords (5-10 descriptive terms)
5. Elements to avoid
"""

    # Inject RAG context if enabled
    rag_context = _get_rag_context(
        capsule_id=DimensionCapsuleId.AESTHETIC_DIRECT.value,
        query=f"{concept} {mood} {reference_style}".strip(),
        use_rag=use_rag,
    )
    user_prompt = _inject_rag_into_prompt(base_prompt, rag_context, position="prepend")

    try:
        result, metrics = await _call_gemini(
            prompt=user_prompt,
            system_prompt=AESTHETIC_DIRECTOR_SYSTEM,
            api_key=user_api_key,
            model=model,
            temperature=0.7,
        )

        # Enrich with auteur info if matched
        if "error" not in result and matched_auteur:
            if "auteur_influence" not in result:
                result["auteur_influence"] = {}
            result["auteur_influence"]["matched_style"] = matched_auteur["name"]
            result["auteur_influence"]["capsule_key"] = matched_auteur["key"]

        return {
            "success": "error" not in result,
            "capsule_id": DimensionCapsuleId.AESTHETIC_DIRECT.value,
            "output": result,
            "error": result.get("error"),
            "metrics": {
                "latency_ms": metrics.latency_ms,
                "tokens": metrics.input_tokens + metrics.output_tokens,
                "model": metrics.model,
            },
        }
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.AESTHETIC_DIRECT.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


AESTHETIC_MOODBOARD_SYSTEM = """You are a world-class visual design consultant.
Your task is to generate 3 DISTINCT visual direction concepts based on the user's input.
Each direction should feel significantly different in tone, style, and mood.

Output ONLY valid JSON:
{
  "directions": [
    {
      "id": "direction_1",
      "title": "Short evocative title (e.g., 'Neon Noir Dreams')",
      "description": "2-3 sentence description of the visual style",
      "keywords": ["keyword1", "keyword2", "keyword3"],
      "suggested_auteur": "A director whose style matches (e.g., 'Wong Kar-wai')",
      "color_preview": ["#hex1", "#hex2", "#hex3"]
    }
  ]
}
"""


async def run_aesthetic_moodboard(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Generate 3 distinct visual direction cards for concept exploration.

    Stage 1 of the Visual Identity Workshop flow.

    Args:
        inputs: concept, mood
        params: model
        user_api_key: Optional BYOK

    Returns:
        CapsuleResult with 3 visual direction cards.
    """
    # Validate inputs
    concept = _sanitize_text(
        inputs.get("concept", ""),
        MAX_CONCEPT_LENGTH,
        "concept"
    )
    if not concept:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.AESTHETIC_MOODBOARD.value,
            "output": {},
            "error": "Concept is required",
            "metrics": None,
        }

    mood = _sanitize_text(inputs.get("mood", "neutral"), 50, "mood")
    
    model = _validate_enum(
        params.get("model", "gemini-3-pro-preview"),
        ALLOWED_MODELS,
        "model",
        "gemini-3-pro-preview"
    )

    # Build base prompt
    base_prompt = f"""Generate 3 distinct visual direction concepts for:

Concept: {concept}
Mood Preference: {mood}

The 3 directions should be:
1. A "Safe" option that's polished and commercially appealing.
2. A "Bold" option that's artistic and unconventional.
3. A "Wild Card" that's unexpected and genre-bending.

For each direction, suggest 3 preview colors that represent the palette.
"""

    try:
        result, metrics = await _call_gemini(
            prompt=base_prompt,
            system_prompt=AESTHETIC_MOODBOARD_SYSTEM,
            api_key=user_api_key,
            model=model,
            temperature=0.9,  # High creativity for brainstorming
        )
        
        return {
            "success": "error" not in result,
            "capsule_id": DimensionCapsuleId.AESTHETIC_MOODBOARD.value,
            "output": result,
            "error": result.get("error"),
            "metrics": {
                "latency_ms": metrics.latency_ms,
                "tokens": metrics.input_tokens + metrics.output_tokens,
                "model": metrics.model,
            },
        }
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.AESTHETIC_MOODBOARD.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


# Persona analysis stage flow (8-stage psychological model)
PERSONA_STAGES = ["intro", "self_expression", "maslow", "formative", "attachment", "shadow", "archetype", "synthesis"]
QUICK_STAGES = ["intro", "maslow", "archetype", "synthesis"]
STANDARD_STAGES = ["intro", "self_expression", "maslow", "attachment", "archetype", "synthesis"]


async def run_sound_moodboard(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Generate 3 distinct audio direction cards."""
    concept = _sanitize_text(
        inputs.get("concept", ""),
        MAX_CONCEPT_LENGTH,
        "concept"
    )
    if not concept:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.SOUND_MOODBOARD.value,
            "output": {},
            "error": "Concept is required",
            "metrics": None,
        }

    model = _validate_enum(
        params.get("model", "gemini-3-pro-preview"),
        ALLOWED_MODELS,
        "model",
        "gemini-3-pro-preview"
    )

    base_prompt = f"""Generate 3 distinct audio direction concepts for:
Concept: {concept}

Explore different interpretations (e.g., one literal, one emotional, one abstract).
Each direction must have a distinct mood and sonic texture.
"""

    try:
        result, metrics = await _call_gemini(
            prompt=base_prompt,
            system_prompt=SOUND_MOODBOARD_SYSTEM,
            api_key=user_api_key,
            model=model,
            temperature=0.9,
        )

        return {
            "success": "error" not in result,
            "capsule_id": DimensionCapsuleId.SOUND_MOODBOARD.value,
            "output": result,
            "error": result.get("error"),
            "metrics": {
                "latency_ms": metrics.latency_ms,
                "tokens": metrics.input_tokens + metrics.output_tokens,
                "model": metrics.model,
            },
        }
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.SOUND_MOODBOARD.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }



async def run_persona_analyzer(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Perform deep persona analysis through multi-turn conversation.

    Analyzes user's persona through 7 stages:
    1. INTRO - Initial self-description
    2. SAJU - Four Pillars analysis
    3. MBTI - Cognitive functions
    4. SUBCONSCIOUS - Pattern recognition
    5. UNCONSCIOUS - Shadow work
    6. BACKGROUND - Formative experiences
    7. SYNTHESIS - Final profile

    Args:
        inputs: user_message, analysis_stage, persona_data, birth_info
        params: model, depth_level
        user_api_key: Optional BYOK

    Returns:
        CapsuleResult with assistant_message, next_stage, persona_update, etc.
    """
    # Get analysis stage first (needed for intro shortcut)
    # Accept both "analysis_stage" (backend convention) and "current_stage" (frontend convention)
    current_stage = _sanitize_text(
        inputs.get("analysis_stage") or inputs.get("current_stage", "intro"),
        30,
        "analysis_stage"
    )

    # Validate inputs
    user_message = _sanitize_text(
        inputs.get("user_message", ""),
        MAX_TOPIC_LENGTH,
        "user_message"
    )
    
    # Skip user_message validation for intro stage (AI speaks first)
    if not user_message and current_stage != "intro":
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.PERSONA_ANALYZE.value,
            "output": {},
            "error": "User message is required",
            "metrics": None,
        }

    persona_data = inputs.get("persona_data", {})
    if not isinstance(persona_data, dict):
        persona_data = {}
    birth_info = inputs.get("birth_info", {})
    if not isinstance(birth_info, dict):
        birth_info = {}

    # Get depth level to determine stage flow
    depth_level = params.get("depth_level", "deep")
    if depth_level == "quick":
        stage_flow = QUICK_STAGES
    elif depth_level == "standard":
        stage_flow = STANDARD_STAGES
    else:
        stage_flow = PERSONA_STAGES

    # Determine max turns based on depth
    max_turns = 2 if depth_level == "deep" else 1

    # Extract meta info
    meta_info = persona_data.get("_meta", {})
    # Reset turn count if stage changed (detected by client sending different stage than last meta)
    # But since client sends back what we sent, we rely on our return value logic.
    # We need to rely on the input 'current_stage' vs 'meta.last_stage' check if possible,
    # or just trust the client keeps state.
    # Simpler: client sends persona_data. If we see _meta, we use it.
    
    current_turn = meta_info.get("stage_turn_count", 0)
    
    # If this is a new stage (based on some heuristic or just 0), it's turn 1 (response to intro)
    # Actually, "intro" returns next_stage="saju".
    # User sends "saju" + User Input. This is Turn 1 for Saju.
    # So if we receive "saju", it means we are processing the user's answer to our previous question.
    # So we are at least at Turn 1.
    
    # Logic:
    # 1. User answers previous question.
    # 2. We analyze answer.
    # 3. If turn < max_turns:
    #      Ask follow-up question.
    #      Return next_stage = current_stage.
    #      Update _meta.turn = current_turn + 1.
    # 4. If turn >= max_turns:
    #      Conclude this stage.
    #      Return next_stage = actual_next_stage.
    #      Update _meta.turn = 0.

    # However, for 'saju' stage, the first input is birth info.
    # This is effectively the answer to "Intro" stage's question.
    # Let's count this as Turn 1.
    
    # Increase turn count for this processing step
    current_turn += 1

    # Validate current stage
    if current_stage not in stage_flow:
        current_stage = stage_flow[0]

    model = _validate_enum(
        params.get("model", "gemini-3-pro-preview"),
        ALLOWED_MODELS,
        "model",
        "gemini-3-flash-preview"
    )

    # === INTRO Stage: Return static opening message (no LLM call) ===
    if current_stage == "intro":
        # Return the opening message immediately
        intro_message = """안녕하세요. 심연의 거울에 오신 것을 환영합니다. 🪷

저는 당신의 내면을 비추는 거울이 되어드릴 거예요. 사주, MBTI, 혈액형, 그리고 깊은 심리학적 렌즈를 통해 당신만의 **창작 DNA**를 발견하는 여정을 함께할게요.

먼저 기본 정보를 알려주세요:

1. **생년월일** (예: 1990년 3월 15일)
2. **태어난 시간** (모르시면 "모름"이라고 적어주세요)
3. **MBTI** (모르시면 "모름"이라고 적어주세요)
4. **혈액형** (A, B, O, AB 또는 "모름")

편하게 한 줄로 적어주셔도 돼요! 😊"""

        next_stage_idx = 1 if len(stage_flow) > 1 else 0
        return {
            "success": True,
            "capsule_id": DimensionCapsuleId.PERSONA_ANALYZE.value,
            "output": {
                "assistant_message": intro_message,
                "next_stage": stage_flow[next_stage_idx],  # Move to next stage (e.g., saju or mbti)
                "persona_update": {},
                "analysis_complete": False,
                "final_persona": None,
            },
            "error": None,
            "metrics": {
                "latency_ms": 0,
                "tokens": 0,
                "model": model,
            },
        }

    # Build context from previous analysis
    context_parts = [f"Current Stage: {current_stage}"]
    context_parts.append(f"Stage Flow: {' -> '.join(stage_flow)}")

    if persona_data:
        context_parts.append(f"Accumulated Persona Data: {json.dumps(persona_data, ensure_ascii=False)}")
    if birth_info:
        context_parts.append(f"Birth Info: {json.dumps(birth_info, ensure_ascii=False)}")

    # Deep Mode Logic: Determine Prompt Strategy
    if current_turn < max_turns and current_stage != "synthesis":
        # STAY in current stage, ask follow-up
        next_stage_logic = current_stage
        next_meta = {"stage_turn_count": current_turn, "last_stage": current_stage}
        prompt_instruction = f"""
Current Stage: {current_stage} (Turn {current_turn}/{max_turns})
This is a DEEP MODE analysis. The user just answered your primary question.
DO NOT move to the next stage yet.
Ask a provocative, insightful FOLLOW-UP question to dig deeper into their answer.
Objective: Uncover hidden motivations, contradictions, or specific examples.
"""
    else:
        # MOVE to next stage
        try:
            current_idx = stage_flow.index(current_stage)
            if current_idx + 1 < len(stage_flow):
                next_stage_logic = stage_flow[current_idx + 1]
            else:
                next_stage_logic = "synthesis"
        except ValueError:
            next_stage_logic = "synthesis"
        
        next_meta = {"stage_turn_count": 0, "last_stage": next_stage_logic}
        prompt_instruction = f"""
Current Stage: {current_stage} (Final Turn)
Analyze the user's response and consolidate insights.
Then, move to the NEXT STAGE: {next_stage_logic}.
Ask the opening question for the {next_stage_logic} stage.
"""

    context_str = "\n".join(context_parts)
    use_rag = params.get("use_rag", True)

    # Build base prompt
    base_prompt = f"""Continue the persona analysis conversation.

{context_str}

User's Response: {user_message}

{prompt_instruction}

Ensure your response is valid JSON.
"""

    # Inject RAG context if enabled (persona analysis frameworks)
    # Stage-specific psychology query keywords
    stage_rag_keywords = {
        "self_expression": "자기표현 창작 동기 심리 분석",
        "maslow": "매슬로우 욕구 계층 자아실현 결핍 동기",
        "formative": "발달심리학 성장배경 원가족 형성기 경험",
        "attachment": "애착이론 볼비 안전기지 애착유형 관계패턴",
        "shadow": "융 그림자 무의식 억압 투사 통합",
        "archetype": "융 원형 집단무의식 페르소나 아니마 아니무스",
        "synthesis": "통합 자기실현 창작DNA 심리프로파일",
    }
    rag_query = stage_rag_keywords.get(current_stage, f"{current_stage} 심리 분석")
    if user_message:
        rag_query = f"{rag_query} {user_message[:80]}"

    rag_context = _get_rag_context(
        capsule_id=DimensionCapsuleId.PERSONA_ANALYZE.value,
        query=rag_query.strip(),
        use_rag=use_rag,
    )
    user_prompt = _inject_rag_into_prompt(base_prompt, rag_context, position="prepend")

    try:
        result, metrics = await _call_gemini(
            prompt=user_prompt,
            system_prompt=PERSONA_ANALYZER_SYSTEM,
            api_key=user_api_key,
            model=model,
            temperature=0.8,  # Slightly higher for more natural conversation
        )

        # Post-process: ensure proper structure
        if "error" not in result:
            # Force next_stage from our logic (prevent LLM hallucination on stage flow)
            result["next_stage"] = next_stage_logic

            # Ensure persona_update exists
            if "persona_update" not in result:
                result["persona_update"] = {}
                
            # Inject _meta into persona_update
            if not isinstance(result["persona_update"], dict):
                result["persona_update"] = {}
            result["persona_update"]["_meta"] = next_meta

            # Check if analysis is complete
            if next_stage_logic == "synthesis" and result.get("analysis_complete") is None:
                result["analysis_complete"] = (current_stage == "synthesis")

        return {
            "success": "error" not in result,
            "capsule_id": DimensionCapsuleId.PERSONA_ANALYZE.value,
            "output": result,
            "error": result.get("error"),
            "metrics": {
                "latency_ms": metrics.latency_ms,
                "tokens": metrics.input_tokens + metrics.output_tokens,
                "model": metrics.model,
            },
        }
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.PERSONA_ANALYZE.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


# Veo model credit costs
VEO_CREDIT_COSTS = {
    "veo-3.1-generate-preview": 200,
    "veo-3.1-fast-generate-preview": 60,
}


async def run_veo_generator(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Generate video using Veo 3.1 with async polling.

    Uses the VeoService for async video generation with exponential
    backoff polling.

    Args:
        inputs: prompt, negative_prompt, duration_seconds, aspect_ratio, include_audio
        params: model, max_wait_seconds
        user_api_key: Optional BYOK

    Returns:
        CapsuleResult with video_uri or error
    """
    from app.services.veo_service import VeoConfig, get_veo_service

    # Validate inputs
    prompt = _sanitize_text(
        inputs.get("prompt", ""),
        MAX_CONCEPT_LENGTH,
        "prompt"
    )
    if not prompt:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.VEO_VIDEO_GENERATE.value,
            "output": {},
            "error": "Prompt is required",
            "metrics": None,
        }

    negative_prompt = inputs.get("negative_prompt")
    if negative_prompt:
        negative_prompt = _sanitize_text(negative_prompt, 500, "negative_prompt")

    duration_seconds = _validate_int_range(inputs.get("duration_seconds", 8), 4, 8, 8)
    aspect_ratio = _sanitize_text(inputs.get("aspect_ratio", "16:9"), 10, "aspect_ratio")
    include_audio = inputs.get("include_audio", True)
    if not isinstance(include_audio, bool):
        include_audio = True

    # Get params
    model = params.get("model", "veo-3.1-generate-preview")
    if model not in VEO_CREDIT_COSTS:
        model = "veo-3.1-generate-preview"

    max_wait_seconds = _validate_int_range(params.get("max_wait_seconds", 360), 60, 600, 360)
    use_rag = params.get("use_rag", True)

    # Optionally enhance prompt with RAG context (Veo templates, video styles)
    enhanced_prompt = prompt
    if use_rag:
        rag_context = _get_rag_context(
            capsule_id=DimensionCapsuleId.VEO_VIDEO_GENERATE.value,
            query=prompt[:500],  # Use first 500 chars as query
            use_rag=use_rag,
        )
        # For Veo, we append style hints rather than prepend verbose context
        if rag_context:
            # Extract key style keywords from RAG context (simplified injection)
            logger.debug(f"[VEO] RAG context available, enhancing prompt")
            # Note: For video generation, keep the prompt concise
            # RAG context is logged but not directly appended to avoid confusion

    # Build config
    config = VeoConfig(
        prompt=enhanced_prompt,
        model=model,
        duration_seconds=duration_seconds,
        aspect_ratio=aspect_ratio,
        negative_prompt=negative_prompt,
        include_audio=include_audio,
    )

    try:
        # Get service (with optional BYOK)
        service = get_veo_service(api_key=user_api_key)

        # Generate video
        result = await service.generate_video(
            config=config,
            max_wait_seconds=max_wait_seconds,
        )

        if result.success:
            return {
                "success": True,
                "capsule_id": DimensionCapsuleId.VEO_VIDEO_GENERATE.value,
                "output": {
                    "video_uri": result.video_uri,
                    "duration_ms": result.duration_ms,
                    "metadata": result.metadata,
                },
                "error": None,
                "metrics": {
                    "latency_ms": result.duration_ms,
                    "model": result.model,
                    "credit_cost": result.credit_cost,
                },
            }
        else:
            return {
                "success": False,
                "capsule_id": DimensionCapsuleId.VEO_VIDEO_GENERATE.value,
                "output": {},
                "error": result.error,
                "metrics": {
                    "latency_ms": result.duration_ms,
                    "model": result.model,
                    "credit_cost": 0,
                },
            }

    except Exception as e:
        logger.exception(f"Veo generation error: {e}")
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.VEO_VIDEO_GENERATE.value,
            "output": {},
            "error": f"Video generation error: {type(e).__name__}: {str(e)}",
            "metrics": None,
        }


# ============================================================================
# Story Architect Adapter
# ============================================================================

STORY_STRUCTURES = {
    "3act": "Classic 3-act structure (Setup, Confrontation, Resolution)",
    "hero": "Hero's Journey (12 stages)",
    "circular": "Circular narrative (ends where it begins)",
    "montage": "Montage-based (thematic progression)",
}

STORY_REFINE_SYSTEM = """You are a master story editor and creative producer.
Your goal is to help a writer refine their raw concept into a compelling pitch.

Analyze the user's concept and generate 3 DISTINCT narrative angles/approaches.
For example, if the concept is "a robot loves flowers":
1. Angle A (Sci-Fi Drama): Focus on programming vs free will.
2. Angle B (Pixar Style): Heartwarming adventure about finding beauty in rust.
3. Angle C (Dark Thriller): The flowers are an invasive species the robot protects.

Output ONLY valid JSON:
{
  "angles": [
    {
      "id": "angle_1",
      "title": "Proposed Title",
      "logline": "One sentence summary focusing on the conflict",
      "tone": "Emotional / Dark / Humorous",
      "theme": "The core thematic question"
    }
  ]
}
"""


async def run_story_architect(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Generate video scenario from concept, persona, and reference analysis.

    Combines creative DNA (persona) and reference analysis to create
    compelling video narratives with clear structure.

    Args:
        inputs: concept, persona_data, reference_analysis, genre, duration, structure, language
        params: model, use_rag
        user_api_key: Optional BYOK

    Returns:
        CapsuleResult with title, logline, synopsis, structure, characters, themes
    """
    # Validate inputs
    concept = _sanitize_text(
        inputs.get("concept", ""),
        MAX_CONCEPT_LENGTH,
        "concept"
    )
    if not concept:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.STORY_ARCHITECT.value,
            "output": {},
            "error": "Concept is required",
            "metrics": None,
        }

    # Optional context from previous dimensions
    persona_data = inputs.get("persona_data", {})
    if not isinstance(persona_data, dict):
        persona_data = {}
    reference_analysis = inputs.get("reference_analysis", {})
    if not isinstance(reference_analysis, dict):
        reference_analysis = {}

    genre = _sanitize_text(inputs.get("genre", "drama"), 30, "genre")
    duration = _sanitize_text(inputs.get("duration", "60s"), 10, "duration")
    structure = _sanitize_text(inputs.get("structure", "3act"), 20, "structure")
    language = _validate_enum(inputs.get("language", "ko"), ALLOWED_LANGUAGES, "language", "ko")

    model = _validate_enum(
        params.get("model", "gemini-3-pro-preview"),
        ALLOWED_MODELS,
        "model",
        "gemini-3-pro-preview"
    )
    use_rag = params.get("use_rag", True)

    # Build context parts
    context_parts = []
    if persona_data:
        context_parts.append(f"Creator's DNA (Persona):\n{json.dumps(persona_data, ensure_ascii=False)[:1000]}")
    if reference_analysis:
        context_parts.append(f"Reference Analysis:\n{json.dumps(reference_analysis, ensure_ascii=False)[:1000]}")

    structure_desc = STORY_STRUCTURES.get(structure, STORY_STRUCTURES["3act"])

    # Build base prompt
    base_prompt = f"""Create a video scenario for:

Concept: {concept}
Genre: {genre}
Target Duration: {duration}
Story Structure: {structure} - {structure_desc}
Output Language: {language}

{chr(10).join(context_parts) if context_parts else ""}

Generate a compelling narrative that:
1. Has a clear emotional arc
2. Includes specific visual cues for storyboarding
3. Matches the requested genre and duration
4. Incorporates the creator's style if persona data is available
"""

    # Inject RAG context if enabled
    rag_context = _get_rag_context(
        capsule_id=DimensionCapsuleId.STORY_ARCHITECT.value,
        query=f"{concept} {genre} scenario structure".strip(),
        use_rag=use_rag,
    )
    user_prompt = _inject_rag_into_prompt(base_prompt, rag_context, position="prepend")

    try:
        result, metrics = await _call_gemini(
            prompt=user_prompt,
            system_prompt=STORY_ARCHITECT_SYSTEM,
            api_key=user_api_key,
            model=model,
            temperature=0.8,  # Higher for creativity
        )

        # Post-process: ensure proper structure
        if "error" not in result:
            # Ensure required fields exist
            if "next_dimension" not in result:
                result["next_dimension"] = "storyboard-sketch"
            if "themes" not in result:
                result["themes"] = []
            if "visual_motifs" not in result:
                result["visual_motifs"] = []

        # Normalize output format (Gemini may return list or dict)
        if isinstance(result, list):
            output = {"story_elements": result, "title": result[0].get("title", "Untitled") if result and isinstance(result[0], dict) else "Untitled"}
            has_error = False
            error_msg = None
        else:
            output = result
            has_error = "error" in result
            error_msg = result.get("error")

        return {
            "success": not has_error,
            "capsule_id": DimensionCapsuleId.STORY_ARCHITECT.value,
            "output": output,
            "error": error_msg,
            "metrics": {
                "latency_ms": metrics.latency_ms,
                "tokens": metrics.input_tokens + metrics.output_tokens,
                "model": metrics.model,
            },
        }
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.STORY_ARCHITECT.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


async def run_story_refinery(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Refine a raw concept into 3 distinct narrative angles."""
    # Validate inputs
    concept = _sanitize_text(
        inputs.get("concept", ""),
        MAX_CONCEPT_LENGTH,
        "concept"
    )
    if not concept:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.STORY_REFINE.value,
            "output": {},
            "error": "Concept is required",
            "metrics": None,
        }

    genre = _sanitize_text(inputs.get("genre", "drama"), 30, "genre")
    
    model = _validate_enum(
        params.get("model", "gemini-3-pro-preview"),
        ALLOWED_MODELS,
        "model",
        "gemini-3-pro-preview"
    )

    # Build base prompt
    base_prompt = f"""Refine this story concept into 3 distinct angles.

Concept: {concept}
Preferred Genre: {genre}

Ensure the 3 angles feel significantly different from each other (e.g., change the focus, the protagonist's motivation, or the stakes).
"""

    try:
        result, metrics = await _call_gemini(
            prompt=base_prompt,
            system_prompt=STORY_REFINE_SYSTEM,
            api_key=user_api_key,
            model=model,
            temperature=0.9,  # High creativity for brainstorming
        )
        
        return {
            "success": "error" not in result,
            "capsule_id": DimensionCapsuleId.STORY_REFINE.value,
            "output": result,
            "error": result.get("error"),
            "metrics": {
                "latency_ms": metrics.latency_ms,
                "tokens": metrics.input_tokens + metrics.output_tokens,
                "model": metrics.model,
            },
        }
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.STORY_REFINE.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


# ============================================================================
# Sound Crafter Adapter
# ============================================================================

SOUND_PLATFORMS = {
    "suno": {"name": "Suno AI", "format": "descriptive prompt with style tags"},
    "udio": {"name": "Udio", "format": "genre tags and mood descriptors"},
    "elevenlabs": {"name": "ElevenLabs", "format": "voice description and script"},
}


async def run_sound_crafter(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Generate music/sound prompts for Suno, Udio, and ElevenLabs.

    Creates platform-specific audio prompts including BGM, SFX, and narration.

    Args:
        inputs: concept, storyboard, sound_type, mood, genre, tempo, duration, target_platform, language
        params: model, use_rag
        user_api_key: Optional BYOK

    Returns:
        CapsuleResult with music_prompt, style_tags, instrumentation, narration_script, etc.
    """
    # Validate inputs
    concept = _sanitize_text(
        inputs.get("concept", ""),
        MAX_TOPIC_LENGTH,
        "concept"
    )
    if not concept:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.SOUND_CRAFT.value,
            "output": {},
            "error": "Concept is required",
            "metrics": None,
        }

    # Optional storyboard context
    storyboard = inputs.get("storyboard", [])
    if not isinstance(storyboard, list):
        storyboard = []

    sound_type = _sanitize_text(inputs.get("sound_type", "bgm"), 20, "sound_type")
    mood = _sanitize_text(inputs.get("mood", "neutral"), 50, "mood")
    genre = _sanitize_text(inputs.get("genre", "cinematic"), 30, "genre")
    tempo = _sanitize_text(inputs.get("tempo", "medium"), 20, "tempo")
    duration = _sanitize_text(inputs.get("duration", "60s"), 10, "duration")
    duration = _sanitize_text(inputs.get("duration", "60s"), 10, "duration")
    target_platform = _sanitize_text(inputs.get("target_platform", "suno"), 20, "target_platform")
    language = _validate_enum(inputs.get("language", "ko"), ALLOWED_LANGUAGES, "language", "ko")
    
    # New: Mix Recipe (from Sound Design Studio Stage 2)
    mix_recipe = inputs.get("mix_recipe", {})
    if not isinstance(mix_recipe, dict):
        mix_recipe = {}

    model = _validate_enum(
        params.get("model", "gemini-3-flash-preview"),
        ALLOWED_MODELS,
        "model",
        "gemini-3-flash-preview"
    )
    use_rag = params.get("use_rag", True)

    # Get platform info
    platform_info = SOUND_PLATFORMS.get(target_platform, SOUND_PLATFORMS["suno"])

    # Build storyboard context
    storyboard_context = ""
    if storyboard:
        storyboard_context = f"\nStoryboard context (match audio to scenes):\n{json.dumps(storyboard[:10], ensure_ascii=False)[:1500]}"

    # Build base prompt
    base_prompt = f"""Create audio/music prompts for:

Concept: {concept}
Sound Type: {sound_type} (bgm/sfx/narration/full)
Mood: {mood}
Genre: {genre}
Tempo: {tempo}
Target Duration: {duration}
Output Language: {language}
{storyboard_context}

Mix Recipe (User Adjustment):
{json.dumps(mix_recipe, indent=2) if mix_recipe else "None"}

Generate detailed audio specifications that:
1. Match the visual narrative and emotional arc
2. Provide prompts for BOTH Suno v3 and Udio
3. Include specific musical/audio terminology
4. {"Include narration script if sound_type is narration or full" if sound_type in ["narration", "full"] else "Focus on instrumental elements"}
"""

    # Inject RAG context if enabled
    rag_context = _get_rag_context(
        capsule_id=DimensionCapsuleId.SOUND_CRAFT.value,
        query=f"{concept} {genre} {mood} music sound design".strip(),
        use_rag=use_rag,
    )
    user_prompt = _inject_rag_into_prompt(base_prompt, rag_context, position="prepend")

    try:
        result, metrics = await _call_gemini(
            prompt=user_prompt,
            system_prompt=SOUND_CRAFTER_SYSTEM,
            api_key=user_api_key,
            model=model,
            temperature=0.7,
        )

        # Post-process: ensure proper structure
        if "error" not in result:
            # Ensure required fields exist
            if "next_dimension" not in result:
                result["next_dimension"] = "video-maker"
            if "style_tags" not in result:
                result["style_tags"] = []
            if "instrumentation" not in result:
                result["instrumentation"] = []
            # Null out narration for non-narration modes
            if sound_type not in ["narration", "full"]:
                result["narration_script"] = None
                result["voice_direction"] = None

        return {
            "success": "error" not in result,
            "capsule_id": DimensionCapsuleId.SOUND_CRAFT.value,
            "output": result,
            "error": result.get("error"),
            "metrics": {
                "latency_ms": metrics.latency_ms,
                "tokens": metrics.input_tokens + metrics.output_tokens,
                "model": metrics.model,
            },
        }
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.SOUND_CRAFT.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


async def run_creative_editor(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Analyze and improve creative content (Creative Editor)."""
    # Validate inputs
    content = _sanitize_text(
        inputs.get("content", ""),
        10000,
        "content"
    )
    if not content:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.CREATIVE_EDITOR.value,
            "output": {},
            "error": "Content is required",
            "metrics": None,
        }

    context = _sanitize_text(inputs.get("context", ""), 1000, "context")
    persona = _sanitize_text(inputs.get("persona", "Senior Editor"), 100, "persona")
    
    model = _validate_enum(
        params.get("model", "gemini-3-pro-preview"),
        ALLOWED_MODELS,
        "model",
        "gemini-3-pro-preview"
    )
    use_rag = params.get("use_rag", True)

    # Build prompt
    base_prompt = f"""Act as a {persona}. Review and improve this content:

Context/Genre: {context}

Content to Edit:
{content}
"""

    # RAG Injection
    rag_context = _get_rag_context(
        capsule_id=DimensionCapsuleId.CREATIVE_EDITOR.value,
        query=f"{context} editing principles",
        use_rag=use_rag,
    )
    user_prompt = _inject_rag_into_prompt(base_prompt, rag_context, position="prepend")

    try:
        result, metrics = await _call_gemini(
            prompt=user_prompt,
            system_prompt=CREATIVE_EDITOR_SYSTEM,
            api_key=user_api_key,
            model=model,
            temperature=0.7, # Lower temp for more distinct editing decisions
        )

        return {
            "success": "error" not in result,
            "capsule_id": DimensionCapsuleId.CREATIVE_EDITOR.value,
            "output": result,
            "error": result.get("error"),
            "metrics": {
                "latency_ms": metrics.latency_ms,
                "tokens": metrics.input_tokens + metrics.output_tokens,
                "model": metrics.model,
            },
        }
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.CREATIVE_EDITOR.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


async def run_json_gen_convert(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Convert JSON Generator output to ShotContract.
    
    This is a lightweight adapter that doesn't call LLM - just data transformation.
    """
    import time
    from app.services.json_generator_adapter import json_generator_to_shot_contract
    
    start_time = time.monotonic()
    
    json_blocks = inputs.get("json_blocks", {})
    shot_id = inputs.get("shot_id", "shot-001")
    sequence_id = inputs.get("sequence_id", "seq-01")
    scene_id = inputs.get("scene_id", "scene-01")
    
    if not json_blocks:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.JSON_GEN_CONVERT.value,
            "output": {},
            "error": "json_blocks is required",
            "metrics": None,
        }
    
    try:
        shot_contract = json_generator_to_shot_contract(
            json_blocks=json_blocks,
            shot_id=shot_id,
            sequence_id=sequence_id,
            scene_id=scene_id,
        )
        
        latency_ms = int((time.monotonic() - start_time) * 1000)
        
        return {
            "success": True,
            "capsule_id": DimensionCapsuleId.JSON_GEN_CONVERT.value,
            "output": {
                "shot_contract": shot_contract.to_dict(),
                "evidence_refs": [f"db:shot_contracts:{shot_id}"],
            },
            "metrics": {
                "latency_ms": latency_ms,
                "tokens": 0,  # No LLM call
            },
        }
    except Exception as e:
        logger.error(f"JSON Generator conversion failed: {e}")
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.JSON_GEN_CONVERT.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


async def run_nanobanana_convert(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Convert Nanobanana Editor state to ShotContract.
    
    Lightweight adapter that doesn't call LLM - just data transformation.
    Preserves camera angle/direction in pose_motion field.
    Uses full lighting descriptions instead of just keys.
    """
    import time
    from app.services.nanobanana_adapter import nanobanana_to_shot_contract
    
    start_time = time.monotonic()
    
    editor_state = inputs.get("editor_state", {})
    shot_id = inputs.get("shot_id", "shot-001")
    sequence_id = inputs.get("sequence_id", "seq-01")
    scene_id = inputs.get("scene_id", "scene-01")
    
    if not editor_state:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.NANOBANANA_CONVERT.value,
            "output": {},
            "error": "editor_state is required",
            "metrics": None,
        }
    
    try:
        shot_contract = nanobanana_to_shot_contract(
            editor_state=editor_state,
            shot_id=shot_id,
            sequence_id=sequence_id,
            scene_id=scene_id,
        )
        
        latency_ms = int((time.monotonic() - start_time) * 1000)
        
        return {
            "success": True,
            "capsule_id": DimensionCapsuleId.NANOBANANA_CONVERT.value,
            "output": {
                "shot_contract": shot_contract.to_dict(),
                "evidence_refs": [f"db:nanobanana:{shot_id}"],
            },
            "metrics": {
                "latency_ms": latency_ms,
                "tokens": 0,  # No LLM call
            },
        }
    except Exception as e:
        logger.error(f"Nanobanana conversion failed: {e}")
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.NANOBANANA_CONVERT.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


# ============================================================================
# Prompt Alchemy - AI Video Platform Prompt Translator
# ============================================================================

# Platform-specific prompt templates (2026 Best Practices)
PROMPT_ALCHEMY_PLATFORMS = {
    "veo_31": {
        "name": "Google Veo 3.1",
        "template": """[Visual Description]: {visual}
[Dialogue]: {dialogue}
[Ambient]: {ambient}
[Mood]: {mood}
No subtitles.""",
        "requires_dialogue": True,
        "max_duration": 8,
        "native_audio": True,
    },
    "kling_26": {
        "name": "Kling 2.6",
        "template": """[Subject]: {subject}
[Action]: {action}
[Context]: {context}
[Style]: {style}
[Camera]: {camera}""",
        "requires_dialogue": False,
        "max_duration": 120,
        "native_audio": False,
    },
    "sora_max_2pro": {
        "name": "Sora Max 2 Pro",
        "template": """[Style]: {animation_style}
[Character]: {character}
[Scene]: {scene}
[Action]: {action}
[Mood]: {mood}""",
        "requires_dialogue": False,
        "max_duration": 20,
        "native_audio": True,
    },
}

PROMPT_ALCHEMY_SYSTEM = """You are Prompt Alchemy, an expert AI video prompt translator.

Your task is to transform scene descriptions into optimized prompts for specific AI video generation platforms.

## Platform Expertise:
1. **Veo 3.1**: Dialogue/narration-heavy viral videos. Always include "No subtitles." at the end.
2. **Kling 2.6**: High-quality silent cinematic videos. Remove dialogue, focus on visual storytelling.
3. **Sora Max 2 Pro**: Animation-style videos. Emphasize artistic style and character design.

## Output Rules:
- Return a JSON object with the translated prompt
- Include quality_score (0-1) indicating confidence in the translation
- Include platform_specific_tips for the target platform
- Preserve the artistic intent while optimizing for the platform's strengths
"""


async def run_prompt_translator(
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    user_api_key: Optional[str] = None,
    intent: Optional[Any] = None,
) -> CapsuleResult:
    """Translate scene descriptions to platform-specific AI video prompts.

    Supports Crebit's 3 official platforms:
    - veo_31: Dialogue/narration-heavy viral videos
    - kling_26: High-quality silent cinematic videos (recommended default)
    - sora_max_2pro: Animation-style videos

    Args:
        inputs: scene_description, target_platform, style, auteur_key
        params: model selection, auto_select (bool)
        user_api_key: Optional BYOK
        intent: Optional CreativeIntent for RAG integration

    Returns:
        CapsuleResult with translated prompt and metadata
    """
    # Intent-Resolver Integration
    if intent is not None or params.get("intent"):
        try:
            from app.resolvers.integration import prepare_dimension_params
            inputs, params = await prepare_dimension_params(
                dimension_code="PROMPT",
                inputs=inputs,
                params=params,
                intent=intent,
            )
            logger.debug("[PROMPT] Intent-resolved params applied")
        except ImportError:
            logger.debug("[PROMPT] Resolver integration not available")
        except Exception as e:
            logger.warning(f"[PROMPT] Resolver integration failed: {e}")

    # Validate inputs
    scene_description = _sanitize_text(
        inputs.get("scene_description", inputs.get("description", "")),
        MAX_DESCRIPTION_LENGTH,
        "scene_description"
    )
    if not scene_description:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.PROMPT_TRANSLATE.value,
            "output": {},
            "error": "Scene description is required",
            "metrics": None,
        }

    # Platform selection (auto or explicit)
    auto_select = params.get("auto_select", True)
    target_platform = inputs.get("target_platform", "")

    if auto_select and not target_platform:
        # Auto-selection logic based on scene content
        has_dialogue = any(kw in scene_description.lower() for kw in [
            "대화", "말하", "dialogue", "speak", "say", "narration",
            "나레이션", "dictation", "voice", "음성", "대사"
        ])
        is_animation = any(kw in scene_description.lower() for kw in [
            "animation", "애니메이션", "cartoon", "만화", "2d", "illustrated",
            "일러스트", "anime", "애니"
        ])

        if has_dialogue:
            target_platform = "veo_31"
        elif is_animation:
            target_platform = "sora_max_2pro"
        else:
            target_platform = "kling_26"  # Default: Kling recommended

    target_platform = target_platform or "kling_26"

    if target_platform not in PROMPT_ALCHEMY_PLATFORMS:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.PROMPT_TRANSLATE.value,
            "output": {},
            "error": f"Unsupported platform: {target_platform}. Supported: {list(PROMPT_ALCHEMY_PLATFORMS.keys())}",
            "metrics": None,
        }

    platform_config = PROMPT_ALCHEMY_PLATFORMS[target_platform]

    # Additional inputs
    style = _sanitize_text(inputs.get("style", "cinematic"), 100, "style")
    auteur_key = inputs.get("auteur_key", "")
    duration = inputs.get("duration", platform_config["max_duration"])
    language = _validate_enum(inputs.get("language", "ko"), ALLOWED_LANGUAGES, "language", "ko")
    model = _validate_enum(params.get("model", "gemini-3-flash-preview"), ALLOWED_MODELS, "model", "gemini-3-flash-preview")

    # RAG context for auteur style
    rag_context = None
    if auteur_key:
        rag_context = _get_rag_context(
            capsule_id=DimensionCapsuleId.PROMPT_TRANSLATE.value,
            query=f"{scene_description} {auteur_key} style",
            use_rag=True,
        )

    # Build translation prompt
    user_prompt = f"""Translate the following scene description into an optimized prompt for {platform_config['name']}.

## Scene Description:
{scene_description}

## Target Platform: {platform_config['name']}
## Visual Style: {style}
## Duration: {duration} seconds
## Language: {language}
{"## Auteur Reference: " + auteur_key if auteur_key else ""}

## Platform Template:
{platform_config['template']}

## Requirements:
1. Follow the platform template structure exactly
2. {"Include dialogue/narration markers" if platform_config.get("requires_dialogue") else "Remove any dialogue, focus on visual storytelling"}
3. Optimize for the platform's strengths
4. {"Add 'No subtitles.' at the end" if target_platform == "veo_31" else ""}

Return a JSON object with:
- "translated_prompt": The optimized prompt
- "quality_score": Your confidence (0-1)
- "platform_tips": Array of optimization tips
- "detected_elements": {{ "has_dialogue": bool, "is_animation": bool, "mood": str }}
"""

    if rag_context:
        user_prompt = _inject_rag_into_prompt(user_prompt, rag_context, position="prepend")

    try:
        result, metrics = await _call_gemini(
            prompt=user_prompt,
            system_prompt=PROMPT_ALCHEMY_SYSTEM,
            api_key=user_api_key,
            model=model,
        )

        # Ensure output structure
        output = result if isinstance(result, dict) else {"translated_prompt": str(result)}
        output["target_platform"] = target_platform
        output["platform_name"] = platform_config["name"]
        output["auto_selected"] = auto_select and not inputs.get("target_platform")
        output["max_duration"] = platform_config["max_duration"]
        output["native_audio"] = platform_config["native_audio"]

        return {
            "success": "error" not in result,
            "capsule_id": DimensionCapsuleId.PROMPT_TRANSLATE.value,
            "output": output,
            "error": result.get("error") if isinstance(result, dict) else None,
            "metrics": {
                "latency_ms": metrics.latency_ms,
                "tokens": metrics.input_tokens + metrics.output_tokens,
                "model": metrics.model,
                "intent_resolved": intent is not None,
                "platform": target_platform,
            },
        }
    except (TimeoutError, RuntimeError, ValueError) as e:
        return {
            "success": False,
            "capsule_id": DimensionCapsuleId.PROMPT_TRANSLATE.value,
            "output": {},
            "error": str(e),
            "metrics": None,
        }


# ============================================================================
# Main Entry Point
# ============================================================================

DIMENSION_ADAPTERS: Dict[str, Callable] = {
    DimensionCapsuleId.PROMPT_GENERATE.value: run_prompt_generator,
    DimensionCapsuleId.STORYBOARD_CREATE.value: run_storyboard_creator,
    DimensionCapsuleId.IMAGE_GENERATE.value: run_image_generator,
    DimensionCapsuleId.REFERENCE_ANALYZE.value: run_reference_analyzer,
    DimensionCapsuleId.QUALITY_CHECK.value: run_quality_checker,
    DimensionCapsuleId.AESTHETIC_DIRECT.value: run_aesthetic_director,
    DimensionCapsuleId.AESTHETIC_MOODBOARD.value: run_aesthetic_moodboard,
    DimensionCapsuleId.PERSONA_ANALYZE.value: run_persona_analyzer,
    DimensionCapsuleId.SOUND_MOODBOARD.value: run_sound_moodboard,
    DimensionCapsuleId.VEO_VIDEO_GENERATE.value: run_veo_generator,
    DimensionCapsuleId.VEO_VIDEO_GENERATE.value: run_veo_generator,
    # 4-Stage Workflow additions
    DimensionCapsuleId.STORY_ARCHITECT.value: run_story_architect,
    DimensionCapsuleId.STORY_REFINE.value: run_story_refinery,
    DimensionCapsuleId.SOUND_CRAFT.value: run_sound_crafter,
    DimensionCapsuleId.CREATIVE_EDITOR.value: run_creative_editor,
    DimensionCapsuleId.JSON_GEN_CONVERT.value: run_json_gen_convert,
    DimensionCapsuleId.NANOBANANA_CONVERT.value: run_nanobanana_convert,
    # Prompt Alchemy - AI Video Platform Prompt Translator
    DimensionCapsuleId.PROMPT_TRANSLATE.value: run_prompt_translator,
}


async def execute_dimension_capsule(
    capsule_id: str,
    inputs: Dict[str, Any],
    params: Optional[Dict[str, Any]] = None,
    user_api_key: Optional[str] = None,
) -> CapsuleResult:
    """Execute a dimension capsule.
    
    Args:
        capsule_id: Capsule identifier (e.g., "teaching.prompt.generate")
        inputs: Input data for the capsule
        params: Optional parameters (model, etc.)
        user_api_key: Optional user API key for BYOK mode
    
    Returns:
        CapsuleResult with success status, output, and metrics
    """
    params = params or {}
    
    # Validate capsule_id
    adapter = DIMENSION_ADAPTERS.get(capsule_id)
    if not adapter:
        valid_ids = [e.value for e in DimensionCapsuleId]
        return {
            "success": False,
            "capsule_id": capsule_id,
            "output": {},
            "error": f"Unknown capsule: {capsule_id}. Valid: {valid_ids}",
            "metrics": None,
        }
    
    logger.info(f"Executing dimension capsule: {capsule_id}")
    
    try:
        result = await adapter(inputs, params, user_api_key)
        
        if result["success"]:
            logger.info(f"Capsule {capsule_id} completed in {result.get('metrics', {}).get('latency_ms', '?')}ms")
        else:
            logger.warning(f"Capsule {capsule_id} failed: {result.get('error')}")
        
        return result
    except Exception as e:
        logger.exception(f"Unexpected error in capsule {capsule_id}")
        return {
            "success": False,
            "capsule_id": capsule_id,
            "output": {},
            "error": f"Internal error: {type(e).__name__}",
            "metrics": None,
        }
