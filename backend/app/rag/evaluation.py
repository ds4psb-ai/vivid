"""
RAG Evaluation Pipeline (2026 Best Practices)
=============================================

Comprehensive RAG quality evaluation using Ragas framework:
- Faithfulness: Is the answer grounded in the retrieved context?
- Answer Relevancy: Is the answer relevant to the question?
- Context Precision: Are retrieved chunks relevant?
- Context Recall: Did we retrieve all relevant information?

Integrations:
- Ragas for automated evaluation
- Langfuse for observability
- BigQuery for analytics (optional)

References:
- https://docs.ragas.io/
- Tavily Research (2026-01-16)
- Context7 MCP: /vibrantlabsai/ragas
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

from pydantic import BaseModel, Field

# Batch API for 50% cost reduction
from app.services.gemini_batch_service import (
    get_batch_service,
    BatchRequest,
    BatchJobStatus,
    DEFAULT_BATCH_MODEL,
)

logger = logging.getLogger(__name__)


class EvaluationMetric(str, Enum):
    """Available RAG evaluation metrics."""
    FAITHFULNESS = "faithfulness"
    ANSWER_RELEVANCY = "answer_relevancy"
    CONTEXT_PRECISION = "context_precision"
    CONTEXT_RECALL = "context_recall"
    CONTEXT_RELEVANCY = "context_relevancy"
    ANSWER_CORRECTNESS = "answer_correctness"


@dataclass
class EvaluationSample:
    """Single evaluation sample."""
    question: str
    answer: str
    contexts: list[str]
    ground_truth: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result of a single evaluation."""
    sample_id: str
    question: str
    scores: dict[str, float]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    latency_ms: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result


@dataclass
class EvaluationReport:
    """Aggregated evaluation report."""
    total_samples: int
    avg_scores: dict[str, float]
    min_scores: dict[str, float]
    max_scores: dict[str, float]
    results: list[EvaluationResult]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_seconds: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "total_samples": self.total_samples,
            "avg_scores": self.avg_scores,
            "min_scores": self.min_scores,
            "max_scores": self.max_scores,
            "results": [r.to_dict() for r in self.results],
            "timestamp": self.timestamp.isoformat(),
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
        }

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"RAG Evaluation Report ({self.timestamp.strftime('%Y-%m-%d %H:%M')})",
            f"Total Samples: {self.total_samples}",
            f"Duration: {self.duration_seconds:.2f}s",
            "",
            "Average Scores:",
        ]
        for metric, score in self.avg_scores.items():
            status = "✅" if score >= 0.7 else "⚠️" if score >= 0.5 else "❌"
            lines.append(f"  {status} {metric}: {score:.4f}")

        return "\n".join(lines)


