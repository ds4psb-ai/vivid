"""
Sound Dimension Endpoints - Sound Crafter.

- Sound Craft: Generate music/sound prompts
- Sound Moodboard: Generate sound direction cards

Security:
- XSS sanitization for concept, storyboard, mood, topic
- Enum validation for sound_type, genre, target_platform, tempo

2026 Best Practices:
- Suno v5: 44.1 kHz studio-grade, 12-stem export, MIDI, 8-min tracks
- Udio: 48 kHz high-fidelity, complex song structures
- MiniMax Music-2.0: Robust competitor with video integration
- Structure Strategy: Defining song structure (Intro→Verse→Chorus→Outro)
- RAG Protocol v2: trace_id, evidence_refs (List[str]), confidence
"""
from __future__ import annotations

import html
import logging
import re
import uuid
from enum import Enum
from typing import Dict, List

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

# Module logger
sound_logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

ALLOWED_TEMPOS = frozenset({"slow", "medium", "fast", "very-slow", "very-fast"})
ALLOWED_AUDIO_PLATFORMS = frozenset({"suno", "udio", "elevenlabs"})
ALLOWED_LANGUAGE_MIX = frozenset({"korean", "english", "japanese", "mixed"})
ALLOWED_SONG_STRUCTURES = frozenset({
    "verse-chorus-verse-chorus-bridge-chorus",
    "verse-chorus-verse-chorus",
    "intro-verse-chorus-verse-chorus-outro",
    "aaba",
    "ababcb",
    "custom",
})


# ============================================================================
# 2026 Audio Platform Capabilities (Suno v5, Udio, MiniMax Music-2.0)
# ============================================================================

class AudioPlatform(str, Enum):
    """Supported audio generation platforms (2026)."""
    SUNO = "suno"
    UDIO = "udio"
    ELEVENLABS = "elevenlabs"
    MINIMAX = "minimax"  # MiniMax Music-2.0 (new 2026)


class AudioQuality(str, Enum):
    """Audio quality levels (2026 industry standards)."""
    STANDARD = "standard"  # 32 kHz
    HIGH = "high"  # 44.1 kHz (CD quality)
    STUDIO = "studio"  # 48 kHz (broadcast quality)


class StemExportFormat(str, Enum):
    """Stem export formats (Suno v5 feature)."""
    WAV = "wav"  # Time-aligned WAV
    MIDI = "midi"  # MIDI export
    MP3 = "mp3"  # Compressed


class SunoV5Capabilities(BaseModel):
    """Suno v5 (2026) platform capabilities.

    Reference: Suno v5 delivers studio-grade audio at 44.1 kHz,
    12-stem export, MIDI conversion, and 8-minute extended tracks.
    """
    max_duration_seconds: int = Field(480, description="8-minute extended tracks")
    sample_rate_khz: float = Field(44.1, description="Studio-grade 44.1 kHz")
    max_stems: int = Field(12, description="12 time-aligned WAV stems")
    supports_midi_export: bool = Field(True, description="MIDI export capability")
    supports_audio_upload: bool = Field(True, description="Audio clip input")
    supports_vocals_upload: bool = Field(True, description="Vocal upload for guidance")


class UdioCapabilities(BaseModel):
    """Udio (2026) platform capabilities.

    Reference: Higher audio fidelity (48 kHz), complex song structures,
    better genre-blend handling, more human-sounding vocals.
    """
    max_duration_seconds: int = Field(300, description="5-minute tracks")
    sample_rate_khz: float = Field(48.0, description="Broadcast-grade 48 kHz")
    supports_detailed_remixing: bool = Field(True, description="Detailed remix control")
    supports_song_extensions: bool = Field(True, description="Iterative extension")
    vocal_quality: str = Field("human-like", description="More realistic vocal synthesis")


class SoundGenerationResult(BaseModel):
    """Comprehensive sound generation result (2026 pattern).

    Includes:
    - Platform-specific prompts
    - Audio quality settings
    - RAG Protocol v2 fields
    """
    suno_prompt: str = Field("", description="Suno-compatible prompt")
    udio_prompt: str = Field("", description="Udio-compatible prompt")
    elevenlabs_prompt: str = Field("", description="ElevenLabs-compatible prompt")

    target_platform: AudioPlatform = Field(
        AudioPlatform.SUNO,
        description="Primary target platform"
    )
    audio_quality: AudioQuality = Field(
        AudioQuality.HIGH,
        description="Target audio quality"
    )

    # Stem export (Suno v5)
    stem_export_available: bool = Field(False, description="Stem export available")
    stem_count: int = Field(0, description="Number of exportable stems")

    # RAG Protocol v2 fields
    trace_id: str = Field("", description="Trace ID for auditability")
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="RAG evidence references (format: 'rag:sound:genre', 'config:platform:suno')"
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="AI confidence score")


