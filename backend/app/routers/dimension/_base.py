"""
Dimension Router Base - Shared components for all dimension endpoints.

This module contains:
- Common imports and dependencies
- Request/Response models
- Helper functions (_execute_dimension_tool, _refund_with_retry)
- Validators and constants
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import StreamingResponse
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
from app.utils.sse_utils import (
    sse_progress,
    sse_complete,
    sse_error,
    sse_heartbeat,
    get_sse_headers,
)

logger = logging.getLogger(__name__)

# Refund retry configuration
REFUND_MAX_RETRIES = 3
REFUND_RETRY_BASE_DELAY_MS = 100


# ============================================================================
# Dimension Mapping
# ============================================================================

DIMENSION_NAMES = {
    "1d": "Origin",      # Veo Prompt Generation
    "2d": "Blueprint",   # Storyboard Creation
    "3d": "Ambience",    # Image Prompt Generation
    "4d": "Moment",      # Reference Analysis
    "qc": "Gate",        # Quality Check
    "ai": "Abyss",       # AI Persona Analysis
    "ad": "Aesthetic Director",
    "veo": "Video Maker",
}


# ============================================================================
# CapsuleId → Dimension Code mapping for Resolver
# ============================================================================

CAPSULE_TO_DIMENSION: Dict[DimensionCapsuleId, str] = {
    DimensionCapsuleId.PROMPT_GENERATE: "1D",
    DimensionCapsuleId.STORYBOARD_CREATE: "2D",
    DimensionCapsuleId.IMAGE_GENERATE: "3D",
    DimensionCapsuleId.REFERENCE_ANALYZE: "4D",
    DimensionCapsuleId.AESTHETIC_DIRECT: "AD",
    DimensionCapsuleId.AESTHETIC_MOODBOARD: "AD",
    DimensionCapsuleId.SOUND_CRAFT: "SOUND",
    DimensionCapsuleId.SOUND_MOODBOARD: "SOUND",
    DimensionCapsuleId.VEO_VIDEO_GENERATE: "VEO",
    DimensionCapsuleId.STORY_ARCHITECT: "STORY",
    DimensionCapsuleId.STORY_REFINE: "STORY",
    DimensionCapsuleId.QUALITY_CHECK: "QC",
    DimensionCapsuleId.PERSONA_ANALYZE: "AI",
    DimensionCapsuleId.CREATIVE_EDITOR: "QC",
}


# ============================================================================
# Credit Costs
# ============================================================================

# CapsuleId → Dimension Code mapping for SSoT lookup
_CAPSULE_TO_DIMENSION_CODE = {
    DimensionCapsuleId.PROMPT_GENERATE: "1d",
    DimensionCapsuleId.STORYBOARD_CREATE: "2d",
    DimensionCapsuleId.IMAGE_GENERATE: "3d",
    DimensionCapsuleId.REFERENCE_ANALYZE: "4d",
    DimensionCapsuleId.AESTHETIC_DIRECT: "ad",
    DimensionCapsuleId.AESTHETIC_MOODBOARD: "ad",
    DimensionCapsuleId.SOUND_CRAFT: "sound",
    DimensionCapsuleId.SOUND_MOODBOARD: "sound",
    DimensionCapsuleId.VEO_VIDEO_GENERATE: "veo",
    DimensionCapsuleId.STORY_ARCHITECT: "story",
    DimensionCapsuleId.STORY_REFINE: "story",
    DimensionCapsuleId.QUALITY_CHECK: "qc",
    DimensionCapsuleId.PERSONA_ANALYZE: "ai",
    DimensionCapsuleId.CREATIVE_EDITOR: "qc",
}

def get_credit_cost(capsule_id: DimensionCapsuleId, model: str) -> int:
    """캡슐과 모델에 따른 동적 크레딧 비용 계산.
    
    v2: AppRegistry SSoT 기반 동적 로딩 (하드코딩 폴백 유지).
    """
    # Model tier classification (2026 updated)
    MODEL_TIERS = {
        # Legacy models (deprecated)
        "gemini-1.5-flash": "flash",
        "gemini-1.5-pro": "pro",
        "gemini-2.0-flash-exp": "flash",
        # Current models (2025-2026)
        "gemini-3-flash-preview": "flash",
        "gemini-3-pro-preview": "pro",
        # Video generation
        "veo-3.1-generate-preview": "pro",
        # Image generation (Nano Banana Pro)
        "gemini-3-pro-image-preview": "pro",
    }

    # Credit multipliers per tier
    MODEL_CREDIT_MULTIPLIERS = {
        "flash": 1.0,
        "pro": 3.0,
    }
    
    base_cost = None
    
    # Try AppRegistry SSoT first
    try:
        from app.core.app_registry import AppRegistry
        
        dimension_code = _CAPSULE_TO_DIMENSION_CODE.get(capsule_id)
        if dimension_code:
            app_config = AppRegistry.get_by_name(dimension_code)
            if app_config:
                exec_cap = app_config.get_capability("execution")
                if exec_cap and exec_cap.config:
                    base_cost = exec_cap.config.get("credit_cost")
    except Exception:
        pass  # Fall through to hardcoded values
    
    # Fallback: hardcoded base credit costs
    if base_cost is None:
        BASE_CREDIT_COSTS = {
            DimensionCapsuleId.PROMPT_GENERATE: 5,
            DimensionCapsuleId.STORYBOARD_CREATE: 10,
            DimensionCapsuleId.IMAGE_GENERATE: 5,
            DimensionCapsuleId.REFERENCE_ANALYZE: 8,
            DimensionCapsuleId.QUALITY_CHECK: 8,
            DimensionCapsuleId.CREATIVE_EDITOR: 8,
            DimensionCapsuleId.AESTHETIC_DIRECT: 10,
            DimensionCapsuleId.AESTHETIC_MOODBOARD: 5,
            DimensionCapsuleId.PERSONA_ANALYZE: 5,
            DimensionCapsuleId.VEO_VIDEO_GENERATE: 200,
            DimensionCapsuleId.STORY_ARCHITECT: 10,
            DimensionCapsuleId.STORY_REFINE: 8,
            DimensionCapsuleId.SOUND_CRAFT: 8,
            DimensionCapsuleId.SOUND_MOODBOARD: 5,
        }
        DEFAULT_BASE_CREDIT_COST = 5
        base_cost = BASE_CREDIT_COSTS.get(capsule_id, DEFAULT_BASE_CREDIT_COST)

    tier = MODEL_TIERS.get(model, "flash")
    multiplier = MODEL_CREDIT_MULTIPLIERS.get(tier, 1.0)

    return int(base_cost * multiplier)


# ============================================================================
# Validation Constants
# ============================================================================

ALLOWED_ASPECT_RATIOS = {"16:9", "9:16", "1:1", "4:3", "3:4"}
ALLOWED_GENRES = {"drama", "thriller", "comedy", "documentary", "horror", "scifi", "ad", "mv", "short"}
ALLOWED_SOUND_TYPES = {"bgm", "sfx", "voiceover", "full_mix"}
ALLOWED_PLATFORMS = {"youtube", "instagram", "tiktok", "shorts", "vimeo", "general"}
ALLOWED_STRUCTURES = {"3-act", "hook-body-cta", "problem-solution", "story-arc", "montage", "interview"}
ALLOWED_VEO_DURATIONS = {4, 5, 6, 7, 8}


# ============================================================================
# Shared Validators
# ============================================================================

def _validate_language(v: str) -> str:
    """Validate language code."""
    if v not in ALLOWED_LANGUAGES:
        raise ValueError(f"지원하지 않는 언어입니다: {v}")
    return v


def _validate_model(v: str) -> str:
    """Validate AI model name."""
    if v not in ALLOWED_MODELS:
        raise ValueError(f"지원하지 않는 모델입니다: {v}")
    return v


def _validate_aspect_ratio(v: str) -> str:
    """Validate aspect ratio."""
    if v not in ALLOWED_ASPECT_RATIOS:
        raise ValueError(f"지원하지 않는 화면비입니다: {v}")
    return v


def _validate_veo_duration(v: int) -> int:
    """Validate Veo video duration."""
    if v not in ALLOWED_VEO_DURATIONS:
        raise ValueError(f"Veo 3.1 지원 영상 길이: 4, 5, 6, 7, 8초")
    return v


def _strip_string(v: str) -> str:
    """Strip whitespace from string."""
    return v.strip() if v else v


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
# Helper: Refund with Retry
# ============================================================================

async def _refund_with_retry(
    db: AsyncSession,
    user_id: str,
    amount: int,
    description: str,
    meta: Optional[Dict[str, Any]] = None,
) -> bool:
    """Attempt to refund credits with exponential backoff retry."""
    for attempt in range(REFUND_MAX_RETRIES):
        try:
            await refund_credits(
                db, user_id, amount,
                description=description,
                meta=meta or {}
            )
            logger.info(f"Refund succeeded: {amount} credits to user {user_id}")
            return True
        except Exception as e:
            delay = REFUND_RETRY_BASE_DELAY_MS * (2 ** attempt)
            logger.warning(f"Refund attempt {attempt + 1} failed: {e}, retrying in {delay}ms")
            await asyncio.sleep(delay / 1000)
    
    # All retries failed - add to DLQ
    logger.error(f"Refund failed after {REFUND_MAX_RETRIES} retries, adding to DLQ")
    try:
        await add_refund_failure_to_dlq(
            user_id=user_id,
            amount=amount,
            description=description,
            meta=meta or {},
            error="Refund failed after retries"
        )
    except Exception as dlq_err:
        logger.critical(f"Failed to add to DLQ: {dlq_err}")
    
    return False


# ============================================================================
# Helper: Extract Auteur Key
# ============================================================================

# Fallback auteur keys (used when AppRegistry unavailable)
_FALLBACK_AUTEUR_KEYS = ["bong", "nolan", "wong", "tarantino", "park", "shinkai"]

# Cache for dynamic auteur keys
_auteur_keys_cache: Optional[List[str]] = None

def _get_auteur_keys() -> List[str]:
    """SSoT: AppRegistry에서 거장 키 동적 조회 (캐싱 + 폴백).
    
    Returns:
        등록된 거장 키 목록
    """
    global _auteur_keys_cache
    
    if _auteur_keys_cache is not None:
        return _auteur_keys_cache
    
    try:
        from app.core.app_registry import AppRegistry
        from app.core.app_schema import AppType
        
        auteur_apps = AppRegistry.get_by_type(AppType.AUTEUR)
        if auteur_apps:
            _auteur_keys_cache = [app.metadata.name for app in auteur_apps]
            return _auteur_keys_cache
    except Exception:
        pass
    
    return _FALLBACK_AUTEUR_KEYS


def _extract_auteur_key(
    inputs: Dict[str, Any],
    intent: Optional[Any] = None,
) -> Optional[str]:
    """inputs와 intent에서 거장 키 추출.
    
    Args:
        inputs: 도구 입력
        intent: CreativeIntent (선택적)
        
    Returns:
        거장 키 또는 None
    """
    auteur_key = None
    auteur_keys = _get_auteur_keys()  # SSoT dynamic lookup
    
    # 1. Intent에서 추출
    if intent:
        rag_hints = getattr(intent, "rag_source_hints", None)
        if rag_hints:
            for hint in rag_hints:
                if isinstance(hint, str):
                    if hint.startswith("auteur."):
                        auteur_key = hint.replace("auteur.", "")
                        break
                    elif hint in auteur_keys:
                        auteur_key = hint
                        break
    
    # 2. Inputs에서 추출 (capsule_id, style 등)
    if not auteur_key:
        for field in ["capsule_id", "style", "auteur", "director"]:
            value = inputs.get(field, "") or ""
            value_lower = str(value).lower()
            for key in auteur_keys:
                if key in value_lower:
                    auteur_key = key
                    break
            if auteur_key:
                break
    
    return auteur_key


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
    intent: Optional[Any] = None,
) -> DimensionResponse:
    """Execute dimension tool with credit deduction, telemetry, and Intent-Resolver integration."""
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

    # Unified RAG → Resolver Pipeline
    dimension_code = CAPSULE_TO_DIMENSION.get(capsule_id, "1D")
    rag_context = None
    
    # Step 1: RAG Context 수집 (프리셋 기반)
    try:
        from app.rag.rag_presets import get_rag_preset, should_enable_rag
        from app.rag.rag_cache import get_rag_cache
        
        # 거장 키 추출
        auteur_key = _extract_auteur_key(inputs, intent)
        preset = get_rag_preset(dimension_code)
        
        if should_enable_rag(preset, auteur_key):
            topic = inputs.get("topic") or inputs.get("concept") or inputs.get("description") or ""
            if topic:
                query = f"{topic[:200]} - 시각적 스타일과 촬영 기법 참조"
                result = await get_rag_cache().get_or_query(
                    query=query,
                    auteur_key=auteur_key,
                    dimension=dimension_code if dimension_code != "AD" else None,
                    use_google_search=preset.use_google_search,
                )
                
                if result.confidence >= preset.confidence_threshold:
                    rag_context = {
                        "auteur_reference": result.answer[:preset.answer_max_length] if result.answer else None,
                        "sources": [
                            {"id": s.source_id, "title": s.title}
                            for s in (result.notebooklm_sources or [])[:preset.max_sources]
                        ],
                        "strategy": result.strategy_used,
                        "confidence": result.confidence,
                        "preset": dimension_code,
                    }
                    logger.debug(f"[{tool_key}] RAG context prepared: strategy={result.strategy_used}")
    except Exception as e:
        logger.debug(f"[{tool_key}] RAG context collection failed: {e}")
    
    # Step 2: Intent-Resolver Integration (with RAG context)
    if intent:
        try:
            from app.resolvers.integration import prepare_dimension_params
            inputs, execution_params = await prepare_dimension_params(
                dimension_code=dimension_code,
                inputs=inputs,
                params=execution_params,
                intent=intent,
                rag_context=rag_context,  # RAG 컨텍스트 전달
            )
            logger.debug(f"[{tool_key}] Intent-resolved with RAG: {dimension_code}")
        except ImportError:
            logger.debug(f"[{tool_key}] Resolver integration not available")
        except Exception as e:
            logger.warning(f"[{tool_key}] Intent resolution failed: {e}")
    
    # Step 3: RAG 컨텍스트를 inputs에도 추가 (캡슐에서 직접 사용 가능)
    if rag_context:
        inputs["_rag_context"] = rag_context


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
    
    # Handle result
    if result and result.get("success"):
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
        
        return DimensionResponse(
            success=True,
            capsule_id=capsule_id.value,
            output=result.get("output", {}),
            metrics=MetricsResponse(
                latency_ms=latency_ms,
                tokens=result.get("metrics", {}).get("tokens", 0),
                model=model,
            ),
        )
    else:
        # Refund on failure
        if credits_deducted:
            await _refund_with_retry(
                db=db,
                user_id=user_id,
                amount=credit_cost,
                description=f"{tool_key} failed",
                meta={"tool": tool_key, "error": str(error_msg)[:500] if error_msg else "Unknown"},
            )
        
        try:
            await record_tool_run(
                db=db,
                tool_key=tool_key,
                user_id=user_id,
                inputs_summary=inputs_summary,
                outputs_summary={},
                status="failure",
                latency_ms=latency_ms,
                credits_charged=0,
                error_message=error_msg,
            )
        except Exception as tel_err:
            logger.warning(f"Telemetry recording failed: {tel_err}")
        
        return DimensionResponse(
            success=False,
            capsule_id=capsule_id.value,
            output={},
            error=result.get("error") if result else error_msg,
        )


# ============================================================================
# Helper: Execute with Streaming
# ============================================================================

async def _execute_dimension_tool_stream(
    capsule_id: DimensionCapsuleId,
    tool_key: str,
    operation_name: str,
    inputs: Dict[str, Any],
    model: str,
    user: dict,
    byok_key: Optional[str],
    db: AsyncSession,
    inputs_summary: Dict[str, Any],
    params: Optional[Dict[str, Any]] = None,
    intent: Optional[Any] = None,
):
    """SSE streaming wrapper for dimension tool execution."""
    start_time = time.time()
    user_id = user.get("id")
    credits_deducted = False
    credit_cost = 0

    yield sse_progress(1, f"{operation_name} 시작...", "starting")

    try:
        if not user_id:
            yield sse_error("유효하지 않은 사용자입니다.", code="INVALID_USER")
            return

        credit_cost = get_credit_cost(capsule_id, model)

        if not byok_key:
            user_credits = await get_or_create_user_credits(db, user_id)
            if user_credits.balance < credit_cost:
                yield sse_error(
                    "크레딧이 부족합니다.",
                    code="INSUFFICIENT_CREDITS",
                    detail=f"필요: {credit_cost}, 보유: {user_credits.balance}",
                )
                return

            try:
                await deduct_credits(
                    db, user_id, credit_cost,
                    description=f"Dimension: {tool_key}",
                    meta={"tool": tool_key, "model": model}
                )
                credits_deducted = True
            except ValueError as e:
                if "insufficient" in str(e).lower():
                    yield sse_error(
                        "크레딧이 부족합니다. (동시 요청으로 인한 잔액 변동)",
                        code="INSUFFICIENT_CREDITS",
                    )
                else:
                    yield sse_error(str(e), code="CREDIT_ERROR")
                return

        yield sse_progress(10, f"{operation_name} 준비 중...", "processing")

        # Merge model into params
        execution_params = {"model": model}
        if params:
            execution_params.update(params)

        # Unified RAG → Resolver Pipeline (matches non-streaming)
        dimension_code = CAPSULE_TO_DIMENSION.get(capsule_id, "1D")
        rag_context = None
        
        # Step 1: RAG Context 수집 (프리셋 기반)
        try:
            from app.rag.rag_presets import get_rag_preset, should_enable_rag
            from app.rag.rag_cache import get_rag_cache
            
            auteur_key = _extract_auteur_key(inputs, intent)
            preset = get_rag_preset(dimension_code)
            
            if should_enable_rag(preset, auteur_key):
                topic = inputs.get("topic") or inputs.get("concept") or inputs.get("description") or ""
                if topic:
                    query = f"{topic[:200]} - 시각적 스타일과 촬영 기법 참조"
                    result = await get_rag_cache().get_or_query(
                        query=query,
                        auteur_key=auteur_key,
                        dimension=dimension_code if dimension_code != "AD" else None,
                        use_google_search=preset.use_google_search,
                    )
                    
                    if result.confidence >= preset.confidence_threshold:
                        rag_context = {
                            "auteur_reference": result.answer[:preset.answer_max_length] if result.answer else None,
                            "sources": [
                                {"id": s.source_id, "title": s.title}
                                for s in (result.notebooklm_sources or [])[:preset.max_sources]
                            ],
                            "strategy": result.strategy_used,
                            "confidence": result.confidence,
                            "preset": dimension_code,
                        }
        except Exception as e:
            logger.debug(f"[{tool_key}] Stream: RAG collection failed: {e}")
        
        # Step 2: Intent-Resolver Integration (with RAG context)
        if intent:
            try:
                from app.resolvers.integration import prepare_dimension_params
                inputs, execution_params = await prepare_dimension_params(
                    dimension_code=dimension_code,
                    inputs=inputs,
                    params=execution_params,
                    intent=intent,
                    rag_context=rag_context,
                )
                logger.debug(f"[{tool_key}] Stream: Intent-resolved with RAG")
            except Exception as e:
                logger.warning(f"[{tool_key}] Stream: Intent resolution failed: {e}")
        
        # Step 3: RAG 컨텍스트를 inputs에도 추가
        if rag_context:
            inputs["_rag_context"] = rag_context

        yield sse_progress(30, f"{operation_name} 처리 중...", "processing")

        result = await execute_dimension_capsule(
            capsule_id=capsule_id.value,
            inputs=inputs,
            params=execution_params,
            user_api_key=byok_key,
        )

        yield sse_progress(90, f"{operation_name} 완료 중...", "finalizing")

        latency_ms = int((time.time() - start_time) * 1000)

        if result and result.get("success"):
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

            metrics = result.get("metrics", {})
            metrics["latency_ms"] = latency_ms
            metrics["credits_charged"] = credit_cost if credits_deducted else 0
            yield sse_complete(result.get("output", {}), metrics)
        else:
            error_msg = result.get("error", "Execution failed") if result else "Unknown error"

            if credits_deducted:
                await _refund_with_retry(
                    db=db,
                    user_id=user_id,
                    amount=credit_cost,
                    description=f"{tool_key} failed",
                    meta={"tool": tool_key, "error": error_msg[:500]},
                )

            try:
                await record_tool_run(
                    db=db,
                    tool_key=tool_key,
                    user_id=user_id,
                    inputs_summary=inputs_summary,
                    outputs_summary={},
                    status="failure",
                    latency_ms=latency_ms,
                    credits_charged=0,
                    error_message=error_msg,
                )
            except Exception as tel_err:
                logger.warning(f"Telemetry recording failed: {tel_err}")

            yield sse_error(error_msg, code="EXECUTION_FAILED")

    except asyncio.CancelledError:
        if credits_deducted:
            try:
                await _refund_with_retry(
                    db=db,
                    user_id=user_id,
                    amount=credit_cost,
                    description=f"{tool_key} cancelled",
                    meta={"tool": tool_key, "reason": "client_disconnect"},
                )
            except Exception as refund_err:
                logger.error(f"Refund on cancel failed: {refund_err}")
        raise
    except Exception as e:
        logger.error(f"{tool_key} stream error: {e}")
        
        if credits_deducted:
            await _refund_with_retry(
                db=db,
                user_id=user_id,
                amount=credit_cost,
                description=f"{tool_key} error",
                meta={"tool": tool_key, "error": str(e)[:500]},
            )
        
        yield sse_error(f"실행 중 오류: {type(e).__name__}", code="INTERNAL_ERROR")


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Dependencies
    "get_db",
    "get_current_user",
    "get_byok_key",
    # Helpers
    "_execute_dimension_tool",
    "_execute_dimension_tool_stream",
    "_refund_with_retry",
    "get_credit_cost",
    # Validators
    "_validate_language",
    "_validate_model",
    "_validate_aspect_ratio",
    "_validate_veo_duration",
    "_strip_string",
    # Response models
    "DimensionResponse",
    "DimensionErrorResponse",
    "MetricsResponse",
    # Mappings
    "DIMENSION_NAMES",
    "CAPSULE_TO_DIMENSION",
    # Constants
    "ALLOWED_ASPECT_RATIOS",
    "ALLOWED_GENRES",
    "ALLOWED_SOUND_TYPES",
    "ALLOWED_PLATFORMS",
    "ALLOWED_STRUCTURES",
    "ALLOWED_VEO_DURATIONS",
    # Re-exports from dimension_adapter
    "DimensionCapsuleId",
    "ALLOWED_LANGUAGES",
    "ALLOWED_MODELS",
    "MAX_TOPIC_LENGTH",
    "MAX_CONCEPT_LENGTH",
    "MAX_DESCRIPTION_LENGTH",
    "MIN_SCENE_COUNT",
    "MAX_SCENE_COUNT",
    # FastAPI
    "APIRouter",
    "Depends",
    "Header",
    "HTTPException",
    "status",
    "StreamingResponse",
    # Pydantic
    "BaseModel",
    "Field",
    "field_validator",
    # SSE
    "sse_progress",
    "sse_complete",
    "sse_error",
    "sse_heartbeat",
    "get_sse_headers",
    # Other
    "logger",
    "AsyncSession",
    "Optional",
    "Dict",
    "List",
    "Any",
]
