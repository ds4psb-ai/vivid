"""
Batch API Router - Async Processing Endpoints

Provides REST endpoints for batch job management:
- Submit batch jobs (50% cost reduction)
- Poll job status
- Retrieve results
- Cancel jobs

All batch jobs complete within 24 hours.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.services.batch_processor import (
    BatchProcessor,
    BatchRequest,
    BatchJobConfig,
    BatchJobRecord,
    BatchJobStatus,
    BatchJobType,
    BatchResult,
    submit_content_review,
    submit_bulk_analysis,
    submit_storyboard_generation,
)
from app.dependencies import get_current_user_optional
from app.logging_config import get_logger

router = APIRouter(prefix="/api/v1/batch", tags=["batch"])
logger = get_logger("batch_router")


# =============================================================================
# Request/Response Models
# =============================================================================

class SubmitBatchRequest(BaseModel):
    """Request to submit a batch job."""
    requests: List[BatchRequest]
    job_type: BatchJobType
    display_name: Optional[str] = None
    model: str = "gemini-3-flash-preview"
    temperature: float = 0.7
    max_output_tokens: int = 2048
    callback_url: Optional[str] = None


class ContentReviewRequest(BaseModel):
    """Request for content review batch job."""
    contents: List[str] = Field(..., min_items=1, max_items=100)


class BulkAnalysisRequest(BaseModel):
    """Request for bulk analysis batch job."""
    items: List[dict] = Field(..., min_items=1, max_items=100)
    analysis_prompt: str = Field(..., min_length=10)


class StoryboardGenerationRequest(BaseModel):
    """Request for bulk storyboard generation."""
    concepts: List[str] = Field(..., min_items=1, max_items=50)
    scene_count: int = Field(default=5, ge=3, le=20)


class BatchJobResponse(BaseModel):
    """Response with batch job details."""
    job_id: str
    job_name: str
    job_type: str
    status: str
    display_name: Optional[str]
    model: str
    request_count: int
    created_at: str
    updated_at: str
    completed_at: Optional[str]
    error: Optional[str]


class BatchJobListResponse(BaseModel):
    """Response with list of batch jobs."""
    jobs: List[BatchJobResponse]
    total: int


class BatchResultsResponse(BaseModel):
    """Response with batch job results."""
    job_id: str
    status: str
    results: List[BatchResult]
    total: int


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/submit", response_model=BatchJobResponse)
async def submit_batch(
    request: SubmitBatchRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Submit a batch job for async processing.
    
    **Benefits:**
    - 50% cost reduction vs real-time API
    - Higher rate limits
    - 24-hour completion SLO
    
    **Job Types:**
    - content_review
    - bulk_analysis
    - storyboard_generation
    - translation
    - summarization
    """
    if not request.requests:
        raise HTTPException(status_code=400, detail="At least one request required")
    
    if len(request.requests) > 1000:
        raise HTTPException(status_code=400, detail="Maximum 1000 requests per batch")
    
    user_id = user.get("sub") if user else None
    
    config = BatchJobConfig(
        job_type=request.job_type,
        display_name=request.display_name,
        model=request.model,
        temperature=request.temperature,
        max_output_tokens=request.max_output_tokens,
        callback_url=request.callback_url,
        user_id=user_id,
    )
    
    try:
        job_record = await BatchProcessor.submit_job(request.requests, config)
        return _to_response(job_record)
    except Exception as e:
        logger.error("Failed to submit batch job", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review", response_model=BatchJobResponse)
async def submit_review_batch(
    request: ContentReviewRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Submit content for async review.
    
    Reviews each piece of content for:
    - 창의성 (Creativity)
    - 명확성 (Clarity)
    - 기술적 품질 (Technical Quality)
    - 개선 제안 (Improvement Suggestions)
    """
    user_id = user.get("sub") if user else None
    
    try:
        job_record = await submit_content_review(request.contents, user_id)
        return _to_response(job_record)
    except Exception as e:
        logger.error("Failed to submit review batch", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=BatchJobResponse)
async def submit_analysis_batch(
    request: BulkAnalysisRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Submit items for bulk analysis.
    
    Applies the provided prompt to each item in the list.
    """
    user_id = user.get("sub") if user else None
    
    try:
        job_record = await submit_bulk_analysis(
            request.items,
            request.analysis_prompt,
            user_id,
        )
        return _to_response(job_record)
    except Exception as e:
        logger.error("Failed to submit analysis batch", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/storyboards", response_model=BatchJobResponse)
async def submit_storyboard_batch(
    request: StoryboardGenerationRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Submit concepts for bulk storyboard generation.
    
    Generates structured storyboards with scenes, camera angles,
    lighting, and timing for each concept.
    """
    user_id = user.get("sub") if user else None
    
    try:
        job_record = await submit_storyboard_generation(
            request.concepts,
            request.scene_count,
            user_id,
        )
        return _to_response(job_record)
    except Exception as e:
        logger.error("Failed to submit storyboard batch", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_model=BatchJobResponse)
async def get_job_status(
    job_id: str,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Get the current status of a batch job.
    
    **Statuses:**
    - PENDING: Job is queued
    - RUNNING: Job is being processed
    - SUCCEEDED: Job completed successfully
    - FAILED: Job failed
    - CANCELLED: Job was cancelled
    """
    job_record = await BatchProcessor.get_job_status(job_id)
    
    if not job_record:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return _to_response(job_record)


@router.get("/{job_id}/results", response_model=BatchResultsResponse)
async def get_job_results(
    job_id: str,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Get results from a completed batch job.
    
    Only available for jobs with status SUCCEEDED.
    """
    job_record = await BatchProcessor.get_job_status(job_id)
    
    if not job_record:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_record.status != BatchJobStatus.SUCCEEDED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Current status: {job_record.status.value}"
        )
    
    results = await BatchProcessor.get_job_results(job_id)
    
    return BatchResultsResponse(
        job_id=job_id,
        status=job_record.status.value,
        results=results,
        total=len(results),
    )


@router.post("/{job_id}/cancel", response_model=BatchJobResponse)
async def cancel_job(
    job_id: str,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Cancel a pending or running batch job.
    
    Only jobs with status PENDING or RUNNING can be cancelled.
    """
    job_record = await BatchProcessor.get_job_status(job_id)
    
    if not job_record:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_record.status not in [BatchJobStatus.PENDING, BatchJobStatus.RUNNING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status: {job_record.status.value}"
        )
    
    success = await BatchProcessor.cancel_job(job_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to cancel job")
    
    # Refresh status
    job_record = await BatchProcessor.get_job_status(job_id)
    return _to_response(job_record)


@router.get("/", response_model=BatchJobListResponse)
async def list_jobs(
    job_type: Optional[BatchJobType] = None,
    status: Optional[BatchJobStatus] = None,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    List batch jobs with optional filters.
    
    Filter by:
    - job_type: content_review, bulk_analysis, storyboard_generation, etc.
    - status: PENDING, RUNNING, SUCCEEDED, FAILED, CANCELLED
    """
    user_id = user.get("sub") if user else None
    
    jobs = await BatchProcessor.list_jobs(
        user_id=user_id,
        job_type=job_type,
        status=status,
    )
    
    return BatchJobListResponse(
        jobs=[_to_response(job) for job in jobs],
        total=len(jobs),
    )


# =============================================================================
# Helpers
# =============================================================================

def _to_response(job: BatchJobRecord) -> BatchJobResponse:
    """Convert BatchJobRecord to API response."""
    return BatchJobResponse(
        job_id=job.job_id,
        job_name=job.job_name,
        job_type=job.job_type.value,
        status=job.status.value,
        display_name=job.display_name,
        model=job.model,
        request_count=job.request_count,
        created_at=job.created_at.isoformat() + "Z",
        updated_at=job.updated_at.isoformat() + "Z",
        completed_at=job.completed_at.isoformat() + "Z" if job.completed_at else None,
        error=job.error,
    )
