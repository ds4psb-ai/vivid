"""MCP Type Definitions (P0 Phase 4 - 2026).

Model Context Protocol 타입 정의.

Reference:
    - MCP Spec 2025-06-18: https://modelcontextprotocol.io/specification/2025-06-18
    - FastMCP: https://github.com/jlowin/fastmcp

2026 Best Practices:
    - Pydantic v2 with ConfigDict
    - Frozen models for immutability
    - Protocol-based duck typing
    - Comprehensive error codes
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Enums
# =============================================================================

class MCPTransport(str, Enum):
    """MCP 전송 프로토콜.

    Reference: MCP Spec 2025-06-18 Transports
    - STDIO: 로컬 프로세스 통신 (Claude Desktop 기본)
    - STREAMABLE_HTTP: HTTP POST + SSE (프로덕션 권장)

    Note: HTTP+SSE는 2025-03-26에서 deprecated, Streamable HTTP로 대체
    """
    STDIO = "stdio"
    STREAMABLE_HTTP = "streamable_http"
    # Legacy (deprecated but supported for backwards compat)
    HTTP_SSE = "http_sse"


class MCPErrorCode(IntEnum):
    """MCP 에러 코드 (JSON-RPC 표준 + MCP 확장).

    Reference: JSON-RPC 2.0 + MCP Spec
    """
    # JSON-RPC Standard Errors
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # MCP Custom Errors
    SERVER_NOT_INITIALIZED = -32002
    TOOL_NOT_FOUND = -32001
    RESOURCE_NOT_FOUND = -32000

    # Gateway Errors (Vivid custom)
    RATE_LIMIT_EXCEEDED = -33001
    POLICY_DENIED = -33002
    AUTHENTICATION_FAILED = -33003
    SERVER_UNAVAILABLE = -33004
    TIMEOUT = -33005


class MCPCapabilityType(str, Enum):
    """MCP 기능 유형."""
    TOOLS = "tools"
    RESOURCES = "resources"
    PROMPTS = "prompts"
    SAMPLING = "sampling"
    ROOTS = "roots"
    ELICITATION = "elicitation"


# =============================================================================
# Core Models
# =============================================================================

class MCPServerConfig(BaseModel):
    """MCP 서버 설정.

    외부/내부 MCP 서버의 연결 설정을 정의합니다.

    Attributes:
        server_id: 고유 서버 식별자 (e.g., "tavily", "qdrant")
        name: 표시 이름
        description: 서버 설명
        transport: 전송 프로토콜
        url: HTTP 엔드포인트 (Streamable HTTP용)
        command: 실행 명령어 (STDIO용)
        args: 명령어 인자
        env: 환경 변수
        auth_type: 인증 유형 ("api_key", "oauth2", "bearer", "none")
        auth_config: 인증 설정 (api_key, header_name 등)
        timeout_seconds: 요청 타임아웃
        max_retries: 최대 재시도 횟수
        retry_delay_ms: 재시도 지연 (밀리초)
        rate_limit_rpm: 분당 요청 제한
        circuit_breaker_threshold: 서킷 브레이커 실패 임계값
        enabled: 활성화 여부
        tags: 메타데이터 태그

    Example:
        >>> config = MCPServerConfig(
        ...     server_id="tavily",
        ...     name="Tavily AI Search",
        ...     transport=MCPTransport.STREAMABLE_HTTP,
        ...     url="https://mcp.tavily.com/mcp",
        ...     auth_type="api_key",
        ...     auth_config={"api_key": "tvly-xxx", "header": "Authorization"},
        ... )
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    server_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="")

    # Transport
    transport: MCPTransport = MCPTransport.STREAMABLE_HTTP
    url: Optional[str] = Field(default=None, description="HTTP endpoint URL")
    command: Optional[str] = Field(default=None, description="STDIO command")
    args: tuple[str, ...] = Field(default_factory=tuple)
    env: Dict[str, str] = Field(default_factory=dict)

    # Authentication
    auth_type: str = Field(default="none", pattern="^(api_key|oauth2|bearer|none)$")
    auth_config: Dict[str, Any] = Field(default_factory=dict)

    # Timeouts & Retries
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_ms: int = Field(default=1000, ge=100, le=30000)

    # Rate Limiting
    rate_limit_rpm: int = Field(default=60, ge=1, le=10000)

    # Circuit Breaker
    circuit_breaker_threshold: int = Field(default=5, ge=1, le=100)

    # State
    enabled: bool = Field(default=True)

    # Metadata
    tags: tuple[str, ...] = Field(default_factory=tuple)

    def with_enabled(self, enabled: bool) -> MCPServerConfig:
        """활성화 상태 변경한 새 인스턴스 반환."""
        return self.model_copy(update={"enabled": enabled})


