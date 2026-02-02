"""Story Engine Router - Unified Story + Prompt API.

Mega app router combining:
- /api/story-engine/generate - Full story generation pipeline
- /api/story-engine/story - Story Architect direct access
- /api/story-engine/prompt - Prompt Alchemy direct access
- /api/story-engine/system-prompt - System Prompt generation only

Features:
- DNA Lab Logic Vector integration
- Multi-platform prompt generation
- SSE streaming support
- Credit management with refund

Usage:
    POST /api/story-engine/generate
    {
        "concept": "dark thriller in abandoned factory",
        "target_platforms": ["veo", "kling"],
        "generate_shot_list": true
    }
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.vpe import LogicVector
from app.services.story_engine_service import (
    StoryEngineService,
    StoryEngineResult,
    StoryScenario,
    TranslatedPrompt,
    ShotListItem,
    StoryEngineComponent,
    STORY_ENGINE_CREDITS,
    get_story_engine_service,
)
from app.routers.story_engine.system_prompt import (
    SystemPromptGenerator,
    SystemPromptResult,
    StoryStructure,
    TargetPlatform,
    get_system_prompt_generator,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/story-engine", tags=["Story Engine"])


# =============================================================================
# Dependencies
# =============================================================================

async def get_db():
    """Get database session."""
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    # Add your auth dependency here
) -> dict:
    """Get current authenticated user."""
    # Placeholder - integrate with your auth system
    return {"id": "test-user", "email": "test@example.com"}


def get_byok_key() -> Optional[str]:
    """Get BYOK API key if provided."""
    return None


async def get_or_create_user_credits(user_id: str, db: AsyncSession):
    """Get or create user credits record."""
    from app.services.kelly_credit_service import get_or_create_user_credits as _get_credits
    return await _get_credits(db, user_id)


async def deduct_credits(user_id: str, amount: int, db: AsyncSession, reason: str = ""):
    """Deduct credits from user account."""
    from app.services.kelly_credit_service import deduct_credits as _deduct
    return await _deduct(db, user_id, amount, reason)


async def refund_credits(user_id: str, amount: int, db: AsyncSession, reason: str = ""):
    """Refund credits to user account."""
    from app.services.kelly_credit_service import refund_credits as _refund
    return await _refund(db, user_id, amount, reason)


# =============================================================================
# Request/Response Models
# =============================================================================

class StoryEngineGenerateRequest(BaseModel):
    """Request for full story generation pipeline."""
    concept: str = Field(..., min_length=5, max_length=2000, description="Story concept or idea")
    logic_vector: Optional[Dict[str, Any]] = Field(None, description="DNA Lab Logic Vector (JSON)")
    auteur_key: Optional[str] = Field(None, max_length=50, description="Auteur key for RAG")
    genre: str = Field("drama", max_length=50, description="Story genre")
    structure: str = Field("3-act", description="Narrative structure")
    duration_seconds: int = Field(60, ge=10, le=300, description="Target video duration")
    persona_data: Optional[str] = Field(None, max_length=10000, description="Creator persona data")
    reference_analysis: Optional[str] = Field(None, max_length=10000, description="Reference analysis")
    target_platforms: Optional[List[str]] = Field(None, description="Target platforms for prompts")
    generate_shot_list: bool = Field(False, description="Generate shot list breakdown")
    language: str = Field("ko", description="Output language")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("target_platforms")
    @classmethod
    def validate_platforms(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        valid_platforms = ["veo", "veo_31", "kling", "kling_26", "sora", "sora_max_2pro"]
        for platform in v:
            normalized = platform.lower().replace("-", "_")
            if normalized not in valid_platforms:
                raise ValueError(f"Invalid platform: {platform}")
        return v


class StoryArchitectRequest(BaseModel):
    """Request for Story Architect only."""
    concept: str = Field(..., min_length=5, max_length=2000)
    genre: str = Field("drama")
    structure: str = Field("3-act")
    duration_seconds: int = Field(60, ge=10, le=300)
    persona_data: Optional[str] = Field(None)
    reference_analysis: Optional[str] = Field(None)
    language: str = Field("ko")
    model: str = Field("gemini-3-flash-preview")


class PromptTranslateRequest(BaseModel):
    """Request for Prompt Alchemy only."""
    scene_description: str = Field(..., min_length=10, max_length=5000)
    target_platforms: List[str] = Field(default_factory=lambda: ["veo"])
    style: str = Field("cinematic")
    auteur_key: Optional[str] = Field(None)
    language: str = Field("ko")
    model: str = Field("gemini-3-flash-preview")


class SystemPromptRequest(BaseModel):
    """Request for System Prompt generation."""
    logic_vector: Dict[str, Any] = Field(..., description="Logic Vector JSON")
    story_description: Optional[str] = Field(None, max_length=2000)
    target_platform: str = Field("veo", description="Target platform: veo, kling, runway")


class ShotListRequest(BaseModel):
    """Request for shot list generation."""
    scenario_text: str = Field(..., min_length=20, max_length=10000)
    duration_seconds: int = Field(60, ge=10, le=300)
    logic_vector: Optional[Dict[str, Any]] = Field(None)
    model: str = Field("gemini-3-flash-preview")


class StoryEngineResponse(BaseModel):
    """Response from Story Engine."""
    success: bool
    trace_id: str
    components_run: List[str] = []
    scenario: Optional[Dict[str, Any]] = None
    translated_prompts: List[Dict[str, Any]] = []
    system_prompt: Optional[str] = None
    shot_list: List[Dict[str, Any]] = []
    logic_vector_used: bool = False
    confidence: float = 0.0
    credits_used: int = 0
    evidence_refs: List[str] = []
    errors: Optional[Dict[str, str]] = None


class SystemPromptResponse(BaseModel):
    """Response from System Prompt generation."""
    success: bool
    system_prompt: str
    negative_prompt: Optional[str] = None
    platform: str
    character_count: int
    truncated: bool = False
    logic_vector_summary: Optional[str] = None


# =============================================================================
# Helper Functions
# =============================================================================

def _parse_logic_vector(data: Optional[Dict[str, Any]]) -> Optional[LogicVector]:
    """Parse Logic Vector from dict."""
    if not data:
        return None
    try:
        return LogicVector.model_validate(data)
    except Exception as e:
        logger.warning(f"Failed to parse Logic Vector: {e}")
        return None


def _result_to_response(result: StoryEngineResult) -> StoryEngineResponse:
    """Convert service result to API response."""
    return StoryEngineResponse(
        success=result.success,
        trace_id=result.trace_id,
        components_run=result.components_run,
        scenario=asdict(result.scenario) if result.scenario else None,
        translated_prompts=[asdict(p) for p in result.translated_prompts],
        system_prompt=result.system_prompt,
        shot_list=[asdict(s) for s in result.shot_list],
        logic_vector_used=result.logic_vector_used,
        confidence=result.confidence,
        credits_used=result.credits_used,
        evidence_refs=result.evidence_refs,
        errors=result.errors if result.errors else None,
    )


async def _sse_event(event_type: str, data: Any) -> str:
    """Format SSE event."""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/generate",
    response_model=StoryEngineResponse,
    summary="Generate Full Story Pipeline",
    description="Generate story scenario with optional prompts and shot list using DNA Lab Logic Vector.",
)
async def generate_story(
    request: StoryEngineGenerateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StoryEngineResponse:
    """Full story generation pipeline."""
    user_id = user.get("id", "unknown")
    trace_id = f"story-engine-{uuid.uuid4().hex[:12]}"

    logger.info(
        f"[STORY_ENGINE] user={user_id} concept_len={len(request.concept)} "
        f"platforms={request.target_platforms} shot_list={request.generate_shot_list}"
    )

    # Calculate required credits
    service = get_story_engine_service()
    components = ["story"]
    if request.logic_vector:
        components.append("system_prompt")
    if request.target_platforms:
        components.extend(["prompt"] * len(request.target_platforms))
    if request.generate_shot_list:
        components.append("shot_list")

    required_credits = service.calculate_total_credits(components)

    # Check user credits
    try:
        user_credits = await get_or_create_user_credits(user_id, db)
        if user_credits.balance < required_credits:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "Insufficient credits",
                    "required": required_credits,
                    "available": user_credits.balance,
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"[STORY_ENGINE] Credit check skipped: {e}")

    # Parse Logic Vector
    logic_vector = _parse_logic_vector(request.logic_vector)

    try:
        # Deduct credits
        await deduct_credits(user_id, required_credits, db, f"story-engine:{trace_id}")

        # Run story generation
        result = await service.generate_story(
            concept=request.concept,
            logic_vector=logic_vector,
            auteur_key=request.auteur_key,
            genre=request.genre,
            structure=request.structure,
            duration_seconds=request.duration_seconds,
            persona_data=request.persona_data,
            reference_analysis=request.reference_analysis,
            target_platforms=request.target_platforms,
            generate_shot_list=request.generate_shot_list,
            language=request.language,
            model=request.model,
        )

        # Partial refund if some components failed
        if result.credits_used < required_credits:
            refund_amount = required_credits - result.credits_used
            await refund_credits(user_id, refund_amount, db, f"story-engine-partial:{trace_id}")

        return _result_to_response(result)

    except Exception as e:
        logger.error(f"[STORY_ENGINE] Generation error: {e}")
        # Full refund on error
        await refund_credits(user_id, required_credits, db, f"story-engine-error:{trace_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e), "trace_id": trace_id},
        )


@router.post(
    "/generate/stream",
    summary="Generate Full Story Pipeline (SSE Stream)",
    description="Generate story with real-time progress updates via SSE.",
)
async def generate_story_stream(
    request: StoryEngineGenerateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Story generation with SSE streaming."""
    user_id = user.get("id", "unknown")
    trace_id = f"story-engine-{uuid.uuid4().hex[:12]}"

    async def stream_generator():
        try:
            yield await _sse_event("start", {"trace_id": trace_id, "status": "started"})

            service = get_story_engine_service()
            logic_vector = _parse_logic_vector(request.logic_vector)

            # Progress callback for SSE
            async def progress_callback(message: str, progress: float):
                yield await _sse_event("progress", {
                    "message": message,
                    "progress": progress,
                })

            # Run generation with progress updates
            yield await _sse_event("progress", {"message": "시나리오 생성 시작...", "progress": 0.1})

            result = await service.generate_story(
                concept=request.concept,
                logic_vector=logic_vector,
                auteur_key=request.auteur_key,
                genre=request.genre,
                structure=request.structure,
                duration_seconds=request.duration_seconds,
                persona_data=request.persona_data,
                reference_analysis=request.reference_analysis,
                target_platforms=request.target_platforms,
                generate_shot_list=request.generate_shot_list,
                language=request.language,
                model=request.model,
            )

            yield await _sse_event("complete", _result_to_response(result).model_dump())

        except Exception as e:
            logger.error(f"[STORY_ENGINE_STREAM] Error: {e}")
            yield await _sse_event("error", {"error": str(e), "trace_id": trace_id})

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/story",
    summary="Story Architect Direct",
    description="Generate story scenario only (direct access to Story Architect).",
)
async def story_architect_direct(
    request: StoryArchitectRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Direct Story Architect access."""
    user_id = user.get("id", "unknown")
    logger.info(f"[STORY_ENGINE] Story Architect direct: user={user_id}")

    service = get_story_engine_service()
    result = await service.generate_story(
        concept=request.concept,
        genre=request.genre,
        structure=request.structure,
        duration_seconds=request.duration_seconds,
        persona_data=request.persona_data,
        reference_analysis=request.reference_analysis,
        language=request.language,
        model=request.model,
        target_platforms=None,
        generate_shot_list=False,
    )

    return {
        "success": result.success,
        "trace_id": result.trace_id,
        "scenario": asdict(result.scenario) if result.scenario else None,
        "credits_used": result.credits_used,
        "evidence_refs": result.evidence_refs,
        "errors": result.errors if result.errors else None,
    }


@router.post(
    "/prompt",
    summary="Prompt Alchemy Direct",
    description="Translate scene to platform-specific prompts (direct access to Prompt Alchemy).",
)
async def prompt_alchemy_direct(
    request: PromptTranslateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Direct Prompt Alchemy access."""
    user_id = user.get("id", "unknown")
    logger.info(f"[STORY_ENGINE] Prompt Alchemy direct: user={user_id}")

    service = get_story_engine_service()
    prompts = await service.translate_prompts_only(
        scene_description=request.scene_description,
        target_platforms=request.target_platforms,
        style=request.style,
        auteur_key=request.auteur_key,
        language=request.language,
        model=request.model,
    )

    return {
        "success": True,
        "prompts": [asdict(p) for p in prompts],
        "platforms": request.target_platforms,
    }


@router.post(
    "/system-prompt",
    response_model=SystemPromptResponse,
    summary="Generate System Prompt",
    description="Generate system prompt from Logic Vector for video generation platforms.",
)
async def generate_system_prompt_endpoint(
    request: SystemPromptRequest,
    user: dict = Depends(get_current_user),
):
    """Generate system prompt from Logic Vector."""
    user_id = user.get("id", "unknown")
    logger.info(f"[STORY_ENGINE] System Prompt: user={user_id} platform={request.target_platform}")

    logic_vector = _parse_logic_vector(request.logic_vector)
    if not logic_vector:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Logic Vector format",
        )

    generator = get_system_prompt_generator()
    story_structure = None
    if request.story_description:
        story_structure = StoryStructure(shot_description=request.story_description)

    result = generator.generate(
        logic_vector=logic_vector,
        story_structure=story_structure,
        target_platform=request.target_platform,
    )

    return SystemPromptResponse(
        success=True,
        system_prompt=result.system_prompt,
        negative_prompt=result.negative_prompt,
        platform=result.platform,
        character_count=result.character_count,
        truncated=result.truncated,
        logic_vector_summary=result.logic_vector_summary,
    )


