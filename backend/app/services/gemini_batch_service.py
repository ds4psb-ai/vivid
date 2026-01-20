"""Gemini Batch API Service - 50% Cost Reduction.

Batch API를 사용하여 비실시간 작업을 50% 저렴하게 처리합니다.

2026 Best Practices:
- 24시간 SLA 내 완료 (대부분 더 빠름)
- Context Caching과 조합 가능 (캐시 히트 시 90% 할인 우선)
- RAG 평가, 대량 콘텐츠 생성, 데이터 전처리에 적합

Usage:
    from app.services.gemini_batch_service import GeminiBatchService

    service = GeminiBatchService()

    # 배치 작업 생성
    job = await service.create_batch_job(
        requests=[
            {"prompt": "프롬프트 1", "system": "시스템 지시"},
            {"prompt": "프롬프트 2", "system": "시스템 지시"},
        ],
        model="gemini-2.5-flash",
        job_name="my-batch-job",
    )

    # 결과 조회
    results = await service.get_batch_results(job.name)
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Constants & Enums
# =============================================================================

class BatchJobStatus(str, Enum):
    """Batch job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchModel(str, Enum):
    """Models supporting Batch API (50% discount).

    2026 Production Models:
    - Text: gemini-3-flash-preview, gemini-3-pro-preview
    - Image: gemini-3-pro-image-preview (Nanobanana Pro)
    - Video: veo-3.1-generate-preview (Quality), veo-3.1-fast-generate-preview (Fast)
    """
    # Gemini 3.0 Preview (Text) - PRIMARY
    GEMINI_3_FLASH_PREVIEW = "gemini-3-flash-preview"
    GEMINI_3_PRO_PREVIEW = "gemini-3-pro-preview"
    # Gemini 3.0 Image (Nanobanana Pro)
    GEMINI_3_PRO_IMAGE_PREVIEW = "gemini-3-pro-image-preview"
    # Veo 3.1 Video Generation
    VEO_3_1_QUALITY = "veo-3.1-generate-preview"
    VEO_3_1_FAST = "veo-3.1-fast-generate-preview"


# Batch pricing (50% of standard) - 2026 Models
BATCH_PRICING_PER_1M_TOKENS = {
    # Gemini 3.0 Text Models
    BatchModel.GEMINI_3_FLASH_PREVIEW.value: {"input": 0.25, "output": 1.50},   # Standard: 0.50/3.0
    BatchModel.GEMINI_3_PRO_PREVIEW.value: {"input": 1.0, "output": 6.0},       # Standard: 2.0/12.0
    # Gemini 3.0 Image (Nanobanana Pro)
    BatchModel.GEMINI_3_PRO_IMAGE_PREVIEW.value: {"input": 0.50, "output": 2.0},  # Image generation
    # Veo 3.1 Video - per minute pricing (not per token)
    BatchModel.VEO_3_1_QUALITY.value: {"per_minute": 0.175},    # Standard: $0.35/min
    BatchModel.VEO_3_1_FAST.value: {"per_minute": 0.0875},      # Standard: $0.175/min
}

# Default batch configuration (can be overridden by settings)
DEFAULT_BATCH_MODEL = BatchModel.GEMINI_3_FLASH_PREVIEW.value
MAX_REQUESTS_PER_BATCH = settings.GEMINI_BATCH_MAX_REQUESTS if hasattr(settings, 'GEMINI_BATCH_MAX_REQUESTS') else 100_000
POLL_INTERVAL_SECONDS = settings.GEMINI_BATCH_POLL_INTERVAL if hasattr(settings, 'GEMINI_BATCH_POLL_INTERVAL') else 30
MAX_WAIT_HOURS = settings.GEMINI_BATCH_MAX_WAIT_HOURS if hasattr(settings, 'GEMINI_BATCH_MAX_WAIT_HOURS') else 24


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class BatchRequest:
    """Single request in a batch job."""
    prompt: str
    system_instruction: Optional[str] = None
    generation_config: Optional[Dict[str, Any]] = None
    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchResponse:
    """Single response from a batch job."""
    request_id: str
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchJob:
    """Batch job information."""
    job_id: str
    name: str
    model: str
    status: BatchJobStatus
    total_requests: int
    completed_requests: int = 0
    failed_requests: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    results: List[BatchResponse] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Gemini Batch Service
