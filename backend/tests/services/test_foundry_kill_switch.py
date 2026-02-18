"""Tests for Foundry kill switch (write guard) and access control."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.features.original_ip_foundry.foundry_auth import (
    foundry_write_guard,
    require_foundry_access,
)


def _make_request(method: str = "GET", path: str = "/api/v1/foundry/health", email: str | None = None):
    """Build a mock Request with the given method/path."""
    request = MagicMock()
    request.method = method
    url = MagicMock()
    url.path = path
    request.url = url
    request.headers = {}
    request.cookies = {}
    request.state = MagicMock(spec=[])  # empty spec so setattr works
    if email:
        request.headers["Authorization"] = f"Bearer fake_token"
    return request


class TestFoundryWriteGuard:
    """foundry_write_guard blocks POST/PUT/PATCH/DELETE when write is disabled."""

    @pytest.mark.asyncio
    @patch("app.features.original_ip_foundry.foundry_auth.settings")
    async def test_post_blocked_when_write_disabled(self, mock_settings):
        mock_settings.AD_FOUNDRY_WRITE_ENABLED = False
        mock_settings.AD_FOUNDRY_READONLY_SAFE_PATHS_SET = set()

        request = _make_request(method="POST", path="/api/v1/foundry/patterns/extract")
        with pytest.raises(HTTPException) as exc_info:
            await foundry_write_guard(request)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    @patch("app.features.original_ip_foundry.foundry_auth.settings")
    async def test_get_allowed_when_write_disabled(self, mock_settings):
        mock_settings.AD_FOUNDRY_WRITE_ENABLED = False
        mock_settings.AD_FOUNDRY_READONLY_SAFE_PATHS_SET = set()

        request = _make_request(method="GET", path="/api/v1/foundry/health")
        # Should not raise
        await foundry_write_guard(request)

    @pytest.mark.asyncio
    @patch("app.features.original_ip_foundry.foundry_auth.settings")
    async def test_safe_path_post_allowed_when_write_disabled(self, mock_settings):
        mock_settings.AD_FOUNDRY_WRITE_ENABLED = False
        mock_settings.AD_FOUNDRY_READONLY_SAFE_PATHS_SET = {
            "/api/v1/foundry/rights/evaluate-assets",
        }

        request = _make_request(method="POST", path="/api/v1/foundry/rights/evaluate-assets")
        # Should not raise — safe path bypass
        await foundry_write_guard(request)

    @pytest.mark.asyncio
    @patch("app.features.original_ip_foundry.foundry_auth.settings")
    async def test_post_allowed_when_write_enabled(self, mock_settings):
        mock_settings.AD_FOUNDRY_WRITE_ENABLED = True
        mock_settings.AD_FOUNDRY_READONLY_SAFE_PATHS_SET = set()

        request = _make_request(method="POST", path="/api/v1/foundry/patterns/extract")
        # Should not raise
        await foundry_write_guard(request)

    @pytest.mark.asyncio
    @patch("app.features.original_ip_foundry.foundry_auth.settings")
    async def test_delete_blocked_when_write_disabled(self, mock_settings):
        mock_settings.AD_FOUNDRY_WRITE_ENABLED = False
        mock_settings.AD_FOUNDRY_READONLY_SAFE_PATHS_SET = set()

        request = _make_request(method="DELETE", path="/api/v1/foundry/memory/123")
        with pytest.raises(HTTPException) as exc_info:
            await foundry_write_guard(request)
        assert exc_info.value.status_code == 403


class TestRequireFoundryAccess:
    """require_foundry_access enforces scope-based access control."""

    @pytest.mark.asyncio
    @patch("app.features.original_ip_foundry.foundry_auth.settings")
    @patch("app.features.original_ip_foundry.foundry_auth._get_session_email")
    async def test_internal_scope_blocks_non_allowlist(self, mock_email, mock_settings):
        mock_settings.AD_FOUNDRY_ACCESS_SCOPE = "internal"
        mock_email.return_value = "outsider@example.com"
        mock_settings.AD_FOUNDRY_ALLOWLIST_SET = {"admin@crebit.com"}

        request = _make_request()
        with pytest.raises(HTTPException) as exc_info:
            await require_foundry_access(request)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    @patch("app.features.original_ip_foundry.foundry_auth.settings")
    @patch("app.features.original_ip_foundry.foundry_auth._get_session_email")
    async def test_internal_scope_allows_allowlisted(self, mock_email, mock_settings):
        mock_settings.AD_FOUNDRY_ACCESS_SCOPE = "internal"
        mock_email.return_value = "admin@crebit.com"
        mock_settings.AD_FOUNDRY_ALLOWLIST_SET = {"admin@crebit.com"}

        request = _make_request()
        result = await require_foundry_access(request)
        assert result == "admin@crebit.com"

    @pytest.mark.asyncio
    @patch("app.features.original_ip_foundry.foundry_auth.settings")
    @patch("app.features.original_ip_foundry.foundry_auth._get_session_email")
    async def test_internal_scope_rejects_unauthenticated(self, mock_email, mock_settings):
        mock_settings.AD_FOUNDRY_ACCESS_SCOPE = "internal"
        mock_email.return_value = None

        request = _make_request()
        with pytest.raises(HTTPException) as exc_info:
            await require_foundry_access(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch("app.features.original_ip_foundry.foundry_auth.settings")
    @patch("app.features.original_ip_foundry.foundry_auth._get_session_email")
    async def test_public_scope_allows_anonymous(self, mock_email, mock_settings):
        mock_settings.AD_FOUNDRY_ACCESS_SCOPE = "public"
        mock_email.return_value = None

        request = _make_request()
        result = await require_foundry_access(request)
        assert result == "public@anonymous"
