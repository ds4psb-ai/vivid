"""Tests for Rights Gate C (publish gate)."""
import pytest

from app.services.rights_gate_service import RightsGateService
from app.features.original_ip_foundry.rights_service import FoundryRightsService


def test_check_publish_allows_clean_content():
    svc = RightsGateService()
    result = svc.check_publish({
        "clone_risk": 0.2,
        "ingredients": [{"source_license": "CC_BY"}],
    })
    assert result["decision"] == "allow"


def test_check_publish_blocks_near_duplicate():
    svc = RightsGateService()
    result = svc.check_publish({
        "near_duplicate_result": {"decision": "block"},
        "clone_risk": 0.1,
        "ingredients": [{"source_license": "CC_BY"}],
    })
    assert result["decision"] == "block"
    assert "NEAR_DUPLICATE_BLOCKED" in result["reason_codes"]


def test_check_publish_blocks_high_clone_risk():
    svc = RightsGateService()
    result = svc.check_publish({
        "clone_risk": 0.7,
        "publish_threshold": 0.5,
        "ingredients": [{"source_license": "CC_BY"}],
    })
    assert result["decision"] == "block"
    assert "CLONE_RISK_PUBLISH_HIGH" in result["reason_codes"]


def test_check_publish_blocks_unknown_license():
    svc = RightsGateService()
    result = svc.check_publish({
        "clone_risk": 0.1,
        "ingredients": [{"source_license": "UNKNOWN"}],
    })
    assert result["decision"] == "block"
    assert "INCOMPLETE_LICENSE_FOR_PUBLISH" in result["reason_codes"]


def test_check_publish_blocks_missing_license():
    svc = RightsGateService()
    result = svc.check_publish({
        "clone_risk": 0.1,
        "ingredients": [{"source_license": ""}],
    })
    assert result["decision"] == "block"
    assert "INCOMPLETE_LICENSE_FOR_PUBLISH" in result["reason_codes"]


@pytest.mark.asyncio
async def test_evaluate_publish_readiness_integration():
    svc = FoundryRightsService()
    result = await svc.evaluate_publish_readiness(
        project_id="test-project",
        clone_risk=0.2,
        ingredients=[{"source_license": "CC_BY"}],
    )
    assert result["decision"] == "allow"
    assert "clone_risk" in result