class MCPToolInfo(BaseModel):
    """MCP 도구 정보.

    MCP 서버가 노출하는 도구의 메타데이터.

    Attributes:
        name: 도구 이름 (식별자)
        description: 도구 설명 (LLM 프롬프트용)
        input_schema: JSON Schema for inputs
        annotations: 추가 어노테이션
    """
    model_config = ConfigDict(frozen=True)

    name: str
    description: str = ""
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    annotations: Dict[str, Any] = Field(default_factory=dict)


class MCPResourceInfo(BaseModel):
    """MCP 리소스 정보.

    MCP 서버가 노출하는 리소스의 메타데이터.

    Attributes:
        uri: 리소스 URI (e.g., "file:///path", "db://table/id")
        name: 리소스 이름
        description: 리소스 설명
        mime_type: MIME 타입
    """
    model_config = ConfigDict(frozen=True)

    uri: str
    name: str = ""
    description: str = ""
    mime_type: Optional[str] = None


class MCPCapabilities(BaseModel):
    """MCP 서버 기능.

    서버가 지원하는 기능 목록.
    """
    model_config = ConfigDict(frozen=True)

    tools: bool = False
    resources: bool = False
    prompts: bool = False
    sampling: bool = False
    roots: bool = False


class MCPToolCall(BaseModel):
    """MCP 도구 호출 결과.

    Attributes:
        tool_name: 호출된 도구 이름
        arguments: 전달된 인자
        result: 실행 결과 (성공 시)
        success: 성공 여부
        error: 에러 메시지 (실패 시)
        error_code: 에러 코드
        latency_ms: 실행 시간 (밀리초)
        server_id: 서버 ID
        request_id: 요청 ID (추적용)
        timestamp: 실행 시각
    """
    model_config = ConfigDict(frozen=True)

    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    success: bool = False
    error: Optional[str] = None
    error_code: Optional[MCPErrorCode] = None
    latency_ms: float = 0.0
    server_id: str = ""
    request_id: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_timeout(self) -> bool:
        """타임아웃 에러인지 확인."""
        return self.error_code == MCPErrorCode.TIMEOUT

    @property
    def is_rate_limited(self) -> bool:
        """Rate limit 에러인지 확인."""
        return self.error_code == MCPErrorCode.RATE_LIMIT_EXCEEDED


class MCPError(Exception):
    """MCP 에러.

    MCP 프로토콜 에러를 나타내는 예외.

    Attributes:
        code: 에러 코드
        message: 에러 메시지
        data: 추가 데이터
    """

    def __init__(
        self,
        code: MCPErrorCode,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.data = data or {}
        super().__init__(f"[{code.name}] {message}")

    def to_dict(self) -> Dict[str, Any]:
        """JSON-RPC 에러 형식으로 변환."""
        return {
            "code": self.code.value,
            "message": self.message,
            "data": self.data,
        }


# =============================================================================
# Protocols (Duck Typing)
# =============================================================================

@runtime_checkable
class MCPClientProtocol(Protocol):
    """MCP 클라이언트 프로토콜.

    MCP 서버와 통신하는 클라이언트 인터페이스.
    """

    async def connect(self) -> None:
        """서버에 연결."""
        ...

    async def disconnect(self) -> None:
        """서버 연결 해제."""
        ...

    async def list_tools(self) -> List[MCPToolInfo]:
        """사용 가능한 도구 목록."""
        ...

    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """도구 호출."""
        ...

    async def health_check(self) -> bool:
        """헬스 체크."""
        ...


@runtime_checkable
class MCPServerProtocol(Protocol):
    """MCP 서버 프로토콜.

    MCP 서버가 구현해야 하는 인터페이스.
    """

    def get_capabilities(self) -> MCPCapabilities:
        """서버 기능 반환."""
        ...

    def list_tools(self) -> List[MCPToolInfo]:
        """도구 목록 반환."""
        ...

    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """도구 실행."""
        ...
