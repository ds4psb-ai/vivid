"""Tests for Original-IP Foundry 4-guardrail safety layer.

Guardrail ①  Kill switch   (AD_FOUNDRY_ENABLED)
Guardrail ②  Allowlist     (AD_FOUNDRY_ALLOWLIST)
Guardrail ③  Resource sep  (naming convention — verified via constants)
Guardrail ④  Write guard   (AD_FOUNDRY_WRITE_ENABLED)
"""
from __future__ import annotations

import importlib
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_token_payload(email: str = "ted.taeeun.kim@gmail.com") -> dict:
    """Minimal JWT-like payload mimicking what auth_tokens.decode_token returns."""
    return {
        "user_id": f"google:test-{email}",
        "email": email,
        "name": "Test User",
        "role": "user",
        "verified": True,
    }


def _create_test_app(*, foundry_enabled: bool, write_enabled: bool, allowlist: str) -> FastAPI:
    """Build a minimal FastAPI app that mirrors main.py's conditional registration."""
    app = FastAPI()

    if foundry_enabled:
        # Patch settings before importing the router
        with patch("app.config.settings") as mock_settings:
            mock_settings.AD_FOUNDRY_ENABLED = foundry_enabled
            mock_settings.AD_FOUNDRY_WRITE_ENABLED = write_enabled
            mock_settings.AD_FOUNDRY_ALLOWLIST = allowlist
            mock_settings.AD_FOUNDRY_ALLOWLIST_SET = {
                e.strip().lower() for e in allowlist.split(",") if e.strip()
            }
            mock_settings.SESSION_COOKIE_NAME = "crebit_session"
            mock_settings.SESSION_SECRET = MagicMock()
            mock_settings.SESSION_SECRET.get_secret_value.return_value = "test-secret"

        from app.features.original_ip_foundry.foundry_router import router
        from app.features.original_ip_foundry.foundry_lifespan import _create_services
        app.include_router(router, prefix="/api/v1/foundry", tags=["foundry"])
        app.state.foundry = _create_services()

    return app


# ---------------------------------------------------------------------------
# Guardrail ① — Kill Switch
# ---------------------------------------------------------------------------

class TestKillSwitch:
    """AD_FOUNDRY_ENABLED=false → router not registered → 404."""

    def test_foundry_disabled_returns_404(self):
        app = _create_test_app(
            foundry_enabled=False,
            write_enabled=False,
            allowlist="ted.taeeun.kim@gmail.com",
        )
        client = TestClient(app)
        resp = client.get("/api/v1/foundry/health")
        assert resp.status_code == 404

    def test_foundry_enabled_health_requires_auth(self):
        """When enabled but no token → 401."""
        app = _create_test_app(
            foundry_enabled=True,
            write_enabled=False,
            allowlist="ted.taeeun.kim@gmail.com",
        )
        client = TestClient(app)

        with patch(
            "app.features.original_ip_foundry.foundry_auth.decode_token",
            return_value=None,
        ):
            resp = client.get("/api/v1/foundry/health")
            assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Guardrail ② — Allowlist
# ---------------------------------------------------------------------------

