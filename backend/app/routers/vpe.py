"""VPE (Video Parsing Engine) Router.

API endpoints for VPE video analysis and Logic Vector management.

Endpoints:
- POST /api/vpe/parse - Parse video and extract Logic Vector
- POST /api/vpe/parse/stream - Parse video with SSE streaming
- POST /api/vpe/query - Query similar Logic Vectors
- GET /api/vpe/vectors/{auteur_id} - Get Logic Vectors by auteur
- DELETE /api/vpe/vectors/{doc_id} - Delete a Logic Vector
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.credit_service import deduct_credits, get_or_create_user_credits, refund_credits
from app.services.vpe_service import (
    VPE_CREDIT_COST,
    VPEProgress,
    VPEService,
    get_vpe_service,
)
from app.services.vpe_storage import (
    VPEStorage,
    get_vpe_storage,
)
from app.schemas.vpe import (
    LogicVector,
    VPEParseRequest,
    VPEParseResponse,
    VPEQueryRequest,
    VPEQueryResponse,
    VPEQueryResult,
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

router = APIRouter(prefix="/api/vpe", tags=["VPE"])


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


async def get_byok_key(
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key"),
) -> Optional[str]:
    """Extract optional BYOK key from header."""
    return x_gemini_api_key


# =============================================================================
# Request/Response Models (Extended)
# =============================================================================

class VPEParseRequestExtended(VPEParseRequest):
    """Extended parse request with streaming option."""
    stream: bool = Field(default=False, description="Enable SSE streaming")


class VPEVectorsResponse(BaseModel):
    """Response for getting vectors by auteur."""
    success: bool
    auteur_id: str
    vectors: List[VPEQueryResult]
    total: int


class VPEDeleteResponse(BaseModel):
    """Response for deleting a vector."""
    success: bool
    doc_id: str
    message: str


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/parse", response_model=VPEParseResponse)
async def parse_video(
    request: VPEParseRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    byok_key: Optional[str] = Depends(get_byok_key),
) -> VPEParseResponse:
    """Parse a video and extract Logic Vector.

    Analyzes the video using Gemini 3 Pro to extract cinematographic DNA
    including camera movements, composition, lighting, and color science.

    Args:
        request: VPEParseRequest with video_uri and options
        user: Authenticated user
        db: Database session
        byok_key: Optional BYOK API key

    Returns:
        VPEParseResponse with Logic Vector and optional shot analysis
    """
    start_time = time.time()
    user_id = user.get("id")
    trace_id = str(uuid.uuid4())

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_USER", "message": "유효하지 않은 사용자입니다."}
        )

    credit_cost = VPE_CREDIT_COST
    credits_deducted = False

    # Credit check (skip for BYOK users)
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
            description="VPE: video parsing",
            meta={"video_uri": request.video_uri[:100], "auteur_hint": request.auteur_hint}
        )
        credits_deducted = True

    try:
        # Get VPE service
        service = get_vpe_service(api_key=byok_key)

        # Parse video
        result = await service.parse_video(
            video_uri=request.video_uri,
            auteur_hint=request.auteur_hint,
            extract_shots=request.extract_shots,
            max_shots=request.max_shots,
        )

        if not result.success:
            # Refund on failure
            if credits_deducted:
                await _refund_with_retry(
                    db=db,
                    user_id=user_id,
                    amount=credit_cost,
                    description="VPE failed",
                    meta={"error": result.error[:500] if result.error else "Unknown"},
                )

            # Record telemetry
            try:
                await record_tool_run(
                    db=db,
                    tool_key="vpe.parse",
                    user_id=user_id,
                    inputs_summary={"video_uri": request.video_uri[:100]},
                    outputs_summary={},
                    status="failure",
                    latency_ms=int((time.time() - start_time) * 1000),
                    credits_charged=0,
                    error_message=result.error,
                )
            except Exception:
                pass

            return result

        # Store to Qdrant if requested
        qdrant_doc_id = None
        if request.store_to_qdrant and result.logic_vector:
            try:
                storage = get_vpe_storage()
                qdrant_doc_id = await storage.store_logic_vector(
                    logic_vector=result.logic_vector,
                    metadata={
                        "user_id": user_id,
                        "trace_id": trace_id,
                    },
                )
                if qdrant_doc_id:
                    result.qdrant_doc_id = qdrant_doc_id
                    result.evidence_refs.append(f"db:vpe_vectors:{qdrant_doc_id}")
            except Exception as e:
                logger.warning(f"[VPE] Failed to store to Qdrant: {e}")

        # Record telemetry
        try:
            await record_tool_run(
                db=db,
                tool_key="vpe.parse",
                user_id=user_id,
                inputs_summary={
                    "video_uri": request.video_uri[:100],
                    "auteur_hint": request.auteur_hint,
                },
                outputs_summary={
                    "success": True,
                    "auteur_id": result.logic_vector.auteur_id if result.logic_vector else None,
                    "shot_count": result.shot_count,
                },
                status="success",
                latency_ms=int((time.time() - start_time) * 1000),
                credits_charged=credit_cost if credits_deducted else 0,
            )
        except Exception:
            pass

        return result

    except Exception as e:
        logger.exception(f"[VPE] Parse error: {e}")

        # Refund on exception
        if credits_deducted:
            await _refund_with_retry(
                db=db,
                user_id=user_id,
                amount=credit_cost,
                description="VPE error",
                meta={"error": str(e)[:500]},
            )

        return VPEParseResponse(
            success=False,
            trace_id=trace_id,
            error=f"영상 분석 중 오류가 발생했습니다: {type(e).__name__}",
            processing_time_ms=int((time.time() - start_time) * 1000),
        )


@router.post("/parse/stream")
async def parse_video_stream(
    request: VPEParseRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    byok_key: Optional[str] = Depends(get_byok_key),
) -> StreamingResponse:
    """Parse a video with SSE streaming progress updates.

    Same as /parse but with real-time progress updates via Server-Sent Events.

    Events:
    - progress: Analysis progress (percentage, status, message)
    - shot: Individual shot analysis result
    - complete: Final result with Logic Vector
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
        credit_cost = VPE_CREDIT_COST

        yield sse_progress(1, "VPE 분석 준비 중...", "starting")

        try:
            # Credit check
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
                        description="VPE: video parsing",
                        meta={"video_uri": request.video_uri[:100]}
                    )
                    credits_deducted = True
                except ValueError as e:
                    yield sse_error(str(e), code="CREDIT_ERROR")
                    return

            yield sse_progress(5, "크레딧 차감 완료", "processing")

            # Define progress callback
            def progress_callback(progress: VPEProgress):
                # This is called from the service but we can't yield from here
                # Instead we'll use a different approach
                pass

            # Get service and parse
            service = get_vpe_service(api_key=byok_key)

            yield sse_progress(10, "Gemini 3 Pro로 영상 분석 시작...", "processing")

            result = await service.parse_video(
                video_uri=request.video_uri,
                auteur_hint=request.auteur_hint,
                extract_shots=request.extract_shots,
                max_shots=request.max_shots,
            )

            if not result.success:
                if credits_deducted:
                    await _refund_with_retry(
                        db=db,
                        user_id=user_id,
                        amount=credit_cost,
                        description="VPE failed",
                        meta={"error": result.error[:500] if result.error else "Unknown"},
                    )
                yield sse_error(result.error or "분석 실패", code="ANALYSIS_FAILED")
                return

            yield sse_progress(80, "Logic Vector 추출 완료", "processing")

            # Store to Qdrant
            qdrant_doc_id = None
            if request.store_to_qdrant and result.logic_vector:
                try:
                    storage = get_vpe_storage()
                    qdrant_doc_id = await storage.store_logic_vector(
                        logic_vector=result.logic_vector,
                        metadata={"user_id": user_id, "trace_id": trace_id},
                    )
                    if qdrant_doc_id:
                        result.qdrant_doc_id = qdrant_doc_id
                except Exception as e:
                    logger.warning(f"[VPE] Stream: Failed to store to Qdrant: {e}")

            yield sse_progress(95, "저장 완료", "finalizing")

            # Stream shot events if available
            if result.shots:
                for shot in result.shots:
                    yield sse_event("shot", shot.model_dump())

            latency_ms = int((time.time() - start_time) * 1000)

            # Complete
            yield sse_complete(
                data={
                    "logic_vector": result.logic_vector.model_dump() if result.logic_vector else None,
                    "shot_count": result.shot_count,
                    "confidence": result.confidence,
                    "qdrant_doc_id": result.qdrant_doc_id,
                    "evidence_refs": result.evidence_refs,
                },
                metrics={
                    "latency_ms": latency_ms,
                    "credits_charged": credit_cost if credits_deducted else 0,
                },
            )

            # Record telemetry
            try:
                await record_tool_run(
                    db=db,
                    tool_key="vpe.parse.stream",
                    user_id=user_id,
                    inputs_summary={"video_uri": request.video_uri[:100]},
                    outputs_summary={"success": True},
                    status="success",
                    latency_ms=latency_ms,
                    credits_charged=credit_cost if credits_deducted else 0,
                )
            except Exception:
                pass

        except asyncio.CancelledError:
            if credits_deducted:
                await _refund_with_retry(
                    db=db,
                    user_id=user_id,
                    amount=credit_cost,
                    description="VPE cancelled",
                    meta={"reason": "client_disconnect"},
                )
            raise
        except Exception as e:
            logger.error(f"[VPE] Stream error: {e}")
            if credits_deducted:
                await _refund_with_retry(
                    db=db,
                    user_id=user_id,
                    amount=credit_cost,
                    description="VPE error",
                    meta={"error": str(e)[:500]},
                )
            yield sse_error(f"영상 분석 중 오류: {type(e).__name__}", code="INTERNAL_ERROR")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )


