"""Dynamic DAG Type Definitions (P0 2026).

도구 역량 및 DAG 구조 타입 정의.

Reference:
    - Temporal DAG: https://temporal.io/code-exchange/temporalgraph-graph-based-orchestration
    - LangGraph: https://langchain-ai.github.io/langgraph/
    - LangGraph Conditional Edges: https://langchain-ai.github.io/langgraph/concepts/low_level/

Usage:
    from app.workflow.types import (
        DataType,
        PortSpec,
        ToolCapability,
        DAGNode,
        DAGEdge,
        ExecutableDAG,
        # 2026 Extensions
        ConditionalEdge,
        RouterNode,
        WorkflowState,
        RoutingDecision,
    )
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Set, Union

from pydantic import BaseModel, ConfigDict, Field


class DataType(str, Enum):
    """데이터 타입 (도구 간 호환성 체크용).

    도구의 입력/출력 포트 타입을 정의합니다.
    can_consume/can_provide 매칭에 사용됩니다.
    """
    # Basic types
    TEXT = "text"
    STRUCTURED_JSON = "structured_json"

    # Media types
    IMAGE_URL = "image_url"
    VIDEO_URL = "video_url"
    AUDIO_URL = "audio_url"

    # Creative types
    STYLE_HINT = "style_hint"
    STORY_STRUCTURE = "story_structure"
    SCENE_LIST = "scene_list"
    STORYBOARD = "storyboard"
    PROMPT = "prompt"

    # Analysis types
    ANALYSIS_RESULT = "analysis_result"
    REFERENCE_DATA = "reference_data"
    COLOR_PALETTE = "color_palette"
    COMPOSITION_GUIDE = "composition_guide"

    # Meta types
    USER_CONTEXT = "user_context"
    RAG_CONTEXT = "rag_context"


class PortSpec(BaseModel):
    """입출력 포트 명세.

    Attributes:
        name: 포트 이름 (예: "video_url", "style_hint")
        data_type: 데이터 타입
        required: 필수 여부
        description: 포트 설명
        default_value: 기본값 (선택적)

    Example:
        >>> input_port = PortSpec(
        ...     name="video_url",
        ...     data_type=DataType.VIDEO_URL,
        ...     required=False,
        ...     description="분석할 동영상 URL",
        ... )
    """
    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, max_length=64)
    data_type: DataType
    required: bool = Field(default=True)
    description: str = Field(default="", max_length=200)
    default_value: Optional[Any] = Field(default=None)


class ToolCapability(BaseModel):
    """도구 역량 명세.

    도구의 입출력 스키마와 의미적 역량을 정의합니다.
    DAG 빌더가 도구 간 연결을 추론할 때 사용됩니다.

    Attributes:
        tool_id: 도구 고유 ID (예: "reference_decoder", "story_architect")
        display_name: UI 표시명
        dimension: 차원 코드 ("1D", "2D", "3D", "4D", "AD", "STORY", etc.)
        description: 도구 설명
        input_ports: 입력 포트 목록
        output_ports: 출력 포트 목록
        can_consume: 입력으로 받을 수 있는 데이터 타입
        can_provide: 출력으로 제공할 수 있는 데이터 타입
        credit_cost: 크레딧 비용
        avg_latency_ms: 평균 실행 시간 (ms)
        requires_human_review: HITL 체크포인트 필요 여부
        required_prior_tools: 필수 선행 도구 ID
        incompatible_with: 함께 사용 불가한 도구 ID

    Example:
        >>> capability = ToolCapability(
        ...     tool_id="reference_decoder",
        ...     display_name="레퍼런스 해석기",
        ...     dimension="4D",
        ...     input_ports=[
        ...         PortSpec(name="video_url", data_type=DataType.VIDEO_URL, required=False),
        ...         PortSpec(name="video_description", data_type=DataType.TEXT, required=True),
        ...     ],
        ...     output_ports=[
        ...         PortSpec(name="analysis", data_type=DataType.ANALYSIS_RESULT),
        ...         PortSpec(name="style_hint", data_type=DataType.STYLE_HINT),
        ...     ],
        ...     can_consume={DataType.VIDEO_URL, DataType.TEXT},
        ...     can_provide={DataType.ANALYSIS_RESULT, DataType.STYLE_HINT},
        ...     credit_cost=10,
        ...     requires_human_review=True,
        ... )
    """
    model_config = ConfigDict(
        frozen=False,
        extra="forbid",
    )

    # Identity
    tool_id: str = Field(..., min_length=1, max_length=64)
    display_name: str = Field(..., min_length=1, max_length=100)
    dimension: str = Field(..., min_length=1, max_length=16)
    description: str = Field(default="", max_length=500)

    # I/O Schemas
    input_ports: List[PortSpec] = Field(default_factory=list)
    output_ports: List[PortSpec] = Field(default_factory=list)

    # Semantic Capabilities (for dependency inference)
    can_consume: Set[DataType] = Field(default_factory=set)
    can_provide: Set[DataType] = Field(default_factory=set)

    # Execution Properties
    credit_cost: int = Field(default=5, ge=0)
    avg_latency_ms: int = Field(default=3000, ge=0)
    requires_human_review: bool = Field(default=False)

    # Constraints
    required_prior_tools: List[str] = Field(default_factory=list)
    incompatible_with: List[str] = Field(default_factory=list)

    # Metadata
    enabled: bool = Field(default=True)
    tags: List[str] = Field(default_factory=list)


@dataclass
class DAGNode:
    """DAG 노드.

    실행 가능한 DAG의 개별 노드를 나타냅니다.

    Attributes:
        node_id: 노드 고유 ID (UUID)
        tool_id: 도구 ID
        inputs: 노드 입력 데이터
        dependencies: 의존하는 노드 ID 집합
        requires_human_review: HITL 체크포인트 필요 여부
        status: 노드 상태 ("pending", "running", "completed", "failed", "paused")
    """
    node_id: str
    tool_id: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)
    requires_human_review: bool = False
    status: str = "pending"


@dataclass
class DAGEdge:
    """DAG 엣지 (데이터 흐름).

    노드 간 데이터 흐름을 나타냅니다.

    Attributes:
        from_node_id: 소스 노드 ID
        from_port: 소스 포트 이름
        to_node_id: 타겟 노드 ID
        to_port: 타겟 포트 이름
        data_type: 전달되는 데이터 타입
    """
    from_node_id: str
    from_port: str
    to_node_id: str
    to_port: str
    data_type: Optional[DataType] = None


@dataclass
class ExecutableDAG:
    """실행 가능한 DAG.

    DynamicDAGBuilder가 생성하는 최종 DAG 구조입니다.

    Attributes:
        dag_id: DAG 고유 ID (UUID)
        nodes: 노드 ID -> DAGNode 매핑
        edges: 엣지 목록
        execution_order: 위상 정렬된 노드 ID 목록
        human_review_points: HITL 체크포인트 노드 ID 목록
        estimated_credits: 예상 총 크레딧
        estimated_latency_ms: 예상 총 실행 시간 (ms)
        metadata: 추가 메타데이터

    Example:
        >>> dag = ExecutableDAG(
        ...     dag_id="dag_123",
        ...     nodes={"node_1": node1, "node_2": node2},
        ...     edges=[edge1, edge2],
        ...     execution_order=["node_1", "node_2"],
        ...     human_review_points=["node_1"],
        ...     estimated_credits=20,
        ...     estimated_latency_ms=8000,
        ... )
    """
    dag_id: str
    nodes: Dict[str, DAGNode]
    edges: List[DAGEdge]
    execution_order: List[str]
    human_review_points: List[str]
    estimated_credits: int = 0
    estimated_latency_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_node(self, node_id: str) -> Optional[DAGNode]:
        """노드 조회."""
        return self.nodes.get(node_id)

    def get_successors(self, node_id: str) -> List[str]:
        """후속 노드 ID 목록."""
        return [
            edge.to_node_id
            for edge in self.edges
            if edge.from_node_id == node_id
        ]

    def get_predecessors(self, node_id: str) -> List[str]:
        """선행 노드 ID 목록."""
        return [
            edge.from_node_id
            for edge in self.edges
            if edge.to_node_id == node_id
        ]

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환 (직렬화용)."""
        return {
            "dag_id": self.dag_id,
            "nodes": {
                node_id: {
                    "node_id": node.node_id,
                    "tool_id": node.tool_id,
                    "inputs": node.inputs,
                    "dependencies": list(node.dependencies),
                    "requires_human_review": node.requires_human_review,
                    "status": node.status,
                }
                for node_id, node in self.nodes.items()
            },
            "edges": [
                {
                    "from_node_id": e.from_node_id,
                    "from_port": e.from_port,
                    "to_node_id": e.to_node_id,
                    "to_port": e.to_port,
                    "data_type": e.data_type.value if e.data_type else None,
                }
                for e in self.edges
            ],
            "execution_order": self.execution_order,
            "human_review_points": self.human_review_points,
            "estimated_credits": self.estimated_credits,
            "estimated_latency_ms": self.estimated_latency_ms,
            "metadata": self.metadata,
        }


