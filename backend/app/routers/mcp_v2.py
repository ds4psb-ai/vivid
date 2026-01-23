"""MCP V2 API Router (P0 Phase 4 - 2026).

MCP Gateway 통합 API 엔드포인트.

2026 Best Practices:
    - Gateway-based authentication and authorization
    - Comprehensive audit logging
    - Policy-based access control
    - Rate limiting at API level
    - Hybrid execution (Native + MCP)

Endpoints:
    - GET  /mcp/v2/servers           - List registered MCP servers
    - GET  /mcp/v2/servers/{id}      - Get server details
    - GET  /mcp/v2/servers/{id}/tools - List server tools
    - GET  /mcp/v2/servers/{id}/health - Server health check
    - GET  /mcp/v2/tools             - List all available tools
    - POST /mcp/v2/call              - Call MCP tool via gateway
    - POST /mcp/v2/execute           - Execute via hybrid executor
    - GET  /mcp/v2/audit             - Get audit logs
    - GET  /mcp/v2/health            - MCP system health
    - POST /mcp/v2/admin/policies    - Create/update policy (admin)
    - GET  /mcp/v2/admin/policies    - List policies (admin)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_user_id, get_is_admin
from app.config import settings
from app.database import get_db
from app.utils.error_sanitize import safe_error_detail
from app.mcp import (
    MCPClientManager,
    get_mcp_client_manager,
    MCPGateway,
    get_mcp_gateway,
    MCPPolicy,
    MCPAuditEntry,
    HybridToolExecutor,
    get_hybrid_executor,
    MCPServerConfig,
    MCPTransport,
    get_all_server_configs,
    register_default_servers,
    get_tool_mapping,
    DEFAULT_TOOL_MAPPINGS,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp/v2", tags=["MCP-V2"])


# =============================================================================
# Admin Dependency
# =============================================================================

async def require_admin(
    request: Request,
    user_id: str = Depends(require_user_id),
) -> str:
    """Require admin role.

    Combines user authentication with admin role check.

    Returns:
        User ID if admin

    Raises:
        HTTPException 403 if not admin
    """
    is_admin = await get_is_admin(request)
    if not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required",
        )
    return user_id


# =============================================================================
# Request/Response Models
# =============================================================================

class MCPToolCallRequest(BaseModel):
    """MCP 도구 호출 요청.

    Gateway를 통한 MCP 도구 호출에 사용됩니다.

    Attributes:
        server_id: MCP 서버 ID (e.g., "tavily", "qdrant")
        tool_name: 호출할 도구 이름
        arguments: 도구 인자
        run_token: Run-Token (선택적, 크레딧 차감용)
    """
    server_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$", description="MCP 서버 ID")
    tool_name: str = Field(..., min_length=1, max_length=128, description="도구 이름")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="도구 인자")
    run_token: Optional[str] = Field(default=None, description="Run-Token (크레딧 차감용)")

    @field_validator("server_id")
    @classmethod
    def validate_server_id(cls, v: str) -> str:
        """서버 ID 유효성 검사."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Server ID must be alphanumeric with hyphens/underscores")
        return v.lower()


