"""
UQSL API Router Tests

Tests for UQSL API endpoints.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import get_db
from app.uqsl.models import (
    CandidateResult,
    QualityScore,
    SelectionResult,
)


def get_mock_db():
    """Create a mock database session."""
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    return mock_db


@pytest_asyncio.fixture
async def async_client():
    """Create async test client with mocked database."""
    # Override database dependency
    mock_db = get_mock_db()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()


class TestGenerateEndpoint:
    """Test POST /api/v1/uqsl/generate endpoint."""

    @pytest.mark.asyncio
    async def test_generate_success(self, async_client, mock_session_cache):
        """Test successful candidate generation."""
        # mock_session_cache is provided by conftest fixture

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
    async def test_select_success(self, async_client, mock_session_cache):
        """Test successful selection with pre-created session."""
        test_session_id = "test-session-123"

        # Configure mock session cache with pre-populated data
        mock_session_data = {
            "candidates": [
                {"idx": 0, "content": "Result 0", "backend_used": "backend_a", "metadata": {}, "latency_ms": 0},
                {"idx": 1, "content": "Result 1", "backend_used": "backend_b", "metadata": {}, "latency_ms": 0},
            ],
            "scores": [],
            "app_key": "test_app",
            "arms_used": ["backend:backend_a", "backend:backend_b"],
            "created_at": "2026-01-16T00:00:00",
        }
        mock_session_cache.get = AsyncMock(return_value=mock_session_data)

        response = await async_client.post(
            "/api/v1/uqsl/select",
            json={
                "session_id": test_session_id,
                "selected_idx": 1,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "selected"
        assert data["session_id"] == test_session_id

    @pytest.mark.asyncio
    async def test_select_session_not_found(self, async_client):
        """Test selection with non-existent session."""
        response = await async_client.post(
            "/api/v1/uqsl/select",
            json={
                "session_id": "non-existent-session",
                "selected_idx": 0,
            },
        )

        assert response.status_code == 404


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
        # Mock both ensemble router and thompson sampling router
        mock_ensemble = MagicMock()
        mock_ensemble.get_three_way_results = AsyncMock(return_value={
            "a": CandidateResult(idx=0, content="Result A", backend_used="qdrant"),
            "b": CandidateResult(idx=1, content="Result B", backend_used="notebooklm"),
            "ab": CandidateResult(idx=2, content="Result AB", backend_used="ensemble"),
        })
        mock_ensemble.select_best_arm = AsyncMock(return_value="ab")

        mock_ts = MagicMock()
        mock_ts.get_arm_stats = MagicMock(return_value={
            "alpha": 5, "beta": 2, "total_trials": 5, "success_rate": 0.7
        })

        # Patch at the source module level (imports happen inside function body)
        with patch("app.uqsl.ensemble_plus_plus.get_ensemble_router", return_value=mock_ensemble), \
             patch("app.uqsl.thompson_sampling.get_initialized_router", new_callable=AsyncMock, return_value=mock_ts):

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
        # Mock DB queries to return test data - the async_client fixture
        # already overrides get_db, but we need to configure the mock's
        # execute to return proper scalar results

        # Create mock results for each query
        mock_result_total = MagicMock()
        mock_result_total.scalar = MagicMock(return_value=10)

        mock_result_positive = MagicMock()
        mock_result_positive.scalar = MagicMock(return_value=7)

        mock_result_feedback = MagicMock()
        mock_result_feedback.scalar = MagicMock(return_value=10)

        mock_result_avg = MagicMock()
        mock_result_avg.scalar = MagicMock(return_value=0.85)

        # Create mock db that returns these results in sequence
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=[
            mock_result_total,
            mock_result_positive,
            mock_result_feedback,
            mock_result_avg,
        ])

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db

        response = await async_client.get(
            "/api/v1/uqsl/metrics/dimension.aesthetic",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["app_key"] == "dimension.aesthetic"
        assert "total_selections" in data
        assert "positive_rate" in data
        assert "avg_quality_score" in data
