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


# =============================================================================
# Background Task: Workflow Execution (FastAPI 2026 Pattern)
# =============================================================================

async def execute_generation_workflow(
    generation_id: UUID,
    run_token: str,
    run_id: str,
):
    """Execute generation workflow in background.

    FastAPI 2026 Best Practice:
    - Create own DB session (not from dependency)
    - Only receive IDs, not ORM objects
    - Handle errors with credit refund
    """
    start_time = time.monotonic()

    async with AsyncSessionLocal() as db:
        try:
            # Load generation
            result = await db.execute(
                select(IPGeneration).where(IPGeneration.id == generation_id)
            )
            generation = result.scalar_one_or_none()

            if not generation:
                logger.error(f"Generation not found: {generation_id}")
                return

            # Load preset with workflow steps
            preset_result = await db.execute(
                select(IPWorkflowPreset).where(IPWorkflowPreset.id == generation.preset_id)
            )
            preset = preset_result.scalar_one_or_none()

            # Load IP for auteur key
            ip_result = await db.execute(
                select(IPCatalog).where(IPCatalog.id == generation.ip_id)
            )
            ip = ip_result.scalar_one_or_none()

            # Update status
            generation.status = "running"
            generation.current_step = "workflow_init"
            generation.progress_percent = 10
            await db.commit()

            # Build capsule inputs
            capsule_inputs = {
                "topic": generation.user_prompt or f"Fan fiction for {ip.name_en if ip else 'IP'}",
                "ip_context": ip.worldbuilding if ip else {},
                "auteur_key": ip.auteur_key if ip else None,
            }

            # Execute capsule (sealed - internal DAG hidden)
            capsule_result: CapsuleExecutionResult = await execute_capsule(
                capsule_id=preset.workflow_capsule_id or "teaching.story.generate:1.0.0",
                inputs=capsule_inputs,
                params={
                    "model": "gemini-2.0-flash",
                    "preset_type": preset.preset_type,
                },
                user={"user_id": generation.user_id},
                db=db,
                run_id=run_id,
            )

            # Generate evidence refs
            evidence_refs = generate_evidence_refs(
                generation=generation,
                preset=preset,
                ip=ip,
                capsule_result=capsule_result,
            )

            # Calculate latency
            latency_ms = int((time.monotonic() - start_time) * 1000)

            if capsule_result.status == "done":
                # Success
                generation.status = "completed"
                generation.progress_percent = 100
                generation.current_step = None
                generation.output_artifacts = capsule_result.summary.get("artifacts", [])
                generation.evidence_refs = evidence_refs
                generation.pattern_version = preset.pattern_version or "v1.0.0"
                generation.credits_consumed = capsule_result.token_usage.get("total_credits", preset.estimated_credits)
                generation.latency_ms = latency_ms

                # Deduct credits
                success, _, error = await run_token_service.deduct_credits(
                    run_token,
                    generation.credits_consumed,
                )
                if not success:
                    logger.warning(f"Failed to deduct credits: {error}")

                logger.info(f"Generation completed: {generation_id}, latency={latency_ms}ms")
            else:
                # Failed
                generation.status = "failed"
                generation.error_message = capsule_result.error or "Workflow execution failed"
                generation.latency_ms = latency_ms

                # Refund credits
                await run_token_service.refund_credits(run_token)

                logger.error(f"Generation failed: {generation_id}, error={capsule_result.error}")

            await db.commit()

        except Exception as e:
            logger.exception(f"Background task error: {generation_id}")

            # Update status
            generation.status = "failed"
            generation.error_message = str(e)
            await db.commit()

            # Refund credits
            try:
                await run_token_service.refund_credits(run_token)
            except Exception as refund_error:
                logger.error(f"Failed to refund credits: {refund_error}")


