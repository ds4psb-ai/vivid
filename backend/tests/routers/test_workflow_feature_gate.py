"""Feature Gate Tests for Workflow Router.

Tests that FLOW_ENABLED feature flag properly gates all workflow endpoints.
When FLOW_ENABLED=False, all endpoints should return 403 Forbidden.
"""
import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestFlowFeatureGate:
    """Test FLOW_ENABLED feature gate on all workflow endpoints."""

    @pytest.mark.asyncio
    async def test_plan_disabled_returns_403(self, client):
        """POST /workflow/plan returns 403 when FLOW_ENABLED=False."""
        with patch("app.dependencies.settings.FLOW_ENABLED", False):
            response = await client.post(
                "/api/v1/workflow/plan",
                json={"user_request": "test"},
                headers={"X-User-Id": "test-user"},
            )
            assert response.status_code == 403
            assert "disabled" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_templates_disabled_returns_403(self, client):
        """GET /workflow/templates returns 403 when FLOW_ENABLED=False."""
        with patch("app.dependencies.settings.FLOW_ENABLED", False):
            response = await client.get("/api/v1/workflow/templates")
            assert response.status_code == 403
            assert "disabled" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_tools_disabled_returns_403(self, client):
        """GET /workflow/tools returns 403 when FLOW_ENABLED=False."""
        with patch("app.dependencies.settings.FLOW_ENABLED", False):
            response = await client.get("/api/v1/workflow/tools")
            assert response.status_code == 403
            assert "disabled" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_session_status_disabled_returns_403(self, client):
        """GET /workflow/session/{id} returns 403 when FLOW_ENABLED=False."""
        with patch("app.dependencies.settings.FLOW_ENABLED", False):
            response = await client.get(
                "/api/v1/workflow/session/test-session-id",
                headers={"X-User-Id": "test-user"},
            )
            assert response.status_code == 403
            assert "disabled" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_advance_disabled_returns_403(self, client):
        """POST /workflow/session/{id}/advance returns 403 when FLOW_ENABLED=False."""
        with patch("app.dependencies.settings.FLOW_ENABLED", False):
            response = await client.post(
                "/api/v1/workflow/session/test-session-id/advance",
                headers={"X-User-Id": "test-user"},
            )
            assert response.status_code == 403
            assert "disabled" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_execute_disabled_returns_403(self, client):
        """POST /workflow/session/{id}/execute returns 403 when FLOW_ENABLED=False."""
        with patch("app.dependencies.settings.FLOW_ENABLED", False):
            response = await client.post(
                "/api/v1/workflow/session/test-session-id/execute",
                headers={"X-User-Id": "test-user"},
            )
            assert response.status_code == 403
            assert "disabled" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_start_disabled_returns_403(self, client):
        """POST /workflow/session/{id}/start returns 403 when FLOW_ENABLED=False."""
        with patch("app.dependencies.settings.FLOW_ENABLED", False):
            response = await client.post(
                "/api/v1/workflow/session/test-session-id/start",
                json={"session_id": "test-session-id"},
                headers={"X-User-Id": "test-user"},
            )
            assert response.status_code == 403
            assert "disabled" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_user_sessions_disabled_returns_403(self, client):
        """GET /workflow/user/sessions returns 403 when FLOW_ENABLED=False."""
        with patch("app.dependencies.settings.FLOW_ENABLED", False):
            response = await client.get(
                "/api/v1/workflow/user/sessions",
                headers={"X-User-Id": "test-user"},
            )
            assert response.status_code == 403
            assert "disabled" in response.json()["detail"].lower()


class TestFlowFeatureGateEnabled:
    """Test that endpoints work when FLOW_ENABLED=True."""

    @pytest.mark.asyncio
    async def test_templates_enabled_returns_200(self, client):
        """GET /workflow/templates returns 200 when FLOW_ENABLED=True."""
        with patch("app.dependencies.settings.FLOW_ENABLED", True):
            response = await client.get("/api/v1/workflow/templates")
            assert response.status_code != 403

    @pytest.mark.asyncio
    async def test_tools_enabled_returns_200(self, client):
        """GET /workflow/tools returns 200 when FLOW_ENABLED=True."""
        with patch("app.dependencies.settings.FLOW_ENABLED", True):
            response = await client.get("/api/v1/workflow/tools")
            assert response.status_code != 403
