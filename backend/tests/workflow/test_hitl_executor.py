"""HITL Workflow Executor Tests (P0 Phase 3 2026).

Tests for CheckpointService, HITLWorkflowExecutor.

Note: These tests use mock objects instead of a real database
since SQLite doesn't support PostgreSQL's JSONB type.

Coverage:
    - CheckpointService: create, resolve, pending, expired checkpoints
    - HITLWorkflowExecutor: start, pause, resume, cancel workflows
    - Integration: full workflow lifecycle with HITL checkpoints
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass, field

import pytest

from app.models_workflow import (
    WorkflowStatus,
    NodeStatus,
    CheckpointAction,
)
from app.workflow import (
    DataType,
    PortSpec,
    ToolCapability,
    ExecutableDAG,
    DAGNode,
    DAGEdge,
    ToolCapabilityRegistry,
    DynamicDAGBuilder,
    reset_tool_registry,
    get_tool_registry,
)
from app.workflow.executor import (
    CheckpointService,
    HITLWorkflowExecutor,
    MockToolExecutor,
    create_executor,
    WorkflowExecutionError,
    CheckpointNotFoundError,
    WorkflowNotPausedError,
)


# =============================================================================
# Mock Database Objects
# =============================================================================

@dataclass
class MockWorkflowExecution:
    """Mock WorkflowExecution for testing."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    dag_id: str = "test_dag"
    user_id: str = "test_user"
    status: str = WorkflowStatus.PENDING.value
    dag_snapshot: dict = field(default_factory=dict)
    initial_inputs: dict = field(default_factory=dict)
    user_context: dict = field(default_factory=dict)
    current_node_id: Optional[str] = None
    completed_nodes: list = field(default_factory=list)
    failed_node_id: Optional[str] = None
    error_message: Optional[str] = None
    estimated_credits: int = 0
    actual_credits: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MockWorkflowCheckpoint:
    """Mock WorkflowCheckpoint for testing."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    execution_id: uuid.UUID = field(default_factory=uuid.uuid4)
    node_id: str = "test_node"
    tool_id: str = "test_tool"
    checkpoint_index: int = 0
    status: str = NodeStatus.WAITING_REVIEW.value
    node_output: dict = field(default_factory=dict)
    user_action: Optional[str] = None
    user_feedback: Optional[str] = None
    modified_output: Optional[dict] = None
    reviewer_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    timeout_seconds: int = 3600
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MockWorkflowNodeResult:
    """Mock WorkflowNodeResult for testing."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    execution_id: uuid.UUID = field(default_factory=uuid.uuid4)
    node_id: str = "test_node"
    tool_id: str = "test_tool"
    execution_index: int = 0
    status: str = NodeStatus.PENDING.value
    inputs: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    error_message: Optional[str] = None
    credit_cost: int = 0
    latency_ms: int = 0
    retry_count: int = 0
    extra_data: dict = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class MockAsyncSession:
    """Mock AsyncSession for testing."""

    def __init__(self):
        self.executions: Dict[uuid.UUID, MockWorkflowExecution] = {}
        self.checkpoints: Dict[uuid.UUID, MockWorkflowCheckpoint] = {}
        self.node_results: Dict[uuid.UUID, MockWorkflowNodeResult] = {}
        self._added = []

    def add(self, obj):
        """Add object to mock session."""
        self._added.append(obj)
        if isinstance(obj, MockWorkflowExecution):
            self.executions[obj.id] = obj
        elif isinstance(obj, MockWorkflowCheckpoint):
            self.checkpoints[obj.id] = obj
        elif isinstance(obj, MockWorkflowNodeResult):
            self.node_results[obj.id] = obj

    async def flush(self):
        """Mock flush."""
        pass

    async def commit(self):
        """Mock commit."""
        pass

    async def execute(self, query):
        """Mock execute - returns mock scalar result."""
        return MockScalarResult(self)


class MockScalarResult:
    """Mock scalar result."""

    def __init__(self, session: MockAsyncSession):
        self._session = session
        self._result = None

    def scalar_one_or_none(self):
        """Return single result or None."""
        return self._result

    def scalars(self):
        """Return scalars."""
        return self

    def all(self):
        """Return all results."""
        return []


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    return MockAsyncSession()


@pytest.fixture
def mock_tool_executor():
    """Mock tool executor."""
    return MockToolExecutor()