@router.post(
    "/shot-list",
    summary="Generate Shot List",
    description="Generate shot list from scenario with tool recommendations.",
)
async def generate_shot_list_endpoint(
    request: ShotListRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate shot list from scenario."""
    user_id = user.get("id", "unknown")
    logger.info(f"[STORY_ENGINE] Shot List: user={user_id} duration={request.duration_seconds}s")

    service = get_story_engine_service()
    logic_vector = _parse_logic_vector(request.logic_vector)

    shots = await service.generate_shot_list_only(
        scenario_text=request.scenario_text,
        duration_seconds=request.duration_seconds,
        logic_vector=logic_vector,
        model=request.model,
    )

    # Calculate tool summary
    tool_counts = {"veo": 0, "kling": 0, "sora": 0}
    for shot in shots:
        tool = shot.recommended_tool.lower()
        if tool in tool_counts:
            tool_counts[tool] += 1

    return {
        "success": True,
        "total_shots": len(shots),
        "total_duration": sum(s.duration for s in shots),
        "shots": [asdict(s) for s in shots],
        "tool_summary": tool_counts,
    }


@router.get(
    "/credits",
    summary="Get Component Credit Costs",
    description="Get credit costs for each Story Engine component.",
)
async def get_credit_costs():
    """Get credit costs for components."""
    return {
        "components": {comp.value: cost for comp, cost in STORY_ENGINE_CREDITS.items()},
        "total_for_all": sum(STORY_ENGINE_CREDITS.values()),
        "description": {
            "story": "Story Architect - scenario generation",
            "prompt": "Prompt Alchemy - platform-specific translation (per platform)",
            "system_prompt": "System Prompt - Logic Vector to shot grammar",
            "shot_list": "Shot List - timeline breakdown with tool recommendations",
        },
    }


@router.get(
    "/platforms",
    summary="Get Supported Platforms",
    description="Get list of supported video generation platforms.",
)
async def get_platforms():
    """Get supported platforms."""
    return {
        "platforms": [p.value for p in TargetPlatform],
        "default": "veo",
        "descriptions": {
            "veo": "Google VEO - Cinematic video with native audio",
            "kling": "Kling - High-fidelity lip sync and facial detail",
            "runway": "Runway - Creative video generation",
            "pika": "Pika - Quick video generation",
            "suno": "Suno - Audio/music generation",
            "generic": "Generic - Platform-agnostic prompts",
        },
    }


@router.get(
    "/health",
    summary="Health Check",
    description="Story Engine service health check.",
)
async def health_check():
    """Health check endpoint."""
    return {
        "service": "story_engine",
        "status": "healthy",
        "components": {
            "story_architect": "available",
            "prompt_alchemy": "available",
            "system_prompt": "available",
            "shot_list": "available",
        },
        "version": "1.0.0",
    }


# =============================================================================
# Exports
# =============================================================================

__all__ = ["router"]
