"""
UQSL API Router Tests

Tests for UQSL API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.uqsl.models import (
    CandidateResult,
    QualityScore,
    SelectionResult,
)


@pytest.fixture
async def async_client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestGenerateEndpoint:
    """Test POST /api/v1/uqsl/generate endpoint."""

    @pytest.mark.asyncio
    async def test_generate_success(self, async_client):
        """Test successful candidate generation."""
        with patch("app.routers.uqsl.get_multi_generate_engine") as mock_engine, \
             patch("app.routers.uqsl.get_quality_evaluator") as mock_evaluator, \
             patch("app.routers.uqsl.get_best_selector") as mock_selector:

            # Mock engine
            engine = MagicMock()
            engine.generate_candidates = AsyncMock(return_value=[
                CandidateResult(idx=0, content="Candidate 1"),
                CandidateResult(idx=1, content="Candidate 2"),
                CandidateResult(idx=2, content="Candidate 3"),
            ])
            mock_engine.return_value = engine

            # Mock evaluator
            evaluator = MagicMock()
            evaluator.evaluate_batch = AsyncMock(return_value=[
                QualityScore(groundedness=0.8, relevance=0.7, coherence=0.9, creativity=0.6, safety=0.95),
                QualityScore(groundedness=0.7, relevance=0.8, coherence=0.8, creativity=0.7, safety=0.90),
                QualityScore(groundedness=0.85, relevance=0.75, coherence=0.85, creativity=0.65, safety=0.92),
            ])
            mock_evaluator.return_value = evaluator

            # Mock selector
            selector = MagicMock()
            selector.select_best = AsyncMock(return_value=SelectionResult(
                session_id="test-session",
                selected=CandidateResult(idx=0, content="Candidate 1"),
                method="auto",
                confidence=0.85,
                arms_used=["backend:qdrant_hybrid"],
                all_candidates=[
                    CandidateResult(idx=0, content="Candidate 1"),
                    CandidateResult(idx=1, content="Candidate 2"),
                    CandidateResult(idx=2, content="Candidate 3"),
                ],
            ))
            mock_selector.return_value = selector

            response = await async_client.post(
                "/api/v1/uqsl/generate",
                json={
                    "prompt": "Create a cinematic scene",
                    "app_key": "dimension.aesthetic",
                    "n_candidates": 3,
                    "strategy": "auto",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            assert "candidates" in data
            assert "quality_scores" in data
            assert data["recommended_idx"] == 0

    @pytest.mark.asyncio
    async def test_generate_invalid_n_candidates(self, async_client):
        """Test validation error for invalid n_candidates."""
        response = await async_client.post(
            "/api/v1/uqsl/generate",
            json={
                "prompt": "Test",
                "app_key": "test.app",
                "n_candidates": 10,  # Invalid: max is 5
            },
        )

        assert response.status_code == 422  # Validation error


class TestSelectEndpoint:
    """Test POST /api/v1/uqsl/select endpoint."""

    @pytest.mark.asyncio
    async def test_select_success(self, async_client):
        """Test successful selection."""
        response = await async_client.post(
            "/api/v1/uqsl/select",
            json={
                "session_id": "test-session-123",
                "selected_idx": 1,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "selected"
        assert data["session_id"] == "test-session-123"


class TestFeedbackEndpoint:
    """Test POST /api/v1/uqsl/feedback endpoint."""

    @pytest.mark.asyncio
    async def test_feedback_positive(self, async_client):
        """Test positive feedback submission."""
        with patch("app.routers.uqsl.get_thompson_sampling_router") as mock_router:
            router = MagicMock()
            router.update = AsyncMock()
            mock_router.return_value = router

            response = await async_client.post(
                "/api/v1/uqsl/feedback",
                json={
                    "selection_id": "test-selection-123",
                    "feedback": "positive",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "recorded"

    @pytest.mark.asyncio
    async def test_feedback_negative(self, async_client):
        """Test negative feedback submission."""
        with patch("app.routers.uqsl.get_thompson_sampling_router") as mock_router:
            router = MagicMock()
            router.update = AsyncMock()
            mock_router.return_value = router

            response = await async_client.post(
                "/api/v1/uqsl/feedback",
                json={
                    "selection_id": "test-selection-123",
                    "feedback": "negative",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "recorded"


class TestThreeWayEndpoint:
    """Test POST /api/v1/uqsl/three-way endpoint."""

    @pytest.mark.asyncio
    async def test_three_way_comparison(self, async_client):
        """Test 3-way comparison endpoint."""
        with patch("app.routers.uqsl.get_ensemble_router") as mock_router:
            router = MagicMock()
            router.get_three_way_results = AsyncMock(return_value={
                "a": CandidateResult(idx=0, content="Result A", backend_used="qdrant"),
                "b": CandidateResult(idx=1, content="Result B", backend_used="notebooklm"),
                "ab": CandidateResult(idx=2, content="Result AB", backend_used="ensemble"),
            })
            router.select_best_arm = AsyncMock(return_value="ab")
            router.get_arm_stats = MagicMock(return_value={
                "qdrant_only": {"alpha": 5, "beta": 2},
                "notebooklm_only": {"alpha": 3, "beta": 4},
                "ensemble_ab": {"alpha": 8, "beta": 1},
            })
            mock_router.return_value = router

            response = await async_client.post(
                "/api/v1/uqsl/three-way",
                json={
                    "query": "Test query",
                    "dimension": "AD",
                    "auteur_key": "bong",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert "recommended" in data
            assert data["recommended"] == "ab"


class TestMetricsEndpoint:
    """Test GET /api/v1/uqsl/metrics/{app_key} endpoint."""

    @pytest.mark.asyncio
    async def test_get_metrics(self, async_client):
        """Test quality metrics retrieval."""
        response = await async_client.get(
            "/api/v1/uqsl/metrics/dimension.aesthetic",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["app_key"] == "dimension.aesthetic"
        assert "total_selections" in data
        assert "positive_rate" in data
        assert "avg_quality_score" in data
