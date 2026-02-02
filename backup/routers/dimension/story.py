"""Story Dimension Endpoints - Story Architect.

API endpoints for AI-powered scenario and shot list generation.

Features:
- Story Architect: Generate video scenarios from concepts
- Story Refine: Refine raw concepts into distinct narrative angles
- Shot List Generation: Break down scenarios into timeline shots with tool recommendations

2026 Best Practices:
- Script-to-storyboard generation flow
- Tool selection heuristics (Veo, Kling, Sora)
- Camera movement and montage theory integration
- Director's cut editing patterns

Security:
- XSS sanitization for concept, persona_data, reference_analysis, scenario, style_preference
- Enum validation for genre, structure

References:
- LTX Studio: Script-to-storyboard functionality
- DomoAI: Frame-to-video storytelling
- Mootion: Script-to-video platform (65% faster in 2026)
- DIMENSION_APP_MACRO_PLANNING_2026.md Part 11
"""
from __future__ import annotations

import html
import logging
import re
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
    _validate_language,
    _strip_string,
    DimensionResponse,
    DimensionErrorResponse,
    DimensionCapsuleId,
    ALLOWED_GENRES,
    ALLOWED_STRUCTURES,
    MAX_CONCEPT_LENGTH,
    get_sse_headers,
    Optional,
)

router = APIRouter()

# Module logger
story_logger = logging.getLogger(__name__)


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


def _validate_structure(value: str) -> str:
    """Validate structure is in allowed list.

    Args:
        value: Raw structure

    Returns:
        Validated structure

    Raises:
        ValueError: If not in allowed list
    """
    value = value.strip().lower()
    if value not in ALLOWED_STRUCTURES:
        raise ValueError(
            f"지원하지 않는 구조: {value}. Allowed: {sorted(ALLOWED_STRUCTURES)}"
        )
    return value


# ============================================================================
# Request Models
# ============================================================================

class StoryArchitectRequest(BaseModel):
    """Request model for Story Architect scenario generation.

    Includes:
    - XSS sanitization for concept, persona_data, reference_analysis
    - Enum validation for genre, structure
    """
    concept: str = Field(..., min_length=1, max_length=MAX_CONCEPT_LENGTH, description="Video concept (sanitized)")
    persona_data: str = Field("", max_length=500000, description="Creator persona data (sanitized)")
    reference_analysis: str = Field("", max_length=500000, description="Reference analysis results (sanitized)")
    genre: str = Field("drama", max_length=50, description="Video genre")
    duration: int = Field(60, ge=10, le=600, description="Target duration in seconds")
    structure: str = Field("3-act", description="Narrative structure")
    language: str = Field("ko", description="Output language")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("concept", mode="before")
    @classmethod
    def sanitize_concept(cls, v: str) -> str:
        """Sanitize concept to prevent XSS."""
        return _sanitize_text_field(v)

    @field_validator("persona_data", mode="before")
    @classmethod
    def sanitize_persona_data(cls, v) -> str:
        """Sanitize persona_data to prevent XSS. Handles dict/list input from workflow steps."""
        import json as json_lib
        # Handle dict or list input (from workflow step data)
        if isinstance(v, (dict, list)):
            v = json_lib.dumps(v, ensure_ascii=False)
        return _sanitize_text_field(v, default="")

    @field_validator("reference_analysis", mode="before")
    @classmethod
    def sanitize_reference_analysis(cls, v) -> str:
        """Sanitize reference_analysis to prevent XSS. Handles dict/list input from workflow steps."""
        import json as json_lib
        # Handle dict or list input (from workflow step data)
        if isinstance(v, (dict, list)):
            v = json_lib.dumps(v, ensure_ascii=False)
        return _sanitize_text_field(v, default="")

    @field_validator("genre")
    @classmethod
    def validate_genre(cls, v: str) -> str:
        """Validate genre is in allowed list."""
        return _validate_genre(v)

    @field_validator("structure")
    @classmethod
    def validate_structure(cls, v: str) -> str:
        """Validate structure is in allowed list."""
        return _validate_structure(v)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class StoryRefineRequest(BaseModel):
    """Request model for Story Refine concept refinement.

    Includes:
    - XSS sanitization for concept
    - Enum validation for genre
    """
    concept: str = Field(..., min_length=1, max_length=MAX_CONCEPT_LENGTH, description="Raw concept (sanitized)")
    genre: str = Field("drama", max_length=50, description="Target genre")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("concept", mode="before")
    @classmethod
    def sanitize_concept(cls, v: str) -> str:
        """Sanitize concept to prevent XSS."""
        return _sanitize_text_field(v)

    @field_validator("genre")
    @classmethod
    def validate_genre(cls, v: str) -> str:
        """Validate genre is in allowed list."""
        return _validate_genre(v)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


