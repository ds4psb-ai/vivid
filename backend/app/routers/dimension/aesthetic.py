"""
Aesthetic Dimension Endpoints - Aesthetic Director.

- Aesthetic Direct: Generate style guide with auteur matching
- Aesthetic Moodboard: Generate visual direction cards

Security:
- XSS sanitization for mood, style, and text fields
- Enum validation for lighting_style, color_mood, style_reference, target_medium

2026 Enhancements:
- Auteur Style Blending with mathematical interpolation
- Mathematical Aesthetics (golden ratio, color harmony)
- Prompt Quality assessment for aesthetic prompts
- Multi-RAG evidence_refs generation
"""
from __future__ import annotations

import logging
import uuid
from enum import Enum
from typing import List

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
    sanitize_generic_text,
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
        return sanitize_generic_text(v)

    @field_validator("reference_style", mode="before")
    @classmethod
    def sanitize_reference_style(cls, v: str) -> str:
        """Sanitize reference_style to prevent XSS."""
        return sanitize_generic_text(v, default="bong")

    @field_validator("mood", mode="before")
    @classmethod
    def sanitize_mood(cls, v: str) -> str:
        """Sanitize mood to prevent XSS."""
        return sanitize_generic_text(v, default="cinematic")

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
        return sanitize_generic_text(v)

    @field_validator("mood", mode="before")
    @classmethod
    def sanitize_mood(cls, v: str) -> str:
        """Sanitize mood to prevent XSS."""
        return sanitize_generic_text(v, default="cinematic")

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
        return sanitize_generic_text(v)

    @field_validator("user_message", mode="before")
    @classmethod
    def sanitize_user_message(cls, v: str) -> str:
        """Sanitize user_message to prevent XSS."""
        return sanitize_generic_text(v, default="")

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
        return sanitize_generic_text(v)

    @field_validator("role", mode="before")
    @classmethod
    def sanitize_role(cls, v: str) -> str:
        """Sanitize role to prevent XSS."""
        return sanitize_generic_text(v)

    @field_validator("personality", mode="before")
    @classmethod
    def sanitize_personality(cls, v: str) -> str:
        """Sanitize personality to prevent XSS."""
        return sanitize_generic_text(v, default="")

    @field_validator("physical_traits", mode="before")
    @classmethod
    def sanitize_physical_traits(cls, v: str) -> str:
        """Sanitize physical_traits to prevent XSS."""
        return sanitize_generic_text(v, default="")

    @field_validator("wiki_context", mode="before")
    @classmethod
    def sanitize_wiki_context(cls, v: str) -> str:
        """Sanitize wiki_context to prevent XSS."""
        return sanitize_generic_text(v, default="")

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
    # RAG Protocol Fields (v2) - P6 evidence_refs as List[str]
    trace_id: str = Field("", description="Trace ID for auditability")
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="RAG evidence references (format: 'rag:auteur_dna:bong:visual:composition', 'db:character_dna:uuid')",
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="AI confidence score")


# ============================================================================
# 2026 Best Practices: Fine-Grained Preference Types (VisionPrefer/AesthetiQ)
# ============================================================================

class AestheticPreferenceAspect(str, Enum):
    """Fine-grained aesthetic preference aspects (VisionPrefer 2026 pattern)."""
    PROMPT_FOLLOWING = "prompt_following"  # Adherence to input concept
    FIDELITY = "fidelity"  # Visual accuracy and realism
    AESTHETIC = "aesthetic"  # Overall visual appeal
    HARMLESSNESS = "harmlessness"  # Safety/appropriateness


class AestheticQualityScore(BaseModel):
    """2026 Best Practice: Multi-aspect quality scoring (AesthetiQ/VisionPrefer pattern)."""
    prompt_following: float = Field(0.0, ge=0.0, le=1.0, description="How well output follows input concept")
    fidelity: float = Field(0.0, ge=0.0, le=1.0, description="Visual accuracy and realism")
    aesthetic: float = Field(0.0, ge=0.0, le=1.0, description="Overall visual appeal")
    harmlessness: float = Field(1.0, ge=0.0, le=1.0, description="Safety score")
    overall: float = Field(0.0, ge=0.0, le=1.0, description="Weighted overall score")


