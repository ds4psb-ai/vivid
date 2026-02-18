# P0 Phase 4: MCP Integration Plan 2026

> External Tool Integration via Model Context Protocol

---

## Executive Summary

Phase 4는 Vivid의 Dynamic DAG Workflow를 **2026 MCP 표준**과 통합하여 외부 도구 연동 및 확장성을 확보합니다.

### 핵심 목표

| 목표 | 설명 | 기대 효과 |
|------|------|----------|
| **External MCP Client** | 외부 MCP 서버 연동 (Tavily, Qdrant, Playwright) | RAG 확장, E2E 테스트 |
| **Internal MCP Gateway** | Dimension Tools를 MCP 프로토콜로 노출 | 표준화된 도구 접근 |
| **DAG-MCP Bridge** | Workflow Node가 MCP 도구 호출 | 동적 도구 확장 |
| **MCP Registry** | 도구 검색/인증/감사 인프라 | 거버넌스, 보안 |

**예상 기간**: 2주
**추가 비용**: ~$0 (오픈소스 + 무료 티어)

---

## 1. 2026 MCP Landscape Analysis

### 1.1 Industry Adoption (2026)

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Ecosystem 2026                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Platform Adoption:                                             │
│  ├── Anthropic (창시자)     ─ Claude Desktop, Claude Code      │
│  ├── OpenAI                 ─ ChatGPT Plugins → MCP 전환 중    │
│  ├── Google                 ─ Gemini MCP 통합 (2025.12)        │
│  ├── Microsoft              ─ Azure AI Agent Service           │
│  └── Linux Foundation       ─ 중립 거버넌스 (2025.11)          │
│                                                                 │
│  Market Size: $1.8B (2025) → $4.2B (2026 예상)                 │
│  Server Registry: 20,000+ MCP 서버 (2025.12 기준)              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Key 2026 Trends

| Trend | Description | Vivid 적용 |
|-------|-------------|-----------|
| **MCP Gateway** | 중앙 집중식 인증/감사/정책 | ToolCapabilityRegistry + Auth |
| **Streamable HTTP** | SSE 기반 실시간 스트리밍 | FastAPI + SSE 활용 |
| **OBO Token Pattern** | On-Behalf-Of 권한 위임 | Run-Token 시스템 연동 |
| **Protocol Evolution** | Resources, Tools, Prompts, Sampling | 4가지 기본 요소 지원 |
| **Registry Discovery** | 런타임 도구 검색 | registry.modelcontextprotocol.io |

### 1.3 FastMCP Framework (권장)

```python
# FastMCP - 2026 Python MCP 표준 프레임워크
# https://github.com/jlowin/fastmcp

from fastmcp import FastMCP, Context

mcp = FastMCP("vivid-dimension-tools")

@mcp.tool
async def generate_storyboard(
    concept: str,
    style: str = "cinematic",
    ctx: Context = None,
) -> dict:
    """Generate storyboard from concept"""
    await ctx.info(f"Generating storyboard: {concept}")
    # ... implementation
    return {"frames": [...]}

# FastAPI 통합
from fastmcp import FastMCP
mcp = FastMCP.from_fastapi(app=fastapi_app)
```

---

## 2. Architecture Design

### 2.1 Target Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Vivid MCP Integration Architecture                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────┐                                                   │
│  │   External MCP       │      ┌──────────────────────────────────┐        │
│  │   Servers            │      │        Vivid Backend              │        │
│  ├──────────────────────┤      │                                   │        │
│  │ ┌────────┐ ┌───────┐ │      │  ┌─────────────────────────────┐ │        │
│  │ │Tavily  │ │Qdrant │ │      │  │      MCP Gateway             │ │        │
│  │ │Search  │ │Vector │ │ ◄────┼──┤  (Auth, Audit, Rate Limit)  │ │        │
│  │ └────────┘ └───────┘ │      │  └──────────────┬──────────────┘ │        │
│  │ ┌────────┐ ┌───────┐ │      │                 │                │        │
│  │ │Playwright│ │Custom│ │      │  ┌──────────────▼──────────────┐ │        │
│  │ │Browser │ │ MCP  │ │      │  │     MCP Client Manager       │ │        │
│  │ └────────┘ └───────┘ │      │  │  (Connection Pool, Health)  │ │        │
│  └──────────────────────┘      │  └──────────────┬──────────────┘ │        │
│                                │                 │                │        │
│                                │  ┌──────────────▼──────────────┐ │        │
│  ┌──────────────────────┐      │  │   Unified Tool Registry     │ │        │
│  │   Internal MCP       │      │  │  (MCP + Native Tools)       │ │        │
│  │   Servers            │      │  └──────────────┬──────────────┘ │        │
│  ├──────────────────────┤      │                 │                │        │
│  │ ┌────────────────┐   │      │  ┌──────────────▼──────────────┐ │        │
│  │ │ Dimension Tools│   │ ◄────┼──┤    DAG Workflow Executor    │ │        │
│  │ │ (as MCP)       │   │      │  │  (HITL + MCP Tool Calls)    │ │        │
│  │ └────────────────┘   │      │  └─────────────────────────────┘ │        │
│  │ ┌────────────────┐   │      │                                  │        │
│  │ │ Pattern Truth  │   │      └──────────────────────────────────┘        │
│  │ │ MCP (existing) │   │                                                   │
│  │ └────────────────┘   │                                                   │
│  └──────────────────────┘                                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Breakdown

| Component | 역할 | 기존 코드 | 신규 개발 |
|-----------|------|----------|----------|
| MCP Gateway | 인증, 감사, 정책 | `routers/mcp.py` | Gateway 클래스 |
| MCP Client Manager | 외부 서버 연결 관리 | - | 전체 신규 |
| Unified Tool Registry | MCP + Native 통합 | `workflow/registry.py` | MCP 어댑터 |
| DAG-MCP Bridge | Workflow에서 MCP 호출 | `workflow/executor.py` | MCP ToolExecutor |
| Internal MCP Server | Dimension Tools 노출 | `pattern_truth_mcp.py` | FastMCP 전환 |

---

## 3. Implementation Plan