class MCPToolCallResponse(BaseModel):
    """MCP 도구 호출 응답."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[int] = None
    latency_ms: float = 0.0
    request_id: str = ""
    credit_cost: int = 0


class MCPExecuteRequest(BaseModel):
    """Hybrid Executor 실행 요청.

    Vivid tool ID를 사용하여 자동으로 MCP 또는 Native로 라우팅됩니다.

    Attributes:
        tool_id: Vivid 도구 ID (e.g., "web_search", "rag_query")
        inputs: 입력 데이터
        context: 실행 컨텍스트 (user_id, session_id 등)
    """
    tool_id: str = Field(..., min_length=1, max_length=128, description="Vivid 도구 ID")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="입력 데이터")
    context: Dict[str, Any] = Field(default_factory=dict, description="실행 컨텍스트")


class MCPExecuteResponse(BaseModel):
    """Hybrid Executor 실행 응답."""
    success: bool
    outputs: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    error_code: Optional[int] = None
    latency_ms: float = 0.0
    credit_cost: int = 0
    request_id: str = ""
    execution_type: str = ""  # "mcp" or "native"
    server_id: Optional[str] = None


class MCPServerInfo(BaseModel):
    """MCP 서버 정보."""
    server_id: str
    name: str
    description: str
    transport: str
    enabled: bool
    url: Optional[str] = None
    tier: str = "core"  # core, premium, internal
    credit_cost: int = 1
    tools_count: int = 0


class MCPToolInfo(BaseModel):
    """MCP 도구 정보."""
    name: str
    description: str
    server_id: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    credit_cost: int = 1


class MCPPolicyRequest(BaseModel):
    """MCP 정책 생성/수정 요청."""
    policy_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="")
    allowed_servers: List[str] = Field(default_factory=list)
    denied_servers: List[str] = Field(default_factory=list)
    allowed_tools: List[str] = Field(default_factory=list)
    denied_tools: List[str] = Field(default_factory=list)
    max_calls_per_minute: int = Field(default=30, ge=1, le=1000)
    max_calls_per_hour: int = Field(default=500, ge=1, le=10000)
    max_calls_per_day: int = Field(default=5000, ge=1, le=100000)
    max_credit_per_call: int = Field(default=100, ge=1)
    max_credit_per_day: int = Field(default=10000, ge=1)
    require_run_token: bool = Field(default=False)
    audit_level: str = Field(default="basic", pattern="^(none|basic|full)$")


class MCPAuditLogResponse(BaseModel):
    """MCP 감사 로그 응답."""
    id: str
    timestamp: datetime
    user_id: str
    server_id: str
    action: str
    tool_name: Optional[str] = None
    success: bool
    latency_ms: float = 0.0
    error_message: Optional[str] = None
    credit_cost: int = 0
    request_id: str = ""


class MCPHealthResponse(BaseModel):
    """MCP 시스템 헬스 응답."""
    status: str  # "healthy", "degraded", "unhealthy"
    servers_total: int
    servers_healthy: int
    servers_status: Dict[str, bool]
    gateway_status: str
    executor_status: str
    last_check: datetime


# =============================================================================
# Dependencies
# =============================================================================

async def get_client_manager() -> MCPClientManager:
    """MCP Client Manager 의존성."""
    manager = get_mcp_client_manager()
    if not manager._started:
        await manager.start()
        # 기본 서버 등록
        await register_default_servers(manager)
    return manager


async def get_gateway() -> MCPGateway:
    """MCP Gateway 의존성."""
    return get_mcp_gateway()


async def get_executor() -> HybridToolExecutor:
    """Hybrid Executor 의존성."""
    return await get_hybrid_executor()


def get_client_ip(request: Request) -> str:
    """클라이언트 IP 추출."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# =============================================================================
# Server Endpoints
# =============================================================================

@router.get("/servers", response_model=Dict[str, Any])
async def list_servers(
    user_id: str = Depends(require_user_id),
    manager: MCPClientManager = Depends(get_client_manager),
    tier: Optional[str] = Query(default=None, description="Filter by tier (core, premium, internal)"),
    enabled_only: bool = Query(default=True, description="Only show enabled servers"),
):
    """등록된 MCP 서버 목록.

    사용자가 접근 가능한 MCP 서버 목록을 반환합니다.

    Args:
        tier: 서버 티어 필터 (core, premium, internal)
        enabled_only: 활성화된 서버만 표시

    Returns:
        서버 목록 및 개수
    """
    logger.info(f"MCP V2: list_servers by user={user_id[:8]}")

    servers = manager.list_servers()

    # 필터링
    if enabled_only:
        servers = [s for s in servers if s.enabled]

    if tier:
        servers = [s for s in servers if s.metadata.get("tier") == tier]

    # 도구 개수 추가
    server_infos = []
    for server in servers:
        tools = await manager.list_tools(server.server_id)
        server_infos.append(MCPServerInfo(
            server_id=server.server_id,
            name=server.name,
            description=server.description,
            transport=server.transport.value,
            enabled=server.enabled,
            url=server.url if server.metadata.get("show_url", False) else None,
            tier=server.metadata.get("tier", "core"),
            credit_cost=server.metadata.get("credit_cost", 1),
            tools_count=len(tools),
        ))

    return {
        "servers": [s.model_dump() for s in server_infos],
        "total": len(server_infos),
        "available_tiers": ["core", "premium", "internal"],
    }


