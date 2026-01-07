"""Dimension API endpoints for Crebit creative tools.

Primary API for dimension-based creative tools:
- POST /api/dimension/1d/generate  (Origin - Veo Prompt)
- POST /api/dimension/2d/create    (Blueprint - Storyboard)
- POST /api/dimension/3d/generate  (Ambience - Image Prompt)
- POST /api/dimension/4d/analyze   (Moment - Reference Analysis)

Uses server API key by default, supports BYOK via header.
Credits are deducted when using server API key (BYOK bypasses billing).

Note: This replaces the legacy /api/teaching/* endpoints.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.credit_service import deduct_credits, get_or_create_user_credits, refund_credits
from app.dimension_adapter import (
    execute_dimension_capsule,
    DimensionCapsuleId,
    ALLOWED_LANGUAGES,
    ALLOWED_MODELS,
    MAX_TOPIC_LENGTH,
    MAX_CONCEPT_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MIN_SCENE_COUNT,
    MAX_SCENE_COUNT,
)
from app.services.telemetry_integration import record_tool_run
from app.services.dlq_service import add_refund_failure_to_dlq

logger = logging.getLogger(__name__)

router = APIRouter()

# Refund retry configuration
REFUND_MAX_RETRIES = 3
REFUND_RETRY_BASE_DELAY_MS = 100


async def _refund_with_retry(
    db: AsyncSession,
    user_id: str,
    amount: int,
    description: str,
    meta: Optional[Dict[str, Any]] = None,
) -> bool:
    """Attempt to refund credits with exponential backoff retry.

    Critical security function: Ensures users get their credits back
    even if there are transient database issues. Failed refunds are
    added to DLQ for manual reconciliation.

    Args:
        db: Database session
        user_id: User to refund
        amount: Credit amount to refund
        description: Refund reason
        meta: Additional metadata

    Returns:
        True if refund succeeded, False if all retries failed
    """
    last_error: Optional[Exception] = None

    for attempt in range(REFUND_MAX_RETRIES):
        try:
            await refund_credits(
                db=db,
                user_id=user_id,
                amount=amount,
                description=description,
                meta=meta,
            )
            logger.info(f"Refund succeeded for user {user_id}: {amount} credits")
            return True
        except Exception as e:
            last_error = e
            logger.warning(f"Refund attempt {attempt + 1}/{REFUND_MAX_RETRIES} failed for user {user_id}: {e}")
            if attempt < REFUND_MAX_RETRIES - 1:
                delay = (REFUND_RETRY_BASE_DELAY_MS * (2 ** attempt)) / 1000
                await asyncio.sleep(delay)

    logger.error(f"CRITICAL: All refund attempts failed for user {user_id}, amount={amount}")

    # Add to DLQ for manual reconciliation
    try:
        await add_refund_failure_to_dlq(
            db=db,
            user_id=user_id,
            amount=amount,
            operation_type=description,
            error=last_error or Exception("Unknown refund failure"),
            context=meta,
        )
        logger.info(f"Added failed refund to DLQ for user {user_id}, amount={amount}")
    except Exception as dlq_error:
        logger.error(f"CRITICAL: Failed to add refund to DLQ: {dlq_error}")

    return False


# ============================================================================
# Dimension Mapping
# ============================================================================

DIMENSION_NAMES = {
    "1d": "Origin",      # Veo Prompt Generation
    "2d": "Blueprint",   # Storyboard Creation
    "3d": "Ambience",    # Image Prompt Generation
    "4d": "Moment",      # Reference Analysis
    # 4-Stage Workflow
    "story": "Story Architect",
    "sound": "Sound Crafter",
    "quality": "Quality Director",
    "aesthetic": "Aesthetic Director",
    "persona": "Persona Analyzer",
    "veo": "Video Maker",
}


# ============================================================================
# Credit Costs (Dynamic from teaching_capsules.py)
# ============================================================================

def get_credit_cost(capsule_id: DimensionCapsuleId, model: str) -> int:
    """캡슐과 모델에 따른 동적 크레딧 비용 계산."""
    from app.fixtures.dimension_capsules import DIMENSION_CAPSULES

    capsule_key_map = {
        DimensionCapsuleId.PROMPT_GENERATE: "teaching.prompt.generate",
        DimensionCapsuleId.STORYBOARD_CREATE: "teaching.storyboard.create",
        DimensionCapsuleId.IMAGE_GENERATE: "teaching.image.generate",
        DimensionCapsuleId.REFERENCE_ANALYZE: "teaching.reference.analyze",
        DimensionCapsuleId.QUALITY_CHECK: "dimension.quality.check",
        DimensionCapsuleId.AESTHETIC_DIRECT: "dimension.aesthetic.direct",
        DimensionCapsuleId.PERSONA_ANALYZE: "dimension.persona.analyze",
        DimensionCapsuleId.VEO_VIDEO_GENERATE: "veo.video.generate",
        DimensionCapsuleId.STORY_ARCHITECT: "dimension.story.architect",
        DimensionCapsuleId.SOUND_CRAFT: "dimension.sound.craft",
    }

    capsule_key = capsule_key_map.get(capsule_id)
    if not capsule_key:
        return 5

    for capsule in DIMENSION_CAPSULES:
        if capsule["capsule_key"] == capsule_key:
            credit_costs = capsule.get("credit_costs", {})
            return credit_costs.get(model, credit_costs.get("gemini-3-flash-preview", 5))

    return 5


# ============================================================================
# Request Models with Validation
# ============================================================================

class PromptGenerateRequest(BaseModel):
    """Request model for 1D Origin prompt generation."""
    topic: str = Field(..., min_length=1, max_length=MAX_TOPIC_LENGTH, description="Video topic or concept")
    style: str = Field("cinematic", max_length=50, description="Visual style")
    mood: str = Field("neutral", max_length=50, description="Mood/tone")
    duration: str = Field("15 seconds", max_length=20, description="Target duration")
    language: str = Field("ko", description="Output language")
    model: str = Field("gemini-3-flash-preview", description="AI model")
    
    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in ALLOWED_LANGUAGES:
            raise ValueError(f"Language must be one of: {ALLOWED_LANGUAGES}")
        return v
    
    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        if v not in ALLOWED_MODELS:
            raise ValueError(f"Model must be one of: {ALLOWED_MODELS}")
        return v


class StoryboardCreateRequest(BaseModel):
    """Request model for 2D Blueprint storyboard creation."""
    concept: str = Field(..., min_length=1, max_length=MAX_CONCEPT_LENGTH, description="Story concept")
    prompt: Optional[str] = Field(None, max_length=MAX_TOPIC_LENGTH, description="Optional Veo prompt")
    scene_count: int = Field(5, ge=MIN_SCENE_COUNT, le=MAX_SCENE_COUNT, description="Number of scenes")
    language: str = Field("ko", description="Output language")
    model: str = Field("gemini-3-flash-preview", description="AI model")
    
    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in ALLOWED_LANGUAGES:
            raise ValueError(f"Language must be one of: {ALLOWED_LANGUAGES}")
        return v


class ImageGenerateRequest(BaseModel):
    """Request model for 3D Ambience image prompt generation."""
    description: str = Field(..., min_length=1, max_length=MAX_DESCRIPTION_LENGTH, description="Image description")
    style: str = Field("photorealistic", max_length=50, description="Art style")
    aspect_ratio: str = Field("16:9", max_length=10, description="Image aspect ratio")
    model: str = Field("gemini-3-flash-preview", description="AI model")


class ReferenceAnalyzeRequest(BaseModel):
    """Request model for 4D Moment reference analysis."""
    video_description: str = Field(..., min_length=1, max_length=MAX_DESCRIPTION_LENGTH, description="Video description")
    focus_areas: List[str] = Field(
        default=["composition", "lighting", "color", "movement"],
        max_length=10,
        description="Analysis focus areas"
    )
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("focus_areas")
    @classmethod
    def validate_focus_areas(cls, v: List[str]) -> List[str]:
        return [area[:30] for area in v[:10]]


# ============================================================================
# Extended Dimension Capsule Request Models
# ============================================================================

class QualityCheckRequest(BaseModel):
    """Request model for Quality Checker."""
    content: str = Field(..., min_length=1, max_length=5000, description="Content to check")
    content_type: str = Field("text", max_length=50, description="Type of content: text, prompt, storyboard, image_prompt")
    criteria: List[str] = Field(
        default=["aesthetic", "consistency", "safety"],
        max_length=6,
        description="Quality criteria to evaluate"
    )
    threshold: int = Field(70, ge=0, le=100, description="Minimum passing score")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("criteria")
    @classmethod
    def validate_criteria(cls, v: List[str]) -> List[str]:
        valid = {"aesthetic", "ad_suitability", "consistency", "safety", "technical", "narrative"}
        return [c for c in v if c in valid][:6]


class AestheticDirectRequest(BaseModel):
    """Request model for Aesthetic Director."""
    concept: str = Field(..., min_length=1, max_length=MAX_CONCEPT_LENGTH, description="Creative concept")
    reference_style: str = Field("", max_length=50, description="Reference auteur style: bong, park, shinkai, lee, na, hong")
    mood: str = Field("neutral", max_length=50, description="Mood/atmosphere")
    target_medium: str = Field("video", max_length=30, description="Target medium: video, image, animation")
    use_rag: bool = Field(False, description="Use RAG for aesthetic references")
    model: str = Field("gemini-3-flash-preview", description="AI model")


class PersonaAnalyzeRequest(BaseModel):
    """Request model for Persona Analyzer (Abyss Interpreter)."""
    user_message: str = Field(..., min_length=1, max_length=MAX_TOPIC_LENGTH, description="User message")
    analysis_stage: str = Field("intro", max_length=30, description="Current analysis stage")
    persona_data: Dict[str, Any] = Field(default_factory=dict, description="Accumulated persona data")
    birth_info: Dict[str, Any] = Field(default_factory=dict, description="Birth info for Saju analysis")
    depth_level: str = Field("deep", max_length=20, description="Analysis depth: quick, medium, deep")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("analysis_stage")
    @classmethod
    def validate_stage(cls, v: str) -> str:
        valid_stages = {"intro", "saju", "mbti", "subconscious", "unconscious", "background", "synthesis"}
        return v.lower() if v.lower() in valid_stages else "intro"


class VeoGenerateRequest(BaseModel):
    """Request model for Veo 3.1 Video Generator."""
    prompt: str = Field(..., min_length=10, max_length=1000, description="Video generation prompt")
    negative_prompt: Optional[str] = Field(None, max_length=500, description="Negative prompt")
    aspect_ratio: str = Field("16:9", max_length=10, description="Aspect ratio: 16:9, 9:16, 1:1, 4:3")
    duration: int = Field(5, ge=5, le=10, description="Duration in seconds: 5 or 10")
    style: str = Field("cinematic", max_length=50, description="Style: cinematic, realistic, artistic, anime")
    seed: Optional[int] = Field(None, ge=0, description="Random seed for reproducibility")
    model: str = Field("veo-3.1", description="Veo model version")


class StoryArchitectRequest(BaseModel):
    """Request model for Story Architect (시나리오 생성기)."""
    concept: str = Field(..., min_length=10, max_length=3000, description="Video concept or idea")
    persona_data: Dict[str, Any] = Field(default_factory=dict, description="Persona data from Abyss Mirror")
    reference_analysis: Dict[str, Any] = Field(default_factory=dict, description="Analysis from Reference Decoder")
    genre: str = Field("drama", max_length=30, description="Genre: drama, ad, mv, documentary, short")
    duration: str = Field("60s", max_length=10, description="Target duration: 15s, 30s, 60s, 3m, 5m")
    structure: str = Field("3act", max_length=20, description="Story structure: 3act, hero, circular, montage")
    language: str = Field("ko", description="Output language")
    model: str = Field("gemini-2.5-pro", description="AI model")

    @field_validator("genre")
    @classmethod
    def validate_genre(cls, v: str) -> str:
        valid_genres = {"drama", "ad", "mv", "documentary", "short"}
        return v.lower() if v.lower() in valid_genres else "drama"

    @field_validator("structure")
    @classmethod
    def validate_structure(cls, v: str) -> str:
        valid_structures = {"3act", "hero", "circular", "montage"}
        return v.lower() if v.lower() in valid_structures else "3act"


class SoundCraftRequest(BaseModel):
    """Request model for Sound Crafter (사운드 크래프터)."""
    concept: str = Field(..., min_length=10, max_length=2000, description="Sound concept or mood description")
    storyboard: List[Dict[str, Any]] = Field(default_factory=list, description="Storyboard data for scene sync")
    sound_type: str = Field("bgm", max_length=20, description="Sound type: bgm, sfx, narration, full")
    mood: str = Field("neutral", max_length=50, description="Mood/atmosphere")
    genre: str = Field("cinematic", max_length=30, description="Music genre")
    tempo: str = Field("medium", max_length=20, description="Tempo: slow, medium, fast, dynamic")
    duration: str = Field("60s", max_length=10, description="Target duration")
    target_platform: str = Field("suno", max_length=20, description="Target platform: suno, udio, elevenlabs")
    language: str = Field("ko", description="Output language")
    model: str = Field("gemini-3-flash-preview", description="AI model")

    @field_validator("sound_type")
    @classmethod
    def validate_sound_type(cls, v: str) -> str:
        valid_types = {"bgm", "sfx", "narration", "full"}
        return v.lower() if v.lower() in valid_types else "bgm"

    @field_validator("target_platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        valid_platforms = {"suno", "udio", "elevenlabs"}
        return v.lower() if v.lower() in valid_platforms else "suno"


# ============================================================================
# Response Models
# ============================================================================

class MetricsResponse(BaseModel):
    """Execution metrics."""
    latency_ms: int
    tokens: int
    model: str


class DimensionResponse(BaseModel):
    """Standardized dimension tool response."""
    success: bool
    capsule_id: str
    output: Dict[str, Any]
    error: Optional[str] = None
    metrics: Optional[MetricsResponse] = None


class DimensionErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    capsule_id: str
    error: str
    detail: Optional[str] = None


# ============================================================================
# Dependency: BYOK Key Extraction
# ============================================================================

async def get_byok_key(
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key"),
) -> Optional[str]:
    """Extract optional BYOK key from header."""
    return x_gemini_api_key


# ============================================================================
# Helper: Execute with Credit Logic
# ============================================================================

async def _execute_dimension_tool(
    capsule_id: DimensionCapsuleId,
    tool_key: str,
    inputs: Dict[str, Any],
    model: str,
    user: dict,
    byok_key: Optional[str],
    db: AsyncSession,
    inputs_summary: Dict[str, Any],
    params: Optional[Dict[str, Any]] = None,
) -> DimensionResponse:
    """Execute dimension tool with credit deduction and telemetry.

    Args:
        capsule_id: Dimension capsule identifier
        tool_key: Tool name for telemetry
        inputs: Input data for the capsule
        model: AI model to use
        user: Current user dict
        byok_key: Optional BYOK API key
        db: Database session
        inputs_summary: Summary for telemetry
        params: Additional parameters (use_rag, threshold, etc.)
    """
    start_time = time.time()
    user_id = user.get("id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_USER", "message": "유효하지 않은 사용자입니다."}
        )
    
    # Credit check (skip for BYOK users)
    credit_cost = get_credit_cost(capsule_id, model)
    credits_deducted = False
    
    if not byok_key:
        user_credits = await get_or_create_user_credits(db, user_id)
        if user_credits.balance < credit_cost:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "code": "INSUFFICIENT_CREDITS",
                    "message": "크레딧이 부족합니다.",
                    "required": credit_cost,
                    "balance": user_credits.balance,
                }
            )
        await deduct_credits(
            db, user_id, credit_cost,
            description=f"Dimension: {tool_key}",
            meta={"tool": tool_key, "model": model}
        )
        credits_deducted = True
    
    result = None
    error_msg = None
    
    # Merge model into params
    execution_params = {"model": model}
    if params:
        execution_params.update(params)

    try:
        result = await execute_dimension_capsule(
            capsule_id=capsule_id.value,
            inputs=inputs,
            params=execution_params,
            user_api_key=byok_key,
        )
    except Exception as e:
        error_msg = f"실행 오류: {type(e).__name__}"
        logger.error(f"execute_dimension_capsule failed: {e}")
        result = {"success": False, "error": error_msg}
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    if not result or not result.get("success"):
        error_msg = error_msg or result.get("error", "Execution failed") if result else "Unknown error"
        
        # Refund on failure with retry
        if credits_deducted:
            await _refund_with_retry(
                db=db,
                user_id=user_id,
                amount=credit_cost,
                description=f"{tool_key} failed",
                meta={"tool": tool_key, "error": error_msg[:500]},
            )
        
        # Record failed run
        try:
            await record_tool_run(
                db=db,
                tool_key=tool_key,
                user_id=user_id,
                inputs_summary=inputs_summary,
                outputs_summary={},
                status="failed",
                latency_ms=latency_ms,
                credits_charged=0,
                error_message=error_msg[:500],
            )
        except Exception as tel_err:
            logger.warning(f"Telemetry recording failed: {tel_err}")
        
        if "timeout" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=error_msg)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg)
    
    # Record successful run
    try:
        await record_tool_run(
            db=db,
            tool_key=tool_key,
            user_id=user_id,
            inputs_summary={**inputs_summary, "model": model},
            outputs_summary={"success": True},
            status="success",
            latency_ms=latency_ms,
            credits_charged=credit_cost if credits_deducted else 0,
        )
    except Exception as tel_err:
        logger.warning(f"Telemetry recording failed: {tel_err}")
    
    return DimensionResponse(**result)


# ============================================================================
# 1D Origin - Veo Prompt Generation
# ============================================================================

@router.post(
    "/1d/generate",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse, "description": "Invalid input"},
        401: {"description": "Not authenticated"},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse, "description": "Generation failed"},
    },
    summary="1D Origin: Generate Veo Prompt",
    description="Generate a Veo 3.1 video prompt from topic, style, and mood.",
    tags=["Dimension 1D"],
)
async def generate_1d_prompt(
    request: PromptGenerateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Generate Veo video prompt (1D Origin)."""
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.PROMPT_GENERATE,
        tool_key="generate_veo_prompt",
        inputs={
            "topic": request.topic,
            "style": request.style,
            "mood": request.mood,
            "duration": request.duration,
            "language": request.language,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"topic": request.topic[:100], "style": request.style},
    )


