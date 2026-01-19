"""Tests for IP payout dispute schemas."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.routers.ip_payout import (
    AdminDisputeResolveRequest,
    AdminHoldbackRequest,
    PayoutDisputeRequest,
    PayoutDisputeResponse,
    PayoutLedgerResponse,
    PayoutDisputeDetailResponse,
)


def test_dispute_request_defaults():
    payload = PayoutDisputeRequest(reason="Revenue share mismatch")
    assert payload.evidence == []


def test_dispute_request_reason_validation():
    with pytest.raises(ValidationError):
        PayoutDisputeRequest(reason="no")


def test_dispute_response_model():
    now = datetime.now(timezone.utc)
    response = PayoutDisputeResponse(
        dispute_id="dispute-1",
        ledger_id="ledger-1",
        status="open",
        created_at=now,
    )
    assert response.status == "open"
    assert response.created_at == now


def test_payout_ledger_response_model():
    now = datetime.now(timezone.utc)
    response = PayoutLedgerResponse(
        id="ledger-1",
        ip_id="ip-1",
        creator_id="user-1",
        gross_amount=100,
        ip_owner_share=30,
        creator_share=50,
        platform_share=20,
        status="holdback",
        holdback_until=now,
        dispute_id=None,
        created_at=now,
        updated_at=now,
    )
    assert response.gross_amount == 100
    assert response.status == "holdback"


def test_admin_holdback_request_optional():
    payload = AdminHoldbackRequest()
    assert payload.holdback_until is None


def test_admin_dispute_resolve_request_validation():
    payload = AdminDisputeResolveRequest(status="resolved", admin_notes="ok")
    assert payload.status == "resolved"

    with pytest.raises(ValidationError):
        AdminDisputeResolveRequest(status="invalid")


def test_dispute_detail_response_model():
    now = datetime.now(timezone.utc)
    response = PayoutDisputeDetailResponse(
        id="dispute-1",
        ledger_id="ledger-1",
        complainant_id="user-1",
        reason="Mismatch",
        evidence=["link"],
        status="open",
        admin_notes=None,
        resolved_by=None,
        resolved_at=None,
        created_at=now,
        updated_at=now,
    )
    assert response.status == "open"
    assert response.evidence == ["link"]
