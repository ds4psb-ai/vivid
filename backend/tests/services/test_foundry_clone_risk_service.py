"""Tests for CloneRiskService."""
from unittest.mock import MagicMock

from app.features.original_ip_foundry.clone_risk_service import CloneRiskService


def test_empty_tags_returns_neutral_score():
    service = CloneRiskService()
    score = service.compute(candidate_tags=[], project_id="p1")
    # 0.5 * 0.5 (pattern default) + 0.3 * 0.0 (no licenses) + 0.2 * 0.5 (empty tags)
    expected = 0.5 * 0.5 + 0.3 * 0.0 + 0.2 * 0.5
    assert abs(score - expected) < 0.01


def test_proprietary_license_high_risk():
    service = CloneRiskService()
    score = service.compute(
        candidate_tags=["action", "thriller"],
        project_id="p1",
        reference_licenses=["PROPRIETARY"],
    )
    # license_risk = 0.8 (proprietary), so score should be relatively high
    assert score > 0.4


def test_cc0_license_low_risk():
    service = CloneRiskService()
    score = service.compute(
        candidate_tags=["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o"],
        project_id="p1",
        reference_licenses=["CC0"],
    )
    # Many unique tags → low tag_density, CC0 → license_risk=0.0
    # tag_density = max(0, 1 - 15/15) = 0.0
    # score = 0.5*0.5 + 0.3*0.0 + 0.2*0.0 = 0.25
    assert score < 0.4


def test_blend_of_licenses_uses_worst_case():
    service = CloneRiskService()
    score_mixed = service.compute(
        candidate_tags=["test"],
        project_id="p1",
        reference_licenses=["CC0", "PROPRIETARY"],
    )
    score_cc0 = service.compute(
        candidate_tags=["test"],
        project_id="p1",
        reference_licenses=["CC0"],
    )
    assert score_mixed > score_cc0


def test_qdrant_fallback_when_unavailable():
    mock_store = MagicMock()
    mock_store.search_atoms.side_effect = Exception("connection failed")
    service = CloneRiskService(qdrant_pattern_store=mock_store)

    score = service.compute(candidate_tags=["tag1"], project_id="p1")
    # Should fall back to pattern_similarity=0.5
    assert 0.0 <= score <= 1.0