@router.post("/query", response_model=VPEQueryResponse)
async def query_logic_vectors(
    request: VPEQueryRequest,
    user: dict = Depends(get_current_user),
) -> VPEQueryResponse:
    """Query similar Logic Vectors by style description.

    Searches the Qdrant vector store for Logic Vectors matching
    the natural language query.

    Args:
        request: VPEQueryRequest with query and filters
        user: Authenticated user

    Returns:
        VPEQueryResponse with matched Logic Vectors
    """
    trace_id = str(uuid.uuid4())

    try:
        storage = get_vpe_storage()
        results = await storage.search_by_style(
            query=request.query,
            auteur_filter=request.auteur_filter,
            top_k=request.top_k,
        )

        return VPEQueryResponse(
            success=True,
            trace_id=trace_id,
            results=results,
            total_found=len(results),
        )

    except Exception as e:
        logger.error(f"[VPE] Query error: {e}")
        return VPEQueryResponse(
            success=False,
            trace_id=trace_id,
            results=[],
            total_found=0,
        )


@router.get("/vectors/{auteur_id}", response_model=VPEVectorsResponse)
async def get_vectors_by_auteur(
    auteur_id: str,
    limit: int = 10,
    user: dict = Depends(get_current_user),
) -> VPEVectorsResponse:
    """Get all Logic Vectors for a specific auteur.

    Args:
        auteur_id: AI Auteur ID to filter by (e.g., "kang", "epoch")
        limit: Maximum results to return
        user: Authenticated user

    Returns:
        VPEVectorsResponse with Logic Vectors for the auteur
    """
    try:
        storage = get_vpe_storage()
        results = await storage.get_by_auteur(
            auteur_id=auteur_id,
            limit=limit,
        )

        return VPEVectorsResponse(
            success=True,
            auteur_id=auteur_id,
            vectors=results,
            total=len(results),
        )

    except Exception as e:
        logger.error(f"[VPE] Get by auteur error: {e}")
        return VPEVectorsResponse(
            success=False,
            auteur_id=auteur_id,
            vectors=[],
            total=0,
        )


