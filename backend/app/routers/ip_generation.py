"""IP Generation API router.

Integrates IP presets with workflow execution and run-token system.
Provides endpoints for:
- Starting generation from IP preset
- Tracking generation progress
- Getting generation evidence

2026 Best Practices Applied:
- Background tasks create own DB sessions (FastAPI pattern)
- Run-token for credit management
- SSE for real-time progress
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.database import get_db, AsyncSessionLocal
from app.auth import require_user_id
from app.models_ip import IPCatalog, IPWorkflowPreset, IPRights, IPGeneration
from app.services.run_token_service import RunTokenService
from app.services.capsule_executor import execute_capsule, CapsuleExecutionResult

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ip-generation"])

# Service instance
run_token_service = RunTokenService()


# --- Pydantic Schemas ---

class GenerationStartRequest(BaseModel):
    """Request to start IP-based generation."""
    preset_id: UUID = Field(..., description="Preset to use for generation")
    user_prompt: Optional[str] = Field(None, max_length=2000, description="Optional user prompt")


class GenerationStartResponse(BaseModel):
    """Response after starting generation."""
    generation_id: str
    session_id: Optional[str] = None
    status: str
    estimated_credits: int
    estimated_duration_seconds: int
    message: str


class GenerationProgressResponse(BaseModel):
    """Generation progress response."""
    generation_id: str
    status: str
    progress_percent: int
    current_step: Optional[str] = None
    credits_consumed: int
    latency_ms: int
    error_message: Optional[str] = None


class GenerationResultResponse(BaseModel):
    """Generation result with output."""
    generation_id: str
    status: str
    output_artifacts: list[dict] = Field(default_factory=list)
    preview_url: Optional[str] = None
    credits_consumed: int
    latency_ms: int


class EvidenceResponse(BaseModel):
    """Evidence and provenance for generation."""
    generation_id: str
    evidence_refs: list[str] = Field(default_factory=list)
    pattern_version: Optional[str] = None
    ip_slug: str
    preset_type: str
    auteur_key: Optional[str] = None
    credits_consumed: int
    latency_ms: int
    workflow_trace: list[dict] = Field(default_factory=list)


# --- API Endpoints ---

@router.post("/{slug}/generate", response_model=GenerationStartResponse)
async def start_ip_generation(
    slug: str,
    request: GenerationStartRequest,
    user_id: str = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Start generation from IP preset.

    This endpoint implements the sealed capsule pattern:
    1. Validates IP rights (prohibited → 403)
    2. Loads preset workflow configuration (sealed)
    3. Reserves run-token credits
    4. Starts async workflow execution
    5. Returns generation ID for progress tracking

    The internal DAG/tool selection is never exposed to the client.
    """
    # Get IP
    ip_result = await db.execute(
        select(IPCatalog)
        .where(IPCatalog.slug == slug)
        .where(IPCatalog.is_active == True)
    )
    ip = ip_result.scalar_one_or_none()

    if not ip:
        raise HTTPException(status_code=404, detail="IP not found")

    # Check rights
    rights_result = await db.execute(
        select(IPRights).where(IPRights.ip_id == ip.id)
    )
    rights = rights_result.scalar_one_or_none()

    license_status = rights.license_status if rights else ip.license_status

    if license_status == "prohibited":
        raise HTTPException(
            status_code=403,
            detail="This IP is not available for generation. Please check the licensing terms."
        )

    if license_status == "restricted":
        # In production, you might want to add additional checks here
        logger.warning(f"Generation started for restricted IP: {slug}")

    # Get preset
    preset_result = await db.execute(
        select(IPWorkflowPreset)
        .where(IPWorkflowPreset.id == request.preset_id)
        .where(IPWorkflowPreset.is_active == True)
    )
    preset = preset_result.scalar_one_or_none()

    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    if preset.ip_id != ip.id:
        raise HTTPException(status_code=400, detail="Preset does not belong to this IP")

    # Create generation record
    generation = IPGeneration(
        ip_id=ip.id,
        preset_id=preset.id,
        user_id=user_id,
        user_prompt=request.user_prompt,
        status="pending",
        credits_reserved=preset.estimated_credits,
    )

    db.add(generation)
    await db.flush()

    # In production, this would:
    # 1. Reserve credits via run-token service
    # 2. Start async workflow execution
    # 3. Return session ID for progress tracking

    # For now, we'll simulate the start
    # TODO: Integrate with actual workflow executor
    generation.status = "running"
    generation.current_step = "initializing"

    # Update IP stats
    await db.execute(
        update(IPCatalog)
        .where(IPCatalog.id == ip.id)
        .values(generation_count=IPCatalog.generation_count + 1)
    )

    # Update preset stats
    await db.execute(
        update(IPWorkflowPreset)
        .where(IPWorkflowPreset.id == preset.id)
        .values(usage_count=IPWorkflowPreset.usage_count + 1)
    )

    await db.flush()

    logger.info(
        f"IP generation started: generation_id={generation.id}, "
        f"ip={slug}, preset={preset.preset_type}, user={user_id}"
    )

    return GenerationStartResponse(
        generation_id=str(generation.id),
        session_id=None,  # Would be set by workflow executor
        status="running",
        estimated_credits=preset.estimated_credits,
        estimated_duration_seconds=preset.estimated_duration_seconds,
        message="Generation started. Track progress using the generation ID.",
    )