### 3.1 Phase 4.1: MCP Client Infrastructure (Week 1)

#### 3.1.1 MCPClientManager

```python
# backend/app/mcp/client_manager.py

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import httpx
from pydantic import BaseModel


class MCPTransport(str, Enum):
    """MCP 전송 프로토콜"""
    STDIO = "stdio"       # 로컬 프로세스
    HTTP_SSE = "http_sse" # Streamable HTTP (권장)
    WEBSOCKET = "ws"      # WebSocket


class MCPServerConfig(BaseModel):
    """외부 MCP 서버 설정"""
    server_id: str
    name: str
    transport: MCPTransport = MCPTransport.HTTP_SSE
    url: Optional[str] = None          # HTTP/WS용
    command: Optional[str] = None      # STDIO용 (npx, python 등)
    args: List[str] = []
    env: Dict[str, str] = {}
    # 인증
    auth_type: Optional[str] = None    # "api_key", "oauth2", "none"
    auth_config: Dict[str, Any] = {}
    # 제약
    timeout_seconds: int = 30
    max_retries: int = 3
    rate_limit_rpm: int = 60           # Requests per minute
    enabled: bool = True


@dataclass
class MCPToolCall:
    """MCP 도구 호출 결과"""
    tool_name: str
    arguments: Dict[str, Any]
    result: Any
    success: bool
    error: Optional[str] = None
    latency_ms: float = 0.0
    server_id: str = ""


class MCPClientManager:
    """외부 MCP 서버 연결 관리자

    2026 Best Practices:
    - Connection pooling for HTTP transports
    - Automatic reconnection with exponential backoff
    - Health check with circuit breaker pattern
    - Audit logging for compliance
    """

    def __init__(self):
        self._servers: Dict[str, MCPServerConfig] = {}
        self._clients: Dict[str, Any] = {}  # Lazy-loaded clients
        self._health_status: Dict[str, bool] = {}
        self._lock = asyncio.Lock()

    async def register_server(self, config: MCPServerConfig) -> None:
        """MCP 서버 등록"""
        async with self._lock:
            self._servers[config.server_id] = config
            self._health_status[config.server_id] = False  # Unknown

    async def unregister_server(self, server_id: str) -> None:
        """MCP 서버 해제"""
        async with self._lock:
            if server_id in self._clients:
                await self._disconnect(server_id)
            self._servers.pop(server_id, None)
            self._health_status.pop(server_id, None)

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> MCPToolCall:
        """MCP 도구 호출

        Args:
            server_id: 대상 MCP 서버 ID
            tool_name: 호출할 도구 이름
            arguments: 도구 인자

        Returns:
            MCPToolCall with result
        """
        import time
        start = time.time()

        config = self._servers.get(server_id)
        if not config:
            return MCPToolCall(
                tool_name=tool_name,
                arguments=arguments,
                result=None,
                success=False,
                error=f"Server not found: {server_id}",
                server_id=server_id,
            )

        if not config.enabled:
            return MCPToolCall(
                tool_name=tool_name,
                arguments=arguments,
                result=None,
                success=False,
                error=f"Server disabled: {server_id}",
                server_id=server_id,
            )

        try:
            client = await self._get_or_create_client(server_id)
            result = await self._execute_tool_call(
                client, config, tool_name, arguments
            )
            latency = (time.time() - start) * 1000

            return MCPToolCall(
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                success=True,
                latency_ms=latency,
                server_id=server_id,
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return MCPToolCall(
                tool_name=tool_name,
                arguments=arguments,
                result=None,
                success=False,
                error=str(e),
                latency_ms=latency,
                server_id=server_id,
            )

    async def list_tools(self, server_id: str) -> List[Dict[str, Any]]:
        """서버의 사용 가능한 도구 목록"""
        config = self._servers.get(server_id)
        if not config or not config.enabled:
            return []

        client = await self._get_or_create_client(server_id)
        return await self._fetch_tools(client, config)

    async def health_check(self, server_id: str) -> bool:
        """서버 헬스 체크"""
        try:
            config = self._servers.get(server_id)
            if not config:
                return False

            client = await self._get_or_create_client(server_id)
            # Implementation depends on transport
            return await self._ping_server(client, config)
        except Exception:
            return False

    async def health_check_all(self) -> Dict[str, bool]:
        """모든 서버 헬스 체크 (병렬)"""
        tasks = [
            self.health_check(server_id)
            for server_id in self._servers.keys()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            server_id: result if isinstance(result, bool) else False
            for server_id, result in zip(self._servers.keys(), results)
        }

    # --- Private Methods ---

    async def _get_or_create_client(self, server_id: str) -> Any:
        """클라이언트 인스턴스 가져오기 (Lazy)"""
        if server_id not in self._clients:
            config = self._servers[server_id]
            self._clients[server_id] = await self._create_client(config)
        return self._clients[server_id]

    async def _create_client(self, config: MCPServerConfig) -> Any:
        """전송 프로토콜에 따른 클라이언트 생성"""
        if config.transport == MCPTransport.HTTP_SSE:
            return httpx.AsyncClient(
                base_url=config.url,
                timeout=config.timeout_seconds,
                headers=self._build_auth_headers(config),
            )
        elif config.transport == MCPTransport.STDIO:
            # STDIO: subprocess 관리
            # FastMCP Client 사용 권장
            from fastmcp import Client
            return Client(config.command, args=config.args, env=config.env)
        else:
            raise ValueError(f"Unsupported transport: {config.transport}")

    def _build_auth_headers(self, config: MCPServerConfig) -> Dict[str, str]:
        """인증 헤더 생성"""
        if config.auth_type == "api_key":
            key = config.auth_config.get("api_key", "")
            header_name = config.auth_config.get("header", "Authorization")
            return {header_name: f"Bearer {key}"}
        return {}

    async def _execute_tool_call(
        self,
        client: Any,
        config: MCPServerConfig,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """실제 도구 호출 실행"""
        if config.transport == MCPTransport.HTTP_SSE:
            response = await client.post(
                "/tools/call",
                json={"tool": tool_name, "arguments": arguments},
            )
            response.raise_for_status()
            return response.json()
        elif config.transport == MCPTransport.STDIO:
            return await client.call_tool(tool_name, arguments)
        else:
            raise ValueError(f"Unsupported transport: {config.transport}")


# Singleton
_mcp_client_manager: Optional[MCPClientManager] = None

def get_mcp_client_manager() -> MCPClientManager:
    """MCP Client Manager 싱글톤"""
    global _mcp_client_manager
    if _mcp_client_manager is None:
        _mcp_client_manager = MCPClientManager()
    return _mcp_client_manager
```

