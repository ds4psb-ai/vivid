"""Dynamic Workflow Module (P0 2026).

동적 DAG 기반 워크플로우 계획 및 실행.

Components:
    - types: 타입 정의 (DataType, ToolCapability, DAGNode, etc.)
    - registry: 도구 역량 레지스트리
    - dag_builder: 동적 DAG 빌더, IntentAnalyzerV2
    - executor: HITL 워크플로우 실행기 (V1/V2)

2026 확장 (V2):
    - ConditionalEdge: 상태 기반 동적 라우팅
    - RouterNode: LLM 기반 라우팅 노드
    - WorkflowState: LangGraph StateGraph 패턴
    - IntentAnalyzerV2: LLM 기반 의도 분석
    - HITLWorkflowExecutorV2: 조건부 실행 지원

Usage:
    from app.workflow import (
        # Types
        DataType,
        ToolCapability,
        DAGNode,
        ExecutableDAG,
        # V2 Types
        ConditionalEdge,
        RouterNode,
        WorkflowState,
        ExecutableDAGV2,
        # Registry
        get_tool_registry,
        # Builder V2
        IntentAnalyzerV2,
        build_dag_from_intent_v2,
        # Executor V2
        HITLWorkflowExecutorV2,
        create_executor_v2,
    )

    # V2: LLM 기반 의도 분석 + 조건부 실행
    dag_v2 = await build_dag_from_intent_v2(
        intent="SF 영화 스토리보드 생성, 만약 레퍼런스가 있으면 분석도",
        user_context={"auteur_key": "epoch"},
    )
    executor = await create_executor_v2(db)
    execution_id = await executor.start_workflow_v2(dag_v2, user_id)
"""
from app.workflow.types import (
    # Core Types
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
    QueryComplexity,
    OrchestrationPattern,
    CompoundOrchestrationPlan,
    ExecutableDAGV2,
)
from app.workflow.registry import (
    ToolCapabilityRegistry,
    get_tool_registry,
    reset_tool_registry,
)
from app.workflow.dag_builder import (
    # V1
    DynamicDAGBuilder,
    IntentAnalyzer,
    create_dag_builder,
    # V2
    IntentAnalyzerV2,
    ToolRecommendation,
    create_intent_analyzer_v2,
    build_dag_from_intent_v2,
    # Exceptions
    DAGBuildError,
    CyclicDependencyError,
    MissingDependencyError,
    IncompatibleToolsError,
)
from app.workflow.executor import (
    # V1
    CheckpointService,
    HITLWorkflowExecutor,
    MockToolExecutor,
    ToolExecutor,
    create_executor,
    # V2
    HITLWorkflowExecutorV2,
    create_executor_v2,
    # Exceptions
    WorkflowExecutionError,
    CheckpointNotFoundError,
    WorkflowNotPausedError,
    InvalidCheckpointActionError,
)

__all__ = [
    # Core Types
    "DataType",
    "PortSpec",
    "ToolCapability",
    "DAGNode",
    "DAGEdge",
    "ExecutableDAG",
    # 2026 Extension Types
    "ConditionalEdge",
    "RouterNode",
    "WorkflowState",
    "RoutingDecision",
    "QueryComplexity",
    "OrchestrationPattern",
    "CompoundOrchestrationPlan",
    "ExecutableDAGV2",
    # Registry
    "ToolCapabilityRegistry",
    "get_tool_registry",
    "reset_tool_registry",
    # Builder V1
    "DynamicDAGBuilder",
    "IntentAnalyzer",
    "create_dag_builder",
    # Builder V2
    "IntentAnalyzerV2",
    "ToolRecommendation",
    "create_intent_analyzer_v2",
    "build_dag_from_intent_v2",
    # Executor V1
    "CheckpointService",
    "HITLWorkflowExecutor",
    "MockToolExecutor",
    "ToolExecutor",
    "create_executor",
    # Executor V2
    "HITLWorkflowExecutorV2",
    "create_executor_v2",
    # Exceptions
    "DAGBuildError",
    "CyclicDependencyError",
    "MissingDependencyError",
    "IncompatibleToolsError",
    "WorkflowExecutionError",
    "CheckpointNotFoundError",
    "WorkflowNotPausedError",
    "InvalidCheckpointActionError",
]