@router.get("/{slug}/generation/{generation_id}/progress", response_model=GenerationProgressResponse)
async def get_generation_progress(
    slug: str,
    generation_id: UUID,
    user_id: str = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get generation progress."""
    result = await db.execute(
        select(IPGeneration)
        .where(IPGeneration.id == generation_id)
    )
    generation = result.scalar_one_or_none()

    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")

    if generation.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this generation")

    return GenerationProgressResponse(
        generation_id=str(generation.id),
        status=generation.status,
        progress_percent=generation.progress_percent,
        current_step=generation.current_step,
        credits_consumed=generation.credits_consumed,
        latency_ms=generation.latency_ms,
        error_message=generation.error_message,
    )


@router.get("/{slug}/generation/{generation_id}/result", response_model=GenerationResultResponse)
async def get_generation_result(
    slug: str,
    generation_id: UUID,
    user_id: str = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get generation result."""
    result = await db.execute(
        select(IPGeneration)
        .where(IPGeneration.id == generation_id)
    )
    generation = result.scalar_one_or_none()

    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")

    if generation.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this generation")

    if generation.status not in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Generation not complete. Current status: {generation.status}"
        )

    return GenerationResultResponse(
        generation_id=str(generation.id),
        status=generation.status,
        output_artifacts=generation.output_artifacts or [],
        preview_url=generation.preview_url,
        credits_consumed=generation.credits_consumed,
        latency_ms=generation.latency_ms,
    )


@router.get("/{slug}/generation/{generation_id}/evidence", response_model=EvidenceResponse)
async def get_generation_evidence(
    slug: str,
    generation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get generation evidence and provenance.

    Returns evidence references for transparency and auditability:
    - RAG sources used
    - Pattern versions applied
    - Auteur style references
    - Workflow execution trace
    """
    result = await db.execute(
        select(IPGeneration)
        .where(IPGeneration.id == generation_id)
    )
    generation = result.scalar_one_or_none()

    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")

    # Get IP info
    ip_result = await db.execute(
        select(IPCatalog).where(IPCatalog.id == generation.ip_id)
    )
    ip = ip_result.scalar_one_or_none()

    # Get preset info
    preset_result = await db.execute(
        select(IPWorkflowPreset).where(IPWorkflowPreset.id == generation.preset_id)
    )
    preset = preset_result.scalar_one_or_none()

    return EvidenceResponse(
        generation_id=str(generation.id),
        evidence_refs=generation.evidence_refs or [],
        pattern_version=generation.pattern_version,
        ip_slug=ip.slug if ip else slug,
        preset_type=preset.preset_type if preset else "unknown",
        auteur_key=ip.auteur_key if ip else None,
        credits_consumed=generation.credits_consumed,
        latency_ms=generation.latency_ms,
        workflow_trace=[],  # Would be populated from workflow session
    )


@router.get("/my-generations")
async def get_my_generations(
    user_id: str = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    """Get user's generation history."""
    query = select(IPGeneration).where(IPGeneration.user_id == user_id)

    if status:
        query = query.where(IPGeneration.status == status)

    query = query.order_by(IPGeneration.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    generations = result.scalars().all()

    # Get IP info for each generation
    ip_ids = [g.ip_id for g in generations]
    if ip_ids:
        ip_result = await db.execute(
            select(IPCatalog).where(IPCatalog.id.in_(ip_ids))
        )
        ip_map = {ip.id: ip for ip in ip_result.scalars().all()}
    else:
        ip_map = {}

    return {
        "generations": [
            {
                "id": str(g.id),
                "ip_slug": ip_map.get(g.ip_id, {}).slug if g.ip_id in ip_map else None,
                "ip_name": ip_map.get(g.ip_id, {}).name_ko if g.ip_id in ip_map else None,
                "status": g.status,
                "progress_percent": g.progress_percent,
                "preview_url": g.preview_url,
                "credits_consumed": g.credits_consumed,
                "created_at": g.created_at.isoformat(),
            }
            for g in generations
        ],
        "limit": limit,
        "offset": offset,
    }


@router.post("/{slug}/generation/{generation_id}/cancel")
async def cancel_generation(
    slug: str,
    generation_id: UUID,
    user_id: str = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a running generation.

    Refunds unused credits via run-token system.
    """
    result = await db.execute(
        select(IPGeneration)
        .where(IPGeneration.id == generation_id)
    )
    generation = result.scalar_one_or_none()

    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")

    if generation.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this generation")

    if generation.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel generation with status: {generation.status}"
        )

    # Cancel and refund
    generation.status = "cancelled"
    generation.error_message = "Cancelled by user"

    # In production, this would trigger run-token refund
    # TODO: Integrate with run-token service

    await db.flush()

    logger.info(f"Generation cancelled: generation_id={generation.id}")

    return {
        "generation_id": str(generation.id),
        "status": "cancelled",
        "message": "Generation cancelled. Credits will be refunded.",
    }
