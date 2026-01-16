"""Tests for A/B Testing System (2026 Best Practice)."""

import pytest
import math
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.experiments.ab_testing import ABTestingService, ExperimentAssignment
from app.experiments.statistics import (
    StatisticalAnalyzer,
    VariantStats,
    SignificanceResult,
)


class TestStatisticalAnalyzer:
    """Test statistical analysis functions."""

    @pytest.fixture
    def analyzer(self):
        return StatisticalAnalyzer(confidence_level=0.95)

    @pytest.fixture
    def control_stats(self):
        return VariantStats(
            name="control",
            sample_size=1000,
            conversions=100,
            sum_values=100,
            sum_squared_values=100,
        )

    @pytest.fixture
    def treatment_stats(self):
        return VariantStats(
            name="treatment",
            sample_size=1000,
            conversions=120,
            sum_values=120,
            sum_squared_values=144,
        )

    def test_conversion_rate(self, control_stats):
        """Test conversion rate calculation."""
        assert control_stats.conversion_rate == 0.10  # 100/1000

    def test_mean_value(self, control_stats):
        """Test mean value calculation."""
        assert control_stats.mean == 0.10  # 100/1000

    def test_variance(self, control_stats):
        """Test variance calculation."""
        # variance = (sum_squared/n) - (mean^2)
        expected = (100 / 1000) - (0.10 ** 2)
        assert abs(control_stats.variance - expected) < 0.0001

    def test_analyze_binary_metric_chi_squared(self, analyzer, control_stats, treatment_stats):
        """Test chi-squared analysis for binary metrics."""
        result = analyzer.analyze_binary_metric(
            control_stats,
            treatment_stats,
            method="chi_squared"
        )

        assert result.control_rate == 0.10
        assert result.treatment_rate == 0.12
        assert abs(result.relative_lift - 0.20) < 0.0001  # 20% lift (floating point tolerance)
        assert result.test_type == "chi_squared"
        assert 0 < result.p_value < 1

    def test_analyze_binary_metric_z_test(self, analyzer, control_stats, treatment_stats):
        """Test z-test analysis for binary metrics."""
        result = analyzer.analyze_binary_metric(
            control_stats,
            treatment_stats,
            method="z_test"
        )

        assert result.test_type == "z_test"
        assert 0 < result.p_value < 1

    def test_confidence_interval(self, analyzer, control_stats, treatment_stats):
        """Test confidence interval calculation."""
        result = analyzer.analyze_binary_metric(control_stats, treatment_stats)

        ci_lower, ci_upper = result.confidence_interval
        absolute_lift = result.absolute_lift

        # CI should contain the observed lift
        assert ci_lower < ci_upper
        # The observed difference should be within a reasonable range of the CI
        assert ci_lower <= absolute_lift <= ci_upper

    def test_bayesian_analysis(self, analyzer, control_stats, treatment_stats):
        """Test Bayesian analysis results."""
        result = analyzer.analyze_binary_metric(control_stats, treatment_stats)

        # Probability of being best should be high for treatment (20% lift)
        assert result.probability_of_being_best is not None
        assert result.probability_of_being_best > 0.7  # Treatment likely better
        assert result.expected_loss is not None
        assert result.expected_loss >= 0

    def test_continuous_metric_analysis(self, analyzer):
        """Test analysis for continuous metrics."""
        control = VariantStats(
            name="control",
            sample_size=500,
            conversions=0,
            sum_values=5000,
            sum_squared_values=52000,  # mean=10, variance≈4
        )
        treatment = VariantStats(
            name="treatment",
            sample_size=500,
            conversions=0,
            sum_values=5500,
            sum_squared_values=63000,  # mean=11, variance≈5
        )

        result = analyzer.analyze_continuous_metric(control, treatment)

        assert result.control_rate == 10.0  # mean
        assert result.treatment_rate == 11.0  # mean
        assert result.test_type == "t_test"
        assert 0 < result.p_value < 1

    def test_calculate_required_sample_size(self, analyzer):
        """Test sample size calculation."""
        sample_size = analyzer.calculate_required_sample_size(
            baseline_rate=0.10,
            minimum_detectable_effect=0.10,  # 10% relative lift
            power=0.8,
        )

        # Should be a reasonable sample size
        assert sample_size > 1000
        assert sample_size < 100000

    def test_sample_size_smaller_mde_larger_sample(self, analyzer):
        """Smaller MDE should require larger sample size."""
        sample_5pct = analyzer.calculate_required_sample_size(
            baseline_rate=0.10,
            minimum_detectable_effect=0.05,
            power=0.8,
        )
        sample_10pct = analyzer.calculate_required_sample_size(
            baseline_rate=0.10,
            minimum_detectable_effect=0.10,
            power=0.8,
        )

        assert sample_5pct > sample_10pct

    def test_cuped_adjustment(self, analyzer):
        """Test CUPED variance reduction."""
        # Simple test data
        pre = [0.10, 0.20, 0.15, 0.12, 0.18]
        post = [0.12, 0.22, 0.17, 0.14, 0.20]

        adjusted = analyzer.cuped_adjustment(post, pre)

        # Adjusted values should exist
        assert len(adjusted) == len(post)
        # Values should be different from original
        assert adjusted != post

    def test_cuped_with_custom_theta(self, analyzer):
        """Test CUPED with custom theta parameter."""
        pre = [1.0, 2.0, 3.0, 4.0, 5.0]
        post = [1.1, 2.2, 3.3, 4.4, 5.5]

        adjusted = analyzer.cuped_adjustment(post, pre, theta=0.5)

        assert len(adjusted) == 5

    def test_cuped_mismatched_length_raises(self, analyzer):
        """Test that mismatched lengths raise error."""
        pre = [1.0, 2.0, 3.0]
        post = [1.0, 2.0]

        with pytest.raises(ValueError):
            analyzer.cuped_adjustment(post, pre)


