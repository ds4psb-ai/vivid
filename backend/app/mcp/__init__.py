"""MCP Integration Module (P0 Phase 4 - 2026).

Model Context Protocol 클라이언트/게이트웨이 통합.

2026 Best Practices:
    - Streamable HTTP transport (SSE deprecated in MCP 2025-03-26)
    - Centralized Gateway with Auth/Audit/Rate Limiting
    - FastMCP for internal MCP servers
    - Circuit Breaker for external servers
    - Hybrid Executor (Native + MCP)

Components:
    - types: MCP 타입 정의
    - client: MCP Client Manager (외부 서버 연결)
    - gateway: MCP Gateway (인증/감사/정책)
    - default_servers: 기본 MCP 서버 설정
    - mcp_executor: DAG-MCP 브릿지

Usage:
    from app.mcp import (
        # Client
        MCPClientManager,
        get_mcp_client_manager,
        # Gateway
        MCPGateway,
        get_mcp_gateway,
        # Types
        MCPServerConfig,
        MCPTransport,
        MCPToolCall,
        # Executor
        HybridToolExecutor,
        get_hybrid_executor,
    )

    # Call external MCP tool
    manager = get_mcp_client_manager()
    result = await manager.call_tool(
        server_id="tavily",
        tool_name="tavily-search",
        arguments={"query": "AI trends 2026"},
    )

    # Call through gateway (with auth/audit)
    gateway = get_mcp_gateway()
    result = await gateway.call_tool(
        user_id="user123",
        server_id="tavily",
        tool_name="tavily-search",
        arguments={"query": "AI trends 2026"},
    )

    # Use hybrid executor (auto-routes to MCP or native)
    executor = await get_hybrid_executor()
    result = await executor.execute(
        tool_id="web_search",
        inputs={"query": "AI trends 2026"},
        context={"user_id": "user123"},
    )
"""

from app.mcp.types import (
    MCPTransport,
    MCPServerConfig,
    MCPToolCall,
    MCPToolInfo,
    MCPResourceInfo,
    MCPCapabilities,
    MCPError,
    MCPErrorCode,
)
from app.mcp.client import (
    MCPClientManager,
    get_mcp_client_manager,
    reset_mcp_client_manager,
)
from app.mcp.gateway import (
    MCPGateway,
    MCPPolicy,
    MCPAuditEntry,
    get_mcp_gateway,
)
from app.mcp.default_servers import (
    get_all_server_configs,
    get_core_server_configs,
    get_premium_server_configs,
    get_internal_server_configs,
    register_default_servers,
    DEFAULT_TOOL_MAPPINGS,
    get_tool_mapping,
    get_server_tools,
)
from app.mcp.mcp_executor import (
    ToolExecutionResult,
    MCPToolExecutor,
    NativeToolExecutor,
    HybridToolExecutor,
    DAGToolExecutorAdapter,
    create_mcp_executor,
    create_hybrid_executor,
    create_dag_executor,
    get_hybrid_executor,
    reset_hybrid_executor,
)

__all__ = [
    # Types
    "MCPTransport",
    "MCPServerConfig",
    "MCPToolCall",
    "MCPToolInfo",
    "MCPResourceInfo",
    "MCPCapabilities",
    "MCPError",
    "MCPErrorCode",
    # Client
    "MCPClientManager",
    "get_mcp_client_manager",
    "reset_mcp_client_manager",
    # Gateway
    "MCPGateway",
    "MCPPolicy",
    "MCPAuditEntry",
    "get_mcp_gateway",
    # Default Servers
    "get_all_server_configs",
    "get_core_server_configs",
    "get_premium_server_configs",
    "get_internal_server_configs",
    "register_default_servers",
    "DEFAULT_TOOL_MAPPINGS",
    "get_tool_mapping",
    "get_server_tools",
    # Executor
    "ToolExecutionResult",
    "MCPToolExecutor",
    "NativeToolExecutor",
    "HybridToolExecutor",
    "DAGToolExecutorAdapter",
    "create_mcp_executor",
    "create_hybrid_executor",
    "create_dag_executor",
    "get_hybrid_executor",
    "reset_hybrid_executor",
]