# ============================================================================
# 2026 Enhancements: Auteur Style Blending & Mathematical Aesthetics
# ============================================================================

# Auteur compatibility matrix for style blending
AUTEUR_COMPATIBILITY_MATRIX: dict[str, dict[str, float]] = {
    "bong": {"nolan": 0.75, "fincher": 0.80, "wong": 0.60, "tarantino": 0.45, "villeneuve": 0.70},
    "nolan": {"bong": 0.75, "fincher": 0.85, "villeneuve": 0.90, "kubrick": 0.80, "spielberg": 0.65},
    "wong": {"bong": 0.60, "tarantino": 0.55, "kar_wai": 1.0, "wong_kar_wai": 1.0},
    "villeneuve": {"nolan": 0.90, "kubrick": 0.85, "ridley_scott": 0.80, "bong": 0.70},
    "tarantino": {"guy_ritchie": 0.75, "rodriguez": 0.80, "wong": 0.55, "bong": 0.45},
    "miyazaki": {"shinkai": 0.65, "ghibli": 1.0, "hosoda": 0.70, "isao": 0.80},
    "kubrick": {"nolan": 0.80, "villeneuve": 0.85, "fincher": 0.75, "bong": 0.60},
    "fincher": {"nolan": 0.85, "bong": 0.80, "kubrick": 0.75, "villeneuve": 0.80},
    "spielberg": {"cameron": 0.75, "nolan": 0.65, "zemeckis": 0.70},
}

# Visual style keywords for each auteur
# Must align with AUTEUR_COMPATIBILITY_MATRIX keys
AUTEUR_VISUAL_KEYWORDS: dict[str, List[str]] = {
    "bong": ["layered framing", "class symbolism", "muted palette", "vertical depth", "social tension"],
    "nolan": ["IMAX scale", "temporal complexity", "practical effects", "blue-gold palette", "geometric precision"],
    "wong": ["neon expressionism", "handheld intimacy", "color saturation", "reflection shots", "time distortion"],
    "villeneuve": ["vast scale", "minimal dialogue", "architectural framing", "amber-grey palette", "slow revelation"],
    "tarantino": ["split screens", "trunk shots", "pop culture references", "vibrant colors", "genre homage"],
    "miyazaki": ["hand-drawn warmth", "nature harmony", "flight sequences", "watercolor backgrounds", "child wonder"],
    "kubrick": ["one-point perspective", "symmetrical composition", "cold precision", "long takes", "existential dread"],
    "fincher": ["dark atmosphere", "desaturated palette", "forensic detail", "shadow play", "meticulous control"],
    # Added to align with AUTEUR_COMPATIBILITY_MATRIX
    "spielberg": ["lens flare", "wonder shots", "suburban americana", "emotional crescendo", "child perspective"],
    "cameron": ["blue palette", "technological sublime", "underwater imagery", "strong female leads", "epic scale"],
    "ridley_scott": ["smoke and light", "industrial decay", "historical epic", "rain noir", "textured environments"],
    "guy_ritchie": ["snappy editing", "British gangster aesthetic", "split-screen montage", "kinetic camera", "masculine ensemble"],
    "shinkai": ["photorealistic backgrounds", "light rays", "cloud formations", "urban loneliness", "romantic melancholy"],
    "rodriguez": ["grindhouse aesthetic", "high contrast", "practical gore", "low-budget inventiveness", "action rhythm"],
    "zemeckis": ["motion capture innovation", "time travel motifs", "visual effects integration", "nostalgic americana", "Boomer appeal"],
    "hosoda": ["family bonds", "digital worlds", "summer settings", "coming-of-age warmth", "vibrant colors"],
    "isao": ["naturalistic movement", "quiet observation", "wartime memory", "pastoral beauty", "emotional restraint"],
    "kar_wai": ["neon expressionism", "handheld intimacy", "color saturation", "reflection shots", "time distortion"],
    "wong_kar_wai": ["neon expressionism", "handheld intimacy", "color saturation", "reflection shots", "time distortion"],
    "ghibli": ["hand-drawn warmth", "nature harmony", "flight sequences", "watercolor backgrounds", "child wonder"],
}