#### 3.1.2 Default MCP Servers Configuration

```python
# backend/app/mcp/default_servers.py

from app.mcp.client_manager import (
    MCPClientManager,
    MCPServerConfig,
    MCPTransport,
)
from app.config import settings


async def register_default_mcp_servers(manager: MCPClientManager) -> None:
    """기본 MCP 서버 등록 (Tier 1)

    Reference: 27_MCP_INTEGRATION_SPEC_V1.md
    """

    # 1. Tavily Search (RAG Enhancement)
    if settings.TAVILY_API_KEY:
        await manager.register_server(MCPServerConfig(
            server_id="tavily",
            name="Tavily AI Search",
            transport=MCPTransport.HTTP_SSE,
            url="https://mcp.tavily.com",
            auth_type="api_key",
            auth_config={"api_key": settings.TAVILY_API_KEY},
            rate_limit_rpm=50,  # Free tier limit
            enabled=True,
        ))

    # 2. Qdrant Vector Search (Tier 1 RAG)
    await manager.register_server(MCPServerConfig(
        server_id="qdrant",
        name="Qdrant Vector Search",
        transport=MCPTransport.HTTP_SSE,
        url=f"{settings.QDRANT_HOST}:6333",
        auth_type="api_key" if settings.QDRANT_API_KEY else "none",
        auth_config={"api_key": settings.QDRANT_API_KEY} if settings.QDRANT_API_KEY else {},
        enabled=True,
    ))

    # 3. Playwright Browser (E2E Testing)
    await manager.register_server(MCPServerConfig(
        server_id="playwright",
        name="Playwright Browser",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["@playwright/mcp@latest"],
        enabled=settings.ENABLE_PLAYWRIGHT_MCP,
    ))

    # 4. Filesystem (Local Files)
    await manager.register_server(MCPServerConfig(
        server_id="filesystem",
        name="Filesystem Access",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["@modelcontextprotocol/server-filesystem", "/tmp/vivid-workspace"],
        enabled=settings.ENABLE_FILESYSTEM_MCP,
    ))


# Tier 2 servers (optional, premium)
async def register_premium_mcp_servers(manager: MCPClientManager) -> None:
    """프리미엄 MCP 서버 등록 (유료)"""
    pass  # Future: Google Sheets, Notion, etc.
```

### 3.2 Phase 4.2: MCP-DAG Bridge (Week 1-2)

#### 3.2.1 MCPToolExecutor

```python
# backend/app/workflow/mcp_executor.py

from typing import Dict, Any, Optional, List
from app.workflow.executor import ToolExecutor, ToolExecutionResult
from app.workflow.types import DAGNode
from app.mcp.client_manager import get_mcp_client_manager, MCPToolCall


class MCPToolExecutor(ToolExecutor):
    """MCP 기반 도구 실행기

    DAG Workflow에서 외부 MCP 서버의 도구를 호출합니다.

    Usage:
        executor = MCPToolExecutor()
        result = await executor.execute(
            node=dag_node,
            inputs={"query": "봉준호 영화 촬영 기법"},
            context={"user_id": "..."},
        )
    """

    def __init__(self):
        self._manager = get_mcp_client_manager()
        # Tool ID → MCP Server mapping
        self._tool_server_map: Dict[str, str] = {}

    def register_tool_mapping(
        self,
        tool_id: str,
        server_id: str,
        mcp_tool_name: Optional[str] = None,
    ) -> None:
        """도구 ID와 MCP 서버 매핑

        Args:
            tool_id: Vivid 내부 도구 ID (e.g., "tavily_search")
            server_id: MCP 서버 ID (e.g., "tavily")
            mcp_tool_name: MCP 도구 이름 (없으면 tool_id 사용)
        """
        self._tool_server_map[tool_id] = {
            "server_id": server_id,
            "mcp_tool_name": mcp_tool_name or tool_id,
        }

    async def execute(
        self,
        node: DAGNode,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ToolExecutionResult:
        """MCP 도구 실행

        Args:
            node: DAG 노드
            inputs: 입력 데이터
            context: 실행 컨텍스트

        Returns:
            ToolExecutionResult
        """
        tool_id = node.tool_id

        # 매핑 확인
        mapping = self._tool_server_map.get(tool_id)
        if not mapping:
            return ToolExecutionResult(
                success=False,
                outputs={},
                error=f"No MCP mapping for tool: {tool_id}",
            )

        # MCP 호출
        mcp_result = await self._manager.call_tool(
            server_id=mapping["server_id"],
            tool_name=mapping["mcp_tool_name"],
            arguments=inputs,
        )

        if mcp_result.success:
            return ToolExecutionResult(
                success=True,
                outputs=self._transform_outputs(node, mcp_result.result),
                credit_cost=self._calculate_credit_cost(node, mcp_result),
                latency_ms=int(mcp_result.latency_ms),
            )
        else:
            return ToolExecutionResult(
                success=False,
                outputs={},
                error=mcp_result.error,
                latency_ms=int(mcp_result.latency_ms),
            )

    def _transform_outputs(
        self,
        node: DAGNode,
        mcp_result: Any,
    ) -> Dict[str, Any]:
        """MCP 결과를 DAG 출력 포맷으로 변환"""
        # 노드의 can_provide에 맞게 출력 매핑
        outputs = {}

        if isinstance(mcp_result, dict):
            # 직접 매핑 시도
            for port in node.config.get("output_mapping", []):
                if port["mcp_key"] in mcp_result:
                    outputs[port["vivid_key"]] = mcp_result[port["mcp_key"]]
        else:
            # 단일 결과
            outputs["result"] = mcp_result

        return outputs

    def _calculate_credit_cost(
        self,
        node: DAGNode,
        mcp_result: MCPToolCall,
    ) -> int:
        """MCP 호출 크레딧 비용 계산"""
        # 기본 비용 + 서버별 가중치
        base_cost = node.config.get("credit_cost", 1)
        server_multiplier = {
            "tavily": 2,      # 외부 API
            "qdrant": 1,      # 내부
            "playwright": 3,  # 리소스 집약적
        }.get(mcp_result.server_id, 1)

        return base_cost * server_multiplier


class HybridToolExecutor(ToolExecutor):
    """하이브리드 도구 실행기 (Native + MCP)

    내부 도구는 직접 실행, MCP 매핑된 도구는 MCP로 실행.
    """

    def __init__(
        self,
        native_executor: ToolExecutor,
        mcp_executor: MCPToolExecutor,
    ):
        self._native = native_executor
        self._mcp = mcp_executor

    async def execute(
        self,
        node: DAGNode,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ToolExecutionResult:
        """도구 실행 (라우팅)"""
        # MCP 매핑 확인
        if node.tool_id in self._mcp._tool_server_map:
            return await self._mcp.execute(node, inputs, context)
        else:
            return await self._native.execute(node, inputs, context)
```