class StructureSegment(BaseModel):
    """Song structure segment (2026 Structure Strategy)."""
    name: str = Field(..., description="Segment name (intro, verse, chorus, bridge, outro)")
    duration_beats: int = Field(16, description="Duration in beats")
    bpm_hint: int = Field(120, description="Suggested BPM for this segment")
    mood_hint: str = Field("neutral", description="Mood for this segment")


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


def _validate_tempo(value: str) -> str:
    """Validate tempo is in allowed list.

    Args:
        value: Raw tempo

    Returns:
        Validated tempo

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip().lower()
    if value not in ALLOWED_TEMPOS:
        raise ValueError(
            f"지원하지 않는 템포: {value}. Allowed: {sorted(ALLOWED_TEMPOS)}"
        )
    return value


def _validate_sound_type(value: str) -> str:
    """Validate sound_type is in allowed list.

    Args:
        value: Raw sound_type

    Returns:
        Validated sound_type

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip().lower()
    if value not in ALLOWED_SOUND_TYPES:
        raise ValueError(
            f"지원하지 않는 사운드 타입: {value}. Allowed: {sorted(ALLOWED_SOUND_TYPES)}"
        )
    return value


def _validate_genre(value: str) -> str:
    """Validate genre is in allowed list.

    Args:
        value: Raw genre

    Returns:
        Validated genre

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip().lower()
    if value not in ALLOWED_GENRES:
        raise ValueError(
            f"지원하지 않는 장르: {value}. Allowed: {sorted(ALLOWED_GENRES)}"
        )
    return value


def _validate_audio_platform(value: str) -> str:
    """Validate target_platform is in allowed audio platform list.

    Args:
        value: Raw platform

    Returns:
        Validated platform

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip().lower()
    if value not in ALLOWED_AUDIO_PLATFORMS:
        raise ValueError(
            f"지원하지 않는 오디오 플랫폼: {value}. Allowed: {sorted(ALLOWED_AUDIO_PLATFORMS)}"
        )
    return value


# ============================================================================
# Request Models
# ============================================================================

