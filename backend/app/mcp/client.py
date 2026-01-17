"""MCP Client Manager (P0 Phase 4 - 2026).

외부 MCP 서버 연결 및 도구 호출 관리.

2026 Best Practices:
    - Streamable HTTP transport (MCP Spec 2025-06-18)
    - Connection pooling with httpx
    - Circuit breaker pattern
    - Exponential backoff retry
    - Health check with async polling

Reference:
    - MCP Transports: https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
    - FastMCP Client: https://github.com/jlowin/fastmcp
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Set

import httpx
from pydantic import BaseModel

from app.mcp.types import (
    MCPCapabilities,
    MCPError,
    MCPErrorCode,
    MCPServerConfig,
    MCPToolCall,
    MCPToolInfo,
    MCPTransport,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Circuit Breaker
# =============================================================================

class CircuitState(str, Enum):
    """서킷 브레이커 상태."""
    CLOSED = "closed"       # 정상
    OPEN = "open"           # 차단
    HALF_OPEN = "half_open" # 복구 시도 중


@dataclass
class CircuitBreaker:
    """서킷 브레이커.

    연속 실패 시 일시적으로 요청을 차단하여 시스템 보호.

    Attributes:
        threshold: 실패 임계값
        timeout_seconds: 차단 시간
        failure_count: 현재 실패 횟수
        last_failure: 마지막 실패 시각
        state: 현재 상태
    """
    threshold: int = 5
    timeout_seconds: int = 60
    failure_count: int = 0
    last_failure: Optional[datetime] = None
    state: CircuitState = CircuitState.CLOSED

    def record_success(self) -> None:
        """성공 기록."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """실패 기록."""
        self.failure_count += 1
        self.last_failure = datetime.utcnow()

        if self.failure_count >= self.threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker OPEN: {self.failure_count} failures"
            )

    def can_execute(self) -> bool:
        """실행 가능 여부."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # 타임아웃 경과 시 half-open으로 전환
            if self.last_failure and (
                datetime.utcnow() - self.last_failure
            ) > timedelta(seconds=self.timeout_seconds):
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        # HALF_OPEN: 1회 시도 허용
        return True


# =============================================================================
# Rate Limiter
# =============================================================================

@dataclass
class RateLimiter:
    """Rate Limiter (Token Bucket Algorithm).

    분당 요청 수를 제한합니다.

    Attributes:
        rpm: Requests per minute
        tokens: 현재 토큰 수
        last_refill: 마지막 리필 시각
    """
    rpm: int = 60
    tokens: float = field(init=False)
    last_refill: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        self.tokens = float(self.rpm)

    def _refill(self) -> None:
        """토큰 리필."""
        now = datetime.utcnow()
        elapsed = (now - self.last_refill).total_seconds()
        refill_amount = elapsed * (self.rpm / 60.0)
        self.tokens = min(self.rpm, self.tokens + refill_amount)
        self.last_refill = now

    def acquire(self) -> bool:
        """토큰 획득 시도."""
        self._refill()
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    def wait_time(self) -> float:
        """다음 토큰까지 대기 시간 (초)."""
        self._refill()
        if self.tokens >= 1:
            return 0.0
        return (1 - self.tokens) * (60.0 / self.rpm)


# =============================================================================
# HTTP MCP Client
# =============================================================================