#### 3.2.2 Default MCP Tool Mappings

```python
# backend/app/workflow/mcp_tool_mappings.py

"""기본 MCP 도구 매핑

Vivid 내부 도구 ID와 외부 MCP 서버 도구를 연결합니다.
"""

# Tool ID → MCP Server + Tool Name
DEFAULT_MCP_MAPPINGS = {
    # Tavily Search
    "web_search": {
        "server_id": "tavily",
        "mcp_tool_name": "tavily-search",
        "description": "AI-optimized web search",
    },
    "web_extract": {
        "server_id": "tavily",
        "mcp_tool_name": "tavily-extract",
        "description": "Extract content from URLs",
    },

    # Qdrant Vector
    "semantic_search": {
        "server_id": "qdrant",
        "mcp_tool_name": "search",
        "description": "Semantic vector search",
    },
    "vector_upsert": {
        "server_id": "qdrant",
        "mcp_tool_name": "upsert",
        "description": "Upsert vectors",
    },

    # Playwright Browser
    "browser_navigate": {
        "server_id": "playwright",
        "mcp_tool_name": "puppeteer_navigate",
        "description": "Navigate browser to URL",
    },
    "browser_screenshot": {
        "server_id": "playwright",
        "mcp_tool_name": "puppeteer_screenshot",
        "description": "Take browser screenshot",
    },
    "browser_click": {
        "server_id": "playwright",
        "mcp_tool_name": "puppeteer_click",
        "description": "Click element in browser",
    },

    # Filesystem
    "file_read": {
        "server_id": "filesystem",
        "mcp_tool_name": "read_file",
        "description": "Read file content",
    },
    "file_write": {
        "server_id": "filesystem",
        "mcp_tool_name": "write_file",
        "description": "Write file content",
    },
}


def register_default_mappings(executor: "MCPToolExecutor") -> None:
    """기본 매핑 등록"""
    for tool_id, config in DEFAULT_MCP_MAPPINGS.items():
        executor.register_tool_mapping(
            tool_id=tool_id,
            server_id=config["server_id"],
            mcp_tool_name=config["mcp_tool_name"],
        )
```

### 3.3 Phase 4.3: Dimension Tools as MCP (Week 2)

#### 3.3.1 FastMCP Integration

