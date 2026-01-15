"""
P1.2 RAG Evaluation Pipeline Tests
==================================

Tests for RAG quality evaluation using Ragas framework.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

from app.rag.evaluation import (
    EvaluationMetric,
    EvaluationSample,
    EvaluationResult,
    EvaluationReport,
    RAGEvaluationPipeline,
    GoldenDatasetManager,
    ProductionRAGMonitor,
)


class TestEvaluationMetric:
    """Test EvaluationMetric enum."""

    def test_metric_values(self):
        """Test metric enum values."""
        assert EvaluationMetric.FAITHFULNESS.value == "faithfulness"
        assert EvaluationMetric.ANSWER_RELEVANCY.value == "answer_relevancy"
        assert EvaluationMetric.CONTEXT_PRECISION.value == "context_precision"
        assert EvaluationMetric.CONTEXT_RECALL.value == "context_recall"


class TestEvaluationSample:
    """Test EvaluationSample dataclass."""

    def test_sample_creation(self):
        """Test creating an evaluation sample."""
        sample = EvaluationSample(
            question="What is RAG?",
            answer="RAG is Retrieval-Augmented Generation.",
            contexts=["RAG combines retrieval with generation."],
            ground_truth="RAG is a technique that combines retrieval with generation.",
        )

        assert sample.question == "What is RAG?"
        assert sample.answer == "RAG is Retrieval-Augmented Generation."
        assert len(sample.contexts) == 1
        assert sample.ground_truth is not None

    def test_sample_without_ground_truth(self):
        """Test sample without ground truth."""
        sample = EvaluationSample(
            question="Test question",
            answer="Test answer",
            contexts=["Context"],
        )

        assert sample.ground_truth is None
        assert sample.metadata == {}


class TestEvaluationResult:
    """Test EvaluationResult dataclass."""

    def test_result_creation(self):
        """Test creating an evaluation result."""
        result = EvaluationResult(
            sample_id="test-001",
            question="What is AI?",
            scores={"faithfulness": 0.95, "answer_relevancy": 0.88},
            latency_ms=150.5,
        )

        assert result.sample_id == "test-001"
        assert result.scores["faithfulness"] == 0.95
        assert result.latency_ms == 150.5

    def test_result_to_dict(self):
        """Test result serialization to dict."""
        result = EvaluationResult(
            sample_id="test-001",
            question="Test",
            scores={"faithfulness": 0.9},
        )

        data = result.to_dict()

        assert data["sample_id"] == "test-001"
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)  # ISO format


class TestEvaluationReport:
    """Test EvaluationReport dataclass."""

    def test_report_creation(self):
        """Test creating an evaluation report."""
        results = [
            EvaluationResult("1", "Q1", {"faithfulness": 0.9}),
            EvaluationResult("2", "Q2", {"faithfulness": 0.8}),
        ]

        report = EvaluationReport(
            total_samples=2,
            avg_scores={"faithfulness": 0.85},
            min_scores={"faithfulness": 0.8},
            max_scores={"faithfulness": 0.9},
            results=results,
            duration_seconds=5.5,
        )

        assert report.total_samples == 2
        assert report.avg_scores["faithfulness"] == 0.85
        assert report.duration_seconds == 5.5

    def test_report_to_dict(self):
        """Test report serialization."""
        report = EvaluationReport(
            total_samples=1,
            avg_scores={"faithfulness": 0.9},
            min_scores={"faithfulness": 0.9},
            max_scores={"faithfulness": 0.9},
            results=[],
            duration_seconds=1.0,
        )

        data = report.to_dict()

        assert data["total_samples"] == 1
        assert "timestamp" in data

    def test_report_summary(self):
        """Test report summary generation."""
        report = EvaluationReport(
            total_samples=10,
            avg_scores={
                "faithfulness": 0.85,
                "answer_relevancy": 0.55,  # Medium score (0.5-0.7)
                "context_precision": 0.45,  # Low score (<0.5)
            },
            min_scores={},
            max_scores={},
            results=[],
            duration_seconds=30.0,
        )

        summary = report.summary()

        assert "Total Samples: 10" in summary
        assert "faithfulness: 0.8500" in summary
        assert "✅" in summary  # High score indicator (faithfulness 0.85)
        assert "⚠️" in summary  # Medium score indicator (relevancy 0.55)
        assert "❌" in summary  # Low score indicator (precision 0.45)


class TestRAGEvaluationPipeline:
    """Test RAG Evaluation Pipeline."""

    @pytest.fixture
    def pipeline(self):
        """Create a pipeline instance."""
        return RAGEvaluationPipeline(
            metrics=[
                EvaluationMetric.FAITHFULNESS,
                EvaluationMetric.ANSWER_RELEVANCY,
            ]
        )

    @pytest.mark.asyncio
    async def test_fallback_evaluation(self, pipeline):
        """Test fallback evaluation when Ragas not available."""
        result = await pipeline.evaluate_single(
            question="What is machine learning?",
            answer="Machine learning is a subset of AI that enables learning from data.",
            contexts=["Machine learning uses algorithms to learn patterns from data."],
        )

        assert result.sample_id is not None
        assert "faithfulness" in result.scores or "answer_relevancy" in result.scores
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_evaluate_with_ground_truth(self, pipeline):
        """Test evaluation with ground truth provided."""
        result = await pipeline.evaluate_single(
            question="What is Python?",
            answer="Python is a programming language.",
            contexts=["Python is a high-level programming language."],
            ground_truth="Python is a versatile programming language.",
        )

        assert result.metadata.get("has_ground_truth") is True

    @pytest.mark.asyncio
    async def test_evaluate_batch(self, pipeline):
        """Test batch evaluation."""
        samples = [
            EvaluationSample(
                question="Q1",
                answer="A1",
                contexts=["C1"],
            ),
            EvaluationSample(
                question="Q2",
                answer="A2",
                contexts=["C2"],
            ),
        ]

        report = await pipeline.evaluate_batch(samples, concurrency=2)

        assert report.total_samples == 2
        assert len(report.results) == 2
        assert report.duration_seconds > 0

    @pytest.mark.asyncio
    async def test_fallback_faithfulness_calculation(self, pipeline):
        """Test fallback faithfulness uses word overlap."""
        # High overlap = high faithfulness
        result = await pipeline._fallback_evaluation(
            question="What is AI?",
            answer="AI is artificial intelligence that enables machines to learn.",
            contexts=["Artificial intelligence (AI) enables machines to learn and improve."],
        )

        assert "faithfulness" in result
        assert result["faithfulness"] > 0  # Should have some overlap

    @pytest.mark.asyncio
    async def test_fallback_empty_contexts(self, pipeline):
        """Test fallback handles empty contexts."""
        result = await pipeline._fallback_evaluation(
            question="Test",
            answer="Test answer",
            contexts=[],
        )

        assert result["context_precision"] == 0

    def test_aggregate_scores(self, pipeline):
        """Test score aggregation."""
        results = [
            EvaluationResult("1", "Q1", {"faithfulness": 0.9, "relevancy": 0.8}),
            EvaluationResult("2", "Q2", {"faithfulness": 0.7, "relevancy": 0.6}),
        ]

        avg, min_s, max_s = pipeline._aggregate_scores(results)

        assert avg["faithfulness"] == 0.8  # (0.9 + 0.7) / 2
        assert min_s["faithfulness"] == 0.7
        assert max_s["faithfulness"] == 0.9

    def test_aggregate_empty_results(self, pipeline):
        """Test aggregation with empty results."""
        avg, min_s, max_s = pipeline._aggregate_scores([])

        assert avg == {}
        assert min_s == {}
        assert max_s == {}


class TestGoldenDatasetManager:
    """Test Golden Dataset Manager."""

    def test_manager_creation(self):
        """Test manager can be created."""
        manager = GoldenDatasetManager("test/path.yaml")

        assert manager.dataset_path == "test/path.yaml"

    def test_load_nonexistent_file(self):
        """Test loading non-existent file returns empty list."""
        manager = GoldenDatasetManager("nonexistent/path.yaml")

        samples = manager.load()

        assert samples == []

    @patch("builtins.open")
    @patch("pathlib.Path.exists", return_value=True)
    def test_load_valid_yaml(self, mock_exists, mock_open):
        """Test loading valid YAML file."""
        import yaml

        yaml_content = """
