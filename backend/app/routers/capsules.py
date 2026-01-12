"""Capsule Router - /api/v1/capsules endpoints.

P5 Commit 4: Complete REST API for capsule operations.

Endpoints:
- GET  /api/v1/capsules/                    List specs
- GET  /api/v1/capsules/{key}               Get spec
- POST /api/v1/capsules/run                 Execute
- GET  /api/v1/capsules/run/{id}            Run status
- GET  /api/v1/capsules/{key}/runs          History
- POST /api/v1/capsules/run/{id}/cancel     Cancel
- GET  /api/v1/capsules/run/{id}/stream     SSE stream
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import CapsuleRun
from app.run_events import run_event_hub
from app.utils.sse_utils import sse_run_event, get_sse_headers
from app.credit_service import (
    get_or_create_user_credits,
    deduct_credits as deduct_user_credits,
    refund_credits as refund_user_credits,
)
from app.routers.run_token import verify_run_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/capsules", tags=["capsules"])


# =============================================================================
# Request/Response Schemas
# =============================================================================

class CapsuleSpecResponse(BaseModel):
    """Capsule specification response."""
    id: str
    capsule_key: str
    version: str
    display_name: str
    description: str
    spec: Dict[str, Any]
    is_active: bool = True
    category: Optional[str] = None
    credit_costs: Optional[Dict[str, int]] = None


class RunRequest(BaseModel):
    """Run execution request."""
    capsule_id: str = Field(..., description="capsule_key or capsule_key:version")
    capsule_version: Optional[str] = Field(None, description="Explicit version override")
    inputs: Dict[str, Any] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)
    canvas_id: Optional[str] = Field(None, description="Source canvas ID")
    node_id: Optional[str] = Field(None, description="Executing node ID")
    upstream_context: Optional[Dict[str, Any]] = Field(None, description="Context from upstream nodes")


class RunResponse(BaseModel):
    """Run execution response."""
    run_id: str
    status: str
    summary: Dict[str, Any] = Field(default_factory=dict)
    evidence_refs: List[str] = Field(default_factory=list)  # P1: string[] for frontend compatibility
    version: str = ""
    token_usage: Dict[str, int] = Field(default_factory=dict)
    latency_ms: int = 0
    cost_usd_est: float = 0.0
    error: Optional[str] = None


class RunStatusResponse(BaseModel):
    """Run status response."""
    run_id: str
    capsule_key: str
    version: str
    status: str
    summary: Dict[str, Any] = Field(default_factory=dict)
    evidence_refs: List[str] = Field(default_factory=list)  # P1: string[] for frontend compatibility
    token_usage: Dict[str, int] = Field(default_factory=dict)
    latency_ms: Optional[int] = None
    cost_usd_est: Optional[float] = None
    created_at: datetime


class RunHistoryItem(BaseModel):
    """Run history item."""
    run_id: str
    status: str
    created_at: datetime
    latency_ms: Optional[int] = None


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/", response_model=List[CapsuleSpecResponse])
async def list_capsules(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List all available capsule specs."""
    try:
        from app.services.capsule_specs import list_specs
        
        specs = await list_specs(db, category=category)
        return [CapsuleSpecResponse(**spec.to_dict()) for spec in specs]
    except Exception as e:
        logger.error(f"Failed to list specs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{capsule_key}", response_model=CapsuleSpecResponse)
