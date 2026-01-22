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
from app.utils.error_sanitize import safe_error_detail
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
    sse_event,
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
    DimensionCapsuleId.JSON_GEN_CONVERT: "JSON_GEN",
    DimensionCapsuleId.NANOBANANA_CONVERT: "3D",  # Reuse 3D Resolver
    DimensionCapsuleId.PROMPT_TRANSLATE: "PROMPT",  # Prompt Alchemy
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
    DimensionCapsuleId.JSON_GEN_CONVERT: "json_gen",
    DimensionCapsuleId.NANOBANANA_CONVERT: "nanobanana",
    DimensionCapsuleId.PROMPT_TRANSLATE: "prompt",  # Prompt Alchemy
}

def get_credit_cost(
    capsule_id: DimensionCapsuleId, 
    model: str,
    credit_multiplier: float = 1.0,  # P3: Multi-mode multiplier
) -> int:
    """캡슐과 모델에 따른 동적 크레딧 비용 계산.
    
    v2: AppRegistry SSoT 기반 동적 로딩 (하드코딩 폴백 유지).
    v3: credit_multiplier 지원 (P3 multi-mode QC).
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
    except Exception as e:
        logger.debug(f"[get_credit_cost] Dynamic config lookup failed, using hardcoded: {e}")
    
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
            DimensionCapsuleId.PROMPT_TRANSLATE: 5,  # Prompt Alchemy
        }
        DEFAULT_BASE_CREDIT_COST = 5
        base_cost = BASE_CREDIT_COSTS.get(capsule_id, DEFAULT_BASE_CREDIT_COST)

    tier = MODEL_TIERS.get(model, "flash")
    model_multiplier = MODEL_CREDIT_MULTIPLIERS.get(tier, 1.0)

    # Apply both model tier multiplier and credit_multiplier (P3)
    return int(base_cost * model_multiplier * credit_multiplier)


# ============================================================================
# Validation Constants
# ============================================================================

ALLOWED_ASPECT_RATIOS = {"16:9", "9:16", "1:1", "4:3", "3:4"}
ALLOWED_GENRES = {"drama", "thriller", "comedy", "documentary", "horror", "scifi", "ad", "mv", "short"}
ALLOWED_SOUND_TYPES = {"bgm", "sfx", "voiceover", "full_mix"}
ALLOWED_PLATFORMS = {"youtube", "instagram", "tiktok", "shorts", "vimeo", "general"}
ALLOWED_STRUCTURES = {"3-act", "5-act", "hook-body-cta", "problem-solution", "story-arc", "montage", "interview", "hero-journey", "nonlinear", "slice-of-life"}
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
    credits_charged: int = 0  # Added for accurate cost tracking


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
    except Exception as e:
        logger.debug(f"[get_auteur_keys] Registry lookup failed, using fallback: {e}")
    
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
    skip_credit_deduction: bool = False,
) -> DimensionResponse:
    """Execute dimension tool with credit deduction, telemetry, and Intent-Resolver integration.

    Args:
        skip_credit_deduction: True면 크레딧 차감 건너뜀 (run-token이 이미 처리한 경우).
    """
    start_time = time.time()
    user_id = user.get("id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_USER", "message": "유효하지 않은 사용자입니다."}
        )

    # P3: Get credit_multiplier from params (default 1.0)
    credit_multiplier = (params or {}).get("credit_multiplier", 1.0)

    # Credit check (skip for BYOK users or run-token flow)
    credit_cost = get_credit_cost(capsule_id, model, credit_multiplier)
    credits_deducted = False


    if not byok_key and not skip_credit_deduction:
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
        # === Legacy Cleanup: migrate from get_rag_cache → hybrid_query ===
        from app.rag.hybrid_rag import hybrid_query
        
        # 거장 키 추출
        auteur_key = _extract_auteur_key(inputs, intent)
        preset = get_rag_preset(dimension_code)
        
        if should_enable_rag(preset, auteur_key):
            topic = inputs.get("topic") or inputs.get("concept") or inputs.get("description") or ""
            if topic:
                query = f"{topic[:200]} - 시각적 스타일과 촬영 기법 참조"
                result = await hybrid_query(
                    query=query,
                    auteur_key=auteur_key,
                    dimension=dimension_code if dimension_code != "AD" else None,
                    use_google_search=preset.use_google_search,
                    use_semantic_cache=True,
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
        
        # === evidence_refs SoR 연결 (JSON Gen + Nanobanana만) ===
        ADAPTER_CAPSULES = {
            DimensionCapsuleId.JSON_GEN_CONVERT,
            DimensionCapsuleId.NANOBANANA_CONVERT,
        }
        
        if capsule_id in ADAPTER_CAPSULES:
            try:
                from app.models import CapsuleRun
                from app.core.app_registry import AppRegistry
                
                # capsule_version: capsule_key로 조회, latest 폴백
                capsule_version = "latest"
                try:
                    app_config = AppRegistry.get_by_capsule_key(capsule_id.value)
                    if app_config and app_config.metadata:
                        capsule_version = app_config.metadata.version or "latest"
                except Exception:
                    pass
                
                # inputs_summary 보강 (shot/scene/sequence 누락 시)
                run_inputs = dict(inputs_summary)
                for key in ("shot_id", "sequence_id", "scene_id"):
                    if key not in run_inputs and key in inputs:
                        run_inputs[key] = inputs[key]
                
                capsule_run = CapsuleRun(
                    user_id=user_id,
                    capsule_key=capsule_id.value,
                    capsule_version=capsule_version,
                    status="done",
                    inputs=run_inputs,
                    summary={"shot_contract": result.get("output", {}).get("shot_contract")},
                    evidence_refs=[],  # 임시, flush 후 갱신
                )
                db.add(capsule_run)
                await db.flush()
                
                # evidence_refs를 실제 ID로 교체 (응답 + CapsuleRun 동기화)
                canonical_ref = f"db:capsule_runs:{capsule_run.id}"
                result.setdefault("output", {})["evidence_refs"] = [canonical_ref]
                capsule_run.evidence_refs = [canonical_ref]
                
            except Exception as run_err:
                logger.warning(f"CapsuleRun save failed (non-blocking): {run_err}")
        
        # P6-2: Sanitize evidence_refs in output before returning
        output = result.get("output", {})
        if "evidence_refs" in output and isinstance(output.get("evidence_refs"), list):
            try:
                from app.agents.tool_utils import filter_evidence_refs
                filtered_refs, warnings = filter_evidence_refs(output["evidence_refs"])
                output["evidence_refs"] = filtered_refs
                if warnings:
                    logger.debug(f"[P6-2] evidence_refs filtered: {warnings}")
            except Exception as filter_err:
                logger.warning(f"[P6-2] filter_evidence_refs failed: {filter_err}")
        
        return DimensionResponse(
            success=True,
            capsule_id=capsule_id.value,
            output=output,
            metrics=MetricsResponse(
                latency_ms=latency_ms,
                tokens=result.get("metrics", {}).get("tokens", 0),
                model=model,
                credits_charged=credit_cost if credits_deducted else 0,
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

        # P3: Get credit_multiplier from params (default 1.0)
        credit_multiplier = (params or {}).get("credit_multiplier", 1.0)
        credit_cost = get_credit_cost(capsule_id, model, credit_multiplier)

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
            # === Legacy Cleanup: migrate from get_rag_cache → hybrid_query ===
            from app.rag.hybrid_rag import hybrid_query
            
            auteur_key = _extract_auteur_key(inputs, intent)
            preset = get_rag_preset(dimension_code)
            
            if should_enable_rag(preset, auteur_key):
                topic = inputs.get("topic") or inputs.get("concept") or inputs.get("description") or ""
                if topic:
                    query = f"{topic[:200]} - 시각적 스타일과 촬영 기법 참조"
                    result = await hybrid_query(
                        query=query,
                        auteur_key=auteur_key,
                        dimension=dimension_code if dimension_code != "AD" else None,
                        use_google_search=preset.use_google_search,
                        use_semantic_cache=True,
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
# Helper: Execute with UQSL Multi-Generate
# ============================================================================

async def _execute_dimension_tool_multi(
    capsule_id: DimensionCapsuleId,
    tool_key: str,
    inputs: Dict[str, Any],
    model: str,
    user: dict,
    byok_key: Optional[str],
    db: AsyncSession,
    inputs_summary: Dict[str, Any],
    n_candidates: int = 3,
    strategy: str = "auto",
    params: Optional[Dict[str, Any]] = None,
    intent: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Execute dimension tool with UQSL multi-candidate generation.

    2026 Best Practice:
    - Generates N candidates in parallel with varied parameters
    - Evaluates quality for each candidate (groundedness, relevance, etc.)
    - Uses Thompson Sampling to recommend best candidate
    - Returns UQSL-compatible response with all candidates and scores

    Args:
        capsule_id: The dimension capsule to execute
        tool_key: Tool identifier for telemetry
        inputs: Capsule inputs
        model: AI model to use
        user: Authenticated user
        byok_key: Optional BYOK API key
        db: Database session
        inputs_summary: Summary for telemetry
        n_candidates: Number of candidates to generate (default: 3)
        strategy: Selection strategy - "auto", "quality", "hitl" (default: "auto")
        params: Additional execution parameters
        intent: Optional CreativeIntent for RAG integration

    Returns:
        UQSL response with session_id, candidates, quality_scores, recommended_idx
    """
    import asyncio
    import uuid
    import hashlib
    from datetime import datetime

    start_time = time.time()
    user_id = user.get("id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_USER", "message": "유효하지 않은 사용자입니다."}
        )

    # P3: Get credit_multiplier from params (default 1.0)
    credit_multiplier = (params or {}).get("credit_multiplier", 1.0)

    # Calculate total credit cost (N candidates × single cost)
    single_cost = get_credit_cost(capsule_id, model, credit_multiplier)
    total_cost = single_cost * n_candidates
    credits_deducted = False

    if not byok_key:
        user_credits = await get_or_create_user_credits(db, user_id)
        if user_credits.balance < total_cost:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "code": "INSUFFICIENT_CREDITS",
                    "message": "크레딧이 부족합니다.",
                    "required": total_cost,
                    "balance": user_credits.balance,
                }
            )
        await deduct_credits(
            db, user_id, total_cost,
            description=f"Dimension Multi: {tool_key} x{n_candidates}",
            meta={"tool": tool_key, "model": model, "n_candidates": n_candidates}
        )
        credits_deducted = True

    # Merge model into params
    execution_params = {"model": model}
    if params:
        execution_params.update(params)

    # RAG context preparation (same as single execution)
    dimension_code = CAPSULE_TO_DIMENSION.get(capsule_id, "1D")
    rag_context = None

    try:
        from app.rag.rag_presets import get_rag_preset, should_enable_rag
        from app.rag.hybrid_rag import hybrid_query

        auteur_key = _extract_auteur_key(inputs, intent)
        preset = get_rag_preset(dimension_code)

        if should_enable_rag(preset, auteur_key):
            topic = inputs.get("topic") or inputs.get("concept") or inputs.get("description") or ""
            if topic:
                query = f"{topic[:200]} - 시각적 스타일과 촬영 기법 참조"
                rag_result = await hybrid_query(
                    query=query,
                    auteur_key=auteur_key,
                    dimension=dimension_code if dimension_code != "AD" else None,
                    use_google_search=preset.use_google_search,
                    use_semantic_cache=True,
                )

                if rag_result.confidence >= preset.confidence_threshold:
                    rag_context = {
                        "auteur_reference": rag_result.answer[:preset.answer_max_length] if rag_result.answer else None,
                        "sources": [
                            {"id": s.source_id, "title": s.title}
                            for s in (rag_result.notebooklm_sources or [])[:preset.max_sources]
                        ],
                        "strategy": rag_result.strategy_used,
                        "confidence": rag_result.confidence,
                    }
    except Exception as e:
        logger.debug(f"[{tool_key}] Multi: RAG collection failed: {e}")

    if rag_context:
        inputs["_rag_context"] = rag_context

    # Generate N candidates in parallel
    candidates = []
    generation_errors = []

    async def generate_candidate(idx: int) -> Dict[str, Any]:
        """Generate single candidate with varied temperature."""
        try:
            # Vary temperature for diversity
            temp = 0.7 + (idx * 0.3 / n_candidates)
            candidate_params = {**execution_params, "temperature": temp, "seed": idx * 1000}

            result = await execute_dimension_capsule(
                capsule_id=capsule_id.value,
                inputs=inputs,
                params=candidate_params,
                user_api_key=byok_key,
            )

            return {
                "idx": idx,
                "content": result.get("output", {}),
                "success": result.get("success", False),
                "metadata": {"seed": idx * 1000, "temperature": temp},
                "backend_used": dimension_code.lower(),
            }
        except Exception as e:
            logger.warning(f"Candidate {idx} generation failed: {e}")
            return {
                "idx": idx,
                "content": {},
                "success": False,
                "error": str(e),
                "metadata": {},
                "backend_used": "failed",
            }

    # Execute in parallel
    tasks = [asyncio.create_task(generate_candidate(i)) for i in range(n_candidates)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for r in results:
        if isinstance(r, Exception):
            generation_errors.append(str(r))
        elif isinstance(r, dict):
            if r.get("success"):
                candidates.append(r)
            else:
                generation_errors.append(r.get("error", "Unknown error"))

    # Sort by index
    candidates.sort(key=lambda c: c["idx"])

    # If all failed, refund and raise error
    if not candidates:
        if credits_deducted:
            await _refund_with_retry(
                db=db,
                user_id=user_id,
                amount=total_cost,
                description=f"{tool_key} multi all failed",
                meta={"errors": generation_errors[:3]},
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "ALL_CANDIDATES_FAILED", "errors": generation_errors[:3]}
        )

    # Partial refund for failed candidates
    failed_count = n_candidates - len(candidates)
    if credits_deducted and failed_count > 0:
        refund_amount = single_cost * failed_count
        await _refund_with_retry(
            db=db,
            user_id=user_id,
            amount=refund_amount,
            description=f"{tool_key} multi partial refund",
            meta={"failed_count": failed_count},
        )

    # Evaluate quality using UQSL evaluator
    quality_scores = []
    try:
        from app.uqsl.quality_evaluator import get_quality_evaluator
        from app.uqsl.models import CandidateResult

        evaluator = get_quality_evaluator()

        for c in candidates:
            # Convert to UQSL CandidateResult format
            content_str = json.dumps(c["content"]) if isinstance(c["content"], dict) else str(c["content"])
            candidate_result = CandidateResult(
                idx=c["idx"],
                content=content_str,
                metadata=c.get("metadata", {}),
                latency_ms=0,
                backend_used=c.get("backend_used", "dimension"),
            )
            score = await evaluator.evaluate(candidate_result)
            quality_scores.append({
                "idx": c["idx"],
                "groundedness": round(score.groundedness, 3),
                "relevance": round(score.relevance, 3),
                "coherence": round(score.coherence, 3),
                "creativity": round(score.creativity, 3),
                "safety": round(score.safety, 3),
                "weighted_score": round(score.weighted_score, 3),
            })
    except Exception as e:
        logger.warning(f"[{tool_key}] Multi: Quality evaluation failed: {e}")
        # Fallback scores based on content length
        for c in candidates:
            content = c.get("content", {})
            length_score = min(1.0, len(str(content)) / 500)
            quality_scores.append({
                "idx": c["idx"],
                "groundedness": 0.7,
                "relevance": 0.8,
                "coherence": 0.75,
                "creativity": length_score,
                "safety": 1.0,
                "weighted_score": 0.75,
            })

    # Select best using UQSL selector
    recommended_idx = 0
    selection_method = strategy
    selection_confidence = 0.0
    arms_used = [c.get("backend_used", "dimension") for c in candidates]

    try:
        from app.uqsl.best_selector import get_best_selector
        from app.uqsl.models import CandidateResult, QualityScore

        selector = get_best_selector()

        # Convert to UQSL format
        uqsl_candidates = [
            CandidateResult(
                idx=c["idx"],
                content=json.dumps(c["content"]) if isinstance(c["content"], dict) else str(c["content"]),
                metadata=c.get("metadata", {}),
                latency_ms=0,
                backend_used=c.get("backend_used", "dimension"),
            )
            for c in candidates
        ]
        uqsl_scores = [
            QualityScore(
                groundedness=s["groundedness"],
                relevance=s["relevance"],
                coherence=s["coherence"],
                creativity=s["creativity"],
                safety=s["safety"],
            )
            for s in quality_scores
        ]

        result = await selector.select_best(
            candidates=uqsl_candidates,
            scores=uqsl_scores,
            strategy=strategy,
        )

        recommended_idx = result.selected.idx
        selection_method = result.method
        selection_confidence = result.confidence
        arms_used = result.arms_used or arms_used
    except Exception as e:
        logger.warning(f"[{tool_key}] Multi: Best selection failed: {e}")
        # Fallback: select highest weighted_score
        if quality_scores:
            best = max(quality_scores, key=lambda s: s["weighted_score"])
            recommended_idx = best["idx"]
            selection_confidence = best["weighted_score"]

    # Create session for HITL
    session_id = str(uuid.uuid4())
    prompt_preview = inputs.get("topic") or inputs.get("concept") or inputs.get("description") or ""
    prompt_hash = hashlib.sha256(prompt_preview.encode()).hexdigest()[:64]

    # Store in session (in-memory, replace with Redis in production)
    try:
        from app.routers.uqsl import _sessions
        _sessions[session_id] = {
            "candidates": candidates,
            "quality_scores": quality_scores,
            "prompt_hash": prompt_hash,
            "prompt_preview": prompt_preview[:200],
            "app_key": f"dimension.{dimension_code.lower()}",
            "strategy": strategy,
            "arms_used": arms_used,
            "created_at": datetime.utcnow(),
        }
    except Exception:
        pass

    latency_ms = int((time.time() - start_time) * 1000)

    # Record telemetry
    try:
        await record_tool_run(
            db=db,
            tool_key=f"{tool_key}_multi",
            user_id=user_id,
            inputs_summary={**inputs_summary, "model": model, "n_candidates": n_candidates},
            outputs_summary={"success": True, "n_generated": len(candidates)},
            status="success",
            latency_ms=latency_ms,
            credits_charged=total_cost - (single_cost * failed_count) if credits_deducted else 0,
        )
    except Exception as tel_err:
        logger.warning(f"Telemetry recording failed: {tel_err}")

    return {
        "session_id": session_id,
        "candidates": candidates,
        "quality_scores": quality_scores,
        "recommended_idx": recommended_idx,
        "method": selection_method,
        "confidence": selection_confidence,
        "arms_used": arms_used,
        "metrics": {
            "latency_ms": latency_ms,
            "n_requested": n_candidates,
            "n_generated": len(candidates),
            "credits_charged": total_cost - (single_cost * failed_count) if credits_deducted else 0,
        },
    }


