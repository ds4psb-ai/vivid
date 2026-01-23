"""MCP V2 Router API Tests (P0 Phase 4 - 2026).

Tests for MCP V2 API endpoints.

Coverage Target: 80%+
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient

from app.mcp import (
    MCPServerConfig,
    MCPTransport,
    MCPPolicy,
    MCPToolInfo,
)
from app.mcp.mcp_executor import ToolExecutionResult


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_user_id():
    """Mock authenticated user ID."""
    return "test-user-123"


@pytest.fixture
def mock_admin_id():
    """Mock admin user ID."""
    return "admin-user-456"


@pytest.fixture
def mock_server_configs():
    """Mock MCP server configurations."""
    return [
        MCPServerConfig(
            server_id="tavily",
            name="Tavily Search",
            description="Web search API",
            transport=MCPTransport.STREAMABLE_HTTP,
            url="https://mcp.tavily.com",
            enabled=True,
            metadata={"tier": "core", "credit_cost": 2},
        ),
        MCPServerConfig(
            server_id="qdrant",
            name="Qdrant",
            description="Vector database",
            transport=MCPTransport.STREAMABLE_HTTP,
            url="http://localhost:6333/mcp",
            enabled=True,
            metadata={"tier": "internal", "credit_cost": 1},
        ),
    ]


@pytest.fixture
def mock_tools():
    """Mock MCP tools."""
    return [
        MCPToolInfo(name="search", description="Web search"),
        MCPToolInfo(name="query", description="Vector query"),
    ]


# =============================================================================
# Server Endpoints Tests
# =============================================================================

class TestMCPV2ServerEndpoints:
    """Tests for /mcp/v2/servers endpoints."""

    @pytest.mark.asyncio
    async def test_list_servers(
        self,
        async_client: AsyncClient,
        mock_user_id,
        mock_server_configs,
    ):
        """GET /mcp/v2/servers returns server list."""
        with patch("app.routers.mcp_v2.get_client_manager") as mock_manager:
            mock_manager.return_value.list_servers.return_value = mock_server_configs
            mock_manager.return_value.list_tools = AsyncMock(return_value=[])

            with patch("app.routers.mcp_v2.require_user_id", return_value=mock_user_id):
                response = await async_client.get("/api/v1/mcp/v2/servers")

        assert response.status_code == 200
        data = response.json()
        assert "servers" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_servers_filter_by_tier(
        self,
        async_client: AsyncClient,
        mock_user_id,
        mock_server_configs,
    ):
        """GET /mcp/v2/servers with tier filter."""
        with patch("app.routers.mcp_v2.get_client_manager") as mock_manager:
            mock_manager.return_value.list_servers.return_value = mock_server_configs
            mock_manager.return_value.list_tools = AsyncMock(return_value=[])

            with patch("app.routers.mcp_v2.require_user_id", return_value=mock_user_id):
                response = await async_client.get(
                    "/api/v1/mcp/v2/servers?tier=core"
                )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_server_details(
        self,
        async_client: AsyncClient,
        mock_user_id,
        mock_server_configs,
        mock_tools,
    ):
        """GET /mcp/v2/servers/{server_id} returns server details."""
        with patch("app.routers.mcp_v2.get_client_manager") as mock_manager:
            mock_manager.return_value.get_server_config.return_value = mock_server_configs[0]
            mock_manager.return_value.list_tools = AsyncMock(return_value=mock_tools)

            with patch("app.routers.mcp_v2.require_user_id", return_value=mock_user_id):
                response = await async_client.get("/api/v1/mcp/v2/servers/tavily")

        assert response.status_code == 200
        data = response.json()
        assert "server" in data
        assert "tools" in data

    @pytest.mark.asyncio
    async def test_get_server_not_found(
        self,
        async_client: AsyncClient,
        mock_user_id,
    ):
        """GET /mcp/v2/servers/{server_id} returns 404 for unknown server."""
        with patch("app.routers.mcp_v2.get_client_manager") as mock_manager:
            mock_manager.return_value.get_server_config.return_value = None

            with patch("app.routers.mcp_v2.require_user_id", return_value=mock_user_id):
                response = await async_client.get("/api/v1/mcp/v2/servers/nonexistent")

        assert response.status_code == 404


# =============================================================================
# Tool Endpoints Tests
# =============================================================================

class TestMCPV2ToolEndpoints:
    """Tests for /mcp/v2/tools and call endpoints."""

    @pytest.mark.asyncio
    async def test_list_all_tools(
        self,
        async_client: AsyncClient,
        mock_user_id,
        mock_server_configs,
        mock_tools,
    ):
        """GET /mcp/v2/tools returns all tools."""
        with patch("app.routers.mcp_v2.get_client_manager") as mock_manager, \
             patch("app.routers.mcp_v2.get_gateway") as mock_gateway:
            mock_manager.return_value.list_servers.return_value = mock_server_configs
            mock_gateway.return_value.list_tools = AsyncMock(return_value=[
                {"name": "search", "description": "Search"},
            ])

            with patch("app.routers.mcp_v2.require_user_id", return_value=mock_user_id):
                response = await async_client.get("/api/v1/mcp/v2/tools")

        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_call_mcp_tool(
        self,
        async_client: AsyncClient,
        mock_user_id,
    ):
        """POST /mcp/v2/call executes MCP tool."""
        from app.main import app
        from app.routers.mcp_v2 import get_gateway

        # Create mock gateway
        mock_gateway_instance = MagicMock()
        mock_gateway_instance.call_tool = AsyncMock(return_value={
            "success": True,
            "result": {"data": "search results"},
            "latency_ms": 150.0,
            "request_id": "abc123",
        })

        async def override_gateway():
            return mock_gateway_instance

        app.dependency_overrides[get_gateway] = override_gateway

        try:
            response = await async_client.post(
                "/api/v1/mcp/v2/call",
                json={
                    "server_id": "tavily",
                    "tool_name": "search",
                    "arguments": {"query": "test"},
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "result" in data
        finally:
            app.dependency_overrides.pop(get_gateway, None)

    @pytest.mark.asyncio
    async def test_call_mcp_tool_failure(
        self,
        async_client: AsyncClient,
        mock_user_id,
    ):
        """POST /mcp/v2/call handles failure."""
        from app.main import app
        from app.routers.mcp_v2 import get_gateway

        # Create mock gateway
        mock_gateway_instance = MagicMock()
        mock_gateway_instance.call_tool = AsyncMock(return_value={
            "success": False,
            "error": "Rate limit exceeded",
            "error_code": 429,
        })

        async def override_gateway():
            return mock_gateway_instance

        app.dependency_overrides[get_gateway] = override_gateway

        try:
            response = await async_client.post(
                "/api/v1/mcp/v2/call",
                json={
                    "server_id": "tavily",
                    "tool_name": "search",
                    "arguments": {"query": "test"},
                }
            )

            assert response.status_code == 200  # Error returned in response body
            data = response.json()
            assert data["success"] is False
            assert "error" in data
        finally:
            app.dependency_overrides.pop(get_gateway, None)

    @pytest.mark.asyncio
    async def test_execute_hybrid(
        self,
        async_client: AsyncClient,
        mock_user_id,
    ):
        """POST /mcp/v2/execute uses hybrid executor."""
        from app.main import app
        from app.routers.mcp_v2 import get_executor

        # Create mock executor
        mock_executor_instance = MagicMock()
        mock_executor_instance.execute = AsyncMock(return_value=ToolExecutionResult(
            success=True,
            outputs={"result": "data"},
            latency_ms=100.0,
            metadata={"execution_type": "mcp", "server_id": "tavily"},
        ))

        async def override_executor():
            return mock_executor_instance

        app.dependency_overrides[get_executor] = override_executor

        try:
            response = await async_client.post(
                "/api/v1/mcp/v2/execute",
                json={
                    "tool_id": "web_search",
                    "inputs": {"query": "test"},
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "execution_type" in data
        finally:
            app.dependency_overrides.pop(get_executor, None)


# =============================================================================
# Audit Endpoints Tests
# =============================================================================

class TestMCPV2AuditEndpoints:
    """Tests for /mcp/v2/audit endpoints."""

    @pytest.mark.asyncio
    async def test_get_audit_logs(
        self,
        async_client: AsyncClient,
        mock_user_id,
    ):
        """GET /mcp/v2/audit returns user's audit logs."""
        from app.mcp.gateway import MCPAuditEntry, MCPAction
        from datetime import datetime

        mock_logs = [
            MCPAuditEntry(
                user_id=mock_user_id,
                server_id="tavily",
                action=MCPAction.TOOL_CALL,
                tool_name="search",
                success=True,
                latency_ms=150.0,
            )
        ]

        with patch("app.routers.mcp_v2.get_gateway") as mock_gateway:
            mock_gateway.return_value.get_audit_logs = AsyncMock(return_value=mock_logs)

            with patch("app.routers.mcp_v2.require_user_id", return_value=mock_user_id):
                response = await async_client.get("/api/v1/mcp/v2/audit")

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data