async def get_capsule(
    capsule_key: str,
    version: Optional[str] = Query(None, description="Specific version"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get a specific capsule spec."""
    try:
        from app.services.capsule_specs import get_spec
        
        spec = await get_spec(db, capsule_key, version)
        if not spec:
            raise HTTPException(status_code=404, detail=f"Capsule not found: {capsule_key}")
        return CapsuleSpecResponse(**spec.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get spec: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run", response_model=RunResponse)
async def run_capsule(
    request: RunRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Execute a capsule with credit management.
    
    Credit flow:
    1. Check user has sufficient credits
    2. Deduct credits before execution
    3. Refund on failure/cancellation
    """
    run_id = str(uuid.uuid4())
    user_id = user.get("id")
    credit_cost = 0
    credits_deducted = False
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    try:
        from app.services.capsule_executor import execute_capsule
        from app.services.capsule_specs import parse_capsule_id, get_spec
        
        # Parse capsule_id
        capsule_key, version = parse_capsule_id(request.capsule_id)
        
        # Get spec for credit cost
        spec = await get_spec(db, capsule_key, version)
        if spec and spec.credit_costs:
            # Use model from params or default
            model = request.params.get("model", "gemini-3-flash-preview")
            credit_cost = spec.credit_costs.get(model, 5)
        else:
            credit_cost = 10  # Default cost
        
        # Check credits (402 if insufficient)
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
        await deduct_user_credits(
            db, user_id, credit_cost,
            description=f"Capsule: {capsule_key}",
            meta={"run_id": run_id, "capsule_key": capsule_key},
        )
        credits_deducted = True
        
        # Use explicit version from request if provided
        effective_version = request.capsule_version or version or "latest"
        
        # Store credit cost in params for cancel refund
        stored_params = dict(request.params)
        stored_params["_credit_cost"] = credit_cost
        
        # Create run record (queued) with user_id for BOLA
        run_record = CapsuleRun(
            id=uuid.UUID(run_id),
            user_id=user_id,  # P0 BOLA: track owner
            capsule_key=capsule_key,
            capsule_version=effective_version,
            status="queued",
            inputs=request.inputs,
            params=stored_params,
            upstream_context=request.upstream_context or {},
        )
        db.add(run_record)
        await db.commit()
        
        # Publish queued event
        await run_event_hub.publish(run_id, "run.queued", {
            "run_id": run_id,
            "capsule_key": capsule_key,
        })
        
        # Update to running
        run_record.status = "running"
        await db.commit()
        await run_event_hub.publish(run_id, "run.started", {"run_id": run_id})
        
        # Execute
        result = await execute_capsule(
            capsule_id=request.capsule_id,
            inputs=request.inputs,
            params=request.params,
            user=user,
            db=db,
            run_id=run_id,
        )
        
        # Update record
        run_record.status = result.status
        run_record.summary = result.summary
        run_record.evidence_refs = result.evidence_refs
        run_record.token_usage = result.token_usage
        run_record.latency_ms = result.latency_ms
        run_record.cost_usd_est = result.cost_usd_est
        run_record.capsule_version = result.version
        await db.commit()
        
        # Refund on failure
        if result.status == "failed" and credits_deducted:
            await refund_user_credits(
                db, user_id, credit_cost,
                description=f"Capsule failed: {capsule_key}",
                meta={"run_id": run_id, "error": result.error or "Unknown"},
            )
        
        # Publish completion event
        if result.status == "done":
            await run_event_hub.publish(run_id, "run.completed", result.to_dict())
        else:
            await run_event_hub.publish(run_id, "run.failed", {
                "run_id": run_id,
                "error": result.error,
            })
        
        return RunResponse(**result.to_dict())
        
    except HTTPException:
        # Re-raise HTTP exceptions (including 402)
        if credits_deducted:
            try:
                await refund_user_credits(
                    db, user_id, credit_cost,
                    description=f"Capsule error refund: {capsule_key}",
                    meta={"run_id": run_id},
                )
            except Exception as refund_err:
                logger.error(f"Refund failed: {refund_err}")
        raise
        
    except Exception as e:
        logger.error(f"Run execution failed: {e}")
        
        # Refund on error
        if credits_deducted:
            try:
                await refund_user_credits(
                    db, user_id, credit_cost,
                    description=f"Capsule error refund",
                    meta={"run_id": run_id, "error": str(e)},
                )
            except Exception as refund_err:
                logger.error(f"Refund failed: {refund_err}")
        
        # Update record to failed
        try:
            run_record = await db.get(CapsuleRun, uuid.UUID(run_id))
            if run_record:
                run_record.status = "failed"
                await db.commit()
        except Exception:
            pass
        
        await run_event_hub.publish(run_id, "run.failed", {
            "run_id": run_id,
            "error": str(e),
        })
        
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}", response_model=RunStatusResponse)
async def get_run_status(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get run status by ID."""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run_id format")
    
    run_record = await db.get(CapsuleRun, run_uuid)
    if not run_record:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    
    # P0 BOLA: Verify ownership (NULL user_id = admin only)
    user_id = user.get("id")
    if run_record.user_id and run_record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if not run_record.user_id and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return RunStatusResponse(
        run_id=str(run_record.id),
        capsule_key=run_record.capsule_key,
        version=run_record.capsule_version,
        status=run_record.status,
        summary=run_record.summary or {},
        evidence_refs=run_record.evidence_refs or [],
        token_usage=run_record.token_usage or {},
        latency_ms=run_record.latency_ms,
        cost_usd_est=run_record.cost_usd_est,
        created_at=run_record.created_at,
    )


@router.get("/{capsule_key}/runs", response_model=List[RunHistoryItem])
async def get_run_history(
    capsule_key: str,
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get run history for a capsule (own runs only)."""
    user_id = user.get("id")
    
    # P0 BOLA: Only return user's own runs
    query = (
        select(CapsuleRun)
        .where(CapsuleRun.capsule_key == capsule_key)
        .where(CapsuleRun.user_id == user_id)  # BOLA filter
        .order_by(CapsuleRun.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    runs = result.scalars().all()
    
    return [
        RunHistoryItem(
            run_id=str(run.id),
            status=run.status,
            created_at=run.created_at,
            latency_ms=run.latency_ms,
        )
        for run in runs
    ]


@router.post("/run/{run_id}/cancel")
async def cancel_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Cancel a running capsule execution."""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run_id format")
    
    run_record = await db.get(CapsuleRun, run_uuid)
    if not run_record:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    
    # P0 BOLA: Verify ownership
    user_id = user.get("id")
    if run_record.user_id and run_record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if run_record.status not in ("queued", "running"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel run in status: {run_record.status}"
        )
    
    # Mark as cancelled
    run_record.status = "cancelled"
    await db.commit()
    
    # Notify hub + trigger refund (credits already deducted)
    run_event_hub.cancel(run_id)
    await run_event_hub.publish(run_id, "run.cancelled", {"run_id": run_id})
    
    # P2: Refund credits on cancel
    try:
        # Get credit cost from params or default
        credit_cost = run_record.params.get("_credit_cost", 10)
        await refund_user_credits(
            db, user_id, credit_cost,
            description=f"Capsule cancelled: {run_record.capsule_key}",
            meta={"run_id": run_id},
        )
    except Exception as refund_err:
        logger.warning(f"Cancel refund failed: {refund_err}")
    
    return {"run_id": run_id, "status": "cancelled"}


@router.get("/run/{run_id}/stream")
async def stream_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Stream run events via SSE."""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run_id format")
    
    # Subscribe to events
    queue = run_event_hub.subscribe(run_id, replay_last=True)
    
    async def event_generator():
        """Generate SSE events from queue."""
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield sse_run_event(event.type, {
                        "run_id": event.run_id,
                        "seq": event.seq,
                        "ts": event.ts,
                        **event.payload,
                    })
                    
                    # Stop on terminal events
                    if event.type in ("run.completed", "run.failed", "run.cancelled"):
                        break
                        
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield sse_run_event("heartbeat", {"ts": datetime.utcnow().isoformat()})
                    
                    # Check if cancelled
                    if run_event_hub.is_cancelled(run_id):
                        yield sse_run_event("run.cancelled", {"run_id": run_id})
                        break
                        
        finally:
            run_event_hub.unsubscribe(run_id, queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=get_sse_headers(),
    )
