"""
Suno AI Music Generation API Router

Provides REST endpoints for Suno AI music generation.
Credit-only billing (no BYOK support).

Endpoints:
- POST /api/v1/dimension/suno/generate - Generate music
- GET /api/v1/dimension/suno/status/{task_id} - Get task status

Security:
- XSS sanitization for prompt, title, style
- Model whitelist validation

2026 Best Practices Applied:
- Four-Component Prompt Framework (Genre, Mood, Instrumentation, Structure)
- Structure tags validation ([Verse], [Chorus], [Bridge], etc.)
- trace_id and evidence_refs for RAG Protocol v2
- V5 extended duration support (up to 4 minutes)
"""
from __future__ import annotations

import html
import logging
import re
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.credit_service import deduct_credits, get_or_create_user_credits, refund_credits
from app.services.suno_service import (
    SunoService,
    SunoMusicRequest,
    SunoMusicResponse,
    SunoModel,
    SunoSong,
    get_suno_service,
)
from app.services.telemetry_integration import record_tool_run

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/suno", tags=["Suno AI"])


# =============================================================================
# 2026 Best Practices: Enums and Models
# =============================================================================

class SunoPromptComponent(str, Enum):
    """Four-Component Framework for Suno prompts (2026).

    Based on effective Suno prompt engineering best practices.
    Reference: learnprompting.org, aimlapi.com
    """
    GENRE_STYLE = "genre_style"  # e.g., "Jazz, Smooth, Relaxing"
    MOOD_EMOTION = "mood_emotion"  # e.g., "melancholic, uplifting, intense"
    INSTRUMENTATION = "instrumentation"  # e.g., "piano, strings, drums"
    STRUCTURE = "structure"  # e.g., "[Verse], [Chorus], [Bridge]"


class SunoStructureTag(str, Enum):
    """Standard structure tags recognized by Suno (2026).

    Use these in lyrics to define song structure.
    """
    INTRO = "[Intro]"
    VERSE = "[Verse]"
    VERSE1 = "[Verse 1]"
    VERSE2 = "[Verse 2]"
    VERSE3 = "[Verse 3]"
    CHORUS = "[Chorus]"
    PRE_CHORUS = "[Pre-Chorus]"
    POST_CHORUS = "[Post-Chorus]"
    BRIDGE = "[Bridge]"
    BREAKDOWN = "[Breakdown]"
    INSTRUMENTAL = "[Instrumental]"
    SOLO = "[Solo]"
    OUTRO = "[Outro]"
    HOOK = "[Hook]"
    DROP = "[Drop]"


class SunoExtendMode(str, Enum):
    """Extend/modify modes for Suno (2026).

    Used for extending or modifying existing songs.
    """
    EXTEND = "extend"  # Continue existing song
    REMIX = "remix"  # Remix with different style
    REPLACE_SECTION = "replace_section"  # Replace specific section
    UPLOAD_EXTEND = "upload_extend"  # Continue uploaded audio


class SunoV5Capabilities(BaseModel):
    """Suno V5 capabilities (2026)."""
    max_duration_seconds: int = Field(default=240, description="Max 4-minute songs")
    songs_per_generation: int = Field(default=2, description="Songs per request")
    custom_mode: bool = Field(default=True, description="Supports custom lyrics")
    instrumental_mode: bool = Field(default=True, description="Supports instrumental only")
    extend_feature: bool = Field(default=True, description="Supports extend existing songs")
    stem_extraction: bool = Field(default=True, description="Supports stem extraction")
    structure_tags: List[str] = Field(
        default_factory=lambda: [t.value for t in SunoStructureTag],
        description="Supported structure tags"
    )


class SunoPromptQualityScore(BaseModel):
    """Prompt quality assessment for Suno (2026)."""
    has_genre: bool = Field(default=False, description="Specifies genre")
    has_mood: bool = Field(default=False, description="Specifies mood/emotion")
    has_instrumentation: bool = Field(default=False, description="Specifies instruments")
    has_structure: bool = Field(default=False, description="Uses structure tags")
    has_tempo: bool = Field(default=False, description="Specifies tempo")
    has_vocal_style: bool = Field(default=False, description="Specifies vocal style")
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall quality")


# =============================================================================
# Constants & Validation
# =============================================================================

ALLOWED_SUNO_MODELS = frozenset(["V5", "V4_5PLUS", "V4_5ALL", "V4_5", "V4"])

# Common genre keywords for auto-detection
GENRE_KEYWORDS = frozenset([
    "pop", "rock", "jazz", "hip-hop", "rap", "r&b", "soul", "country", "electronic",
    "edm", "house", "techno", "classical", "folk", "metal", "punk", "reggae",
    "blues", "indie", "alternative", "ambient", "lo-fi", "k-pop", "j-pop", "latin"
])

