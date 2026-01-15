"""
Quality Evaluator Tests

Tests for rule-based and LLM-as-Judge quality evaluation.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.uqsl.quality_evaluator import (
    QualityEvaluator,
    get_quality_evaluator,
)
from app.uqsl.models import CandidateResult, QualityScore


class TestQualityEvaluator:
    """Test Quality Evaluator."""

    def test_evaluator_initialization_free_tier(self):
        """Test evaluator initializes in free tier (no LLM)."""
        evaluator = QualityEvaluator(tier="free")

        assert evaluator.tier == "free"
        assert evaluator.use_llm_judge is False

    def test_evaluator_initialization_premium_tier(self):
        """Test evaluator initializes in premium tier (with LLM)."""
        evaluator = QualityEvaluator(use_llm_judge=True, tier="premium")

        assert evaluator.tier == "premium"
        assert evaluator.use_llm_judge is True

    @pytest.mark.asyncio
    async def test_evaluate_returns_quality_score(self):
        """Test evaluate returns QualityScore."""
        evaluator = QualityEvaluator(tier="free")
        candidate = CandidateResult(
            idx=0,
            content="This is a test response about film aesthetics. It has multiple sentences. The cinematography is excellent.",
        )

        score = await evaluator.evaluate(candidate, context=None)

        assert isinstance(score, QualityScore)
        assert 0 <= score.groundedness <= 1
        assert 0 <= score.relevance <= 1
        assert 0 <= score.coherence <= 1
        assert 0 <= score.creativity <= 1
        assert 0 <= score.safety <= 1

    @pytest.mark.asyncio
    async def test_evaluate_batch(self):
        """Test evaluate_batch processes multiple candidates."""
        evaluator = QualityEvaluator(tier="free")
        candidates = [
            CandidateResult(idx=0, content="First candidate response. It is good."),
            CandidateResult(idx=1, content="Second candidate response with more detail. Therefore it is better."),
            CandidateResult(idx=2, content="Third candidate. Short."),
        ]

        scores = await evaluator.evaluate_batch(candidates, context=None)

        assert len(scores) == 3
        assert all(isinstance(s, QualityScore) for s in scores)

    def test_coherence_heuristic_short_text(self):
        """Test coherence heuristic for short text (single sentence)."""
        evaluator = QualityEvaluator(tier="free")

        score = evaluator._compute_coherence_heuristic("Short.")
        assert score == 0.4  # Single sentence = 0.4

    def test_coherence_heuristic_long_text(self):
        """Test coherence heuristic for longer text with multiple sentences."""
        evaluator = QualityEvaluator(tier="free")

        text = "First sentence with some content. Second sentence follows. Third sentence with more words. Therefore, it has good coherence."
        score = evaluator._compute_coherence_heuristic(text)

        assert score > 0.4  # Multiple sentences should score higher
        assert score <= 1.0

    def test_coherence_heuristic_with_markers(self):
        """Test coherence heuristic gives bonus for transition markers."""
        evaluator = QualityEvaluator(tier="free")

        text_no_markers = "This is a sentence. Another sentence here. More content follows."
        text_with_markers = "This is a sentence. However, another point arises. Therefore, this follows."

        score_no = evaluator._compute_coherence_heuristic(text_no_markers)
        score_with = evaluator._compute_coherence_heuristic(text_with_markers)

        # Markers should increase score
        assert score_with >= score_no

    def test_creativity_heuristic_diverse_text(self):
        """Test creativity heuristic for diverse vocabulary."""
        evaluator = QualityEvaluator(tier="free")

        text = "The quick brown fox jumps over lazy dog while exploring unique territory"
        score = evaluator._compute_creativity_heuristic(text)

        # High vocabulary diversity should score well
        assert score > 0.5
        assert score <= 1.0

    def test_creativity_heuristic_repetitive_text(self):
        """Test creativity heuristic for repetitive text."""
        evaluator = QualityEvaluator(tier="free")

        text = "the the the the the the the the the the"
        score = evaluator._compute_creativity_heuristic(text)

        # Low vocabulary diversity
        # TTR = 1/10 = 0.1, scaled = 0.15
        assert score < 0.5

    def test_creativity_heuristic_with_markers(self):
        """Test creativity heuristic with creative markers."""
        evaluator = QualityEvaluator(tier="free")

        text = "Imagine a unique vision of unexpected transformation with innovative approach"
        score = evaluator._compute_creativity_heuristic(text)

        # Creative markers should boost score
        assert score > 0.5

    @pytest.mark.asyncio
    async def test_safety_check_safe_text(self):
        """Test safety check for safe content."""
        evaluator = QualityEvaluator(tier="free")

        score = await evaluator._safety_check("This is a beautiful scene with great cinematography.")
        assert score == 1.0

    @pytest.mark.asyncio
    async def test_safety_check_unsafe_text(self):
        """Test safety check detects unsafe patterns."""
        evaluator = QualityEvaluator(tier="free")

        # Contains unsafe pattern
        score = await evaluator._safety_check("How to hack into systems and exploit vulnerabilities")
        assert score < 1.0
        assert score == 0.5  # Two violations: hack, exploit -> 1.0 - 0.5 = 0.5

    @pytest.mark.asyncio
    async def test_groundedness_with_sources(self):
        """Test groundedness scoring with context sources."""
        evaluator = QualityEvaluator(tier="free")

        # Mock context with sources
        class MockSource:
            def __init__(self, title, content=""):
                self.title = title
                self.content = content

        class MockContext:
            def __init__(self):
                self.notebooklm_sources = [
                    MockSource("Bong Joon-ho Style Guide"),
                    MockSource("Korean Cinema Analysis"),
                ]
                self.query = "test"

        # Text mentions source title
        text = "According to bong joon-ho style guide, the composition should be balanced."
        score = await evaluator._check_groundedness(text, MockContext())

        assert score > 0.3  # Should have some grounding

    @pytest.mark.asyncio
    async def test_groundedness_no_context(self):
        """Test groundedness returns neutral when no context."""
        evaluator = QualityEvaluator(tier="free")

        score = await evaluator._check_groundedness("Any text", context=None)
        assert score == 0.5  # Neutral

    @pytest.mark.asyncio
    async def test_relevance_without_context(self):
        """Test relevance computation without context."""
        evaluator = QualityEvaluator(tier="free")

        score = await evaluator._compute_relevance("text", context=None)
        assert score == 0.5  # Neutral without context


class TestGetQualityEvaluator:
    """Test evaluator factory function."""

    def test_get_quality_evaluator_free(self):
        """Test get_quality_evaluator returns free tier."""
        evaluator = get_quality_evaluator(tier="free")
        assert evaluator.tier == "free"
        assert evaluator.use_llm_judge is False

    def test_get_quality_evaluator_premium(self):
        """Test get_quality_evaluator returns premium tier."""
        evaluator = get_quality_evaluator(tier="premium")
        assert evaluator.tier == "premium"
        assert evaluator.use_llm_judge is True

    def test_get_quality_evaluator_dev(self):
        """Test get_quality_evaluator returns dev tier."""
        evaluator = get_quality_evaluator(tier="dev")
        assert evaluator.tier == "dev"
        assert evaluator.use_llm_judge is True


class TestLLMJudge:
    """Test LLM-as-Judge features (premium/dev tier)."""

    @pytest.mark.asyncio
    async def test_llm_judge_creativity_fallback(self):
        """Test LLM creativity falls back to heuristic when LLM unavailable."""
        evaluator = QualityEvaluator(use_llm_judge=True, tier="premium")

        # Without mocking, it should fall back to heuristic (no generate_with_gemini)
        score = await evaluator._llm_judge_creativity("Creative unique imaginative text with diverse vocabulary")

        # Should fall back to heuristic method
        assert 0 <= score <= 1

    @pytest.mark.asyncio
    async def test_llm_judge_coherence_fallback(self):
        """Test LLM coherence falls back to heuristic when LLM unavailable."""
        evaluator = QualityEvaluator(use_llm_judge=True, tier="premium")

        # Without mocking, it should fall back to heuristic
        score = await evaluator._llm_judge_coherence("First sentence. Second sentence. Therefore third.")

        # Should fall back to heuristic method
        assert 0 <= score <= 1

    @pytest.mark.asyncio
    async def test_premium_evaluate_uses_llm_methods(self):
        """Test premium tier calls LLM judge methods."""
        evaluator = QualityEvaluator(use_llm_judge=True, tier="premium")
        candidate = CandidateResult(idx=0, content="Test content with multiple sentences. It should be evaluated.")

        with patch.object(evaluator, '_llm_judge_creativity', new_callable=AsyncMock) as mock_creativity, \
             patch.object(evaluator, '_llm_judge_coherence', new_callable=AsyncMock) as mock_coherence:

            mock_creativity.return_value = 0.8
            mock_coherence.return_value = 0.9

            score = await evaluator.evaluate(candidate, context=None)

            # LLM judge should be called for premium tier
            mock_creativity.assert_called_once()
            mock_coherence.assert_called_once()
            assert score.creativity == 0.8
            assert score.coherence == 0.9

    @pytest.mark.asyncio
    async def test_free_tier_no_llm(self):
        """Test free tier does not call LLM judge methods."""
        evaluator = QualityEvaluator(use_llm_judge=False, tier="free")
        candidate = CandidateResult(idx=0, content="Test content with multiple sentences. It should be evaluated.")

        with patch.object(evaluator, '_llm_judge_creativity', new_callable=AsyncMock) as mock_creativity, \
             patch.object(evaluator, '_llm_judge_coherence', new_callable=AsyncMock) as mock_coherence:

            score = await evaluator.evaluate(candidate, context=None)

            # LLM judge should NOT be called for free tier
            mock_creativity.assert_not_called()
            mock_coherence.assert_not_called()
            # Should use heuristics
            assert 0 <= score.creativity <= 1
            assert 0 <= score.coherence <= 1


class TestParseScore:
    """Test score parsing utility."""

    def test_parse_valid_decimal(self):
        """Test parsing valid decimal string."""
        evaluator = QualityEvaluator()
        assert evaluator._parse_score("0.85") == 0.85
        assert evaluator._parse_score("0.5") == 0.5
        assert evaluator._parse_score("1.0") == 1.0

    def test_parse_integer(self):
        """Test parsing integer as score."""
        evaluator = QualityEvaluator()
        assert evaluator._parse_score("1") == 1.0
        assert evaluator._parse_score("0") == 0.0

    def test_parse_with_text(self):
        """Test parsing number from text."""
        evaluator = QualityEvaluator()
        assert evaluator._parse_score("The score is 0.75") == 0.75
        assert evaluator._parse_score("Rating: 0.9/1.0") == 0.9

    def test_parse_invalid(self):
        """Test parsing invalid input returns default."""
        evaluator = QualityEvaluator()
        assert evaluator._parse_score("no numbers") == 0.5
        assert evaluator._parse_score("") == 0.5

    def test_parse_clamps_value(self):
        """Test parsing clamps values to 0-1 range."""
        evaluator = QualityEvaluator()
        assert evaluator._parse_score("1.5") == 1.0  # Clamped to 1.0
        assert evaluator._parse_score("-0.5") == 0.5  # No match, returns 0.5
