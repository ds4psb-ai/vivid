"""DNA Lab Router - Mega App for DNA Extraction.

Combines VPE, Aesthetic Director, Mirror, and Quality Controller
into a unified DNA extraction interface.

Endpoints:
- POST /api/dna-lab/extract - Extract DNA using selected components
- POST /api/dna-lab/extract/stream - Extract with SSE streaming
- POST /api/dna-lab/vpe/parse - Direct VPE access
- POST /api/dna-lab/aesthetic - Direct AD access
- POST /api/dna-lab/mirror - Direct Mirror access
- POST /api/dna-lab/quality - Direct QC access
- GET /api/dna-lab/credits - Get credit costs for components
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.credit_service import deduct_credits, get_or_create_user_credits, refund_credits
from app.services.dna_lab_service import (
    COMPONENT_CREDITS,
    DNAComponent,
    DNALabProgress,
    DNALabResult,
    DNALabService,
    get_dna_lab_service,
)
from app.services.telemetry_integration import record_tool_run
from app.services.dlq_service import add_refund_failure_to_dlq
from app.utils.sse_utils import (
    sse_progress,
    sse_complete,
    sse_error,
    sse_event,
    get_sse_headers,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dna-lab", tags=["DNA Lab"])


# =============================================================================
# Constants
# =============================================================================

REFUND_MAX_RETRIES = 3
REFUND_RETRY_BASE_DELAY_MS = 100


# =============================================================================
# Helper Functions
# =============================================================================

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


async def get_byok_key(
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key"),
) -> Optional[str]:
    """Extract optional BYOK key from header."""
    return x_gemini_api_key


# =============================================================================
# Request/Response Models
# =============================================================================

class DNALabExtractRequest(BaseModel):
    """Request to extract DNA using selected components."""
    video_uri: Optional[str] = Field(
        default=None,
        description="Video URI for VPE analysis (required if 'vpe' in components)"
    )
    concept: Optional[str] = Field(
        default=None,
        description="Creative concept for AD analysis"
    )
    auteur_key: Optional[str] = Field(
        default=None,
        description="Auteur hint for style matching"
    )
    components: List[str] = Field(
        default=["ad"],
        description="Components to run: vpe, ad, mirror, qc"
    )
    persona_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Context for Mirror analysis"
    )
    quality_content: Optional[str] = Field(
        default=None,
        description="Content for QC analysis"
    )
    stream: bool = Field(
        default=False,
        description="Enable SSE streaming"
    )


class DNALabExtractResponse(BaseModel):
    """Response from DNA extraction."""
    success: bool
    trace_id: str
    logic_vector: Optional[Dict[str, Any]] = None
    aesthetic_guidelines: Optional[Dict[str, Any]] = None
    persona_dna: Optional[Dict[str, Any]] = None
    quality_metrics: Optional[Dict[str, Any]] = None
    evidence_refs: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    components_run: List[str] = Field(default_factory=list)
    processing_time_ms: int = 0
    credits_used: int = 0
    errors: Dict[str, str] = Field(default_factory=dict)


class CreditCostsResponse(BaseModel):
    """Response with credit costs for components."""
    components: Dict[str, int]
    total_for_all: int


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/extract", response_model=DNALabExtractResponse)
async def extract_dna(
    request: DNALabExtractRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    byok_key: Optional[str] = Depends(get_byok_key),
) -> DNALabExtractResponse:
    """Extract DNA using selected components.

    Combines VPE, Aesthetic Director, Mirror, and Quality Controller
    to extract comprehensive cinematographic DNA.

    Args:
        request: DNALabExtractRequest with options
        user: Authenticated user
        db: Database session
        byok_key: Optional BYOK API key

    Returns:
        DNALabExtractResponse with combined results
    """
    start_time = time.time()
    user_id = user.get("id")
    trace_id = str(uuid.uuid4())

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_USER", "message": "유효하지 않은 사용자입니다."}
        )

    # Calculate credit cost
    service = get_dna_lab_service(api_key=byok_key)
    credit_cost = service.calculate_total_credits(request.components)
    credits_deducted = False

    # Credit check (skip for BYOK users)
    if not byok_key and credit_cost > 0:
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
            description=f"DNA Lab: {', '.join(request.components)}",
            meta={"components": request.components}
        )
        credits_deducted = True

    try:
        # Extract DNA
        result = await service.extract_dna(
            video_uri=request.video_uri,
            concept=request.concept,
            auteur_key=request.auteur_key,
            components=request.components,
            persona_context=request.persona_context,
            quality_content=request.quality_content,
        )

        if not result.success:
            # Partial refund based on what actually ran
            if credits_deducted:
                refund_amount = credit_cost - result.credits_used
                if refund_amount > 0:
                    await _refund_with_retry(
                        db=db,
                        user_id=user_id,
                        amount=refund_amount,
                        description="DNA Lab partial refund",
                        meta={"errors": result.errors},
                    )

        # Record telemetry
        try:
            await record_tool_run(
                db=db,
                tool_key="dna_lab.extract",
                user_id=user_id,
                inputs_summary={
                    "components": request.components,
                    "has_video": bool(request.video_uri),
                    "auteur_key": request.auteur_key,
                },
                outputs_summary={
                    "success": result.success,
                    "components_run": result.components_run,
                },
                status="success" if result.success else "failure",
                latency_ms=int((time.time() - start_time) * 1000),
                credits_charged=result.credits_used if credits_deducted else 0,
            )
        except Exception:
            pass

        return DNALabExtractResponse(
            success=result.success,
            trace_id=result.trace_id,
            logic_vector=result.logic_vector.model_dump() if result.logic_vector else None,
            aesthetic_guidelines=asdict(result.aesthetic_guidelines) if result.aesthetic_guidelines else None,
            persona_dna=asdict(result.persona_dna) if result.persona_dna else None,
            quality_metrics=asdict(result.quality_metrics) if result.quality_metrics else None,
            evidence_refs=result.evidence_refs,
            confidence=result.confidence,
            components_run=result.components_run,
            processing_time_ms=result.processing_time_ms,
            credits_used=result.credits_used,
            errors=result.errors,
        )

    except Exception as e:
        logger.exception(f"[DNALab] Extract error: {e}")

        if credits_deducted:
            await _refund_with_retry(
                db=db,
                user_id=user_id,
                amount=credit_cost,
                description="DNA Lab error",
                meta={"error": str(e)[:500]},
            )

        return DNALabExtractResponse(
            success=False,
            trace_id=trace_id,
            errors={"system": f"DNA 추출 중 오류: {type(e).__name__}"},
        )


@router.post("/extract/stream")
async def extract_dna_stream(
    request: DNALabExtractRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    byok_key: Optional[str] = Depends(get_byok_key),
) -> StreamingResponse:
    """Extract DNA with SSE streaming progress updates.

    Events:
    - progress: Extraction progress
    - component: Individual component result
    - complete: Final combined result
    - error: Error message
    """
    user_id = user.get("id")

    if not user_id:
        async def error_gen():
            yield sse_error("유효하지 않은 사용자입니다.", code="INVALID_USER")
        return StreamingResponse(error_gen(), media_type="text/event-stream", headers=get_sse_headers())

    async def generate():
        start_time = time.time()
        trace_id = str(uuid.uuid4())
        credits_deducted = False
        credit_cost = 0

        yield sse_progress(1, "DNA Lab 추출 준비 중...", "starting")

        try:
            service = get_dna_lab_service(api_key=byok_key)
            credit_cost = service.calculate_total_credits(request.components)

            # Credit check
            if not byok_key and credit_cost > 0:
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
                        description=f"DNA Lab: {', '.join(request.components)}",
                        meta={"components": request.components}
                    )
                    credits_deducted = True
                except ValueError as e:
                    yield sse_error(str(e), code="CREDIT_ERROR")
                    return

            yield sse_progress(5, f"{len(request.components)}개 컴포넌트 실행 준비 완료", "processing")

            # Progress callback
            def progress_callback(progress: DNALabProgress):
                # Note: Can't yield from callback, but we log progress
                logger.debug(f"[DNALab] Progress: {progress.status} - {progress.message}")

            result = await service.extract_dna(
                video_uri=request.video_uri,
                concept=request.concept,
                auteur_key=request.auteur_key,
                components=request.components,
                persona_context=request.persona_context,
                quality_content=request.quality_content,
                progress_callback=progress_callback,
            )

            if not result.success:
                if credits_deducted:
                    refund_amount = credit_cost - result.credits_used
                    if refund_amount > 0:
                        await _refund_with_retry(
                            db=db,
                            user_id=user_id,
                            amount=refund_amount,
                            description="DNA Lab partial refund",
                            meta={"errors": result.errors},
                        )

            yield sse_progress(90, "결과 정리 중...", "finalizing")

            # Stream component events
            for comp in result.components_run:
                yield sse_event("component", {"name": comp, "status": "completed"})

            for comp, error in result.errors.items():
                yield sse_event("component", {"name": comp, "status": "failed", "error": error})

            latency_ms = int((time.time() - start_time) * 1000)

            yield sse_complete(
                data={
                    "logic_vector": result.logic_vector.model_dump() if result.logic_vector else None,
                    "aesthetic_guidelines": asdict(result.aesthetic_guidelines) if result.aesthetic_guidelines else None,
                    "persona_dna": asdict(result.persona_dna) if result.persona_dna else None,
                    "quality_metrics": asdict(result.quality_metrics) if result.quality_metrics else None,
                    "evidence_refs": result.evidence_refs,
                    "confidence": result.confidence,
                    "components_run": result.components_run,
                    "errors": result.errors,
                },
                metrics={
                    "latency_ms": latency_ms,
                    "credits_charged": result.credits_used if credits_deducted else 0,
                },
            )

        except asyncio.CancelledError:
            if credits_deducted:
                await _refund_with_retry(
                    db=db,
                    user_id=user_id,
                    amount=credit_cost,
                    description="DNA Lab cancelled",
                    meta={"reason": "client_disconnect"},
                )
            raise
        except Exception as e:
            logger.error(f"[DNALab] Stream error: {e}")
            if credits_deducted:
                await _refund_with_retry(
                    db=db,
                    user_id=user_id,
                    amount=credit_cost,
                    description="DNA Lab error",
                    meta={"error": str(e)[:500]},
                )
            yield sse_error(f"DNA 추출 중 오류: {type(e).__name__}", code="INTERNAL_ERROR")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


@router.get("/credits", response_model=CreditCostsResponse)
async def get_credit_costs(
    user: dict = Depends(get_current_user),
) -> CreditCostsResponse:
    """Get credit costs for each DNA Lab component.

    Returns:
        CreditCostsResponse with per-component and total costs
    """
    component_costs = {c.value: COMPONENT_CREDITS[c] for c in DNAComponent}
    total = sum(component_costs.values())

    return CreditCostsResponse(
        components=component_costs,
        total_for_all=total,
    )


# =============================================================================
# Direct Component Access Endpoints
# =============================================================================

@router.post("/vpe/parse")
async def vpe_parse_direct(
    request: Dict[str, Any],
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    byok_key: Optional[str] = Depends(get_byok_key),
):
    """Direct access to VPE component.

    Redirects to /api/vpe/parse for backward compatibility.
    """
    from app.routers.vpe import parse_video
    from app.schemas.vpe import VPEParseRequest

    vpe_request = VPEParseRequest(**request)
    return await parse_video(vpe_request, user, db, byok_key)


@router.post("/aesthetic")
async def aesthetic_direct(
    request: Dict[str, Any],
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    byok_key: Optional[str] = Depends(get_byok_key),
):
    """Direct access to Aesthetic Director component.

    For full AD features, use /api/dimension/aesthetic/direct.
    """
    service = get_dna_lab_service(api_key=byok_key)
    result = await service._run_aesthetic_director(
        concept=request.get("concept"),
        auteur_key=request.get("auteur_key"),
    )
    return result


@router.post("/mirror")
async def mirror_direct(
    request: Dict[str, Any],
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    byok_key: Optional[str] = Depends(get_byok_key),
):
    """Direct access to Mirror (Persona) component.

    For full Mirror features, use /api/dimension/mirror/analyze.
    """
    service = get_dna_lab_service(api_key=byok_key)
    result = await service._run_mirror(persona_context=request)
    return result


@router.post("/quality")
async def quality_direct(
    request: Dict[str, Any],
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    byok_key: Optional[str] = Depends(get_byok_key),
):
    """Direct access to Quality Controller component.

    For full QC features, use /api/dimension/quality/check.
    """
    service = get_dna_lab_service(api_key=byok_key)
    result = await service._run_quality_check(content=request.get("content", ""))
    return result


# =============================================================================
# Unified Pipeline (Saga Pattern)
# =============================================================================

@router.post("/run-pipeline")
async def run_dna_pipeline(
    request: Dict[str, Any],
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    byok_key: Optional[str] = Depends(get_byok_key),
):
    """Run unified DNA pipeline with Saga pattern orchestration.

    Executes steps in order: VPE → AD → Mirror → QC
    with automatic compensation (rollback) on failure.

    Args:
        request: Pipeline configuration
            - video_uri: Video URI for VPE (gs:// or https://)
            - concept: Creative concept for AD
            - auteur_key: Auteur hint
            - steps: List of steps to run (default: all)
            - persona_context: Context for Mirror
            - quality_content: Content for QC
            - ip_id: IP ID for context-aware QC
            - store_to_qdrant: Whether to sync to Qdrant (default: true)
            - fail_fast: Stop on first failure (default: false)

    Returns:
        DNALabResult with all outputs and execution metadata
    """
    from app.schemas.dna_lab_unified import DNALabPipelineRequest, PipelineStep
    from app.services.dna_lab_orchestrator import get_orchestrator, STEP_CREDITS

    start_time = time.time()
    user_id = user.get("id")
    trace_id = str(uuid.uuid4())

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_USER", "message": "유효하지 않은 사용자입니다."}
        )

    # Parse request
    try:
        # Convert step strings to enums if needed
        if "steps" in request and isinstance(request["steps"], list):
            request["steps"] = [
                PipelineStep(s) if isinstance(s, str) else s
                for s in request["steps"]
            ]
        pipeline_request = DNALabPipelineRequest(**request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_REQUEST", "message": str(e)}
        )

    # Calculate credit cost
    steps = pipeline_request.steps or [
        PipelineStep.VPE, PipelineStep.AD, PipelineStep.MIRROR, PipelineStep.QC
    ]
    credit_cost = sum(STEP_CREDITS.get(s, 0) for s in steps)
    credits_deducted = False

    # Credit check (skip for BYOK users)
    if not byok_key and credit_cost > 0:
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
            description=f"DNA Lab Pipeline: {', '.join(s.value for s in steps)}",
            meta={"steps": [s.value for s in steps]}
        )
        credits_deducted = True

    try:
        # Run pipeline
        orchestrator = get_orchestrator(api_key=byok_key)
        result = await orchestrator.run_pipeline(
            request=pipeline_request,
            user_id=user_id,
            db=db,
        )

        # Partial refund if not all steps succeeded
        if credits_deducted and result.credits_used < credit_cost:
            refund_amount = credit_cost - result.credits_used
            if refund_amount > 0:
                await _refund_with_retry(
                    db=db,
                    user_id=user_id,
                    amount=refund_amount,
                    description="DNA Lab Pipeline partial refund",
                    meta={"errors": result.errors},
                )

        # Record telemetry
        try:
            await record_tool_run(
                db=db,
                tool_key="dna_lab.pipeline",
                user_id=user_id,
                inputs_summary={
                    "steps": [s.value for s in steps],
                    "has_video": bool(pipeline_request.video_uri),
                    "auteur_key": pipeline_request.auteur_key,
                },
                outputs_summary={
                    "success": result.success,
                    "status": result.status.value,
                    "completed_steps": [sr.step.value for sr in result.steps if sr.status == "completed"],
                },
                status="success" if result.success else "failure",
                latency_ms=int((time.time() - start_time) * 1000),
                credits_charged=result.credits_used if credits_deducted else 0,
            )
        except Exception:
            pass

        # Serialize result
        return {
            "success": result.success,
            "trace_id": result.trace_id,
            "status": result.status.value,
            "vpe": result.vpe.model_dump() if result.vpe else None,
            "ad": result.ad.model_dump() if result.ad else None,
            "mirror": result.mirror.model_dump() if result.mirror else None,
            "qc": result.qc.model_dump() if result.qc else None,
            "evidence_refs": result.evidence_refs,
            "steps": [
                {
                    "step": sr.step.value,
                    "status": sr.status,
                    "duration_ms": sr.duration_ms,
                    "credits_used": sr.credits_used,
                    "error": sr.error,
                }
                for sr in result.steps
            ],
            "credits_used": result.credits_used,
            "processing_time_ms": result.processing_time_ms,
            "errors": result.errors,
        }

    except Exception as e:
        logger.exception(f"[DNALab] Pipeline error: {e}")

        if credits_deducted:
            await _refund_with_retry(
                db=db,
                user_id=user_id,
                amount=credit_cost,
                description="DNA Lab Pipeline error",
                meta={"error": str(e)[:500]},
            )

        return {
            "success": False,
            "trace_id": trace_id,
            "status": "failed",
            "errors": {"pipeline": f"파이프라인 오류: {type(e).__name__}"},
        }


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for DNA Lab service."""
    from app.services.dna_lab_orchestrator import STEP_CREDITS
    from app.schemas.dna_lab_unified import PipelineStep

    return {
        "service": "dna_lab",
        "status": "healthy",
        "components": [c.value for c in DNAComponent],
        "component_credits": {c.value: COMPONENT_CREDITS[c] for c in DNAComponent},
        "pipeline_steps": [s.value for s in PipelineStep],
        "pipeline_step_credits": {s.value: STEP_CREDITS[s] for s in PipelineStep},
    }