# =============================================================================
# Health Endpoints Tests
# =============================================================================

class TestMCPV2HealthEndpoints:
    """Tests for /mcp/v2/health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(
        self,
        async_client: AsyncClient,
    ):
        """GET /mcp/v2/health returns system health."""
        with patch("app.routers.mcp_v2.get_client_manager") as mock_manager:
            mock_manager.return_value.health_check_all = AsyncMock(return_value={
                "tavily": True,
                "qdrant": True,
            })

            response = await async_client.get("/api/v1/mcp/v2/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "servers_total" in data
        assert "servers_healthy" in data

    @pytest.mark.asyncio
    async def test_health_check_degraded(
        self,
        async_client: AsyncClient,
    ):
        """GET /mcp/v2/health shows degraded status."""
        from app.main import app
        from app.routers.mcp_v2 import get_client_manager

        # Create a mock manager with degraded state
        mock_manager = MagicMock()
        mock_manager.health_check_all = AsyncMock(return_value={
            "tavily": True,
            "qdrant": False,  # One server unhealthy
        })

        async def override_manager():
            return mock_manager

        app.dependency_overrides[get_client_manager] = override_manager

        try:
            response = await async_client.get("/api/v1/mcp/v2/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
        finally:
            app.dependency_overrides.pop(get_client_manager, None)


# =============================================================================
# Admin Endpoints Tests
# =============================================================================

class TestMCPV2AdminEndpoints:
    """Tests for /mcp/v2/admin endpoints."""

    @pytest.mark.asyncio
    async def test_create_policy_requires_admin(
        self,
        async_client: AsyncClient,
        mock_user_id,  # Regular user, not admin
    ):
        """POST /mcp/v2/admin/policies requires admin role."""
        with patch("app.routers.mcp_v2.require_admin") as mock_auth:
            mock_auth.side_effect = Exception("Not authorized")

            response = await async_client.post(
                "/api/v1/mcp/v2/admin/policies",
                json={
                    "policy_id": "new-policy",
                    "name": "New Policy",
                }
            )

        # Should fail due to authorization
        assert response.status_code != 200

    @pytest.mark.asyncio
    async def test_create_policy(
        self,
        admin_async_client: AsyncClient,
        mock_admin_id,
    ):
        """POST /mcp/v2/admin/policies creates policy."""
        from app.main import app
        from app.routers.mcp_v2 import require_admin  # Use the router's own require_admin

        # Override require_admin to return admin user ID
        async def override_admin():
            return mock_admin_id

        app.dependency_overrides[require_admin] = override_admin

        try:
            with patch("app.routers.mcp_v2.get_gateway") as mock_gateway:
                mock_gateway.return_value.register_policy = MagicMock()

                response = await admin_async_client.post(
                    "/api/v1/mcp/v2/admin/policies",
                    json={
                        "policy_id": "new-policy",
                        "name": "New Policy",
                        "max_calls_per_minute": 50,
                    }
                )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["policy_id"] == "new-policy"
        finally:
            app.dependency_overrides.pop(require_admin, None)

    @pytest.mark.asyncio
    async def test_list_policies(
        self,
        admin_async_client: AsyncClient,
        mock_admin_id,
    ):
        """GET /mcp/v2/admin/policies lists policies."""
        from app.main import app
        from app.routers.mcp_v2 import require_admin  # Use the router's own require_admin

        mock_policy = MCPPolicy(
            policy_id="test-policy",
            name="Test Policy",
        )

        # Override require_admin to return admin user ID
        async def override_admin():
            return mock_admin_id

        app.dependency_overrides[require_admin] = override_admin

        try:
            with patch("app.routers.mcp_v2.get_gateway") as mock_gateway:
                mock_gateway.return_value._policies = {"test-policy": mock_policy}
                mock_gateway.return_value._default_policy = mock_policy

                response = await admin_async_client.get("/api/v1/mcp/v2/admin/policies")

            assert response.status_code == 200
            data = response.json()
            assert "policies" in data
            assert "total" in data
        finally:
            app.dependency_overrides.pop(require_admin, None)


# =============================================================================
# Validation Tests
# =============================================================================

class TestMCPV2Validation:
    """Tests for request validation."""

    @pytest.mark.asyncio
    async def test_call_tool_invalid_server_id(
        self,
        async_client: AsyncClient,
        mock_user_id,
    ):
        """POST /mcp/v2/call validates server_id."""
        with patch("app.routers.mcp_v2.require_user_id", return_value=mock_user_id):
            response = await async_client.post(
                "/api/v1/mcp/v2/call",
                json={
                    "server_id": "invalid@server!",  # Invalid characters
                    "tool_name": "search",
                    "arguments": {},
                }
            )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_call_tool_empty_tool_name(
        self,
        async_client: AsyncClient,
        mock_user_id,
    ):
        """POST /mcp/v2/call validates tool_name."""
        with patch("app.routers.mcp_v2.require_user_id", return_value=mock_user_id):
            response = await async_client.post(
                "/api/v1/mcp/v2/call",
                json={
                    "server_id": "tavily",
                    "tool_name": "",  # Empty
                    "arguments": {},
                }
            )

        assert response.status_code == 422  # Validation error


# =============================================================================
# Stats Endpoints Tests
# =============================================================================

class TestMCPV2StatsEndpoints:
    """Tests for /mcp/v2/stats endpoint."""

    @pytest.mark.asyncio
    async def test_get_stats(
        self,
        async_client: AsyncClient,
        mock_user_id,
        mock_server_configs,
    ):
        """GET /mcp/v2/stats returns system statistics."""
        from app.mcp.gateway import MCPAuditEntry, MCPAction

        mock_logs = [
            MCPAuditEntry(
                user_id=mock_user_id,
                server_id="tavily",
                action=MCPAction.TOOL_CALL,
                success=True,
                latency_ms=150.0,
                credit_cost=2,
            )
        ]

        with patch("app.routers.mcp_v2.get_client_manager") as mock_manager, \
             patch("app.routers.mcp_v2.get_gateway") as mock_gateway:
            mock_manager.return_value.list_servers.return_value = mock_server_configs
            mock_manager.return_value.list_tools = AsyncMock(return_value=[])
            mock_gateway.return_value.get_audit_logs = AsyncMock(return_value=mock_logs)

            with patch("app.routers.mcp_v2.require_user_id", return_value=mock_user_id):
                response = await async_client.get("/api/v1/mcp/v2/stats")

        assert response.status_code == 200
        data = response.json()
        assert "servers" in data
        assert "tools" in data
        assert "usage" in data
        assert "config" in data