# =============================================================================
# 2026 Extensions: LangGraph-style Conditional Routing
# =============================================================================


class WorkflowState(BaseModel):
    """워크플로우 상태 (LangGraph StateGraph 패턴).

    노드 간 전달되는 상태 객체입니다.
    각 노드는 상태를 읽고 업데이트하며, 조건부 라우팅에 활용됩니다.

    Attributes:
        query: 원본 사용자 쿼리
        intent_type: 분류된 의도 타입
        selected_tools: 선택된 도구 목록
        current_step: 현재 실행 단계
        accumulated_outputs: 누적된 출력 데이터
        user_context: 사용자 컨텍스트 (auteur_key 등)
        error: 에러 정보 (있는 경우)

    Example:
        >>> state = WorkflowState(
        ...     query="강주노 스타일로 3분 MV 만들어줘",
        ...     intent_type="full_production",
        ...     user_context={"auteur_key": "bong"},
        ... )
    """
    model_config = ConfigDict(extra="allow")

    # Core fields
    query: str = Field(default="")
    intent_type: str = Field(default="unknown")
    selected_tools: List[str] = Field(default_factory=list)
    current_step: str = Field(default="start")

    # Accumulated data
    accumulated_outputs: Dict[str, Any] = Field(default_factory=dict)
    user_context: Dict[str, Any] = Field(default_factory=dict)

    # Routing info
    route: str = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Error handling
    error: Optional[str] = Field(default=None)
    retry_count: int = Field(default=0)


