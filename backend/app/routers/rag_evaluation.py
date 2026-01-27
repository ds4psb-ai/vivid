"""
RAG Evaluation Router - Quality assessment endpoints

Provides:
- POST /rag-eval/evaluate - Single sample evaluation
- POST /rag-eval/evaluate/batch - Batch evaluation (Gemini 50% cost)
- GET /rag-eval/report - Latest evaluation report
- GET /rag-eval/golden-dataset - View golden dataset
- POST /rag-eval/golden-dataset - Add golden dataset item (Admin)
- POST /rag-eval/run-golden - Run full golden dataset evaluation (Admin)

2026 Best Practices:
- Ragas v0.4 integration for automated metrics
- Gemini Batch API for 50% cost reduction
- Langfuse integration for observability
"""

import logging
from datetime import datetime
from typing import Any, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import require_admin
from app.rag.evaluation import (
    RAGEvaluationPipeline,
    GoldenDatasetManager,
    ProductionRAGMonitor,
    EvaluationSample,
    EvaluationResult,
    EvaluationReport,
    EvaluationMetric,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag-eval", tags=["rag-evaluation"])


# =============================================================================
# Request/Response Models
# =============================================================================


class EvaluateSingleRequest(BaseModel):
    """Single sample evaluation request."""
    question: str = Field(..., min_length=1, max_length=2000, description="Question/query")
    answer: str = Field(..., min_length=1, max_length=10000, description="Generated answer")
    contexts: list[str] = Field(..., min_length=1, max_length=20, description="Retrieved contexts")
    ground_truth: Optional[str] = Field(None, description="Expected answer (for reference)")
    sample_id: Optional[str] = Field(None, description="Optional sample identifier")


class EvaluateSingleResponse(BaseModel):
    """Single evaluation result."""
    sample_id: str
    question: str
    scores: dict[str, float]
    timestamp: str
    latency_ms: float
    metadata: dict[str, Any]


class EvaluateBatchRequest(BaseModel):
    """Batch evaluation request."""
    samples: list[EvaluateSingleRequest] = Field(..., min_length=1, max_length=1000)
    use_gemini_batch: bool = Field(True, description="Use Gemini Batch API (50% cost)")
    wait_for_results: bool = Field(True, description="Wait for batch completion")


class EvaluateBatchResponse(BaseModel):
    """Batch evaluation result."""
    total_samples: int
    avg_scores: dict[str, float]
    min_scores: dict[str, float]
    max_scores: dict[str, float]
    duration_seconds: float
    metadata: dict[str, Any]


class ReportResponse(BaseModel):
    """Latest evaluation report."""
    total_samples: int
    avg_scores: dict[str, float]
    min_scores: dict[str, float]
    max_scores: dict[str, float]
    timestamp: str
    duration_seconds: float
    metadata: dict[str, Any]
    summary: str


class GoldenDatasetItem(BaseModel):
    """Golden dataset item."""
    query: str = Field(..., min_length=1, description="Test query")
    ground_truth: Optional[str] = Field(None, description="Expected answer")
    expected_contexts: list[str] = Field(default_factory=list, description="Expected context refs")
    difficulty: str = Field("medium", description="easy/medium/hard")
    category: str = Field("general", description="Test category")
    dimension: Optional[str] = Field(None, description="Dimension code (AD, 1D, etc.)")
    auteur_key: Optional[str] = Field(None, description="Auteur key for auteur tests")


class GoldenDatasetResponse(BaseModel):
    """Golden dataset listing."""
    total_items: int
    items: list[GoldenDatasetItem]
    categories: list[str]


class RunGoldenRequest(BaseModel):
    """Run golden dataset evaluation request."""
    use_gemini_batch: bool = Field(True, description="Use Gemini Batch API")
    send_to_langfuse: bool = Field(True, description="Send results to Langfuse")
    category_filter: Optional[str] = Field(None, description="Filter by category")


class RunGoldenResponse(BaseModel):
    """Golden dataset evaluation result."""
    status: str
    job_id: Optional[str]
    message: str


# =============================================================================
# Module-level State
# =============================================================================


_pipeline: Optional[RAGEvaluationPipeline] = None
_monitor: Optional[ProductionRAGMonitor] = None
_latest_report: Optional[EvaluationReport] = None


def get_pipeline() -> RAGEvaluationPipeline:
    """Get or create evaluation pipeline singleton."""
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGEvaluationPipeline(
            llm_model=settings.RAG_EVAL_LLM_MODEL,
        )
    return _pipeline


def get_monitor() -> ProductionRAGMonitor:
    """Get or create production monitor singleton."""
    global _monitor
    if _monitor is None:
        _monitor = ProductionRAGMonitor(
            pipeline=get_pipeline(),
            sample_rate=settings.RAG_EVAL_SAMPLE_RATE,
            alert_threshold=settings.RAG_EVAL_ALERT_THRESHOLD,
        )
    return _monitor


def get_golden_manager() -> GoldenDatasetManager:
    """Get golden dataset manager."""
    return GoldenDatasetManager(
        dataset_path=settings.RAG_EVAL_GOLDEN_DATASET_PATH,
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/evaluate", response_model=EvaluateSingleResponse)
async def evaluate_single(body: EvaluateSingleRequest):
    """
    Evaluate a single RAG response.

    Returns scores for:
    - faithfulness: Is the answer grounded in contexts?
    - answer_relevancy: Does the answer address the question?
    - context_precision: Are retrieved contexts relevant?

    Example:
        POST /rag-eval/evaluate
        {
            "question": "봉준호 감독의 영화적 특징은?",
            "answer": "봉준호는 비선형 서사와 계급 갈등을 주제로...",
            "contexts": ["봉준호는 기생충에서...", "봉준호의 초기작..."]
        }
    """
    if not settings.RAG_EVAL_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="RAG evaluation is disabled. Set RAG_EVAL_ENABLED=True",
        )

    pipeline = get_pipeline()

    result = await pipeline.evaluate_single(
        question=body.question,
        answer=body.answer,
        contexts=body.contexts,
        ground_truth=body.ground_truth,
        sample_id=body.sample_id,
    )

    return EvaluateSingleResponse(
        sample_id=result.sample_id,
        question=result.question,
        scores=result.scores,
        timestamp=result.timestamp.isoformat(),
        latency_ms=result.latency_ms,
        metadata=result.metadata,
    )


@router.post("/evaluate/batch", response_model=EvaluateBatchResponse)
async def evaluate_batch(body: EvaluateBatchRequest):
    """
    Evaluate multiple RAG responses in batch.

    With use_gemini_batch=True (default), uses Gemini Batch API for 50% cost savings.
    Batch API has 24h SLA but typically completes much faster.

    Example:
        POST /rag-eval/evaluate/batch
        {
            "samples": [
                {"question": "...", "answer": "...", "contexts": ["..."]},
                ...
            ],
            "use_gemini_batch": true
        }
    """
    if not settings.RAG_EVAL_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="RAG evaluation is disabled. Set RAG_EVAL_ENABLED=True",
        )

    pipeline = get_pipeline()

    # Convert request samples to EvaluationSample objects
    samples = [
        EvaluationSample(
            question=s.question,
            answer=s.answer,
            contexts=s.contexts,
            ground_truth=s.ground_truth,
        )
        for s in body.samples
    ]

    if body.use_gemini_batch:
        report = await pipeline.evaluate_batch_with_gemini(
            samples=samples,
            model=settings.RAG_EVAL_BATCH_MODEL,
            wait_for_results=body.wait_for_results,
        )
    else:
        report = await pipeline.evaluate_batch(
            samples=samples,
            concurrency=5,
        )

    # Store latest report
    global _latest_report
    _latest_report = report

    return EvaluateBatchResponse(
        total_samples=report.total_samples,
        avg_scores=report.avg_scores,
        min_scores=report.min_scores,
        max_scores=report.max_scores,
        duration_seconds=report.duration_seconds,
        metadata=report.metadata,
    )