# ============================================================================
# 2D Blueprint - Storyboard Creation
# ============================================================================

@router.post(
    "/2d/create",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="2D Blueprint: Create Storyboard",
    description="Create storyboard cards from a concept or video idea.",
    tags=["Dimension 2D"],
)
async def create_2d_storyboard(
    request: StoryboardCreateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Create storyboard cards (2D Blueprint)."""
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.STORYBOARD_CREATE,
        tool_key="create_storyboard",
        inputs={
            "concept": request.concept,
            "prompt": request.prompt,
            "scene_count": request.scene_count,
            "language": request.language,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"concept": request.concept[:100] if request.concept else "", "scene_count": request.scene_count},
    )


# ============================================================================
# 3D Ambience - Image Prompt Generation
# ============================================================================

@router.post(
    "/3d/generate",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="3D Ambience: Generate Image Prompt",
    description="Generate an optimized image prompt for AI generation.",
    tags=["Dimension 3D"],
)
async def generate_3d_image_prompt(
    request: ImageGenerateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Generate optimized image prompt (3D Ambience)."""
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.IMAGE_GENERATE,
        tool_key="generate_image_prompt",
        inputs={
            "description": request.description,
            "style": request.style,
            "aspect_ratio": request.aspect_ratio,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"description": request.description[:100] if request.description else "", "style": request.style},
    )


