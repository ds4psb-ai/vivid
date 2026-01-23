"""Tests for P7 ThresholdTuner Service.

Tests for automatic threshold optimization.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

# Skip all tests if dependencies unavailable
try:
    from app.services.threshold_tuner import (
        ThresholdTuner,
        get_threshold_tuner,
    )
    from app.schemas.self_correction_schemas import (
        ThresholdConfig,
        ThresholdTuningResult,
        MisclassificationReport,
        MisclassificationType,
    )
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    ThresholdTuner = None
    ThresholdConfig = None
    ThresholdTuningResult = None


pytestmark = pytest.mark.skipif(
    not DEPS_AVAILABLE,
    reason=f"Dependencies not available: {IMPORT_ERROR if not DEPS_AVAILABLE else ''}"
)


class TestThresholdTunerInit:
    """Tests for ThresholdTuner initialization."""

    def test_default_init(self):
        """Should initialize with default config."""
        tuner = ThresholdTuner()

        config = tuner.get_current_config()
        assert config.semantic_threshold == 0.7
        assert config.skip_confidence_threshold == 0.85
        assert config.reranker_min_score == 0.5
        assert config.crag_relevance_threshold == 0.6
        assert config.llm_fallback_threshold == 0.5

    def test_custom_config_init(self):
        """Should initialize with custom config."""
        custom_config = ThresholdConfig(
            semantic_threshold=0.8,
            skip_confidence_threshold=0.9,
        )
        tuner = ThresholdTuner(current_config=custom_config)

        config = tuner.get_current_config()
        assert config.semantic_threshold == 0.8
        assert config.skip_confidence_threshold == 0.9

    def test_singleton_pattern(self):
        """Should return singleton instance."""
        tuner1 = get_threshold_tuner()
        tuner2 = get_threshold_tuner()

        assert tuner1 is tuner2


class TestThresholdConfig:
    """Tests for ThresholdConfig schema."""

    def test_default_config(self):
        """Should create config with defaults."""
        config = ThresholdConfig()

        assert config.semantic_threshold == 0.7
        assert config.skip_confidence_threshold == 0.85
        assert config.reranker_min_score == 0.5
        assert config.crag_relevance_threshold == 0.6
        assert config.llm_fallback_threshold == 0.5

    def test_custom_config(self):
        """Should create config with custom values."""
        config = ThresholdConfig(
            semantic_threshold=0.75,
            skip_confidence_threshold=0.88,
            reranker_min_score=0.55,
            crag_relevance_threshold=0.65,
            llm_fallback_threshold=0.55,
        )

        assert config.semantic_threshold == 0.75
        assert config.skip_confidence_threshold == 0.88

    def test_config_validation(self):
        """Should validate threshold ranges."""
        # Should not allow values > 1.0
        with pytest.raises(ValueError):
            ThresholdConfig(semantic_threshold=1.5)

        # Should not allow negative values
        with pytest.raises(ValueError):
            ThresholdConfig(skip_confidence_threshold=-0.1)

    def test_config_model_dump(self):
        """Should serialize to dict."""
        config = ThresholdConfig()

        data = config.model_dump()

        assert "semantic_threshold" in data
        assert "skip_confidence_threshold" in data
        assert data["semantic_threshold"] == 0.7


class TestThresholdTuningResult:
    """Tests for ThresholdTuningResult schema."""

    def test_result_with_changes(self):
        """Should create result with changes."""
        old_config = ThresholdConfig()
        new_config = ThresholdConfig(
            semantic_threshold=0.75,
            skip_confidence_threshold=0.88,
        )

        result = ThresholdTuningResult(
            previous_config=old_config,
            new_config=new_config,
            changes={
                "semantic_threshold": {"old": 0.7, "new": 0.75, "delta": 0.05},
                "skip_confidence_threshold": {"old": 0.85, "new": 0.88, "delta": 0.03},
            },
            rationale="Increased thresholds due to high negative feedback rate",
            expected_improvement={
                "skip_negative_rate": -0.05,
                "accuracy": 0.03,
            },
            experiment_key="p7_threshold_tuning_20260123",
        )

        assert len(result.changes) == 2
        assert result.changes["semantic_threshold"]["delta"] == 0.05
        assert result.experiment_key == "p7_threshold_tuning_20260123"

    def test_result_no_changes(self):
        """Should create result with no changes."""
        config = ThresholdConfig()

        result = ThresholdTuningResult(
            previous_config=config,
            new_config=config,
            changes={},
            rationale="No changes needed",
            expected_improvement={},
        )

        assert len(result.changes) == 0
        assert result.experiment_key is None


class TestCalculateAdjustments:
    """Tests for threshold adjustment calculation."""

    def test_adjust_for_high_skip_negative(self):
        """Should increase skip threshold when negative rate is high."""
        tuner = ThresholdTuner()

        metrics = {
            "skip_negative_rate": 0.15,  # 15% > 5% target
            "crag_trigger_rate": 0.05,
            "crag_success_rate": 0.75,
            "low_conf_failure_rate": 0.10,
        }

        adjustments = tuner._calculate_adjustments(metrics)

        assert "skip_confidence_threshold" in adjustments
        assert adjustments["skip_confidence_threshold"] > 0

    def test_adjust_for_high_crag_trigger(self):
        """Should increase semantic threshold when CRAG rate is high."""
        tuner = ThresholdTuner()

        metrics = {
            "skip_negative_rate": 0.03,
            "crag_trigger_rate": 0.25,  # 25% > 8% * 1.5 = 12%
            "crag_success_rate": 0.75,
            "low_conf_failure_rate": 0.10,
        }

        adjustments = tuner._calculate_adjustments(metrics)

        assert "semantic_threshold" in adjustments
        assert adjustments["semantic_threshold"] > 0

    def test_adjust_for_low_crag_success(self):
        """Should decrease CRAG threshold when success rate is low."""
        tuner = ThresholdTuner()

        metrics = {
            "skip_negative_rate": 0.03,
            "crag_trigger_rate": 0.10,
            "crag_success_rate": 0.50,  # 50% < 75% target
            "low_conf_failure_rate": 0.10,
        }

        adjustments = tuner._calculate_adjustments(metrics)

        assert "crag_relevance_threshold" in adjustments
        assert adjustments["crag_relevance_threshold"] < 0

    def test_adjust_for_high_low_conf_failure(self):
        """Should increase LLM fallback threshold when low conf failures are high."""
        tuner = ThresholdTuner()

        metrics = {
            "skip_negative_rate": 0.03,
            "crag_trigger_rate": 0.08,
            "crag_success_rate": 0.75,
            "low_conf_failure_rate": 0.25,  # 25% > 20%
        }

        adjustments = tuner._calculate_adjustments(metrics)

        assert "llm_fallback_threshold" in adjustments
        assert adjustments["llm_fallback_threshold"] > 0

    def test_no_adjustments_optimal_metrics(self):
        """Should make minimal adjustments when metrics are optimal."""
        tuner = ThresholdTuner()

        metrics = {
            "skip_negative_rate": 0.02,  # Low, may slightly decrease
            "crag_trigger_rate": 0.06,  # Within range
            "crag_success_rate": 0.85,  # Good
            "low_conf_failure_rate": 0.10,  # Normal
        }

        adjustments = tuner._calculate_adjustments(metrics)

        # Should have small or negative adjustments
        for key, value in adjustments.items():
            assert abs(value) <= tuner.MAX_ADJUSTMENT


class TestApplyAdjustments:
    """Tests for applying adjustments to config."""

    def test_apply_positive_adjustments(self):
        """Should increase thresholds."""
        tuner = ThresholdTuner()

        adjustments = {
            "semantic_threshold": 0.05,
            "skip_confidence_threshold": 0.03,
        }

        new_config = tuner._apply_adjustments(adjustments)

        assert new_config.semantic_threshold == 0.75  # 0.7 + 0.05
        assert new_config.skip_confidence_threshold == 0.88  # 0.85 + 0.03

    def test_apply_negative_adjustments(self):
        """Should decrease thresholds."""
        tuner = ThresholdTuner()

        adjustments = {
            "crag_relevance_threshold": -0.05,
        }

        new_config = tuner._apply_adjustments(adjustments)

        assert new_config.crag_relevance_threshold == 0.55  # 0.6 - 0.05

    def test_clamp_to_max(self):
        """Should clamp values to maximum."""
        tuner = ThresholdTuner()
        tuner._current_config = ThresholdConfig(semantic_threshold=0.92)

        adjustments = {
            "semantic_threshold": 0.10,  # Would go to 1.02
        }

        new_config = tuner._apply_adjustments(adjustments)

        assert new_config.semantic_threshold <= tuner.MAX_THRESHOLD

    def test_clamp_to_min(self):
        """Should clamp values to minimum."""
        tuner = ThresholdTuner()
        tuner._current_config = ThresholdConfig(crag_relevance_threshold=0.35)

        adjustments = {
            "crag_relevance_threshold": -0.10,  # Would go to 0.25
        }

        new_config = tuner._apply_adjustments(adjustments)

        assert new_config.crag_relevance_threshold >= tuner.MIN_THRESHOLD


class TestCalculateChanges:
    """Tests for calculating changes between configs."""

    def test_calculate_changes_same_config(self):
        """Should return empty dict for same config."""
        tuner = ThresholdTuner()
        config = ThresholdConfig()

        changes = tuner._calculate_changes(config, config)

        assert changes == {}

    def test_calculate_changes_different_config(self):
        """Should return detailed changes."""
        tuner = ThresholdTuner()
        old_config = ThresholdConfig()
        new_config = ThresholdConfig(
            semantic_threshold=0.75,
            skip_confidence_threshold=0.88,
        )

        changes = tuner._calculate_changes(old_config, new_config)

        assert "semantic_threshold" in changes
        assert changes["semantic_threshold"]["old"] == 0.7
        assert changes["semantic_threshold"]["new"] == 0.75
        assert changes["semantic_threshold"]["delta"] == 0.05

        assert "skip_confidence_threshold" in changes


class TestGenerateRationale:
    """Tests for rationale generation."""

    def test_generate_rationale_no_changes(self):
        """Should generate rationale for no changes."""
        tuner = ThresholdTuner()

        rationale = tuner._generate_rationale({}, None)

        assert "No threshold changes" in rationale

    def test_generate_rationale_skip_increase(self):
        """Should explain skip threshold increase."""
        tuner = ThresholdTuner()

        changes = {
            "skip_confidence_threshold": {"old": 0.85, "new": 0.88, "delta": 0.03},
        }

        rationale = tuner._generate_rationale(changes, None)

        assert "검색 생략" in rationale or "skip" in rationale.lower()

    def test_generate_rationale_semantic_increase(self):
        """Should explain semantic threshold increase."""
        tuner = ThresholdTuner()

        changes = {
            "semantic_threshold": {"old": 0.7, "new": 0.75, "delta": 0.05},
        }

        rationale = tuner._generate_rationale(changes, None)

        assert "시맨틱" in rationale or "semantic" in rationale.lower() or "CRAG" in rationale


class TestEstimateImprovement:
    """Tests for improvement estimation."""

    def test_estimate_improvement_no_changes(self):
        """Should return empty dict for no changes."""
        tuner = ThresholdTuner()

        expected = tuner._estimate_improvement({}, None)

        assert expected == {}

    def test_estimate_improvement_with_changes(self):
        """Should estimate improvements for changes."""
        tuner = ThresholdTuner()

        changes = {
            "skip_confidence_threshold": {"old": 0.85, "new": 0.88, "delta": 0.03},
            "semantic_threshold": {"old": 0.7, "new": 0.75, "delta": 0.05},
        }

        expected = tuner._estimate_improvement(changes, None)

        assert "skip_negative_rate" in expected
        assert expected["skip_negative_rate"] < 0  # Expected to decrease


class TestApplyConfig:
    """Tests for applying new config."""

    def test_apply_config(self):
        """Should update current config."""
        tuner = ThresholdTuner()
        new_config = ThresholdConfig(
            semantic_threshold=0.8,
            skip_confidence_threshold=0.9,
        )

        tuner.apply_config(new_config)

        current = tuner.get_current_config()
        assert current.semantic_threshold == 0.8
        assert current.skip_confidence_threshold == 0.9


class TestOptimizeThresholdsMocked:
    """Tests for optimize_thresholds with mocked database."""

    @pytest.mark.asyncio
    async def test_optimize_with_report(self):
        """Should optimize using provided report."""
        tuner = ThresholdTuner()

        mock_db = AsyncMock()

        report = MisclassificationReport(
            period_days=7,
            total_responses=1000,
            total_with_feedback=100,
            total_misclassified=15,
            misclassification_rate=0.15,
            misclassifications_by_type={},
            accuracy_by_query_type={},
            crag_trigger_rate=0.20,  # High - should increase semantic threshold
            crag_success_rate=0.75,
            skip_retrieval_negative_rate=0.12,  # High - should increase skip threshold
        )

        new_config = await tuner.optimize_thresholds(mock_db, report=report)

        # Should have increased thresholds
        assert new_config.semantic_threshold >= tuner._current_config.semantic_threshold
        assert new_config.skip_confidence_threshold >= tuner._current_config.skip_confidence_threshold

    @pytest.mark.asyncio
    async def test_optimize_without_report(self):
        """Should gather metrics and optimize."""
        tuner = ThresholdTuner()

        mock_db = AsyncMock()

        # Mock _gather_metrics
        with patch.object(tuner, '_gather_metrics', return_value={
            "skip_negative_rate": 0.05,
            "crag_trigger_rate": 0.08,
            "crag_success_rate": 0.80,
            "low_conf_failure_rate": 0.10,
        }):
            new_config = await tuner.optimize_thresholds(mock_db)

        assert isinstance(new_config, ThresholdConfig)


class TestRunFullTuningMocked:
    """Tests for run_full_tuning with mocked database."""

    @pytest.mark.asyncio
    async def test_full_tuning_without_experiment(self):
        """Should run tuning without creating experiment."""
        tuner = ThresholdTuner()

        mock_db = AsyncMock()

        report = MisclassificationReport(
            period_days=7,
            total_responses=1000,
            total_with_feedback=100,
            total_misclassified=10,
            misclassification_rate=0.10,
            misclassifications_by_type={},
            accuracy_by_query_type={},
            crag_trigger_rate=0.08,
            crag_success_rate=0.80,
            skip_retrieval_negative_rate=0.05,
        )

        result = await tuner.run_full_tuning(
            db=mock_db,
            report=report,
            auto_experiment=False,  # Don't create experiment
        )

        assert isinstance(result, ThresholdTuningResult)
        assert result.experiment_key is None

    @pytest.mark.asyncio
    async def test_full_tuning_generates_rationale(self):
        """Should generate rationale for changes."""
        tuner = ThresholdTuner()

        mock_db = AsyncMock()

        report = MisclassificationReport(
            period_days=7,
            total_responses=1000,
            total_with_feedback=100,
            total_misclassified=20,
            misclassification_rate=0.20,
            misclassifications_by_type={},
            accuracy_by_query_type={},
            crag_trigger_rate=0.25,  # High
            crag_success_rate=0.50,  # Low
            skip_retrieval_negative_rate=0.15,  # High
        )

        result = await tuner.run_full_tuning(
            db=mock_db,
            report=report,
            auto_experiment=False,
        )

        assert result.rationale != ""
        assert len(result.changes) > 0
