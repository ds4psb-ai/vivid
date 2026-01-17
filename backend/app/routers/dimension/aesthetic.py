"""
Aesthetic Dimension Endpoints - Aesthetic Director.

- Aesthetic Direct: Generate style guide with auteur matching
- Aesthetic Moodboard: Generate visual direction cards

Security:
- XSS sanitization for mood, style, and text fields
- Enum validation for lighting_style, color_mood, style_reference, target_medium
"""
from __future__ import annotations

import html
import logging
import re
from enum import Enum

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from ._base import (
    get_db,
    get_current_user,
    get_byok_key,
    _execute_dimension_tool,
    _execute_dimension_tool_stream,
    _validate_model,
    _strip_string,
    DimensionResponse,
    DimensionErrorResponse,
    DimensionCapsuleId,
    MAX_CONCEPT_LENGTH,
    get_sse_headers,
    Optional,
)

router = APIRouter()

# Module logger
aesthetic_logger = logging.getLogger(__name__)


# ============================================================================
# Constants & Enums
# ============================================================================

class LightingStyle(str, Enum):
    """Supported lighting styles for aesthetic direction."""
    NATURAL = "natural"
    HIGH_KEY = "high-key"
    LOW_KEY = "low-key"
    DRAMATIC = "dramatic"
    SOFT = "soft"


class ColorMood(str, Enum):
    """Supported color moods for aesthetic direction."""
    NEUTRAL = "neutral"
    WARM = "warm"
    COOL = "cool"
    DESATURATED = "desaturated"
    VIBRANT = "vibrant"


class StyleReference(str, Enum):
    """Supported visual style references for character DNA."""
    ANIME = "anime"
    REALISTIC = "realistic"
    STYLIZED = "stylized"
    CINEMATIC = "cinematic"


class PersonaStage(str, Enum):
    """Persona analysis stages."""
    INTRO = "intro"
    BIRTH = "birth"
    SAJU = "saju"
    SYNTHESIS = "synthesis"
    FINAL = "final"


ALLOWED_LIGHTING_STYLES = frozenset([s.value for s in LightingStyle])
ALLOWED_COLOR_MOODS = frozenset([c.value for c in ColorMood])
ALLOWED_STYLE_REFERENCES = frozenset([s.value for s in StyleReference])
ALLOWED_PERSONA_STAGES = frozenset([s.value for s in PersonaStage])
ALLOWED_TARGET_MEDIUMS = frozenset(["video", "image", "animation", "web", "print", "social"])


# ============================================================================
# Sanitization Helpers
# ============================================================================

def _sanitize_text_field(value: str, default: str = "") -> str:
    """Sanitize text fields to prevent XSS.

    Args:
        value: Raw text input
        default: Default value if empty

    Returns:
        Sanitized string
    """
    if not value:
        return default
    value = value.strip()
    if not value:
        return default
    # Remove HTML tags
    value = re.sub(r"<[^>]+>", "", value)
    # Escape HTML entities
    value = html.escape(value)
    # Remove script/javascript patterns
    value = re.sub(r"(?i)javascript\s*:", "", value)
    value = re.sub(r"(?i)on\w+\s*=", "", value)
    return value or default


def _validate_lighting_style(value: str) -> str:
    """Validate lighting style is in allowed list.

    Args:
        value: Raw lighting style

    Returns:
        Validated lighting style

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip().lower()
    if value not in ALLOWED_LIGHTING_STYLES:
        raise ValueError(
            f"Invalid lighting_style: {value}. Allowed: {sorted(ALLOWED_LIGHTING_STYLES)}"
        )
    return value


def _validate_color_mood(value: str) -> str:
    """Validate color mood is in allowed list.

    Args:
        value: Raw color mood

    Returns:
        Validated color mood

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip().lower()
    if value not in ALLOWED_COLOR_MOODS:
        raise ValueError(
            f"Invalid color_mood: {value}. Allowed: {sorted(ALLOWED_COLOR_MOODS)}"
        )
    return value