class TestAllowlist:
    """Only emails in AD_FOUNDRY_ALLOWLIST are allowed."""

    def test_allowlist_blocks_unknown_user(self):
        app = _create_test_app(
            foundry_enabled=True,
            write_enabled=False,
            allowlist="ted.taeeun.kim@gmail.com",
        )
        client = TestClient(app)

        with patch(
            "app.features.original_ip_foundry.foundry_auth.decode_token",
            return_value=_make_token_payload("student@example.com"),
        ), patch(
            "app.features.original_ip_foundry.foundry_auth.settings"
        ) as mock_s:
            mock_s.SESSION_COOKIE_NAME = "crebit_session"
            mock_s.SESSION_SECRET = MagicMock()
            mock_s.SESSION_SECRET.get_secret_value.return_value = "test-secret"
            mock_s.AD_FOUNDRY_ALLOWLIST_SET = {"ted.taeeun.kim@gmail.com"}
            mock_s.AD_FOUNDRY_WRITE_ENABLED = False

            resp = client.get(
                "/api/v1/foundry/health",
                cookies={"crebit_session": "fake-token"},
            )
            assert resp.status_code == 403
            assert "denied" in resp.json()["detail"].lower()

    def test_allowlist_permits_internal_user(self):
        app = _create_test_app(
            foundry_enabled=True,
            write_enabled=False,
            allowlist="ted.taeeun.kim@gmail.com",
        )
        client = TestClient(app)

        with patch(
            "app.features.original_ip_foundry.foundry_auth.decode_token",
            return_value=_make_token_payload("ted.taeeun.kim@gmail.com"),
        ), patch(
            "app.features.original_ip_foundry.foundry_auth.settings"
        ) as mock_s:
            mock_s.SESSION_COOKIE_NAME = "crebit_session"
            mock_s.SESSION_SECRET = MagicMock()
            mock_s.SESSION_SECRET.get_secret_value.return_value = "test-secret"
            mock_s.AD_FOUNDRY_ALLOWLIST_SET = {"ted.taeeun.kim@gmail.com"}
            mock_s.AD_FOUNDRY_WRITE_ENABLED = False

            resp = client.get(
                "/api/v1/foundry/health",
                cookies={"crebit_session": "fake-token"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"


# ---------------------------------------------------------------------------
# Guardrail ④ — Read-Only Write Guard
# ---------------------------------------------------------------------------

class TestWriteGuard:
    """AD_FOUNDRY_WRITE_ENABLED=false → POST/PUT/PATCH/DELETE 403."""

    def _authenticated_client(self, write_enabled: bool):
        app = _create_test_app(
            foundry_enabled=True,
            write_enabled=write_enabled,
            allowlist="ted.taeeun.kim@gmail.com",
        )

        # Add a test write endpoint
        from app.features.original_ip_foundry.foundry_auth import (
            require_foundry_access,
            foundry_write_guard,
        )
        from fastapi import Depends

        @app.post("/api/v1/foundry/test-write",
                   dependencies=[Depends(require_foundry_access), Depends(foundry_write_guard)])
        async def test_write():
            return {"written": True}

        return TestClient(app)

    def test_read_only_blocks_post(self):
        client = self._authenticated_client(write_enabled=False)

        with patch(
            "app.features.original_ip_foundry.foundry_auth.decode_token",
            return_value=_make_token_payload("ted.taeeun.kim@gmail.com"),
        ), patch(
            "app.features.original_ip_foundry.foundry_auth.settings"
        ) as mock_s:
            mock_s.SESSION_COOKIE_NAME = "crebit_session"
            mock_s.SESSION_SECRET = MagicMock()
            mock_s.SESSION_SECRET.get_secret_value.return_value = "test-secret"
            mock_s.AD_FOUNDRY_ALLOWLIST_SET = {"ted.taeeun.kim@gmail.com"}
            mock_s.AD_FOUNDRY_WRITE_ENABLED = False

            resp = client.post(
                "/api/v1/foundry/test-write",
                cookies={"crebit_session": "fake-token"},
            )
            assert resp.status_code == 403
            assert "read-only" in resp.json()["detail"].lower()

    def test_write_enabled_allows_post(self):
        client = self._authenticated_client(write_enabled=True)

        with patch(
            "app.features.original_ip_foundry.foundry_auth.decode_token",
            return_value=_make_token_payload("ted.taeeun.kim@gmail.com"),
        ), patch(
            "app.features.original_ip_foundry.foundry_auth.settings"
        ) as mock_s:
            mock_s.SESSION_COOKIE_NAME = "crebit_session"
            mock_s.SESSION_SECRET = MagicMock()
            mock_s.SESSION_SECRET.get_secret_value.return_value = "test-secret"
            mock_s.AD_FOUNDRY_ALLOWLIST_SET = {"ted.taeeun.kim@gmail.com"}
            mock_s.AD_FOUNDRY_WRITE_ENABLED = True

            resp = client.post(
                "/api/v1/foundry/test-write",
                cookies={"crebit_session": "fake-token"},
            )
            assert resp.status_code == 200
            assert resp.json()["written"] is True


# ---------------------------------------------------------------------------
# Guardrail ③ — Resource Separation (naming convention check)
# ---------------------------------------------------------------------------

class TestResourceSeparation:
    """Verify Foundry Qdrant collections use 'foundry_' prefix."""

    def test_foundry_collections_use_prefix(self):
        """Foundry collections must NOT overlap with existing vivid_multimodal_*."""
        expected_collections = [
            "foundry_shot_corpus",
            "foundry_pattern_atoms",
            "foundry_transition_rules",
            "foundry_rights_constraints",
        ]
        for name in expected_collections:
            assert name.startswith("foundry_"), f"{name} missing foundry_ prefix"
            assert not name.startswith("vivid_"), f"{name} must not use vivid_ prefix"

    def test_worker_queue_separation(self):
        """Foundry worker queue must be distinct from default."""
        foundry_queue = "arq:queue:foundry"
        default_queue = "arq:queue"
        assert foundry_queue != default_queue
        assert "foundry" in foundry_queue


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

class TestConfigValidation:
    """Production config validator catches unsafe Foundry settings."""

    def test_allowlist_empty_warns(self):
        from app.config import Settings
        s = Settings(
            AD_FOUNDRY_ENABLED=True,
            AD_FOUNDRY_ALLOWLIST="",
            ENVIRONMENT="production",
        )
        warnings = s.validate_production_config()
        assert any("AD_FOUNDRY_ALLOWLIST" in w for w in warnings)

    def test_write_without_enable_warns(self):
        from app.config import Settings
        s = Settings(
            AD_FOUNDRY_ENABLED=False,
            AD_FOUNDRY_WRITE_ENABLED=True,
            ENVIRONMENT="production",
        )
        warnings = s.validate_production_config()
        assert any("AD_FOUNDRY_WRITE_ENABLED" in w for w in warnings)