class StreamableHTTPClient:
    """Streamable HTTP MCP Client.

    MCP Spec 2025-06-18 Streamable HTTP 전송 구현.

    Features:
        - HTTP POST for requests
        - SSE streaming for responses (optional)
        - Session management with Mcp-Session-Id header
        - Automatic initialization
    """

    def __init__(
        self,
        config: MCPServerConfig,
        http_client: httpx.AsyncClient,
    ):
        self.config = config
        self._http = http_client
        self._session_id: Optional[str] = None
        self._initialized = False
        self._capabilities: Optional[MCPCapabilities] = None
        self._tools_cache: Optional[List[MCPToolInfo]] = None
        self._cache_expires: Optional[datetime] = None

    async def initialize(self) -> None:
        """MCP 세션 초기화."""
        if self._initialized:
            return

        request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "vivid-mcp-client",
                    "version": "1.0.0",
                },
            },
        }

        response = await self._send_request(request)

        if "result" in response:
            result = response["result"]
            self._session_id = result.get("sessionId")
            caps = result.get("capabilities", {})
            self._capabilities = MCPCapabilities(
                tools="tools" in caps,
                resources="resources" in caps,
                prompts="prompts" in caps,
                sampling="sampling" in caps,
            )
            self._initialized = True

            # Send initialized notification
            notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            }
            await self._send_notification(notification)

            logger.info(
                f"MCP initialized: {self.config.server_id} "
                f"(session={self._session_id})"
            )
        else:
            error = response.get("error", {})
            raise MCPError(
                MCPErrorCode.INTERNAL_ERROR,
                f"Initialize failed: {error.get('message', 'Unknown error')}",
            )

    async def list_tools(self) -> List[MCPToolInfo]:
        """도구 목록 조회."""
        await self.initialize()

        # 캐시 확인 (5분)
        if (
            self._tools_cache is not None
            and self._cache_expires
            and datetime.utcnow() < self._cache_expires
        ):
            return self._tools_cache

        request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list",
            "params": {},
        }

        response = await self._send_request(request)

        if "result" in response:
            tools_data = response["result"].get("tools", [])
            tools = [
                MCPToolInfo(
                    name=t.get("name", ""),
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema", {}),
                )
                for t in tools_data
            ]
            self._tools_cache = tools
            self._cache_expires = datetime.utcnow() + timedelta(minutes=5)
            return tools
        else:
            return []

    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """도구 호출."""
        await self.initialize()

        request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments,
            },
        }

        response = await self._send_request(request)

        if "result" in response:
            content = response["result"].get("content", [])
            # Extract text content
            if content and isinstance(content, list):
                for item in content:
                    if item.get("type") == "text":
                        return item.get("text")
                return content
            return response["result"]
        else:
            error = response.get("error", {})
            raise MCPError(
                MCPErrorCode(error.get("code", -32603)),
                error.get("message", "Unknown error"),
                error.get("data"),
            )

    async def health_check(self) -> bool:
        """헬스 체크."""
        try:
            await self.initialize()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """연결 종료."""
        self._initialized = False
        self._session_id = None

    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """JSON-RPC 요청 전송."""
        headers = self._build_headers()
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json, text/event-stream"

        try:
            response = await self._http.post(
                self.config.url or "",
                json=request,
                headers=headers,
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")

            if "text/event-stream" in content_type:
                # SSE response - collect all events
                return await self._parse_sse_response(response)
            else:
                # JSON response
                return response.json()

        except httpx.TimeoutException:
            raise MCPError(MCPErrorCode.TIMEOUT, "Request timed out")
        except httpx.HTTPStatusError as e:
            raise MCPError(
                MCPErrorCode.INTERNAL_ERROR,
                f"HTTP error: {e.response.status_code}",
            )

    async def _send_notification(self, notification: Dict[str, Any]) -> None:
        """JSON-RPC 알림 전송 (응답 없음)."""
        headers = self._build_headers()
        headers["Content-Type"] = "application/json"

        try:
            await self._http.post(
                self.config.url or "",
                json=notification,
                headers=headers,
                timeout=5,
            )
        except Exception as e:
            logger.warning(f"Notification failed: {e}")

    async def _parse_sse_response(
        self,
        response: httpx.Response,
    ) -> Dict[str, Any]:
        """SSE 응답 파싱."""
        # For simplicity, collect the last data event
        last_data: Optional[Dict[str, Any]] = None

        async for line in response.aiter_lines():
            line = line.strip()
            if line.startswith("data:"):
                data_str = line[5:].strip()
                if data_str:
                    try:
                        last_data = json.loads(data_str)
                    except json.JSONDecodeError:
                        pass

        return last_data or {"error": {"message": "No data received"}}

    def _build_headers(self) -> Dict[str, str]:
        """요청 헤더 생성."""
        headers = {}

        # Session ID
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        # Protocol Version
        headers["Mcp-Protocol-Version"] = "2025-06-18"

        # Authentication
        if self.config.auth_type == "api_key":
            api_key = self.config.auth_config.get("api_key", "")
            header_name = self.config.auth_config.get("header", "Authorization")
            prefix = self.config.auth_config.get("prefix", "Bearer")
            headers[header_name] = f"{prefix} {api_key}"
        elif self.config.auth_type == "bearer":
            token = self.config.auth_config.get("token", "")
            headers["Authorization"] = f"Bearer {token}"

        return headers


# =============================================================================
# MCP Client Manager
# =============================================================================

class MCPClientManager:
    """MCP Client Manager.

    외부 MCP 서버 연결을 중앙 관리합니다.

    Features:
        - 서버 등록/해제
        - 연결 풀링 (httpx)
        - 서킷 브레이커
        - Rate limiting
        - 헬스 체크

    Usage:
        >>> manager = MCPClientManager()
        >>> await manager.register_server(config)
        >>> result = await manager.call_tool("tavily", "search", {"query": "..."})
    """

    def __init__(self):
        self._servers: Dict[str, MCPServerConfig] = {}
        self._clients: Dict[str, StreamableHTTPClient] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._rate_limiters: Dict[str, RateLimiter] = {}
        self._http_pool: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()
        self._started = False

    async def start(self) -> None:
        """매니저 시작."""
        if self._started:
            return

        self._http_pool = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            timeout=httpx.Timeout(30.0, connect=10.0),
        )
        self._started = True
        logger.info("MCPClientManager started")

    async def stop(self) -> None:
        """매니저 종료."""
        if not self._started:
            return

        # Close all clients
        for client in self._clients.values():
            await client.close()
        self._clients.clear()

        # Close HTTP pool
        if self._http_pool:
            await self._http_pool.aclose()
            self._http_pool = None

        self._started = False
        logger.info("MCPClientManager stopped")

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[MCPClientManager]:
        """Lifespan context manager."""
        await self.start()
        try:
            yield self
        finally:
            await self.stop()

    async def register_server(self, config: MCPServerConfig) -> None:
        """MCP 서버 등록.

        Args:
            config: 서버 설정
        """
        async with self._lock:
            self._servers[config.server_id] = config
            self._circuit_breakers[config.server_id] = CircuitBreaker(
                threshold=config.circuit_breaker_threshold
            )
            self._rate_limiters[config.server_id] = RateLimiter(
                rpm=config.rate_limit_rpm
            )

            logger.info(
                f"MCP server registered: {config.server_id} "
                f"({config.transport.value})"
            )

    async def unregister_server(self, server_id: str) -> None:
        """MCP 서버 해제.

        Args:
            server_id: 서버 ID
        """
        async with self._lock:
            if server_id in self._clients:
                await self._clients[server_id].close()
                del self._clients[server_id]

            self._servers.pop(server_id, None)
            self._circuit_breakers.pop(server_id, None)
            self._rate_limiters.pop(server_id, None)

            logger.info(f"MCP server unregistered: {server_id}")

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> MCPToolCall:
        """MCP 도구 호출.

        Args:
            server_id: 서버 ID
            tool_name: 도구 이름
            arguments: 도구 인자

        Returns:
            MCPToolCall with result or error
        """
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # 서버 확인
        config = self._servers.get(server_id)
        if not config:
            return MCPToolCall(
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                error=f"Server not found: {server_id}",
                error_code=MCPErrorCode.SERVER_UNAVAILABLE,
                server_id=server_id,
                request_id=request_id,
            )

        if not config.enabled:
            return MCPToolCall(
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                error=f"Server disabled: {server_id}",
                error_code=MCPErrorCode.SERVER_UNAVAILABLE,
                server_id=server_id,
                request_id=request_id,
            )

        # 서킷 브레이커 확인
        circuit = self._circuit_breakers.get(server_id)
        if circuit and not circuit.can_execute():
            return MCPToolCall(
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                error="Circuit breaker open",
                error_code=MCPErrorCode.SERVER_UNAVAILABLE,
                server_id=server_id,
                request_id=request_id,
            )

        # Rate limit 확인
        rate_limiter = self._rate_limiters.get(server_id)
        if rate_limiter and not rate_limiter.acquire():
            wait_time = rate_limiter.wait_time()
            return MCPToolCall(
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                error=f"Rate limit exceeded. Retry after {wait_time:.1f}s",
                error_code=MCPErrorCode.RATE_LIMIT_EXCEEDED,
                server_id=server_id,
                request_id=request_id,
            )

        # 클라이언트 가져오기 (또는 생성)
        try:
            client = await self._get_or_create_client(server_id)
        except Exception as e:
            logger.error(f"Failed to create client for {server_id}: {e}")
            return MCPToolCall(
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                error=str(e),
                error_code=MCPErrorCode.SERVER_UNAVAILABLE,
                server_id=server_id,
                request_id=request_id,
            )

        # 도구 호출 (재시도 포함)
        last_error: Optional[Exception] = None
        for attempt in range(config.max_retries + 1):
            try:
                result = await client.call_tool(tool_name, arguments)
                latency = (time.time() - start_time) * 1000

                # 성공
                if circuit:
                    circuit.record_success()

                logger.info(
                    f"MCP call success: {server_id}/{tool_name} "
                    f"[{request_id}] ({latency:.1f}ms)"
                )

                return MCPToolCall(
                    tool_name=tool_name,
                    arguments=arguments,
                    result=result,
                    success=True,
                    latency_ms=latency,
                    server_id=server_id,
                    request_id=request_id,
                )

            except MCPError as e:
                last_error = e
                if e.code == MCPErrorCode.TIMEOUT:
                    # 타임아웃은 재시도
                    if attempt < config.max_retries:
                        await asyncio.sleep(config.retry_delay_ms / 1000)
                        continue
                else:
                    # 다른 에러는 즉시 반환
                    break

            except Exception as e:
                last_error = e
                if attempt < config.max_retries:
                    await asyncio.sleep(config.retry_delay_ms / 1000)
                    continue

        # 실패
        latency = (time.time() - start_time) * 1000
        if circuit:
            circuit.record_failure()

        error_code = MCPErrorCode.INTERNAL_ERROR
        error_msg = str(last_error) if last_error else "Unknown error"

        if isinstance(last_error, MCPError):
            error_code = last_error.code
            error_msg = last_error.message

        logger.warning(
            f"MCP call failed: {server_id}/{tool_name} "
            f"[{request_id}] - {error_msg}"
        )

        return MCPToolCall(
            tool_name=tool_name,
            arguments=arguments,
            success=False,
            error=error_msg,
            error_code=error_code,
            latency_ms=latency,
            server_id=server_id,
            request_id=request_id,
        )

    async def list_tools(self, server_id: str) -> List[MCPToolInfo]:
        """서버의 도구 목록 조회.

        Args:
            server_id: 서버 ID

        Returns:
            도구 목록
        """
        config = self._servers.get(server_id)
        if not config or not config.enabled:
            return []

        try:
            client = await self._get_or_create_client(server_id)
            return await client.list_tools()
        except Exception as e:
            logger.error(f"Failed to list tools for {server_id}: {e}")
            return []

    async def health_check(self, server_id: str) -> bool:
        """서버 헬스 체크.

        Args:
            server_id: 서버 ID

        Returns:
            True if healthy
        """
        config = self._servers.get(server_id)
        if not config or not config.enabled:
            return False

        try:
            client = await self._get_or_create_client(server_id)
            return await client.health_check()
        except Exception:
            return False

    async def health_check_all(self) -> Dict[str, bool]:
        """모든 서버 헬스 체크.

        Returns:
            {server_id: healthy} 맵
        """
        tasks = [
            self.health_check(server_id)
            for server_id in self._servers.keys()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            server_id: result if isinstance(result, bool) else False
            for server_id, result in zip(self._servers.keys(), results)
        }

    def get_server_config(self, server_id: str) -> Optional[MCPServerConfig]:
        """서버 설정 조회."""
        return self._servers.get(server_id)

    def list_servers(self) -> List[MCPServerConfig]:
        """등록된 서버 목록."""
        return list(self._servers.values())

    async def _get_or_create_client(
        self,
        server_id: str,
    ) -> StreamableHTTPClient:
        """클라이언트 인스턴스 가져오기 (또는 생성)."""
        if server_id not in self._clients:
            config = self._servers[server_id]

            if config.transport == MCPTransport.STREAMABLE_HTTP:
                if not self._http_pool:
                    await self.start()

                self._clients[server_id] = StreamableHTTPClient(
                    config=config,
                    http_client=self._http_pool,  # type: ignore
                )
            else:
                raise NotImplementedError(
                    f"Transport not implemented: {config.transport}"
                )

        return self._clients[server_id]


# =============================================================================
# Singleton
# =============================================================================

_mcp_client_manager: Optional[MCPClientManager] = None
_manager_lock = asyncio.Lock()


def get_mcp_client_manager() -> MCPClientManager:
    """MCP Client Manager 싱글톤.

    Returns:
        MCPClientManager 인스턴스
    """
    global _mcp_client_manager
    if _mcp_client_manager is None:
        _mcp_client_manager = MCPClientManager()
    return _mcp_client_manager


def reset_mcp_client_manager() -> None:
    """MCP Client Manager 리셋 (테스트용)."""
    global _mcp_client_manager
    _mcp_client_manager = None
