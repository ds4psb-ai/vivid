"""
Batch Processor Service - Async Processing with 50% Cost Reduction

Implements Google Gemini Batch API for background tasks that don't require
immediate responses. Batch jobs complete within 24 hours at 50% discount.

Use Cases:
- Content review and summarization
- Large-scale analysis tasks
- Bulk storyboard generation
- Synthetic data generation

References:
- https://ai.google.dev/gemini-api/docs/batch-api
- https://developers.googleblog.com/en/scale-your-ai-workloads-batch-mode-gemini-api/
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

class BatchJobStatus(str, Enum):
    """Batch job status enum."""
    PENDING = "JOB_STATE_PENDING"
    RUNNING = "JOB_STATE_RUNNING"
    SUCCEEDED = "JOB_STATE_SUCCEEDED"
    FAILED = "JOB_STATE_FAILED"
    CANCELLED = "JOB_STATE_CANCELLED"


class BatchJobType(str, Enum):
    """Types of batch jobs supported."""
    CONTENT_REVIEW = "content_review"
    BULK_ANALYSIS = "bulk_analysis"
    STORYBOARD_GENERATION = "storyboard_generation"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"


class BatchRequest(BaseModel):
    """Single request within a batch."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BatchJobConfig(BaseModel):
    """Configuration for a batch job."""
    job_type: BatchJobType
    display_name: Optional[str] = None
    model: str = "gemini-3-flash-preview"
    temperature: float = 0.7
    max_output_tokens: int = 2048
    callback_url: Optional[str] = None
    user_id: Optional[str] = None


class BatchJobRecord(BaseModel):
    """Record of a submitted batch job."""
    job_id: str
    job_name: str  # Gemini API job name
    job_type: BatchJobType
    status: BatchJobStatus = BatchJobStatus.PENDING
    display_name: Optional[str] = None
    model: str
    request_count: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    user_id: Optional[str] = None
    output_uri: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BatchResult(BaseModel):
    """Result of a completed batch job."""
    job_id: str
    request_id: str
    content: str
    finish_reason: Optional[str] = None
    usage: Dict[str, int] = Field(default_factory=dict)


# =============================================================================
# Batch Processor Service
# =============================================================================