- query: "What is RAG?"
  ground_truth: "RAG is Retrieval-Augmented Generation."
  expected_contexts:
    - "db:rag_docs:1"
  difficulty: easy
  category: general
"""
        mock_open.return_value.__enter__.return_value.read.return_value = yaml_content

        manager = GoldenDatasetManager("test.yaml")

        with patch("yaml.safe_load", return_value=[{
            "query": "What is RAG?",
            "ground_truth": "RAG is Retrieval-Augmented Generation.",
            "expected_contexts": ["db:rag_docs:1"],
            "difficulty": "easy",
            "category": "general",
        }]):
            samples = manager.load()

        assert len(samples) == 1
        assert samples[0].question == "What is RAG?"


class TestProductionRAGMonitor:
    """Test Production RAG Monitor."""

    @pytest.fixture
    def monitor(self):
        """Create a monitor instance."""
        pipeline = RAGEvaluationPipeline()
        return ProductionRAGMonitor(
            pipeline=pipeline,
            sample_rate=0.5,  # 50% for testing
            alert_threshold=0.6,
        )

    def test_should_sample_respects_rate(self, monitor):
        """Test sampling respects configured rate."""
        # With 50% rate, should get roughly half True over many samples
        samples = [monitor.should_sample() for _ in range(100)]
        true_count = sum(samples)

        # Should be roughly 50 (allow variance)
        assert 30 < true_count < 70

    @pytest.mark.asyncio
    async def test_record_sample(self, monitor):
        """Test recording a sample."""
        await monitor.record_sample(
            question="Test question",
            answer="Test answer",
            contexts=["Test context"],
        )

        assert len(monitor._buffer) == 1

    @pytest.mark.asyncio
    async def test_evaluate_buffer_empty(self, monitor):
        """Test evaluating empty buffer returns None."""
        result = await monitor.evaluate_buffer()

        assert result is None

    @pytest.mark.asyncio
    async def test_evaluate_buffer_with_samples(self, monitor):
        """Test evaluating buffer with samples."""
        # Add samples
        for i in range(5):
            await monitor.record_sample(
                question=f"Q{i}",
                answer=f"A{i}",
                contexts=[f"C{i}"],
            )

        report = await monitor.evaluate_buffer()

        assert report is not None
        assert report.total_samples == 5
        assert len(monitor._buffer) == 0  # Buffer cleared

    def test_get_latest_report_initially_none(self, monitor):
        """Test latest report is None initially."""
        assert monitor.get_latest_report() is None

    @pytest.mark.asyncio
    async def test_get_latest_report_after_evaluation(self, monitor):
        """Test latest report is available after evaluation."""
        await monitor.record_sample("Q", "A", ["C"])
        await monitor.evaluate_buffer()

        report = monitor.get_latest_report()

        assert report is not None
        assert isinstance(report, EvaluationReport)
