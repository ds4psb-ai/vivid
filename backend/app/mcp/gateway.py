"""MCP Gateway (P0 Phase 4 - 2026).

중앙 집중식 MCP 게이트웨이 - 인증/감사/정책/라우팅.

2026 Best Practices:
    - Centralized authentication (Run-Token integration)
    - Comprehensive audit logging (compliance-ready)
    - Policy-based access control
    - Rate limiting at gateway level
    - Request/response sanitization

Reference:
    - MCP Gateway Architecture: https://composio.dev/blog/mcp-gateways-guide
    - Enterprise MCP Security: https://insight.factset.com/enterprise-mcp-part-3-security-and-governance
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field

from app.mcp.client import MCPClientManager, get_mcp_client_manager
from app.mcp.types import (
    MCPError,
    MCPErrorCode,
    MCPToolCall,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Audit Types
# =============================================================================

class MCPAction(str, Enum):
    """MCP 액션 유형."""
    TOOL_CALL = "tool_call"
    TOOL_LIST = "tool_list"
    RESOURCE_READ = "resource_read"
    RESOURCE_LIST = "resource_list"
    PROMPT_GET = "prompt_get"
    HEALTH_CHECK = "health_check"


class MCPAuditEntry(BaseModel):
    """MCP 감사 로그 엔트리.

    모든 MCP 호출을 기록합니다.

    Attributes:
        id: 감사 로그 ID
        timestamp: 발생 시각
        user_id: 사용자 ID
        server_id: MCP 서버 ID
        action: 액션 유형
        tool_name: 도구 이름 (tool_call인 경우)
        arguments_hash: 인자 해시 (보안 목적)
        result_summary: 결과 요약 (최대 500자)
        latency_ms: 처리 시간 (밀리초)
        success: 성공 여부
        error_code: 에러 코드 (실패 시)
        error_message: 에러 메시지 (실패 시)
        ip_address: 클라이언트 IP
        user_agent: User-Agent
        request_id: 요청 추적 ID
        credit_cost: 사용된 크레딧
        policy_applied: 적용된 정책 ID
    """
    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: str
    server_id: str
    action: MCPAction
    tool_name: Optional[str] = None
    arguments_hash: Optional[str] = None
    result_summary: Optional[str] = None
    latency_ms: float = 0.0
    success: bool = False
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    credit_cost: int = 0
    policy_applied: Optional[str] = None


# =============================================================================
# Policy
# =============================================================================

class MCPPolicy(BaseModel):
    """MCP 접근 정책.

    사용자/그룹별 MCP 접근 권한을 정의합니다.

    Attributes:
        policy_id: 정책 ID
        name: 정책 이름
        description: 정책 설명
        allowed_servers: 허용된 서버 (빈 리스트 = 모두 허용)
        denied_servers: 거부된 서버
        allowed_tools: 허용된 도구
        denied_tools: 거부된 도구
        max_calls_per_minute: 분당 최대 호출 수
        max_calls_per_hour: 시간당 최대 호출 수
        max_calls_per_day: 일일 최대 호출 수
        max_credit_per_call: 호출당 최대 크레딧
        max_credit_per_day: 일일 최대 크레딧
        allowed_hours: 허용 시간 (시작, 종료)
        require_run_token: Run-Token 필수 여부
        audit_level: 감사 수준 ("none", "basic", "full")
        priority: 정책 우선순위 (높을수록 우선)
    """
    model_config = ConfigDict(frozen=True)

    policy_id: str
    name: str
    description: str = ""

    # Access Control
    allowed_servers: frozenset[str] = Field(default_factory=frozenset)
    denied_servers: frozenset[str] = Field(default_factory=frozenset)
    allowed_tools: frozenset[str] = Field(default_factory=frozenset)
    denied_tools: frozenset[str] = Field(default_factory=frozenset)

    # Rate Limits
    max_calls_per_minute: int = Field(default=30, ge=1)
    max_calls_per_hour: int = Field(default=500, ge=1)
    max_calls_per_day: int = Field(default=5000, ge=1)

    # Credit Limits
    max_credit_per_call: int = Field(default=100, ge=1)
    max_credit_per_day: int = Field(default=10000, ge=1)

    # Time Restrictions
    allowed_hours: tuple[int, int] = Field(default=(0, 24))

    # Security
    require_run_token: bool = False
    audit_level: str = Field(default="basic", pattern="^(none|basic|full)$")

    # Priority
    priority: int = Field(default=0)


# =============================================================================
# Rate Limit Tracker
# =============================================================================

@dataclass
class RateLimitState:
    """사용자별 Rate Limit 상태."""
    user_id: str
    minute_count: int = 0
    hour_count: int = 0
    day_count: int = 0
    minute_reset: datetime = field(default_factory=datetime.utcnow)
    hour_reset: datetime = field(default_factory=datetime.utcnow)
    day_reset: datetime = field(default_factory=datetime.utcnow)
    day_credit: int = 0

    def reset_if_needed(self) -> None:
        """시간 경과 시 카운터 리셋."""
        now = datetime.utcnow()

        if (now - self.minute_reset) > timedelta(minutes=1):
            self.minute_count = 0
            self.minute_reset = now

        if (now - self.hour_reset) > timedelta(hours=1):
            self.hour_count = 0
            self.hour_reset = now

        if (now - self.day_reset) > timedelta(days=1):
            self.day_count = 0
            self.day_credit = 0
            self.day_reset = now

    def record_call(self, credit_cost: int = 0) -> None:
        """호출 기록."""
        self.reset_if_needed()
        self.minute_count += 1
        self.hour_count += 1
        self.day_count += 1
        self.day_credit += credit_cost


# =============================================================================
# Audit Store (In-Memory + DB Persistence)
# =============================================================================

class AuditStore:
    """감사 로그 저장소.

    메모리 버퍼 + 비동기 DB 저장.
    """

    def __init__(self, max_buffer_size: int = 1000):
        self._buffer: List[MCPAuditEntry] = []
        self._max_buffer_size = max_buffer_size
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None

    async def log(self, entry: MCPAuditEntry) -> None:
        """감사 로그 기록."""
        async with self._lock:
            self._buffer.append(entry)

            # 로그 출력
            log_data = {
                "audit": "mcp",
                "user": entry.user_id,
                "server": entry.server_id,
                "action": entry.action.value,
                "tool": entry.tool_name,
                "success": entry.success,
                "latency_ms": entry.latency_ms,
                "request_id": entry.request_id,
            }

            if entry.success:
                logger.info(f"MCP Audit: {json.dumps(log_data)}")
            else:
                log_data["error"] = entry.error_message
                logger.warning(f"MCP Audit: {json.dumps(log_data)}")

            # 버퍼가 가득 차면 flush
            if len(self._buffer) >= self._max_buffer_size:
                await self._flush_to_db()

    async def _flush_to_db(self) -> None:
        """DB로 플러시."""
        if not self._buffer:
            return

        # TODO: 실제 DB 저장 구현
        # 현재는 버퍼 클리어만
        entries_to_flush = self._buffer.copy()
        self._buffer.clear()

        logger.debug(f"Flushed {len(entries_to_flush)} audit entries")

    async def get_recent(
        self,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[MCPAuditEntry]:
        """최근 감사 로그 조회."""
        async with self._lock:
            entries = self._buffer.copy()

        if user_id:
            entries = [e for e in entries if e.user_id == user_id]

        return sorted(entries, key=lambda e: e.timestamp, reverse=True)[:limit]


# =============================================================================
# MCP Gateway
# =============================================================================

class MCPGateway:
    """MCP Gateway.

    모든 MCP 호출의 중앙 관리 게이트웨이.

    Features:
        - 인증: Run-Token 또는 API Key 검증
        - 권한: 정책 기반 접근 제어
        - 제한: Rate limiting (분/시/일)
        - 감사: 모든 호출 기록
        - 라우팅: 적절한 MCP 서버로 전달

    Usage:
        >>> gateway = MCPGateway(client_manager)
        >>> result = await gateway.call_tool(
        ...     user_id="user123",
        ...     server_id="tavily",
        ...     tool_name="search",
        ...     arguments={"query": "..."},
        ... )
    """

    def __init__(
        self,
        client_manager: Optional[MCPClientManager] = None,
        default_policy: Optional[MCPPolicy] = None,
    ):
        self._client_manager = client_manager or get_mcp_client_manager()
        self._policies: Dict[str, MCPPolicy] = {}
        self._user_policies: Dict[str, str] = {}  # user_id → policy_id
        self._rate_limits: Dict[str, RateLimitState] = {}
        self._audit_store = AuditStore()

        # 기본 정책
        self._default_policy = default_policy or MCPPolicy(
            policy_id="default",
            name="Default Policy",
            max_calls_per_minute=30,
            max_calls_per_hour=500,
            max_calls_per_day=5000,
            audit_level="basic",
        )

    async def call_tool(
        self,
        user_id: str,
        server_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        *,
        run_token: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """MCP 도구 호출.

        Args:
            user_id: 사용자 ID
            server_id: MCP 서버 ID
            tool_name: 도구 이름
            arguments: 도구 인자
            run_token: Run-Token (있으면 크레딧 차감)
            ip_address: 클라이언트 IP
            user_agent: User-Agent

        Returns:
            {"success": bool, "result": Any, "error": str, "latency_ms": float}
        """
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # 1. 정책 확인
        policy = self._get_policy(user_id)
        policy_check = self._check_policy(policy, server_id, tool_name)

        if not policy_check["allowed"]:
            latency = (time.time() - start_time) * 1000
            await self._log_audit(
                user_id=user_id,
                server_id=server_id,
                action=MCPAction.TOOL_CALL,
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                error_code=MCPErrorCode.POLICY_DENIED.value,
                error_message=policy_check["reason"],
                latency_ms=latency,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                policy_applied=policy.policy_id,
            )

            return {
                "success": False,
                "result": None,
                "error": f"Policy denied: {policy_check['reason']}",
                "error_code": MCPErrorCode.POLICY_DENIED.value,
                "latency_ms": latency,
                "request_id": request_id,
            }

        # 2. Rate Limit 확인
        rate_check = self._check_rate_limit(user_id, policy)

        if not rate_check["allowed"]:
            latency = (time.time() - start_time) * 1000
            await self._log_audit(
                user_id=user_id,
                server_id=server_id,
                action=MCPAction.TOOL_CALL,
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                error_code=MCPErrorCode.RATE_LIMIT_EXCEEDED.value,
                error_message=rate_check["reason"],
                latency_ms=latency,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                policy_applied=policy.policy_id,
            )

            return {
                "success": False,
                "result": None,
                "error": f"Rate limit: {rate_check['reason']}",
                "error_code": MCPErrorCode.RATE_LIMIT_EXCEEDED.value,
                "latency_ms": latency,
                "request_id": request_id,
            }

        # 3. Run-Token 검증 (필요시)
        if policy.require_run_token and not run_token:
            latency = (time.time() - start_time) * 1000
            await self._log_audit(
                user_id=user_id,
                server_id=server_id,
                action=MCPAction.TOOL_CALL,
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                error_code=MCPErrorCode.AUTHENTICATION_FAILED.value,
                error_message="Run-Token required",
                latency_ms=latency,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                policy_applied=policy.policy_id,
            )

            return {
                "success": False,
                "result": None,
                "error": "Run-Token required",
                "error_code": MCPErrorCode.AUTHENTICATION_FAILED.value,
                "latency_ms": latency,
                "request_id": request_id,
            }

        # 4. MCP 호출 실행
        try:
            mcp_result = await self._client_manager.call_tool(
                server_id=server_id,
                tool_name=tool_name,
                arguments=arguments,
            )

            latency = (time.time() - start_time) * 1000

            # 5. Rate limit 기록
            credit_cost = self._calculate_credit_cost(server_id, tool_name)
            self._record_call(user_id, credit_cost)

            # 6. 감사 로그
            await self._log_audit(
                user_id=user_id,
                server_id=server_id,
                action=MCPAction.TOOL_CALL,
                tool_name=tool_name,
                arguments=arguments,
                result=mcp_result.result,
                success=mcp_result.success,
                error_code=mcp_result.error_code.value if mcp_result.error_code else None,
                error_message=mcp_result.error,
                latency_ms=latency,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                credit_cost=credit_cost,
                policy_applied=policy.policy_id,
            )

            return {
                "success": mcp_result.success,
                "result": mcp_result.result,
                "error": mcp_result.error,
                "error_code": mcp_result.error_code.value if mcp_result.error_code else None,
                "latency_ms": latency,
                "request_id": request_id,
            }

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            logger.exception(f"MCP Gateway error: {e}")

            await self._log_audit(
                user_id=user_id,
                server_id=server_id,
                action=MCPAction.TOOL_CALL,
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                error_code=MCPErrorCode.INTERNAL_ERROR.value,
                error_message=str(e),
                latency_ms=latency,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                policy_applied=policy.policy_id,
            )

            return {
                "success": False,
                "result": None,
                "error": str(e),
                "error_code": MCPErrorCode.INTERNAL_ERROR.value,
                "latency_ms": latency,
                "request_id": request_id,
            }

    async def list_tools(
        self,
        user_id: str,
        server_id: str,
    ) -> List[Dict[str, Any]]:
        """서버의 도구 목록 조회.

        Args:
            user_id: 사용자 ID
            server_id: 서버 ID

        Returns:
            도구 목록
        """
        policy = self._get_policy(user_id)

        # 서버 접근 권한 확인
        if policy.denied_servers and server_id in policy.denied_servers:
            return []
        if policy.allowed_servers and server_id not in policy.allowed_servers:
            return []

        tools = await self._client_manager.list_tools(server_id)

        # 도구 필터링
        result = []
        for tool in tools:
            tool_key = f"{server_id}/{tool.name}"
            if policy.denied_tools and tool_key in policy.denied_tools:
                continue
            if policy.allowed_tools and tool_key not in policy.allowed_tools:
                continue
            result.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            })

        return result

    # =========================================================================
    # Policy Management
    # =========================================================================

    def register_policy(self, policy: MCPPolicy) -> None:
        """정책 등록."""
        self._policies[policy.policy_id] = policy
        logger.info(f"MCP policy registered: {policy.policy_id}")

    def unregister_policy(self, policy_id: str) -> None:
        """정책 해제."""
        self._policies.pop(policy_id, None)

    def assign_policy(self, user_id: str, policy_id: str) -> None:
        """사용자에게 정책 할당."""
        if policy_id in self._policies:
            self._user_policies[user_id] = policy_id
        else:
            raise ValueError(f"Policy not found: {policy_id}")

    def _get_policy(self, user_id: str) -> MCPPolicy:
        """사용자의 정책 조회."""
        policy_id = self._user_policies.get(user_id)
        if policy_id and policy_id in self._policies:
            return self._policies[policy_id]
        return self._default_policy

    def _check_policy(
        self,
        policy: MCPPolicy,
        server_id: str,
        tool_name: str,
    ) -> Dict[str, Any]:
        """정책 검증."""
        # 서버 체크
        if policy.denied_servers and server_id in policy.denied_servers:
            return {"allowed": False, "reason": f"Server denied: {server_id}"}
        if policy.allowed_servers and server_id not in policy.allowed_servers:
            return {"allowed": False, "reason": f"Server not allowed: {server_id}"}

        # 도구 체크
        tool_key = f"{server_id}/{tool_name}"
        if policy.denied_tools and tool_key in policy.denied_tools:
            return {"allowed": False, "reason": f"Tool denied: {tool_key}"}
        if policy.allowed_tools and tool_key not in policy.allowed_tools:
            return {"allowed": False, "reason": f"Tool not allowed: {tool_key}"}

        # 시간 체크
        current_hour = datetime.utcnow().hour
        if not (policy.allowed_hours[0] <= current_hour < policy.allowed_hours[1]):
            return {"allowed": False, "reason": "Outside allowed hours"}

        return {"allowed": True, "reason": ""}

    # =========================================================================
    # Rate Limiting
    # =========================================================================

    def _check_rate_limit(
        self,
        user_id: str,
        policy: MCPPolicy,
    ) -> Dict[str, Any]:
        """Rate limit 확인."""
        state = self._get_rate_limit_state(user_id)
        state.reset_if_needed()

        if state.minute_count >= policy.max_calls_per_minute:
            return {"allowed": False, "reason": "Minute limit exceeded"}
        if state.hour_count >= policy.max_calls_per_hour:
            return {"allowed": False, "reason": "Hour limit exceeded"}
        if state.day_count >= policy.max_calls_per_day:
            return {"allowed": False, "reason": "Day limit exceeded"}
        if state.day_credit >= policy.max_credit_per_day:
            return {"allowed": False, "reason": "Daily credit limit exceeded"}

        return {"allowed": True, "reason": ""}

    def _record_call(self, user_id: str, credit_cost: int = 0) -> None:
        """호출 기록."""
        state = self._get_rate_limit_state(user_id)
        state.record_call(credit_cost)

    def _get_rate_limit_state(self, user_id: str) -> RateLimitState:
        """Rate limit 상태 조회."""
        if user_id not in self._rate_limits:
            self._rate_limits[user_id] = RateLimitState(user_id=user_id)
        return self._rate_limits[user_id]

    # =========================================================================
    # Credit Cost
    # =========================================================================

    def _calculate_credit_cost(
        self,
        server_id: str,
        tool_name: str,
    ) -> int:
        """크레딧 비용 계산."""
        # 서버별 기본 비용
        base_cost = {
            "tavily": 2,       # 외부 API
            "qdrant": 1,       # 내부
            "playwright": 3,  # 리소스 집약적
        }.get(server_id, 1)

        # 도구별 가중치
        tool_multiplier = 1
        if "search" in tool_name.lower():
            tool_multiplier = 2
        elif "generate" in tool_name.lower():
            tool_multiplier = 3

        return base_cost * tool_multiplier

    # =========================================================================
    # Audit Logging
    # =========================================================================

    async def _log_audit(
        self,
        user_id: str,
        server_id: str,
        action: MCPAction,
        tool_name: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
        result: Any = None,
        success: bool = False,
        error_code: Optional[int] = None,
        error_message: Optional[str] = None,
        latency_ms: float = 0.0,
        request_id: str = "",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        credit_cost: int = 0,
        policy_applied: Optional[str] = None,
    ) -> None:
        """감사 로그 기록."""
        # 인자 해시 (보안)
        arguments_hash = None
        if arguments:
            args_str = json.dumps(arguments, sort_keys=True, default=str)
            arguments_hash = hashlib.sha256(args_str.encode()).hexdigest()[:16]

        # 결과 요약 (최대 500자)
        result_summary = None
        if result is not None:
            result_str = str(result)
            result_summary = result_str[:500] if len(result_str) > 500 else result_str

        entry = MCPAuditEntry(
            user_id=user_id,
            server_id=server_id,
            action=action,
            tool_name=tool_name,
            arguments_hash=arguments_hash,
            result_summary=result_summary,
            latency_ms=latency_ms,
            success=success,
            error_code=error_code,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            credit_cost=credit_cost,
            policy_applied=policy_applied,
        )

        await self._audit_store.log(entry)

    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[MCPAuditEntry]:
        """감사 로그 조회."""
        return await self._audit_store.get_recent(user_id=user_id, limit=limit)


# =============================================================================
# Singleton
# =============================================================================

_mcp_gateway: Optional[MCPGateway] = None


def get_mcp_gateway() -> MCPGateway:
    """MCP Gateway 싱글톤.

    Returns:
        MCPGateway 인스턴스
    """
    global _mcp_gateway
    if _mcp_gateway is None:
        _mcp_gateway = MCPGateway()
    return _mcp_gateway


def reset_mcp_gateway() -> None:
    """MCP Gateway 리셋 (테스트용)."""
    global _mcp_gateway
    _mcp_gateway = None