# Common mood keywords for auto-detection
MOOD_KEYWORDS = frozenset([
    "happy", "sad", "melancholic", "uplifting", "energetic", "calm", "relaxing",
    "intense", "dark", "bright", "romantic", "nostalgic", "aggressive", "peaceful"
])

# Structure tag pattern for detection
STRUCTURE_TAG_PATTERN = re.compile(r"\[(Verse|Chorus|Bridge|Intro|Outro|Hook|Drop|Pre-Chorus|Post-Chorus|Solo|Instrumental|Breakdown)\s*\d*\]", re.IGNORECASE)


# =============================================================================
# Sanitization Helpers
# =============================================================================

def _sanitize_text(value: str) -> str:
    """Sanitize text fields to prevent XSS.

    Args:
        value: Raw text input

    Returns:
        Sanitized string
    """
    if not value:
        return value
    value = value.strip()
    # Remove HTML tags
    value = re.sub(r"<[^>]+>", "", value)
    # Escape HTML entities
    value = html.escape(value)
    # Remove script/javascript patterns
    value = re.sub(r"(?i)javascript\s*:", "", value)
    value = re.sub(r"(?i)on\w+\s*=", "", value)
    return value


def _validate_suno_model(value: str) -> str:
    """Validate Suno model is in allowed list.

    Args:
        value: Raw model name

    Returns:
        Validated model name

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip()
    if value not in ALLOWED_SUNO_MODELS:
        raise ValueError(
            f"Invalid model: {value}. Allowed: {sorted(ALLOWED_SUNO_MODELS)}"
        )
    return value


# =============================================================================
# Request/Response Models
# =============================================================================

class SunoGenerateRequest(BaseModel):
    """API request for Suno music generation.

    Includes:
    - XSS sanitization for prompt, title, style
    - Model whitelist validation
    """

    prompt: str = Field(..., min_length=1, max_length=2000, description="Music description or lyrics (sanitized)")
    title: str = Field(..., min_length=1, max_length=100, description="Song title (sanitized)")
    style: str = Field(..., min_length=1, max_length=500, description="Music style/genre (sanitized)")
    instrumental: bool = Field(default=False, description="Instrumental only (no vocals)")
    model: str = Field(default="V5", description="Model: V5, V4_5PLUS, V4_5ALL, V4_5, V4")

    @field_validator("prompt", mode="before")
    @classmethod
    def sanitize_prompt(cls, v: str) -> str:
        """Sanitize prompt to prevent XSS."""
        return _sanitize_text(v)

    @field_validator("title", mode="before")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        """Sanitize title to prevent XSS."""
        return _sanitize_text(v)

    @field_validator("style", mode="before")
    @classmethod
    def sanitize_style(cls, v: str) -> str:
        """Sanitize style to prevent XSS."""
        return _sanitize_text(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate model is in allowed whitelist."""
        return _validate_suno_model(v)


class SunoSongResponse(BaseModel):
    """Individual song in response."""

    id: str
    title: str
    audio_url: Optional[str] = None
    stream_url: Optional[str] = None
    image_url: Optional[str] = None
    duration: Optional[float] = None


class SunoGenerateResponse(BaseModel):
    """API response for Suno music generation.

    2026 Best Practices:
    - trace_id: Unique request identifier for debugging
    - evidence_refs: RAG Protocol v2 references (List[str])
    - prompt_quality: Quality assessment of the input prompt
    """

    success: bool
    task_id: str
    status: str
    songs: List[SunoSongResponse] = []
    credits_used: int = 0
    error: Optional[str] = None
    # 2026: RAG Protocol v2 fields
    trace_id: str = Field(default="", description="Unique trace identifier")
    evidence_refs: List[str] = Field(default_factory=list, description="RAG evidence references")
    prompt_quality: Optional[SunoPromptQualityScore] = Field(None, description="Prompt quality assessment")


class SunoStatusResponse(BaseModel):
    """API response for task status."""

    task_id: str
    status: str
    songs: List[Dict[str, Any]] = []
    error: Optional[str] = None
    trace_id: str = Field(default="", description="Unique trace identifier")


# =============================================================================
# Credit Cost Calculation
# =============================================================================

def get_credit_cost(model: str) -> int:
    """Calculate credit cost based on model."""
    costs = {
        "V5": 20,
        "V4_5PLUS": 15,
        "V4_5ALL": 15,
        "V4_5": 12,
        "V4": 10,
    }
    return costs.get(model, 20)


# =============================================================================
# 2026: Prompt Quality Assessment
# =============================================================================