class RoutingDecision(BaseModel):
    """라우팅 결정 결과.

    IntentAnalyzerV2 또는 RouterNode가 반환하는 라우팅 결정입니다.

    Attributes:
        target_node: 다음 실행할 노드 ID
        confidence: 결정 신뢰도 (0-1)
        reasoning: 결정 이유 (디버깅용)
        alternatives: 대안 노드들 (폴백용)
    """
    model_config = ConfigDict(frozen=True)

    target_node: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reasoning: str = Field(default="")
    alternatives: List[str] = Field(default_factory=list)


# Routing function type alias
RoutingFunction = Callable[[WorkflowState], str]


@dataclass
class ConditionalEdge:
    """조건부 엣지 - 상태 기반 동적 라우팅.

    LangGraph의 add_conditional_edges 패턴을 구현합니다.
    상태에 따라 다음 노드를 동적으로 결정합니다.

    Attributes:
        from_node_id: 소스 노드 ID
        condition: 상태를 받아 라우트 키를 반환하는 함수
        route_map: 라우트 키 → 타겟 노드 ID 매핑
        default_route: 매핑되지 않을 때 기본 라우트

    Example:
        >>> def classify_intent(state: WorkflowState) -> str:
        ...     if "분석" in state.query:
        ...         return "analysis"
        ...     elif "생성" in state.query:
        ...         return "generation"
        ...     return "general"
        ...
        >>> edge = ConditionalEdge(
        ...     from_node_id="intent_classifier",
        ...     condition=classify_intent,
        ...     route_map={
        ...         "analysis": "reference_decoder",
        ...         "generation": "visual_realizer",
        ...         "general": "prompt_alchemy",
        ...     },
        ...     default_route="prompt_alchemy",
        ... )
    """
    from_node_id: str
    condition: RoutingFunction
    route_map: Dict[str, str]  # condition_result → target_node_id
    default_route: str = "end"

    def resolve(self, state: WorkflowState) -> str:
        """상태를 기반으로 다음 노드 결정.

        Args:
            state: 현재 워크플로우 상태

        Returns:
            다음 실행할 노드 ID
        """
        route_key = self.condition(state)
        return self.route_map.get(route_key, self.default_route)