```python
# backend/app/mcp_servers/dimension_tools_mcp.py

"""Dimension Tools를 MCP 프로토콜로 노출

2026 Best Practice: FastMCP 사용
"""

from typing import Dict, Any, Optional, List
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field

from app.dimension_adapter import (
    run_reference_decode,
    run_storyboard_generate,
    run_image_generate,
    run_video_generate,
    run_aesthetic_direct,
    run_rag_collect,
)


# FastMCP 서버 생성
dimension_mcp = FastMCP(
    name="vivid-dimension-tools",
    version="1.0.0",
    description="Crebit Studio Dimension Tools for AI Content Creation",
)


# =========================================================================
# Tool Definitions
# =========================================================================

class ReferenceDecodeInput(BaseModel):
    """레퍼런스 분석 입력"""
    video_url: str = Field(..., description="분석할 영상 URL")
    analysis_depth: str = Field("detailed", description="분석 깊이: quick, detailed, comprehensive")
    auteur_key: Optional[str] = Field(None, description="거장 키 (e.g., bong, kubrick)")


class StoryboardInput(BaseModel):
    """스토리보드 생성 입력"""
    concept: str = Field(..., description="영상 컨셉")
    style: str = Field("cinematic", description="스타일: cinematic, documentary, commercial")
    duration_seconds: int = Field(30, description="예상 영상 길이 (초)")
    auteur_key: Optional[str] = Field(None, description="거장 키")


@dimension_mcp.tool
async def reference_decode(
    input: ReferenceDecodeInput,
    ctx: Context,
) -> Dict[str, Any]:
    """영상 레퍼런스 분석 (4D Dimension)

    YouTube/Vimeo URL을 분석하여 촬영 기법, 편집 스타일,
    미학적 요소를 추출합니다.
    """
    await ctx.info(f"Analyzing reference: {input.video_url}")

    result = await run_reference_decode(
        video_url=input.video_url,
        analysis_depth=input.analysis_depth,
        auteur_key=input.auteur_key,
    )

    return {
        "analysis": result.get("analysis"),
        "techniques": result.get("techniques", []),
        "style_notes": result.get("style_notes"),
        "evidence_refs": result.get("evidence_refs", []),
    }


@dimension_mcp.tool
async def storyboard_generate(
    input: StoryboardInput,
    ctx: Context,
) -> Dict[str, Any]:
    """스토리보드 생성 (Story Dimension)

    컨셉을 기반으로 씬별 스토리보드를 생성합니다.
    """
    await ctx.info(f"Generating storyboard for: {input.concept[:50]}...")

    result = await run_storyboard_generate(
        concept=input.concept,
        style=input.style,
        duration_seconds=input.duration_seconds,
        auteur_key=input.auteur_key,
    )

    return {
        "scenes": result.get("scenes", []),
        "total_duration": result.get("total_duration"),
        "style_guide": result.get("style_guide"),
    }


@dimension_mcp.tool
async def image_generate(
    prompt: str,
    aspect_ratio: str = "16:9",
    style: str = "photorealistic",
    ctx: Context = None,
) -> Dict[str, Any]:
    """이미지 생성 (3D Dimension)"""
    await ctx.info(f"Generating image: {prompt[:50]}...")

    result = await run_image_generate(
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        style=style,
    )

    return {
        "image_url": result.get("image_url"),
        "prompt_used": result.get("prompt_used"),
        "seed": result.get("seed"),
    }


@dimension_mcp.tool
async def aesthetic_direct(
    content_type: str,
    content_id: str,
    direction: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """미학 디렉션 (AD Dimension)

    생성된 콘텐츠에 미학적 피드백과 개선 방향을 제시합니다.
    """
    await ctx.info(f"Directing aesthetics for {content_type}:{content_id}")

    result = await run_aesthetic_direct(
        content_type=content_type,
        content_id=content_id,
        direction=direction,
    )

    return {
        "feedback": result.get("feedback"),
        "improvements": result.get("improvements", []),
        "score": result.get("score"),
    }


@dimension_mcp.tool
async def rag_collect(
    query: str,
    dimension: str = "4D",
    auteur_key: Optional[str] = None,
    max_results: int = 5,
    ctx: Context = None,
) -> Dict[str, Any]:
    """RAG 지식 수집

    거장 DNA 및 차원별 지식베이스에서 관련 정보를 검색합니다.
    """
    await ctx.info(f"Collecting RAG for: {query[:50]}...")

    result = await run_rag_collect(
        query=query,
        dimension=dimension,
        auteur_key=auteur_key,
        max_results=max_results,
    )

    return {
        "sources": result.get("sources", []),
        "summary": result.get("summary"),
        "evidence_refs": result.get("evidence_refs", []),
    }


# =========================================================================
# Resources (Read-only Data)
# =========================================================================

@dimension_mcp.resource("vivid://tools")
async def list_dimension_tools() -> str:
    """사용 가능한 Dimension Tools 목록"""
    return """
    Available Dimension Tools:
    - reference_decode: 영상 레퍼런스 분석 (4D)
    - storyboard_generate: 스토리보드 생성 (Story)
    - image_generate: 이미지 생성 (3D)
    - aesthetic_direct: 미학 디렉션 (AD)
    - rag_collect: RAG 지식 수집
    """


@dimension_mcp.resource("vivid://auteurs")
async def list_available_auteurs() -> str:
    """사용 가능한 거장 목록"""
    from app.rag.rag_presets import RAG_PRESETS

    auteurs = list(RAG_PRESETS.keys())
    return f"Available Auteurs: {', '.join(auteurs)}"


# =========================================================================
# Prompts (Reusable Templates)
# =========================================================================

@dimension_mcp.prompt
def cinematic_analysis_prompt(video_url: str, focus: str = "cinematography") -> str:
    """시네마틱 분석 프롬프트 템플릿"""
    return f"""
    Analyze the following video with focus on {focus}:

    Video URL: {video_url}

    Please identify:
    1. Camera techniques (shots, movements, angles)
    2. Lighting design
    3. Color grading approach
    4. Editing rhythm and pacing
    5. Sound design elements

    Provide specific timestamps for key moments.
    """


# =========================================================================
# Server Entry Point
# =========================================================================

def get_dimension_mcp_server() -> FastMCP:
    """Dimension MCP 서버 인스턴스"""
    return dimension_mcp


# FastAPI 통합용
async def run_dimension_mcp_stdio():
    """STDIO 모드로 MCP 서버 실행 (Claude Desktop용)"""
    dimension_mcp.run(transport="stdio")


async def run_dimension_mcp_http(port: int = 8200):
    """HTTP/SSE 모드로 MCP 서버 실행"""
    dimension_mcp.run(transport="http", port=port)
```

### 3.4 Phase 4.4: MCP Gateway & Audit (Week 2)

#### 3.4.1 MCP Gateway