def assess_prompt_quality(prompt: str, style: str) -> SunoPromptQualityScore:
    """Assess the quality of a Suno prompt using Four-Component Framework.

    Args:
        prompt: The lyrics/description prompt
        style: The style/genre string

    Returns:
        SunoPromptQualityScore with quality assessment
    """
    prompt_lower = prompt.lower()
    style_lower = style.lower()
    combined = f"{prompt_lower} {style_lower}"

    # Check for genre
    has_genre = any(genre in combined for genre in GENRE_KEYWORDS)

    # Check for mood
    has_mood = any(mood in combined for mood in MOOD_KEYWORDS)

    # Check for instrumentation
    instrumentation_keywords = [
        "piano", "guitar", "drums", "bass", "strings", "violin", "synth",
        "organ", "brass", "saxophone", "trumpet", "flute", "percussion"
    ]
    has_instrumentation = any(inst in combined for inst in instrumentation_keywords)

    # Check for structure tags
    has_structure = bool(STRUCTURE_TAG_PATTERN.search(prompt))

    # Check for tempo
    tempo_keywords = ["slow", "fast", "upbeat", "tempo", "bpm", "mid-tempo"]
    has_tempo = any(tempo in combined for tempo in tempo_keywords)

    # Check for vocal style
    vocal_keywords = [
        "male", "female", "deep", "high", "raspy", "smooth", "falsetto",
        "soprano", "tenor", "baritone", "vocal", "singing", "rapping"
    ]
    has_vocal_style = any(vocal in combined for vocal in vocal_keywords)

    # Calculate overall score (0.0 - 1.0)
    score_components = [
        has_genre, has_mood, has_instrumentation,
        has_structure, has_tempo, has_vocal_style
    ]
    overall_score = sum(score_components) / len(score_components)

    return SunoPromptQualityScore(
        has_genre=has_genre,
        has_mood=has_mood,
        has_instrumentation=has_instrumentation,
        has_structure=has_structure,
        has_tempo=has_tempo,
        has_vocal_style=has_vocal_style,
        overall_score=round(overall_score, 2),
    )


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/generate",
    response_model=SunoGenerateResponse,
    summary="Generate Music with Suno AI",
    description="Generate music using Suno AI. Always uses platform credits (no BYOK).",
)
async def generate_music(
    request: SunoGenerateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SunoGenerateResponse:
    """Generate music using Suno AI.

    2026 Best Practices:
    - Generates trace_id for request tracking
    - Assesses prompt quality using Four-Component Framework
    - Returns evidence_refs for RAG Protocol v2
    """
    import time
    start_time = time.time()

    # Generate trace_id for RAG Protocol v2
    trace_id = f"suno-{uuid.uuid4().hex[:12]}"

    user_id = user.get("id")
    logger.info(
        f"[SUNO_GENERATE] user={user_id} title={request.title[:50]} "
        f"style={request.style[:50]} model={request.model} instrumental={request.instrumental}"
    )

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )
    
    # Calculate credit cost
    credit_cost = get_credit_cost(request.model)
    
    # Check and deduct credits (always required for Suno - no BYOK)
    user_credits = await get_or_create_user_credits(db, user_id)
    if user_credits.balance < credit_cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "INSUFFICIENT_CREDITS",
                "message": "크레딧이 부족합니다.",
                "required": credit_cost,
                "balance": user_credits.balance,
            },
        )
    
    await deduct_credits(
        db, user_id, credit_cost,
        description="Suno AI: Music Generation",
        meta={"model": request.model, "style": request.style[:50]},
    )
    
    try:
        # Build service request
        service_request = SunoMusicRequest(
            prompt=request.prompt,
            title=request.title,
            style=request.style,
            custom_mode=True,
            instrumental=request.instrumental,
            model=SunoModel(request.model),
        )
        
        # Generate music
        service = get_suno_service()
        result = await service.generate_music(service_request, wait_for_completion=True)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Assess prompt quality (2026 Best Practice)
        prompt_quality = assess_prompt_quality(request.prompt, request.style)

        # Build evidence_refs (List[str]) - RAG Protocol v2
        evidence_refs: List[str] = [
            f"db:suno:task:{result.task_id}",
            f"db:suno:model:{request.model}",
        ]
        if prompt_quality.overall_score >= 0.5:
            evidence_refs.append(f"db:suno:quality:high")

        if not result.success:
            # Refund on failure
            await refund_credits(
                db, user_id, credit_cost,
                description="Refund: Suno generation failed",
                meta={"error": result.error[:200] if result.error else "Unknown", "trace_id": trace_id},
            )

            await record_tool_run(
                db=db,
                tool_key="suno_music_generate",
                user_id=user_id,
                inputs_summary={"title": request.title, "style": request.style[:50], "trace_id": trace_id},
                outputs_summary={},
                status="failed",
                latency_ms=latency_ms,
                credits_charged=0,
                error_message=result.error,
            )

            return SunoGenerateResponse(
                success=False,
                task_id=result.task_id,
                status="failed",
                error=result.error,
                trace_id=trace_id,
                evidence_refs=evidence_refs,
                prompt_quality=prompt_quality,
            )

        # Convert songs to response format
        songs = [
            SunoSongResponse(
                id=s.id,
                title=s.title,
                audio_url=s.audio_url,
                stream_url=s.stream_url,
                image_url=s.image_url,
                duration=s.duration,
            )
            for s in result.songs
        ]

        # Add song references to evidence_refs
        for song in songs:
            evidence_refs.append(f"db:suno:song:{song.id}")

        await record_tool_run(
            db=db,
            tool_key="suno_music_generate",
            user_id=user_id,
            inputs_summary={
                "title": request.title,
                "style": request.style[:50],
                "model": request.model,
                "trace_id": trace_id,
                "prompt_quality_score": prompt_quality.overall_score,
            },
            outputs_summary={"song_count": len(songs)},
            status="success",
            latency_ms=latency_ms,
            credits_charged=credit_cost,
        )

        return SunoGenerateResponse(
            success=True,
            task_id=result.task_id,
            status="completed",
            songs=songs,
            credits_used=credit_cost,
            trace_id=trace_id,
            evidence_refs=evidence_refs,
            prompt_quality=prompt_quality,
        )
        
    except Exception as e:
        logger.error(f"Suno generation error: {e}")
        
        # Refund on error
        await refund_credits(
            db, user_id, credit_cost,
            description="Refund: Suno generation error",
            meta={"error": str(e)[:200]},
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/status/{task_id}",
    response_model=SunoStatusResponse,
    summary="Get Generation Status",
    description="Get the status of a Suno music generation task.",
)
async def get_status(
    task_id: str,
    user: dict = Depends(get_current_user),
) -> SunoStatusResponse:
    """Get status of a generation task."""
    service = get_suno_service()
    result = await service.get_task_status(task_id)
    
    return SunoStatusResponse(
        task_id=result.task_id,
        status=result.status,
        songs=result.songs,
        error=result.error,
    )