class BatchProcessor:
    """
    Manages Gemini Batch API jobs for async processing.
    
    Benefits:
    - 50% cost reduction compared to real-time API
    - Higher rate limits for bulk processing
    - 24-hour completion SLO
    - Implicit caching with 90% discount on cached tokens
    
    Usage:
        processor = BatchProcessor()
        job_id = await processor.submit_job(requests, config)
        status = await processor.get_job_status(job_id)
        results = await processor.get_job_results(job_id)
    """
    
    _genai = None
    _jobs: Dict[str, BatchJobRecord] = {}  # In-memory job tracking
    
    @classmethod
    def _ensure_genai(cls):
        """Lazy load google.generativeai."""
        if cls._genai is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                cls._genai = genai
            except ImportError as e:
                logger.error("google-generativeai not installed", exc_info=e)
                raise
        return cls._genai
    
    @classmethod
    async def submit_job(
        cls,
        requests: List[BatchRequest],
        config: BatchJobConfig,
    ) -> BatchJobRecord:
        """
        Submit a batch job for async processing.
        
        Args:
            requests: List of prompts to process
            config: Job configuration
            
        Returns:
            BatchJobRecord with job details
            
        Note:
            Jobs complete within 24 hours at 50% discount.
        """
        genai = cls._ensure_genai()
        
        job_id = str(uuid.uuid4())
        display_name = config.display_name or f"{config.job_type.value}_{job_id[:8]}"
        
        try:
            # Build inline requests for the batch
            inline_requests = []
            for req in requests:
                inline_requests.append({
                    "custom_id": req.request_id,
                    "request": {
                        "contents": [{"parts": [{"text": req.prompt}]}],
                        "generationConfig": {
                            "temperature": config.temperature,
                            "maxOutputTokens": config.max_output_tokens,
                        }
                    }
                })
            
            # Submit batch job
            batch_job = genai.batches.create(
                model=f"models/{config.model}",
                src=inline_requests,
                config={
                    "display_name": display_name,
                }
            )
            
            # Create job record
            job_record = BatchJobRecord(
                job_id=job_id,
                job_name=batch_job.name,
                job_type=config.job_type,
                display_name=display_name,
                model=config.model,
                request_count=len(requests),
                user_id=config.user_id,
                metadata={
                    "callback_url": config.callback_url,
                    "request_ids": [r.request_id for r in requests],
                }
            )
            
            # Store in memory (should be DB in production)
            cls._jobs[job_id] = job_record
            
            logger.info(
                "Batch job submitted",
                extra={
                    "job_id": job_id,
                    "job_name": batch_job.name,
                    "job_type": config.job_type.value,
                    "request_count": len(requests),
                }
            )
            
            return job_record
            
        except Exception as e:
            logger.error("Failed to submit batch job", exc_info=e)
            raise
    
    @classmethod
    async def get_job_status(cls, job_id: str) -> Optional[BatchJobRecord]:
        """
        Get the current status of a batch job.
        
        Args:
            job_id: Job ID returned from submit_job
            
        Returns:
            Updated BatchJobRecord or None if not found
        """
        job_record = cls._jobs.get(job_id)
        if not job_record:
            return None
        
        genai = cls._ensure_genai()
        
        try:
            # Poll Gemini API for status
            batch_job = genai.batches.get(name=job_record.job_name)
            
            # Update status
            new_status = BatchJobStatus(batch_job.state)
            job_record.status = new_status
            job_record.updated_at = datetime.now(timezone.utc)
            
            if new_status == BatchJobStatus.SUCCEEDED:
                job_record.completed_at = datetime.now(timezone.utc)
                job_record.output_uri = getattr(batch_job, "output_uri", None)
            elif new_status == BatchJobStatus.FAILED:
                job_record.completed_at = datetime.now(timezone.utc)
                job_record.error = getattr(batch_job, "error_message", "Unknown error")
            
            logger.debug(
                "Batch job status updated",
                extra={"job_id": job_id, "status": new_status.value}
            )
            
            return job_record
            
        except Exception as e:
            logger.warning("Failed to get batch job status", exc_info=e)
            return job_record
    
    @classmethod
    async def get_job_results(cls, job_id: str) -> List[BatchResult]:
        """
        Get results from a completed batch job.
        
        Args:
            job_id: Job ID returned from submit_job
            
        Returns:
            List of BatchResult objects
        """
        job_record = cls._jobs.get(job_id)
        if not job_record:
            return []
        
        if job_record.status != BatchJobStatus.SUCCEEDED:
            logger.warning(
                "Attempting to get results for non-completed job",
                extra={"job_id": job_id, "status": job_record.status.value}
            )
            return []
        
        genai = cls._ensure_genai()
        
        try:
            # Retrieve batch job results
            batch_job = genai.batches.get(name=job_record.job_name)
            
            results = []
            if hasattr(batch_job, "responses"):
                for response in batch_job.responses:
                    result = BatchResult(
                        job_id=job_id,
                        request_id=response.get("custom_id", ""),
                        content=cls._extract_content(response),
                        finish_reason=response.get("finish_reason"),
                        usage=response.get("usage_metadata", {}),
                    )
                    results.append(result)
            
            logger.info(
                "Batch job results retrieved",
                extra={"job_id": job_id, "result_count": len(results)}
            )
            
            return results
            
        except Exception as e:
            logger.error("Failed to get batch job results", exc_info=e)
            return []
    
    @classmethod
    def _extract_content(cls, response: Dict[str, Any]) -> str:
        """Extract text content from batch response."""
        try:
            candidates = response.get("response", {}).get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        except Exception:
            pass
        return ""
    
    @classmethod
    async def cancel_job(cls, job_id: str) -> bool:
        """
        Cancel a pending or running batch job.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        job_record = cls._jobs.get(job_id)
        if not job_record:
            return False
        
        if job_record.status not in [BatchJobStatus.PENDING, BatchJobStatus.RUNNING]:
            return False
        
        genai = cls._ensure_genai()
        
        try:
            genai.batches.cancel(name=job_record.job_name)
            job_record.status = BatchJobStatus.CANCELLED
            job_record.updated_at = datetime.now(timezone.utc)
            
            logger.info("Batch job cancelled", extra={"job_id": job_id})
            return True
            
        except Exception as e:
            logger.error("Failed to cancel batch job", exc_info=e)
            return False
    
    @classmethod
    async def list_jobs(
        cls,
        user_id: Optional[str] = None,
        job_type: Optional[BatchJobType] = None,
        status: Optional[BatchJobStatus] = None,
    ) -> List[BatchJobRecord]:
        """
        List batch jobs with optional filters.
        
        Args:
            user_id: Filter by user
            job_type: Filter by job type
            status: Filter by status
            
        Returns:
            List of matching BatchJobRecord objects
        """
        jobs = list(cls._jobs.values())
        
        if user_id:
            jobs = [j for j in jobs if j.user_id == user_id]
        if job_type:
            jobs = [j for j in jobs if j.job_type == job_type]
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)


# =============================================================================
# Convenience Functions
# =============================================================================

async def submit_content_review(
    contents: List[str],
    user_id: Optional[str] = None,
) -> BatchJobRecord:
    """
    Submit content for async review.
    
    Args:
        contents: List of content strings to review
        user_id: Optional user ID for tracking
        
    Returns:
        BatchJobRecord with job details
    """
    requests = [
        BatchRequest(
            prompt=f"""
