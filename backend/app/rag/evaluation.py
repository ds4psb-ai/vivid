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
            question="봉준호 감독의 영화적 특징은?",
            answer="봉준호는 비선형 서사와 계급 갈등을 주제로...",
            contexts=["봉준호는 기생충에서...", "봉준호의 초기작..."],
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
            from langchain_openai import ChatOpenAI
            from ragas.llms import LangchainLLMWrapper

            # Initialize LLM wrapper for Ragas
            llm = ChatOpenAI(model=self.llm_model)
            self._evaluator_llm = LangchainLLMWrapper(llm)

            # Map metrics to Ragas metric instances
            metric_map = {
                EvaluationMetric.FAITHFULNESS: Faithfulness(llm=self._evaluator_llm),
                EvaluationMetric.ANSWER_RELEVANCY: AnswerRelevancy(llm=self._evaluator_llm),
                EvaluationMetric.CONTEXT_PRECISION: ContextPrecision(llm=self._evaluator_llm),
                EvaluationMetric.CONTEXT_RECALL: ContextRecall(llm=self._evaluator_llm),
            }

            self._ragas_metrics = [
                metric_map[m] for m in self.metric_types
                if m in metric_map
            ]

            logger.info(f"Ragas initialized with metrics: {[m.value for m in self.metric_types]}")

        except ImportError as e:
            logger.warning(f"Ragas not installed: {e}. Using fallback evaluation.")
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
        """Evaluate using Ragas framework."""
        try:
            from ragas import evaluate
            from datasets import Dataset

            # Prepare dataset
            data = {
                "question": [question],
                "answer": [answer],
                "contexts": [contexts],
            }

            if ground_truth:
                data["ground_truth"] = [ground_truth]

            dataset = Dataset.from_dict(data)

            # Run evaluation
            result = evaluate(dataset, metrics=self._ragas_metrics)

            # Extract scores
            scores = {}
            for metric in self.metric_types:
                metric_name = metric.value
                if metric_name in result:
                    score = result[metric_name]
                    # Handle numpy types
                    if hasattr(score, 'item'):
                        score = score.item()
                    scores[metric_name] = float(score)

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


class GoldenDatasetManager:
    """
    Manages golden dataset for RAG evaluation.

    Golden dataset structure (YAML):
        - query: "봉준호 감독의 영화적 특징은?"
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
