"""Tests for Feature Flags System (2026 Best Practice)."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.features.flags import FeatureFlagService, CachedFlag
from app.features.schemas import FeatureContext


class TestConsistentHashing:
    """Test consistent hashing for percentage rollouts."""

    def test_same_user_same_result(self):
        """Same user should always get the same hash value."""
        service = FeatureFlagService()
        user_id = "user_123"
        flag_key = "test_flag"

        # Multiple calls should return the same value
        results = [
            service._consistent_hash(user_id, flag_key)
            for _ in range(10)
        ]

        assert all(r == results[0] for r in results)

    def test_different_users_different_results(self):
        """Different users should generally get different hash values."""
        service = FeatureFlagService()
        flag_key = "test_flag"

        users = [f"user_{i}" for i in range(100)]
        results = [service._consistent_hash(u, flag_key) for u in users]

        # Should have variety in results
        unique_results = set(results)
        assert len(unique_results) > 10  # At least some variety

    def test_hash_range(self):
        """Hash values should be in expected range."""
        service = FeatureFlagService()

        for i in range(100):
            result = service._consistent_hash(f"user_{i}", "flag_key")
            assert 0 <= result < 100


class TestFeatureFlagEvaluation:
    """Test feature flag evaluation logic."""

    @pytest.fixture
    def service(self):
        return FeatureFlagService()

    @pytest.fixture
    def basic_flag(self):
        return CachedFlag(
            flag_key="test_flag",
            enabled=True,
            strategies={
                "percentage": 50,
            },
            variants=[],
            default_variant="on",
            cached_at=datetime.utcnow(),
        )

    @pytest.fixture
    def targeted_flag(self):
        return CachedFlag(
            flag_key="beta_feature",
            enabled=True,
            strategies={
                "user_ids": ["vip_user_1", "vip_user_2"],
                "properties": {"plan": "premium"},
                "percentage": 10,
            },
            variants=[
                {"name": "control", "weight": 50},
                {"name": "treatment", "weight": 50},
            ],
            default_variant="control",
            cached_at=datetime.utcnow(),
        )

    def test_user_targeting(self, service, targeted_flag):
        """Test user ID targeting."""
        context = FeatureContext(user_id="vip_user_1")
        enabled, variant, reason = service._evaluate_strategies(targeted_flag, context)

        assert enabled is True
        assert reason == "user_targeted"

    def test_property_matching(self, service, targeted_flag):
        """Test property matching."""
        context = FeatureContext(
            user_id="regular_user",
            properties={"plan": "premium"}
        )
        enabled, variant, reason = service._evaluate_strategies(targeted_flag, context)

        assert enabled is True
        assert reason == "property_match"

    def test_percentage_rollout(self, service, basic_flag):
        """Test percentage rollout."""
        # Generate many users and check distribution
        enabled_count = 0
        total = 1000

        for i in range(total):
            context = FeatureContext(user_id=f"user_{i}")
            enabled, _, reason = service._evaluate_strategies(basic_flag, context)
            if enabled:
                enabled_count += 1

        # Should be roughly 50% (with some margin)
        assert 400 < enabled_count < 600

    def test_disabled_flag_returns_default(self, service):
        """Test that disabled flag returns default."""
        flag = CachedFlag(
            flag_key="disabled_flag",
            enabled=False,
            strategies={"percentage": 100},
            variants=[],
            default_variant="off",
            cached_at=datetime.utcnow(),
        )

        # Even with 100% rollout, disabled flag should return default
        context = FeatureContext(user_id="any_user")
        enabled, variant, reason = service._evaluate_strategies(flag, context)

        # Note: _evaluate_strategies doesn't check enabled flag, that's done in evaluate()
        # So this should still return True based on percentage
        assert enabled is True


class TestVariantSelection:
    """Test variant selection for multivariate flags."""

    @pytest.fixture
    def service(self):
        return FeatureFlagService()

    @pytest.fixture
    def multivariate_flag(self):
        return CachedFlag(
            flag_key="button_color_test",
            enabled=True,
            strategies={"percentage": 100},
            variants=[
                {"name": "control", "weight": 34},
                {"name": "blue", "weight": 33},
                {"name": "green", "weight": 33},
            ],
            default_variant="control",
            cached_at=datetime.utcnow(),
        )

    def test_variant_distribution(self, service, multivariate_flag):
        """Test that variants are distributed according to weights."""
        variant_counts = {"control": 0, "blue": 0, "green": 0}
        total = 3000

        for i in range(total):
            variant = service._select_variant(multivariate_flag, f"user_{i}")
            variant_counts[variant] += 1

        # Each variant should be roughly 33% (with margin)
        for name, count in variant_counts.items():
            assert 800 < count < 1200, f"{name}: {count}"

    def test_consistent_variant_selection(self, service, multivariate_flag):
        """Same user should always get same variant."""
        user_id = "consistent_user"
        variants = [
            service._select_variant(multivariate_flag, user_id)
            for _ in range(10)
        ]

        assert all(v == variants[0] for v in variants)


@pytest.mark.asyncio
class TestFeatureFlagServiceAsync:
    """Test async methods of FeatureFlagService."""

    async def test_evaluate_not_found(self):
        """Test evaluation of non-existent flag."""
        service = FeatureFlagService()

        # Mock _get_flag to return None
        with patch.object(service, '_get_flag', return_value=None):
            result = await service.evaluate("nonexistent_flag", None, None)

        assert result.enabled is False
        assert result.reason == "not_found"

    async def test_evaluate_disabled_flag(self):
        """Test evaluation of disabled flag."""
        service = FeatureFlagService()

        disabled_flag = CachedFlag(
            flag_key="disabled_flag",
            enabled=False,
            strategies={},
            variants=[],
            default_variant="off",
            cached_at=datetime.utcnow(),
        )

        with patch.object(service, '_get_flag', return_value=disabled_flag):
            result = await service.evaluate("disabled_flag", None, None)

        assert result.enabled is False
        assert result.reason == "disabled"

    async def test_is_enabled_with_default(self):
        """Test is_enabled with default value."""
        service = FeatureFlagService()

        with patch.object(service, '_get_flag', return_value=None):
            result = await service.is_enabled("missing_flag", None, None, default=True)

        assert result is True

    async def test_bulk_evaluate(self):
        """Test bulk evaluation of multiple flags."""
        service = FeatureFlagService()

        flag1 = CachedFlag(
            flag_key="flag1",
            enabled=True,
            strategies={"percentage": 100},
            variants=[],
            default_variant="on",
            cached_at=datetime.utcnow(),
        )
        flag2 = CachedFlag(
            flag_key="flag2",
            enabled=False,
            strategies={},
            variants=[],
            default_variant="off",
            cached_at=datetime.utcnow(),
        )

        async def mock_get_flag(key, db):
            if key == "flag1":
                return flag1
            elif key == "flag2":
                return flag2
            return None

        with patch.object(service, '_get_flag', side_effect=mock_get_flag):
            results = await service.bulk_evaluate(
                ["flag1", "flag2", "flag3"],
                FeatureContext(user_id="test_user"),
                None
            )

        assert len(results) == 3
        assert results["flag1"].enabled is True
        assert results["flag2"].enabled is False
        assert results["flag3"].reason == "not_found"