@router.get("/report", response_model=ReportResponse)
async def get_report():
    """
    Get the latest evaluation report.

    Returns cached report from the most recent batch evaluation
    or production monitor evaluation.
    """
    global _latest_report

    # Try monitor's latest report first
    monitor = get_monitor()
    report = monitor.get_latest_report() or _latest_report

    if not report:
        raise HTTPException(
            status_code=404,
            detail="No evaluation report available. Run an evaluation first.",
        )

    return ReportResponse(
        total_samples=report.total_samples,
        avg_scores=report.avg_scores,
        min_scores=report.min_scores,
        max_scores=report.max_scores,
        timestamp=report.timestamp.isoformat(),
        duration_seconds=report.duration_seconds,
        metadata=report.metadata,
        summary=report.summary(),
    )


@router.get("/golden-dataset", response_model=GoldenDatasetResponse)
async def get_golden_dataset():
    """
    Get the current golden dataset.

    Returns all test cases from the golden dataset YAML file.
    """
    manager = get_golden_manager()
    samples = manager.load()

    # Extract unique categories
    categories = list(set(
        s.metadata.get("category", "general")
        for s in samples
    ))

    items = [
        GoldenDatasetItem(
            query=s.question,
            ground_truth=s.ground_truth,
            expected_contexts=s.contexts,
            difficulty=s.metadata.get("difficulty", "medium"),
            category=s.metadata.get("category", "general"),
            dimension=s.metadata.get("dimension"),
            auteur_key=s.metadata.get("auteur_key"),
        )
        for s in samples
    ]

    return GoldenDatasetResponse(
        total_items=len(items),
        items=items,
        categories=categories,
    )