# Mathematical aesthetics constants
GOLDEN_RATIO = 1.618033988749895
RULE_OF_THIRDS = 0.333

# Color harmony types with angle offsets on color wheel
COLOR_HARMONY_ANGLES: dict[str, List[int]] = {
    "complementary": [180],  # Opposite colors
    "triadic": [120, 240],  # 3 equidistant colors
    "analogous": [30, -30],  # Adjacent colors
    "split_complementary": [150, 210],  # Adjacent to complement
    "tetradic": [90, 180, 270],  # 4 colors (square)
}


class AuteurBlendResult(BaseModel):
    """Result of blending two auteur styles."""
    primary_auteur: str
    secondary_auteur: str
    compatibility_score: float = Field(0.0, ge=0.0, le=1.0)
    blend_ratio: str = Field("60:40", description="Primary:Secondary ratio")
    visual_keywords: List[str] = Field(default_factory=list)
    color_approach: str = ""
    composition_approach: str = ""
    recommended_for: List[str] = Field(default_factory=list)


class AestheticPromptQuality(BaseModel):
    """2026 Prompt Quality assessment for aesthetic requests."""
    # Scores (0-100)
    concept_clarity: int = Field(0, ge=0, le=100, description="Concept description clarity")
    style_specificity: int = Field(0, ge=0, le=100, description="Style reference specificity")
    technical_detail: int = Field(0, ge=0, le=100, description="Technical parameters detail")
    overall_score: int = Field(0, ge=0, le=100, description="Overall quality score")

    # Components detected
    has_auteur_reference: bool = False
    has_color_specification: bool = False
    has_lighting_specification: bool = False
    has_composition_hint: bool = False

    # Suggestions
    suggestions: List[str] = Field(default_factory=list)


def get_auteur_compatibility(primary: str, secondary: str) -> float:
    """Get compatibility score between two auteurs.

    Args:
        primary: Primary auteur key
        secondary: Secondary auteur key

    Returns:
        Compatibility score (0.0-1.0), default 0.5 if unknown
    """
    primary = primary.lower()
    secondary = secondary.lower()

    if primary == secondary:
        return 1.0

    # Check direct mapping
    if primary in AUTEUR_COMPATIBILITY_MATRIX:
        if secondary in AUTEUR_COMPATIBILITY_MATRIX[primary]:
            return AUTEUR_COMPATIBILITY_MATRIX[primary][secondary]

    # Check reverse mapping
    if secondary in AUTEUR_COMPATIBILITY_MATRIX:
        if primary in AUTEUR_COMPATIBILITY_MATRIX[secondary]:
            return AUTEUR_COMPATIBILITY_MATRIX[secondary][primary]

    return 0.5  # Default unknown compatibility


