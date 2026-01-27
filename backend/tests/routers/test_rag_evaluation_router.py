"""
Tests for RAG Evaluation Router (P1.2)

Tests the HTTP endpoints for RAG quality evaluation.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Synchronous test client."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


class TestEvaluateSingleEndpoint:
    """Tests for POST /api/v1/rag-eval/evaluate"""

    def test_evaluate_single_success(self, client):
        """Test single sample evaluation."""
        # Mock the pipeline to avoid actual LLM calls
        with patch("app.routers.rag_evaluation.get_pipeline") as mock_get:
            mock_pipeline = MagicMock()
            mock_pipeline.evaluate_single = AsyncMock(return_value=MagicMock(
                sample_id="test_1",
                question="봉준호 스타일",
                scores={"faithfulness": 0.85, "answer_relevancy": 0.9},
                timestamp=MagicMock(isoformat=lambda: "2026-01-28T00:00:00"),
                latency_ms=150.0,
                metadata={"answer_length": 100},
            ))
            mock_get.return_value = mock_pipeline

            response = client.post(
                "/api/v1/rag-eval/evaluate",
                json={
                    "question": "봉준호 감독의 영화적 특징은?",
                    "answer": "봉준호는 비선형 서사와 계급 갈등을 주제로 합니다.",
                    "contexts": ["봉준호는 기생충에서 계급 갈등을 다뤘습니다."],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "scores" in data
            assert "faithfulness" in data["scores"]

    def test_evaluate_single_validation_error(self, client):
        """Test validation error for invalid input."""
        response = client.post(
            "/api/v1/rag-eval/evaluate",
            json={
                "question": "",  # Invalid: empty
                "answer": "test",
                "contexts": [],  # Invalid: empty
            },
        )

        assert response.status_code == 422


class TestGoldenDatasetEndpoint:
    """Tests for GET /api/v1/rag-eval/golden-dataset"""

    def test_get_golden_dataset(self, client):
        """Test getting golden dataset."""
        response = client.get("/api/v1/rag-eval/golden-dataset")

        assert response.status_code == 200
        data = response.json()
        assert "total_items" in data
        assert "items" in data
        assert "categories" in data
        # We created 75 items
        assert data["total_items"] >= 65


class TestReportEndpoint:
    """Tests for GET /api/v1/rag-eval/report"""

    def test_get_report_no_data(self, client):
        """Test getting report when no evaluation has run."""
        # Reset module state
        import app.routers.rag_evaluation as module
        module._latest_report = None
        module._monitor = None

        response = client.get("/api/v1/rag-eval/report")

        # Should return 404 when no report available
        assert response.status_code == 404


class TestEvaluateBatchEndpoint:
    """Tests for POST /api/v1/rag-eval/evaluate/batch"""

    def test_evaluate_batch_success(self, client):
        """Test batch evaluation."""
        from app.rag.evaluation import EvaluationReport

        with patch("app.routers.rag_evaluation.get_pipeline") as mock_get:
            mock_pipeline = MagicMock()
            mock_pipeline.evaluate_batch = AsyncMock(return_value=EvaluationReport(
                total_samples=2,
                avg_scores={"faithfulness": 0.85},
                min_scores={"faithfulness": 0.80},
                max_scores={"faithfulness": 0.90},
                results=[],
                duration_seconds=5.0,
                metadata={},
            ))
            mock_get.return_value = mock_pipeline

            response = client.post(
                "/api/v1/rag-eval/evaluate/batch",
                json={
                    "samples": [
                        {
                            "question": "Question 1",
                            "answer": "Answer 1",
                            "contexts": ["Context 1"],
                        },
                        {
                            "question": "Question 2",
                            "answer": "Answer 2",
                            "contexts": ["Context 2"],
                        },
                    ],
                    "use_gemini_batch": False,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_samples"] == 2
            assert "avg_scores" in data


class TestGoldenDatasetCount:
    """Verify golden dataset has required items."""

    def test_golden_dataset_count(self):
        """Verify golden dataset has 65+ items."""
        import yaml
        from pathlib import Path

        path = Path("data/rag_eval/golden_dataset.yaml")
        assert path.exists(), "Golden dataset file should exist"

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert len(data) >= 65, f"Expected 65+ items, got {len(data)}"

    def test_golden_dataset_categories(self):
        """Verify golden dataset has required categories."""
        import yaml
        from pathlib import Path

        path = Path("data/rag_eval/golden_dataset.yaml")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        categories = set(item.get("category", "unknown") for item in data)

        required = {
            "auteur_technique",
            "auteur_symbolism",
            "prompt",
            "storyboard",
            "visual",
            "reference",
            "structure",
            "design",
            "basics",
            "technique",
            "negative_test",
            "security_test",
        }

        assert required.issubset(categories), f"Missing categories: {required - categories}"

    def test_golden_dataset_dimensions(self):
        """Verify golden dataset covers all dimensions."""
        import yaml
        from pathlib import Path

        path = Path("data/rag_eval/golden_dataset.yaml")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        dimensions = set(
            item.get("dimension")
            for item in data
            if item.get("dimension")
        )

        required = {"AD", "1D", "2D", "3D", "4D", "STORY", "SOUND", "QC", "VEO"}

        assert required.issubset(dimensions), f"Missing dimensions: {required - dimensions}"