@router.delete("/vectors/{doc_id}", response_model=VPEDeleteResponse)
async def delete_logic_vector(
    doc_id: str,
    user: dict = Depends(get_current_user),
) -> VPEDeleteResponse:
    """Delete a Logic Vector by document ID.

    Args:
        doc_id: Document ID to delete
        user: Authenticated user

    Returns:
        VPEDeleteResponse with deletion result
    """
    try:
        storage = get_vpe_storage()
        deleted = await storage.delete_logic_vector(doc_id)

        if deleted:
            return VPEDeleteResponse(
                success=True,
                doc_id=doc_id,
                message="Logic Vector 삭제 완료",
            )
        else:
            return VPEDeleteResponse(
                success=False,
                doc_id=doc_id,
                message="삭제 실패",
            )

    except Exception as e:
        logger.error(f"[VPE] Delete error: {e}")
        return VPEDeleteResponse(
            success=False,
            doc_id=doc_id,
            message=f"삭제 중 오류: {type(e).__name__}",
        )


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for VPE service."""
    # Check Qdrant connection
    qdrant_ok = False
    try:
        storage = get_vpe_storage()
        qdrant_ok = await storage.ensure_collection()
    except Exception:
        pass

    return {
        "service": "vpe",
        "status": "healthy" if qdrant_ok else "degraded",
        "qdrant": "connected" if qdrant_ok else "disconnected",
        "credit_cost": VPE_CREDIT_COST,
    }