def _validate_style_reference(value: str) -> str:
    """Validate style reference is in allowed list.

    Args:
        value: Raw style reference

    Returns:
        Validated style reference

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip().lower()
    if value not in ALLOWED_STYLE_REFERENCES:
        raise ValueError(
            f"Invalid style_reference: {value}. Allowed: {sorted(ALLOWED_STYLE_REFERENCES)}"
        )
    return value


def _validate_target_medium(value: str) -> str:
    """Validate target medium is in allowed list.

    Args:
        value: Raw target medium

    Returns:
        Validated target medium

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip().lower()
    if value not in ALLOWED_TARGET_MEDIUMS:
        raise ValueError(
            f"Invalid target_medium: {value}. Allowed: {sorted(ALLOWED_TARGET_MEDIUMS)}"
        )
    return value


def _validate_persona_stage(value: str) -> str:
    """Validate persona stage is in allowed list.

    Args:
        value: Raw persona stage

    Returns:
        Validated persona stage

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip().lower()
    if value not in ALLOWED_PERSONA_STAGES:
        raise ValueError(
            f"Invalid current_stage: {value}. Allowed: {sorted(ALLOWED_PERSONA_STAGES)}"
        )
    return value


# ============================================================================
# Request Models
# ============================================================================

class AestheticDirectRequest(BaseModel):
    """Request model for Aesthetic Director style guide generation.

    Includes:
    - XSS sanitization for concept, reference_style, mood
    - Enum validation for lighting_style, color_mood, target_medium
    """
    concept: str = Field(..., min_length=1, max_length=MAX_CONCEPT_LENGTH, description="Visual concept (sanitized)")
    reference_style: str = Field("bong", max_length=100, description="Auteur reference style (sanitized)")
    mood: str = Field("cinematic", max_length=100, description="Visual mood (sanitized)")
    lighting_style: str = Field("natural", max_length=50, description="Lighting style: natural, high-key, low-key, dramatic, soft")
    color_mood: str = Field("neutral", max_length=50, description="Color mood: neutral, warm, cool, desaturated, vibrant")
    target_medium: str = Field("video", max_length=50, description="Target medium: video, image, animation, web, print, social")
    use_rag: bool = Field(True, description="Use RAG for auteur knowledge")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("concept", mode="before")
    @classmethod
    def sanitize_concept(cls, v: str) -> str:
        """Sanitize concept to prevent XSS."""
        return _sanitize_text_field(v)

    @field_validator("reference_style", mode="before")
    @classmethod
    def sanitize_reference_style(cls, v: str) -> str:
        """Sanitize reference_style to prevent XSS."""
        return _sanitize_text_field(v, default="bong")

    @field_validator("mood", mode="before")
    @classmethod
    def sanitize_mood(cls, v: str) -> str:
        """Sanitize mood to prevent XSS."""
        return _sanitize_text_field(v, default="cinematic")

    @field_validator("lighting_style")
    @classmethod
    def validate_lighting_style(cls, v: str) -> str:
        """Validate lighting_style is in allowed list."""
        return _validate_lighting_style(v)

    @field_validator("color_mood")
    @classmethod
    def validate_color_mood(cls, v: str) -> str:
        """Validate color_mood is in allowed list."""
        return _validate_color_mood(v)

    @field_validator("target_medium")
    @classmethod
    def validate_target_medium(cls, v: str) -> str:
        """Validate target_medium is in allowed list."""
        return _validate_target_medium(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class AestheticMoodboardRequest(BaseModel):
    """Request model for Aesthetic Moodboard generation.

    Includes:
    - XSS sanitization for concept and mood
    """
    concept: str = Field(..., min_length=1, max_length=MAX_CONCEPT_LENGTH, description="Visual concept (sanitized)")
    mood: str = Field("cinematic", max_length=100, description="Visual mood (sanitized)")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("concept", mode="before")
    @classmethod
    def sanitize_concept(cls, v: str) -> str:
        """Sanitize concept to prevent XSS."""
        return _sanitize_text_field(v)

    @field_validator("mood", mode="before")
    @classmethod
    def sanitize_mood(cls, v: str) -> str:
        """Sanitize mood to prevent XSS."""
        return _sanitize_text_field(v, default="cinematic")

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


# ============================================================================
# Aesthetic Direct
# ============================================================================

@router.post(
    "/aesthetic/direct",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Aesthetic Director: Generate Style Guide",
    description="Generate visual style guidelines with auteur matching.",
    tags=["Dimension Extended"],
)
async def direct_aesthetic(
    request: AestheticDirectRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Generate aesthetic style guide with Intent-Resolver integration."""
    user_id = user.get("id", "unknown")
    aesthetic_logger.info(
        f"[AESTHETIC_DIRECT] user={user_id} concept_len={len(request.concept)} "
        f"style={request.reference_style} lighting={request.lighting_style} "
        f"color={request.color_mood} medium={request.target_medium}"
    )

    from app.routers.intent_helpers import infer_intent_for_aesthetic
    intent = infer_intent_for_aesthetic(
        concept=request.concept,
        mood=request.mood,
        reference_style=request.reference_style,
        target_medium=request.target_medium,
    )
    
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.AESTHETIC_DIRECT,
        tool_key="aesthetic_direct",
        inputs={
            "concept": request.concept,
            "reference_style": request.reference_style,
            "mood": request.mood,
            "lighting_style": request.lighting_style,
            "color_mood": request.color_mood,
            "target_medium": request.target_medium,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"concept": request.concept[:100], "style": request.reference_style, "lighting": request.lighting_style},
        params={"use_rag": request.use_rag},
        intent=intent,
    )


