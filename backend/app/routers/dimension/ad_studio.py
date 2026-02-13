"""AD Studio — Assistant Director Dimension Endpoints.

Cinematic analysis + prompt generation for Kling 3.0 and Seedance 2.0.

Endpoints:
- POST /ad-studio/analyze — Scenario text analysis
- POST /ad-studio/analyze/stream — SSE streaming analysis
- POST /ad-studio/analyze-video — Video reference analysis
- GET /ad-studio/techniques — List available cinematic techniques

Security:
- XSS sanitization for all text inputs
- Content size validation
- Input enum validation
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
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
    sanitize_generic_text,
    validate_content_size,
    DimensionResponse,
    DimensionErrorResponse,
    DimensionCapsuleId,
    get_sse_headers,
    MAX_CONTENT_SIZE,
)
from app.utils.sse_utils import sse_progress, sse_complete, sse_error, sse_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ad-studio", tags=["AD Studio"])


def _is_quota_error(exc: Exception) -> bool:
    """Detect Gemini API quota/rate-limit errors from exception message."""
    msg = str(exc).lower()
    return any(kw in msg for kw in ("resource_exhausted", "quota exceeded", "429", "rate limit"))


def _quota_detail(exc: Exception) -> str:
    """Build user-facing error detail for quota errors."""
    msg = str(exc)
    # Extract model name if present
    model_match = re.search(r"model:\s*([\w\-\.]+)", msg)
    model_hint = f" (모델: {model_match.group(1)})" if model_match else ""
    return (
        f"API 키의 호출 할당량이 초과되었습니다{model_hint}. "
        "다른 모델을 선택하거나 잠시 후 다시 시도하세요."
    )


# ============================================================================
# Constants
# ============================================================================

MAX_SCENARIO_LENGTH = 10000
MAX_STYLE_HINT_LENGTH = 500
ALLOWED_ENGINES = {"kling", "seedance", "veo"}
DEFAULT_ENGINES = ["kling", "seedance", "veo"]


# ============================================================================
# Request Models
# ============================================================================

class ADStudioScenarioRequest(BaseModel):
    """Scenario-based analysis request."""
    scenario: str = Field(..., min_length=10, max_length=MAX_SCENARIO_LENGTH,
                          description="Free-form scenario text")
    style_hint: Optional[str] = Field(None, max_length=MAX_STYLE_HINT_LENGTH,
                                       description="Style hint (e.g., 'dark and moody')")
    target_engines: List[str] = Field(default=DEFAULT_ENGINES,
                                       description="Target video engines")
    language: str = Field(default="ko")
    model: str = Field(default="gemini-3-pro-preview")
    generate_video: bool = Field(default=False,
                                  description="Optional async video generation flag (Phase 5)")

    @field_validator("scenario")
    @classmethod
    def sanitize_scenario(cls, v: str) -> str:
        v = _strip_string(v)
        v = sanitize_generic_text(v)
        return validate_content_size(v, MAX_SCENARIO_LENGTH, "scenario")

    @field_validator("style_hint")
    @classmethod
    def sanitize_style_hint(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return sanitize_generic_text(_strip_string(v))
        return v

    @field_validator("target_engines")
    @classmethod
    def validate_engines(cls, v: List[str]) -> List[str]:
        for engine in v:
            if engine not in ALLOWED_ENGINES:
                raise ValueError(f"Unsupported engine: {engine}. Allowed: {ALLOWED_ENGINES}")
        return v

    @field_validator("language")
    @classmethod
    def check_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("model")
    @classmethod
    def check_model(cls, v: str) -> str:
        return _validate_model(v)


class ADStudioVideoRequest(BaseModel):
    """Video reference analysis request."""
    video_url: str = Field(..., description="Uploaded video URL (from scene detection)")
    scene_timestamps: List[str] = Field(default_factory=list,
                                         description="Scene timestamps from detection")
    style_hint: Optional[str] = Field(None, max_length=MAX_STYLE_HINT_LENGTH)
    target_engines: List[str] = Field(default=DEFAULT_ENGINES)
    language: str = Field(default="ko")
    model: str = Field(default="gemini-3-pro-preview")

    @field_validator("video_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = _strip_string(v)
        if not v.startswith(("http://", "https://")):
            raise ValueError("video_url must be a valid HTTP(S) URL")
        return v

    @field_validator("style_hint")
    @classmethod
    def sanitize_style_hint(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return sanitize_generic_text(_strip_string(v))
        return v

    @field_validator("target_engines")
    @classmethod
    def validate_engines(cls, v: List[str]) -> List[str]:
        for engine in v:
            if engine not in ALLOWED_ENGINES:
                raise ValueError(f"Unsupported engine: {engine}. Allowed: {ALLOWED_ENGINES}")
        return v

    @field_validator("language")
    @classmethod
    def check_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("model")
    @classmethod
    def check_model(cls, v: str) -> str:
        return _validate_model(v)


# ============================================================================
# Response Models
# ============================================================================

class EmotionalBeat(BaseModel):
    """Single point on the emotional arc."""
    scene_number: int
    emotion: str  # Korean
    intensity: float = Field(ge=0.0, le=1.0)
    description: str  # Korean


class ColorBeat(BaseModel):
    """Color temperature at a scene."""
    scene_number: int
    temperature: str  # e.g., "warm", "cool", "neutral"
    palette: str  # Korean description
    hex_hint: Optional[str] = None


class VisualRhythm(BaseModel):
    """Camera distance and edit tempo progression."""
    camera_distance_curve: List[str]  # e.g., ["WS", "MS", "CU", "ECU"]
    edit_tempo: str  # Korean description
    average_shot_duration: Optional[str] = None


class ContinuityAnchors(BaseModel):
    """Elements that must remain constant across scenes."""
    character_anchors: List[str] = Field(default_factory=list)  # Korean
    style_anchors: List[str] = Field(default_factory=list)  # Korean
    lighting_anchors: List[str] = Field(default_factory=list)  # Korean


class FiveDomains(BaseModel):
    """VGoT-inspired 5-domain analysis for cross-shot coherence."""
    character_dynamics: str = ""  # English
    background_continuity: str = ""  # English
    relationship_evolution: str = ""  # English
    camera_evolution: str = ""  # English
    lighting_evolution: str = ""  # English


class SequenceAnalysis(BaseModel):
    """Cross-scene intelligence."""
    emotional_arc: List[EmotionalBeat] = Field(default_factory=list)
    visual_rhythm: Optional[VisualRhythm] = None
    color_progression: List[ColorBeat] = Field(default_factory=list)
    continuity_anchors: Optional[ContinuityAnchors] = None
    five_domains: Optional[FiveDomains] = None
    continuity_score: float = Field(default=0.0, ge=0.0, le=1.0)


class SequenceContext(BaseModel):
    """Where this scene sits in the sequence."""
    previous_exit: Optional[str] = None  # Korean
    transition_in: Optional[str] = None  # Korean
    transition_out_setup: Optional[str] = None  # Korean
    emotional_position: str = ""  # Korean
    camera_distance_flow: str = ""  # Korean: e.g., "이전 MS -> 현재 CU -> 다음 ECU"


class TechniqueTag(BaseModel):
    """A cinematic technique applied to a scene."""
    technique_id: str
    category: str
    name_ko: str
    name_en: str
    description_ko: str


class SceneTechniques(BaseModel):
    """All techniques applied to a scene (12 categories)."""
    composition: List[TechniqueTag] = Field(default_factory=list)
    camera_movement: List[TechniqueTag] = Field(default_factory=list)
    camera_angle: List[TechniqueTag] = Field(default_factory=list)
    lighting: List[TechniqueTag] = Field(default_factory=list)
    color: List[TechniqueTag] = Field(default_factory=list)
    shot_scale: List[TechniqueTag] = Field(default_factory=list)
    focus_technique: List[TechniqueTag] = Field(default_factory=list)
    lens_character: List[TechniqueTag] = Field(default_factory=list)
    editing_rhythm: List[TechniqueTag] = Field(default_factory=list)
    transition_type: List[TechniqueTag] = Field(default_factory=list)
    aesthetic_style: List[TechniqueTag] = Field(default_factory=list)
    physics_motion: List[TechniqueTag] = Field(default_factory=list)


class EnginePrompts(BaseModel):
    """Optimized prompts per video engine."""
    kling_3_0: str = ""  # English
    seedance_2_0: str = ""  # English
    veo_3_1: str = ""  # English


class SceneAnalysis(BaseModel):
    """Per-scene cinematic analysis."""
    scene_number: int
    description: str  # Korean
    description_en: str = ""  # English summary
    techniques: SceneTechniques = Field(default_factory=SceneTechniques)
    sequence_context: SequenceContext = Field(default_factory=SequenceContext)
    prompts: EnginePrompts = Field(default_factory=EnginePrompts)
    continuity_anchors: Optional[Dict[str, str]] = None  # Per-scene anchors


class ADStudioResponse(BaseModel):
    """Full AD Studio analysis response."""
    success: bool = True
    sequence: SequenceAnalysis = Field(default_factory=SequenceAnalysis)
    scenes: List[SceneAnalysis] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    trace_id: str = ""
    metrics: Optional[Dict[str, Any]] = None
    # v2: 5-Domain decomposition fields
    characters: List[Dict[str, Any]] = Field(default_factory=list)
    beat_structure: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Decomposition Schema Models — for Gemini response_schema enforcement
# ============================================================================


class DecompositionCharacter(BaseModel):
    """Character extracted from scenario."""
    binding_token: str = ""
    name: str = ""
    description_en: str = ""
    first_appears_in_shot: int = 1
    arc_summary_en: str = ""


class DecompositionBeat(BaseModel):
    """Single narrative beat."""
    beat: str = ""
    shot_numbers: List[int] = Field(default_factory=list)
    purpose_en: str = ""


class DecompositionBeatStructure(BaseModel):
    """Beat structure for the sequence."""
    type: str = "4-act"
    pacing_profile: str = "dramatic"
    total_target_duration_sec: int = 10
    beats: List[DecompositionBeat] = Field(default_factory=list)


class DecompositionAudio(BaseModel):
    """Audio design per shot."""
    ambient: str = ""
    sfx: str = ""
    music: str = ""
    dialogue: Optional[str] = None


class DecompositionShotContinuity(BaseModel):
    """Per-shot continuity anchors."""
    character: str = ""
    style: str = ""
    end_frame_hint: str = ""


class DecompositionTechniques(BaseModel):
    """Technique IDs per category."""
    shot_scale: List[str] = Field(default_factory=list)
    camera_movement: List[str] = Field(default_factory=list)
    camera_angle: List[str] = Field(default_factory=list)
    lighting: List[str] = Field(default_factory=list)
    color: List[str] = Field(default_factory=list)
    composition: List[str] = Field(default_factory=list)
    aesthetic_style: List[str] = Field(default_factory=list)
    physics_motion: List[str] = Field(default_factory=list)
    focus_technique: List[str] = Field(default_factory=list)
    editing_rhythm: List[str] = Field(default_factory=list)


class DecompositionPrompts(BaseModel):
    """Engine-specific prompts per shot."""
    kling_3_0: str = ""
    seedance_2_0: str = ""
    veo_3_1: str = ""


class DecompositionShot(BaseModel):
    """Single shot in the decomposition."""
    shot_number: int = 1
    beat: str = ""
    description: str = ""
    description_en: str = ""
    shot_type: str = ""
    duration_weight: float = 1.0
    techniques: DecompositionTechniques = Field(default_factory=DecompositionTechniques)
    characters_in_shot: List[str] = Field(default_factory=list)
    action_en: str = ""
    audio: DecompositionAudio = Field(default_factory=DecompositionAudio)
    continuity_anchors: DecompositionShotContinuity = Field(default_factory=DecompositionShotContinuity)
    transition_to_next: str = ""
    prompts: DecompositionPrompts = Field(default_factory=DecompositionPrompts)


class DecompositionEmotionalBeat(BaseModel):
    """Emotional arc point."""
    shot_number: int = 1
    emotion: str = ""
    intensity: float = 0.5
    description: str = ""


class DecompositionVisualRhythm(BaseModel):
    """Visual rhythm progression."""
    camera_distance_curve: List[str] = Field(default_factory=list)
    edit_tempo: str = ""


class DecompositionColorBeat(BaseModel):
    """Color progression point."""
    shot_number: int = 1
    temperature: str = "neutral"
    palette: str = ""


class DecompositionSequenceContinuity(BaseModel):
    """Sequence-level continuity anchors."""
    character_anchors: List[str] = Field(default_factory=list)
    style_anchors: List[str] = Field(default_factory=list)
    lighting_anchors: List[str] = Field(default_factory=list)


class DecompositionFiveDomains(BaseModel):
    """VGoT 5-domain analysis."""
    character_dynamics: str = ""
    background_continuity: str = ""
    relationship_evolution: str = ""
    camera_evolution: str = ""
    lighting_evolution: str = ""


class DecompositionSequence(BaseModel):
    """Sequence-level analysis."""
    emotional_arc: List[DecompositionEmotionalBeat] = Field(default_factory=list)
    visual_rhythm: DecompositionVisualRhythm = Field(default_factory=DecompositionVisualRhythm)
    color_progression: List[DecompositionColorBeat] = Field(default_factory=list)
    continuity_anchors: DecompositionSequenceContinuity = Field(default_factory=DecompositionSequenceContinuity)
    five_domains: DecompositionFiveDomains = Field(default_factory=DecompositionFiveDomains)


class DecompositionOutput(BaseModel):
    """Gemini response_schema for cinematic scenario decomposition."""
    characters: List[DecompositionCharacter] = Field(default_factory=list)
    beat_structure: DecompositionBeatStructure = Field(default_factory=DecompositionBeatStructure)
    shots: List[DecompositionShot] = Field(default_factory=list)
    sequence: DecompositionSequence = Field(default_factory=DecompositionSequence)


class TechniqueInfo(BaseModel):
    """Technique info for the techniques listing endpoint."""
    technique_id: str
    category: str
    name_ko: str
    name_en: str
    description_ko: str
    best_for: List[str] = Field(default_factory=list)


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/analyze",
    response_model=ADStudioResponse,
    summary="Analyze scenario and generate cinematic prompts",
    responses={400: {"model": DimensionErrorResponse}},
)
async def analyze_scenario(
    req: ADStudioScenarioRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> ADStudioResponse:
    """Analyze a text scenario and generate sequence-aware cinematic prompts."""
    trace_id = str(uuid4())
    start_time = time.time()

    try:
        from app.services.ad_brain import ADStudioBrain

        brain = ADStudioBrain(model=req.model, byok_key=byok_key)

        result = await brain.analyze_scenario(
            scenario=req.scenario,
            style_hint=req.style_hint,
            target_engines=req.target_engines,
            language=req.language,
            user=user,
            db=db,
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        result.trace_id = trace_id
        result.metrics = {"latency_ms": elapsed_ms, "model": req.model}

        logger.info(
            f"[ad-studio] analyze_scenario completed: "
            f"{len(result.scenes)} scenes, {elapsed_ms}ms"
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        if _is_quota_error(e):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=_quota_detail(e),
            )
        logger.error(f"[ad-studio] analyze_scenario error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AD Studio 분석 중 오류가 발생했습니다.",
        )


@router.post(
    "/analyze/stream",
    summary="Analyze scenario with SSE streaming",
    responses={400: {"model": DimensionErrorResponse}},
)
async def analyze_scenario_stream(
    req: ADStudioScenarioRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """SSE streaming version of scenario analysis."""
    trace_id = str(uuid4())

    async def event_generator():
        try:
            yield sse_progress(10, "시나리오 분석 시작...")

            from app.services.ad_brain import ADStudioBrain

            brain = ADStudioBrain(model=req.model, byok_key=byok_key)

            yield sse_progress(20, "씬 분해 중...")

            result = await brain.analyze_scenario(
                scenario=req.scenario,
                style_hint=req.style_hint,
                target_engines=req.target_engines,
                language=req.language,
                user=user,
                db=db,
                progress_callback=lambda pct, msg: sse_progress(
                    min(20 + int(pct * 0.7), 90), msg
                ),
            )

            result.trace_id = trace_id
            yield sse_progress(95, "프롬프트 생성 완료")
            yield sse_complete(result.model_dump())

        except Exception as e:
            logger.error(f"[ad-studio] stream error: {e}", exc_info=True)
            if _is_quota_error(e):
                yield sse_error(_quota_detail(e))
            else:
                yield sse_error(str(e))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


@router.post(
    "/analyze-video",
    response_model=ADStudioResponse,
    summary="Analyze video reference and generate cinematic prompts",
    responses={400: {"model": DimensionErrorResponse}},
)
async def analyze_video(
    req: ADStudioVideoRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> ADStudioResponse:
    """Analyze a video reference (from scene detection) and generate prompts."""
    trace_id = str(uuid4())
    start_time = time.time()

    try:
        from app.services.ad_brain import ADStudioBrain

        brain = ADStudioBrain(model=req.model, byok_key=byok_key)

        result = await brain.analyze_video(
            video_url=req.video_url,
            scene_timestamps=req.scene_timestamps,
            style_hint=req.style_hint,
            target_engines=req.target_engines,
            language=req.language,
            user=user,
            db=db,
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        result.trace_id = trace_id
        result.metrics = {"latency_ms": elapsed_ms, "model": req.model}

        logger.info(
            f"[ad-studio] analyze_video completed: "
            f"{len(result.scenes)} scenes, {elapsed_ms}ms"
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        if _is_quota_error(e):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=_quota_detail(e),
            )
        logger.error(f"[ad-studio] analyze_video error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="비디오 분석 중 오류가 발생했습니다.",
        )


@router.get(
    "/techniques",
    response_model=List[TechniqueInfo],
    summary="List available cinematic techniques",
)
async def list_techniques(
    category: Optional[str] = None,
) -> List[TechniqueInfo]:
    """Return all available cinematic techniques, optionally filtered by category."""
    try:
        from app.rag.cinematic_techniques import get_all_techniques

        techniques = get_all_techniques(category=category)
        return [
            TechniqueInfo(
                technique_id=t.technique_id,
                category=t.category,
                name_ko=t.name_ko,
                name_en=t.name_en,
                description_ko=t.description_ko,
                best_for=t.best_for,
            )
            for t in techniques
        ]
    except Exception as e:
        logger.error(f"[ad-studio] list_techniques error: {e}", exc_info=True)
        return []
