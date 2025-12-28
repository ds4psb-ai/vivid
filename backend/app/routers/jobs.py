"""Async Jobs API Router (Phase 3).

Provides endpoints for submitting long-running jobs and polling their status.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from arq.connections import ArqRedis
from arq.jobs import Job, JobStatus

from app.auth import get_is_admin

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────

class AnalyzeJobRequest(BaseModel):
    """Request to start an analysis job."""
    source_pack: Dict[str, Any]
    capsule_id: str


class GenerateJobRequest(BaseModel):
    """Request to start a generation job."""
    storyboard_cards: List[Dict[str, Any]]
    provider: str = "mock"
    sequence_id: str = "seq-01"
    scene_id: str = "scene-01"


class JobSubmitResponse(BaseModel):
    """Response when a job is successfully submitted."""
    job_id: str
    status: str = "queued"
    message: str = "Job submitted successfully"


class JobStatusResponse(BaseModel):
    """Response for job status query."""
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def get_arq_pool(request: Request) -> ArqRedis:
    """Dependency to get Arq Redis pool from app state."""
    if not hasattr(request.app.state, "arq_pool"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Worker pool not initialized"
        )
    return request.app.state.arq_pool


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/jobs/analyze", response_model=JobSubmitResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_analyze_job(
    data: AnalyzeJobRequest,
    arq_pool: ArqRedis = Depends(get_arq_pool),
    is_admin: bool = Depends(get_is_admin),
):
    """
    Submit a source pack analysis job to the worker queue.
    Returns immediately with job_id for status polling.
    """
    job = await arq_pool.enqueue_job(
        "analyze_source_pack",
        source_pack=data.source_pack,
        capsule_id=data.capsule_id,
    )
    return JobSubmitResponse(job_id=job.job_id)


@router.post("/jobs/generate", response_model=JobSubmitResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_generate_job(
    data: GenerateJobRequest,
    arq_pool: ArqRedis = Depends(get_arq_pool),
    is_admin: bool = Depends(get_is_admin),
):
    """
    Submit a video generation job to the worker queue.
    Returns immediately with job_id for status polling.
    """
    job = await arq_pool.enqueue_job(
        "generate_video_batch",
        storyboard_cards=data.storyboard_cards,
        provider=data.provider,
        sequence_id=data.sequence_id,
        scene_id=data.scene_id,
    )
    return JobSubmitResponse(job_id=job.job_id)


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    arq_pool: ArqRedis = Depends(get_arq_pool),
):
    """
    Get the status of an async job by its ID.
    
    Status values:
    - queued: Job is waiting to be processed
    - in_progress: Job is currently being processed
    - completed: Job finished successfully
    - failed: Job encountered an error
    - not_found: Job ID not found
    """
    job = Job(job_id, arq_pool)
    job_status = await job.status()
    
    if job_status == JobStatus.not_found:
        return JobStatusResponse(job_id=job_id, status="not_found")
    
    if job_status == JobStatus.queued:
        return JobStatusResponse(job_id=job_id, status="queued")
    
    if job_status == JobStatus.in_progress:
        return JobStatusResponse(job_id=job_id, status="in_progress")
    
    # Job is complete, get result
    result = await job.result()
    if isinstance(result, dict) and result.get("status") == "failed":
        return JobStatusResponse(
            job_id=job_id,
            status="failed",
            error=result.get("error"),
        )
    
    return JobStatusResponse(
        job_id=job_id,
        status="completed",
        result=result,
    )
