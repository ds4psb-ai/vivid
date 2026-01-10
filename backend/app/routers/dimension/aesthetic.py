"""
Aesthetic Dimension Endpoints - Aesthetic Director.

- Aesthetic Direct: Generate style guide with auteur matching
- Aesthetic Moodboard: Generate visual direction cards
"""
from __future__ import annotations

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


# ============================================================================
# Request Models
# ============================================================================

class AestheticDirectRequest(BaseModel):
    """Request model for Aesthetic Director style guide generation."""
    concept: str = Field(..., min_length=1, max_length=MAX_CONCEPT_LENGTH, description="Visual concept")
    reference_style: str = Field("bong", max_length=100, description="Auteur reference style")
    mood: str = Field("cinematic", max_length=100, description="Visual mood")
    lighting_style: str = Field("natural", max_length=50, description="Lighting style (natural, high-key, low-key, dramatic, soft)")
    color_mood: str = Field("neutral", max_length=50, description="Color mood (neutral, warm, cool, desaturated, vibrant)")
    target_medium: str = Field("video", max_length=50, description="Target medium")
    use_rag: bool = Field(True, description="Use RAG for auteur knowledge")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("concept", "reference_style", "mood", "lighting_style", "color_mood", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class AestheticMoodboardRequest(BaseModel):
    """Request model for Aesthetic Moodboard generation."""
    concept: str = Field(..., min_length=1, max_length=MAX_CONCEPT_LENGTH, description="Visual concept")
    mood: str = Field("cinematic", max_length=100, description="Visual mood")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("concept", "mood", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return _strip_string(v)

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
    """Request model for AI Persona Analyzer."""
    subject: str = Field(..., min_length=1, max_length=1000, description="Subject to analyze")
    user_message: str = Field("", max_length=2000, description="User message in conversation")
    persona_data: dict = Field(default_factory=dict, description="Accumulated persona data")
    birth_info: dict = Field(default_factory=dict, description="Birth info for saju analysis")
    current_stage: str = Field("intro", description="Current analysis stage")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("subject", "user_message", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return _strip_string(v)

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
        params={"use_rag": False},
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
            params={"use_rag": False},
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
    """
    name: str = Field(..., min_length=1, max_length=100, description="Character name")
    role: str = Field(..., min_length=1, max_length=200, description="Character role (e.g., '48-year-old master chef')")
    personality: str = Field("", max_length=1000, description="Personality traits and behaviors")
    physical_traits: str = Field("", max_length=1000, description="Physical appearance details")
    wiki_context: str = Field("", max_length=5000, description="External context (Wiki, articles) about the character")
    style_reference: str = Field("anime", max_length=100, description="Visual style (anime, realistic, stylized)")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("name", "role", "personality", "physical_traits", "wiki_context", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return _strip_string(v)

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