@dataclass
class RouterNode(DAGNode):
    """LLM 기반 라우팅 노드.

    복잡한 의도 분석이 필요할 때 LLM을 활용하여 라우팅합니다.
    기존 키워드 기반 IntentAnalyzer를 LLM으로 업그레이드합니다.

    Attributes:
        routing_prompt: LLM에 전달할 라우팅 프롬프트 템플릿
        possible_routes: 가능한 라우트 목록
        llm_model: 사용할 LLM 모델 (기본: gemini-2.5-flash)
        fallback_route: LLM 실패 시 폴백 라우트
        max_retries: 최대 재시도 횟수

    Example:
        >>> router = RouterNode(
        ...     node_id="smart_router",
        ...     tool_id="llm_router",
        ...     routing_prompt='''
        ...     사용자 의도를 분석하고 적절한 도구를 선택하세요.
        ...     가능한 라우트: {possible_routes}
        ...     사용자 쿼리: {query}
        ...     ''',
        ...     possible_routes=["reference", "story", "image", "video"],
        ...     llm_model="gemini-2.5-flash",
        ... )
    """
    routing_prompt: str = ""
    possible_routes: List[str] = field(default_factory=list)
    llm_model: str = "gemini-2.5-flash"
    fallback_route: str = "general"
    max_retries: int = 2

    def __post_init__(self) -> None:
        """tool_id 기본값 설정."""
        if not self.tool_id:
            self.tool_id = "llm_router"


class QueryComplexity(str, Enum):
    """쿼리 복잡도 레벨 (Compound Orchestration용).

    복잡도에 따라 오케스트레이션 전략이 달라집니다.
    """
    SIMPLE = "simple"          # 단일 도구로 해결 가능
    MODERATE = "moderate"      # 2-3개 도구 순차 실행
    COMPLEX = "complex"        # 다중 도구 + 조건부 분기
    ITERATIVE = "iterative"    # 사용자 피드백 기반 반복 (HITL)


class OrchestrationPattern(str, Enum):
    """오케스트레이션 패턴.

    Compound Orchestration에서 사용하는 실행 패턴입니다.
    """
    DIRECT = "direct"          # 단일 도구 직접 호출
    LINEAR = "linear"          # 순차 DAG 실행
    PARALLEL = "parallel"      # 병렬 실행 (독립 노드)
    CONDITIONAL = "conditional"  # 조건부 분기 DAG
    HITL_LOOP = "hitl_loop"    # Human-in-the-Loop 반복


@dataclass
class CompoundOrchestrationPlan:
    """복합 오케스트레이션 계획.

    IntentAnalyzerV2가 생성하는 실행 계획입니다.

    Attributes:
        complexity: 쿼리 복잡도
        pattern: 오케스트레이션 패턴
        primary_tools: 메인 도구 목록 (순서대로)
        optional_tools: 선택적 도구 (조건 충족 시)
        conditional_branches: 조건부 분기 정보
        estimated_steps: 예상 단계 수
        confidence: 계획 신뢰도
    """
    complexity: QueryComplexity
    pattern: OrchestrationPattern
    primary_tools: List[str]
    optional_tools: List[str] = field(default_factory=list)
    conditional_branches: Dict[str, List[str]] = field(default_factory=dict)
    estimated_steps: int = 1
    confidence: float = 1.0
    reasoning: str = ""


@dataclass
class ExecutableDAGV2(ExecutableDAG):
    """확장된 실행 가능 DAG (조건부 엣지 지원).

    LangGraph 스타일의 조건부 라우팅을 지원합니다.

    Attributes:
        conditional_edges: 조건부 엣지 목록
        router_nodes: LLM 라우팅 노드 ID 목록
        orchestration_plan: 오케스트레이션 계획 (있는 경우)
    """
    conditional_edges: List[ConditionalEdge] = field(default_factory=list)
    router_nodes: List[str] = field(default_factory=list)
    orchestration_plan: Optional[CompoundOrchestrationPlan] = None

    def get_conditional_edge(self, from_node_id: str) -> Optional[ConditionalEdge]:
        """노드의 조건부 엣지 조회."""
        for edge in self.conditional_edges:
            if edge.from_node_id == from_node_id:
                return edge
        return None

    def is_router_node(self, node_id: str) -> bool:
        """라우터 노드 여부 확인."""
        return node_id in self.router_nodes

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환 (조건부 엣지 포함)."""
        base_dict = super().to_dict()
        base_dict["conditional_edges"] = [
            {
                "from_node_id": ce.from_node_id,
                "route_map": ce.route_map,
                "default_route": ce.default_route,
                # condition은 직렬화 불가 - 생략
            }
            for ce in self.conditional_edges
        ]
        base_dict["router_nodes"] = self.router_nodes
        if self.orchestration_plan:
            base_dict["orchestration_plan"] = {
                "complexity": self.orchestration_plan.complexity.value,
                "pattern": self.orchestration_plan.pattern.value,
                "primary_tools": self.orchestration_plan.primary_tools,
                "optional_tools": self.orchestration_plan.optional_tools,
                "estimated_steps": self.orchestration_plan.estimated_steps,
                "confidence": self.orchestration_plan.confidence,
            }
        return base_dict
