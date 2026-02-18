from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.features.original_ip_foundry.foundry_router import router


def _token_payload(email: str = "ted.taeeun.kim@gmail.com") -> dict:
    return {"user_id": "google:test", "email": email, "role": "admin", "verified": True}


@pytest.mark.asyncio
async def test_export_c2pa_manifest_endpoint():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/foundry")

    safe_paths = {
        "/api/v1/foundry/rights/evaluate-assets",
        "/api/v1/foundry/patterns/extract",
        "/api/v1/foundry/recommendations/next-scene",
        "/api/v1/foundry/experiments/assign",
        "/api/v1/foundry/experiments/feedback",
        "/api/v1/foundry/memory/normalize",
        "/api/v1/foundry/retrieval/query",
        "/api/v1/foundry/provenance/export-c2pa",
    }

    with patch(
        "app.features.original_ip_foundry.foundry_auth.decode_token",
        return_value=_token_payload(),
    ), patch(
        "app.features.original_ip_foundry.foundry_auth.settings"
    ) as auth_settings, patch(
        "app.features.original_ip_foundry.foundry_router.settings"
    ) as router_settings:
        auth_settings.SESSION_COOKIE_NAME = "crebit_session"
        auth_settings.SESSION_SECRET = MagicMock()
        auth_settings.SESSION_SECRET.get_secret_value.return_value = "test-secret"
        auth_settings.AD_FOUNDRY_ALLOWLIST_SET = {"ted.taeeun.kim@gmail.com"}
        auth_settings.AD_FOUNDRY_WRITE_ENABLED = False
        auth_settings.AD_FOUNDRY_ACCESS_SCOPE = "internal"
        auth_settings.AD_FOUNDRY_READONLY_SAFE_PATHS_SET = safe_paths

        router_settings.AD_FOUNDRY_ENABLED = True
        router_settings.AD_FOUNDRY_WRITE_ENABLED = False
        router_settings.AD_FOUNDRY_ACCESS_SCOPE = "internal"
        router_settings.AD_FOUNDRY_ALLOWLIST_SET = {"ted.taeeun.kim@gmail.com"}
        router_settings.AD_FOUNDRY_READONLY_SAFE_PATHS_SET = safe_paths

        payload = {
            "project_id": "proj-1",
            "scene_id": "scene-9",
            "asset_id": "asset-1",
            "title": "Scene 9",
            "generator_model": "gemini-3-pro",
            "source_license": "cc-by-4.0",
            "actions": [{"action": "c2pa.created", "parameters": {"prompt": "hello"}}],
            "provenance_trace": [{"asset_id": "src-1", "relationship": "componentOf"}],
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/foundry/provenance/export-c2pa",
                json=payload,
                cookies={"crebit_session": "fake-token"},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["spec_version"] == "2.2"
        assert body["manifest"]["claim_generator"] == "VIVID Original-IP Foundry"
        assert body["compliance"]["eu_ai_act_article_50_ready"] is True