```python
# backend/app/mcp/gateway.py

"""MCP Gateway - 중앙 집중식 인증/감사/정책

2026 Best Practice: Enterprise MCP Gateway Pattern
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class MCPAction(str, Enum):
    """MCP 액션 유형"""
    TOOL_CALL = "tool_call"
    RESOURCE_READ = "resource_read"
    PROMPT_GET = "prompt_get"


@dataclass
class MCPAuditLog:
    """MCP 감사 로그"""
    id: str
    timestamp: datetime
    user_id: str
    server_id: str
    action: MCPAction
    tool_name: Optional[str]
    arguments_hash: str  # 보안을 위해 해시만 저장
    result_summary: str
    latency_ms: float
    success: bool
    error: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]


class MCPPolicy(BaseModel):
    """MCP 정책 정의"""
    policy_id: str
    name: str
    # 허용/거부 규칙
    allowed_tools: List[str] = []      # 빈 리스트 = 모두 허용
    denied_tools: List[str] = []
    allowed_servers: List[str] = []
    denied_servers: List[str] = []
    # Rate Limiting
    max_calls_per_minute: int = 60
    max_calls_per_hour: int = 1000
    # 시간 제한
    allowed_hours: tuple = (0, 24)     # 24시간 허용
    # 비용 제한
    max_credit_per_call: int = 100
    max_credit_per_day: int = 10000


class MCPGateway:
    """MCP Gateway - 모든 MCP 호출의 중앙 관리

    Responsibilities:
    1. Authentication - Run-Token 검증
    2. Authorization - 정책 기반 접근 제어
    3. Rate Limiting - 호출 제한
    4. Audit Logging - 모든 호출 기록
    5. Routing - 적절한 MCP 서버로 라우팅
    """

    def __init__(
        self,
        client_manager: "MCPClientManager",
        db_session: Optional[AsyncSession] = None,
    ):
        self._client_manager = client_manager
        self._db = db_session
        self._policies: Dict[str, MCPPolicy] = {}
        self._rate_limits: Dict[str, List[datetime]] = {}  # user_id → timestamps
        self._default_policy = MCPPolicy(
            policy_id="default",
            name="Default Policy",
            max_calls_per_minute=30,
        )

    async def call_tool(
        self,
        user_id: str,
        server_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        run_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Gateway를 통한 MCP 도구 호출

        Args:
            user_id: 요청 사용자 ID
            server_id: 대상 MCP 서버 ID
            tool_name: 호출할 도구 이름
            arguments: 도구 인자
            run_token: Run-Token (있으면 크레딧 차감)

        Returns:
            MCP 호출 결과
        """
        import time
        start = time.time()

        # 1. 정책 체크
        policy = self._get_policy(user_id)
        policy_result = await self._check_policy(
            policy, user_id, server_id, tool_name
        )
        if not policy_result["allowed"]:
            return {
                "success": False,
                "error": f"Policy denied: {policy_result['reason']}",
            }

        # 2. Rate Limit 체크
        if not self._check_rate_limit(user_id, policy):
            return {
                "success": False,
                "error": "Rate limit exceeded",
            }

        # 3. MCP 호출 실행
        try:
            result = await self._client_manager.call_tool(
                server_id=server_id,
                tool_name=tool_name,
                arguments=arguments,
            )

            latency = (time.time() - start) * 1000

            # 4. 감사 로그
            await self._log_audit(
                user_id=user_id,
                server_id=server_id,
                action=MCPAction.TOOL_CALL,
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                latency_ms=latency,
                success=result.success,
                error=result.error,
            )

            # 5. Rate Limit 업데이트
            self._record_call(user_id)

            return {
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "latency_ms": latency,
            }

        except Exception as e:
            latency = (time.time() - start) * 1000
            logger.error(f"MCP Gateway error: {e}")

            await self._log_audit(
                user_id=user_id,
                server_id=server_id,
                action=MCPAction.TOOL_CALL,
                tool_name=tool_name,
                arguments=arguments,
                result=None,
                latency_ms=latency,
                success=False,
                error=str(e),
            )

            return {
                "success": False,
                "error": str(e),
                "latency_ms": latency,
            }

    def set_policy(self, user_id: str, policy: MCPPolicy) -> None:
        """사용자별 정책 설정"""
        self._policies[user_id] = policy

    def _get_policy(self, user_id: str) -> MCPPolicy:
        """사용자 정책 조회"""
        return self._policies.get(user_id, self._default_policy)

    async def _check_policy(
        self,
        policy: MCPPolicy,
        user_id: str,
        server_id: str,
        tool_name: str,
    ) -> Dict[str, Any]:
        """정책 검증"""
        # 서버 체크
        if policy.denied_servers and server_id in policy.denied_servers:
            return {"allowed": False, "reason": f"Server {server_id} denied"}
        if policy.allowed_servers and server_id not in policy.allowed_servers:
            return {"allowed": False, "reason": f"Server {server_id} not allowed"}

        # 도구 체크
        if policy.denied_tools and tool_name in policy.denied_tools:
            return {"allowed": False, "reason": f"Tool {tool_name} denied"}
        if policy.allowed_tools and tool_name not in policy.allowed_tools:
            return {"allowed": False, "reason": f"Tool {tool_name} not allowed"}

        # 시간 체크
        current_hour = datetime.now().hour
        if not (policy.allowed_hours[0] <= current_hour < policy.allowed_hours[1]):
            return {"allowed": False, "reason": "Outside allowed hours"}

        return {"allowed": True, "reason": "Policy passed"}

    def _check_rate_limit(self, user_id: str, policy: MCPPolicy) -> bool:
        """Rate Limit 체크"""
        now = datetime.now()
        calls = self._rate_limits.get(user_id, [])

        # 1분 이내 호출 수
        minute_ago = now.timestamp() - 60
        recent_calls = [c for c in calls if c.timestamp() > minute_ago]

        if len(recent_calls) >= policy.max_calls_per_minute:
            return False

        return True

    def _record_call(self, user_id: str) -> None:
        """호출 기록"""
        now = datetime.now()
        if user_id not in self._rate_limits:
            self._rate_limits[user_id] = []
        self._rate_limits[user_id].append(now)

        # 오래된 기록 정리 (1시간 이상)
        hour_ago = now.timestamp() - 3600
        self._rate_limits[user_id] = [
            c for c in self._rate_limits[user_id]
            if c.timestamp() > hour_ago
        ]

    async def _log_audit(
        self,
        user_id: str,
        server_id: str,
        action: MCPAction,
        tool_name: Optional[str],
        arguments: Dict[str, Any],
        result: Any,
        latency_ms: float,
        success: bool,
        error: Optional[str],
    ) -> None:
        """감사 로그 기록"""
        import hashlib
        import json

        # 인자 해시 (보안)
        args_str = json.dumps(arguments, sort_keys=True, default=str)
        args_hash = hashlib.sha256(args_str.encode()).hexdigest()[:16]

        # 결과 요약
        result_summary = str(result)[:200] if result else ""

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "server_id": server_id,
            "action": action.value,
            "tool_name": tool_name,
            "arguments_hash": args_hash,
            "result_summary": result_summary,
            "latency_ms": latency_ms,
            "success": success,
            "error": error,
        }

        logger.info(f"MCP Audit: {log_entry}")

        # TODO: DB에 저장 (telemetry 테이블 활용)
```

---

## 4. API Endpoints

### 4.1 New MCP Endpoints

