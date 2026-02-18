"""Continuity Score Golden Test Set validation.

Tests _calculate_continuity_score against golden expected values
with tolerance-based assertions.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.features.original_ip_foundry.recommendation_service import FoundryRecommendationService

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "foundry" / "golden_continuity_test_set.json"


@pytest.fixture(scope="module")
def golden_tests() -> list[dict]:
    with open(DATA_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def service() -> FoundryRecommendationService:
    return FoundryRecommendationService()


def _compute_score(service: FoundryRecommendationService, test_case: dict) -> float:
    ctx = test_case["scene_context"]
    first_shot = test_case["first_shot"]
    shots = test_case["candidate"].get("shots", [first_shot])

    return service._calculate_continuity_score(
        context_characters={str(c).lower() for c in (ctx.get("characters") or [])},
        context_location=str(ctx.get("location") or "unknown").lower(),
        desired_rhythm=str(ctx.get("desired_camera_rhythm") or "balanced").lower(),
        first_shot=first_shot,
        shots=shots,
    )


class TestGoldenSetWithinTolerance:
    """Every golden test case must produce a score within tolerance of expected."""

    def test_golden_set_within_tolerance(self, golden_tests, service):
        failures = []
        for t in golden_tests:
            actual = _compute_score(service, t)
            diff = abs(actual - t["expected"])
            if diff > t["tolerance"]:
                failures.append(
                    f"{t['test_id']}: expected={t['expected']:.4f}, "
                    f"actual={actual:.4f}, diff={diff:.4f}, tolerance={t['tolerance']}"
                )

        assert not failures, (
            f"{len(failures)}/{len(golden_tests)} golden tests failed:\n"
            + "\n".join(failures)
        )

    def test_total_test_count(self, golden_tests):
        """Golden set must have at least 40 test cases."""
        assert len(golden_tests) >= 40

    def test_category_coverage(self, golden_tests):
        """All categories must be represented."""
        categories = {t["category"] for t in golden_tests}
        required = {"high", "medium", "low", "edge_unknown_location", "edge_emotion_mismatch"}
        assert categories >= required, f"Missing categories: {required - categories}"


class TestCategoryBehavior:
    """Verify that categories behave as expected."""

    def test_high_scores_above_threshold(self, golden_tests, service):
        """High category tests should generally score above 0.6."""
        high_tests = [t for t in golden_tests if t["category"] == "high"]
        scores = [_compute_score(service, t) for t in high_tests]
        above_threshold = sum(1 for s in scores if s >= 0.6)
        assert above_threshold / len(high_tests) >= 0.8, (
            f"Only {above_threshold}/{len(high_tests)} high tests scored >= 0.6"
        )

    def test_low_scores_below_threshold(self, golden_tests, service):
        """Low category tests should generally score below 0.5."""
        low_tests = [t for t in golden_tests if t["category"] == "low"]
        scores = [_compute_score(service, t) for t in low_tests]
        below_threshold = sum(1 for s in scores if s < 0.5)
        assert below_threshold / len(low_tests) >= 0.7, (
            f"Only {below_threshold}/{len(low_tests)} low tests scored < 0.5"
        )

    def test_unknown_location_uses_fallback(self, golden_tests, service):
        """Unknown location should yield location_score=0.7 (not 1.0 or 0.35)."""
        edge_tests = [t for t in golden_tests if t["category"] == "edge_unknown_location"]
        for t in edge_tests:
            actual = _compute_score(service, t)
            # Score should be within tolerance of expected
            assert abs(actual - t["expected"]) <= t["tolerance"], (
                f"{t['test_id']}: expected ~{t['expected']}, got {actual}"
            )


class TestScoreBounds:
    """Continuity score should always be in [0, 1]."""

    def test_scores_bounded(self, golden_tests, service):
        for t in golden_tests:
            score = _compute_score(service, t)
            assert 0.0 <= score <= 1.0, f"{t['test_id']}: score {score} out of [0,1]"
