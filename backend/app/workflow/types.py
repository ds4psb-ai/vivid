"""Dynamic DAG Type Definitions (P0 2026).

도구 역량 및 DAG 구조 타입 정의.

Reference:
    - Temporal DAG: https://temporal.io/code-exchange/temporalgraph-graph-based-orchestration
    - LangGraph: https://docs.langchain.com/oss/python/langchain

Usage:
    from app.workflow.types import (
        DataType,
        PortSpec,
        ToolCapability,
        DAGNode,
        DAGEdge,
        ExecutableDAG,
    )
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

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