```python
# backend/app/routers/mcp_v2.py

"""MCP V2 Router - External Tool Integration"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from app.mcp.client_manager import get_mcp_client_manager
from app.mcp.gateway import MCPGateway
from app.auth import get_current_user

router = APIRouter(prefix="/mcp/v2", tags=["MCP V2"])


class MCPToolCallRequest(BaseModel):
    """MCP 도구 호출 요청"""
    server_id: str = Field(..., description="MCP 서버 ID")
    tool_name: str = Field(..., description="도구 이름")
    arguments: Dict[str, Any] = Field(default_factory=dict)


class MCPToolCallResponse(BaseModel):
    """MCP 도구 호출 응답"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    latency_ms: float


@router.get("/servers")
async def list_mcp_servers(
    current_user = Depends(get_current_user),
):
    """등록된 MCP 서버 목록"""
    manager = get_mcp_client_manager()
    servers = []

    for server_id, config in manager._servers.items():
        health = await manager.health_check(server_id)
        servers.append({
            "server_id": server_id,
            "name": config.name,
            "transport": config.transport.value,
            "enabled": config.enabled,
            "healthy": health,
        })

    return {"servers": servers}


@router.get("/servers/{server_id}/tools")
async def list_server_tools(
    server_id: str,
    current_user = Depends(get_current_user),
):
    """특정 MCP 서버의 도구 목록"""
    manager = get_mcp_client_manager()
    tools = await manager.list_tools(server_id)
    return {"server_id": server_id, "tools": tools}


@router.post("/call", response_model=MCPToolCallResponse)
async def call_mcp_tool(
    request: MCPToolCallRequest,
    current_user = Depends(get_current_user),
):
    """MCP 도구 호출 (Gateway 경유)"""
    gateway = MCPGateway(get_mcp_client_manager())

    result = await gateway.call_tool(
        user_id=current_user.id,
        server_id=request.server_id,
        tool_name=request.tool_name,
        arguments=request.arguments,
    )

    return MCPToolCallResponse(**result)


@router.get("/health")
async def mcp_health_check():
    """모든 MCP 서버 헬스 체크"""
    manager = get_mcp_client_manager()
    health = await manager.health_check_all()

    return {
        "overall": all(health.values()) if health else False,
        "servers": health,
    }
```

---

## 5. Database Migrations

### 5.1 MCP Audit Table

```python
# backend/alembic/versions/014_add_mcp_audit.py

"""Add MCP Audit tables

Revision ID: 014_add_mcp_audit
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


def upgrade():
    # MCP Audit Log
    op.create_table(
        "mcp_audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("timestamp", sa.DateTime, nullable=False, index=True),
        sa.Column("user_id", sa.String(64), nullable=False, index=True),
        sa.Column("server_id", sa.String(64), nullable=False, index=True),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("tool_name", sa.String(100), nullable=True),
        sa.Column("arguments_hash", sa.String(64), nullable=True),
        sa.Column("result_summary", sa.Text, nullable=True),
        sa.Column("latency_ms", sa.Float, nullable=False, default=0.0),
        sa.Column("success", sa.Boolean, nullable=False, default=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
    )

    # MCP Server Registry
    op.create_table(
        "mcp_server_registry",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("server_id", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("transport", sa.String(32), nullable=False),
        sa.Column("url", sa.String(500), nullable=True),
        sa.Column("command", sa.String(255), nullable=True),
        sa.Column("args", JSONB, default=list),
        sa.Column("env", JSONB, default=dict),
        sa.Column("auth_type", sa.String(32), nullable=True),
        sa.Column("auth_config", JSONB, default=dict),
        sa.Column("enabled", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, onupdate=sa.func.now()),
    )

    # Indexes
    op.create_index(
        "ix_mcp_audit_user_timestamp",
        "mcp_audit_logs",
        ["user_id", "timestamp"],
    )
    op.create_index(
        "ix_mcp_audit_server_timestamp",
        "mcp_audit_logs",
        ["server_id", "timestamp"],
    )


def downgrade():
    op.drop_table("mcp_audit_logs")
    op.drop_table("mcp_server_registry")
```

---

## 6. Testing Strategy

### 6.1 Test Cases

```python
# backend/tests/mcp/test_mcp_client.py

"""MCP Client Manager Tests"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from app.mcp.client_manager import (
    MCPClientManager,
    MCPServerConfig,
    MCPTransport,
)


class TestMCPClientManager:
    """MCPClientManager 테스트"""

    @pytest_asyncio.fixture
    async def manager(self):
        return MCPClientManager()

    @pytest.mark.asyncio
    async def test_register_server(self, manager):
        """서버 등록 테스트"""
        config = MCPServerConfig(
            server_id="test-server",
            name="Test Server",
            transport=MCPTransport.HTTP_SSE,
            url="http://localhost:8000",
        )

        await manager.register_server(config)

        assert "test-server" in manager._servers
        assert manager._servers["test-server"].name == "Test Server"

    @pytest.mark.asyncio
    async def test_unregister_server(self, manager):
        """서버 해제 테스트"""
        config = MCPServerConfig(
            server_id="test-server",
            name="Test Server",
            transport=MCPTransport.HTTP_SSE,
            url="http://localhost:8000",
        )

        await manager.register_server(config)
        await manager.unregister_server("test-server")

        assert "test-server" not in manager._servers

    @pytest.mark.asyncio
    async def test_call_tool_server_not_found(self, manager):
        """존재하지 않는 서버 호출"""
        result = await manager.call_tool(
            server_id="nonexistent",
            tool_name="test_tool",
            arguments={},
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_call_tool_disabled_server(self, manager):
        """비활성화된 서버 호출"""
        config = MCPServerConfig(
            server_id="disabled-server",
            name="Disabled Server",
            transport=MCPTransport.HTTP_SSE,
            url="http://localhost:8000",
            enabled=False,
        )

        await manager.register_server(config)

        result = await manager.call_tool(
            server_id="disabled-server",
            tool_name="test_tool",
            arguments={},
        )

        assert result.success is False
        assert "disabled" in result.error.lower()


class TestMCPGateway:
    """MCP Gateway 테스트"""

    @pytest.mark.asyncio
    async def test_policy_denial(self):
        """정책 거부 테스트"""
        from app.mcp.gateway import MCPGateway, MCPPolicy

        manager = MCPClientManager()
        gateway = MCPGateway(manager)

        # 특정 도구 금지 정책
        gateway.set_policy("user123", MCPPolicy(
            policy_id="strict",
            name="Strict Policy",
            denied_tools=["dangerous_tool"],
        ))

        result = await gateway.call_tool(
            user_id="user123",
            server_id="test",
            tool_name="dangerous_tool",
            arguments={},
        )

        assert result["success"] is False
        assert "denied" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_rate_limit(self):
        """Rate Limit 테스트"""
        from app.mcp.gateway import MCPGateway, MCPPolicy

        manager = MCPClientManager()
        gateway = MCPGateway(manager)

        # 분당 2회 제한
        gateway.set_policy("user123", MCPPolicy(
            policy_id="limited",
            name="Limited Policy",
            max_calls_per_minute=2,
        ))

        # 3번째 호출은 제한되어야 함
        gateway._record_call("user123")
        gateway._record_call("user123")

        result = gateway._check_rate_limit("user123", gateway._get_policy("user123"))
        assert result is False
```