class SoundCraftRequest(BaseModel):
    """Request model for Sound Crafter music prompt generation.

    Includes:
    - XSS sanitization for concept, storyboard, mood
    - Enum validation for sound_type, genre, target_platform, tempo
    """
    concept: str = Field(..., min_length=1, max_length=MAX_CONCEPT_LENGTH, description="Music concept (sanitized)")
    storyboard: str = Field("", max_length=5000, description="Optional storyboard for sync (sanitized)")
    sound_type: str = Field("bgm", description="Type of sound")
    mood: str = Field("cinematic", max_length=100, description="Music mood (sanitized)")
    genre: str = Field("drama", max_length=50, description="Genre")
    tempo: str = Field("medium", max_length=50, description="Tempo")
    duration: int = Field(60, ge=10, le=300, description="Duration in seconds")
    target_platform: str = Field("suno", description="Target audio platform (suno/udio/elevenlabs)")
    language: str = Field("ko", description="Output language")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("concept", mode="before")
    @classmethod
    def sanitize_concept(cls, v: str) -> str:
        """Sanitize concept to prevent XSS."""
        return _sanitize_text_field(v)

    @field_validator("storyboard", mode="before")
    @classmethod
    def sanitize_storyboard(cls, v: str) -> str:
        """Sanitize storyboard to prevent XSS."""
        return _sanitize_text_field(v, default="")

    @field_validator("mood", mode="before")
    @classmethod
    def sanitize_mood(cls, v: str) -> str:
        """Sanitize mood to prevent XSS."""
        return _sanitize_text_field(v, default="cinematic")

    @field_validator("sound_type")
    @classmethod
    def validate_sound_type(cls, v: str) -> str:
        """Validate sound_type is in allowed list."""
        return _validate_sound_type(v)

    @field_validator("genre")
    @classmethod
    def validate_genre(cls, v: str) -> str:
        """Validate genre is in allowed list."""
        return _validate_genre(v)

    @field_validator("tempo")
    @classmethod
    def validate_tempo(cls, v: str) -> str:
        """Validate tempo is in allowed list."""
        return _validate_tempo(v)

    @field_validator("target_platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        """Validate target_platform is in allowed audio platform list."""
        return _validate_audio_platform(v)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class SoundMoodboardRequest(BaseModel):
    """Request model for Sound Moodboard (Stage 1).

    Includes:
    - XSS sanitization for concept
    """
    concept: str = Field(..., min_length=1, max_length=MAX_CONCEPT_LENGTH, description="Sound concept (sanitized)")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("concept", mode="before")
    @classmethod
    def sanitize_concept(cls, v: str) -> str:
        """Sanitize concept to prevent XSS."""
        return _sanitize_text_field(v)

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
    """Generate music/sound prompts with Intent-Resolver integration.

    2026 Best Practice: Multi-platform prompt generation with
    Suno v5/Udio capabilities and RAG Protocol v2 trace fields.
    """
    user_id = user.get("id", "unknown")
    trace_id = f"sc-{uuid.uuid4().hex[:12]}"

    sound_logger.info(
        f"[SOUND_CRAFT] trace={trace_id} user={user_id} concept_len={len(request.concept)} "
        f"type={request.sound_type} genre={request.genre} tempo={request.tempo} platform={request.target_platform}"
    )

    from app.routers.intent_helpers import infer_intent_for_sound
    intent = infer_intent_for_sound(
        concept=request.concept,
        mood=request.mood,
        genre=request.genre,
        tempo=request.tempo,
        sound_type=request.sound_type,
    )

    # 2026: Build evidence_refs for traceability
    evidence_refs = [
        f"rag:sound_craft:{request.sound_type}",
        f"config:platform:{request.target_platform}",
        f"config:genre:{request.genre}",
        f"config:tempo:{request.tempo}",
    ]

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
            # 2026: RAG Protocol v2 trace fields
            "trace_id": trace_id,
            "evidence_refs": evidence_refs,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={
            "concept": request.concept[:100],
            "sound_type": request.sound_type,
            "platform": request.target_platform,
            "trace_id": trace_id,
        },
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
    """Generate music/sound prompts with SSE streaming.

    2026 Best Practice: Multi-platform prompt generation with
    Suno v5/Udio capabilities and RAG Protocol v2 trace fields.
    """
    user_id = user.get("id", "unknown")
    trace_id = f"scs-{uuid.uuid4().hex[:12]}"

    sound_logger.info(
        f"[SOUND_CRAFT_STREAM] trace={trace_id} user={user_id} concept_len={len(request.concept)} "
        f"type={request.sound_type} genre={request.genre} platform={request.target_platform}"
    )

    from app.routers.intent_helpers import infer_intent_for_sound
    intent = infer_intent_for_sound(
        concept=request.concept,
        mood=request.mood,
        genre=request.genre,
        tempo=request.tempo,
        sound_type=request.sound_type,
    )

    # 2026: Build evidence_refs for traceability
    evidence_refs = [
        f"rag:sound_craft:{request.sound_type}",
        f"config:platform:{request.target_platform}",
        f"config:genre:{request.genre}",
        f"config:tempo:{request.tempo}",
    ]

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
                # 2026: RAG Protocol v2 trace fields
                "trace_id": trace_id,
                "evidence_refs": evidence_refs,
            },
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={
                "concept": request.concept[:100],
                "sound_type": request.sound_type,
                "platform": request.target_platform,
                "trace_id": trace_id,
            },
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
    """Generate sound direction cards with Intent-Resolver integration.

    2026 Best Practice: RAG Protocol v2 trace fields for auditability.
    """
    user_id = user.get("id", "unknown")
    trace_id = f"sm-{uuid.uuid4().hex[:12]}"

    sound_logger.info(
        f"[SOUND_MOODBOARD] trace={trace_id} user={user_id} concept_len={len(request.concept)}"
    )

    from app.routers.intent_helpers import with_intent
    intent = with_intent(request)

    # 2026: Build evidence_refs for traceability
    evidence_refs = [
        f"rag:sound_moodboard:concept",
    ]

    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.SOUND_MOODBOARD,
        tool_key="sound_moodboard",
        inputs={
            "concept": request.concept,
            # 2026: RAG Protocol v2 trace fields
            "trace_id": trace_id,
            "evidence_refs": evidence_refs,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={
            "concept": request.concept[:100],
            "trace_id": trace_id,
        },
        intent=intent,
    )


# ============================================================================
# Iterative Lyrics Workflow (Expert Workflow Pattern)
# ============================================================================

class LyricsStyleGuide(BaseModel):
    """Style guide for lyrics generation."""
    genre: str = Field("J-POP rock", description="Music genre (e.g., 'Japanese anime opening')")
    tempo: str = Field("fast", description="Tempo (slow, medium, fast)")
    mood: str = Field("hopeful", description="Mood/emotion (e.g., 'hopeful, determined')")
    vocal_style: str = Field("powerful male rock vocal", description="Vocal style description")
    language_mix: str = Field("korean", description="Language: korean, english, mixed")
    reference_songs: list[str] = Field(default_factory=list, description="Reference song styles")


class LyricsRequest(BaseModel):
    """Request model for Iterative Lyrics generation.

    Implements the Expert Workflow's 4-step lyrics process:
    1. Topic Analysis
    2. Context Injection (Wiki/articles)
    3. Style Guide Application
    4. Final Generation with Suno metatags

    Includes:
    - XSS sanitization for topic
    """
    topic: str = Field(..., min_length=1, max_length=500, description="Song topic or theme (sanitized)")
    context_documents: list[str] = Field(default_factory=list, description="External context (Wiki, articles, research)")
    style_guide: LyricsStyleGuide = Field(default_factory=LyricsStyleGuide, description="Style guide for the song")
    song_structure: str = Field("verse-chorus-verse-chorus-bridge-chorus", description="Song structure")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("topic", mode="before")
    @classmethod
    def sanitize_topic(cls, v: str) -> str:
        """Sanitize topic to prevent XSS."""
        return _sanitize_text_field(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class LyricsSection(BaseModel):
    """A section of the song."""
    type: str  # verse, chorus, bridge, intro, outro
    content: str
    notes: str = ""


class LyricsResponse(BaseModel):
    """Response for Iterative Lyrics generation.

    2026 Best Practice: RAG Protocol v2 fields for auditability.
    """
    success: bool
    topic_analysis: str
    lyrics_sections: list[LyricsSection]
    full_lyrics: str  # Complete lyrics with metatags
    suno_prompt: str  # Suno-compatible generation prompt
    udio_prompt: str  # Udio-compatible prompt
    style_summary: str

    # RAG Protocol v2 fields
    trace_id: str = Field("", description="Trace ID for auditability")
    evidence_refs: List[str] = Field(
        default_factory=list,
        description="RAG evidence references (format: 'rag:lyrics:genre', 'config:structure:...')"
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="AI confidence score")


@router.post(
    "/sound/lyrics",
    response_model=LyricsResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        500: {"model": DimensionErrorResponse},
    },
    summary="Sound Crafter: Generate Lyrics (Expert Workflow)",
    description="Generate professional lyrics using the 4-step Expert Workflow with context injection and Suno-compatible output.",
    tags=["Dimension Extended"],
)
async def generate_lyrics(
    request: LyricsRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
) -> LyricsResponse:
    """Generate lyrics following the Expert Workflow pattern.

    2026 Best Practice: 4-step Expert Workflow with RAG Protocol v2 trace fields.

    The 4-step process:
    1. ANALYZE: Understand topic's emotional core and cultural resonance
    2. INCORPORATE: Inject external context (Wiki, articles)
    3. APPLY: Use style guide (genre, tempo, vocal style)
    4. OUTPUT: Structured lyrics with Suno/Udio metatags
    """
    user_id = user.get("id", "unknown")
    trace_id = f"lyr-{uuid.uuid4().hex[:12]}"

    sound_logger.info(
        f"[LYRICS_GENERATE] trace={trace_id} user={user_id} topic_len={len(request.topic)} "
        f"genre={request.style_guide.genre} tempo={request.style_guide.tempo}"
    )

    # 2026: Build evidence_refs for traceability
    evidence_refs = [
        f"rag:lyrics:genre:{request.style_guide.genre.lower().replace(' ', '_')}",
        f"config:tempo:{request.style_guide.tempo}",
        f"config:structure:{request.song_structure}",
        f"config:language:{request.style_guide.language_mix}",
    ]

    from google import genai
    from google.genai import types
    from app.config import settings
    import json
    
    # Build context block from documents
    context_block = ""
    if request.context_documents:
        context_lines = []
        for i, doc in enumerate(request.context_documents[:5], 1):
            context_lines.append(f"### Context Document {i}\n{doc[:2000]}")
        context_block = "\n\n".join(context_lines)
    
    # Build reference songs hint
    ref_songs = ", ".join(request.style_guide.reference_songs[:3]) if request.style_guide.reference_songs else "None provided"
    
    system_prompt = """You are a Master Lyricist and Music Producer.
Follow the Expert Workflow for lyrics generation:

STEP 1 - ANALYZE: Understand the topic's emotional core and cultural resonance
STEP 2 - INCORPORATE: Use provided context to ground the lyrics
STEP 3 - APPLY: Match the style guide specifications
STEP 4 - OUTPUT: Generate structured lyrics with metatags

EXPERT GENRE KNOWLEDGE (Anime/J-Pop Rock):
- Structure: Soft Intro -> Driving Verse -> Build-up Pre-Chorus -> Explosive Chorus -> Emotional Bridge -> Key-up Final Chorus
- Vibe: "Running toward a goal", "Youth burning forward", "Believing in the future"
- Vocals: Powerful, emotional restraint in verses, explosive in chorus

VISUAL BPM (Part 6 - Scene-Music Sync):
- High BPM (120+): Fast cuts, rapid movement, action. Match with quick-fire lyrics.
- Mid BPM (80-110): Dialogue, emotional scenes, walking. Match with flowing verses.
- Low BPM (<80): Contemplation, loss, tension. Match with sparse, weighted lines.

OUTPUT FORMAT (valid JSON):
{
  "topic_analysis": "Brief analysis of topic's emotional core",
  "lyrics_sections": [
    {"type": "verse", "content": "Lyrics here...", "notes": "Performance note"},
    {"type": "chorus", "content": "Lyrics here...", "notes": ""},
    {"type": "bridge", "content": "Lyrics here...", "notes": ""}
  ],
  "full_lyrics": "[Verse 1]\\nLyrics...\\n\\n[Chorus]\\nLyrics...",
  "suno_prompt": "Genre: ... Style: ... Tempo: ... Mood: ... Vocals: ...",
  "udio_prompt": "Instrumental focus prompt...",
  "style_summary": "Brief summary of the style direction"
}

CRITICAL RULES:
- Use metatags: [Verse], [Chorus], [Bridge], [Intro], [Outro]
- Keep lines 6-10 syllables for singability
- Avoid clichés and overused AI phrases
- Match the language_mix specification"""

    user_prompt = f"""Generate professional lyrics for:

TOPIC: {request.topic}

CONTEXT (User-Provided Knowledge):
{context_block if context_block else "No additional context provided."}

STYLE GUIDE:
- Genre: {request.style_guide.genre}
- Tempo: {request.style_guide.tempo}
- Mood: {request.style_guide.mood}
- Vocal Style: {request.style_guide.vocal_style}
- Language: {request.style_guide.language_mix}
- Reference Songs: {ref_songs}

SONG STRUCTURE: {request.song_structure}

Generate complete, singable lyrics with Suno-compatible formatting."""

    try:
        api_key = byok_key or settings.GEMINI_API_KEY
        client = genai.Client(api_key=api_key)
        
        response = await client.aio.models.generate_content(
            model=request.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.8,
                response_mime_type="application/json",
            ),
        )
        
        # Parse response
        text = response.text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            if text.startswith("json"):
                text = text[4:].strip()
        
        data = json.loads(text)
        
        # Convert sections
        sections = []
        for section_data in data.get("lyrics_sections", []):
            sections.append(LyricsSection(
                type=section_data.get("type", "verse"),
                content=section_data.get("content", ""),
                notes=section_data.get("notes", ""),
            ))
        
        return LyricsResponse(
            success=True,
            topic_analysis=data.get("topic_analysis", ""),
            lyrics_sections=sections,
            full_lyrics=data.get("full_lyrics", ""),
            suno_prompt=data.get("suno_prompt", ""),
            udio_prompt=data.get("udio_prompt", ""),
            style_summary=data.get("style_summary", ""),
            # 2026: RAG Protocol v2 trace fields
            trace_id=trace_id,
            evidence_refs=evidence_refs,
            confidence=0.85,  # Default confidence for successful generation
        )

    except json.JSONDecodeError as e:
        return LyricsResponse(
            success=False,
            topic_analysis=f"JSON parsing error: {str(e)}",
            lyrics_sections=[],
            full_lyrics="",
            suno_prompt="",
            udio_prompt="",
            style_summary="",
            trace_id=trace_id,
            evidence_refs=evidence_refs,
            confidence=0.0,
        )
    except Exception as e:
        return LyricsResponse(
            success=False,
            topic_analysis=f"Error: {str(e)}",
            lyrics_sections=[],
            full_lyrics="",
            suno_prompt="",
            udio_prompt="",
            style_summary="",
            trace_id=trace_id,
            evidence_refs=evidence_refs,
            confidence=0.0,
        )

