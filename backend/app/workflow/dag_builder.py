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
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from app.workflow.registry import ToolCapabilityRegistry, get_tool_registry
from app.workflow.types import (
    DataType,
    DAGEdge,
    DAGNode,
    ExecutableDAG,
    ToolCapability,
    # 2026 Extensions
    ConditionalEdge,
    RouterNode,
    WorkflowState,
    RoutingDecision,
    QueryComplexity,
    OrchestrationPattern,
    CompoundOrchestrationPlan,
    ExecutableDAGV2,
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
            user_context={"preferred_style": "epoch"},
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


# =============================================================================
# Intent Analyzer V2 (LLM-based, 2026 Extension)
# =============================================================================

@dataclass
class ToolRecommendation:
    """도구 추천 결과."""
    primary_tools: List[str]
    optional_tools: List[str]
    workflow_type: str  # "linear" | "parallel" | "conditional"
    confidence: float
    reasoning: str
    orchestration_plan: Optional[CompoundOrchestrationPlan] = None


class IntentAnalyzerV2:
    """LLM 기반 의도 분석기 V2.

    2026 업그레이드:
    - 키워드 기반 → LLM 기반 분석
    - Compound Orchestration 지원
    - Query Complexity 자동 판별
    - Conditional Routing 결정

    Usage:
        analyzer = IntentAnalyzerV2(registry)
        recommendation = await analyzer.analyze(
            intent="SF 영화 오프닝을 위한 스토리보드와 레퍼런스 분석",
            user_context={"preferred_style": "epoch"},
            available_tools=["story_architect", "reference_decoder", ...],
        )
        # recommendation.primary_tools
        # recommendation.orchestration_plan
    """

    # 복잡도 판별 키워드
    COMPLEXITY_SIGNALS = {
        QueryComplexity.SIMPLE: [
            "단순", "simple", "기본", "하나", "quick", "single",
        ],
        QueryComplexity.MODERATE: [
            "분석", "analyze", "생성", "generate", "만들기",
            "그리고", "and", "with",
        ],
        QueryComplexity.COMPLEX: [
            "여러", "multiple", "모두", "all", "비교", "compare",
            "통합", "integrate", "병렬", "parallel",
        ],
        QueryComplexity.ITERATIVE: [
            "반복", "iterate", "수정", "refine", "피드백", "feedback",
            "개선", "improve", "최적화", "optimize",
        ],
    }

    # 워크플로우 패턴 매핑
    PATTERN_FOR_COMPLEXITY = {
        QueryComplexity.SIMPLE: OrchestrationPattern.DIRECT,
        QueryComplexity.MODERATE: OrchestrationPattern.LINEAR,
        QueryComplexity.COMPLEX: OrchestrationPattern.PARALLEL,
        QueryComplexity.ITERATIVE: OrchestrationPattern.HITL_LOOP,
    }

    # 도구 의존성 그래프 (도구 → 선행 도구)
    TOOL_DEPENDENCIES = {
        "storyboard_generator": ["story_architect"],
        "image_generator": ["prompt_composer"],
        "video_generator": ["prompt_composer"],
        "aesthetic_director": ["reference_decoder"],
    }

    # 도구 병렬 실행 가능 그룹
    PARALLELIZABLE_GROUPS = [
        {"reference_decoder", "story_architect"},
        {"image_generator", "sound_crafter"},
        {"prompt_composer", "aesthetic_director"},
    ]

    def __init__(
        self,
        registry: Optional[ToolCapabilityRegistry] = None,
        llm_model: str = "gemini-2.5-flash",
        use_llm: bool = True,
    ) -> None:
        """Initialize V2 analyzer.

        Args:
            registry: 도구 레지스트리
            llm_model: LLM 모델 (gemini-2.5-flash or gemini-2.5-pro)
            use_llm: LLM 사용 여부 (False면 휴리스틱만 사용)
        """
        self._registry = registry or get_tool_registry()
        self._llm_model = llm_model
        self._use_llm = use_llm
        self._fallback_analyzer = IntentAnalyzer(registry)

    async def analyze(
        self,
        intent: str,
        user_context: Optional[Dict[str, Any]] = None,
        available_tools: Optional[List[str]] = None,
    ) -> ToolRecommendation:
        """의도 분석 및 도구/오케스트레이션 추천.

        Args:
            intent: 사용자 의도
            user_context: 사용자 컨텍스트
            available_tools: 사용 가능한 도구 ID 목록 (None이면 전체)

        Returns:
            ToolRecommendation with orchestration plan
        """
        user_context = user_context or {}
        available_tools = available_tools or self._get_all_enabled_tools()

        logger.info(
            f"[IntentAnalyzerV2] Analyzing | intent='{intent[:50]}...' | "
            f"available_tools={len(available_tools)}"
        )

        try:
            # 1. 복잡도 판별
            complexity = self._determine_complexity(intent)

            # 2. LLM 기반 도구 선택 (또는 휴리스틱 fallback)
            if self._use_llm:
                primary, optional = await self._llm_select_tools(
                    intent, available_tools, user_context
                )
            else:
                primary = await self._fallback_analyzer.analyze(intent, user_context)
                optional = []

            # 3. 오케스트레이션 패턴 결정
            pattern = self._determine_pattern(complexity, primary)

            # 4. 조건부 브랜치 추론
            conditional_branches = self._infer_conditional_branches(
                intent, primary, optional
            )

            # 5. CompoundOrchestrationPlan 생성
            orchestration_plan = CompoundOrchestrationPlan(
                complexity=complexity,
                pattern=pattern,
                primary_tools=primary,
                optional_tools=optional,
                conditional_branches=conditional_branches,
                estimated_steps=self._estimate_steps(primary, pattern),
                confidence=self._calculate_confidence(intent, primary),
                reasoning=self._generate_reasoning(intent, complexity, pattern, primary),
            )

            # 6. 워크플로우 타입 결정
            workflow_type = self._pattern_to_workflow_type(pattern)

            recommendation = ToolRecommendation(
                primary_tools=primary,
                optional_tools=optional,
                workflow_type=workflow_type,
                confidence=orchestration_plan.confidence,
                reasoning=orchestration_plan.reasoning,
                orchestration_plan=orchestration_plan,
            )

            logger.info(
                f"[IntentAnalyzerV2] Result | complexity={complexity.value} | "
                f"pattern={pattern.value} | primary={primary} | "
                f"confidence={recommendation.confidence:.2f}"
            )

            return recommendation

        except Exception as e:
            logger.warning(
                f"[IntentAnalyzerV2] Error, falling back | error={e}"
            )
            # Fallback to V1
            fallback_tools = await self._fallback_analyzer.analyze(intent, user_context)
            return ToolRecommendation(
                primary_tools=fallback_tools,
                optional_tools=[],
                workflow_type="linear",
                confidence=0.5,
                reasoning=f"Fallback to V1 due to error: {e}",
                orchestration_plan=None,
            )

    # -------------------------------------------------------------------------
    # Complexity Analysis
    # -------------------------------------------------------------------------

    def _determine_complexity(self, intent: str) -> QueryComplexity:
        """쿼리 복잡도 판별.

        키워드 기반 휴리스틱 + 문장 구조 분석.
        """
        intent_lower = intent.lower()
        scores: Dict[QueryComplexity, int] = {c: 0 for c in QueryComplexity}

        # 키워드 매칭
        for complexity, keywords in self.COMPLEXITY_SIGNALS.items():
            for keyword in keywords:
                if keyword in intent_lower:
                    scores[complexity] += 1

        # 문장 구조 분석
        # 여러 동사/목적어 = 복잡
        connector_count = sum(
            1 for c in ["그리고", "또한", "and", ",", ";"]
            if c in intent_lower
        )
        if connector_count >= 2:
            scores[QueryComplexity.COMPLEX] += 2
        elif connector_count == 1:
            scores[QueryComplexity.MODERATE] += 1

        # 질문 형태 분석
        if any(q in intent_lower for q in ["어떻게", "how", "?", "방법"]):
            scores[QueryComplexity.MODERATE] += 1

        # 최고 점수 복잡도 반환
        max_complexity = max(scores, key=lambda c: scores[c])

        # 점수가 모두 0이면 MODERATE 기본값
        if scores[max_complexity] == 0:
            return QueryComplexity.MODERATE

        return max_complexity

    # -------------------------------------------------------------------------
    # LLM-based Tool Selection
    # -------------------------------------------------------------------------

    async def _llm_select_tools(
        self,
        intent: str,
        available_tools: List[str],
        user_context: Dict[str, Any],
    ) -> Tuple[List[str], List[str]]:
        """LLM 기반 도구 선택.

        TODO: 실제 LLM 호출 구현 (현재는 향상된 휴리스틱)
        """
        # Phase 1: 향상된 휴리스틱 (LLM 호출 없이)
        # Phase 2에서 실제 Gemini 호출로 교체

        intent_lower = intent.lower()

        # 향상된 키워드-도구 매핑
        tool_scores: Dict[str, float] = defaultdict(float)

        # 의도별 도구 점수 부여
        intent_tool_map = {
            # 스토리 관련
            "스토리": {"story_architect": 1.0, "storyboard_generator": 0.8},
            "story": {"story_architect": 1.0, "storyboard_generator": 0.8},
            "narrative": {"story_architect": 1.0},
            "시나리오": {"story_architect": 1.0},

            # 스토리보드 관련
            "스토리보드": {"storyboard_generator": 1.0, "story_architect": 0.7},
            "storyboard": {"storyboard_generator": 1.0, "story_architect": 0.7},
            "콘티": {"storyboard_generator": 1.0},

            # 레퍼런스/분석 관련
            "레퍼런스": {"reference_decoder": 1.0},
            "reference": {"reference_decoder": 1.0},
            "분석": {"reference_decoder": 0.9, "aesthetic_director": 0.6},
            "analyze": {"reference_decoder": 0.9},

            # 이미지 관련
            "이미지": {"prompt_composer": 0.9, "image_generator": 1.0},
            "image": {"prompt_composer": 0.9, "image_generator": 1.0},
            "그림": {"image_generator": 1.0, "prompt_composer": 0.8},
            "시각": {"image_generator": 0.9, "visual_realizer": 1.0},

            # 비디오 관련
            "비디오": {"video_generator": 1.0, "prompt_composer": 0.7},
            "video": {"video_generator": 1.0, "prompt_composer": 0.7},
            "영상": {"video_generator": 1.0, "video_maker": 0.9},
            "VEO": {"veo_generator": 1.0},

            # 사운드 관련
            "사운드": {"sound_crafter": 1.0},
            "sound": {"sound_crafter": 1.0},
            "음악": {"sound_crafter": 1.0},
            "music": {"sound_crafter": 1.0},
            "오디오": {"sound_crafter": 1.0},

            # 미학/스타일 관련
            "미학": {"aesthetic_director": 1.0},
            "aesthetic": {"aesthetic_director": 1.0},
            "스타일": {"aesthetic_director": 0.9, "prompt_composer": 0.6},
            "style": {"aesthetic_director": 0.9},

            # 프롬프트 관련
            "프롬프트": {"prompt_composer": 1.0},
            "prompt": {"prompt_composer": 1.0},
        }

        for keyword, tools in intent_tool_map.items():
            if keyword in intent_lower:
                for tool_id, score in tools.items():
                    if tool_id in available_tools:
                        tool_scores[tool_id] += score

        # 사용자 컨텍스트 기반 보정
        if user_context.get("auteur_key"):
            tool_scores["reference_decoder"] += 0.3
            tool_scores["aesthetic_director"] += 0.3

        # 의존성 도구 자동 추가
        for tool_id in list(tool_scores.keys()):
            if tool_id in self.TOOL_DEPENDENCIES:
                for dep in self.TOOL_DEPENDENCIES[tool_id]:
                    if dep in available_tools:
                        tool_scores[dep] = max(tool_scores[dep], 0.5)

        # 점수 기준 정렬
        sorted_tools = sorted(
            tool_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Primary: 점수 0.7 이상, Optional: 0.4~0.7
        primary = [t for t, s in sorted_tools if s >= 0.7]
        optional = [t for t, s in sorted_tools if 0.4 <= s < 0.7]

        # 기본 도구 (아무것도 선택되지 않으면)
        if not primary:
            primary = ["prompt_composer"]

        return primary, optional

    # -------------------------------------------------------------------------
    # Pattern & Workflow Determination
    # -------------------------------------------------------------------------

    def _determine_pattern(
        self,
        complexity: QueryComplexity,
        tools: List[str],
    ) -> OrchestrationPattern:
        """오케스트레이션 패턴 결정.

        복잡도 + 도구 조합 기반.
        """
        base_pattern = self.PATTERN_FOR_COMPLEXITY.get(
            complexity,
            OrchestrationPattern.LINEAR
        )

        # 도구 수에 따른 조정
        if len(tools) == 1:
            return OrchestrationPattern.DIRECT

        # 병렬 실행 가능한 도구가 2개 이상이면 PARALLEL
        parallel_count = 0
        tool_set = set(tools)
        for group in self.PARALLELIZABLE_GROUPS:
            if len(tool_set & group) >= 2:
                parallel_count += 1

        if parallel_count >= 1 and complexity in [
            QueryComplexity.COMPLEX,
            QueryComplexity.MODERATE,
        ]:
            return OrchestrationPattern.PARALLEL

        # 조건부 분기가 필요한 경우
        conditional_keywords = ["만약", "if", "조건", "선택", "또는", "or"]
        # (intent는 여기서 접근 불가 - pattern 결정 시점에서는 도구만 참조)

        return base_pattern

    def _pattern_to_workflow_type(self, pattern: OrchestrationPattern) -> str:
        """패턴을 워크플로우 타입 문자열로 변환."""
        mapping = {
            OrchestrationPattern.DIRECT: "linear",
            OrchestrationPattern.LINEAR: "linear",
            OrchestrationPattern.PARALLEL: "parallel",
            OrchestrationPattern.CONDITIONAL: "conditional",
            OrchestrationPattern.HITL_LOOP: "conditional",
        }
        return mapping.get(pattern, "linear")

    # -------------------------------------------------------------------------
    # Conditional Branch Inference
    # -------------------------------------------------------------------------

    def _infer_conditional_branches(
        self,
        intent: str,
        primary_tools: List[str],
        optional_tools: List[str],
    ) -> Dict[str, List[str]]:
        """조건부 브랜치 추론.

        의도에서 분기 조건을 추출하여 조건부 실행 경로 생성.
        """
        branches: Dict[str, List[str]] = {}
        intent_lower = intent.lower()

        # "만약 X이면 Y" 패턴 감지
        if "만약" in intent_lower or "if" in intent_lower:
            branches["condition_true"] = primary_tools
            branches["condition_false"] = optional_tools or ["prompt_composer"]

        # "A 또는 B" 패턴 감지
        if "또는" in intent_lower or " or " in intent_lower:
            if len(primary_tools) >= 2:
                mid = len(primary_tools) // 2
                branches["option_a"] = primary_tools[:mid]
                branches["option_b"] = primary_tools[mid:]

        # 품질 기반 분기 (QC 관련)
        if any(t in primary_tools for t in ["quality_director", "quality_checker"]):
            branches["quality_pass"] = [t for t in primary_tools if "quality" not in t]
            branches["quality_fail"] = ["prompt_composer"]  # 재생성

        return branches

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def _get_all_enabled_tools(self) -> List[str]:
        """활성화된 모든 도구 ID 반환."""
        all_tools = self._registry.get_all()
        return [t.tool_id for t in all_tools if t.enabled]

    def _estimate_steps(
        self,
        tools: List[str],
        pattern: OrchestrationPattern,
    ) -> int:
        """예상 실행 단계 수."""
        if pattern == OrchestrationPattern.DIRECT:
            return 1
        elif pattern == OrchestrationPattern.PARALLEL:
            # 병렬 실행은 depth 기준
            return max(2, len(tools) // 2)
        elif pattern == OrchestrationPattern.HITL_LOOP:
            return len(tools) * 2  # 반복 고려
        else:
            return len(tools)

    def _calculate_confidence(
        self,
        intent: str,
        tools: List[str],
    ) -> float:
        """추천 신뢰도 계산."""
        # 기본 신뢰도
        confidence = 0.7

        # 도구 수가 적절하면 신뢰도 증가
        if 1 <= len(tools) <= 4:
            confidence += 0.1

        # 의도가 명확하면 신뢰도 증가
        clear_intent_keywords = [
            "만들기", "생성", "분석", "create", "generate", "analyze"
        ]
        if any(k in intent.lower() for k in clear_intent_keywords):
            confidence += 0.1

        return min(confidence, 1.0)

    def _generate_reasoning(
        self,
        intent: str,
        complexity: QueryComplexity,
        pattern: OrchestrationPattern,
        tools: List[str],
    ) -> str:
        """추천 이유 생성."""
        return (
            f"Query complexity: {complexity.value}. "
            f"Selected orchestration pattern: {pattern.value}. "
            f"Recommended {len(tools)} tool(s): {', '.join(tools)}."
        )

    # -------------------------------------------------------------------------
    # DAG V2 Builder Integration
    # -------------------------------------------------------------------------

    async def build_dag_v2(
        self,
        intent: str,
        user_context: Optional[Dict[str, Any]] = None,
        initial_inputs: Optional[Dict[str, Any]] = None,
    ) -> ExecutableDAGV2:
        """의도에서 ExecutableDAGV2 직접 생성.

        IntentAnalyzerV2 + DynamicDAGBuilder 통합.

        Args:
            intent: 사용자 의도
            user_context: 사용자 컨텍스트
            initial_inputs: 초기 입력

        Returns:
            ExecutableDAGV2 with conditional edges and orchestration plan
        """
        # 1. 의도 분석
        recommendation = await self.analyze(
            intent=intent,
            user_context=user_context,
        )

        # 2. 기본 DAG 빌드
        builder = DynamicDAGBuilder(self._registry)
        base_dag = await builder.build_from_intent(
            intent=intent,
            selected_tools=recommendation.primary_tools + recommendation.optional_tools,
            initial_inputs=initial_inputs,
            user_context=user_context,
        )

        # 3. Conditional Edges 생성
        conditional_edges = self._create_conditional_edges(
            recommendation, base_dag
        )

        # 4. Router Nodes 식별
        router_node_ids = [
            node_id for node_id, node in base_dag.nodes.items()
            if isinstance(node, RouterNode)
        ]

        # 5. DAG V2 생성
        dag_v2 = ExecutableDAGV2(
            dag_id=base_dag.dag_id,
            nodes=base_dag.nodes,
            edges=base_dag.edges,
            execution_order=base_dag.execution_order,
            human_review_points=base_dag.human_review_points,
            estimated_credits=base_dag.estimated_credits,
            estimated_latency_ms=base_dag.estimated_latency_ms,
            metadata=base_dag.metadata,
            conditional_edges=conditional_edges,
            router_nodes=router_node_ids,
            orchestration_plan=recommendation.orchestration_plan,
        )

        logger.info(
            f"[IntentAnalyzerV2] Built DAG V2 | id={dag_v2.dag_id} | "
            f"conditional_edges={len(conditional_edges)} | "
            f"pattern={recommendation.orchestration_plan.pattern.value if recommendation.orchestration_plan else 'none'}"
        )

        return dag_v2

    def _create_conditional_edges(
        self,
        recommendation: ToolRecommendation,
        base_dag: ExecutableDAG,
    ) -> List[ConditionalEdge]:
        """조건부 엣지 생성."""
        conditional_edges: List[ConditionalEdge] = []

        if not recommendation.orchestration_plan:
            return conditional_edges

        branches = recommendation.orchestration_plan.conditional_branches

        if not branches:
            return conditional_edges

        # 첫 번째 노드에서 분기하는 조건부 엣지 생성
        if base_dag.execution_order:
            first_node_id = base_dag.execution_order[0]

            # 분기 조건에 따른 라우트 맵 생성
            route_map: Dict[str, str] = {}
            for branch_name, tool_ids in branches.items():
                # 해당 도구의 노드 ID 찾기
                for node_id, node in base_dag.nodes.items():
                    if node.tool_id in tool_ids:
                        route_map[branch_name] = node_id
                        break

            if route_map:
                # 기본 라우팅 함수 (상태 기반)
                def default_router(state: WorkflowState) -> str:
                    # confidence 기반 라우팅
                    if state.confidence >= 0.8:
                        return "condition_true"
                    elif state.confidence >= 0.5:
                        return "option_a"
                    else:
                        return "condition_false"

                edge = ConditionalEdge(
                    from_node_id=first_node_id,
                    condition=default_router,
                    route_map=route_map,
                    default_route=base_dag.execution_order[1] if len(base_dag.execution_order) > 1 else "end",
                )
                conditional_edges.append(edge)

        return conditional_edges


# =============================================================================
# Factory Functions (V2)
# =============================================================================

def create_intent_analyzer_v2(
    registry: Optional[ToolCapabilityRegistry] = None,
    use_llm: bool = True,
) -> IntentAnalyzerV2:
    """IntentAnalyzerV2 팩토리 함수.

    Args:
        registry: 도구 레지스트리
        use_llm: LLM 사용 여부

    Returns:
        IntentAnalyzerV2 인스턴스
    """
    return IntentAnalyzerV2(
        registry=registry,
        use_llm=use_llm,
    )


async def build_dag_from_intent_v2(
    intent: str,
    user_context: Optional[Dict[str, Any]] = None,
    initial_inputs: Optional[Dict[str, Any]] = None,
) -> ExecutableDAGV2:
    """의도에서 DAG V2 생성 (편의 함수).

    Args:
        intent: 사용자 의도
        user_context: 사용자 컨텍스트
        initial_inputs: 초기 입력

    Returns:
        ExecutableDAGV2
    """
    analyzer = create_intent_analyzer_v2()
    return await analyzer.build_dag_v2(
        intent=intent,
        user_context=user_context,
        initial_inputs=initial_inputs,
    )
