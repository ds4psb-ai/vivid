"""Dynamic DAG Builder (P0 2026).

의도 기반 동적 DAG 생성 - 도구 선택, 의존성 추론, 위상 정렬.

Reference:
    - Temporal Graph: https://temporal.io/code-exchange/temporalgraph-graph-based-orchestration
    - LangGraph: https://docs.langchain.com/oss/python/langchain
    - NetworkX: https://networkx.org/documentation/stable/

Usage:
    from app.workflow import DynamicDAGBuilder, create_dag_builder

    builder = create_dag_builder()
    dag = await builder.build_from_intent(
        intent="스토리보드 생성",
        selected_tools=["story_architect", "storyboard_generator"],
        initial_inputs={"concept": "SF 영화 오프닝"},
    )

    # DAG 정보
    print(dag.execution_order)  # 위상 정렬된 실행 순서
    print(dag.human_review_points)  # HITL 체크포인트
    print(dag.estimated_credits)  # 예상 크레딧
"""
from __future__ import annotations

import logging
import uuid
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple

from app.workflow.registry import ToolCapabilityRegistry, get_tool_registry
from app.workflow.types import (
    DataType,
    DAGEdge,
    DAGNode,
    ExecutableDAG,
    ToolCapability,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================

class DAGBuildError(Exception):
    """DAG 빌드 중 발생하는 예외."""
    pass


class CyclicDependencyError(DAGBuildError):
    """순환 의존성 발견 시 예외."""
    pass


class MissingDependencyError(DAGBuildError):
    """필수 의존성 누락 시 예외."""
    pass


class IncompatibleToolsError(DAGBuildError):
    """비호환 도구 조합 시 예외."""
    pass


# =============================================================================
# Dynamic DAG Builder
# =============================================================================

class DynamicDAGBuilder:
    """동적 DAG 빌더.

    의도와 선택된 도구를 기반으로 실행 가능한 DAG를 생성합니다.

    Features:
        - can_consume/can_provide 기반 자동 의존성 추론
        - 위상 정렬로 실행 순서 결정
        - HITL 체크포인트 자동 식별
        - 순환 의존성 감지
        - 비호환 도구 조합 검증

    Example:
        >>> builder = DynamicDAGBuilder(registry)
        >>> dag = await builder.build_from_intent(
        ...     intent="스토리보드 생성",
        ...     selected_tools=["story_architect", "storyboard_generator"],
        ...     initial_inputs={"concept": "SF 영화 오프닝"},
        ... )
    """

    def __init__(
        self,
        registry: Optional[ToolCapabilityRegistry] = None,
        auto_add_dependencies: bool = True,
    ) -> None:
        """Initialize DAG builder.

        Args:
            registry: 도구 레지스트리 (None이면 전역 레지스트리 사용)
            auto_add_dependencies: 필수 선행 도구 자동 추가 여부
        """
        self._registry = registry or get_tool_registry()
        self._auto_add_dependencies = auto_add_dependencies

    async def build_from_intent(
        self,
        intent: str,
        selected_tools: List[str],
        initial_inputs: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> ExecutableDAG:
        """의도로부터 DAG 생성.

        Args:
            intent: 사용자 의도 (예: "스토리보드 생성", "레퍼런스 분석")
            selected_tools: 선택된 도구 ID 목록
            initial_inputs: 초기 입력 데이터
            user_context: 사용자 컨텍스트 (auteur_key 등)

        Returns:
            실행 가능한 DAG

        Raises:
            DAGBuildError: DAG 빌드 실패 시
        """
        dag_id = f"dag_{uuid.uuid4().hex[:12]}"
        initial_inputs = initial_inputs or {}
        user_context = user_context or {}

        logger.info(
            f"[DAGBuilder] Building DAG | id={dag_id} | "
            f"intent='{intent}' | tools={selected_tools}"
        )

        # 1. 도구 역량 조회 및 검증
        tools = self._resolve_tools(selected_tools)

        # 2. 필수 선행 도구 자동 추가
        if self._auto_add_dependencies:
            tools = self._add_required_dependencies(tools)

        # 3. 비호환 도구 검증
        self._validate_compatibility(tools)

        # 4. 노드 생성
        nodes = self._create_nodes(tools, initial_inputs, user_context)

        # 5. 엣지 추론 (can_provide → can_consume 매칭)
        edges = self._infer_edges(nodes, tools)

        # 6. 위상 정렬
        execution_order = self._topological_sort(nodes, edges)

        # 7. HITL 체크포인트 식별
        hitl_points = [
            node_id for node_id, node in nodes.items()
            if node.requires_human_review
        ]

        # 8. 비용 추정
        estimated_credits = sum(t.credit_cost for t in tools)
        estimated_latency = self._estimate_latency(tools, execution_order)

        dag = ExecutableDAG(
            dag_id=dag_id,
            nodes=nodes,
            edges=edges,
            execution_order=execution_order,
            human_review_points=hitl_points,
            estimated_credits=estimated_credits,
            estimated_latency_ms=estimated_latency,
            metadata={
                "intent": intent,
                "selected_tools": selected_tools,
                "user_context": user_context,
            },
        )

        logger.info(
            f"[DAGBuilder] DAG built | id={dag_id} | "
            f"nodes={len(nodes)} | edges={len(edges)} | "
            f"hitl_points={len(hitl_points)} | credits={estimated_credits}"
        )

        return dag

    def build_from_intent_sync(
        self,
        intent: str,
        selected_tools: List[str],
        initial_inputs: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> ExecutableDAG:
        """의도로부터 DAG 생성 (동기 버전).

        Synchronous version for non-async contexts.
        """
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.build_from_intent(intent, selected_tools, initial_inputs, user_context)
        )

    # -------------------------------------------------------------------------
    # Tool Resolution
    # -------------------------------------------------------------------------

    def _resolve_tools(self, tool_ids: List[str]) -> List[ToolCapability]:
        """도구 ID를 역량 객체로 변환.

        Args:
            tool_ids: 도구 ID 목록

        Returns:
            ToolCapability 목록

        Raises:
            DAGBuildError: 존재하지 않는 도구 ID
        """
        tools: List[ToolCapability] = []
        missing: List[str] = []

        for tool_id in tool_ids:
            tool = self._registry.get(tool_id)
            if tool is None:
                missing.append(tool_id)
            elif not tool.enabled:
                logger.warning(f"[DAGBuilder] Tool '{tool_id}' is disabled, skipping")
            else:
                tools.append(tool)

        if missing:
            raise DAGBuildError(f"Unknown tools: {missing}")

        return tools

    def _add_required_dependencies(
        self,
        tools: List[ToolCapability],
    ) -> List[ToolCapability]:
        """필수 선행 도구 자동 추가.

        Args:
            tools: 선택된 도구 목록

        Returns:
            선행 도구가 추가된 목록
        """
        existing_ids = {t.tool_id for t in tools}
        added: List[ToolCapability] = []

        for tool in tools:
            for required_id in tool.required_prior_tools:
                if required_id not in existing_ids:
                    required_tool = self._registry.get(required_id)
                    if required_tool and required_tool.enabled:
                        added.append(required_tool)
                        existing_ids.add(required_id)
                        logger.debug(
                            f"[DAGBuilder] Auto-added required tool: {required_id}"
                        )

        return added + tools

    def _validate_compatibility(self, tools: List[ToolCapability]) -> None:
        """비호환 도구 조합 검증.

        Args:
            tools: 도구 목록

        Raises:
            IncompatibleToolsError: 비호환 도구 발견 시
        """
        tool_ids = {t.tool_id for t in tools}

        for tool in tools:
            for incompatible_id in tool.incompatible_with:
                if incompatible_id in tool_ids:
                    raise IncompatibleToolsError(
                        f"Tool '{tool.tool_id}' is incompatible with '{incompatible_id}'"
                    )

    # -------------------------------------------------------------------------
    # Node Creation
    # -------------------------------------------------------------------------

    def _create_nodes(
        self,
        tools: List[ToolCapability],
        initial_inputs: Dict[str, Any],
        user_context: Dict[str, Any],
    ) -> Dict[str, DAGNode]:
        """DAG 노드 생성.

        Args:
            tools: 도구 목록
            initial_inputs: 초기 입력
            user_context: 사용자 컨텍스트

        Returns:
            노드 ID → DAGNode 매핑
        """
        nodes: Dict[str, DAGNode] = {}

        for tool in tools:
            node_id = f"node_{tool.tool_id}_{uuid.uuid4().hex[:6]}"

            # 초기 입력에서 해당 도구가 소비할 수 있는 데이터 추출
            node_inputs: Dict[str, Any] = {}

            for port in tool.input_ports:
                port_name = port.name
                # 초기 입력에서 직접 매칭
                if port_name in initial_inputs:
                    node_inputs[port_name] = initial_inputs[port_name]
                # 타입 기반 매칭 (fallback)
                elif port.data_type.value in initial_inputs:
                    node_inputs[port_name] = initial_inputs[port.data_type.value]

            # 사용자 컨텍스트 추가
            if DataType.USER_CONTEXT in tool.can_consume:
                node_inputs["user_context"] = user_context

            node = DAGNode(
                node_id=node_id,
                tool_id=tool.tool_id,
                inputs=node_inputs,
                dependencies=set(),
                requires_human_review=tool.requires_human_review,
                status="pending",
            )

            nodes[node_id] = node

        return nodes

    # -------------------------------------------------------------------------
    # Edge Inference
    # -------------------------------------------------------------------------

    def _infer_edges(
        self,
        nodes: Dict[str, DAGNode],
        tools: List[ToolCapability],
    ) -> List[DAGEdge]:
        """can_provide → can_consume 매칭으로 엣지 추론.

        Args:
            nodes: 노드 맵
            tools: 도구 목록

        Returns:
            DAGEdge 목록
        """
        edges: List[DAGEdge] = []
        tool_map = {t.tool_id: t for t in tools}

        # 노드 ID → 도구 ID 매핑
        node_to_tool: Dict[str, str] = {
            node_id: node.tool_id for node_id, node in nodes.items()
        }

        # 도구 ID → 노드 ID 매핑 (역방향)
        tool_to_node: Dict[str, str] = {
            node.tool_id: node_id for node_id, node in nodes.items()
        }

        # 데이터 타입별 provider 노드 찾기
        providers_by_type: Dict[DataType, List[str]] = defaultdict(list)
        for node_id, node in nodes.items():
            tool = tool_map.get(node.tool_id)
            if tool:
                for dtype in tool.can_provide:
                    providers_by_type[dtype].append(node_id)

        # 각 노드의 입력에 대해 provider 연결
        for node_id, node in nodes.items():
            tool = tool_map.get(node.tool_id)
            if not tool:
                continue

            for port in tool.input_ports:
                dtype = port.data_type
                # 이미 초기 입력으로 충족되면 skip
                if port.name in node.inputs:
                    continue

                # provider 노드 찾기
                for provider_node_id in providers_by_type.get(dtype, []):
                    # 자기 자신은 제외
                    if provider_node_id == node_id:
                        continue

                    provider_tool_id = node_to_tool[provider_node_id]
                    provider_tool = tool_map.get(provider_tool_id)
                    if not provider_tool:
                        continue

                    # 출력 포트 찾기
                    for out_port in provider_tool.output_ports:
                        if out_port.data_type == dtype:
                            edge = DAGEdge(
                                from_node_id=provider_node_id,
                                from_port=out_port.name,
                                to_node_id=node_id,
                                to_port=port.name,
                                data_type=dtype,
                            )
                            edges.append(edge)

                            # 의존성 추가
                            node.dependencies.add(provider_node_id)
                            break

        # required_prior_tools 기반 의존성 추가
        for node_id, node in nodes.items():
            tool = tool_map.get(node.tool_id)
            if not tool:
                continue

            for prior_tool_id in tool.required_prior_tools:
                prior_node_id = tool_to_node.get(prior_tool_id)
                if prior_node_id and prior_node_id != node_id:
                    node.dependencies.add(prior_node_id)

        return edges

    # -------------------------------------------------------------------------
    # Topological Sort (Kahn's Algorithm)
    # -------------------------------------------------------------------------

    def _topological_sort(
        self,
        nodes: Dict[str, DAGNode],
        edges: List[DAGEdge],
    ) -> List[str]:
        """위상 정렬 (Kahn's Algorithm).

        Args:
            nodes: 노드 맵
            edges: 엣지 목록

        Returns:
            위상 정렬된 노드 ID 목록

        Raises:
            CyclicDependencyError: 순환 의존성 발견 시
        """
        # In-degree 계산
        in_degree: Dict[str, int] = {node_id: 0 for node_id in nodes}
        adjacency: Dict[str, List[str]] = defaultdict(list)

        for edge in edges:
            in_degree[edge.to_node_id] += 1
            adjacency[edge.from_node_id].append(edge.to_node_id)

        # 의존성 기반 추가 (edges에 없는 경우)
        for node_id, node in nodes.items():
            for dep_id in node.dependencies:
                if dep_id in nodes and edge_not_exists(edges, dep_id, node_id):
                    in_degree[node_id] += 1
                    adjacency[dep_id].append(node_id)

        # In-degree가 0인 노드로 시작
        queue: deque[str] = deque()
        for node_id, degree in in_degree.items():
            if degree == 0:
                queue.append(node_id)

        result: List[str] = []

        while queue:
            node_id = queue.popleft()
            result.append(node_id)

            for next_id in adjacency[node_id]:
                in_degree[next_id] -= 1
                if in_degree[next_id] == 0:
                    queue.append(next_id)

        # 순환 의존성 체크
        if len(result) != len(nodes):
            remaining = [nid for nid in nodes if nid not in result]
            raise CyclicDependencyError(
                f"Cyclic dependency detected. Nodes not sortable: {remaining}"
            )

        return result

    # -------------------------------------------------------------------------
    # Latency Estimation
    # -------------------------------------------------------------------------

    def _estimate_latency(
        self,
        tools: List[ToolCapability],
        execution_order: List[str],
    ) -> int:
        """실행 시간 추정.

        병렬 실행 가능한 노드는 동시에 실행된다고 가정.
        직렬 의존성이 있는 경로의 최대 지연 시간 계산.

        Simplified: 현재는 단순 합산 (보수적 추정)

        Args:
            tools: 도구 목록
            execution_order: 실행 순서

        Returns:
            예상 실행 시간 (ms)
        """
        # 단순 합산 (직렬 실행 가정)
        # TODO: Critical path 분석으로 병렬 실행 고려
        return sum(t.avg_latency_ms for t in tools)


# =============================================================================
# Helper Functions
# =============================================================================

def edge_not_exists(edges: List[DAGEdge], from_id: str, to_id: str) -> bool:
    """엣지 존재 여부 확인."""
    return not any(
        e.from_node_id == from_id and e.to_node_id == to_id
        for e in edges
    )


def create_dag_builder(
    registry: Optional[ToolCapabilityRegistry] = None,
    auto_add_dependencies: bool = True,
) -> DynamicDAGBuilder:
    """DAG 빌더 팩토리 함수.

    Args:
        registry: 도구 레지스트리 (None이면 전역 사용)
        auto_add_dependencies: 필수 선행 도구 자동 추가

    Returns:
        DynamicDAGBuilder 인스턴스
    """
    return DynamicDAGBuilder(
        registry=registry,
        auto_add_dependencies=auto_add_dependencies,
    )


# =============================================================================
# Intent Analyzer (LLM-based Tool Selection) - Future Extension
# =============================================================================

class IntentAnalyzer:
    """의도 분석기 (LLM 기반 도구 선택).

    Phase 3에서 구현 예정:
    - 자연어 의도에서 최적 도구 조합 추천
    - 사용자 히스토리 기반 개인화
    - 컨텍스트 기반 자동 파라미터 추론

    Usage:
        analyzer = IntentAnalyzer(registry)
        recommended_tools = await analyzer.analyze(
            intent="SF 영화 오프닝 스토리보드 만들기",
            user_context={"preferred_style": "nolan"},
        )
    """

    def __init__(
        self,
        registry: Optional[ToolCapabilityRegistry] = None,
    ) -> None:
        """Initialize analyzer."""
        self._registry = registry or get_tool_registry()

    async def analyze(
        self,
        intent: str,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """의도 분석 및 도구 추천.

        Args:
            intent: 사용자 의도
            user_context: 사용자 컨텍스트

        Returns:
            추천 도구 ID 목록
        """
        # Phase 3 구현 예정
        # 현재는 키워드 기반 간단한 추천

        intent_lower = intent.lower()
        recommended: Set[str] = set()

        # 키워드 → 도구 매핑
        keyword_map = {
            "스토리보드": ["story_architect", "storyboard_generator"],
            "storyboard": ["story_architect", "storyboard_generator"],
            "레퍼런스": ["reference_decoder"],
            "reference": ["reference_decoder"],
            "분석": ["reference_decoder"],
            "analysis": ["reference_decoder"],
            "이미지": ["prompt_composer", "image_generator"],
            "image": ["prompt_composer", "image_generator"],
            "비디오": ["prompt_composer", "video_generator"],
            "video": ["prompt_composer", "video_generator"],
            "프롬프트": ["prompt_composer"],
            "prompt": ["prompt_composer"],
            "미학": ["aesthetic_director"],
            "aesthetic": ["aesthetic_director"],
        }

        for keyword, tools in keyword_map.items():
            if keyword in intent_lower:
                recommended.update(tools)

        # 기본 도구 (아무것도 매칭되지 않으면)
        if not recommended:
            recommended.add("prompt_composer")

        logger.debug(
            f"[IntentAnalyzer] intent='{intent}' → recommended={list(recommended)}"
        )

        return list(recommended)

    def analyze_sync(
        self,
        intent: str,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """동기 버전."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.analyze(intent, user_context)
        )
