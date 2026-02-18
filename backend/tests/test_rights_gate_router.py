"""Router tests for rights gate endpoints."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.routers.rights_gate import router


@pytest.mark.asyncio
async def test_check_pre_gen_returns_policy_decision():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/rights")

    payload = {
        "action": "remix",
        "rights_asset": {
            "derivative_allowed": False,
            "allowed_actions": ["reference"],
        },
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/rights/check-pre-gen", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "block"
    assert "DERIVATIVE_NOT_ALLOWED" in body["reason_codes"]


@pytest.mark.asyncio
async def test_check_post_gen_returns_allow():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/rights")

    payload = {
        "clone_risk": 0.12,
        "threshold": 0.6,
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/rights/check-post-gen", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "allow"
    assert body["reason_codes"] == []
