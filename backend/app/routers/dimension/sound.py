"""
Sound Dimension Endpoints - Sound Crafter.

- Sound Craft: Generate music/sound prompts
- Sound Moodboard: Generate sound direction cards
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
    _validate_language,
    _strip_string,
    DimensionResponse,
    DimensionErrorResponse,
    DimensionCapsuleId,
    ALLOWED_GENRES,
    ALLOWED_SOUND_TYPES,
    ALLOWED_PLATFORMS,
    MAX_CONCEPT_LENGTH,
    get_sse_headers,
    Optional,
)

router = APIRouter()


# ============================================================================
# Request Models
# ============================================================================

class SoundCraftRequest(BaseModel):
    """Request model for Sound Crafter music prompt generation."""
    concept: str = Field(..., min_length=1, max_length=MAX_CONCEPT_LENGTH, description="Music concept")
    storyboard: str = Field("", max_length=5000, description="Optional storyboard for sync")
    sound_type: str = Field("bgm", description="Type of sound")
    mood: str = Field("cinematic", max_length=100, description="Music mood")
    genre: str = Field("drama", max_length=50, description="Genre")
    tempo: str = Field("medium", max_length=50, description="Tempo")
    duration: int = Field(60, ge=10, le=300, description="Duration in seconds")
    target_platform: str = Field("suno", description="Target audio platform (suno/udio/elevenlabs)")
    language: str = Field("ko", description="Output language")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("concept", "storyboard", "mood", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("sound_type")
    @classmethod
    def validate_sound_type(cls, v: str) -> str:
        if v not in ALLOWED_SOUND_TYPES:
            raise ValueError(f"지원하지 않는 사운드 타입: {v}")
        return v

    @field_validator("genre")
    @classmethod
    def validate_genre(cls, v: str) -> str:
        if v not in ALLOWED_GENRES:
            raise ValueError(f"지원하지 않는 장르: {v}")
        return v

    @field_validator("target_platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        if v not in ALLOWED_PLATFORMS:
            raise ValueError(f"지원하지 않는 플랫폼: {v}")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class SoundMoodboardRequest(BaseModel):
    """Request model for Sound Moodboard (Stage 1)."""
    concept: str = Field(..., min_length=1, max_length=MAX_CONCEPT_LENGTH, description="Sound concept")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("concept", mode="before")
    @classmethod
    def strip_concept(cls, v: str) -> str:
        return _strip_string(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


# ============================================================================
# Sound Craft
# ============================================================================

@router.post(
    "/sound/craft",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Sound Crafter: Generate Music Prompt",
    description="Generate music/sound prompts for Suno, Udio, and ElevenLabs.",
    tags=["Dimension 4-Stage"],
)
async def craft_sound(
    request: SoundCraftRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Generate music/sound prompts with Intent-Resolver integration."""
    from app.routers.intent_helpers import infer_intent_for_sound
    intent = infer_intent_for_sound(
        concept=request.concept,
        mood=request.mood,
        genre=request.genre,
        tempo=request.tempo,
        sound_type=request.sound_type,
    )
    
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.SOUND_CRAFT,
        tool_key="sound_craft",
        inputs={
            "concept": request.concept,
            "storyboard": request.storyboard,
            "sound_type": request.sound_type,
            "mood": request.mood,
            "genre": request.genre,
            "tempo": request.tempo,
            "duration": f"{request.duration}s",  # Convert int to string format
            "target_platform": request.target_platform,
            "language": request.language,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"concept": request.concept[:100], "sound_type": request.sound_type, "platform": request.target_platform},
        params={"use_rag": True},
        intent=intent,
    )


@router.post(
    "/sound/craft/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Sound Crafter: Generate Music Prompt (SSE Stream)",
    description="Generate music/sound prompts with real-time progress updates via SSE.",
    tags=["Dimension 4-Stage"],
)
async def craft_sound_stream(
    request: SoundCraftRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Generate music/sound prompts with SSE streaming."""
    from app.routers.intent_helpers import infer_intent_for_sound
    intent = infer_intent_for_sound(
        concept=request.concept,
        mood=request.mood,
        genre=request.genre,
        tempo=request.tempo,
        sound_type=request.sound_type,
    )
    
    return StreamingResponse(
        _execute_dimension_tool_stream(
            capsule_id=DimensionCapsuleId.SOUND_CRAFT,
            tool_key="sound_craft",
            operation_name="사운드 프롬프트 생성",
            inputs={
                "concept": request.concept,
                "storyboard": request.storyboard,
                "sound_type": request.sound_type,
                "mood": request.mood,
                "genre": request.genre,
                "tempo": request.tempo,
                "duration": f"{request.duration}s",  # Convert int to string format
                "target_platform": request.target_platform,
                "language": request.language,
            },
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={"concept": request.concept[:100], "sound_type": request.sound_type, "platform": request.target_platform},
            params={"use_rag": True},
            intent=intent,
        ),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


# ============================================================================
# Sound Moodboard
# ============================================================================

@router.post(
    "/sound/moodboard",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Sound Crafter: Generate Mood Board",
    description="Stage 1: Generate 3 distinct sound direction cards.",
    tags=["Dimension 4-Stage"],
)
async def generate_sound_moodboard(
    request: SoundMoodboardRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Generate sound direction cards with Intent-Resolver integration."""
    from app.routers.intent_helpers import with_intent
    intent = with_intent(request)
    
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.SOUND_MOODBOARD,
        tool_key="sound_moodboard",
        inputs={
            "concept": request.concept,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"concept": request.concept[:100]},
        intent=intent,
    )