@router.post(
    "/aesthetic/direct/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Aesthetic Director: Generate Style Guide (SSE Stream)",
    description="Generate visual style guidelines with real-time progress updates via SSE.",
    tags=["Dimension Extended"],
)
async def direct_aesthetic_stream(
    request: AestheticDirectRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Generate aesthetic style guide with SSE streaming."""
    user_id = user.get("id", "unknown")
    aesthetic_logger.info(
        f"[AESTHETIC_DIRECT_STREAM] user={user_id} concept_len={len(request.concept)} "
        f"style={request.reference_style} lighting={request.lighting_style}"
    )

    from app.routers.intent_helpers import infer_intent_for_aesthetic
    intent = infer_intent_for_aesthetic(
        concept=request.concept,
        mood=request.mood,
        reference_style=request.reference_style,
        target_medium=request.target_medium,
    )
    
    return StreamingResponse(
        _execute_dimension_tool_stream(
            capsule_id=DimensionCapsuleId.AESTHETIC_DIRECT,
            tool_key="aesthetic_direct",
            operation_name="스타일 가이드 생성",
            inputs={
                "concept": request.concept,
                "reference_style": request.reference_style,
                "mood": request.mood,
                "lighting_style": request.lighting_style,
                "color_mood": request.color_mood,
                "target_medium": request.target_medium,
            },
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={"concept": request.concept[:100], "style": request.reference_style, "lighting": request.lighting_style},
            params={"use_rag": request.use_rag},
            intent=intent,
        ),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


# ============================================================================
# Aesthetic Moodboard
# ============================================================================

@router.post(
    "/aesthetic/moodboard",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Aesthetic Director: Generate Mood Board",
    description="Stage 1: Generate 3 distinct visual direction cards.",
    tags=["Dimension Extended"],
)
async def generate_aesthetic_moodboard(
    request: AestheticMoodboardRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Generate visual direction cards with Intent-Resolver integration."""
    user_id = user.get("id", "unknown")
    aesthetic_logger.info(
        f"[AESTHETIC_MOODBOARD] user={user_id} concept_len={len(request.concept)} mood={request.mood}"
    )

    from app.routers.intent_helpers import with_intent
    intent = with_intent(request, "aesthetic")
    
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.AESTHETIC_MOODBOARD,
        tool_key="aesthetic_moodboard",
        inputs={
            "concept": request.concept,
            "mood": request.mood,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"concept": request.concept[:100], "mood": request.mood},
        intent=intent,
    )


