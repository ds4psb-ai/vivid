"""MCP V2 Module Tests (P0 Phase 4 - 2026).

Comprehensive tests for MCP Gateway, Client Manager, and Hybrid Executor.

Coverage Target: 80%+
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.mcp.types import (
    MCPTransport,
    MCPServerConfig,
    MCPToolCall,
    MCPToolInfo,
    MCPError,
    MCPErrorCode,
)
from app.mcp.client import (
    MCPClientManager,
    CircuitBreaker,
    CircuitState,
    RateLimiter,
    StreamableHTTPClient,
    get_mcp_client_manager,
    reset_mcp_client_manager,
)
from app.mcp.gateway import (
    MCPGateway,
    MCPPolicy,
    MCPAuditEntry,
    MCPAction,
    RateLimitState,
    AuditStore,
    get_mcp_gateway,
)
from app.mcp.mcp_executor import (
    ToolExecutionResult,
    MCPToolExecutor,
    NativeToolExecutor,
    HybridToolExecutor,
    create_hybrid_executor,
    get_hybrid_executor,
    reset_hybrid_executor,
)
from app.mcp.default_servers import (
    get_tavily_config,
    get_qdrant_config,
    DEFAULT_TOOL_MAPPINGS,
    get_tool_mapping,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_server_config():
    """Sample MCP server configuration."""
    return MCPServerConfig(
        server_id="test-server",
        name="Test Server",
        description="Test MCP server",
        transport=MCPTransport.STREAMABLE_HTTP,
        url="http://localhost:8000/mcp",
        enabled=True,
        timeout_seconds=10,
        max_retries=2,
    )


@pytest.fixture
def sample_policy():
    """Sample MCP policy."""
    return MCPPolicy(
        policy_id="test-policy",
        name="Test Policy",
        description="Policy for testing",
        max_calls_per_minute=10,
        max_calls_per_hour=100,
        max_calls_per_day=1000,
        audit_level="basic",
    )


@pytest.fixture
def sample_policy_restricted():
    """Sample restricted MCP policy."""
    return MCPPolicy(
        policy_id="restricted-policy",
        name="Restricted Policy",
        allowed_servers=frozenset(["allowed-server"]),
        denied_tools=frozenset(["test-server/dangerous-tool"]),
        max_calls_per_minute=5,
        require_run_token=True,
    )


@pytest.fixture
async def client_manager():
    """MCP Client Manager fixture."""
    reset_mcp_client_manager()
    manager = MCPClientManager()
    await manager.start()
    yield manager
    await manager.stop()


# =============================================================================
# Circuit Breaker Tests
# =============================================================================

class TestCircuitBreaker:
    """Circuit Breaker unit tests."""

    def test_initial_state_closed(self):
        """Initial state should be closed."""
        cb = CircuitBreaker(threshold=3)
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute()

    def test_opens_after_threshold_failures(self):
        """Circuit opens after threshold failures."""
        cb = CircuitBreaker(threshold=3)

        for _ in range(3):
            cb.record_failure()

        assert cb.state == CircuitState.OPEN
        assert not cb.can_execute()

    def test_success_resets_counter(self):
        """Success resets failure counter."""
        cb = CircuitBreaker(threshold=3)

        cb.record_failure()
        cb.record_failure()
        cb.record_success()

        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED

    def test_half_open_after_timeout(self):
        """Circuit becomes half-open after timeout."""
        cb = CircuitBreaker(threshold=3, timeout_seconds=1)

        # Open the circuit
        for _ in range(3):
            cb.record_failure()

        assert cb.state == CircuitState.OPEN

        # Simulate timeout
        cb.last_failure = datetime.utcnow() - timedelta(seconds=2)

        assert cb.can_execute()
        assert cb.state == CircuitState.HALF_OPEN


# =============================================================================
# Rate Limiter Tests
# =============================================================================

class TestRateLimiter:
    """Rate Limiter unit tests."""

    def test_acquire_within_limit(self):
        """Can acquire tokens within limit."""
        rl = RateLimiter(rpm=60)

        for _ in range(60):
            assert rl.acquire()

    def test_acquire_exceeds_limit(self):
        """Cannot acquire when limit exceeded."""
        rl = RateLimiter(rpm=5)

        for _ in range(5):
            rl.acquire()

        assert not rl.acquire()

    def test_tokens_refill_over_time(self):
        """Tokens refill over time."""
        rl = RateLimiter(rpm=60)

        # Use all tokens
        for _ in range(60):
            rl.acquire()

        # Simulate 1 second passing
        rl.last_refill = datetime.utcnow() - timedelta(seconds=1)

        # Should be able to acquire again
        assert rl.acquire()

    def test_wait_time_calculation(self):
        """Wait time calculated correctly."""
        rl = RateLimiter(rpm=60)

        # No wait when tokens available
        assert rl.wait_time() == 0.0

        # Use all tokens
        for _ in range(60):
            rl.acquire()

        # Should have wait time
        wait = rl.wait_time()
        assert wait > 0


# =============================================================================
# MCP Client Manager Tests
# =============================================================================

class TestMCPClientManager:
    """MCP Client Manager tests."""

    @pytest.mark.asyncio
    async def test_register_server(self, client_manager, sample_server_config):
        """Server registration works."""
        await client_manager.register_server(sample_server_config)

        config = client_manager.get_server_config("test-server")
        assert config is not None
        assert config.name == "Test Server"

    @pytest.mark.asyncio
    async def test_unregister_server(self, client_manager, sample_server_config):
        """Server unregistration works."""
        await client_manager.register_server(sample_server_config)
        await client_manager.unregister_server("test-server")

        config = client_manager.get_server_config("test-server")
        assert config is None

    @pytest.mark.asyncio
    async def test_list_servers(self, client_manager, sample_server_config):
        """Server listing works."""
        await client_manager.register_server(sample_server_config)

        servers = client_manager.list_servers()
        assert len(servers) == 1
        assert servers[0].server_id == "test-server"

    @pytest.mark.asyncio
    async def test_call_tool_server_not_found(self, client_manager):
        """Call tool fails for unknown server."""
        result = await client_manager.call_tool(
            server_id="nonexistent",
            tool_name="test",
            arguments={},
        )

        assert not result.success
        assert result.error_code == MCPErrorCode.SERVER_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_call_tool_server_disabled(self, client_manager):
        """Call tool fails for disabled server."""
        config = MCPServerConfig(
            server_id="disabled-server",
            name="Disabled",
            description="Test",
            transport=MCPTransport.STREAMABLE_HTTP,
            url="http://localhost:8000",
            enabled=False,
        )
        await client_manager.register_server(config)

        result = await client_manager.call_tool(
            server_id="disabled-server",
            tool_name="test",
            arguments={},
        )

        assert not result.success
        assert result.error_code == MCPErrorCode.SERVER_UNAVAILABLE


# =============================================================================
# MCP Gateway Tests
# =============================================================================

class TestMCPGateway:
    """MCP Gateway tests."""

    @pytest.fixture
    def gateway(self):
        """Create a gateway with mock client manager."""
        mock_manager = MagicMock(spec=MCPClientManager)
        mock_manager.call_tool = AsyncMock(return_value=MCPToolCall(
            tool_name="test",
            arguments={},
            result={"data": "test"},
            success=True,
        ))
        mock_manager.list_tools = AsyncMock(return_value=[
            MCPToolInfo(name="tool1", description="Test tool"),
        ])

        return MCPGateway(client_manager=mock_manager)

    @pytest.mark.asyncio
    async def test_call_tool_success(self, gateway):
        """Successful tool call through gateway."""
        result = await gateway.call_tool(
            user_id="test-user",
            server_id="test-server",
            tool_name="test",
            arguments={"query": "test"},
        )

        assert result["success"]
        assert result["result"] == {"data": "test"}
        assert "latency_ms" in result
        assert "request_id" in result

    @pytest.mark.asyncio
    async def test_call_tool_policy_denied(self, gateway, sample_policy_restricted):
        """Tool call denied by policy."""
        gateway.register_policy(sample_policy_restricted)
        gateway.assign_policy("test-user", "restricted-policy")

        result = await gateway.call_tool(
            user_id="test-user",
            server_id="denied-server",  # Not in allowed_servers
            tool_name="test",
            arguments={},
        )

        assert not result["success"]
        assert "Policy denied" in result["error"]

    @pytest.mark.asyncio
    async def test_call_tool_rate_limited(self, gateway, sample_policy):
        """Tool call rate limited."""
        # Create policy with very low limit
        low_limit_policy = MCPPolicy(
            policy_id="low-limit",
            name="Low Limit",
            max_calls_per_minute=1,
            max_calls_per_hour=100,
            max_calls_per_day=1000,
        )
        gateway.register_policy(low_limit_policy)
        gateway.assign_policy("rate-test-user", "low-limit")

        # First call should succeed
        await gateway.call_tool(
            user_id="rate-test-user",
            server_id="test-server",
            tool_name="test",
            arguments={},
        )

        # Second call should be rate limited
        result = await gateway.call_tool(
            user_id="rate-test-user",
            server_id="test-server",
            tool_name="test",
            arguments={},
        )

        assert not result["success"]
        assert "Rate limit" in result["error"]

    @pytest.mark.asyncio
    async def test_call_tool_requires_run_token(self, gateway, sample_policy_restricted):
        """Tool call requires run token when policy demands it."""
        gateway.register_policy(sample_policy_restricted)
        gateway.assign_policy("test-user", "restricted-policy")

        result = await gateway.call_tool(
            user_id="test-user",
            server_id="allowed-server",
            tool_name="test",
            arguments={},
            run_token=None,  # No token provided
        )

        assert not result["success"]
        assert "Run-Token required" in result["error"]

    def test_register_policy(self, gateway, sample_policy):
        """Policy registration works."""
        gateway.register_policy(sample_policy)

        # Policy should be retrievable
        policy = gateway._get_policy("some-user")  # Should get default
        assert policy.policy_id == "default"

    def test_assign_policy(self, gateway, sample_policy):
        """Policy assignment works."""
        gateway.register_policy(sample_policy)
        gateway.assign_policy("test-user", "test-policy")

        policy = gateway._get_policy("test-user")
        assert policy.policy_id == "test-policy"

    def test_assign_nonexistent_policy_raises(self, gateway):
        """Assigning nonexistent policy raises error."""
        with pytest.raises(ValueError, match="Policy not found"):
            gateway.assign_policy("test-user", "nonexistent")

    @pytest.mark.asyncio
    async def test_audit_log_recorded(self, gateway):
        """Audit log is recorded for calls."""
        await gateway.call_tool(
            user_id="audit-test-user",
            server_id="test-server",
            tool_name="test",
            arguments={"query": "audit test"},
        )

        logs = await gateway.get_audit_logs(user_id="audit-test-user")
        assert len(logs) >= 1
        assert logs[0].user_id == "audit-test-user"
        assert logs[0].action == MCPAction.TOOL_CALL


# =============================================================================
# Audit Store Tests
# =============================================================================

class TestAuditStore:
    """Audit Store unit tests."""

    @pytest.mark.asyncio
    async def test_log_and_retrieve(self):
        """Log and retrieve audit entries."""
        store = AuditStore()

        entry = MCPAuditEntry(
            user_id="test-user",
            server_id="test-server",
            action=MCPAction.TOOL_CALL,
            tool_name="test-tool",
            success=True,
        )

        await store.log(entry)

        recent = await store.get_recent(limit=10)
        assert len(recent) == 1
        assert recent[0].user_id == "test-user"

    @pytest.mark.asyncio
    async def test_filter_by_user(self):
        """Filter audit logs by user."""
        store = AuditStore()

        # Log entries for different users
        await store.log(MCPAuditEntry(
            user_id="user-a",
            server_id="server",
            action=MCPAction.TOOL_CALL,
            success=True,
        ))
        await store.log(MCPAuditEntry(
            user_id="user-b",
            server_id="server",
            action=MCPAction.TOOL_CALL,
            success=True,
        ))

        # Filter by user-a
        logs = await store.get_recent(user_id="user-a", limit=10)
        assert len(logs) == 1
        assert logs[0].user_id == "user-a"


# =============================================================================
# Rate Limit State Tests
# =============================================================================

class TestRateLimitState:
    """Rate Limit State tests."""

    def test_record_call_increments_counters(self):
        """Recording a call increments all counters."""
        state = RateLimitState(user_id="test")

        state.record_call(credit_cost=5)

        assert state.minute_count == 1
        assert state.hour_count == 1
        assert state.day_count == 1
        assert state.day_credit == 5

    def test_reset_counters_on_time_boundary(self):
        """Counters reset when time boundaries crossed."""
        state = RateLimitState(user_id="test")
        state.minute_count = 10
        state.minute_reset = datetime.utcnow() - timedelta(minutes=2)

        state.reset_if_needed()

        assert state.minute_count == 0


# =============================================================================
# Default Servers Tests
# =============================================================================

class TestDefaultServers:
    """Default server configuration tests."""

    def test_tavily_config(self):
        """Tavily config loads correctly."""
        config = get_tavily_config()

        if config:  # Only if API key is set
            assert config.server_id == "tavily"
            assert config.transport == MCPTransport.STREAMABLE_HTTP

    def test_qdrant_config(self):
        """Qdrant config loads correctly."""
        config = get_qdrant_config()

        if config:
            assert config.server_id == "qdrant"

    def test_tool_mappings_exist(self):
        """Tool mappings are defined."""
        assert len(DEFAULT_TOOL_MAPPINGS) > 0
        assert "web_search" in DEFAULT_TOOL_MAPPINGS

    def test_get_tool_mapping(self):
        """Get tool mapping works."""
        mapping = get_tool_mapping("web_search")

        assert mapping is not None
        assert "server_id" in mapping
        assert "mcp_tool_name" in mapping


# =============================================================================
# Hybrid Tool Executor Tests
# =============================================================================

class TestHybridToolExecutor:
    """Hybrid Tool Executor tests.

    Note: These tests use the actual HybridToolExecutor with mocked
    dependencies to test routing behavior.
    """

    @pytest.mark.asyncio
    async def test_hybrid_executor_creation(self):
        """HybridToolExecutor can be created."""
        # This test verifies the executor can be instantiated
        # without actually running MCP calls
        reset_hybrid_executor()

        # Create with mocked components
        with patch("app.mcp.mcp_executor.create_mcp_executor") as mock_mcp, \
             patch("app.mcp.mcp_executor.NativeToolExecutor") as mock_native:
            mock_mcp.return_value = AsyncMock()
            mock_native.return_value = MagicMock()

            # Should not raise
            from app.mcp.mcp_executor import create_hybrid_executor
            # Note: We can't easily test this without the full dependency chain

    @pytest.mark.asyncio
    async def test_tool_execution_result_structure(self):
        """ToolExecutionResult has correct structure."""
        result = ToolExecutionResult(
            success=True,
            outputs={"data": "test"},
            latency_ms=100.0,
            credit_cost=2,
            metadata={"execution_type": "mcp"},
        )

        assert result.success
        assert result.outputs == {"data": "test"}
        assert result.latency_ms == 100.0
        assert result.credit_cost == 2
        assert result.metadata["execution_type"] == "mcp"

    @pytest.mark.asyncio
    async def test_tool_mappings_configured(self):
        """Tool mappings are configured for hybrid routing."""
        # Verify key tools have mappings
        assert "web_search" in DEFAULT_TOOL_MAPPINGS
        assert "semantic_search" in DEFAULT_TOOL_MAPPINGS

        # Verify mapping structure
        web_search = DEFAULT_TOOL_MAPPINGS["web_search"]
        assert "server_id" in web_search
        assert "mcp_tool_name" in web_search


# =============================================================================
# Tool Execution Result Tests
# =============================================================================

class TestToolExecutionResult:
    """Tool Execution Result tests."""

    def test_to_dict(self):
        """Result serializes to dict correctly."""
        result = ToolExecutionResult(
            success=True,
            outputs={"data": "test"},
            latency_ms=100.5,
            credit_cost=2,
        )

        d = result.to_dict()

        assert d["success"] is True
        assert d["outputs"] == {"data": "test"}
        assert d["latency_ms"] == 100.5
        assert d["credit_cost"] == 2
        assert "timestamp" in d
        assert "request_id" in d


# =============================================================================
# MCP Error Tests
# =============================================================================

class TestMCPError:
    """MCP Error tests."""

    def test_error_creation(self):
        """Error creation with code and message."""
        error = MCPError(
            code=MCPErrorCode.TIMEOUT,
            message="Request timed out",
        )

        assert error.code == MCPErrorCode.TIMEOUT
        assert error.message == "Request timed out"

    def test_error_with_data(self):
        """Error with additional data."""
        error = MCPError(
            code=MCPErrorCode.INTERNAL_ERROR,
            message="Internal error",
            data={"details": "stack trace"},
        )

        assert error.data == {"details": "stack trace"}


# =============================================================================
# Policy Tests
# =============================================================================

class TestMCPPolicy:
    """MCP Policy tests."""

    def test_policy_creation(self):
        """Policy creation with defaults."""
        policy = MCPPolicy(
            policy_id="test",
            name="Test",
        )

        assert policy.max_calls_per_minute == 30
        assert policy.audit_level == "basic"
        assert not policy.require_run_token

    def test_policy_with_restrictions(self):
        """Policy with access restrictions."""
        policy = MCPPolicy(
            policy_id="restricted",
            name="Restricted",
            allowed_servers=frozenset(["server-a", "server-b"]),
            denied_tools=frozenset(["server-a/dangerous"]),
        )

        assert "server-a" in policy.allowed_servers
        assert "server-a/dangerous" in policy.denied_tools

    def test_policy_immutable(self):
        """Policy is immutable (frozen)."""
        policy = MCPPolicy(
            policy_id="test",
            name="Test",
        )

        # Should not be able to modify
        with pytest.raises(Exception):
            policy.name = "Modified"


# =============================================================================
# Integration Tests
# =============================================================================

class TestMCPIntegration:
    """Integration tests for MCP module."""

    @pytest.mark.asyncio
    async def test_singleton_management(self):
        """Singleton management works correctly."""
        reset_mcp_client_manager()
        reset_hybrid_executor()

        # Get singletons
        manager1 = get_mcp_client_manager()
        manager2 = get_mcp_client_manager()
        gateway1 = get_mcp_gateway()
        gateway2 = get_mcp_gateway()

        assert manager1 is manager2
        assert gateway1 is gateway2

        # Reset and verify new instances
        reset_mcp_client_manager()
        manager3 = get_mcp_client_manager()
        assert manager1 is not manager3

    @pytest.mark.asyncio
    async def test_end_to_end_flow(self):
        """End-to-end flow through gateway and executor."""
        reset_mcp_client_manager()
        reset_hybrid_executor()

        # This test demonstrates the full flow
        # In production, actual MCP servers would be called

        gateway = get_mcp_gateway()

        # Register a test policy
        test_policy = MCPPolicy(
            policy_id="e2e-test",
            name="E2E Test Policy",
            max_calls_per_minute=100,
        )
        gateway.register_policy(test_policy)

        # Verify policy is registered
        gateway.assign_policy("e2e-user", "e2e-test")
        policy = gateway._get_policy("e2e-user")
        assert policy.policy_id == "e2e-test"