다음 콘텐츠를 리뷰하고 평가해주세요:

{content}

평가 기준:
1. 창의성 (1-10)
2. 명확성 (1-10)
3. 기술적 품질 (1-10)
4. 개선 제안

JSON 형식으로 응답해주세요.
""",
            metadata={"content_index": i}
        )
        for i, content in enumerate(contents)
    ]
    
    config = BatchJobConfig(
        job_type=BatchJobType.CONTENT_REVIEW,
        display_name=f"content_review_{len(contents)}_items",
        user_id=user_id,
    )
    
    return await BatchProcessor.submit_job(requests, config)


async def submit_bulk_analysis(
    items: List[Dict[str, Any]],
    analysis_prompt: str,
    user_id: Optional[str] = None,
) -> BatchJobRecord:
    """
    Submit items for bulk analysis.
    
    Args:
        items: List of items to analyze
        analysis_prompt: Base prompt for analysis
        user_id: Optional user ID for tracking
        
    Returns:
        BatchJobRecord with job details
    """
    requests = [
        BatchRequest(
            prompt=f"{analysis_prompt}\n\n데이터:\n{json.dumps(item, ensure_ascii=False)}",
            metadata={"item_index": i}
        )
        for i, item in enumerate(items)
    ]
    
    config = BatchJobConfig(
        job_type=BatchJobType.BULK_ANALYSIS,
        display_name=f"bulk_analysis_{len(items)}_items",
        user_id=user_id,
    )
    
    return await BatchProcessor.submit_job(requests, config)


async def submit_storyboard_generation(
    concepts: List[str],
    scene_count: int = 5,
    user_id: Optional[str] = None,
) -> BatchJobRecord:
    """
    Submit concepts for bulk storyboard generation.
    
    Args:
        concepts: List of story concepts
        scene_count: Number of scenes per storyboard
        user_id: Optional user ID for tracking
        
    Returns:
        BatchJobRecord with job details
    """
    requests = [
        BatchRequest(
            prompt=f"""
다음 개념을 {scene_count}개 장면의 스토리보드로 변환해주세요:

개념: {concept}

각 장면에 대해 다음을 포함해주세요:
- 장면 번호
- 설명
- 카메라 앵글
- 조명
- 예상 시간

JSON 배열 형식으로 응답해주세요.
""",
            metadata={"concept_index": i, "scene_count": scene_count}
        )
        for i, concept in enumerate(concepts)
    ]
    
    config = BatchJobConfig(
        job_type=BatchJobType.STORYBOARD_GENERATION,
        display_name=f"storyboard_gen_{len(concepts)}_concepts",
        user_id=user_id,
        temperature=0.8,  # More creative for storyboards
    )
    
    return await BatchProcessor.submit_job(requests, config)