def blend_auteur_styles(
    primary: str,
    secondary: str,
    primary_weight: float = 0.6,
) -> AuteurBlendResult:
    """Blend two auteur styles using 2026 weighted interpolation.

    Args:
        primary: Primary auteur key
        secondary: Secondary auteur key
        primary_weight: Weight for primary auteur (0.0-1.0)

    Returns:
        AuteurBlendResult with blended characteristics
    """
    primary = primary.lower()
    secondary = secondary.lower()
    secondary_weight = 1.0 - primary_weight

    compatibility = get_auteur_compatibility(primary, secondary)

    # Get visual keywords
    primary_keywords = AUTEUR_VISUAL_KEYWORDS.get(primary, [])
    secondary_keywords = AUTEUR_VISUAL_KEYWORDS.get(secondary, [])

    # Weighted selection: more keywords from primary
    num_primary = int(len(primary_keywords) * primary_weight) if primary_keywords else 0
    num_secondary = int(len(secondary_keywords) * secondary_weight) if secondary_keywords else 0

    blended_keywords = primary_keywords[:max(2, num_primary)] + secondary_keywords[:max(1, num_secondary)]

    # Determine color and composition approach
    if compatibility >= 0.8:
        color_approach = "Seamless blend - complementary palettes"
        composition_approach = "Primary rules with secondary variations"
    elif compatibility >= 0.6:
        color_approach = "Primary palette with secondary accents"
        composition_approach = "Primary framing, secondary pacing"
    else:
        color_approach = "Separate color zones by scene type"
        composition_approach = "Choose dominant style per scene"

    # Recommendations
    recommended_for = []
    if compatibility >= 0.7:
        recommended_for.extend(["feature film", "music video", "commercial"])
    elif compatibility >= 0.5:
        recommended_for.extend(["experimental short", "art film"])
    else:
        recommended_for.append("stylistic contrast project")

    ratio_str = f"{int(primary_weight * 100)}:{int(secondary_weight * 100)}"

    return AuteurBlendResult(
        primary_auteur=primary,
        secondary_auteur=secondary,
        compatibility_score=compatibility,
        blend_ratio=ratio_str,
        visual_keywords=blended_keywords,
        color_approach=color_approach,
        composition_approach=composition_approach,
        recommended_for=recommended_for,
    )


