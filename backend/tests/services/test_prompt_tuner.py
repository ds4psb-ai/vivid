"""Tests for P7 PromptTuner Service.

Tests for LLM-based prompt improvement.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

# Skip all tests if dependencies unavailable
try:
    from app.services.prompt_tuner import (
        PromptTuner,
        get_prompt_tuner,
        ANALYSIS_PROMPT,
        IMPROVEMENT_PROMPT,
    )
    from app.schemas.self_correction_schemas import (
        MisclassifiedQuery,
        MisclassificationType,
        PromptIssue,
        PromptIssueType,
        PromptAnalysis,
        PromptTuningResult,
    )
    from app.rag.llm_classifier import CLASSIFICATION_PROMPT
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    PromptTuner = None
    PromptIssue = None
    PromptIssueType = None


pytestmark = pytest.mark.skipif(
    not DEPS_AVAILABLE,
    reason=f"Dependencies not available: {IMPORT_ERROR if not DEPS_AVAILABLE else ''}"
)


class TestPromptTunerInit:
    """Tests for PromptTuner initialization."""

    def test_default_init(self):
        """Should initialize with default model."""
        tuner = PromptTuner()

        assert tuner.model_name == "gemini-2.0-flash"
        assert tuner._current_prompt == CLASSIFICATION_PROMPT

    def test_custom_model_init(self):
        """Should initialize with custom model."""
        tuner = PromptTuner(model_name="gemini-2.0-pro")

        assert tuner.model_name == "gemini-2.0-pro"

    def test_singleton_pattern(self):
        """Should return singleton instance."""
        tuner1 = get_prompt_tuner()
        tuner2 = get_prompt_tuner()

        assert tuner1 is tuner2

    def test_set_current_prompt(self):
        """Should update current prompt."""
        tuner = PromptTuner()
        new_prompt = "New classification prompt"

        tuner.set_current_prompt(new_prompt)

        assert tuner.get_current_prompt() == new_prompt


class TestPromptIssue:
    """Tests for PromptIssue schema."""

    def test_boundary_ambiguity_issue(self):
        """Should create boundary ambiguity issue."""
        issue = PromptIssue(
            issue_type=PromptIssueType.BOUNDARY_AMBIGUITY,
            severity="high",
            description="Unclear boundary between creative and domain_specific",
            affected_query_types=["creative", "domain_specific"],
            example_queries=["Write a scene like Bong Joon-ho"],
            suggested_fix="Add examples for queries that combine creativity with domain knowledge",
        )

        assert issue.issue_type == PromptIssueType.BOUNDARY_AMBIGUITY
        assert issue.severity == "high"
        assert "creative" in issue.affected_query_types
        assert len(issue.example_queries) == 1

    def test_missing_examples_issue(self):
        """Should create missing examples issue."""
        issue = PromptIssue(
            issue_type=PromptIssueType.MISSING_EXAMPLES,
            severity="medium",
            description="Lack of Korean film examples",
            affected_query_types=["domain_specific"],
            suggested_fix="Add Korean director and film examples",
        )

        assert issue.issue_type == PromptIssueType.MISSING_EXAMPLES


class TestPromptAnalysis:
    """Tests for PromptAnalysis schema."""

    def test_analysis_with_issues(self):
        """Should create analysis with identified issues."""
        issues = [
            PromptIssue(
                issue_type=PromptIssueType.BOUNDARY_AMBIGUITY,
                severity="high",
                description="Test issue 1",
                affected_query_types=["creative", "domain_specific"],
                suggested_fix="Fix 1",
            ),
            PromptIssue(
                issue_type=PromptIssueType.MISSING_EXAMPLES,
                severity="medium",
                description="Test issue 2",
                affected_query_types=["recency_required"],
                suggested_fix="Fix 2",
            ),
        ]

        analysis = PromptAnalysis(
            current_prompt="Test prompt",
            issues=issues,
            overall_score=0.7,
            improvement_potential=0.15,
        )

        assert len(analysis.issues) == 2
        assert analysis.overall_score == 0.7
        assert analysis.improvement_potential == 0.15


class TestPromptTuningResult:
    """Tests for PromptTuningResult schema."""

    def test_result_with_experiment(self):
        """Should create result with experiment info."""
        analysis = PromptAnalysis(
            current_prompt="Current",
            issues=[],
            overall_score=0.8,
            improvement_potential=0.1,
        )

        result = PromptTuningResult(
            analysis=analysis,
            improved_prompt="Improved prompt text",
            changes_summary="Added boundary examples",
            expected_improvement=0.10,
            experiment_key="p7_prompt_tuning_20260123",
            variant_name="treatment",
        )

        assert result.improved_prompt == "Improved prompt text"
        assert result.expected_improvement == 0.10
        assert result.experiment_key == "p7_prompt_tuning_20260123"
        assert result.variant_name == "treatment"

    def test_result_without_experiment(self):
        """Should create result without experiment."""
        analysis = PromptAnalysis(
            current_prompt="Current",
            issues=[],
            overall_score=0.95,
            improvement_potential=0.02,
        )

        result = PromptTuningResult(
            analysis=analysis,
            improved_prompt="Current",
            changes_summary="No changes needed",
            expected_improvement=0.0,
        )

        assert result.experiment_key is None
        assert result.variant_name is None


class TestBuildFailureExamples:
    """Tests for failure example building."""

    def test_build_examples_empty(self):
        """Should handle empty failure list."""
        tuner = PromptTuner()

        examples = tuner._build_failure_examples([])

        assert examples == ""

    def test_build_examples_with_failures(self):
        """Should format failure examples."""
        tuner = PromptTuner()

        failures = [
            MisclassifiedQuery(
                response_id=uuid4(),
                query="Test query 1",
                query_hash="hash1",
                predicted_type="simple_factual",
                confidence=0.85,
                classifier_used="semantic_router",
                strategy_used="direct_llm",
                retrieval_skipped=True,
                crag_triggered=False,
                latency_ms=50,
                avg_rating=2.0,
                negative_feedback_count=3,
                misclassification_type=MisclassificationType.SKIP_BUT_NEGATIVE,
                analysis_reason="검색이 필요했던 쿼리",
                created_at=datetime.utcnow(),
            ),
        ]

        examples = tuner._build_failure_examples(failures)

        assert "Test query 1" in examples
        assert "simple_factual" in examples
        assert "skip_but_negative" in examples


class TestBuildIssuesSummary:
    """Tests for issues summary building."""

    def test_build_summary_empty(self):
        """Should handle empty issues list."""
        tuner = PromptTuner()

        summary = tuner._build_issues_summary([])

        assert summary == ""

    def test_build_summary_with_issues(self):
        """Should format issues summary."""
        tuner = PromptTuner()

        issues = [
            PromptIssue(
                issue_type=PromptIssueType.BOUNDARY_AMBIGUITY,
                severity="high",
                description="Boundary problem",
                affected_query_types=["creative"],
                suggested_fix="Add examples",
            ),
        ]

        summary = tuner._build_issues_summary(issues)

        assert "boundary_ambiguity" in summary
        assert "high" in summary
        assert "Boundary problem" in summary


class TestBuildSpecificImprovements:
    """Tests for specific improvements building."""

    def test_improvements_for_boundary_ambiguity(self):
        """Should suggest boundary improvements."""
        tuner = PromptTuner()

        issues = [
            PromptIssue(
                issue_type=PromptIssueType.BOUNDARY_AMBIGUITY,
                severity="high",
                description="Boundary issue",
                affected_query_types=["creative", "domain_specific"],
                suggested_fix="Fix",
            ),
        ]

        improvements = tuner._build_specific_improvements(issues)

        assert "boundary" in improvements.lower() or "creative" in improvements.lower()

    def test_improvements_for_domain_gap(self):
        """Should suggest domain knowledge improvements."""
        tuner = PromptTuner()

        issues = [
            PromptIssue(
                issue_type=PromptIssueType.DOMAIN_GAP,
                severity="medium",
                description="Domain gap",
                affected_query_types=["domain_specific"],
                suggested_fix="Add domain knowledge",
            ),
        ]

        improvements = tuner._build_specific_improvements(issues)

        assert "domain" in improvements.lower() or "film" in improvements.lower()


class TestInferIssuesFromFailures:
    """Tests for issue inference from failures."""

    def test_infer_skip_but_negative_pattern(self):
        """Should infer boundary ambiguity from skip failures."""
        tuner = PromptTuner()

        # Create failures with high skip_but_negative rate
        failures = [
            MisclassifiedQuery(
                response_id=uuid4(),
                query=f"Test query {i}",
                query_hash=f"hash{i}",
                predicted_type="simple_factual",
                confidence=0.85,
                classifier_used="semantic_router",
                strategy_used="direct_llm",
                retrieval_skipped=True,
                crag_triggered=False,
                latency_ms=50,
                misclassification_type=MisclassificationType.SKIP_BUT_NEGATIVE,
                created_at=datetime.utcnow(),
            )
            for i in range(5)
        ]

        issues = tuner._infer_issues_from_failures(failures)

        # Should detect boundary ambiguity
        assert any(i.issue_type == PromptIssueType.BOUNDARY_AMBIGUITY for i in issues)

    def test_infer_crag_pattern(self):
        """Should infer domain gap from CRAG triggers."""
        tuner = PromptTuner()

        # Create failures with CRAG triggers
        failures = [
            MisclassifiedQuery(
                response_id=uuid4(),
                query=f"Test query {i}",
                query_hash=f"hash{i}",
                predicted_type="domain_specific",
                confidence=0.75,
                classifier_used="semantic_router",
                strategy_used="ensemble_rrf",
                retrieval_skipped=False,
                crag_triggered=True,
                latency_ms=300,
                misclassification_type=MisclassificationType.RETRIEVAL_BUT_CRAG,
                created_at=datetime.utcnow(),
            )
            for i in range(3)
        ]

        issues = tuner._infer_issues_from_failures(failures)

        # Should detect domain gap
        assert any(i.issue_type == PromptIssueType.DOMAIN_GAP for i in issues)


class TestAnalyzeFailuresMocked:
    """Tests for analyze_failures with mocked LLM."""

    @pytest.mark.asyncio
    async def test_analyze_failures_empty(self):
        """Should return empty list for no failures."""
        tuner = PromptTuner()

        issues = await tuner.analyze_failures([])

        assert issues == []

    @pytest.mark.asyncio
    async def test_analyze_failures_llm_error_fallback(self):
        """Should fallback to inference on LLM error."""
        tuner = PromptTuner()

        failures = [
            MisclassifiedQuery(
                response_id=uuid4(),
                query="Test query",
                query_hash="hash1",
                predicted_type="simple_factual",
                confidence=0.85,
                classifier_used="semantic_router",
                strategy_used="direct_llm",
                retrieval_skipped=True,
                crag_triggered=False,
                latency_ms=50,
                misclassification_type=MisclassificationType.SKIP_BUT_NEGATIVE,
                created_at=datetime.utcnow(),
            )
        ]

        # Mock LLM to raise error
        with patch.object(tuner, '_call_llm', side_effect=Exception("API Error")):
            issues = await tuner.analyze_failures(failures)

        # Should still return inferred issues
        assert isinstance(issues, list)


class TestGenerateImprovedPromptMocked:
    """Tests for generate_improved_prompt with mocked LLM."""

    @pytest.mark.asyncio
    async def test_generate_no_issues(self):
        """Should return current prompt when no issues."""
        tuner = PromptTuner()

        improved, summary, improvement = await tuner.generate_improved_prompt(
            current_prompt="Test prompt",
            issues=[],
        )

        assert improved == "Test prompt"
        assert summary == "No changes needed"
        assert improvement == 0.0

    @pytest.mark.asyncio
    async def test_generate_llm_error_fallback(self):
        """Should fallback to basic fixes on LLM error."""
        tuner = PromptTuner()
        original_prompt = tuner.get_current_prompt()

        issues = [
            PromptIssue(
                issue_type=PromptIssueType.BOUNDARY_AMBIGUITY,
                severity="high",
                description="Test issue",
                affected_query_types=["creative"],
                suggested_fix="Fix boundary",
            ),
        ]

        with patch.object(tuner, '_call_llm', side_effect=Exception("API Error")):
            improved, summary, improvement = await tuner.generate_improved_prompt(
                current_prompt=original_prompt,
                issues=issues,
            )

        # Should return basic fix result
        assert improved == original_prompt  # Basic fix returns current
        assert "basic" in summary.lower() or "fixes" in summary.lower()


class TestCleanJsonResponse:
    """Tests for JSON response cleaning."""

    def test_clean_plain_json(self):
        """Should return plain JSON as-is."""
        tuner = PromptTuner()

        json_text = '{"key": "value"}'
        cleaned = tuner._clean_json_response(json_text)

        assert cleaned == '{"key": "value"}'

    def test_clean_markdown_json(self):
        """Should strip markdown code blocks."""
        tuner = PromptTuner()

        json_text = '```json\n{"key": "value"}\n```'
        cleaned = tuner._clean_json_response(json_text)

        assert cleaned == '{"key": "value"}'

    def test_clean_with_whitespace(self):
        """Should strip whitespace."""
        tuner = PromptTuner()

        json_text = '  {"key": "value"}  '
        cleaned = tuner._clean_json_response(json_text)

        assert cleaned == '{"key": "value"}'


class TestParseAnalysisResponse:
    """Tests for analysis response parsing."""

    def test_parse_valid_response(self):
        """Should parse valid JSON response."""
        tuner = PromptTuner()

        response = '''
        {
            "overall_score": 0.75,
            "improvement_potential": 0.15,
            "issues": [
                {
                    "issue_type": "boundary_ambiguity",
                    "severity": "high",
                    "description": "Test issue",
                    "affected_query_types": ["creative"],
                    "suggested_fix": "Fix it"
                }
            ]
        }
        '''

        issues = tuner._parse_analysis_response(response)

        assert len(issues) == 1
        assert issues[0].issue_type == PromptIssueType.BOUNDARY_AMBIGUITY
        assert issues[0].severity == "high"

    def test_parse_invalid_response(self):
        """Should return empty list on invalid JSON."""
        tuner = PromptTuner()

        response = "Invalid JSON"
        issues = tuner._parse_analysis_response(response)

        assert issues == []


class TestParseImprovementResponse:
    """Tests for improvement response parsing."""

    def test_parse_valid_response(self):
        """Should parse valid improvement response."""
        tuner = PromptTuner()

        response = '''
        {
            "improved_prompt": "New improved prompt text",
            "changes_summary": "Added examples",
            "expected_improvement": 0.15
        }
        '''

        improved, summary, improvement = tuner._parse_improvement_response(response)

        assert improved == "New improved prompt text"
        assert summary == "Added examples"
        assert improvement == 0.15

    def test_parse_invalid_response(self):
        """Should return current prompt on invalid JSON."""
        tuner = PromptTuner()

        response = "Invalid JSON"
        improved, summary, improvement = tuner._parse_improvement_response(response)

        assert improved == tuner._current_prompt
        assert improvement == 0.0
