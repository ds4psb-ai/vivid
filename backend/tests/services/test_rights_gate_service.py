"""Tests for rights gate policy service."""

from app.services.rights_gate_service import RightsGateService


def test_block_when_derivative_not_allowed():
    service = RightsGateService()

    decision = service.check_pre_generation(
        {
            "action": "remix",
            "rights_asset": {
                "derivative_allowed": False,
                "allowed_actions": ["reference"],
            },
        }
    )

    assert decision["decision"] == "block"
    assert "DERIVATIVE_NOT_ALLOWED" in decision["reason_codes"]


def test_pass_when_action_allowed():
    service = RightsGateService()

    decision = service.check_pre_generation(
        {
            "action": "reference",
            "rights_asset": {
                "derivative_allowed": True,
                "allowed_actions": ["reference", "summarize"],
            },
        }
    )

    assert decision["decision"] == "allow"
    assert decision["reason_codes"] == []
