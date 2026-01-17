"""Dynamic Workflow Module (P0 2026).

동적 DAG 기반 워크플로우 계획 및 실행.

Components:
    - types: 타입 정의 (DataType, ToolCapability, DAGNode, etc.)
    - registry: 도구 역량 레지스트리
    - dag_builder: 동적 DAG 빌더
    - executor: HITL 워크플로우 실행기 (Phase 3)

Usage:
    from app.workflow import (
        # Types
        DataType,
        ToolCapability,
        DAGNode,
        ExecutableDAG,
        # Registry
        get_tool_registry,
        # Builder
        DynamicDAGBuilder,
    )

    # Get registry with pre-registered tools
    registry = get_tool_registry()

    # Build DAG from intent
    builder = DynamicDAGBuilder(registry)
    dag = await builder.build_from_intent(
        intent="스토리보드 생성",
        selected_tools=["story_architect", "storyboard_generator"],
        initial_inputs={"concept": "SF 영화 오프닝"},
    )
"""
from app.workflow.types import (
    DataType,
    PortSpec,
    ToolCapability,
    DAGNode,
    DAGEdge,
    ExecutableDAG,
)
from app.workflow.registry import (
    ToolCapabilityRegistry,
    get_tool_registry,
    reset_tool_registry,
)
from app.workflow.dag_builder import (
    DynamicDAGBuilder,
    IntentAnalyzer,
    create_dag_builder,
    DAGBuildError,
    CyclicDependencyError,
    MissingDependencyError,
    IncompatibleToolsError,
)
from app.workflow.executor import (
    CheckpointService,
    HITLWorkflowExecutor,
    MockToolExecutor,
    ToolExecutor,
    create_executor,
    WorkflowExecutionError,
    CheckpointNotFoundError,
    WorkflowNotPausedError,
    InvalidCheckpointActionError,
)

__all__ = [
    # Types
    "DataType",
    "PortSpec",
    "ToolCapability",
    "DAGNode",
    "DAGEdge",
    "ExecutableDAG",
    # Registry
    "ToolCapabilityRegistry",
    "get_tool_registry",
    "reset_tool_registry",
    # Builder
    "DynamicDAGBuilder",
    "IntentAnalyzer",
    "create_dag_builder",
    # Executor
    "CheckpointService",
    "HITLWorkflowExecutor",
    "MockToolExecutor",
    "ToolExecutor",
    "create_executor",
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