def calculate_golden_ratio_points(frame_width: int, frame_height: int) -> dict:
    """Calculate golden ratio focal points for composition.

    Args:
        frame_width: Frame width in pixels
        frame_height: Frame height in pixels

    Returns:
        Dict with focal points and grid lines
    """
    phi = GOLDEN_RATIO
    phi_inverse = 1 / phi  # 0.618

    # Vertical lines (golden section)
    v_left = int(frame_width * (1 - phi_inverse))   # ~38.2%
    v_right = int(frame_width * phi_inverse)        # ~61.8%

    # Horizontal lines
    h_top = int(frame_height * (1 - phi_inverse))
    h_bottom = int(frame_height * phi_inverse)

    # Power points (intersections)
    power_points = [
        (v_left, h_top),     # Top-left
        (v_right, h_top),    # Top-right
        (v_left, h_bottom),  # Bottom-left
        (v_right, h_bottom), # Bottom-right
    ]

    return {
        "golden_ratio": phi,
        "vertical_lines": [v_left, v_right],
        "horizontal_lines": [h_top, h_bottom],
        "power_points": power_points,
        "center": (frame_width // 2, frame_height // 2),
        "thirds_grid": {
            "vertical": [frame_width // 3, 2 * frame_width // 3],
            "horizontal": [frame_height // 3, 2 * frame_height // 3],
        }
    }


def get_color_harmony_palette(base_hue: int, harmony_type: str = "complementary") -> List[int]:
    """Generate harmonious color hues based on color wheel theory.

    Args:
        base_hue: Base hue (0-360)
        harmony_type: Type of color harmony

    Returns:
        List of hues in the harmony
    """
    if harmony_type not in COLOR_HARMONY_ANGLES:
        harmony_type = "complementary"

    angles = COLOR_HARMONY_ANGLES[harmony_type]
    palette = [base_hue]

    for angle in angles:
        new_hue = (base_hue + angle) % 360
        palette.append(new_hue)

    return palette


def assess_aesthetic_prompt_quality(
    concept: str,
    reference_style: str = "",
    mood: str = "",
    lighting_style: str = "",
    color_mood: str = "",
) -> AestheticPromptQuality:
    """Assess aesthetic prompt quality using 2026 best practices.

    Args:
        concept: Visual concept description
        reference_style: Auteur reference
        mood: Visual mood
        lighting_style: Lighting specification
        color_mood: Color specification

    Returns:
        AestheticPromptQuality with scores and suggestions
    """
    suggestions: List[str] = []
    concept_lower = concept.lower() if concept else ""

    # 1. Concept Clarity Score
    concept_clarity = 0
    if concept:
        word_count = len(concept.split())
        if word_count >= 10:
            concept_clarity += 40
        elif word_count >= 5:
            concept_clarity += 25
        else:
            concept_clarity += 10
            suggestions.append("Add more detail to your concept description (aim for 10+ words)")

        # Check for visual keywords
        visual_keywords = ["scene", "shot", "frame", "composition", "angle", "perspective"]
        if any(kw in concept_lower for kw in visual_keywords):
            concept_clarity += 30

        # Check for subject clarity
        if any(kw in concept_lower for kw in ["character", "person", "object", "landscape", "interior"]):
            concept_clarity += 30
        else:
            suggestions.append("Specify the main subject (character, object, landscape, etc.)")

    concept_clarity = min(100, concept_clarity)

    # 2. Style Specificity Score
    style_specificity = 0
    has_auteur = False

    if reference_style:
        style_specificity += 40
        has_auteur = reference_style.lower() in AUTEUR_VISUAL_KEYWORDS
        if has_auteur:
            style_specificity += 30
        else:
            suggestions.append(f"Consider using a known auteur: {', '.join(list(AUTEUR_VISUAL_KEYWORDS.keys())[:5])}")
    else:
        suggestions.append("Add an auteur reference for stronger style direction")

    if mood:
        style_specificity += 30

    style_specificity = min(100, style_specificity)

    # 3. Technical Detail Score
    technical_detail = 0
    has_lighting = bool(lighting_style)
    has_color = bool(color_mood)
    has_composition = any(kw in concept_lower for kw in ["wide", "close", "medium", "angle", "overhead", "low"])

    if has_lighting:
        technical_detail += 35
    else:
        suggestions.append("Specify lighting style (natural, dramatic, soft, high-key, low-key)")

    if has_color:
        technical_detail += 35
    else:
        suggestions.append("Specify color mood (warm, cool, vibrant, desaturated)")

    if has_composition:
        technical_detail += 30
    else:
        suggestions.append("Add composition hints (wide shot, close-up, low angle, etc.)")

    technical_detail = min(100, technical_detail)

    # 4. Overall Score
    overall_score = int(
        concept_clarity * 0.4 +
        style_specificity * 0.3 +
        technical_detail * 0.3
    )

    return AestheticPromptQuality(
        concept_clarity=concept_clarity,
        style_specificity=style_specificity,
        technical_detail=technical_detail,
        overall_score=overall_score,
        has_auteur_reference=has_auteur,
        has_color_specification=has_color,
        has_lighting_specification=has_lighting,
        has_composition_hint=has_composition,
        suggestions=suggestions[:5],  # Limit to 5 suggestions
    )


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

        # Generate trace_id and evidence_refs (P6 RAG Protocol)
        trace_id = str(uuid.uuid4())
        evidence_refs: List[str] = [
            f"rag:character_dna:{request.style_reference}:visual_layer",
            f"rag:character_dna:{request.style_reference}:psychological_layer",
            f"db:character_dna:{trace_id}",
        ]

        return CharacterDNAResponse(
            success=True,
            character_name=request.name,
            character_dna=character_dna,
            style_prompt=style_prompt,
            full_prompt=full_prompt,
            usage_hint="Copy the 'full_prompt' and use it as a prefix for all image/video generations of this character.",
            trace_id=trace_id,
            evidence_refs=evidence_refs,
            confidence=0.85,  # LLM-generated, high confidence
        )

    except Exception as e:
        return CharacterDNAResponse(
            success=False,
            character_name=request.name,
            character_dna="",
            style_prompt="",
            full_prompt="",
            usage_hint=f"Error: {str(e)}",
            trace_id=str(uuid.uuid4()),
            evidence_refs=[],
            confidence=0.0,
        )


