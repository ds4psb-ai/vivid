"""Tests for Ops audit response schema."""

from app.routers.ops_audit import OpsActionLogResponse


def test_ops_action_log_response():
    response = OpsActionLogResponse(
        id="log-1",
        action_type="ip_payout_ledger_created",
        status="holdback",
        note="auto",
        payload={"ledger_id": "ledger-1"},
        stats={"gross_amount": 10},
        duration_ms=None,
        actor_id="user-1",
        created_at="2026-01-19T00:00:00Z",
    )
    assert response.action_type == "ip_payout_ledger_created"
    assert response.payload["ledger_id"] == "ledger-1"