@router.post(
    "/aesthetic/moodboard/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Aesthetic Director: Generate Mood Board (SSE Stream)",
    description="Generate mood board with real-time progress updates via SSE.",
    tags=["Dimension Extended"],
)
async def generate_aesthetic_moodboard_stream(
    request: AestheticMoodboardRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Generate visual direction cards with SSE streaming."""
    user_id = user.get("id", "unknown")
    aesthetic_logger.info(
        f"[AESTHETIC_MOODBOARD_STREAM] user={user_id} concept_len={len(request.concept)} mood={request.mood}"
    )

    from app.routers.intent_helpers import with_intent
    intent = with_intent(request, "aesthetic")
    
    return StreamingResponse(
        _execute_dimension_tool_stream(
            capsule_id=DimensionCapsuleId.AESTHETIC_MOODBOARD,
            tool_key="aesthetic_moodboard",
            operation_name="무드보드 생성",
            inputs={
                "concept": request.concept,
                "mood": request.mood,
            },
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={"concept": request.concept[:100], "mood": request.mood},
            intent=intent,
        ),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


# ============================================================================
# AI Persona Analyzer (Abyss Interpreter)
# ============================================================================

class PersonaAnalyzeRequest(BaseModel):
    """Request model for AI Persona Analyzer.

    Includes:
    - XSS sanitization for subject and user_message
    - Enum validation for current_stage
    """
    subject: str = Field(..., min_length=1, max_length=1000, description="Subject to analyze (sanitized)")
    user_message: str = Field("", max_length=2000, description="User message in conversation (sanitized)")
    persona_data: dict = Field(default_factory=dict, description="Accumulated persona data")
    birth_info: dict = Field(default_factory=dict, description="Birth info for saju analysis")
    current_stage: str = Field("intro", description="Current analysis stage: intro, birth, saju, synthesis, final")
    model: str = Field("gemini-3-flash-preview", description="AI model")
    params: dict = Field(default_factory=dict, description="Additional parameters (depth_level, etc.)")

    @field_validator("subject", mode="before")
    @classmethod
    def sanitize_subject(cls, v: str) -> str:
        """Sanitize subject to prevent XSS."""
        return _sanitize_text_field(v)

    @field_validator("user_message", mode="before")
    @classmethod
    def sanitize_user_message(cls, v: str) -> str:
        """Sanitize user_message to prevent XSS."""
        return _sanitize_text_field(v, default="")

    @field_validator("current_stage")
    @classmethod
    def validate_current_stage(cls, v: str) -> str:
        """Validate current_stage is in allowed list."""
        return _validate_persona_stage(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


@router.post(
    "/persona/analyze",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="AI Persona: Abyss Interpreter",
    description="Analyze creative persona through deep psychology interpretation.",
    tags=["Dimension Extended"],
)
async def analyze_persona(
    request: PersonaAnalyzeRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Analyze persona with Intent-Resolver integration."""
    user_id = user.get("id", "unknown")
    aesthetic_logger.info(
        f"[PERSONA_ANALYZE] user={user_id} subject_len={len(request.subject)} stage={request.current_stage}"
    )

    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.PERSONA_ANALYZE,
        tool_key="persona_analyze",
        inputs={
            "subject": request.subject,
            "user_message": request.user_message,
            "persona_data": request.persona_data,
            "birth_info": request.birth_info,
            "current_stage": request.current_stage,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"subject": request.subject[:100], "stage": request.current_stage},
        params=request.params,
    )