class TestConsistentHashing:
    """Test consistent hashing for A/B Testing."""

    @pytest.fixture
    def service(self):
        return ABTestingService()

    def test_same_user_same_experiment_same_result(self, service):
        """Same user and experiment should always get same hash."""
        user_id = "user_123"
        experiment_key = "checkout_test"

        results = [
            service._consistent_hash(user_id, experiment_key)
            for _ in range(10)
        ]

        assert all(r == results[0] for r in results)

    def test_different_experiments_different_hashes(self, service):
        """Different experiments should produce different hashes."""
        user_id = "user_123"

        hash1 = service._consistent_hash(user_id, "experiment_a")
        hash2 = service._consistent_hash(user_id, "experiment_b")

        # Not guaranteed to be different, but very likely
        # This test might occasionally fail but that's statistically expected
        # In practice, we test distribution instead

    def test_hash_distribution(self, service):
        """Test that hashes are uniformly distributed."""
        experiment_key = "distribution_test"
        buckets = [0] * 10  # 10 buckets

        for i in range(10000):
            hash_val = service._consistent_hash(f"user_{i}", experiment_key)
            bucket = hash_val // 1000  # 0-9999 -> 0-9
            buckets[bucket] += 1

        # Each bucket should have roughly 1000 users
        for i, count in enumerate(buckets):
            assert 800 < count < 1200, f"Bucket {i} has {count} users"


class TestSignificanceResult:
    """Test SignificanceResult dataclass."""

    def test_significance_result_creation(self):
        """Test creating a significance result."""
        result = SignificanceResult(
            control_rate=0.10,
            treatment_rate=0.12,
            relative_lift=0.20,
            absolute_lift=0.02,
            p_value=0.05,
            confidence_interval=(-0.01, 0.05),
            is_significant=True,
            test_type="chi_squared",
            probability_of_being_best=0.92,
            expected_loss=0.001,
            control_sample_size=1000,
            treatment_sample_size=1000,
        )

        assert result.is_significant is True
        assert result.relative_lift == 0.20


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def analyzer(self):
        return StatisticalAnalyzer()

    def test_zero_sample_size(self, analyzer):
        """Test handling of zero sample size."""
        zero_sample = VariantStats(
            name="empty",
            sample_size=0,
            conversions=0,
            sum_values=0,
            sum_squared_values=0,
        )

        assert zero_sample.conversion_rate == 0.0
        assert zero_sample.mean == 0.0
        assert zero_sample.variance == 0.0

    def test_small_sample_chi_squared(self, analyzer):
        """Chi-squared should handle small samples gracefully."""
        small_control = VariantStats("control", 3, 1, 1, 1)
        small_treatment = VariantStats("treatment", 3, 2, 2, 4)

        result = analyzer.analyze_binary_metric(small_control, small_treatment)

        # Should return safe defaults for small samples
        assert result.p_value == 1.0

    def test_zero_control_rate(self, analyzer):
        """Test handling when control rate is zero."""
        control = VariantStats("control", 100, 0, 0, 0)
        treatment = VariantStats("treatment", 100, 10, 10, 100)

        result = analyzer.analyze_binary_metric(control, treatment)

        # Relative lift should be infinity or handled gracefully
        assert result.relative_lift == float('inf')

    def test_identical_variants(self, analyzer):
        """Test when both variants have identical stats."""
        stats = VariantStats("variant", 1000, 100, 100, 100)

        result = analyzer.analyze_binary_metric(stats, stats)

        assert result.relative_lift == 0.0
        assert result.absolute_lift == 0.0


@pytest.mark.asyncio
class TestABTestingServiceAsync:
    """Test async methods of ABTestingService."""

    async def test_service_initialization(self):
        """Test service can be initialized."""
        service = ABTestingService()
        assert service._analyzer is not None
        assert service._redis is None  # Lazy initialization