# ============================================================================
# Story Architect
# ============================================================================

@router.post(
    "/story/architect",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Story Architect: Generate Scenario",
    description="Generate video scenario combining persona DNA and reference analysis.",
    tags=["Dimension 4-Stage"],
)
async def architect_story(
    request: StoryArchitectRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Generate video scenario with Intent-Resolver integration."""
    user_id = user.get("id", "unknown")
    story_logger.info(
        f"[STORY_ARCHITECT] user={user_id} concept_len={len(request.concept)} "
        f"genre={request.genre} structure={request.structure} duration={request.duration}s"
    )

    from app.routers.intent_helpers import infer_intent_for_story
    intent = infer_intent_for_story(
        concept=request.concept,
        genre=request.genre,
        structure=request.structure,
    )
    
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.STORY_ARCHITECT,
        tool_key="story_architect",
        inputs={
            "concept": request.concept,
            "persona_data": request.persona_data,
            "reference_analysis": request.reference_analysis,
            "genre": request.genre,
            "duration": f"{request.duration}s",  # Convert int to string format
            "structure": request.structure,
            "language": request.language,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"concept": request.concept[:100], "genre": request.genre, "structure": request.structure},
        params={"use_rag": True},
        intent=intent,
    )


@router.post(
    "/story/architect/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Story Architect: Generate Scenario (SSE Stream)",
    description="Generate video scenario with real-time progress updates via SSE.",
    tags=["Dimension 4-Stage"],
)
async def architect_story_stream(
    request: StoryArchitectRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Generate video scenario with SSE streaming."""
    user_id = user.get("id", "unknown")
    story_logger.info(
        f"[STORY_ARCHITECT_STREAM] user={user_id} concept_len={len(request.concept)} "
        f"genre={request.genre} structure={request.structure}"
    )

    from app.routers.intent_helpers import infer_intent_for_story
    intent = infer_intent_for_story(
        concept=request.concept,
        genre=request.genre,
        structure=request.structure,
    )
    
    return StreamingResponse(
        _execute_dimension_tool_stream(
            capsule_id=DimensionCapsuleId.STORY_ARCHITECT,
            tool_key="story_architect",
            operation_name="시나리오 생성",
            inputs={
                "concept": request.concept,
                "persona_data": request.persona_data,
                "reference_analysis": request.reference_analysis,
                "genre": request.genre,
                "duration": f"{request.duration}s",  # Convert int to string format
                "structure": request.structure,
                "language": request.language,
            },
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={"concept": request.concept[:100], "genre": request.genre, "structure": request.structure},
            params={"use_rag": True},
            intent=intent,
        ),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


# ============================================================================
# Story Refine
# ============================================================================

@router.post(
    "/story/refine",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Story Architect: Refine Concept",
    description="Stage 1: Refine raw concept into distinct narrative angles.",
    tags=["Dimension 4-Stage"],
)
async def refine_story(
    request: StoryRefineRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Refine concept with Intent-Resolver integration."""
    user_id = user.get("id", "unknown")
    story_logger.info(
        f"[STORY_REFINE] user={user_id} concept_len={len(request.concept)} genre={request.genre}"
    )

    from app.routers.intent_helpers import infer_intent_from_request
    intent = infer_intent_from_request(genre=request.genre)
    
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.STORY_REFINE,
        tool_key="story_refine",
        inputs={
            "concept": request.concept,
            "genre": request.genre,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"concept": request.concept[:100], "genre": request.genre},
        intent=intent,
    )


@router.post(
    "/story/refine/stream",
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Story Architect: Refine Concept (SSE Stream)",
    description="Refine concept with real-time progress updates via SSE.",
    tags=["Dimension 4-Stage"],
)
async def refine_story_stream(
    request: StoryRefineRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Refine concept with SSE streaming."""
    user_id = user.get("id", "unknown")
    story_logger.info(
        f"[STORY_REFINE_STREAM] user={user_id} concept_len={len(request.concept)} genre={request.genre}"
    )

    from app.routers.intent_helpers import infer_intent_from_request
    intent = infer_intent_from_request(genre=request.genre)
    
    return StreamingResponse(
        _execute_dimension_tool_stream(
            capsule_id=DimensionCapsuleId.STORY_REFINE,
            tool_key="story_refine",
            operation_name="컨셉 정제",
            inputs={
                "concept": request.concept,
                "genre": request.genre,
            },
            model=request.model,
            user=user,
            byok_key=byok_key,
            db=db,
            inputs_summary={"concept": request.concept[:100], "genre": request.genre},
            intent=intent,
        ),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


# ============================================================================
# Timeline Shot List Generator (Expert Workflow Pattern)
# ============================================================================

class ShotListRequest(BaseModel):
    """Request model for Timeline Shot List generation.

    Breaks down a scenario into precise shot segments for AI video generation,
    following the Expert Workflow pattern (0-2s, 3-5s, etc.).

    Includes:
    - XSS sanitization for scenario and style_preference
    """
    scenario: str = Field(..., min_length=10, max_length=10000, description="Full scenario (sanitized)")
    total_duration: int = Field(60, ge=10, le=300, description="Total video duration in seconds")
    max_shot_duration: int = Field(8, ge=4, le=10, description="Maximum duration per shot (AI video limit)")
    style_preference: str = Field("cinematic", max_length=100, description="Visual style preference (sanitized)")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("scenario", mode="before")
    @classmethod
    def sanitize_scenario(cls, v: str) -> str:
        """Sanitize scenario to prevent XSS."""
        return _sanitize_text_field(v)

    @field_validator("style_preference", mode="before")
    @classmethod
    def sanitize_style_preference(cls, v: str) -> str:
        """Sanitize style_preference to prevent XSS."""
        return _sanitize_text_field(v, default="cinematic")

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        return _validate_model(v)


class TimelineShot(BaseModel):
    """A single shot in the timeline."""
    shot_number: int
    time_range: str  # e.g., "0:00-0:02"
    start_seconds: float
    end_seconds: float
    duration: float
    shot_type: str  # wide, medium, close-up, extreme-close-up
    description: str
    camera_movement: str  # static, pan, zoom, dolly, tracking
    recommended_tool: str  # veo, kling, sora
    tool_reason: str
    audio_notes: str = ""


class ShotListResponse(BaseModel):
    """Response for Timeline Shot List generation.

    2026 Best Practices:
    - Tool recommendations based on expert heuristics
    - Camera movement theory integration
    - Montage editing patterns
    """
    success: bool
    total_shots: int
    total_duration: float
    shots: list[TimelineShot]
    tool_summary: dict  # Count of each tool recommendation
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="Evidence references: [\"db:scenarios:uuid\", \"rag:cinematography:technique_id\"]",
    )


@router.post(
    "/story/shot-list",
    response_model=ShotListResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        500: {"model": DimensionErrorResponse},
    },
    summary="Story Architect: Generate Shot List",
    description="Break down scenario into precise timeline shots (≤8s each) with AI tool recommendations.",
    tags=["Dimension Extended"],
)
async def generate_shot_list(
    request: ShotListRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
) -> ShotListResponse:
    """Generate Timeline Shot List following the Expert Workflow pattern.

    Breaks down the scenario into shots that are:
    1. ≤8 seconds each (AI video generation limit)
    2. Optimized for specific tools (Kling, Sora, Veo)
    3. Include camera movements and audio notes

    Tool Selection Guide:
    - Kling: Close-ups, low motion, high detail, start/end frame control
    - Sora: Action, transitions, dynamic scenes, montage sequences
    - Veo: Cinematic, narrative, audio sync, longer continuity
    """
    user_id = user.get("id", "unknown")
    story_logger.info(
        f"[SHOT_LIST] user={user_id} scenario_len={len(request.scenario)} "
        f"duration={request.total_duration}s max_shot={request.max_shot_duration}s style={request.style_preference}"
    )

    from google import genai
    from google.genai import types
    from app.config import settings
    import json
    
    system_prompt = f"""You are a Professional Storyboard Director for AI video generation.
Break down the scenario into precise SHOT SEGMENTS for Veo/Kling/Sora.

CRITICAL RULES:
1. Each shot must be ≤{request.max_shot_duration} seconds (AI video limit)
2. Shots must cover the ENTIRE {request.total_duration} second duration
3. Use precise time ranges: "0:00-0:02", "0:03-0:05", etc.

EXPERT TOOL SELECTION HEURISTICS (Strictly Follow):
- kling:
    * USE FOR: Extreme close-ups (face, hands, food), shots with minimal movement, high-fidelity texture shots.
    * REASON: "Best for preserving high facial fidelity and texture in static/slow-motion shots."
    * EXAMPLE: "Eye close-up", "Chopping vegetables (hands only)", "Food plating detail".
- sora:
    * USE FOR: High motion, fighting/action scenes, rapid cuts, complex background transitions, full-body movement.
    * REASON: "Best for temporal consistency in complex motion and dynamic camera work."
    * EXAMPLE: "Running sequence", "Battle animation", "Kitchen panorama with many chefs moving".
- veo:
    * USE FOR: Cinematic narrative, atmospheric establishing shots, long takes (>5s) requiring alignment, audio-visual sync.
    * REASON: "Best for coherent cinematic flow and atmospheric consistency."

EDITING & MOVEMENT HEURISTICS (The "Director's Cut"):
1. MOVEMENT MOTIVATION:
   - "Push-In": Use when a character realizes something or feels intense emotion (Empathy).
   - "Pull-Out": Use at the end of a scene or to show isolation/abandonment.
   - "Dolly Zoom": Use for moments of shock or reality distortion (Vertigo effect).
   
2. MONTAGE THEORY:
   - "Match Cut": Connect shots with similar shapes (e.g., Clock -> Moon, Eye -> Drain).
   - "Intellectual Montage": Juxtapose conflicting images to create metaphor (e.g., Anger -> Volcano eruption).

OUTPUT FORMAT (valid JSON array):
[
  {{
    "shot_number": 1,
    "time_range": "0:00-0:03",
    "start_seconds": 0,
    "end_seconds": 3,
    "duration": 3,
    "shot_type": "wide",
    "description": "Detailed visual description",
    "camera_movement": "static",
    "recommended_tool": "veo",
    "tool_reason": "Establishing shot with atmosphere",
    "audio_notes": "Ambient kitchen sounds"
  }}
]

Be specific with descriptions. Include character actions, expressions, and visual details."""

    user_prompt = f"""Break down this scenario into timeline shots:

SCENARIO:
{request.scenario}

REQUIREMENTS:
- Total Duration: {request.total_duration} seconds
- Max Shot Duration: {request.max_shot_duration} seconds
- Visual Style: {request.style_preference}

Generate a complete shot list covering the entire duration."""

    try:
        api_key = byok_key or settings.GEMINI_API_KEY
        client = genai.Client(api_key=api_key)
        
        response = await client.aio.models.generate_content(
            model=request.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
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
        
        shots_data = json.loads(text)
        
        # Convert to TimelineShot objects
        shots = []
        tool_counts = {"veo": 0, "kling": 0, "sora": 0}
        
        for shot_data in shots_data:
            shot = TimelineShot(
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
            
            tool = shot.recommended_tool.lower()
            if tool in tool_counts:
                tool_counts[tool] += 1
        
        total_duration = sum(s.duration for s in shots)
        
        # Build evidence refs (Vivid convention: List[str])
        evidence_refs = [
            "rag:cinematography:expert_heuristics",
            "rag:cinematography:montage_theory",
        ]
        for shot in shots:
            tool = shot.recommended_tool.lower()
            evidence_refs.append(f"rag:tool_selection:{tool}")

        return ShotListResponse(
            success=True,
            total_shots=len(shots),
            total_duration=total_duration,
            shots=shots,
            tool_summary=tool_counts,
            evidence_refs=list(set(evidence_refs)),  # Deduplicate
        )

    except json.JSONDecodeError as e:
        return ShotListResponse(
            success=False,
            total_shots=0,
            total_duration=0,
            shots=[],
            tool_summary={"error": str(e)},
            evidence_refs=[],
        )
    except Exception as e:
        return ShotListResponse(
            success=False,
            total_shots=0,
            total_duration=0,
            shots=[],
            tool_summary={"error": str(e)},
            evidence_refs=[],
        )

