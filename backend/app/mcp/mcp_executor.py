"""MCP Tool Executor - DAG-MCP Bridge (P0 Phase 4 - 2026).

Dynamic DAG Workflow에서 MCP 도구를 호출하기 위한 브릿지.

2026 Best Practices:
    - Hybrid execution (Native + MCP)
    - Automatic tool mapping
    - Output transformation
    - Credit cost tracking
    - Comprehensive error handling

Architecture:
    ┌─────────────────────────────────────────────────────┐
    │             HITLWorkflowExecutor                    │
    │  (app/workflow/executor.py)                         │
    └────────────────────┬────────────────────────────────┘
                         │ calls execute()
                         ▼
    ┌─────────────────────────────────────────────────────┐
    │             HybridToolExecutor                      │
    │  (routes to Native or MCP based on mapping)         │
    └───────┬─────────────────────────────┬───────────────┘
            │                             │
            ▼                             ▼
    ┌───────────────┐           ┌─────────────────────────┐
    │ NativeExecutor│           │   MCPToolExecutor       │
    │ (dimension_   │           │   ┌───────────────────┐ │
    │  adapter.py)  │           │   │ MCPClientManager  │ │
    └───────────────┘           │   │ (app/mcp/client)  │ │
                                │   └───────────────────┘ │
                                └─────────────────────────┘

Usage:
    from app.mcp.mcp_executor import (
        MCPToolExecutor,
        HybridToolExecutor,
        create_hybrid_executor,
    )

    # Create hybrid executor
    executor = await create_hybrid_executor()

    # Execute tool (automatically routes to MCP or native)
    result = await executor.execute(
        tool_id="web_search",
        inputs={"query": "봉준호 영화 촬영 기법"},
        context={"user_id": "..."},
    )
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple

from app.config import settings
from app.mcp.client import MCPClientManager, get_mcp_client_manager
from app.mcp.gateway import MCPGateway, get_mcp_gateway
from app.mcp.types import MCPToolCall, MCPErrorCode
from app.mcp.default_servers import (
    DEFAULT_TOOL_MAPPINGS,
    get_tool_mapping,
    register_default_servers,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Result Types
# =============================================================================

@dataclass
class ToolExecutionResult:
    """도구 실행 결과.

    Attributes:
        success: 성공 여부
        outputs: 출력 데이터
        error: 에러 메시지 (실패 시)
        error_code: 에러 코드
        latency_ms: 실행 시간 (밀리초)
        credit_cost: 사용된 크레딧
        metadata: 추가 메타데이터
        request_id: 요청 추적 ID
        timestamp: 실행 시각
    """
    success: bool
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    error_code: Optional[int] = None
    latency_ms: float = 0.0
    credit_cost: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환."""
        return {
            "success": self.success,
            "outputs": self.outputs,
            "error": self.error,
            "error_code": self.error_code,
            "latency_ms": self.latency_ms,
            "credit_cost": self.credit_cost,
            "metadata": self.metadata,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# Tool Executor Protocol
# =============================================================================

class ToolExecutorProtocol(Protocol):
    """도구 실행기 프로토콜."""

    async def execute(
        self,
        tool_id: str,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ToolExecutionResult:
        """도구 실행."""
        ...

    async def list_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록."""
        ...

    async def health_check(self) -> bool:
        """헬스 체크."""
        ...


# =============================================================================
# MCP Tool Executor
# =============================================================================

class MCPToolExecutor:
    """MCP 기반 도구 실행기.

    MCP 서버의 도구를 호출하고 결과를 변환합니다.

    Features:
        - Automatic tool mapping (Vivid ID → MCP tool)
        - Output transformation (MCP result → DAG output)
        - Credit cost calculation
        - Gateway integration (auth/audit)

    Example:
        >>> executor = MCPToolExecutor()
        >>> await executor.initialize()
        >>> result = await executor.execute(
        ...     tool_id="web_search",
        ...     inputs={"query": "AI trends 2026"},
        ...     context={"user_id": "user123"},
        ... )
    """

    def __init__(
        self,
        client_manager: Optional[MCPClientManager] = None,
        gateway: Optional[MCPGateway] = None,
        use_gateway: bool = True,
    ):
        """Initialize MCP executor.

        Args:
            client_manager: MCP Client Manager (None이면 싱글톤 사용)
            gateway: MCP Gateway (None이면 싱글톤 사용)
            use_gateway: Gateway 사용 여부 (인증/감사)
        """
        self._manager = client_manager
        self._gateway = gateway
        self._use_gateway = use_gateway and settings.MCP_GATEWAY_ENABLED
        self._initialized = False

        # Tool ID → MCP mapping 캐시
        self._tool_mappings: Dict[str, Dict[str, Any]] = {}

        # Output transformers (tool_id → transformer function)
        self._output_transformers: Dict[
            str, Callable[[Any, Dict[str, Any]], Dict[str, Any]]
        ] = {}

    async def initialize(self) -> None:
        """실행기 초기화.

        MCP 서버 등록 및 매핑 설정.
        """
        if self._initialized:
            return

        # Get or create manager
        if self._manager is None:
            self._manager = get_mcp_client_manager()

        # Start manager
        await self._manager.start()

        # Register default servers
        await register_default_servers(self._manager)

        # Get gateway
        if self._use_gateway and self._gateway is None:
            self._gateway = get_mcp_gateway()

        # Load default mappings
        self._tool_mappings = dict(DEFAULT_TOOL_MAPPINGS)

        # Register default output transformers
        self._register_default_transformers()

        self._initialized = True
        logger.info("MCPToolExecutor initialized")

    async def shutdown(self) -> None:
        """실행기 종료."""
        if self._manager:
            await self._manager.stop()
        self._initialized = False

    async def execute(
        self,
        tool_id: str,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ToolExecutionResult:
        """MCP 도구 실행.

        Args:
            tool_id: Vivid 내부 도구 ID
            inputs: 입력 데이터
            context: 실행 컨텍스트 (user_id, etc.)

        Returns:
            ToolExecutionResult with outputs or error
        """
        if not self._initialized:
            await self.initialize()

        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # 매핑 확인
        mapping = self._tool_mappings.get(tool_id)
        if not mapping:
            return ToolExecutionResult(
                success=False,
                error=f"No MCP mapping for tool: {tool_id}",
                error_code=MCPErrorCode.TOOL_NOT_FOUND.value,
                request_id=request_id,
            )

        server_id = mapping["server_id"]
        mcp_tool_name = mapping["mcp_tool_name"]
        credit_cost = mapping.get("credit_cost", settings.MCP_CREDIT_COST_DEFAULT)

        # 입력 변환
        transformed_inputs = self._transform_inputs(tool_id, inputs)

        try:
            # Gateway 또는 직접 호출
            if self._use_gateway and self._gateway:
                user_id = context.get("user_id", "anonymous")
                result = await self._gateway.call_tool(
                    user_id=user_id,
                    server_id=server_id,
                    tool_name=mcp_tool_name,
                    arguments=transformed_inputs,
                    ip_address=context.get("ip_address"),
                    user_agent=context.get("user_agent"),
                )

                latency_ms = (time.time() - start_time) * 1000

                if result["success"]:
                    # 출력 변환
                    outputs = self._transform_outputs(
                        tool_id, result["result"], inputs
                    )

                    return ToolExecutionResult(
                        success=True,
                        outputs=outputs,
                        latency_ms=latency_ms,
                        credit_cost=credit_cost,
                        request_id=result.get("request_id", request_id),
                        metadata={
                            "server_id": server_id,
                            "mcp_tool": mcp_tool_name,
                        },
                    )
                else:
                    return ToolExecutionResult(
                        success=False,
                        error=result.get("error"),
                        error_code=result.get("error_code"),
                        latency_ms=latency_ms,
                        request_id=result.get("request_id", request_id),
                    )

            else:
                # 직접 호출 (Gateway 없이)
                mcp_result = await self._manager.call_tool(
                    server_id=server_id,
                    tool_name=mcp_tool_name,
                    arguments=transformed_inputs,
                )

                latency_ms = (time.time() - start_time) * 1000

                if mcp_result.success:
                    outputs = self._transform_outputs(
                        tool_id, mcp_result.result, inputs
                    )

                    return ToolExecutionResult(
                        success=True,
                        outputs=outputs,
                        latency_ms=latency_ms,
                        credit_cost=credit_cost,
                        request_id=mcp_result.request_id,
                        metadata={
                            "server_id": server_id,
                            "mcp_tool": mcp_tool_name,
                        },
                    )
                else:
                    return ToolExecutionResult(
                        success=False,
                        error=mcp_result.error,
                        error_code=mcp_result.error_code.value if mcp_result.error_code else None,
                        latency_ms=latency_ms,
                        request_id=mcp_result.request_id,
                    )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.exception(f"MCP execution error: {e}")

            return ToolExecutionResult(
                success=False,
                error=str(e),
                error_code=MCPErrorCode.INTERNAL_ERROR.value,
                latency_ms=latency_ms,
                request_id=request_id,
            )

    async def list_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 MCP 도구 목록.

        Returns:
            MCP 매핑된 도구 목록
        """
        if not self._initialized:
            await self.initialize()

        tools = []
        for tool_id, mapping in self._tool_mappings.items():
            server_config = self._manager.get_server_config(mapping["server_id"])
            tools.append({
                "tool_id": tool_id,
                "server_id": mapping["server_id"],
                "mcp_tool_name": mapping["mcp_tool_name"],
                "description": mapping.get("description", ""),
                "credit_cost": mapping.get("credit_cost", 1),
                "server_enabled": server_config.enabled if server_config else False,
            })

        return tools

    async def health_check(self) -> bool:
        """헬스 체크."""
        if not self._initialized:
            return False

        try:
            # Check at least one server is healthy
            health = await self._manager.health_check_all()
            return any(health.values())
        except Exception:
            return False

    def register_mapping(
        self,
        tool_id: str,
        server_id: str,
        mcp_tool_name: str,
        description: str = "",
        credit_cost: int = 1,
    ) -> None:
        """도구 매핑 등록.

        Args:
            tool_id: Vivid 내부 도구 ID
            server_id: MCP 서버 ID
            mcp_tool_name: MCP 도구 이름
            description: 도구 설명
            credit_cost: 크레딧 비용
        """
        self._tool_mappings[tool_id] = {
            "server_id": server_id,
            "mcp_tool_name": mcp_tool_name,
            "description": description,
            "credit_cost": credit_cost,
        }

    def register_output_transformer(
        self,
        tool_id: str,
        transformer: Callable[[Any, Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        """출력 변환기 등록.

        Args:
            tool_id: 도구 ID
            transformer: (mcp_result, original_inputs) → outputs
        """
        self._output_transformers[tool_id] = transformer

    def _transform_inputs(
        self,
        tool_id: str,
        inputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """입력 변환 (Vivid → MCP).

        대부분의 경우 직접 전달하지만,
        특수한 변환이 필요한 경우 여기서 처리.
        """
        # Tool-specific transformations
        if tool_id == "web_search":
            # Tavily expects 'query' field
            return {
                "query": inputs.get("query") or inputs.get("search_term", ""),
                "max_results": inputs.get("max_results", 10),
                "search_depth": inputs.get("depth", "basic"),
            }
        elif tool_id == "semantic_search":
            # Qdrant format
            return {
                "collection_name": inputs.get("collection", "default"),
                "query_vector": inputs.get("vector") or inputs.get("embedding"),
                "limit": inputs.get("limit", 10),
                "filter": inputs.get("filter"),
            }

        # Default: pass through
        return inputs

    def _transform_outputs(
        self,
        tool_id: str,
        mcp_result: Any,
        original_inputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """출력 변환 (MCP → Vivid).

        MCP 결과를 DAG 노드 출력 형식으로 변환.
        """
        # Custom transformer registered?
        if tool_id in self._output_transformers:
            return self._output_transformers[tool_id](mcp_result, original_inputs)

        # Default transformations
        if isinstance(mcp_result, dict):
            return mcp_result
        elif isinstance(mcp_result, str):
            return {"result": mcp_result}
        elif isinstance(mcp_result, list):
            return {"items": mcp_result}
        else:
            return {"result": mcp_result}

    def _register_default_transformers(self) -> None:
        """기본 출력 변환기 등록."""

        # Tavily search transformer
        def tavily_search_transformer(result: Any, inputs: Dict) -> Dict[str, Any]:
            if isinstance(result, dict):
                return {
                    "search_results": result.get("results", []),
                    "answer": result.get("answer"),
                    "query": result.get("query", inputs.get("query")),
                    "images": result.get("images", []),
                }
            return {"search_results": [], "raw": result}

        self._output_transformers["web_search"] = tavily_search_transformer

        # Tavily extract transformer
        def tavily_extract_transformer(result: Any, inputs: Dict) -> Dict[str, Any]:
            if isinstance(result, dict):
                return {
                    "content": result.get("content", ""),
                    "url": result.get("url", inputs.get("url")),
                    "title": result.get("title"),
                    "metadata": result.get("metadata", {}),
                }
            return {"content": str(result)}

        self._output_transformers["web_extract"] = tavily_extract_transformer

        # Qdrant search transformer
        def qdrant_search_transformer(result: Any, inputs: Dict) -> Dict[str, Any]:
            if isinstance(result, list):
                return {
                    "matches": [
                        {
                            "id": m.get("id"),
                            "score": m.get("score"),
                            "payload": m.get("payload", {}),
                        }
                        for m in result
                    ],
                    "count": len(result),
                }
            return {"matches": [], "raw": result}

        self._output_transformers["semantic_search"] = qdrant_search_transformer


# =============================================================================
# Native Tool Executor (Dimension Adapter)
# =============================================================================

class NativeToolExecutor:
    """Native 도구 실행기.

    Dimension Adapter를 통한 직접 도구 실행.
    MCP를 거치지 않는 내부 도구용.
    """

    def __init__(self):
        self._tool_handlers: Dict[str, Callable] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """실행기 초기화."""
        if self._initialized:
            return

        # Register dimension adapter handlers
        self._register_dimension_handlers()
        self._initialized = True

    async def execute(
        self,
        tool_id: str,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ToolExecutionResult:
        """Native 도구 실행."""
        if not self._initialized:
            await self.initialize()

        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        handler = self._tool_handlers.get(tool_id)
        if not handler:
            return ToolExecutionResult(
                success=False,
                error=f"No native handler for tool: {tool_id}",
                error_code=MCPErrorCode.TOOL_NOT_FOUND.value,
                request_id=request_id,
            )

        try:
            outputs = await handler(inputs, context)
            latency_ms = (time.time() - start_time) * 1000

            return ToolExecutionResult(
                success=True,
                outputs=outputs,
                latency_ms=latency_ms,
                credit_cost=self._get_credit_cost(tool_id),
                request_id=request_id,
                metadata={"executor": "native"},
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.exception(f"Native execution error: {e}")

            return ToolExecutionResult(
                success=False,
                error=str(e),
                error_code=MCPErrorCode.INTERNAL_ERROR.value,
                latency_ms=latency_ms,
                request_id=request_id,
            )

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Native 도구 목록."""
        return [
            {"tool_id": tool_id, "type": "native"}
            for tool_id in self._tool_handlers.keys()
        ]

    async def health_check(self) -> bool:
        """헬스 체크."""
        return self._initialized

    def register_handler(
        self,
        tool_id: str,
        handler: Callable[[Dict[str, Any], Dict[str, Any]], Any],
    ) -> None:
        """Native 핸들러 등록."""
        self._tool_handlers[tool_id] = handler

    def _register_dimension_handlers(self) -> None:
        """Dimension Adapter 핸들러 등록."""
        # Lazy import to avoid circular dependencies
        try:
            from app.dimension_adapter import (
                run_reference_decode,
                run_storyboard_generate,
                run_image_generate,
                run_aesthetic_direct,
            )

            async def reference_handler(inputs: Dict, context: Dict) -> Dict:
                result = await run_reference_decode(
                    video_url=inputs.get("video_url"),
                    analysis_depth=inputs.get("analysis_depth", "detailed"),
                    auteur_key=inputs.get("auteur_key"),
                )
                return result

            async def storyboard_handler(inputs: Dict, context: Dict) -> Dict:
                result = await run_storyboard_generate(
                    concept=inputs.get("concept"),
                    style=inputs.get("style", "cinematic"),
                    duration_seconds=inputs.get("duration_seconds", 30),
                    auteur_key=inputs.get("auteur_key"),
                )
                return result

            self._tool_handlers["reference_decode_native"] = reference_handler
            self._tool_handlers["storyboard_generate_native"] = storyboard_handler

        except ImportError as e:
            logger.warning(f"Could not import dimension_adapter: {e}")

    def _get_credit_cost(self, tool_id: str) -> int:
        """도구 크레딧 비용."""
        costs = {
            "reference_decode_native": 10,
            "storyboard_generate_native": 15,
            "image_generate_native": 20,
            "aesthetic_direct_native": 5,
        }
        return costs.get(tool_id, settings.MCP_CREDIT_COST_DEFAULT)


# =============================================================================
# Hybrid Tool Executor
# =============================================================================

class HybridToolExecutor:
    """하이브리드 도구 실행기 (Native + MCP).

    도구 ID에 따라 Native 또는 MCP 실행기로 라우팅합니다.

    Routing Rules:
        1. MCP 매핑이 있는 도구 → MCPToolExecutor
        2. Native 핸들러가 있는 도구 → NativeToolExecutor
        3. 둘 다 있으면 → 설정에 따라 (기본: MCP 우선)

    Example:
        >>> executor = await create_hybrid_executor()
        >>> result = await executor.execute("web_search", {"query": "..."}, {})
    """

    def __init__(
        self,
        mcp_executor: Optional[MCPToolExecutor] = None,
        native_executor: Optional[NativeToolExecutor] = None,
        prefer_mcp: bool = True,
    ):
        """Initialize hybrid executor.

        Args:
            mcp_executor: MCP 실행기
            native_executor: Native 실행기
            prefer_mcp: MCP 우선 여부 (둘 다 가능할 때)
        """
        self._mcp = mcp_executor or MCPToolExecutor()
        self._native = native_executor or NativeToolExecutor()
        self._prefer_mcp = prefer_mcp
        self._initialized = False

    async def initialize(self) -> None:
        """실행기 초기화."""
        if self._initialized:
            return

        await asyncio.gather(
            self._mcp.initialize(),
            self._native.initialize(),
        )
        self._initialized = True
        logger.info("HybridToolExecutor initialized")

    async def shutdown(self) -> None:
        """실행기 종료."""
        await self._mcp.shutdown()
        self._initialized = False

    async def execute(
        self,
        tool_id: str,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ToolExecutionResult:
        """도구 실행 (자동 라우팅).

        Args:
            tool_id: 도구 ID
            inputs: 입력 데이터
            context: 실행 컨텍스트

        Returns:
            ToolExecutionResult
        """
        if not self._initialized:
            await self.initialize()

        # 라우팅 결정
        executor, routing_reason = self._route(tool_id)

        logger.debug(
            f"Routing tool '{tool_id}' to {executor.__class__.__name__} "
            f"({routing_reason})"
        )

        # 실행
        result = await executor.execute(tool_id, inputs, context)

        # 라우팅 정보 추가
        result.metadata["routing"] = routing_reason

        return result

    async def list_tools(self) -> List[Dict[str, Any]]:
        """모든 사용 가능한 도구 목록."""
        if not self._initialized:
            await self.initialize()

        mcp_tools = await self._mcp.list_tools()
        native_tools = await self._native.list_tools()

        # Merge with deduplication
        all_tools = {}
        for tool in native_tools:
            all_tools[tool["tool_id"]] = {**tool, "source": "native"}
        for tool in mcp_tools:
            tool_id = tool["tool_id"]
            if tool_id in all_tools:
                # Both available
                all_tools[tool_id]["source"] = "hybrid"
                all_tools[tool_id]["mcp_info"] = tool
            else:
                all_tools[tool_id] = {**tool, "source": "mcp"}

        return list(all_tools.values())

    async def health_check(self) -> Dict[str, bool]:
        """헬스 체크."""
        mcp_healthy = await self._mcp.health_check()
        native_healthy = await self._native.health_check()

        return {
            "mcp": mcp_healthy,
            "native": native_healthy,
            "overall": mcp_healthy or native_healthy,
        }

    def _route(
        self,
        tool_id: str,
    ) -> Tuple[ToolExecutorProtocol, str]:
        """실행기 라우팅.

        Returns:
            (executor, reason)
        """
        has_mcp = tool_id in self._mcp._tool_mappings
        has_native = tool_id in self._native._tool_handlers

        if has_mcp and has_native:
            if self._prefer_mcp:
                return self._mcp, "mcp_preferred"
            else:
                return self._native, "native_preferred"
        elif has_mcp:
            return self._mcp, "mcp_only"
        elif has_native:
            return self._native, "native_only"
        else:
            # Default to MCP (will return not found error)
            return self._mcp, "no_mapping_mcp_fallback"


# =============================================================================
# DAG Workflow Integration
# =============================================================================

class DAGToolExecutorAdapter:
    """DAG Workflow용 도구 실행기 어댑터.

    HITLWorkflowExecutor와 호환되는 인터페이스 제공.
    """

    def __init__(self, hybrid_executor: HybridToolExecutor):
        self._executor = hybrid_executor

    async def execute(
        self,
        tool_id: str,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Workflow 실행기 호환 인터페이스.

        Returns:
            출력 딕셔너리 (성공 시) 또는 예외 발생 (실패 시)
        """
        result = await self._executor.execute(tool_id, inputs, context)

        if result.success:
            return result.outputs
        else:
            raise RuntimeError(
                f"Tool execution failed: {result.error} "
                f"(code: {result.error_code})"
            )


# =============================================================================
# Factory Functions
# =============================================================================

async def create_mcp_executor(
    use_gateway: bool = True,
) -> MCPToolExecutor:
    """MCP 도구 실행기 생성.

    Args:
        use_gateway: Gateway 사용 여부

    Returns:
        초기화된 MCPToolExecutor
    """
    executor = MCPToolExecutor(use_gateway=use_gateway)
    await executor.initialize()
    return executor


async def create_hybrid_executor(
    prefer_mcp: bool = True,
) -> HybridToolExecutor:
    """하이브리드 도구 실행기 생성.

    Args:
        prefer_mcp: MCP 우선 여부

    Returns:
        초기화된 HybridToolExecutor
    """
    executor = HybridToolExecutor(prefer_mcp=prefer_mcp)
    await executor.initialize()
    return executor


async def create_dag_executor() -> DAGToolExecutorAdapter:
    """DAG Workflow용 실행기 생성.

    Returns:
        HITLWorkflowExecutor 호환 실행기
    """
    hybrid = await create_hybrid_executor()
    return DAGToolExecutorAdapter(hybrid)


# =============================================================================
# Singleton Management
# =============================================================================

_hybrid_executor: Optional[HybridToolExecutor] = None


async def get_hybrid_executor() -> HybridToolExecutor:
    """HybridToolExecutor 싱글톤.

    Returns:
        HybridToolExecutor 인스턴스
    """
    global _hybrid_executor
    if _hybrid_executor is None:
        _hybrid_executor = await create_hybrid_executor()
    return _hybrid_executor


def reset_hybrid_executor() -> None:
    """HybridToolExecutor 리셋 (테스트용)."""
    global _hybrid_executor
    _hybrid_executor = None