### 6.2 Integration Tests

```python
# backend/tests/mcp/test_mcp_integration.py

"""MCP Integration Tests (External Servers)"""

import pytest
import os

from app.mcp.client_manager import get_mcp_client_manager
from app.mcp.default_servers import register_default_mcp_servers


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("TAVILY_API_KEY"),
    reason="TAVILY_API_KEY not set"
)
class TestTavilyIntegration:
    """Tavily MCP 통합 테스트"""

    @pytest.mark.asyncio
    async def test_tavily_search(self):
        """Tavily 검색 테스트"""
        manager = get_mcp_client_manager()
        await register_default_mcp_servers(manager)

        result = await manager.call_tool(
            server_id="tavily",
            tool_name="tavily-search",
            arguments={"query": "Python FastAPI best practices 2026"},
        )

        assert result.success is True
        assert result.result is not None


@pytest.mark.integration
class TestQdrantIntegration:
    """Qdrant MCP 통합 테스트"""

    @pytest.mark.asyncio
    async def test_qdrant_health(self):
        """Qdrant 헬스 체크"""
        manager = get_mcp_client_manager()
        await register_default_mcp_servers(manager)

        healthy = await manager.health_check("qdrant")
        # Qdrant가 실행 중이면 True, 아니면 False
        assert isinstance(healthy, bool)
```

---

## 7. Configuration

### 7.1 Environment Variables

```bash
# .env additions for Phase 4

# MCP Servers
TAVILY_API_KEY=tvly-xxx            # Tavily AI Search
QDRANT_HOST=http://localhost       # Qdrant Vector DB
QDRANT_API_KEY=                    # Qdrant API Key (optional)

# MCP Feature Flags
ENABLE_PLAYWRIGHT_MCP=false        # Playwright Browser (resource-heavy)
ENABLE_FILESYSTEM_MCP=false        # Filesystem Access (security)
ENABLE_EXTERNAL_MCP=true           # External MCP Servers

# MCP Gateway
MCP_DEFAULT_RATE_LIMIT_RPM=30      # Default rate limit
MCP_AUDIT_ENABLED=true             # Audit logging
MCP_GATEWAY_TIMEOUT_SECONDS=30     # Gateway timeout
```

### 7.2 Config Class

```python
# backend/app/config.py additions

class Settings(BaseSettings):
    # ... existing settings ...

    # MCP Configuration
    TAVILY_API_KEY: str = ""
    QDRANT_HOST: str = "http://localhost"
    QDRANT_API_KEY: str = ""

    ENABLE_PLAYWRIGHT_MCP: bool = False
    ENABLE_FILESYSTEM_MCP: bool = False
    ENABLE_EXTERNAL_MCP: bool = True

    MCP_DEFAULT_RATE_LIMIT_RPM: int = 30
    MCP_AUDIT_ENABLED: bool = True
    MCP_GATEWAY_TIMEOUT_SECONDS: int = 30
```

---

## 8. Rollout Plan

### 8.1 Phase 4 Timeline

| Week | Task | Deliverables |
|------|------|--------------|
| **W1 D1-2** | MCP Client Manager | `client_manager.py`, unit tests |
| **W1 D3-4** | Default MCP Servers | `default_servers.py`, Tavily/Qdrant 연동 |
| **W1 D5** | MCPToolExecutor | `mcp_executor.py`, DAG 브릿지 |
| **W2 D1-2** | Dimension Tools MCP | `dimension_tools_mcp.py`, FastMCP 통합 |
| **W2 D3-4** | MCP Gateway | `gateway.py`, audit logging |
| **W2 D5** | Integration Tests | E2E tests, documentation |

### 8.2 Success Criteria

- [ ] 3+ 외부 MCP 서버 연동 (Tavily, Qdrant, Playwright)
- [ ] DAG Workflow에서 MCP 도구 호출 가능
- [ ] Dimension Tools가 MCP 프로토콜로 노출
- [ ] 모든 MCP 호출 감사 로그 기록
- [ ] 20+ 단위 테스트 통과
- [ ] 5+ 통합 테스트 통과 (실제 외부 서버)

---

## 9. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| 외부 MCP 서버 불안정 | 워크플로우 실패 | Circuit breaker, 폴백 로직 |
| Rate Limit 초과 | 서비스 중단 | 사전 제한, 큐잉 |
| 보안 취약점 | 데이터 유출 | Gateway 인증, 감사 로그 |
| 비용 초과 | 예산 초과 | 크레딧 제한, 알림 |
| MCP 프로토콜 변경 | 호환성 문제 | FastMCP 최신 버전 유지 |

---

## 10. References

### 10.1 MCP Resources

- [MCP Official Spec](https://modelcontextprotocol.io)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [MCP Registry](https://registry.modelcontextprotocol.io)
- [Anthropic MCP Blog](https://www.anthropic.com/news/model-context-protocol)

### 10.2 Vivid Internal Docs

- `27_MCP_INTEGRATION_SPEC_V1.md` - MCP 통합 스펙
- `backend/app/routers/mcp.py` - 기존 MCP 라우터
- `backend/app/mcp_servers/pattern_truth_mcp.py` - 내부 MCP 서버

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-01-16 | Initial Phase 4 plan |