# =============================================================================

class GeminiBatchService:
    """Gemini Batch API Service for 50% cost reduction.

    Batch API는 비실시간 작업을 비동기적으로 처리하여 50% 비용 절감을 제공합니다.
    24시간 SLA 내 완료되며, 대부분 더 빠르게 처리됩니다.

    적합한 사용 사례:
    - RAG 품질 평가 (대량 샘플)
    - 대량 콘텐츠 생성 (블로그, 설명문)
    - 데이터 전처리/변환
    - 평가 파이프라인
    - 번역/요약 배치

    부적합한 사용 사례:
    - 실시간 채팅
    - 즉시 응답이 필요한 API
    - 인터랙티브 기능
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini Batch Service.

        Args:
            api_key: Gemini API key. If not provided, uses settings.GEMINI_BATCH_API_KEY
                     or settings.GEMINI_API_KEY as fallback.
        """
        # Priority: provided key > BATCH_API_KEY > GEMINI_API_KEY
        # H1.3: SecretStr - use .get_secret_value() for actual API key
        batch_key = settings.GEMINI_BATCH_API_KEY.get_secret_value() if settings.GEMINI_BATCH_API_KEY else None
        gemini_key = settings.GEMINI_API_KEY.get_secret_value() if settings.GEMINI_API_KEY else None
        self._api_key = api_key or batch_key or gemini_key
        self._client = None
        self._jobs: Dict[str, BatchJob] = {}

    def _get_client(self):
        """Get or create Gemini client using new SDK."""
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self._api_key)
                logger.info("Gemini Batch client initialized with google.genai SDK")
            except ImportError:
                # Fallback to old SDK if new one not available
                logger.warning("google-genai not installed, batch features limited")
                raise ImportError(
                    "Batch API requires google-genai SDK. "
                    "Install with: pip install google-genai"
                )
        return self._client

    def estimate_cost(
        self,
        requests: List[BatchRequest],
        model: str = DEFAULT_BATCH_MODEL,
    ) -> Dict[str, float]:
        """Estimate batch job cost (50% of standard pricing).

        Args:
            requests: List of batch requests
            model: Model to use

        Returns:
            Cost estimate dict with input/output/total costs
        """
        pricing = BATCH_PRICING_PER_1M_TOKENS.get(model, BATCH_PRICING_PER_1M_TOKENS[DEFAULT_BATCH_MODEL])

        # Rough token estimation (4 chars ≈ 1 token)
        total_input_chars = sum(
            len(r.prompt) + len(r.system_instruction or "")
            for r in requests
        )
        estimated_input_tokens = total_input_chars / 4

        # Assume output is ~2x input for generation tasks
        estimated_output_tokens = estimated_input_tokens * 2

        input_cost = (estimated_input_tokens / 1_000_000) * pricing["input"]
        output_cost = (estimated_output_tokens / 1_000_000) * pricing["output"]

        # Standard pricing for comparison
        standard_pricing = {
            k: v * 2 for k, v in pricing.items()  # Batch is 50% off
        }
        standard_cost = (estimated_input_tokens / 1_000_000) * standard_pricing["input"] + \
                       (estimated_output_tokens / 1_000_000) * standard_pricing["output"]

        return {
            "estimated_input_tokens": int(estimated_input_tokens),
            "estimated_output_tokens": int(estimated_output_tokens),
            "batch_cost_usd": round(input_cost + output_cost, 4),
            "standard_cost_usd": round(standard_cost, 4),
            "savings_usd": round(standard_cost - (input_cost + output_cost), 4),
            "savings_percent": 50.0,
        }

    async def create_batch_job(
        self,
        requests: List[BatchRequest | Dict[str, Any]],
        model: str = DEFAULT_BATCH_MODEL,
        job_name: Optional[str] = None,
        generation_config: Optional[Dict[str, Any]] = None,
    ) -> BatchJob:
        """Create a new batch job.

        Args:
            requests: List of BatchRequest objects or dicts with 'prompt' key
            model: Model to use (default: gemini-2.5-flash)
            job_name: Optional job name for tracking
            generation_config: Default generation config for all requests

        Returns:
            BatchJob with job_id and initial status

        Raises:
            ValueError: If requests exceed limits or invalid model
        """
        if len(requests) > MAX_REQUESTS_PER_BATCH:
            raise ValueError(f"Maximum {MAX_REQUESTS_PER_BATCH} requests per batch")

        if not requests:
            raise ValueError("At least one request required")

        # Normalize requests
        normalized_requests: List[BatchRequest] = []
        for r in requests:
            if isinstance(r, dict):
                normalized_requests.append(BatchRequest(
                    prompt=r.get("prompt", ""),
                    system_instruction=r.get("system") or r.get("system_instruction"),
                    generation_config=r.get("generation_config") or generation_config,
                    metadata=r.get("metadata", {}),
                ))
            else:
                normalized_requests.append(r)

        # Estimate cost
        cost_estimate = self.estimate_cost(normalized_requests, model)

        job_id = f"batch_{uuid.uuid4().hex[:12]}"
        job_name = job_name or f"vivid-batch-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        logger.info(
            f"[BATCH] Creating job: {job_name} | model={model} | "
            f"requests={len(normalized_requests)} | "
            f"estimated_cost=${cost_estimate['batch_cost_usd']:.4f} "
            f"(saving ${cost_estimate['savings_usd']:.4f})"
        )

        try:
            client = self._get_client()

            # Format requests for Batch API
            batch_requests = []
            for req in normalized_requests:
                content = {
                    "contents": [{
                        "parts": [{"text": req.prompt}],
                        "role": "user"
                    }]
                }
                if req.system_instruction:
                    content["system_instruction"] = {
                        "parts": [{"text": req.system_instruction}]
                    }
                if req.generation_config:
                    content["generation_config"] = req.generation_config

                batch_requests.append(content)

            # Submit batch job
            batch_job = client.batches.create(
                model=f"models/{model}",
                src=batch_requests,
                config={
                    "display_name": job_name,
                },
            )

            # Create tracking object
            job = BatchJob(
                job_id=job_id,
                name=batch_job.name,
                model=model,
                status=BatchJobStatus.PENDING,
                total_requests=len(normalized_requests),
                estimated_cost=cost_estimate["batch_cost_usd"],
                metadata={
                    "cost_estimate": cost_estimate,
                    "created_by": "GeminiBatchService",
                    "sdk_job_name": batch_job.name,
                },
            )

            self._jobs[job_id] = job

            logger.info(f"[BATCH] Job created: {job_id} -> SDK job: {batch_job.name}")
            return job

        except Exception as e:
            logger.error(f"[BATCH] Failed to create job: {e}")
            raise

    async def get_job_status(self, job_id: str) -> BatchJob:
        """Get current status of a batch job.

        Args:
            job_id: Job ID returned from create_batch_job

        Returns:
            Updated BatchJob with current status
        """
        if job_id not in self._jobs:
            raise ValueError(f"Job not found: {job_id}")

        job = self._jobs[job_id]

        try:
            client = self._get_client()
            sdk_job = client.batches.get(job.name)

            # Update status based on SDK response
            if sdk_job.state.name == "JOB_STATE_SUCCEEDED":
                job.status = BatchJobStatus.COMPLETED
                job.completed_at = datetime.utcnow()
            elif sdk_job.state.name == "JOB_STATE_FAILED":
                job.status = BatchJobStatus.FAILED
            elif sdk_job.state.name == "JOB_STATE_CANCELLED":
                job.status = BatchJobStatus.CANCELLED
            elif sdk_job.state.name in ("JOB_STATE_RUNNING", "JOB_STATE_PENDING"):
                job.status = BatchJobStatus.RUNNING

            logger.debug(f"[BATCH] Job {job_id} status: {job.status}")
            return job

        except Exception as e:
            logger.error(f"[BATCH] Failed to get job status: {e}")
            raise

    async def wait_for_completion(
        self,
        job_id: str,
        poll_interval: int = POLL_INTERVAL_SECONDS,
        max_wait_hours: int = MAX_WAIT_HOURS,
        progress_callback: Optional[Callable[[BatchJob], None]] = None,
    ) -> BatchJob:
        """Wait for batch job to complete.

        Args:
            job_id: Job ID
            poll_interval: Seconds between status checks
            max_wait_hours: Maximum hours to wait
            progress_callback: Optional callback for progress updates

        Returns:
            Completed BatchJob with results
        """
        max_wait_seconds = max_wait_hours * 3600
        start_time = time.time()

        while True:
            job = await self.get_job_status(job_id)

            if progress_callback:
                progress_callback(job)

            if job.status in (BatchJobStatus.COMPLETED, BatchJobStatus.FAILED, BatchJobStatus.CANCELLED):
                break

            elapsed = time.time() - start_time
            if elapsed > max_wait_seconds:
                logger.warning(f"[BATCH] Job {job_id} timed out after {max_wait_hours}h")
                break

            logger.debug(f"[BATCH] Waiting for job {job_id}... (elapsed: {elapsed/60:.1f}m)")
            await asyncio.sleep(poll_interval)

        # Fetch results if completed
        if job.status == BatchJobStatus.COMPLETED:
            job = await self.get_batch_results(job_id)

        return job

    async def get_batch_results(self, job_id: str) -> BatchJob:
        """Get results from a completed batch job.

        Args:
            job_id: Job ID

        Returns:
            BatchJob with results populated
        """
        if job_id not in self._jobs:
            raise ValueError(f"Job not found: {job_id}")

        job = self._jobs[job_id]

        try:
            client = self._get_client()

            # Get batch job results
            sdk_job = client.batches.get(job.name)

            if sdk_job.state.name != "JOB_STATE_SUCCEEDED":
                logger.warning(f"[BATCH] Job {job_id} not completed: {sdk_job.state.name}")
                return job

            # Parse results
            results: List[BatchResponse] = []
            total_input_tokens = 0
            total_output_tokens = 0

            # Results are in the response
            for i, response in enumerate(sdk_job.response.responses or []):
                request_id = f"req_{i}"

                try:
                    content = response.candidates[0].content.parts[0].text if response.candidates else None
                    usage = {
                        "input": getattr(response.usage_metadata, 'prompt_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
                        "output": getattr(response.usage_metadata, 'candidates_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
                    }
                    total_input_tokens += usage["input"]
                    total_output_tokens += usage["output"]

                    results.append(BatchResponse(
                        request_id=request_id,
                        success=True,
                        content=content,
                        usage=usage,
                    ))
                    job.completed_requests += 1

                except Exception as e:
                    results.append(BatchResponse(
                        request_id=request_id,
                        success=False,
                        error=str(e),
                    ))
                    job.failed_requests += 1

            job.results = results

            # Calculate actual cost
            pricing = BATCH_PRICING_PER_1M_TOKENS.get(job.model, BATCH_PRICING_PER_1M_TOKENS[DEFAULT_BATCH_MODEL])
            job.actual_cost = (total_input_tokens / 1_000_000) * pricing["input"] + \
                             (total_output_tokens / 1_000_000) * pricing["output"]

            logger.info(
                f"[BATCH] Job {job_id} results: "
                f"completed={job.completed_requests}/{job.total_requests} | "
                f"failed={job.failed_requests} | "
                f"tokens={total_input_tokens}+{total_output_tokens} | "
                f"cost=${job.actual_cost:.4f}"
            )

            return job

        except Exception as e:
            logger.error(f"[BATCH] Failed to get results: {e}")
            raise

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running batch job.

        Args:
            job_id: Job ID

        Returns:
            True if cancelled successfully
        """
        if job_id not in self._jobs:
            raise ValueError(f"Job not found: {job_id}")

        job = self._jobs[job_id]

        try:
            client = self._get_client()
            client.batches.cancel(job.name)
            job.status = BatchJobStatus.CANCELLED
            logger.info(f"[BATCH] Job {job_id} cancelled")
            return True
        except Exception as e:
            logger.error(f"[BATCH] Failed to cancel job: {e}")
            return False

    def list_jobs(self, status: Optional[BatchJobStatus] = None) -> List[BatchJob]:
        """List all tracked batch jobs.

        Args:
            status: Optional filter by status

        Returns:
            List of BatchJob objects
        """
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return jobs


# =============================================================================
# Singleton Instance
# =============================================================================

_batch_service: Optional[GeminiBatchService] = None


def get_batch_service(api_key: Optional[str] = None) -> GeminiBatchService:
    """Get singleton batch service instance.

    Args:
        api_key: Optional API key override

    Returns:
        GeminiBatchService instance
    """
    global _batch_service
    if _batch_service is None or api_key:
        _batch_service = GeminiBatchService(api_key=api_key)
    return _batch_service


# =============================================================================
# Convenience Functions
# =============================================================================

async def batch_generate(
    prompts: List[str],
    system_instruction: Optional[str] = None,
    model: str = DEFAULT_BATCH_MODEL,
    wait: bool = True,
) -> List[str]:
    """Simple batch generation helper.

    Args:
        prompts: List of prompts to process
        system_instruction: Optional system instruction for all prompts
        model: Model to use
        wait: If True, wait for completion

    Returns:
        List of generated texts (empty strings for failures)

    Example:
        results = await batch_generate(
            prompts=["프롬프트 1", "프롬프트 2", "프롬프트 3"],
            system_instruction="당신은 전문 작가입니다.",
            model="gemini-2.5-flash",
        )
    """
    service = get_batch_service()

    requests = [
        BatchRequest(prompt=p, system_instruction=system_instruction)
        for p in prompts
    ]

    job = await service.create_batch_job(requests, model=model)

    if wait:
        job = await service.wait_for_completion(job.job_id)
        return [r.content or "" for r in job.results]

    return []


async def batch_evaluate_rag(
    samples: List[Dict[str, Any]],
    evaluation_prompt_template: str,
    model: str = DEFAULT_BATCH_MODEL,
) -> List[Dict[str, Any]]:
    """Batch evaluate RAG samples (50% cost savings).

    Args:
        samples: List of RAG samples with 'question', 'answer', 'contexts'
        evaluation_prompt_template: Template with {question}, {answer}, {contexts} placeholders
        model: Model to use

    Returns:
        List of evaluation results

    Example:
        results = await batch_evaluate_rag(
            samples=[
                {"question": "Q1", "answer": "A1", "contexts": ["C1"]},
                {"question": "Q2", "answer": "A2", "contexts": ["C2"]},
            ],
            evaluation_prompt_template=\"\"\"
                Question: {question}
                Answer: {answer}
                Contexts: {contexts}

                Evaluate faithfulness (0-1) and relevancy (0-1).
                Output JSON: {{"faithfulness": 0.X, "relevancy": 0.X}}
            \"\"\",
        )
    """
    service = get_batch_service()

    requests = []
    for sample in samples:
        prompt = evaluation_prompt_template.format(
            question=sample.get("question", ""),
            answer=sample.get("answer", ""),
            contexts="\n".join(sample.get("contexts", [])),
        )
        requests.append(BatchRequest(
            prompt=prompt,
            metadata={"sample_id": sample.get("id", str(uuid.uuid4())[:8])},
        ))

    job = await service.create_batch_job(
        requests,
        model=model,
        job_name=f"rag-eval-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
    )

    job = await service.wait_for_completion(job.job_id)

    # Parse results
    results = []
    for i, response in enumerate(job.results):
        sample_result = {
            "sample_id": samples[i].get("id") if i < len(samples) else None,
            "success": response.success,
        }

        if response.success and response.content:
            try:
                # Try to parse JSON from response
                parsed = json.loads(response.content)
                sample_result.update(parsed)
            except json.JSONDecodeError:
                sample_result["raw_response"] = response.content
        else:
            sample_result["error"] = response.error

        results.append(sample_result)

    return results