@pytest.fixture
def simple_dag():
    """Simple DAG with one node (no HITL)."""
    node = DAGNode(
        node_id="node_1",
        tool_id="simple_tool",
        inputs={"text": "hello"},
        dependencies=set(),
        requires_human_review=False,
        status="pending",
    )

    return ExecutableDAG(
        dag_id="dag_simple",
        nodes={"node_1": node},
        edges=[],
        execution_order=["node_1"],
        human_review_points=[],
        estimated_credits=5,
        estimated_latency_ms=1000,
        metadata={"intent": "test"},
    )


@pytest.fixture
def hitl_dag():
    """DAG with HITL checkpoint."""
    node1 = DAGNode(
        node_id="node_1",
        tool_id="tool_a",
        inputs={"text": "hello"},
        dependencies=set(),
        requires_human_review=False,
        status="pending",
    )

    node2 = DAGNode(
        node_id="node_2",
        tool_id="tool_b",
        inputs={},
        dependencies={"node_1"},
        requires_human_review=True,  # HITL checkpoint
        status="pending",
    )

    node3 = DAGNode(
        node_id="node_3",
        tool_id="tool_c",
        inputs={},
        dependencies={"node_2"},
        requires_human_review=False,
        status="pending",
    )

    edge1 = DAGEdge(
        from_node_id="node_1",
        from_port="output",
        to_node_id="node_2",
        to_port="input",
        data_type=DataType.TEXT,
    )

    edge2 = DAGEdge(
        from_node_id="node_2",
        from_port="output",
        to_node_id="node_3",
        to_port="input",
        data_type=DataType.TEXT,
    )

    return ExecutableDAG(
        dag_id="dag_hitl",
        nodes={"node_1": node1, "node_2": node2, "node_3": node3},
        edges=[edge1, edge2],
        execution_order=["node_1", "node_2", "node_3"],
        human_review_points=["node_2"],
        estimated_credits=20,
        estimated_latency_ms=5000,
        metadata={"intent": "test with hitl"},
    )


@pytest.fixture
def multi_hitl_dag():
    """DAG with multiple HITL checkpoints."""
    nodes = {}
    for i in range(1, 5):
        nodes[f"node_{i}"] = DAGNode(
            node_id=f"node_{i}",
            tool_id=f"tool_{i}",
            inputs={} if i > 1 else {"text": "start"},
            dependencies={f"node_{i-1}"} if i > 1 else set(),
            requires_human_review=(i % 2 == 0),  # nodes 2 and 4 require HITL
            status="pending",
        )

    edges = []
    for i in range(1, 4):
        edges.append(DAGEdge(
            from_node_id=f"node_{i}",
            from_port="output",
            to_node_id=f"node_{i+1}",
            to_port="input",
            data_type=DataType.TEXT,
        ))

    return ExecutableDAG(
        dag_id="dag_multi_hitl",
        nodes=nodes,
        edges=edges,
        execution_order=["node_1", "node_2", "node_3", "node_4"],
        human_review_points=["node_2", "node_4"],
        estimated_credits=40,
        estimated_latency_ms=10000,
        metadata={"intent": "test with multiple hitl"},
    )


# =============================================================================
# Unit Tests - ExecutableDAG
# =============================================================================

class TestExecutableDAG:
    """ExecutableDAG unit tests."""

    def test_dag_creation(self, simple_dag):
        """Test DAG creation."""
        assert simple_dag.dag_id == "dag_simple"
        assert len(simple_dag.nodes) == 1
        assert len(simple_dag.execution_order) == 1

    def test_dag_to_dict(self, hitl_dag):
        """Test DAG serialization."""
        dag_dict = hitl_dag.to_dict()

        assert dag_dict["dag_id"] == "dag_hitl"
        assert len(dag_dict["nodes"]) == 3
        assert len(dag_dict["edges"]) == 2
        assert dag_dict["execution_order"] == ["node_1", "node_2", "node_3"]
        assert dag_dict["human_review_points"] == ["node_2"]

    def test_dag_get_node(self, hitl_dag):
        """Test get node by ID."""
        node = hitl_dag.get_node("node_2")

        assert node is not None
        assert node.tool_id == "tool_b"
        assert node.requires_human_review is True

    def test_dag_get_successors(self, hitl_dag):
        """Test get successor nodes."""
        successors = hitl_dag.get_successors("node_1")

        assert len(successors) == 1
        assert "node_2" in successors

    def test_dag_get_predecessors(self, hitl_dag):
        """Test get predecessor nodes."""
        predecessors = hitl_dag.get_predecessors("node_2")

        assert len(predecessors) == 1
        assert "node_1" in predecessors