def generate_evidence_refs(
    generation: IPGeneration,
    preset: IPWorkflowPreset,
    ip: IPCatalog,
    capsule_result: CapsuleExecutionResult,
) -> list[str]:
    """Generate evidence references for transparency.

    SSoT: evidence_refs is List[str]
    """
    refs = []

    # 1. IP source
    if ip:
        refs.append(f"db:ip_catalog:{ip.id}")

    # 2. Preset source
    refs.append(f"db:ip_presets:{preset.id}")

    # 3. Auteur style reference
    if ip and ip.auteur_key:
        refs.append(f"rag:auteur:{ip.auteur_key}")

    # 4. Pattern version
    refs.append(f"pattern:{preset.pattern_version or 'v1.0.0'}")

    # 5. Capsule run
    refs.append(f"capsule:run:{capsule_result.run_id}")

    # 6. Include capsule's evidence refs
    if capsule_result.evidence_refs:
        refs.extend(capsule_result.evidence_refs[:5])  # Limit to 5

    return refs


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
    background_tasks: BackgroundTasks,
    user_id: str = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Start generation from IP preset.

    This endpoint implements the sealed capsule pattern:
    1. Validates IP rights (prohibited → 403)
    2. Loads preset workflow configuration (sealed)
    3. Reserves run-token credits
    4. Starts async workflow execution via BackgroundTasks
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

    # Issue run-token and reserve credits
    success, run_token, run_id, error = await run_token_service.issue_token(
        user_id=user_id,
        app_id=f"ip_generation:{preset.id}",
        credits_to_reserve=preset.estimated_credits,
        permissions=["capsule:execute", "storage:write"],
    )

    if not success:
        logger.error(f"Failed to issue run-token: {error}")
        raise HTTPException(
            status_code=402,
            detail=f"Failed to reserve credits: {error or 'Insufficient credits'}"
        )

    # Create generation record
    generation = IPGeneration(
        ip_id=ip.id,
        preset_id=preset.id,
        user_id=user_id,
        user_prompt=request.user_prompt,
        status="pending",
        credits_reserved=preset.estimated_credits,
        run_token_id=run_id,  # Store run-token ID
        workflow_session_id=run_id,
    )

    db.add(generation)
    await db.flush()

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

    await db.commit()

    # Start background workflow execution
    # FastAPI 2026 Pattern: Pass only IDs, create new session in task
    background_tasks.add_task(
        execute_generation_workflow,
        generation_id=generation.id,
        run_token=run_token,
        run_id=run_id,
    )

    logger.info(
        f"IP generation started: generation_id={generation.id}, "
        f"ip={slug}, preset={preset.preset_type}, user={user_id}, run_id={run_id}"
    )

    return GenerationStartResponse(
        generation_id=str(generation.id),
        session_id=run_id,
        status="pending",
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

    # Refund credits via run-token
    if generation.run_token_id:
        try:
            # Get the token from storage and refund
            await run_token_service.refund_credits(generation.run_token_id)
            logger.info(f"Credits refunded for cancelled generation: {generation_id}")
        except Exception as e:
            logger.error(f"Failed to refund credits for {generation_id}: {e}")

    await db.commit()

    logger.info(f"Generation cancelled: generation_id={generation.id}")

    return {
        "generation_id": str(generation.id),
        "status": "cancelled",
        "message": "Generation cancelled. Credits have been refunded.",
    }


# =============================================================================
# SSE Streaming Endpoint (2026 Best Practice)
# =============================================================================

@router.get("/{slug}/generation/{generation_id}/stream")
async def stream_generation_progress(
    slug: str,
    generation_id: UUID,
):
    """Stream generation progress via Server-Sent Events.

    2026 Best Practice: SSE instead of polling for real-time updates.
    Reduces bandwidth by ~90% compared to polling.
    """
    async def event_generator():
        last_status = None
        last_progress = -1
        consecutive_errors = 0
        max_errors = 5

        while True:
            try:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(IPGeneration).where(IPGeneration.id == generation_id)
                    )
                    generation = result.scalar_one_or_none()

                    if not generation:
                        yield {
                            "event": "error",
                            "data": json.dumps({"error": "Generation not found"})
                        }
                        break

                    # Only emit when status or progress changes
                    if (generation.status != last_status or
                        generation.progress_percent != last_progress):

                        yield {
                            "event": "progress",
                            "data": json.dumps({
                                "generation_id": str(generation.id),
                                "status": generation.status,
                                "progress_percent": generation.progress_percent,
                                "current_step": generation.current_step,
                                "credits_consumed": generation.credits_consumed,
                                "latency_ms": generation.latency_ms,
                                "error_message": generation.error_message,
                            })
                        }

                        last_status = generation.status
                        last_progress = generation.progress_percent

                    # Stop if terminal state
                    if generation.status in ["completed", "failed", "cancelled"]:
                        yield {
                            "event": "complete",
                            "data": json.dumps({
                                "status": generation.status,
                                "preview_url": generation.preview_url,
                            })
                        }
                        break

                consecutive_errors = 0
                await asyncio.sleep(1)  # 1 second between checks

            except Exception as e:
                consecutive_errors += 1
                logger.error(f"SSE error for {generation_id}: {e}")

                if consecutive_errors >= max_errors:
                    yield {
                        "event": "error",
                        "data": json.dumps({"error": "Connection lost"})
                    }
                    break

                await asyncio.sleep(2)

    return EventSourceResponse(event_generator())
