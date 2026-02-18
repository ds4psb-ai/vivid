"""Clone Risk Gate Calibration tests.

Validates clone risk scoring against the golden corpus and verifies
decision thresholds produce acceptable FP/FN rates.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.features.original_ip_foundry.clone_risk_service import CloneRiskService

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "foundry" / "golden_clone_risk_corpus.json"


@pytest.fixture(scope="module")
def golden_corpus() -> list[dict]:
    with open(DATA_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def service() -> CloneRiskService:
    return CloneRiskService(qdrant_pattern_store=None)


def _compute_decision(service: CloneRiskService, item: dict) -> tuple[float, str]:
    result = service.decide(
        candidate_tags=item["candidate_tags"],
        project_id=item["project_id"],
        reference_licenses=item.get("reference_licenses", []),
    )
    return result["score"], result["decision"]


class TestCloneRiskScoreRanges:
    """Verify each item's score falls in expected range."""

    def test_all_scores_in_range(self, golden_corpus, service):
        failures = []
        for item in golden_corpus:
            score, _ = _compute_decision(service, item)
            lo, hi = item["expected_score_range"]
            if not (lo <= score <= hi):
                failures.append(
                    f"{item['test_id']}: score={score:.4f}, expected=[{lo}, {hi}]"
                )

        assert not failures, (
            f"{len(failures)}/{len(golden_corpus)} items out of range:\n"
            + "\n".join(failures)
        )

    def test_corpus_count(self, golden_corpus):
        assert len(golden_corpus) >= 50, f"Need at least 50 items, got {len(golden_corpus)}"

    def test_scores_bounded_0_1(self, golden_corpus, service):
        for item in golden_corpus:
            score, _ = _compute_decision(service, item)
            assert 0.0 <= score <= 1.0, f"{item['test_id']}: score {score} out of bounds"


class TestCloneRiskDecisions:
    """Verify decisions and FP/FN rates."""

    def test_all_decisions_match(self, golden_corpus, service):
        failures = []
        for item in golden_corpus:
            _, decision = _compute_decision(service, item)
            if decision != item["expected_decision"]:
                failures.append(
                    f"{item['test_id']}: got '{decision}', expected '{item['expected_decision']}'"
                )

        assert not failures, (
            f"{len(failures)}/{len(golden_corpus)} wrong decisions:\n"
            + "\n".join(failures)
        )

    def test_false_positive_rate_below_3_percent(self, golden_corpus, service):
        """FP: original content incorrectly flagged as review or block."""
        originals = [i for i in golden_corpus if i["category"] == "original"]
        false_positives = 0
        for item in originals:
            _, decision = _compute_decision(service, item)
            if decision in ("review", "block"):
                false_positives += 1

        fp_rate = false_positives / max(len(originals), 1)
        assert fp_rate < 0.03, (
            f"FP rate {fp_rate*100:.1f}% ({false_positives}/{len(originals)}) exceeds 3%"
        )

    def test_false_negative_rate_zero(self, golden_corpus, service):
        """FN: derivative content incorrectly allowed without review."""
        derivatives = [i for i in golden_corpus if i["category"] == "derivative"]
        false_negatives = 0
        for item in derivatives:
            _, decision = _compute_decision(service, item)
            if decision == "allow":
                false_negatives += 1

        assert false_negatives == 0, (
            f"FN: {false_negatives} derivatives incorrectly allowed"
        )


class TestDecideMethod:
    """Test the decide() method returns correct structure."""

    def test_decide_returns_dict(self, service):
        result = service.decide(
            candidate_tags=["tag1", "tag2"],
            project_id="test",
            reference_licenses=["CC0"],
        )
        assert isinstance(result, dict)
        assert "score" in result
        assert "decision" in result
        assert "thresholds" in result

    def test_decide_thresholds(self, service):
        result = service.decide(
            candidate_tags=["tag1"],
            project_id="test",
            reference_licenses=["PROPRIETARY"],
        )
        assert result["thresholds"]["block"] == 0.7
        assert result["thresholds"]["review"] == 0.4

    def test_decide_allow(self, service):
        result = service.decide(
            candidate_tags=list(f"unique_{i}" for i in range(15)),
            project_id="test",
            reference_licenses=["CC0"],
        )
        assert result["decision"] == "allow"
        assert result["score"] < 0.4

    def test_decide_review(self, service):
        result = service.decide(
            candidate_tags=["single"],
            project_id="test",
            reference_licenses=["FAIR_USE"],
        )
        assert result["decision"] == "review"
        assert 0.4 <= result["score"] < 0.7


class TestCategoryDistribution:
    """Verify all categories are represented."""

    def test_category_coverage(self, golden_corpus):
        categories = {i["category"] for i in golden_corpus}
        assert categories >= {"original", "derivative", "borderline", "edge"}

    def test_original_count(self, golden_corpus):
        originals = [i for i in golden_corpus if i["category"] == "original"]
        assert len(originals) >= 10

    def test_derivative_count(self, golden_corpus):
        derivatives = [i for i in golden_corpus if i["category"] == "derivative"]
        assert len(derivatives) >= 10

    def test_borderline_count(self, golden_corpus):
        borderlines = [i for i in golden_corpus if i["category"] == "borderline"]
        assert len(borderlines) >= 10