# ============================================================================
# 4D Moment - Reference Analysis
# ============================================================================

@router.post(
    "/4d/analyze",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="4D Moment: Analyze Reference",
    description="Analyze video reference for cinematic elements.",
    tags=["Dimension 4D"],
)
async def analyze_4d_reference(
    request: ReferenceAnalyzeRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Analyze video reference (4D Moment)."""
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.REFERENCE_ANALYZE,
        tool_key="analyze_reference",
        inputs={
            "video_description": request.video_description,
            "focus_areas": request.focus_areas,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"video_description": request.video_description[:100] if request.video_description else ""},
    )


# ============================================================================
# Extended Dimension Capsules
# ============================================================================

@router.post(
    "/quality/check",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Quality Checker: Evaluate Content",
    description="Evaluate content quality across 6 criteria.",
    tags=["Dimension Extended"],
)
async def check_quality(
    request: QualityCheckRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Check content quality (QC)."""
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.QUALITY_CHECK,
        tool_key="quality_check",
        inputs={
            "content": request.content,
            "content_type": request.content_type,
            "criteria": request.criteria,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"content_type": request.content_type, "criteria": request.criteria},
        params={"threshold": request.threshold},
    )


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
    """Generate aesthetic style guide (AD)."""
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.AESTHETIC_DIRECT,
        tool_key="aesthetic_direct",
        inputs={
            "concept": request.concept,
            "reference_style": request.reference_style,
            "mood": request.mood,
            "target_medium": request.target_medium,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"concept": request.concept[:100], "style": request.reference_style},
        params={"use_rag": request.use_rag},
    )