@router.post("/golden-dataset", dependencies=[Depends(require_admin)])
async def add_golden_dataset_item(item: GoldenDatasetItem):
    """
    Add an item to the golden dataset.

    Requires admin privileges.

    Example:
        POST /rag-eval/golden-dataset
        {
            "query": "봉준호 스타일의 특징",
            "ground_truth": "비선형 서사, 블랙코미디, 계급갈등...",
            "difficulty": "medium",
            "category": "auteur_technique",
            "dimension": "AD",
            "auteur_key": "bong"
        }
    """
    manager = get_golden_manager()

    # Load existing samples
    existing = manager.load()

    # Create new sample
    new_sample = EvaluationSample(
        question=item.query,
        answer="",  # Filled during evaluation
        contexts=item.expected_contexts,
        ground_truth=item.ground_truth,
        metadata={
            "difficulty": item.difficulty,
            "category": item.category,
            "dimension": item.dimension,
            "auteur_key": item.auteur_key,
        },
    )

    # Append and save
    existing.append(new_sample)
    manager.save(existing)

    return {
        "status": "success",
        "message": f"Added item to golden dataset. Total items: {len(existing)}",
    }


@router.post("/run-golden", response_model=RunGoldenResponse, dependencies=[Depends(require_admin)])
async def run_golden_evaluation(
    body: RunGoldenRequest,
    background_tasks: BackgroundTasks,
):
    """
    Run full golden dataset evaluation.

    Requires admin privileges.
    Runs in background and stores results for /report endpoint.

    Example:
        POST /rag-eval/run-golden
        {
            "use_gemini_batch": true,
            "send_to_langfuse": true,
            "category_filter": "auteur_technique"
        }
    """
    if not settings.RAG_EVAL_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="RAG evaluation is disabled. Set RAG_EVAL_ENABLED=True",
        )

    manager = get_golden_manager()
    samples = manager.load()

    if not samples:
        raise HTTPException(
            status_code=404,
            detail="Golden dataset is empty. Add test cases first.",
        )

    # Filter by category if specified
    if body.category_filter:
        samples = [
            s for s in samples
            if s.metadata.get("category") == body.category_filter
        ]
        if not samples:
            raise HTTPException(
                status_code=404,
                detail=f"No samples found for category: {body.category_filter}",
            )

    # Run evaluation in background
    async def _run_evaluation():
        global _latest_report
        try:
            pipeline = get_pipeline()

            # First, we need to generate answers for each sample using RAG
            from app.rag.hybrid_rag import hybrid_query

            filled_samples = []
            for sample in samples:
                try:
                    # Query RAG to get answer and contexts
                    rag_result = await hybrid_query(
                        query=sample.question,
                        auteur_key=sample.metadata.get("auteur_key"),
                        dimension=sample.metadata.get("dimension"),
                    )

                    # Create filled sample
                    filled = EvaluationSample(
                        question=sample.question,
                        answer=rag_result.answer,
                        contexts=[
                            src.excerpt if hasattr(src, 'excerpt') else str(src)
                            for src in (rag_result.notebooklm_sources + rag_result.vertex_sources)[:5]
                        ] or sample.contexts,
                        ground_truth=sample.ground_truth,
                        metadata=sample.metadata,
                    )
                    filled_samples.append(filled)
                except Exception as e:
                    logger.warning(f"[RAG-EVAL] Failed to get RAG answer: {e}")
                    # Use original sample with empty answer
                    filled_samples.append(sample)

            # Run batch evaluation
            if body.use_gemini_batch:
                report = await pipeline.evaluate_batch_with_gemini(
                    samples=filled_samples,
                    model=settings.RAG_EVAL_BATCH_MODEL,
                    wait_for_results=True,
                )
            else:
                report = await pipeline.evaluate_batch(
                    samples=filled_samples,
                    concurrency=5,
                )

            _latest_report = report

            # Send to Langfuse if enabled
            if body.send_to_langfuse:
                await _send_report_to_langfuse(report)

            logger.info(
                f"[RAG-EVAL] Golden dataset evaluation complete | "
                f"samples={report.total_samples} | "
                f"avg_faithfulness={report.avg_scores.get('faithfulness', 0):.4f}"
            )

        except Exception as e:
            logger.error(f"[RAG-EVAL] Golden evaluation failed: {e}")

    background_tasks.add_task(_run_evaluation)

    return RunGoldenResponse(
        status="started",
        job_id=f"golden-eval-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        message=f"Evaluation started for {len(samples)} samples. Check /report for results.",
    )