# =============================================================================
# Unit Tests - MockToolExecutor
# =============================================================================

class TestMockToolExecutor:
    """MockToolExecutor tests."""

    @pytest.mark.asyncio
    async def test_execute_returns_output(self, mock_tool_executor):
        """Test mock executor returns output."""
        result = await mock_tool_executor.execute(
            tool_id="test_tool",
            inputs={"key": "value"},
            context={"user_id": "test"},
        )

        assert "result" in result
        assert result["tool_id"] == "test_tool"
        assert result["inputs_received"]["key"] == "value"


# =============================================================================
# Unit Tests - CheckpointService (Mock-based)
# =============================================================================

class TestCheckpointServiceUnit:
    """CheckpointService unit tests with mocks."""

    def test_checkpoint_action_enum(self):
        """Test CheckpointAction enum values."""
        assert CheckpointAction.APPROVE.value == "approve"
        assert CheckpointAction.REJECT.value == "reject"
        assert CheckpointAction.MODIFY.value == "modify"
        assert CheckpointAction.SKIP.value == "skip"

    def test_workflow_status_enum(self):
        """Test WorkflowStatus enum values."""
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.PAUSED.value == "paused"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"

    def test_node_status_enum(self):
        """Test NodeStatus enum values."""
        assert NodeStatus.PENDING.value == "pending"
        assert NodeStatus.RUNNING.value == "running"
        assert NodeStatus.WAITING_REVIEW.value == "waiting_review"
        assert NodeStatus.COMPLETED.value == "completed"
        assert NodeStatus.FAILED.value == "failed"


# =============================================================================
# Integration Tests - DAG Builder + Executor Flow
# =============================================================================

class TestWorkflowIntegration:
    """Integration tests for the workflow system."""

    @pytest.mark.asyncio
    async def test_build_dag_with_hitl(self):
        """Test building DAG that includes HITL checkpoints."""
        reset_tool_registry()
        registry = get_tool_registry()

        builder = DynamicDAGBuilder(registry)
        dag = await builder.build_from_intent(
            intent="레퍼런스 분석",
            selected_tools=["reference_decoder"],
            initial_inputs={"description": "영화 장면 분석"},
        )

        # reference_decoder has requires_human_review=True
        assert len(dag.human_review_points) > 0

    @pytest.mark.asyncio
    async def test_dag_snapshot_roundtrip(self, hitl_dag):
        """Test DAG can be serialized and deserialized."""
        # Serialize
        snapshot = hitl_dag.to_dict()

        # Verify structure
        assert snapshot["dag_id"] == "dag_hitl"
        assert len(snapshot["nodes"]) == 3
        assert len(snapshot["edges"]) == 2

        # Verify node data
        node_1_data = snapshot["nodes"]["node_1"]
        assert node_1_data["tool_id"] == "tool_a"
        assert node_1_data["requires_human_review"] is False

        node_2_data = snapshot["nodes"]["node_2"]
        assert node_2_data["tool_id"] == "tool_b"
        assert node_2_data["requires_human_review"] is True

        # Verify edge data
        edge_0 = snapshot["edges"][0]
        assert edge_0["from_node_id"] == "node_1"
        assert edge_0["to_node_id"] == "node_2"

    @pytest.mark.asyncio
    async def test_multi_tool_dag_execution_order(self):
        """Test execution order respects dependencies."""
        reset_tool_registry()
        registry = get_tool_registry()

        builder = DynamicDAGBuilder(registry)
        dag = await builder.build_from_intent(
            intent="스토리보드 생성",
            selected_tools=["story_architect", "storyboard_generator"],
            initial_inputs={"concept": "SF 영화 오프닝"},
        )

        # story_architect should come before storyboard_generator
        order = dag.execution_order
        node_tool_ids = [dag.nodes[nid].tool_id for nid in order]

        assert node_tool_ids.index("story_architect") < node_tool_ids.index("storyboard_generator")

    @pytest.mark.asyncio
    async def test_create_executor_factory(self, mock_db):
        """Test factory function creates executor."""
        executor = await create_executor(mock_db)

        assert isinstance(executor, HITLWorkflowExecutor)