@router.get("/servers/{server_id}", response_model=Dict[str, Any])
async def get_server(
    server_id: str,
    user_id: str = Depends(require_user_id),
    manager: MCPClientManager = Depends(get_client_manager),
):
    """특정 MCP 서버 상세 정보.

    Args:
        server_id: 서버 ID

    Returns:
        서버 상세 정보 및 도구 목록
    """
    config = manager.get_server_config(server_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Server not found: {server_id}")

    tools = await manager.list_tools(server_id)

    return {
        "server": MCPServerInfo(
            server_id=config.server_id,
            name=config.name,
            description=config.description,
            transport=config.transport.value,
            enabled=config.enabled,
            tier=config.metadata.get("tier", "core"),
            credit_cost=config.metadata.get("credit_cost", 1),
            tools_count=len(tools),
        ).model_dump(),
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
            }
            for t in tools
        ],
        "capabilities": {
            "tools": True,
            "resources": config.metadata.get("has_resources", False),
            "prompts": config.metadata.get("has_prompts", False),
        },
    }


@router.get("/servers/{server_id}/tools", response_model=Dict[str, Any])
async def list_server_tools(
    server_id: str,
    user_id: str = Depends(require_user_id),
    gateway: MCPGateway = Depends(get_gateway),
):
    """서버의 도구 목록 (Gateway 필터링 적용).

    사용자 정책에 따라 접근 가능한 도구만 반환합니다.

    Args:
        server_id: 서버 ID

    Returns:
        도구 목록
    """
    tools = await gateway.list_tools(user_id, server_id)

    return {
        "server_id": server_id,
        "tools": tools,
        "total": len(tools),
    }


