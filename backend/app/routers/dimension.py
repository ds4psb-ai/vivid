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

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Dimension Mapping
# ============================================================================

DIMENSION_NAMES = {
    "1d": "Origin",      # Veo Prompt Generation
    "2d": "Blueprint",   # Storyboard Creation
    "3d": "Ambience",    # Image Prompt Generation
    "4d": "Moment",      # Reference Analysis
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
) -> DimensionResponse:
    """Execute dimension tool with credit deduction and telemetry."""
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
    
    try:
        result = await execute_dimension_capsule(
            capsule_id=capsule_id.value,
            inputs=inputs,
            params={"model": model},
            user_api_key=byok_key,
        )
    except Exception as e:
        error_msg = f"실행 오류: {type(e).__name__}"
        logger.error(f"execute_dimension_capsule failed: {e}")
        result = {"success": False, "error": error_msg}
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    if not result or not result.get("success"):
        error_msg = error_msg or result.get("error", "Execution failed") if result else "Unknown error"
        
        # Refund on failure
        if credits_deducted:
            try:
                await refund_credits(
                    db, user_id, credit_cost,
                    description=f"Refund: {tool_key} failed",
                    meta={"tool": tool_key, "error": error_msg[:200]}
                )
            except Exception as refund_err:
                logger.error(f"CRITICAL: Refund failed for user {user_id}: {refund_err}")
        
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
            {"id": "1d", "name": "Origin", "description": "Veo 프롬프트 생성 - 비디오의 시작점", "endpoint": "/api/dimension/1d/generate"},
            {"id": "2d", "name": "Blueprint", "description": "스토리보드 생성 - 구조와 흐름", "endpoint": "/api/dimension/2d/create"},
            {"id": "3d", "name": "Ambience", "description": "이미지 프롬프트 생성 - 분위기와 시각", "endpoint": "/api/dimension/3d/generate"},
            {"id": "4d", "name": "Moment", "description": "레퍼런스 분석 - 순간 포착", "endpoint": "/api/dimension/4d/analyze"},
        ]
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
    
    DIMENSION_TOOLS = {"1d": "generate_veo_prompt", "2d": "create_storyboard", "3d": "generate_image_prompt", "4d": "analyze_reference"}
    
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
