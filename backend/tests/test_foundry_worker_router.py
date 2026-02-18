from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.features.original_ip_foundry.foundry_router import router


def _token_payload(email: str = "ted.taeeun.kim@gmail.com") -> dict:
    return {"user_id": "google:test", "email": email, "role": "admin", "verified": True}


@pytest.mark.asyncio
async def test_worker_provider_and_dispatch_routes():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/foundry")

    safe_paths = {
        "/api/v1/foundry/workers/dispatch",
        "/api/v1/foundry/workers/jobs",
        "/api/v1/foundry/recommendations/next-scene",
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
        router_settings.AD_FOUNDRY_WORKER_PROVIDER = "agent0"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            providers = await client.get(
                "/api/v1/foundry/workers/providers",
                cookies={"crebit_session": "fake-token"},
            )
            assert providers.status_code == 200
            providers_json = providers.json()
            assert providers_json["active_provider"] == "agent0"

            dispatch = await client.post(
                "/api/v1/foundry/workers/dispatch",
                json={
                    "tenant_id": "tenant-a",
                    "project_id": "project-a",
                    "job_type": "pattern_reindex",
                    "payload": {"scope": "all"},
                    "provider": "taskiq",
                    "input_type": "worker_dispatch_test",
                },
                cookies={"crebit_session": "fake-token"},
            )
            assert dispatch.status_code == 200
            dispatch_json = dispatch.json()
            assert dispatch_json["provider"] == "taskiq"
            job_id = dispatch_json["job_id"]

            status = await client.get(
                f"/api/v1/foundry/workers/jobs/{job_id}?tenant_id=tenant-a&project_id=project-a",
                cookies={"crebit_session": "fake-token"},
            )
            assert status.status_code == 200
            assert status.json()["job_id"] == job_id

            cancel = await client.post(
                f"/api/v1/foundry/workers/jobs/{job_id}/cancel?tenant_id=tenant-a&project_id=project-a",
                cookies={"crebit_session": "fake-token"},
            )
            assert cancel.status_code == 200
            assert cancel.json()["status"] == "cancel_requested"

            forbidden = await client.get(
                f"/api/v1/foundry/workers/jobs/{job_id}?tenant_id=tenant-bad&project_id=project-a",
                cookies={"crebit_session": "fake-token"},
            )
            assert forbidden.status_code == 403