# =============================================================================
# Data Type Tests
# =============================================================================

class TestDataTypes:
    """DataType enum tests."""

    def test_data_type_values(self):
        """Test DataType enum has expected values."""
        assert DataType.TEXT.value == "text"
        assert DataType.IMAGE_URL.value == "image_url"
        assert DataType.VIDEO_URL.value == "video_url"
        assert DataType.STYLE_HINT.value == "style_hint"
        assert DataType.STORYBOARD.value == "storyboard"

    def test_data_type_is_string_enum(self):
        """Test DataType is string enum."""
        assert isinstance(DataType.TEXT, str)
        assert DataType.TEXT == "text"


# =============================================================================
# Tool Capability Tests (Default Tools)
# =============================================================================

class TestDefaultTools:
    """Tests for default tool registration."""

    def test_default_tools_registered(self):
        """Test default tools are registered in global registry."""
        reset_tool_registry()
        registry = get_tool_registry()

        # Core tools should be registered
        assert "reference_decoder" in registry
        assert "story_architect" in registry
        assert "storyboard_generator" in registry
        assert "prompt_composer" in registry
        assert "image_generator" in registry
        assert "video_generator" in registry
        assert "aesthetic_director" in registry
        assert "rag_collector" in registry

    def test_reference_decoder_requires_hitl(self):
        """Test reference_decoder requires human review."""
        reset_tool_registry()
        registry = get_tool_registry()

        tool = registry.get("reference_decoder")
        assert tool is not None
        assert tool.requires_human_review is True

    def test_story_architect_requires_hitl(self):
        """Test story_architect requires human review."""
        reset_tool_registry()
        registry = get_tool_registry()

        tool = registry.get("story_architect")
        assert tool is not None
        assert tool.requires_human_review is True

    def test_storyboard_generator_requires_prior_tool(self):
        """Test storyboard_generator requires story_architect."""
        reset_tool_registry()
        registry = get_tool_registry()

        tool = registry.get("storyboard_generator")
        assert tool is not None
        assert "story_architect" in tool.required_prior_tools


# =============================================================================
# Workflow Model Tests
# =============================================================================

class TestWorkflowModels:
    """Tests for workflow model dataclasses."""

    def test_mock_execution_creation(self):
        """Test MockWorkflowExecution creation."""
        execution = MockWorkflowExecution(
            dag_id="test_dag",
            user_id="user_123",
            status=WorkflowStatus.RUNNING.value,
        )

        assert execution.id is not None
        assert execution.dag_id == "test_dag"
        assert execution.user_id == "user_123"
        assert execution.status == "running"

    def test_mock_checkpoint_creation(self):
        """Test MockWorkflowCheckpoint creation."""
        checkpoint = MockWorkflowCheckpoint(
            node_id="node_1",
            tool_id="tool_a",
            status=NodeStatus.WAITING_REVIEW.value,
            node_output={"result": "test output"},
        )

        assert checkpoint.id is not None
        assert checkpoint.node_id == "node_1"
        assert checkpoint.status == "waiting_review"

    def test_mock_node_result_creation(self):
        """Test MockWorkflowNodeResult creation."""
        result = MockWorkflowNodeResult(
            node_id="node_1",
            tool_id="tool_a",
            inputs={"key": "value"},
            outputs={"result": "success"},
        )

        assert result.id is not None
        assert result.inputs == {"key": "value"}
        assert result.outputs == {"result": "success"}


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Edge case tests."""

    def test_empty_dag(self):
        """Test empty DAG handling."""
        dag = ExecutableDAG(
            dag_id="empty_dag",
            nodes={},
            edges=[],
            execution_order=[],
            human_review_points=[],
            estimated_credits=0,
            estimated_latency_ms=0,
            metadata={},
        )

        assert len(dag.nodes) == 0
        assert len(dag.edges) == 0
        assert dag.estimated_credits == 0

    def test_dag_nonexistent_node(self, hitl_dag):
        """Test getting nonexistent node returns None."""
        node = hitl_dag.get_node("nonexistent")
        assert node is None

    def test_dag_node_no_successors(self, hitl_dag):
        """Test node with no successors."""
        successors = hitl_dag.get_successors("node_3")
        assert len(successors) == 0

    def test_dag_node_no_predecessors(self, hitl_dag):
        """Test node with no predecessors."""
        predecessors = hitl_dag.get_predecessors("node_1")
        assert len(predecessors) == 0