@router.get("/servers/{server_id}/health", response_model=Dict[str, Any])
async def check_server_health(
    server_id: str,
    user_id: str = Depends(require_user_id),
    manager: MCPClientManager = Depends(get_client_manager),
):
    """서버 헬스 체크.

    Args:
        server_id: 서버 ID

    Returns:
        헬스 상태
    """
    config = manager.get_server_config(server_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Server not found: {server_id}")

    healthy = await manager.health_check(server_id)

    return {
        "server_id": server_id,
        "healthy": healthy,
        "enabled": config.enabled,
        "checked_at": datetime.utcnow().isoformat(),
    }


# =============================================================================
# Tool Endpoints
# =============================================================================

@router.get("/tools", response_model=Dict[str, Any])
async def list_all_tools(
    user_id: str = Depends(require_user_id),
    manager: MCPClientManager = Depends(get_client_manager),
    gateway: MCPGateway = Depends(get_gateway),
    include_native: bool = Query(default=True, description="Include native tools"),
):
    """모든 사용 가능한 도구 목록.

    MCP 서버의 도구와 선택적으로 Native 도구를 포함합니다.

    Args:
        include_native: Native 도구 포함 여부

    Returns:
        전체 도구 목록
    """
    all_tools: List[Dict[str, Any]] = []

    # MCP 서버별 도구 수집
    for server in manager.list_servers():
        if not server.enabled:
            continue

        tools = await gateway.list_tools(user_id, server.server_id)
        for tool in tools:
            all_tools.append({
                "name": tool["name"],
                "description": tool.get("description", ""),
                "server_id": server.server_id,
                "type": "mcp",
                "input_schema": tool.get("input_schema", {}),
                "credit_cost": server.metadata.get("credit_cost", 1),
            })

    # Vivid tool mappings 추가
    if include_native:
        for tool_id, mapping in DEFAULT_TOOL_MAPPINGS.items():
            # MCP 매핑이 있는 것은 위에서 이미 포함됨
            all_tools.append({
                "name": tool_id,
                "description": f"Vivid tool: {tool_id}",
                "server_id": mapping.get("server_id"),
                "type": "hybrid",
                "mcp_tool": mapping.get("tool_name"),
                "credit_cost": mapping.get("credit_cost", 1),
            })

    return {
        "tools": all_tools,
        "total": len(all_tools),
        "mcp_count": len([t for t in all_tools if t["type"] == "mcp"]),
        "hybrid_count": len([t for t in all_tools if t["type"] == "hybrid"]),
    }


@router.post("/call", response_model=MCPToolCallResponse)
async def call_mcp_tool(
    request: MCPToolCallRequest,
    http_request: Request,
    user_id: str = Depends(require_user_id),
    gateway: MCPGateway = Depends(get_gateway),
    user_agent: Optional[str] = Header(default=None),
):
    """MCP 도구 직접 호출 (Gateway 경유).

    Gateway를 통해 인증, 정책, Rate limiting, 감사 로깅이 적용됩니다.

    Args:
        request: 도구 호출 요청

    Returns:
        도구 호출 결과
    """
    logger.info(
        f"MCP V2: call {request.server_id}/{request.tool_name} by user={user_id[:8]}"
    )

    client_ip = get_client_ip(http_request)

    result = await gateway.call_tool(
        user_id=user_id,
        server_id=request.server_id,
        tool_name=request.tool_name,
        arguments=request.arguments,
        run_token=request.run_token,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    return MCPToolCallResponse(
        success=result["success"],
        result=result.get("result"),
        error=result.get("error"),
        error_code=result.get("error_code"),
        latency_ms=result.get("latency_ms", 0.0),
        request_id=result.get("request_id", ""),
        credit_cost=result.get("credit_cost", 0),
    )


@router.post("/execute", response_model=MCPExecuteResponse)
async def execute_hybrid(
    request: MCPExecuteRequest,
    http_request: Request,
    user_id: str = Depends(require_user_id),
    executor: HybridToolExecutor = Depends(get_executor),
):
    """Hybrid Executor를 통한 도구 실행.

    Vivid tool ID를 기반으로 자동으로 MCP 또는 Native로 라우팅됩니다.

    Args:
        request: 실행 요청

    Returns:
        실행 결과
    """
    logger.info(f"MCP V2: execute {request.tool_id} by user={user_id[:8]}")

    # 컨텍스트에 user_id 추가
    context = {**request.context, "user_id": user_id}

    result = await executor.execute(
        tool_id=request.tool_id,
        inputs=request.inputs,
        context=context,
    )

    return MCPExecuteResponse(
        success=result.success,
        outputs=result.outputs,
        error=result.error,
        error_code=result.error_code,
        latency_ms=result.latency_ms,
        credit_cost=result.credit_cost,
        request_id=result.request_id,
        execution_type=result.metadata.get("execution_type", "unknown"),
        server_id=result.metadata.get("server_id"),
    )


# =============================================================================
# Audit Endpoints
# =============================================================================

@router.get("/audit", response_model=Dict[str, Any])
async def get_audit_logs(
    user_id: str = Depends(require_user_id),
    gateway: MCPGateway = Depends(get_gateway),
    limit: int = Query(default=100, ge=1, le=1000),
    success_only: Optional[bool] = Query(default=None),
):
    """사용자의 MCP 감사 로그 조회.

    Args:
        limit: 최대 개수
        success_only: 성공만 필터링 (None=전체)

    Returns:
        감사 로그 목록
    """
    logs = await gateway.get_audit_logs(user_id=user_id, limit=limit)

    if success_only is not None:
        logs = [log for log in logs if log.success == success_only]

    return {
        "logs": [
            MCPAuditLogResponse(
                id=log.id,
                timestamp=log.timestamp,
                user_id=log.user_id,
                server_id=log.server_id,
                action=log.action.value,
                tool_name=log.tool_name,
                success=log.success,
                latency_ms=log.latency_ms,
                error_message=log.error_message,
                credit_cost=log.credit_cost,
                request_id=log.request_id,
            ).model_dump()
            for log in logs
        ],
        "total": len(logs),
    }


# =============================================================================
# Health Endpoint
# =============================================================================

@router.get("/health", response_model=MCPHealthResponse)
async def mcp_health(
    manager: MCPClientManager = Depends(get_client_manager),
):
    """MCP 시스템 전체 헬스 체크.

    모든 서버의 상태와 게이트웨이/실행기 상태를 반환합니다.

    Returns:
        시스템 헬스 상태
    """
    servers_status = await manager.health_check_all()

    servers_total = len(servers_status)
    servers_healthy = sum(1 for healthy in servers_status.values() if healthy)

    # 전체 상태 결정
    if servers_healthy == servers_total and servers_total > 0:
        status = "healthy"
    elif servers_healthy > 0:
        status = "degraded"
    else:
        status = "unhealthy"

    return MCPHealthResponse(
        status=status,
        servers_total=servers_total,
        servers_healthy=servers_healthy,
        servers_status=servers_status,
        gateway_status="healthy",  # Gateway는 항상 사용 가능
        executor_status="healthy",
        last_check=datetime.utcnow(),
    )


# =============================================================================
# Admin Endpoints (Requires Admin Role)
# =============================================================================

@router.post("/admin/policies", response_model=Dict[str, Any])
async def create_or_update_policy(
    request: MCPPolicyRequest,
    user_id: str = Depends(require_admin),
    gateway: MCPGateway = Depends(get_gateway),
):
    """MCP 정책 생성/수정 (관리자 전용).

    Args:
        request: 정책 설정

    Returns:
        생성/수정된 정책 정보
    """
    logger.info(f"MCP V2: create/update policy {request.policy_id} by admin={user_id[:8]}")

    policy = MCPPolicy(
        policy_id=request.policy_id,
        name=request.name,
        description=request.description,
        allowed_servers=frozenset(request.allowed_servers) if request.allowed_servers else frozenset(),
        denied_servers=frozenset(request.denied_servers) if request.denied_servers else frozenset(),
        allowed_tools=frozenset(request.allowed_tools) if request.allowed_tools else frozenset(),
        denied_tools=frozenset(request.denied_tools) if request.denied_tools else frozenset(),
        max_calls_per_minute=request.max_calls_per_minute,
        max_calls_per_hour=request.max_calls_per_hour,
        max_calls_per_day=request.max_calls_per_day,
        max_credit_per_call=request.max_credit_per_call,
        max_credit_per_day=request.max_credit_per_day,
        require_run_token=request.require_run_token,
        audit_level=request.audit_level,
    )

    gateway.register_policy(policy)

    return {
        "success": True,
        "policy_id": policy.policy_id,
        "name": policy.name,
        "message": f"Policy '{policy.policy_id}' registered successfully",
    }


@router.get("/admin/policies", response_model=Dict[str, Any])
async def list_policies(
    user_id: str = Depends(require_admin),
    gateway: MCPGateway = Depends(get_gateway),
):
    """등록된 MCP 정책 목록 (관리자 전용).

    Returns:
        정책 목록
    """
    # Note: MCPGateway._policies is private, so we expose a limited view
    policies = []
    for policy_id, policy in gateway._policies.items():
        policies.append({
            "policy_id": policy.policy_id,
            "name": policy.name,
            "description": policy.description,
            "max_calls_per_minute": policy.max_calls_per_minute,
            "max_calls_per_day": policy.max_calls_per_day,
            "require_run_token": policy.require_run_token,
            "audit_level": policy.audit_level,
        })

    return {
        "policies": policies,
        "total": len(policies),
        "default_policy": {
            "policy_id": gateway._default_policy.policy_id,
            "name": gateway._default_policy.name,
        },
    }


@router.post("/admin/policies/{policy_id}/assign", response_model=Dict[str, Any])
async def assign_policy_to_user(
    policy_id: str,
    target_user_id: str = Query(..., description="User ID to assign policy to"),
    admin_id: str = Depends(require_admin),
    gateway: MCPGateway = Depends(get_gateway),
):
    """사용자에게 정책 할당 (관리자 전용).

    Args:
        policy_id: 할당할 정책 ID
        target_user_id: 대상 사용자 ID

    Returns:
        할당 결과
    """
    logger.info(
        f"MCP V2: assign policy {policy_id} to user={target_user_id[:8]} "
        f"by admin={admin_id[:8]}"
    )

    try:
        gateway.assign_policy(target_user_id, policy_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_error_detail(e, "MCP operation"))

    return {
        "success": True,
        "policy_id": policy_id,
        "user_id": target_user_id,
        "message": f"Policy '{policy_id}' assigned to user",
    }


# =============================================================================
# Tool Mappings Endpoint (Debugging)
# =============================================================================

@router.get("/mappings", response_model=Dict[str, Any])
async def get_tool_mappings(
    user_id: str = Depends(require_user_id),
):
    """Vivid Tool → MCP 매핑 정보.

    디버깅 및 개발용으로 현재 설정된 도구 매핑을 반환합니다.

    Returns:
        도구 매핑 정보
    """
    mappings = []
    for tool_id, mapping in DEFAULT_TOOL_MAPPINGS.items():
        mappings.append({
            "tool_id": tool_id,
            "server_id": mapping.get("server_id"),
            "mcp_tool": mapping.get("tool_name"),
            "credit_cost": mapping.get("credit_cost", 1),
        })

    return {
        "mappings": mappings,
        "total": len(mappings),
    }


# =============================================================================
# Statistics Endpoint
# =============================================================================

@router.get("/stats", response_model=Dict[str, Any])
async def get_mcp_stats(
    user_id: str = Depends(require_user_id),
    manager: MCPClientManager = Depends(get_client_manager),
    gateway: MCPGateway = Depends(get_gateway),
):
    """MCP 시스템 통계.

    Returns:
        시스템 통계 (서버 수, 도구 수, 최근 호출 등)
    """
    servers = manager.list_servers()
    total_tools = 0

    for server in servers:
        if server.enabled:
            tools = await manager.list_tools(server.server_id)
            total_tools += len(tools)

    # 최근 감사 로그에서 통계 추출
    recent_logs = await gateway.get_audit_logs(user_id=user_id, limit=100)
    success_count = sum(1 for log in recent_logs if log.success)
    total_latency = sum(log.latency_ms for log in recent_logs)
    total_credit = sum(log.credit_cost for log in recent_logs)

    return {
        "servers": {
            "total": len(servers),
            "enabled": len([s for s in servers if s.enabled]),
        },
        "tools": {
            "total": total_tools,
            "mappings": len(DEFAULT_TOOL_MAPPINGS),
        },
        "usage": {
            "recent_calls": len(recent_logs),
            "success_rate": success_count / len(recent_logs) if recent_logs else 0.0,
            "avg_latency_ms": total_latency / len(recent_logs) if recent_logs else 0.0,
            "total_credits": total_credit,
        },
        "config": {
            "mcp_enabled": settings.MCP_ENABLED,
            "gateway_enabled": settings.MCP_GATEWAY_ENABLED,
            "rate_limit_rpm": settings.MCP_GATEWAY_RATE_LIMIT_RPM,
        },
    }