@router.get(
    "/pricing",
    summary="Get Pricing Information",
    description="Get Suno AI pricing information in credits.",
)
async def get_pricing() -> Dict[str, Any]:
    """Get pricing information.

    2026 Best Practices:
    - Includes V5 capabilities
    - Documents structure tags
    - Provides prompt quality tips
    """
    return {
        "service": "Suno AI",
        "provider": "suno",
        "credit_only": True,
        "byok_supported": False,
        "pricing": {
            "V5": {
                "credits": 20,
                "usd": 0.14,
                "songs_per_generation": 2,
                "max_duration_seconds": 240,  # 2026: 4 minutes
            },
            "V4_5PLUS": {"credits": 15, "usd": 0.10, "songs_per_generation": 2, "max_duration_seconds": 180},
            "V4_5ALL": {"credits": 15, "usd": 0.10, "songs_per_generation": 2, "max_duration_seconds": 180},
            "V4_5": {"credits": 12, "usd": 0.08, "songs_per_generation": 2, "max_duration_seconds": 120},
            "V4": {"credits": 10, "usd": 0.07, "songs_per_generation": 2, "max_duration_seconds": 120},
        },
        "supported_models": ["V5", "V4_5PLUS", "V4_5ALL", "V4_5", "V4"],
        "features": [
            "Custom mode with lyrics",
            "Instrumental mode",
            "Multiple music styles",
            "2 songs per generation",
            "Stream & download URLs",
            "Stem extraction (V5)",  # 2026 addition
            "Extend existing songs (V5)",  # 2026 addition
            "Up to 4-minute songs (V5)",  # 2026 addition
        ],
        # 2026: Four-Component Framework documentation
        "prompt_tips": {
            "genre_style": "Specify genre clearly: 'Jazz, Smooth, Relaxing'",
            "mood_emotion": "Add mood keywords: 'melancholic, uplifting, energetic'",
            "instrumentation": "List instruments: 'piano, strings, drums'",
            "structure": "Use structure tags in lyrics: [Verse], [Chorus], [Bridge]",
            "tempo": "Specify tempo: 'slow', 'upbeat', 'mid-tempo'",
            "vocal_style": "Describe vocals: 'male deep voice', 'female soprano'",
        },
        "structure_tags": [tag.value for tag in SunoStructureTag],
        "v5_capabilities": SunoV5Capabilities().model_dump(),
    }