class RAGEvaluationPipeline:
    """
    2026 Best Practice: RAG Quality Evaluation Pipeline

    Usage:
        pipeline = RAGEvaluationPipeline()
        result = await pipeline.evaluate_single(
            question="강주노 감독의 영화적 특징은?",
            answer="강주노는 비선형 서사와 계급 갈등을 주제로...",
            contexts=["강주노는 기생충에서...", "강주노의 초기작..."],
        )

        # Batch evaluation with golden dataset
        report = await pipeline.evaluate_batch(samples)
    """

    def __init__(
        self,
        metrics: Optional[list[EvaluationMetric]] = None,
        llm_model: str = "gpt-4o-mini",
        embedding_model: str = "text-embedding-3-small",
    ):
        """
        Initialize RAG Evaluation Pipeline.

        Args:
            metrics: List of metrics to evaluate (default: all core metrics)
            llm_model: LLM model for evaluation (OpenAI or Gemini)
            embedding_model: Embedding model for semantic similarity
        """
        self.metric_types = metrics or [
            EvaluationMetric.FAITHFULNESS,
            EvaluationMetric.ANSWER_RELEVANCY,
            EvaluationMetric.CONTEXT_PRECISION,
        ]
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self._ragas_metrics = None
        self._evaluator_llm = None

    def _initialize_ragas(self):
        """Lazy initialization of Ragas components."""
        if self._ragas_metrics is not None:
            return

        try:
            from ragas.metrics import (
                Faithfulness,
                AnswerRelevancy,
                ContextPrecision,
                ContextRecall,
            )
            from ragas.llms import llm_factory
            from openai import OpenAI

            # Initialize LLM using Ragas v0.4 factory with OpenAI client
            client = OpenAI()
            self._evaluator_llm = llm_factory(self.llm_model, client=client)

            # Map metrics to Ragas metric instances (v0.4: no LLM in constructor)
            metric_map = {
                EvaluationMetric.FAITHFULNESS: Faithfulness(),
                EvaluationMetric.ANSWER_RELEVANCY: AnswerRelevancy(),
                EvaluationMetric.CONTEXT_PRECISION: ContextPrecision(),
                EvaluationMetric.CONTEXT_RECALL: ContextRecall(),
            }

            self._ragas_metrics = [
                metric_map[m] for m in self.metric_types
                if m in metric_map
            ]

            logger.info(f"Ragas initialized with metrics: {[m.value for m in self.metric_types]}")

        except ImportError as e:
            logger.warning(f"Ragas not installed: {e}. Using fallback evaluation.")
            self._ragas_metrics = []
        except Exception as e:
            # Catch OpenAI API key errors and other initialization failures
            logger.warning(f"Ragas initialization failed: {e}. Using fallback evaluation.")
            self._ragas_metrics = []

    async def evaluate_single(
        self,
        question: str,
        answer: str,
        contexts: list[str],
        ground_truth: Optional[str] = None,
        sample_id: Optional[str] = None,
    ) -> EvaluationResult:
        """
        Evaluate a single RAG response.

        Args:
            question: User query
            answer: Generated answer
            contexts: Retrieved context chunks
            ground_truth: Optional expected answer for reference metrics
            sample_id: Optional identifier for the sample

        Returns:
            EvaluationResult with scores for each metric
        """
        start_time = time.time()
        sample_id = sample_id or f"eval_{int(time.time() * 1000)}"

        self._initialize_ragas()

        if not self._ragas_metrics:
            # Fallback: basic heuristic evaluation
            scores = await self._fallback_evaluation(question, answer, contexts)
        else:
            scores = await self._ragas_evaluation(question, answer, contexts, ground_truth)

        latency_ms = (time.time() - start_time) * 1000

        return EvaluationResult(
            sample_id=sample_id,
            question=question,
            scores=scores,
            latency_ms=latency_ms,
            metadata={
                "answer_length": len(answer),
                "context_count": len(contexts),
                "has_ground_truth": ground_truth is not None,
            }
        )

    async def _ragas_evaluation(
        self,
        question: str,
        answer: str,
        contexts: list[str],
        ground_truth: Optional[str] = None,
    ) -> dict[str, float]:
        """Evaluate using Ragas framework (v0.4 API)."""
        try:
            from ragas import evaluate, EvaluationDataset, SingleTurnSample

            # Prepare dataset using v0.4 API
            sample = SingleTurnSample(
                user_input=question,
                response=answer,
                retrieved_contexts=contexts,
                reference=ground_truth,
            )
            dataset = EvaluationDataset(samples=[sample])

            # Run evaluation with v0.4 API (llm parameter required)
            result = evaluate(
                dataset=dataset,
                metrics=self._ragas_metrics,
                llm=self._evaluator_llm,
            )

            # Extract scores from v0.4 result format
            scores = {}
            for metric in self.metric_types:
                metric_name = metric.value
                if metric_name in result:
                    score_obj = result[metric_name]
                    # v0.4: handle MetricResult object or direct values
                    if hasattr(score_obj, 'score'):
                        scores[metric_name] = float(score_obj.score)
                    elif hasattr(score_obj, 'item'):
                        scores[metric_name] = float(score_obj.item())
                    else:
                        scores[metric_name] = float(score_obj)

            return scores

        except Exception as e:
            logger.error(f"Ragas evaluation failed: {e}")
            return await self._fallback_evaluation(question, answer, contexts)

    async def _fallback_evaluation(
        self,
        question: str,
        answer: str,
        contexts: list[str],
    ) -> dict[str, float]:
        """
        Fallback heuristic evaluation when Ragas is not available.

        Uses simple heuristics:
        - Faithfulness: Word overlap between answer and contexts
        - Relevancy: Keyword overlap between question and answer
        - Context Precision: Non-empty context ratio
        """
        scores = {}

        # Faithfulness: word overlap with contexts
        answer_words = set(answer.lower().split())
        context_words = set()
        for ctx in contexts:
            context_words.update(ctx.lower().split())

        if answer_words and context_words:
            overlap = len(answer_words & context_words) / len(answer_words)
            scores["faithfulness"] = min(overlap * 1.5, 1.0)  # Scale up slightly
        else:
            scores["faithfulness"] = 0.0

        # Answer Relevancy: keyword overlap with question
        question_words = set(question.lower().split())
        if question_words and answer_words:
            relevancy = len(question_words & answer_words) / len(question_words)
            scores["answer_relevancy"] = min(relevancy * 2.0, 1.0)
        else:
            scores["answer_relevancy"] = 0.0

        # Context Precision: ratio of non-empty contexts
        non_empty = sum(1 for ctx in contexts if ctx.strip())
        scores["context_precision"] = non_empty / max(len(contexts), 1)

        return scores

    async def evaluate_batch(
        self,
        samples: list[EvaluationSample],
        concurrency: int = 5,
    ) -> EvaluationReport:
        """
        Evaluate multiple samples in batch.

        Args:
            samples: List of EvaluationSample objects
            concurrency: Max concurrent evaluations

        Returns:
            EvaluationReport with aggregated statistics
        """
        start_time = time.time()
        semaphore = asyncio.Semaphore(concurrency)

        async def evaluate_with_limit(idx: int, sample: EvaluationSample):
            async with semaphore:
                return await self.evaluate_single(
                    question=sample.question,
                    answer=sample.answer,
                    contexts=sample.contexts,
                    ground_truth=sample.ground_truth,
                    sample_id=f"batch_{idx}",
                )

        # Run evaluations concurrently
        tasks = [
            evaluate_with_limit(idx, sample)
            for idx, sample in enumerate(samples)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = [r for r in results if isinstance(r, EvaluationResult)]
        failed_count = len(results) - len(valid_results)

        if failed_count > 0:
            logger.warning(f"{failed_count} evaluations failed")

        # Aggregate scores
        avg_scores, min_scores, max_scores = self._aggregate_scores(valid_results)

        duration = time.time() - start_time

        return EvaluationReport(
            total_samples=len(samples),
            avg_scores=avg_scores,
            min_scores=min_scores,
            max_scores=max_scores,
            results=valid_results,
            duration_seconds=duration,
            metadata={
                "failed_count": failed_count,
                "concurrency": concurrency,
                "metrics": [m.value for m in self.metric_types],
            }
        )

    def _aggregate_scores(
        self,
        results: list[EvaluationResult],
    ) -> tuple[dict, dict, dict]:
        """Aggregate scores from multiple results."""
        if not results:
            return {}, {}, {}

        # Collect all scores by metric
        scores_by_metric: dict[str, list[float]] = {}
        for result in results:
            for metric, score in result.scores.items():
                if metric not in scores_by_metric:
                    scores_by_metric[metric] = []
                scores_by_metric[metric].append(score)

        # Calculate aggregates
        avg_scores = {
            metric: sum(scores) / len(scores)
            for metric, scores in scores_by_metric.items()
        }
        min_scores = {
            metric: min(scores)
            for metric, scores in scores_by_metric.items()
        }
        max_scores = {
            metric: max(scores)
            for metric, scores in scores_by_metric.items()
        }

        return avg_scores, min_scores, max_scores

    # =========================================================================
    # Batch API Methods (50% Cost Reduction)
    # =========================================================================

    async def evaluate_batch_with_gemini(
        self,
        samples: list[EvaluationSample],
        model: str = DEFAULT_BATCH_MODEL,
        wait_for_results: bool = True,
    ) -> EvaluationReport:
        """
        Batch evaluation using Gemini Batch API (50% cost savings).

        Ideal for:
        - Large-scale evaluation (>10 samples)
        - Non-real-time quality assessment
        - CI/CD pipeline integration
        - Golden dataset evaluation

        Args:
            samples: List of EvaluationSample objects
            model: Gemini model to use (default: gemini-2.5-flash)
            wait_for_results: If True, wait for batch job completion (up to 24h)

        Returns:
            EvaluationReport with results from batch processing

        Note:
            Batch API has 24h SLA but typically completes much faster.
            Cost is 50% of standard API pricing.
        """
        start_time = time.time()
        batch_service = get_batch_service()

        # Build evaluation prompts
        batch_requests: list[BatchRequest] = []
        for idx, sample in enumerate(samples):
            prompt = self._build_evaluation_prompt(sample)
            batch_requests.append(BatchRequest(
                prompt=prompt,
                system_instruction=self._get_evaluation_system_prompt(),
                request_id=f"eval_{idx}",
                metadata={"sample_index": idx},
            ))

        # Estimate and log cost savings
        cost_estimate = batch_service.estimate_cost(batch_requests, model)
        logger.info(
            f"[RAG-BATCH] Starting batch evaluation | "
            f"samples={len(samples)} | model={model} | "
            f"estimated_cost=${cost_estimate['batch_cost_usd']:.4f} "
            f"(saving ${cost_estimate['savings_usd']:.4f})"
        )

        # Create batch job
        job = await batch_service.create_batch_job(
            batch_requests,
            model=model,
            job_name=f"rag-eval-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        )

        if not wait_for_results:
            # Return pending report with job info
            return EvaluationReport(
                total_samples=len(samples),
                avg_scores={},
                min_scores={},
                max_scores={},
                results=[],
                metadata={
                    "batch_job_id": job.job_id,
                    "batch_job_name": job.name,
                    "status": "pending",
                    "cost_estimate": cost_estimate,
                },
            )

        # Wait for completion
        job = await batch_service.wait_for_completion(job.job_id)

        if job.status != BatchJobStatus.COMPLETED:
            logger.error(f"[RAG-BATCH] Job failed: {job.status}")
            return EvaluationReport(
                total_samples=len(samples),
                avg_scores={},
                min_scores={},
                max_scores={},
                results=[],
                metadata={
                    "batch_job_id": job.job_id,
                    "status": str(job.status),
                    "error": "Batch job did not complete successfully",
                },
            )

        # Parse results
        results: list[EvaluationResult] = []
        for idx, response in enumerate(job.results):
            sample = samples[idx] if idx < len(samples) else None
            scores = self._parse_evaluation_response(response.content if response.success else None)

            results.append(EvaluationResult(
                sample_id=f"batch_{idx}",
                question=sample.question if sample else "",
                scores=scores,
                latency_ms=0,  # Batch doesn't track individual latency
                metadata={
                    "batch_response": response.success,
                    "usage": response.usage,
                },
            ))

        # Aggregate scores
        avg_scores, min_scores, max_scores = self._aggregate_scores(results)
        duration = time.time() - start_time

        logger.info(
            f"[RAG-BATCH] Evaluation complete | "
            f"samples={len(samples)} | "
            f"duration={duration:.1f}s | "
            f"actual_cost=${job.actual_cost:.4f} | "
            f"avg_faithfulness={avg_scores.get('faithfulness', 0):.4f}"
        )

        return EvaluationReport(
            total_samples=len(samples),
            avg_scores=avg_scores,
            min_scores=min_scores,
            max_scores=max_scores,
            results=results,
            duration_seconds=duration,
            metadata={
                "batch_job_id": job.job_id,
                "model": model,
                "actual_cost": job.actual_cost,
                "estimated_cost": cost_estimate["batch_cost_usd"],
                "savings": cost_estimate["savings_usd"],
                "method": "gemini_batch_api",
            },
        )

    def _build_evaluation_prompt(self, sample: EvaluationSample) -> str:
        """Build evaluation prompt for a single sample."""
        contexts_text = "\n".join(f"[{i+1}] {ctx}" for i, ctx in enumerate(sample.contexts))

        return f"""Evaluate the following RAG (Retrieval-Augmented Generation) response.

## Question
{sample.question}

## Generated Answer
{sample.answer}

## Retrieved Contexts
{contexts_text}

## Evaluation Criteria
1. **Faithfulness** (0.0-1.0): Is the answer grounded in and supported by the contexts?
   - 1.0: All claims in the answer are directly supported by contexts
   - 0.5: Some claims are supported, others are not
   - 0.0: Answer contradicts or is unrelated to contexts

2. **Answer Relevancy** (0.0-1.0): Does the answer address the question?
   - 1.0: Directly and completely answers the question
   - 0.5: Partially addresses the question
   - 0.0: Does not address the question at all

3. **Context Precision** (0.0-1.0): Are the retrieved contexts relevant to the question?
   - 1.0: All contexts are highly relevant
   - 0.5: Some contexts are relevant
   - 0.0: Contexts are not relevant

Respond with ONLY a JSON object:
{{"faithfulness": 0.X, "answer_relevancy": 0.X, "context_precision": 0.X}}"""

    def _get_evaluation_system_prompt(self) -> str:
        """Get system prompt for evaluation."""
        return """You are a RAG (Retrieval-Augmented Generation) quality evaluator.
Your task is to assess the quality of AI-generated answers based on retrieved contexts.
Be objective and precise in your scoring. Output only valid JSON."""

    def _parse_evaluation_response(self, content: Optional[str]) -> dict[str, float]:
        """Parse LLM evaluation response into scores."""
        default_scores = {
            "faithfulness": 0.0,
            "answer_relevancy": 0.0,
            "context_precision": 0.0,
        }

        if not content:
            return default_scores

        try:
            # Try to extract JSON from response
            content = content.strip()
            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            scores = json.loads(content)

            # Validate and clamp scores
            for key in default_scores:
                if key in scores:
                    default_scores[key] = max(0.0, min(1.0, float(scores[key])))

            return default_scores

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse evaluation response: {e}")
            return default_scores


class GoldenDatasetManager:
    """
    Manages golden dataset for RAG evaluation.

    Golden dataset structure (YAML):
        - query: "강주노 감독의 영화적 특징은?"
          ground_truth: "비선형 서사, 계급 갈등, 블랙 코미디..."
          expected_contexts:
            - "db:rag_docs:AD:auteur:bong:..."
          difficulty: medium
          category: auteur_analysis
    """

    def __init__(self, dataset_path: str = "data/rag_golden_dataset.yaml"):
        self.dataset_path = dataset_path
        self._samples: list[EvaluationSample] = []

    def load(self) -> list[EvaluationSample]:
        """Load golden dataset from YAML file."""
        import yaml
        from pathlib import Path

        path = Path(self.dataset_path)
        if not path.exists():
            logger.warning(f"Golden dataset not found: {self.dataset_path}")
            return []

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self._samples = []
        for item in data:
            sample = EvaluationSample(
                question=item["query"],
                answer="",  # Will be filled during evaluation
                contexts=item.get("expected_contexts", []),
                ground_truth=item.get("ground_truth"),
                metadata={
                    "difficulty": item.get("difficulty", "medium"),
                    "category": item.get("category", "general"),
                }
            )
            self._samples.append(sample)

        logger.info(f"Loaded {len(self._samples)} samples from golden dataset")
        return self._samples

    def save(self, samples: list[EvaluationSample]) -> None:
        """Save samples to golden dataset."""
        import yaml
        from pathlib import Path

        path = Path(self.dataset_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = []
        for sample in samples:
            item = {
                "query": sample.question,
                "ground_truth": sample.ground_truth,
                "expected_contexts": sample.contexts,
            }
            if sample.metadata:
                item.update(sample.metadata)
            data.append(item)

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

        logger.info(f"Saved {len(samples)} samples to golden dataset")


class ProductionRAGMonitor:
    """
    Monitor RAG quality in production traffic.

    Samples production queries and evaluates them periodically
    to detect quality degradation.
    """

    def __init__(
        self,
        pipeline: RAGEvaluationPipeline,
        sample_rate: float = 0.01,  # 1% of production traffic
        alert_threshold: float = 0.6,  # Alert if avg score drops below
    ):
        self.pipeline = pipeline
        self.sample_rate = sample_rate
        self.alert_threshold = alert_threshold
        self._buffer: list[EvaluationSample] = []
        self._buffer_max_size = 100
        self._latest_report: Optional[EvaluationReport] = None

    def should_sample(self) -> bool:
        """Determine if current request should be sampled."""
        import random
        return random.random() < self.sample_rate

    async def record_sample(
        self,
        question: str,
        answer: str,
        contexts: list[str],
    ) -> None:
        """Record a sample for batch evaluation."""
        if len(self._buffer) >= self._buffer_max_size:
            # Trigger evaluation when buffer is full
            await self.evaluate_buffer()

        self._buffer.append(EvaluationSample(
            question=question,
            answer=answer,
            contexts=contexts,
        ))

    async def evaluate_buffer(self) -> Optional[EvaluationReport]:
        """Evaluate accumulated samples and check for alerts."""
        if not self._buffer:
            return None

        samples = self._buffer.copy()
        self._buffer.clear()

        report = await self.pipeline.evaluate_batch(samples)
        self._latest_report = report

        # Check for quality alerts
        for metric, score in report.avg_scores.items():
            if score < self.alert_threshold:
                logger.warning(
                    f"RAG quality alert: {metric} = {score:.4f} "
                    f"(threshold: {self.alert_threshold})"
                )

        return report

    def get_latest_report(self) -> Optional[EvaluationReport]:
        """Get the most recent evaluation report."""
        return self._latest_report