@router.post(
    "/persona/analyze",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Persona Analyzer: Deep Analysis",
    description="Perform deep persona analysis through multi-turn conversation.",
    tags=["Dimension Extended"],
)
async def analyze_persona(
    request: PersonaAnalyzeRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Analyze persona through conversation (AI)."""
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.PERSONA_ANALYZE,
        tool_key="persona_analyze",
        inputs={
            "user_message": request.user_message,
            "analysis_stage": request.analysis_stage,
            "persona_data": request.persona_data,
            "birth_info": request.birth_info,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"stage": request.analysis_stage, "depth": request.depth_level},
        params={"depth_level": request.depth_level},
    )


@router.post(
    "/veo/generate",
    response_model=DimensionResponse,
    responses={
        400: {"model": DimensionErrorResponse},
        402: {"model": DimensionErrorResponse, "description": "Insufficient credits"},
        500: {"model": DimensionErrorResponse},
    },
    summary="Veo 3.1: Generate Video",
    description="Generate video using Veo 3.1 from text prompt.",
    tags=["Dimension Extended"],
)
async def generate_veo_video(
    request: VeoGenerateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> DimensionResponse:
    """Generate video with Veo 3.1 (VEO)."""
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.VEO_VIDEO_GENERATE,
        tool_key="veo_generate",
        inputs={
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "aspect_ratio": request.aspect_ratio,
            "duration": request.duration,
            "style": request.style,
            "seed": request.seed,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"prompt": request.prompt[:100], "style": request.style},
    )


# ============================================================================
# 4-Stage Workflow: Story Architect
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
    """Generate video scenario (Story Architect)."""
    return await _execute_dimension_tool(
        capsule_id=DimensionCapsuleId.STORY_ARCHITECT,
        tool_key="story_architect",
        inputs={
            "concept": request.concept,
            "persona_data": request.persona_data,
            "reference_analysis": request.reference_analysis,
            "genre": request.genre,
            "duration": request.duration,
            "structure": request.structure,
            "language": request.language,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"concept": request.concept[:100], "genre": request.genre, "structure": request.structure},
        params={"use_rag": True},
    )


# ============================================================================
# 4-Stage Workflow: Sound Crafter
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
    """Generate music/sound prompts (Sound Crafter)."""
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
            "duration": request.duration,
            "target_platform": request.target_platform,
            "language": request.language,
        },
        model=request.model,
        user=user,
        byok_key=byok_key,
        db=db,
        inputs_summary={"concept": request.concept[:100], "sound_type": request.sound_type, "platform": request.target_platform},
        params={"use_rag": True},
    )


# ============================================================================
# Info Endpoints
# ============================================================================

@router.get(
    "/info",
    summary="Dimension Info",
    description="Get information about all dimensions.",
    tags=["Dimension Info"],
)
async def dimension_info() -> Dict[str, Any]:
    """List all dimensions and their purposes."""
    return {
        "dimensions": [
            # Classic Dimensions
            {"id": "1d", "name": "Origin", "description": "Veo 프롬프트 생성 - 비디오의 시작점", "endpoint": "/api/dimension/1d/generate"},
            {"id": "2d", "name": "Blueprint", "description": "스토리보드 생성 - 구조와 흐름", "endpoint": "/api/dimension/2d/create"},
            {"id": "3d", "name": "Ambience", "description": "이미지 프롬프트 생성 - 분위기와 시각", "endpoint": "/api/dimension/3d/generate"},
            {"id": "4d", "name": "Moment", "description": "레퍼런스 분석 - 순간 포착", "endpoint": "/api/dimension/4d/analyze"},
        ],
        "workflow_4stage": [
            # Stage 1: Planning
            {"id": "persona", "stage": "planning", "name": "Abyss Mirror", "description": "창작 DNA 분석", "endpoint": "/api/dimension/persona/analyze"},
            {"id": "reference", "stage": "planning", "name": "Reference Decoder", "description": "레퍼런스 해석", "endpoint": "/api/dimension/4d/analyze"},
            {"id": "story", "stage": "planning", "name": "Story Architect", "description": "시나리오 생성", "endpoint": "/api/dimension/story/architect"},
            {"id": "aesthetic", "stage": "planning", "name": "Aesthetic Director", "description": "미학 디렉팅", "endpoint": "/api/dimension/aesthetic/direct"},
            # Stage 2: Pre-production
            {"id": "sound", "stage": "pre_production", "name": "Sound Crafter", "description": "사운드/음악 프롬프트", "endpoint": "/api/dimension/sound/craft"},
            {"id": "storyboard", "stage": "pre_production", "name": "Storyboard Sketch", "description": "스토리보드 생성", "endpoint": "/api/dimension/2d/create"},
            {"id": "prompt", "stage": "pre_production", "name": "Prompt Alchemy", "description": "이미지 프롬프트", "endpoint": "/api/dimension/3d/generate"},
            # Stage 3: Production
            {"id": "visual", "stage": "production", "name": "Visual Realizer", "description": "키프레임 생성", "endpoint": "/api/dimension/3d/generate"},
            {"id": "video", "stage": "production", "name": "Video Maker", "description": "영상 생성", "endpoint": "/api/dimension/veo/generate"},
            # Stage 4: Finishing
            {"id": "quality", "stage": "finishing", "name": "Quality Director", "description": "품질 검수", "endpoint": "/api/dimension/quality/check"},
        ],
    }


@router.get(
    "/capsules",
    summary="List Capsules",
    description="List available dimension capsules with their inputs/outputs.",
    tags=["Dimension Info"],
)
async def list_capsules() -> Dict[str, Any]:
    """List available dimension capsules."""
    from app.fixtures.dimension_capsules import get_dimension_capsule_specs

    specs = get_dimension_capsule_specs()
    return {
        "capsules": [
            {"id": s["capsule_key"], "name": s["spec"]["name"], "description": s["spec"]["description"], "inputs": list(s["spec"].get("inputs", {}).keys())}
            for s in specs
        ]
    }


@router.get(
    "/health",
    summary="Health Check",
    description="Check dimension API health status.",
    tags=["Dimension Info"],
)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    from app.config import settings
    
    return {
        "status": "healthy",
        "api_key_configured": "yes" if settings.GEMINI_API_KEY else "no",
        "api_version": "dimension-v2",
    }


# ============================================================================
# Metrics Endpoints (Evidence Loop Integration)
# ============================================================================

@router.get("/metrics/stats", summary="Evidence Stats", tags=["Dimension Metrics"])
async def get_metrics_stats() -> Dict[str, Any]:
    """Get evidence collection statistics."""
    from app.agents.evidence_loop import get_evidence_stats
    return {"evidence": get_evidence_stats(), "api_version": "dimension-v2"}


@router.get("/metrics/session/{session_id}", summary="Session Metrics", tags=["Dimension Metrics"])
async def get_metrics_by_session(session_id: str) -> Dict[str, Any]:
    """Get metrics for a specific session."""
    from app.agents.evidence_loop import get_session_metrics
    return {"session_id": session_id, "metrics": get_session_metrics(session_id)}


@router.get("/metrics/tool/{tool_name}", summary="Tool Metrics", tags=["Dimension Metrics"])
async def get_metrics_by_tool(tool_name: str) -> Dict[str, Any]:
    """Get metrics for a specific tool."""
    from app.agents.evidence_loop import get_tool_metrics
    return {"tool_name": tool_name, "metrics": get_tool_metrics(tool_name)}


@router.get("/metrics/summary", summary="Metrics Summary", tags=["Dimension Metrics"])
async def get_metrics_summary() -> Dict[str, Any]:
    """Get aggregated metrics summary for all dimension tools."""
    from app.agents.evidence_loop import get_tool_metrics, get_evidence_stats
    
    DIMENSION_TOOLS = {
        "1d": "generate_veo_prompt",
        "2d": "create_storyboard",
        "3d": "generate_image_prompt",
        "4d": "analyze_reference",
        # 4-Stage Workflow
        "story": "story_architect",
        "sound": "sound_craft",
        "quality": "quality_check",
        "aesthetic": "aesthetic_direct",
        "persona": "persona_analyze",
        "veo": "veo_generate",
    }
    
    summary = {"dimensions": {}, "overall": get_evidence_stats()}
    for dim_id, tool_name in DIMENSION_TOOLS.items():
        tool_metrics = get_tool_metrics(tool_name)
        summary["dimensions"][dim_id] = {
            "name": DIMENSION_NAMES.get(dim_id, dim_id),
            "tool_name": tool_name,
            "total_executions": tool_metrics.get("total_executions", 0),
            "success_count": tool_metrics.get("success_count", 0),
            "completion_rate": tool_metrics.get("completion_rate", 0),
            "avg_latency_ms": tool_metrics.get("avg_latency_ms", 0),
        }
    return summary