# =============================================================================
# Langfuse Integration
# =============================================================================


async def _send_report_to_langfuse(report: EvaluationReport):
    """Send evaluation report to Langfuse for observability."""
    try:
        from langfuse import Langfuse

        if not settings.LANGFUSE_ENABLED:
            logger.debug("[RAG-EVAL] Langfuse disabled, skipping upload")
            return

        langfuse = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY.get_secret_value(),
            host=settings.LANGFUSE_HOST,
        )

        # Create a trace for the evaluation run
        trace = langfuse.trace(
            name="rag-evaluation-run",
            metadata={
                "total_samples": report.total_samples,
                "duration_seconds": report.duration_seconds,
                **report.metadata,
            },
        )

        # Score the trace with average metrics
        for metric, score in report.avg_scores.items():
            trace.score(
                name=f"avg_{metric}",
                value=score,
                comment=f"Average {metric} score across {report.total_samples} samples",
            )

        # Upload individual results to dataset
        dataset_name = settings.RAG_EVAL_LANGFUSE_DATASET

        # Create or get dataset
        try:
            dataset = langfuse.get_dataset(dataset_name)
        except Exception:
            dataset = langfuse.create_dataset(
                name=dataset_name,
                description="RAG Quality Evaluation Dataset",
            )

        # Add each result as a dataset item
        for result in report.results:
            langfuse.create_dataset_item(
                dataset_name=dataset_name,
                input={"question": result.question},
                expected_output=None,  # Will be set by ground truth if available
                metadata={
                    "scores": result.scores,
                    "sample_id": result.sample_id,
                    **result.metadata,
                },
            )

        langfuse.flush()
        logger.info(f"[RAG-EVAL] Sent {len(report.results)} results to Langfuse")

    except ImportError:
        logger.warning("[RAG-EVAL] Langfuse not installed, skipping upload")
    except Exception as e:
        logger.error(f"[RAG-EVAL] Failed to send to Langfuse: {e}")


# =============================================================================
# Production Monitoring Hook (for hybrid_rag.py)
# =============================================================================


async def record_evaluation_sample(
    question: str,
    answer: str,
    contexts: list[str],
) -> None:
    """
    Record a sample for production monitoring.

    Called from hybrid_rag.py when RAG_EVAL_ENABLED=True.
    Samples are collected and evaluated periodically.
    """
    if not settings.RAG_EVAL_ENABLED:
        return

    monitor = get_monitor()
    if monitor.should_sample():
        await monitor.record_sample(question, answer, contexts)