async def _execute_dimension_tool_multi_stream(
    capsule_id: DimensionCapsuleId,
    tool_key: str,
    operation_name: str,
    inputs: Dict[str, Any],
    model: str,
    user: dict,
    byok_key: Optional[str],
    db: AsyncSession,
    inputs_summary: Dict[str, Any],
    n_candidates: int = 3,
    strategy: str = "auto",
    params: Optional[Dict[str, Any]] = None,
    intent: Optional[Any] = None,
):
    """
    SSE streaming wrapper for UQSL multi-candidate dimension tool execution.

    Events:
    - progress: Generation progress
    - candidate: Individual candidate result
    - quality: Quality score for candidate
    - selection: Final selection with recommendation
    - complete: Final response
    - error: Error event
    """
    import asyncio
    import uuid
    import hashlib
    from datetime import datetime

    start_time = time.time()
    user_id = user.get("id")
    credits_deducted = False
    total_cost = 0
    single_cost = 0

    yield sse_progress(1, f"{operation_name} UQSL 다중 생성 시작...", "starting")

    try:
        if not user_id:
            yield sse_error("유효하지 않은 사용자입니다.", code="INVALID_USER")
            return

        # Calculate credit cost
        credit_multiplier = (params or {}).get("credit_multiplier", 1.0)
        single_cost = get_credit_cost(capsule_id, model, credit_multiplier)
        total_cost = single_cost * n_candidates

        if not byok_key:
            user_credits = await get_or_create_user_credits(db, user_id)
            if user_credits.balance < total_cost:
                yield sse_error(
                    "크레딧이 부족합니다.",
                    code="INSUFFICIENT_CREDITS",
                    detail=f"필요: {total_cost}, 보유: {user_credits.balance}",
                )
                return

            try:
                await deduct_credits(
                    db, user_id, total_cost,
                    description=f"Dimension Multi: {tool_key} x{n_candidates}",
                    meta={"tool": tool_key, "model": model, "n_candidates": n_candidates}
                )
                credits_deducted = True
            except ValueError as e:
                yield sse_error(str(e), code="CREDIT_ERROR")
                return

        yield sse_progress(5, f"{n_candidates}개 후보 생성 준비 중...", "processing")

        # Prepare execution params
        execution_params = {"model": model}
        if params:
            execution_params.update(params)

        # RAG context
        dimension_code = CAPSULE_TO_DIMENSION.get(capsule_id, "1D")
        rag_context = None

        try:
            from app.rag.rag_presets import get_rag_preset, should_enable_rag
            from app.rag.hybrid_rag import hybrid_query

            auteur_key = _extract_auteur_key(inputs, intent)
            preset = get_rag_preset(dimension_code)

            if should_enable_rag(preset, auteur_key):
                topic = inputs.get("topic") or inputs.get("concept") or inputs.get("description") or ""
                if topic:
                    rag_result = await hybrid_query(
                        query=f"{topic[:200]} - 시각적 스타일과 촬영 기법 참조",
                        auteur_key=auteur_key,
                        dimension=dimension_code if dimension_code != "AD" else None,
                        use_google_search=preset.use_google_search,
                        use_semantic_cache=True,
                    )
                    if rag_result.confidence >= preset.confidence_threshold:
                        rag_context = {
                            "auteur_reference": rag_result.answer[:preset.answer_max_length] if rag_result.answer else None,
                            "sources": [{"id": s.source_id, "title": s.title} for s in (rag_result.notebooklm_sources or [])[:preset.max_sources]],
                        }
                        inputs["_rag_context"] = rag_context
        except Exception as e:
            logger.debug(f"[{tool_key}] Multi stream: RAG failed: {e}")

        yield sse_progress(10, f"{n_candidates}개 후보 병렬 생성 시작...", "processing")

        # Generate candidates
        candidates = []
        failed_count = 0

        async def generate_candidate(idx: int) -> Dict[str, Any]:
            try:
                temp = 0.7 + (idx * 0.3 / n_candidates)
                candidate_params = {**execution_params, "temperature": temp, "seed": idx * 1000}

                result = await execute_dimension_capsule(
                    capsule_id=capsule_id.value,
                    inputs=inputs,
                    params=candidate_params,
                    user_api_key=byok_key,
                )

                return {
                    "idx": idx,
                    "content": result.get("output", {}),
                    "success": result.get("success", False),
                    "metadata": {"seed": idx * 1000, "temperature": temp},
                    "backend_used": dimension_code.lower(),
                }
            except Exception as e:
                return {"idx": idx, "content": {}, "success": False, "error": str(e)}

        # Stream progress as candidates complete
        tasks = [asyncio.create_task(generate_candidate(i)) for i in range(n_candidates)]
        completed = 0

        for coro in asyncio.as_completed(tasks):
            result = await coro
            completed += 1

            if result.get("success"):
                candidates.append(result)
                # Stream candidate event
                content_preview = str(result.get("content", {}))[:200]
                yield sse_event("candidate", {
                    "idx": result["idx"],
                    "content_preview": content_preview,
                    "backend_used": result.get("backend_used", "dimension"),
                })
            else:
                failed_count += 1

            progress_pct = 10 + int(40 * completed / n_candidates)
            yield sse_progress(progress_pct, f"후보 {completed}/{n_candidates} 완료", "processing")

        # Sort candidates
        candidates.sort(key=lambda c: c["idx"])

        # Check if all failed
        if not candidates:
            if credits_deducted:
                await _refund_with_retry(
                    db=db, user_id=user_id, amount=total_cost,
                    description=f"{tool_key} multi all failed", meta={}
                )
            yield sse_error("모든 후보 생성 실패", code="ALL_CANDIDATES_FAILED")
            return

        # Partial refund
        if credits_deducted and failed_count > 0:
            await _refund_with_retry(
                db=db, user_id=user_id, amount=single_cost * failed_count,
                description=f"{tool_key} multi partial refund", meta={"failed_count": failed_count}
            )

        yield sse_progress(55, "품질 평가 시작...", "processing")

        # Quality evaluation
        quality_scores = []
        try:
            from app.uqsl.quality_evaluator import get_quality_evaluator
            from app.uqsl.models import CandidateResult

            evaluator = get_quality_evaluator()

            for i, c in enumerate(candidates):
                content_str = json.dumps(c["content"]) if isinstance(c["content"], dict) else str(c["content"])
                candidate_result = CandidateResult(
                    idx=c["idx"], content=content_str,
                    metadata=c.get("metadata", {}), latency_ms=0,
                    backend_used=c.get("backend_used", "dimension"),
                )
                score = await evaluator.evaluate(candidate_result)
                score_dict = {
                    "idx": c["idx"],
                    "groundedness": round(score.groundedness, 3),
                    "relevance": round(score.relevance, 3),
                    "coherence": round(score.coherence, 3),
                    "creativity": round(score.creativity, 3),
                    "safety": round(score.safety, 3),
                    "weighted_score": round(score.weighted_score, 3),
                }
                quality_scores.append(score_dict)

                # Stream quality event
                yield sse_event("quality", score_dict)

                progress_pct = 55 + int(25 * (i + 1) / len(candidates))
                yield sse_progress(progress_pct, f"품질 평가 {i + 1}/{len(candidates)} 완료", "processing")
        except Exception as e:
            logger.warning(f"Quality evaluation failed: {e}")
            for c in candidates:
                quality_scores.append({
                    "idx": c["idx"], "groundedness": 0.7, "relevance": 0.8,
                    "coherence": 0.75, "creativity": 0.7, "safety": 1.0, "weighted_score": 0.75,
                })

        yield sse_progress(85, "최적 후보 선택 중...", "processing")

        # Best selection
        recommended_idx = 0
        selection_method = strategy
        selection_confidence = 0.0
        arms_used = [c.get("backend_used", "dimension") for c in candidates]
        arms_stats = {}

        try:
            from app.uqsl.best_selector import get_best_selector
            from app.uqsl.models import CandidateResult, QualityScore
            from app.uqsl.thompson_sampling import get_initialized_router

            selector = get_best_selector()
            ts_router = await get_initialized_router(db)

            uqsl_candidates = [
                CandidateResult(
                    idx=c["idx"],
                    content=json.dumps(c["content"]) if isinstance(c["content"], dict) else str(c["content"]),
                    metadata=c.get("metadata", {}), latency_ms=0,
                    backend_used=c.get("backend_used", "dimension"),
                )
                for c in candidates
            ]
            uqsl_scores = [
                QualityScore(
                    groundedness=s["groundedness"], relevance=s["relevance"],
                    coherence=s["coherence"], creativity=s["creativity"], safety=s["safety"],
                )
                for s in quality_scores
            ]

            result = await selector.select_best(
                candidates=uqsl_candidates, scores=uqsl_scores, strategy=strategy,
            )

            recommended_idx = result.selected.idx
            selection_method = result.method
            selection_confidence = result.confidence
            arms_used = result.arms_used or arms_used

            # Get arm stats
            for arm_id in arms_used:
                arms_stats[arm_id] = ts_router.get_arm_stats(arm_id)
        except Exception as e:
            logger.warning(f"Best selection failed: {e}")
            if quality_scores:
                best = max(quality_scores, key=lambda s: s["weighted_score"])
                recommended_idx = best["idx"]
                selection_confidence = best["weighted_score"]

        # Stream selection event
        yield sse_event("selection", {
            "selected_idx": recommended_idx,
            "method": selection_method,
            "confidence": round(selection_confidence, 3),
            "arms_used": arms_used,
            "arms_stats": arms_stats,
        })

        yield sse_progress(95, "세션 저장 중...", "finalizing")

        # Create session
        session_id = str(uuid.uuid4())
        prompt_preview = inputs.get("topic") or inputs.get("concept") or inputs.get("description") or ""

        try:
            from app.routers.uqsl import _sessions
            _sessions[session_id] = {
                "candidates": candidates,
                "quality_scores": quality_scores,
                "prompt_hash": hashlib.sha256(prompt_preview.encode()).hexdigest()[:64],
                "prompt_preview": prompt_preview[:200],
                "app_key": f"dimension.{dimension_code.lower()}",
                "strategy": strategy,
                "arms_used": arms_used,
                "created_at": datetime.utcnow(),
            }
        except Exception:
            pass

        latency_ms = int((time.time() - start_time) * 1000)
        actual_cost = total_cost - (single_cost * failed_count) if credits_deducted else 0

        # Record telemetry
        try:
            await record_tool_run(
                db=db, tool_key=f"{tool_key}_multi", user_id=user_id,
                inputs_summary={**inputs_summary, "model": model, "n_candidates": n_candidates},
                outputs_summary={"success": True, "n_generated": len(candidates)},
                status="success", latency_ms=latency_ms, credits_charged=actual_cost,
            )
        except Exception:
            pass

        # Complete event
        yield sse_complete(
            data={
                "session_id": session_id,
                "candidates": candidates,
                "quality_scores": quality_scores,
                "recommended_idx": recommended_idx,
                "method": selection_method,
            },
            metrics={
                "latency_ms": latency_ms,
                "n_requested": n_candidates,
                "n_generated": len(candidates),
                "credits_charged": actual_cost,
            },
        )

    except asyncio.CancelledError:
        if credits_deducted:
            await _refund_with_retry(
                db=db, user_id=user_id, amount=total_cost,
                description=f"{tool_key} multi cancelled", meta={}
            )
        raise
    except Exception as e:
        logger.error(f"{tool_key} multi stream error: {e}")
        if credits_deducted:
            await _refund_with_retry(
                db=db, user_id=user_id, amount=total_cost,
                description=f"{tool_key} multi error", meta={"error": str(e)[:500]}
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
    "_execute_dimension_tool_multi",
    "_execute_dimension_tool_multi_stream",
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
    "sse_event",
    "get_sse_headers",
    # Other
    "logger",
    "AsyncSession",
    "Optional",
    "Dict",
    "List",
    "Any",
    # Security
    "safe_error_detail",
]
