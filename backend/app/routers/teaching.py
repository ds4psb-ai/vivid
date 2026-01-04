"""Teaching API endpoints for Crebit teaching tools.

Provides lightweight API endpoints for teaching capsules:
- POST /api/teaching/prompt/generate
- POST /api/teaching/storyboard/create
- POST /api/teaching/image/generate
- POST /api/teaching/reference/analyze

Uses server API key by default, supports BYOK via header.
Rate limiting applied per-user.
Credits are deducted when using server API key (BYOK bypasses billing).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.credit_service import deduct_credits, get_or_create_user_credits, refund_credits
from app.teaching_adapter import (
    execute_teaching_capsule,
    TeachingCapsuleId,
    ALLOWED_LANGUAGES,
    ALLOWED_MODELS,
    MAX_TOPIC_LENGTH,
    MAX_CONCEPT_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MIN_SCENE_COUNT,
    MAX_SCENE_COUNT,
)
from app.services.telemetry_integration import record_tool_run

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Credit Costs (Dynamic from teaching_capsules.py)
# ============================================================================

def get_credit_cost(capsule_id: TeachingCapsuleId, model: str) -> int:
    """캡슐과 모델에 따른 동적 크레딧 비용 계산.
    
    Single Source of Truth: teaching_capsules.py에서 credit_costs 조회
    """
    from app.fixtures.teaching_capsules import TEACHING_CAPSULES
    
    capsule_key_map = {
        TeachingCapsuleId.PROMPT_GENERATE: "teaching.prompt.generate",
        TeachingCapsuleId.STORYBOARD_CREATE: "teaching.storyboard.create",
        TeachingCapsuleId.IMAGE_GENERATE: "teaching.image.generate",
        TeachingCapsuleId.REFERENCE_ANALYZE: "teaching.reference.analyze",
    }
    
    capsule_key = capsule_key_map.get(capsule_id)
    if not capsule_key:
        return 5  # fallback
    
    for capsule in TEACHING_CAPSULES:
        if capsule["capsule_key"] == capsule_key:
            credit_costs = capsule.get("credit_costs", {})
            return credit_costs.get(model, credit_costs.get("gemini-3-flash-preview", 5))
    
    return 5  # fallback


# Legacy compatibility - default costs
CREDIT_COSTS = {
    TeachingCapsuleId.PROMPT_GENERATE: 5,
    TeachingCapsuleId.STORYBOARD_CREATE: 10,
    TeachingCapsuleId.IMAGE_GENERATE: 5,
    TeachingCapsuleId.REFERENCE_ANALYZE: 8,
}


# ============================================================================
# Request Models with Validation
# ============================================================================

class PromptGenerateRequest(BaseModel):
    """Request model for prompt generation."""
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
    """Request model for storyboard creation."""
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
    """Request model for image prompt generation."""
    description: str = Field(..., min_length=1, max_length=MAX_DESCRIPTION_LENGTH, description="Image description")
    style: str = Field("photorealistic", max_length=50, description="Art style")
    aspect_ratio: str = Field("16:9", max_length=10, description="Image aspect ratio")
    model: str = Field("gemini-3-flash-preview", description="AI model")


class ReferenceAnalyzeRequest(BaseModel):
    """Request model for reference analysis."""
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
        return [area[:30] for area in v[:10]]  # Limit each area and total count


# ============================================================================
# Response Models
# ============================================================================

class MetricsResponse(BaseModel):
    """Execution metrics."""
    latency_ms: int
    tokens: int
    model: str


class TeachingResponse(BaseModel):
    """Standardized teaching capsule response."""
    success: bool
    capsule_id: str
    output: Dict[str, Any]
    error: Optional[str] = None
    metrics: Optional[MetricsResponse] = None


class TeachingErrorResponse(BaseModel):
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
    """Extract optional BYOK key from header.
    
    The key is never logged or stored.
    """
    return x_gemini_api_key


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/prompt/generate",
    response_model=TeachingResponse,
    responses={
        400: {"model": TeachingErrorResponse, "description": "Invalid input"},
        401: {"description": "Not authenticated"},
        402: {"model": TeachingErrorResponse, "description": "Insufficient credits"},
        500: {"model": TeachingErrorResponse, "description": "Generation failed"},
    },
    summary="Generate Veo Prompt",
    description="Generate a Veo 3.1 video prompt from topic, style, and mood.",
)
async def generate_prompt(
    request: PromptGenerateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> TeachingResponse:
    """Generate Veo video prompt from topic and style."""
    import time
    start_time = time.time()
    
    user_id = user.get("id")
    
    # Validate user_id
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_USER", "message": "유효하지 않은 사용자입니다."}
        )
    
    logger.info(f"Prompt generation request from user {user_id}")
    
    # Credit check (skip for BYOK users) - dynamic cost by model
    credit_cost = get_credit_cost(TeachingCapsuleId.PROMPT_GENERATE, request.model)
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
        # Deduct credits before execution
        await deduct_credits(
            db, user_id, credit_cost,
            description=f"Teaching: Prompt Generation",
            meta={"capsule": "prompt.generate", "model": request.model}
        )
        credits_deducted = True
    
    result = None
    error_msg = None
    
    try:
        result = await execute_teaching_capsule(
            capsule_id=TeachingCapsuleId.PROMPT_GENERATE.value,
            inputs={
                "topic": request.topic,
                "style": request.style,
                "mood": request.mood,
                "duration": request.duration,
                "language": request.language,
            },
            params={"model": request.model},
            user_api_key=byok_key,
        )
    except Exception as e:
        error_msg = f"실행 오류: {type(e).__name__}"
        logger.error(f"execute_teaching_capsule failed: {e}")
        result = {"success": False, "error": error_msg}
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    if not result or not result.get("success"):
        error_msg = error_msg or result.get("error", "Generation failed") if result else "Unknown error"
        
        # Refund on failure (only if we deducted) - wrapped in try-except
        if credits_deducted:
            try:
                await refund_credits(
                    db, user_id, credit_cost,
                    description=f"Refund: Prompt generation failed - {error_msg[:50]}",
                    meta={"capsule": "prompt.generate", "error": error_msg[:200]}
                )
            except Exception as refund_err:
                logger.error(f"CRITICAL: Refund failed for user {user_id}: {refund_err}")
                # Add to dead letter queue for manual reconciliation
                try:
                    from app.services.dlq_service import add_refund_failure_to_dlq
                    await add_refund_failure_to_dlq(
                        db=db,
                        user_id=user_id,
                        amount=credit_cost,
                        operation_type="prompt.generate",
                        error=refund_err,
                        context={"topic": request.topic[:100], "model": request.model},
                    )
                except Exception as dlq_err:
                    logger.error(f"CRITICAL: DLQ add also failed: {dlq_err}")
        
        # Record failed run (no settlement) - don't let this fail the response
        try:
            await record_tool_run(
                db=db,
                tool_key="generate_veo_prompt",
                user_id=user_id,
                inputs_summary={"topic": request.topic[:100], "style": request.style},
                outputs_summary={},
                status="failed",
                latency_ms=latency_ms,
                credits_charged=0,  # Refunded
                error_message=error_msg[:500],
            )
        except Exception as tel_err:
            logger.warning(f"Telemetry recording failed: {tel_err}")
        
        # Determine appropriate status code
        if "required" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
        elif "api key" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=error_msg)
        elif "timeout" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=error_msg)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg)
    
    # Record successful run → triggers settlement
    try:
        await record_tool_run(
            db=db,
            tool_key="generate_veo_prompt",
            user_id=user_id,
            inputs_summary={"topic": request.topic[:100], "style": request.style, "model": request.model},
            outputs_summary={"has_prompt": bool(result.get("output", {}).get("prompt"))},
            status="success",
            latency_ms=latency_ms,
            credits_charged=credit_cost if credits_deducted else 0,
        )
    except Exception as tel_err:
        logger.warning(f"Telemetry recording failed: {tel_err}")
    
    return TeachingResponse(**result)


@router.post(
    "/storyboard/create",
    response_model=TeachingResponse,
    responses={
        400: {"model": TeachingErrorResponse},
        402: {"model": TeachingErrorResponse, "description": "Insufficient credits"},
        500: {"model": TeachingErrorResponse},
    },
    summary="Create Storyboard",
    description="Create storyboard cards from a concept or video idea.",
)
async def create_storyboard(
    request: StoryboardCreateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> TeachingResponse:
    """Create storyboard cards from concept."""
    import time
    start_time = time.time()
    
    user_id = user.get("id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_USER", "message": "유효하지 않은 사용자입니다."}
        )
    
    logger.info(f"Storyboard creation request from user {user_id}")
    
    # Credit check (skip for BYOK users) - dynamic cost by model
    credit_cost = get_credit_cost(TeachingCapsuleId.STORYBOARD_CREATE, request.model)
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
            description=f"Teaching: Storyboard Creation",
            meta={"capsule": "storyboard.create", "model": request.model}
        )
        credits_deducted = True
    
    result = None
    error_msg = None
    
    try:
        result = await execute_teaching_capsule(
            capsule_id=TeachingCapsuleId.STORYBOARD_CREATE.value,
            inputs={
                "concept": request.concept,
                "prompt": request.prompt,
                "scene_count": request.scene_count,
                "language": request.language,
            },
            params={"model": request.model},
            user_api_key=byok_key,
        )
    except Exception as e:
        error_msg = f"실행 오류: {type(e).__name__}"
        logger.error(f"execute_teaching_capsule failed: {e}")
        result = {"success": False, "error": error_msg}
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    if not result or not result.get("success"):
        error_msg = error_msg or result.get("error", "Generation failed") if result else "Unknown error"
        
        if credits_deducted:
            try:
                await refund_credits(
                    db, user_id, credit_cost,
                    description=f"Refund: Storyboard creation failed",
                    meta={"capsule": "storyboard.create", "error": error_msg[:200]}
                )
            except Exception as refund_err:
                logger.error(f"CRITICAL: Refund failed for user {user_id}: {refund_err}")
                try:
                    from app.services.dlq_service import add_refund_failure_to_dlq
                    await add_refund_failure_to_dlq(
                        db=db, user_id=user_id, amount=credit_cost,
                        operation_type="storyboard.create", error=refund_err,
                        context={"concept": request.concept[:100] if request.concept else ""},
                    )
                except Exception as dlq_err:
                    logger.error(f"CRITICAL: DLQ add also failed: {dlq_err}")
        
        try:
            await record_tool_run(
                db=db,
                tool_key="create_storyboard",
                user_id=user_id,
                inputs_summary={"concept": request.concept[:100] if request.concept else "", "scene_count": request.scene_count},
                outputs_summary={},
                status="failed",
                latency_ms=latency_ms,
                credits_charged=0,
                error_message=error_msg[:500],
            )
        except Exception as tel_err:
            logger.warning(f"Telemetry recording failed: {tel_err}")
        
        if "required" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
        elif "timeout" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=error_msg)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg)
    
    try:
        await record_tool_run(
            db=db,
            tool_key="create_storyboard",
            user_id=user_id,
            inputs_summary={"concept": request.concept[:100] if request.concept else "", "scene_count": request.scene_count, "model": request.model},
            outputs_summary={"scene_count": len(result.get("output", {}).get("scenes", []))},
            status="success",
            latency_ms=latency_ms,
            credits_charged=credit_cost if credits_deducted else 0,
        )
    except Exception as tel_err:
        logger.warning(f"Telemetry recording failed: {tel_err}")
    
    return TeachingResponse(**result)


@router.post(
    "/image/generate",
    response_model=TeachingResponse,
    responses={
        400: {"model": TeachingErrorResponse},
        402: {"model": TeachingErrorResponse, "description": "Insufficient credits"},
        500: {"model": TeachingErrorResponse},
    },
    summary="Generate Image Prompt",
    description="Generate an optimized image prompt for AI generation.",
)
async def generate_image_prompt(
    request: ImageGenerateRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> TeachingResponse:
    """Generate optimized image prompt."""
    import time
    start_time = time.time()
    
    user_id = user.get("id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_USER", "message": "유효하지 않은 사용자입니다."}
        )
    
    logger.info(f"Image prompt request from user {user_id}")
    
    # Credit check (skip for BYOK users) - dynamic cost by model
    credit_cost = get_credit_cost(TeachingCapsuleId.IMAGE_GENERATE, request.model)
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
            description=f"Teaching: Image Prompt Generation",
            meta={"capsule": "image.generate", "model": request.model}
        )
        credits_deducted = True
    
    result = None
    error_msg = None
    
    try:
        result = await execute_teaching_capsule(
            capsule_id=TeachingCapsuleId.IMAGE_GENERATE.value,
            inputs={
                "description": request.description,
                "style": request.style,
                "aspect_ratio": request.aspect_ratio,
            },
            params={"model": request.model},
            user_api_key=byok_key,
        )
    except Exception as e:
        error_msg = f"실행 오류: {type(e).__name__}"
        logger.error(f"execute_teaching_capsule failed: {e}")
        result = {"success": False, "error": error_msg}
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    if not result or not result.get("success"):
        error_msg = error_msg or result.get("error", "Generation failed") if result else "Unknown error"
        
        if credits_deducted:
            try:
                await refund_credits(
                    db, user_id, credit_cost,
                    description=f"Refund: Image prompt generation failed",
                    meta={"capsule": "image.generate", "error": error_msg[:200]}
                )
            except Exception as refund_err:
                logger.error(f"CRITICAL: Refund failed for user {user_id}: {refund_err}")
                try:
                    from app.services.dlq_service import add_refund_failure_to_dlq
                    await add_refund_failure_to_dlq(
                        db=db, user_id=user_id, amount=credit_cost,
                        operation_type="image.generate", error=refund_err,
                        context={"description": request.description[:100]},
                    )
                except Exception as dlq_err:
                    logger.error(f"CRITICAL: DLQ add also failed: {dlq_err}")
        
        try:
            await record_tool_run(
                db=db,
                tool_key="generate_image_prompt",
                user_id=user_id,
                inputs_summary={"description": request.description[:100] if request.description else "", "style": request.style},
                outputs_summary={},
                status="failed",
                latency_ms=latency_ms,
                credits_charged=0,
                error_message=error_msg[:500],
            )
        except Exception as tel_err:
            logger.warning(f"Telemetry recording failed: {tel_err}")
        
        if "required" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
        elif "timeout" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=error_msg)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg)
    
    try:
        await record_tool_run(
            db=db,
            tool_key="generate_image_prompt",
            user_id=user_id,
            inputs_summary={"description": request.description[:100] if request.description else "", "style": request.style, "model": request.model},
            outputs_summary={"has_prompt": bool(result.get("output", {}).get("prompt"))},
            status="success",
            latency_ms=latency_ms,
            credits_charged=credit_cost if credits_deducted else 0,
        )
    except Exception as tel_err:
        logger.warning(f"Telemetry recording failed: {tel_err}")
    
    return TeachingResponse(**result)


@router.post(
    "/reference/analyze",
    response_model=TeachingResponse,
    responses={
        400: {"model": TeachingErrorResponse},
        402: {"model": TeachingErrorResponse, "description": "Insufficient credits"},
        500: {"model": TeachingErrorResponse},
    },
    summary="Analyze Reference",
    description="Analyze video reference for cinematic elements.",
)
async def analyze_reference(
    request: ReferenceAnalyzeRequest,
    user: dict = Depends(get_current_user),
    byok_key: Optional[str] = Depends(get_byok_key),
    db: AsyncSession = Depends(get_db),
) -> TeachingResponse:
    """Analyze video reference for cinematic elements."""
    import time
    start_time = time.time()
    
    user_id = user.get("id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_USER", "message": "유효하지 않은 사용자입니다."}
        )
    
    logger.info(f"Reference analysis request from user {user_id}")
    
    # Credit check (skip for BYOK users) - dynamic cost by model
    credit_cost = get_credit_cost(TeachingCapsuleId.REFERENCE_ANALYZE, request.model)
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
            description=f"Teaching: Reference Analysis",
            meta={"capsule": "reference.analyze", "model": request.model}
        )
        credits_deducted = True
    
    result = None
    error_msg = None
    
    try:
        result = await execute_teaching_capsule(
            capsule_id=TeachingCapsuleId.REFERENCE_ANALYZE.value,
            inputs={
                "video_description": request.video_description,
                "focus_areas": request.focus_areas,
            },
            params={"model": request.model},
            user_api_key=byok_key,
        )
    except Exception as e:
        error_msg = f"실행 오류: {type(e).__name__}"
        logger.error(f"execute_teaching_capsule failed: {e}")
        result = {"success": False, "error": error_msg}
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    if not result or not result.get("success"):
        error_msg = error_msg or result.get("error", "Analysis failed") if result else "Unknown error"
        
        if credits_deducted:
            try:
                await refund_credits(
                    db, user_id, credit_cost,
                    description=f"Refund: Reference analysis failed",
                    meta={"capsule": "reference.analyze", "error": error_msg[:200]}
                )
            except Exception as refund_err:
                logger.error(f"CRITICAL: Refund failed for user {user_id}: {refund_err}")
                try:
                    from app.services.dlq_service import add_refund_failure_to_dlq
                    await add_refund_failure_to_dlq(
                        db=db, user_id=user_id, amount=credit_cost,
                        operation_type="reference.analyze", error=refund_err,
                        context={"description": request.video_description[:100]},
                    )
                except Exception as dlq_err:
                    logger.error(f"CRITICAL: DLQ add also failed: {dlq_err}")
        
        try:
            await record_tool_run(
                db=db,
                tool_key="analyze_reference",
                user_id=user_id,
                inputs_summary={"video_description": request.video_description[:100] if request.video_description else ""},
                outputs_summary={},
                status="failed",
                latency_ms=latency_ms,
                credits_charged=0,
                error_message=error_msg[:500],
            )
        except Exception as tel_err:
            logger.warning(f"Telemetry recording failed: {tel_err}")
        
        if "required" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
        elif "timeout" in error_msg.lower():
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=error_msg)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg)
    
    try:
        await record_tool_run(
            db=db,
            tool_key="analyze_reference",
            user_id=user_id,
            inputs_summary={"video_description": request.video_description[:100] if request.video_description else "", "model": request.model},
            outputs_summary={"has_analysis": bool(result.get("output"))},
            status="success",
            latency_ms=latency_ms,
            credits_charged=credit_cost if credits_deducted else 0,
        )
    except Exception as tel_err:
        logger.warning(f"Telemetry recording failed: {tel_err}")
    
    return TeachingResponse(**result)


# ============================================================================
# Info Endpoints
# ============================================================================

@router.get(
    "/capsules",
    summary="List Capsules",
    description="List available teaching capsules with their inputs/outputs.",
)
async def list_teaching_capsules() -> Dict[str, Any]:
    """List available teaching capsules."""
    from app.fixtures.teaching_capsules import get_teaching_capsule_specs
    
    specs = get_teaching_capsule_specs()
    return {
        "capsules": [
            {
                "id": s["capsule_key"],
                "name": s["spec"]["name"],
                "description": s["spec"]["description"],
                "inputs": list(s["spec"].get("inputs", {}).keys()),
            }
            for s in specs
        ]
    }


@router.get(
    "/health",
    summary="Health Check",
    description="Check teaching API health status.",
)
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    from app.config import settings
    
    return {
        "status": "healthy",
        "api_key_configured": "yes" if settings.GEMINI_API_KEY else "no",
    }


# ============================================================================
# Kelly Credit Integration Endpoints
# ============================================================================

@router.get(
    "/kelly/check",
    summary="Kelly Allocation Check",
    description="Check Kelly-optimal credit allocation before execution.",
)
async def kelly_check(
    capsule_id: str = "prompt.generate",
    model: str = "gemini-3-flash-preview",
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Kelly 배분 확인 - 실행 전 최적 배분 체크."""
    from app.services.kelly_credit_service import kelly_credit_service
    
    user_id = user.get("id")
    
    # 캡슐 ID 파싱
    try:
        capsule_enum = TeachingCapsuleId(capsule_id)
    except ValueError:
        capsule_enum = TeachingCapsuleId.PROMPT_GENERATE
    
    credit_cost = get_credit_cost(capsule_enum, model)
    
    decision = await kelly_credit_service.check_kelly_allocation(
        db=db,
        user_id=user_id,
        credit_cost=credit_cost,
        model=model,
    )
    
    return {
        "should_execute": decision.should_execute,
        "warning": decision.warning,
        "recommendation": decision.recommendation,
        "allocation": decision.allocation.model_dump() if decision.allocation else None,
    }


@router.get(
    "/kelly/optimal-runs",
    summary="Get Optimal Runs",
    description="Calculate Kelly-optimal number of runs based on balance.",
)
async def get_optimal_runs(
    capsule_id: str = "prompt.generate",
    model: str = "gemini-3-flash-preview",
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """최적 실행 횟수 계산."""
    from app.services.kelly_credit_service import kelly_credit_service
    
    user_id = user.get("id")
    
    try:
        capsule_enum = TeachingCapsuleId(capsule_id)
    except ValueError:
        capsule_enum = TeachingCapsuleId.PROMPT_GENERATE
    
    credit_cost = get_credit_cost(capsule_enum, model)
    
    return await kelly_credit_service.get_optimal_runs(
        db=db,
        user_id=user_id,
        credit_cost=credit_cost,
        model=model,
    )
