from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.features.original_ip_foundry.foundry_router import router


def _token_payload(email: str = "ted.taeeun.kim@gmail.com") -> dict:
    return {"user_id": "google:test", "email": email, "role": "admin", "verified": True}


@pytest.mark.asyncio
async def test_rights_evaluate_assets_endpoint_returns_decision():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/foundry")

    safe_paths = {
        "/api/v1/foundry/rights/evaluate-assets",
        "/api/v1/foundry/recommendations/next-scene",
        "/api/v1/foundry/memory/normalize",
        "/api/v1/foundry/retrieval/query",
        "/api/v1/foundry/experiments/assign",
        "/api/v1/foundry/experiments/feedback",
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
            "action": "remix",
            "requested_elements": ["hero_face"],
            "assets": [
                {
                    "asset_id": "asset-1",
                    "source_license": "",
                    "derivative_allowed": True,
                    "allowed_actions": ["reference"],
                    "blocked_elements": ["hero_face"],
                }
            ],
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/foundry/rights/evaluate-assets",
                json=payload,
                cookies={"crebit_session": "fake-token"},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["decision"] == "block"
        assert "BLOCKED_ELEMENT_MATCH" in body["reason_codes"]


@pytest.mark.asyncio
async def test_recommendation_endpoint_returns_continuity_and_reason_codes():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/foundry")

    safe_paths = {
        "/api/v1/foundry/rights/evaluate-assets",
        "/api/v1/foundry/recommendations/next-scene",
        "/api/v1/foundry/memory/normalize",
        "/api/v1/foundry/retrieval/query",
        "/api/v1/foundry/experiments/assign",
        "/api/v1/foundry/experiments/feedback",
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
            "scene_context": {
                "project_id": "p1",
                "scene_id": "s1",
                "target_emotion": "anxiety",
                "location": "warehouse",
                "characters": ["hero"],
                "desired_camera_rhythm": "dynamic",
                "intent_tags": ["power"],
            },
            "candidates": [
                {
                    "candidate_id": "cand-1",
                    "title": "Hero push-in",
                    "shots": [
                        {
                            "shot_id": "shot-1",
                            "camera_angle": "low_angle",
                            "camera_movement": "tracking",
                            "shot_size": "medium",
                            "emotion_tone": "anxiety",
                            "transition_to_next": "cut",
                            "location": "warehouse",
                            "characters": ["hero"],
                        }
                    ],
                    "rights_assets": [],
                    "mise_en_scene_score": 0.8,
                    "story_intent_fit": 0.8,
                    "director_style_fit": 0.8,
                    "execution_feasibility": 0.8,
                    "clone_risk": 0.2,
                    "pattern_tags": ["power"],
                }
            ],
            "rights_action": "reference",
            "continuity_floor": 0.6,
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/foundry/recommendations/next-scene",
                json=payload,
                cookies={"crebit_session": "fake-token"},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["scene_id"] == "s1"
        assert body["ranked"][0]["continuity_score"] >= 0.6
        assert body["ranked"][0]["decision"] in {"allow", "hold", "review"}
        assert isinstance(body["ranked"][0]["recommendation_rationale"], list)