@router.post(
    "/persona/analyze/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="AI Persona: Abyss Interpreter (SSE Stream)",
    description="Analyze creative persona with real-time progress updates via SSE.",
    tags=["Dimension Extended"],
)
async def analyze_persona_stream(
    request: PersonaAnalyzeRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Analyze persona with SSE streaming."""
    user_id = user.get("id", "unknown")
    aesthetic_logger.info(
        f"[PERSONA_ANALYZE_STREAM] user={user_id} subject_len={len(request.subject)} stage={request.current_stage}"
    )

    return StreamingResponse(
        _execute_dimension_tool_stream(
            capsule_id=DimensionCapsuleId.PERSONA_ANALYZE,
            tool_key="persona_analyze",
            operation_name="페르소나 분석",
            inputs={
                "subject": request.subject,
                "user_message": request.user_message,
                "persona_data": request.persona_data,
                "birth_info": request.birth_info,
                "current_stage": request.current_stage,
            },
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={"subject": request.subject[:100], "stage": request.current_stage},
            params=request.params,
        ),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


# ============================================================================
# Character DNA Generator (Expert Workflow Pattern)
# ============================================================================

class CharacterDNARequest(BaseModel):
    """Request model for Character DNA generation.

    Generates a reusable "Visual DNA" prompt string for character consistency,
    following the Expert Workflow pattern.

    Includes:
    - XSS sanitization for name, role, personality, physical_traits, wiki_context
    - Enum validation for style_reference
    """
    name: str = Field(..., min_length=1, max_length=100, description="Character name (sanitized)")
    role: str = Field(..., min_length=1, max_length=200, description="Character role (sanitized)")
    personality: str = Field("", max_length=1000, description="Personality traits and behaviors (sanitized)")
    physical_traits: str = Field("", max_length=1000, description="Physical appearance details (sanitized)")
    wiki_context: str = Field("", max_length=5000, description="External context (sanitized)")
    style_reference: str = Field("anime", max_length=100, description="Visual style: anime, realistic, stylized, cinematic")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("name", mode="before")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        """Sanitize name to prevent XSS."""
        return _sanitize_text_field(v)

    @field_validator("role", mode="before")
    @classmethod
    def sanitize_role(cls, v: str) -> str:
        """Sanitize role to prevent XSS."""
        return _sanitize_text_field(v)

    @field_validator("personality", mode="before")
    @classmethod
    def sanitize_personality(cls, v: str) -> str:
        """Sanitize personality to prevent XSS."""
        return _sanitize_text_field(v, default="")

    @field_validator("physical_traits", mode="before")
    @classmethod
    def sanitize_physical_traits(cls, v: str) -> str:
        """Sanitize physical_traits to prevent XSS."""
        return _sanitize_text_field(v, default="")

    @field_validator("wiki_context", mode="before")
    @classmethod
    def sanitize_wiki_context(cls, v: str) -> str:
        """Sanitize wiki_context to prevent XSS."""
        return _sanitize_text_field(v, default="")

    @field_validator("style_reference")
    @classmethod
    def validate_style_reference(cls, v: str) -> str:
        """Validate style_reference is in allowed list."""
        return _validate_style_reference(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class CharacterDNAResponse(BaseModel):
    """Response for Character DNA generation."""
    success: bool
    character_name: str
    character_dna: str  # The reusable prompt string
    style_prompt: str   # Style-specific prefix
    full_prompt: str    # Combined: style + dna
    usage_hint: str


@router.post(
    "/aesthetic/character-dna",
    response_model=CharacterDNAResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        500: {"model": DimensionErrorResponse},
    },
    summary="Character DNA: Generate Visual DNA",
    description="Generate a reusable 'Visual DNA' prompt string for consistent character generation across multiple images/videos.",
    tags=["Dimension Extended"],
)
async def generate_character_dna(
    request: CharacterDNARequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
) -> CharacterDNAResponse:
    """Generate Character DNA following the Expert Workflow pattern.

    Creates a detailed, reusable prompt string that captures:
    1. Physical traits (age, build, distinguishing features)
    2. Personality traits (how they move, speak, express)
    3. Costume/Style details
    4. Performance notes
    
    Usage: Prepend this DNA string to every image/video prompt
    to maintain character consistency.
    """
    user_id = user.get("id", "unknown")
    aesthetic_logger.info(
        f"[CHARACTER_DNA] user={user_id} name={request.name} role_len={len(request.role)} "
        f"style={request.style_reference}"
    )

    from google import genai
    from google.genai import types
    from app.config import settings
    
    # Build context from inputs
    context_parts = []
    if request.wiki_context:
        context_parts.append(f"### External Context (Wiki/Research)\n{request.wiki_context}")
    if request.physical_traits:
        context_parts.append(f"### Physical Traits\n{request.physical_traits}")
    if request.personality:
        context_parts.append(f"### Personality\n{request.personality}")
    
    context_block = "\n\n".join(context_parts) if context_parts else ""
    
    # System prompt for Character DNA generation
    system_prompt = """You are a Character Design Expert for AI image/video generation.
Generate a "Visual DNA" prompt string that will be REUSED across all generations.

The output should be a SINGLE BLOCK of descriptive text (not JSON) that can be
copy-pasted as a prompt prefix. It should capture TWO layers:

LAYER 1: VISUAL PERCEPTION (Pixels)
- Physical details (age, gender, build, skin tone)
- Costume/Texture (clothing, accessories, colors)

LAYER 2: PSYCHOLOGICAL ACTING (Motion/Vibe)
- "Appears awkward/inarticulate" (Acting direction)
- "Thinking faster than speaking" (Subtext)
- "Subtle intensity beneath gentle exterior" (Micro-expression)

The output should read like this example:
"48-year-old male chef character, quiet and introverted master craftsman type,
appears awkward and inarticulate when speaking, often hesitates mid-sentence,
calm eyes, reserved expression, subtle intensity beneath a gentle exterior,
white chef uniform with subtle stains from work, strong weathered hands,
gives the impression of someone constantly searching for the right word."

DO NOT include:
- JSON formatting
- Numbered lists
- Headers or sections
- Style instructions (that's separate)

JUST the character description as a continuous prompt string that combines visual and psychological traits."""

    user_prompt = f"""Create a Visual DNA prompt string for:

Character Name: {request.name}
Role: {request.role}
Visual Style Target: {request.style_reference}

{context_block}

Generate a detailed, reusable character prompt string."""

    try:
        api_key = byok_key or settings.GEMINI_API_KEY
        client = genai.Client(api_key=api_key)
        
        response = await client.aio.models.generate_content(
            model=request.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
            ),
        )
        
        character_dna = response.text.strip()
        
        # Generate style-specific prefix based on style_reference
        style_prompts = {
            "anime": "Japanese TV anime style illustration, clean and sharp lineart, thin and consistent black outlines, digital cel-shaded coloring, large expressive anime eyes, anime-style hair with large defined clumps, high saturation, modern anime screenshot look, no realism, no 3D",
            "realistic": "Photorealistic style, natural lighting, detailed skin texture, realistic proportions, cinematic composition, shallow depth of field, professional photography look",
            "stylized": "Stylized digital art, bold colors, strong silhouettes, graphic design aesthetics, clean lines, modern illustration style",
            "cinematic": "Cinematic film still, anamorphic lens, movie color grading, dramatic lighting, professional cinematography, 35mm film texture",
        }
        
        style_prompt = style_prompts.get(
            request.style_reference.lower(),
            style_prompts["cinematic"]
        )
        
        # Combine for full prompt
        full_prompt = f"{style_prompt}, {character_dna}"
        
        return CharacterDNAResponse(
            success=True,
            character_name=request.name,
            character_dna=character_dna,
            style_prompt=style_prompt,
            full_prompt=full_prompt,
            usage_hint="Copy the 'full_prompt' and use it as a prefix for all image/video generations of this character.",
        )
        
    except Exception as e:
        return CharacterDNAResponse(
            success=False,
            character_name=request.name,
            character_dna="",
            style_prompt="",
            full_prompt="",
            usage_hint=f"Error: {str(e)}",
        )


