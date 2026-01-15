"""
UQSL Models Tests

Tests for Pydantic v2 models with computed_field and validation.
"""

import pytest
from pydantic import ValidationError

from app.uqsl.models import (
    QualityScore,
    CandidateResult,
    SelectionResult,
    GenerateCandidatesRequest,
    GenerateCandidatesResponse,
)


class TestQualityScore:
    """Test QualityScore model with computed total_score."""

    def test_quality_score_valid(self):
        """Test valid quality score creation."""
        score = QualityScore(
            groundedness=0.8,
            relevance=0.7,
            coherence=0.9,
            creativity=0.6,
            safety=0.95,
        )
        assert score.groundedness == 0.8
        assert score.relevance == 0.7
        assert score.coherence == 0.9
        assert score.creativity == 0.6
        assert score.safety == 0.95

    def test_quality_score_computed_total(self):
        """Test computed_field total_score calculation."""
        score = QualityScore(
            groundedness=0.8,
            relevance=0.7,
            coherence=0.9,
            creativity=0.6,
            safety=1.0,
        )
        # Expected: 0.8*0.30 + 0.7*0.25 + 0.9*0.20 + 0.6*0.15 + 1.0*0.10
        # = 0.24 + 0.175 + 0.18 + 0.09 + 0.10 = 0.785
        expected_total = (
            0.8 * 0.30 +
            0.7 * 0.25 +
            0.9 * 0.20 +
            0.6 * 0.15 +
            1.0 * 0.10
        )
        assert abs(score.total_score - expected_total) < 0.001

    def test_quality_score_all_ones(self):
        """Test perfect score (all 1.0)."""
        score = QualityScore(
            groundedness=1.0,
            relevance=1.0,
            coherence=1.0,
            creativity=1.0,
            safety=1.0,
        )
        assert score.total_score == 1.0

    def test_quality_score_all_zeros(self):
        """Test minimum score (all 0.0)."""
        score = QualityScore(
            groundedness=0.0,
            relevance=0.0,
            coherence=0.0,
            creativity=0.0,
            safety=0.0,
        )
        assert score.total_score == 0.0

    def test_quality_score_validation_bounds(self):
        """Test validation rejects out-of-bounds values."""
        with pytest.raises(ValidationError):
            QualityScore(
                groundedness=1.5,  # Invalid: > 1
                relevance=0.7,
                coherence=0.9,
                creativity=0.6,
                safety=0.95,
            )

        with pytest.raises(ValidationError):
            QualityScore(
                groundedness=0.8,
                relevance=-0.1,  # Invalid: < 0
                coherence=0.9,
                creativity=0.6,
                safety=0.95,
            )

    def test_quality_score_model_dump(self):
        """Test model serialization."""
        score = QualityScore(
            groundedness=0.8,
            relevance=0.7,
            coherence=0.9,
            creativity=0.6,
            safety=0.95,
        )
        data = score.model_dump()
        assert "groundedness" in data
        assert "total_score" in data  # computed_field included


class TestCandidateResult:
    """Test CandidateResult model."""

    def test_candidate_result_basic(self):
        """Test basic candidate creation."""
        candidate = CandidateResult(
            idx=0,
            content="Test output",
            metadata={"seed": 42},
            latency_ms=150,
            backend_used="qdrant_hybrid",
        )
        assert candidate.idx == 0
        assert candidate.content == "Test output"
        assert candidate.metadata["seed"] == 42
        assert candidate.latency_ms == 150
        assert candidate.backend_used == "qdrant_hybrid"

    def test_candidate_result_defaults(self):
        """Test default values."""
        candidate = CandidateResult(
            idx=0,
            content="Test",
        )
        assert candidate.metadata == {}
        assert candidate.quality_score is None
        assert candidate.latency_ms == 0
        assert candidate.backend_used == "default"

    def test_candidate_result_with_quality_score(self):
        """Test candidate with attached quality score."""
        score = QualityScore(
            groundedness=0.8,
            relevance=0.7,
            coherence=0.9,
            creativity=0.6,
            safety=0.95,
        )
        candidate = CandidateResult(
            idx=0,
            content="Test",
            quality_score=score,
        )
        assert candidate.quality_score is not None
        assert candidate.quality_score.groundedness == 0.8


class TestSelectionResult:
    """Test SelectionResult model."""

    def test_selection_result_creation(self):
        """Test selection result creation."""
        candidate = CandidateResult(idx=0, content="Selected")
        all_candidates = [
            CandidateResult(idx=0, content="Selected"),
            CandidateResult(idx=1, content="Not selected"),
        ]

        result = SelectionResult(
            session_id="test-session-123",
            selected=candidate,
            method="auto",
            confidence=0.85,
            arms_used=["backend:qdrant_hybrid"],
            all_candidates=all_candidates,
        )

        assert result.session_id == "test-session-123"
        assert result.selected.idx == 0
        assert result.method == "auto"
        assert result.confidence == 0.85
        assert len(result.all_candidates) == 2

    def test_selection_result_method_validation(self):
        """Test method field accepts valid values."""
        for method in ["auto", "hitl", "hybrid", "llm_judge"]:
            candidate = CandidateResult(idx=0, content="Test")
            result = SelectionResult(
                session_id="test",
                selected=candidate,
                method=method,
                confidence=0.5,
                arms_used=[],
                all_candidates=[candidate],
            )
            assert result.method == method


class TestRequestModels:
    """Test request/response models."""

    def test_generate_candidates_request(self):
        """Test generate request validation."""
        request = GenerateCandidatesRequest(
            prompt="Create a scene",
            app_key="dimension.aesthetic",
            n_candidates=3,
            strategy="auto",
        )
        assert request.prompt == "Create a scene"
        assert request.n_candidates == 3
        assert request.strategy == "auto"

    def test_generate_candidates_request_defaults(self):
        """Test default values."""
        request = GenerateCandidatesRequest(
            prompt="Test",
            app_key="test.app",
        )
        assert request.n_candidates == 3
        assert request.strategy == "auto"

    def test_generate_candidates_request_validation(self):
        """Test validation constraints."""
        # n_candidates must be 1-5
        with pytest.raises(ValidationError):
            GenerateCandidatesRequest(
                prompt="Test",
                app_key="test.app",
                n_candidates=10,  # Too many
            )

        with pytest.raises(ValidationError):
            GenerateCandidatesRequest(
                prompt="Test",
                app_key="test.app",
                n_candidates=0,  # Too few
            )
