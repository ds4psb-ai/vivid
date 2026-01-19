"""Tests for Multi-Agent Orchestrator (Phase 4)."""
from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

import pytest

from app.agents.base_agent import (
    BaseAgent,
    CreativeAgent,
    PlannerAgent,
    ResearchAgent,
    ValidatorAgent,
)
from app.agents.orchestrator import (
    AgentOrchestrator,
    OrchestratorConfig,
    create_default_orchestrator,
    execute_workflow_with_agents,
)
from app.schemas.agent_task import (
    AgentTask,
    AgentTaskStatus,
    AgentTaskType,
    HandoffRequest,
    TaskComplexity,
    TaskPlan,
)


# =============================================================================
# Test Fixtures
# =============================================================================


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    agent_id = "mock"
    name = "Mock Agent"
    supported_task_types = [AgentTaskType.RESEARCH, AgentTaskType.CREATE]
    max_complexity = TaskComplexity.HIGH
    concurrent_limit = 2

    def __init__(self, delay: float = 0.0, should_fail: bool = False):
        super().__init__()
        self.delay = delay
        self.should_fail = should_fail
        self.executed_tasks: list[AgentTask] = []

    async def execute(self, task: AgentTask) -> AgentTask:
        self.executed_tasks.append(task)

        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if self.should_fail:
            task.mark_failed("Mock failure")
        else:
            task.mark_completed(
                result={"mock": True, "input": task.input_context},
                cost=0.01,
            )

        return task


@pytest.fixture
def orchestrator() -> AgentOrchestrator:
    """Create orchestrator with mock agent."""
    config = OrchestratorConfig(
        max_concurrent_tasks=3,
        task_timeout_seconds=5.0,
    )
    orch = AgentOrchestrator(config)
    orch.register_agent(MockAgent())
    return orch


@pytest.fixture
def default_orchestrator() -> AgentOrchestrator:
    """Create orchestrator with default agents."""
    return create_default_orchestrator()


# =============================================================================
# AgentTask Schema Tests
# =============================================================================


class TestAgentTask:
    """Test AgentTask schema."""

    def test_task_creation(self):
        """Test basic task creation."""
        task = AgentTask(
            task_type=AgentTaskType.RESEARCH,
            input_context={"query": "test"},
        )

        assert task.task_id is not None
        assert task.task_type == AgentTaskType.RESEARCH
        assert task.status == AgentTaskStatus.PENDING
        assert task.input_context == {"query": "test"}

    def test_task_is_ready_no_deps(self):
        """Test task readiness without dependencies."""
        task = AgentTask(task_type=AgentTaskType.RESEARCH)
        assert task.is_ready(set()) is True

    def test_task_is_ready_with_deps(self):
        """Test task readiness with dependencies."""
        dep_id = uuid4()
        task = AgentTask(
            task_type=AgentTaskType.RESEARCH,
            dependencies=[dep_id],
        )

        assert task.is_ready(set()) is False
        assert task.is_ready({dep_id}) is True

    def test_task_mark_running(self):
        """Test marking task as running."""
        task = AgentTask(task_type=AgentTaskType.RESEARCH)
        task.mark_running("agent-1")

        assert task.status == AgentTaskStatus.RUNNING
        assert task.assigned_agent == "agent-1"
        assert task.started_at is not None

    def test_task_mark_completed(self):
        """Test marking task as completed."""
        task = AgentTask(task_type=AgentTaskType.RESEARCH)
        task.mark_completed({"result": "data"}, cost=0.05)

        assert task.status == AgentTaskStatus.COMPLETED
        assert task.result == {"result": "data"}
        assert task.actual_cost == 0.05
        assert task.completed_at is not None

    def test_task_mark_failed(self):
        """Test marking task as failed."""
        task = AgentTask(task_type=AgentTaskType.RESEARCH)
        task.mark_failed("Something went wrong")

        assert task.status == AgentTaskStatus.FAILED
        assert task.error == "Something went wrong"
        assert task.completed_at is not None


class TestTaskPlan:
    """Test TaskPlan schema."""

    def test_plan_creation(self):
        """Test basic plan creation."""
        plan = TaskPlan()
        assert plan.plan_id is not None
        assert len(plan.tasks) == 0

    def test_add_task(self):
        """Test adding tasks to plan."""
        plan = TaskPlan()
        task = plan.add_task(
            task_type=AgentTaskType.RESEARCH,
            input_context={"query": "test"},
        )

        assert len(plan.tasks) == 1
        assert task.task_type == AgentTaskType.RESEARCH

    def test_add_task_with_dependency(self):
        """Test adding task with dependency."""
        plan = TaskPlan()
        task1 = plan.add_task(AgentTaskType.RESEARCH, {})
        task2 = plan.add_task(
            AgentTaskType.CREATE,
            {},
            dependencies=[task1.task_id],
        )

        assert task2.dependencies == [task1.task_id]

    def test_get_ready_tasks(self):
        """Test getting ready tasks."""
        plan = TaskPlan()
        task1 = plan.add_task(AgentTaskType.RESEARCH, {})
        task2 = plan.add_task(AgentTaskType.CREATE, {}, dependencies=[task1.task_id])

        # Initially only task1 is ready
        ready = plan.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == task1.task_id

        # After task1 completes, task2 is ready
        task1.mark_completed({})
        ready = plan.get_ready_tasks({task1.task_id})
        assert len(ready) == 1
        assert ready[0].task_id == task2.task_id

    def test_is_complete(self):
        """Test plan completion check."""
        plan = TaskPlan()
        task = plan.add_task(AgentTaskType.RESEARCH, {})

        assert plan.is_complete is False

        task.mark_completed({})
        assert plan.is_complete is True

    def test_total_costs(self):
        """Test cost calculations."""
        plan = TaskPlan()
        task1 = plan.add_task(AgentTaskType.RESEARCH, {})
        task1.estimated_cost = 0.01
        task2 = plan.add_task(AgentTaskType.CREATE, {})
        task2.estimated_cost = 0.02

        assert plan.total_estimated_cost == 0.03

        task1.actual_cost = 0.015
        task2.actual_cost = 0.025
        assert plan.total_actual_cost == 0.04


# =============================================================================
# BaseAgent Tests
# =============================================================================


class TestBaseAgent:
    """Test BaseAgent functionality."""

    def test_agent_capability(self):
        """Test agent capability declaration."""
        agent = MockAgent()
        cap = agent.capability

        assert cap.agent_id == "mock"
        assert cap.name == "Mock Agent"
        assert AgentTaskType.RESEARCH in cap.task_types

    def test_agent_can_handle(self):
        """Test task handling check."""
        agent = MockAgent()

        # Can handle supported type
        task = AgentTask(task_type=AgentTaskType.RESEARCH)
        assert agent.can_handle(task) is True

        # Cannot handle unsupported type
        task = AgentTask(task_type=AgentTaskType.VALIDATE)
        assert agent.can_handle(task) is False

    def test_agent_availability(self):
        """Test agent availability."""
        agent = MockAgent()
        assert agent.is_available is True

        # Fill up concurrent slots
        agent._active_tasks["1"] = AgentTask(task_type=AgentTaskType.RESEARCH)
        agent._active_tasks["2"] = AgentTask(task_type=AgentTaskType.RESEARCH)

        assert agent.is_available is False

    @pytest.mark.asyncio
    async def test_agent_run_success(self):
        """Test successful task execution."""
        agent = MockAgent()
        task = AgentTask(
            task_type=AgentTaskType.RESEARCH,
            input_context={"query": "test"},
        )

        result = await agent.run(task)

        assert result.status == AgentTaskStatus.COMPLETED
        assert result.result is not None
        assert result.actual_cost == 0.01
        assert agent._total_executions == 1
        assert agent._total_failures == 0

    @pytest.mark.asyncio
    async def test_agent_run_failure(self):
        """Test failed task execution."""
        agent = MockAgent(should_fail=True)
        task = AgentTask(task_type=AgentTaskType.RESEARCH)

        result = await agent.run(task)

        assert result.status == AgentTaskStatus.FAILED
        assert result.error == "Mock failure"
        assert agent._total_failures == 1

    def test_agent_metrics(self):
        """Test agent metrics."""
        agent = MockAgent()
        agent._total_executions = 10
        agent._total_failures = 2

        metrics = agent.get_metrics()

        assert metrics["agent_id"] == "mock"
        assert metrics["total_executions"] == 10
        assert metrics["total_failures"] == 2
        assert metrics["success_rate"] == 0.8


# =============================================================================
# AgentOrchestrator Tests
# =============================================================================


class TestAgentOrchestrator:
    """Test AgentOrchestrator functionality."""

    def test_register_agent(self, orchestrator: AgentOrchestrator):
        """Test agent registration."""
        new_agent = ValidatorAgent()
        orchestrator.register_agent(new_agent)

        assert "validator" in orchestrator._agents

    def test_unregister_agent(self, orchestrator: AgentOrchestrator):
        """Test agent unregistration."""
        result = orchestrator.unregister_agent("mock")
        assert result is True
        assert "mock" not in orchestrator._agents

        result = orchestrator.unregister_agent("nonexistent")
        assert result is False

    def test_find_agent_for_task(self, orchestrator: AgentOrchestrator):
        """Test finding agent for task."""
        task = AgentTask(task_type=AgentTaskType.RESEARCH)
        agent = orchestrator.find_agent_for_task(task)

        assert agent is not None
        assert agent.agent_id == "mock"

    def test_find_agent_unsupported_type(self, orchestrator: AgentOrchestrator):
        """Test finding agent for unsupported task type."""
        task = AgentTask(task_type=AgentTaskType.VALIDATE)
        agent = orchestrator.find_agent_for_task(task)

        assert agent is None

    @pytest.mark.asyncio
    async def test_execute_single_task(self, orchestrator: AgentOrchestrator):
        """Test executing single task."""
        task = AgentTask(
            task_type=AgentTaskType.RESEARCH,
            input_context={"query": "test"},
        )

        result = await orchestrator.execute_task(task)

        assert result.status == AgentTaskStatus.COMPLETED
        assert orchestrator._execution_count == 1

    @pytest.mark.asyncio
    async def test_execute_task_no_agent(self, orchestrator: AgentOrchestrator):
        """Test executing task with no available agent."""
        task = AgentTask(task_type=AgentTaskType.VALIDATE)

        result = await orchestrator.execute_task(task)

        assert result.status == AgentTaskStatus.FAILED
        assert "No agent available" in result.error

    @pytest.mark.asyncio
    async def test_execute_plan_sequential(self, orchestrator: AgentOrchestrator):
        """Test executing plan with sequential tasks."""
        plan = TaskPlan()
        task1 = plan.add_task(AgentTaskType.RESEARCH, {"step": 1})
        task2 = plan.add_task(AgentTaskType.CREATE, {"step": 2}, dependencies=[task1.task_id])

        result = await orchestrator.execute_plan(plan)

        assert result.is_complete
        assert task1.status == AgentTaskStatus.COMPLETED
        assert task2.status == AgentTaskStatus.COMPLETED

        # Verify execution order
        mock = orchestrator._agents["mock"]
        assert mock.executed_tasks[0].input_context["step"] == 1
        assert mock.executed_tasks[1].input_context["step"] == 2

    @pytest.mark.asyncio
    async def test_execute_plan_parallel(self, orchestrator: AgentOrchestrator):
        """Test executing plan with parallel tasks."""
        plan = TaskPlan()
        plan.add_task(AgentTaskType.RESEARCH, {"id": 1})
        plan.add_task(AgentTaskType.RESEARCH, {"id": 2})
        plan.add_task(AgentTaskType.RESEARCH, {"id": 3})

        result = await orchestrator.execute_plan(plan, max_parallel=3)

        assert result.is_complete
        assert all(t.status == AgentTaskStatus.COMPLETED for t in result.tasks)

    @pytest.mark.asyncio
    async def test_cost_budget_enforcement(self):
        """Test cost budget enforcement."""
        config = OrchestratorConfig(cost_budget=0.02)
        orch = AgentOrchestrator(config)
        orch.register_agent(MockAgent())

        # First task should succeed
        task1 = AgentTask(task_type=AgentTaskType.RESEARCH)
        await orch.execute_task(task1)
        assert task1.status == AgentTaskStatus.COMPLETED

        # Second task should succeed
        task2 = AgentTask(task_type=AgentTaskType.RESEARCH)
        await orch.execute_task(task2)
        assert task2.status == AgentTaskStatus.COMPLETED

        # Third task should fail (budget exceeded)
        task3 = AgentTask(task_type=AgentTaskType.RESEARCH)
        await orch.execute_task(task3)
        assert task3.status == AgentTaskStatus.FAILED
        assert "budget exceeded" in task3.error.lower()

    def test_get_metrics(self, orchestrator: AgentOrchestrator):
        """Test orchestrator metrics."""
        metrics = orchestrator.get_metrics()

        assert "total_executions" in metrics
        assert "total_cost" in metrics
        assert "agents" in metrics
        assert "mock" in metrics["agents"]

    def test_get_capabilities(self, orchestrator: AgentOrchestrator):
        """Test getting all capabilities."""
        caps = orchestrator.get_capabilities()

        assert len(caps) == 1
        assert caps[0]["agent_id"] == "mock"


class TestHandoff:
    """Test agent handoff functionality."""

    @pytest.mark.asyncio
    async def test_handoff_success(self):
        """Test successful handoff."""
        orch = AgentOrchestrator()
        source = MockAgent()
        source.agent_id = "source"
        source.supported_task_types = [AgentTaskType.RESEARCH]

        target = MockAgent()
        target.agent_id = "target"
        target.supported_task_types = [AgentTaskType.RESEARCH]

        orch.register_agent(source)
        orch.register_agent(target)

        # Execute initial task
        task = AgentTask(task_type=AgentTaskType.RESEARCH)
        await orch.execute_task(task)

        # Request handoff
        request = HandoffRequest(
            source_agent="source",
            target_agent="target",
            task_id=task.task_id,
            reason="Testing handoff",
        )

        accepted = await orch.handle_handoff(request)
        assert accepted is True

    @pytest.mark.asyncio
    async def test_handoff_disabled(self):
        """Test handoff when disabled."""
        config = OrchestratorConfig(handoff_enabled=False)
        orch = AgentOrchestrator(config)
        orch.register_agent(MockAgent())

        request = HandoffRequest(
            source_agent="mock",
            target_agent="other",
            task_id=uuid4(),
        )

        accepted = await orch.handle_handoff(request)
        assert accepted is False

    @pytest.mark.asyncio
    async def test_handoff_unknown_target(self):
        """Test handoff to unknown agent."""
        orch = AgentOrchestrator()
        orch.register_agent(MockAgent())

        request = HandoffRequest(
            source_agent="mock",
            target_agent="nonexistent",
            task_id=uuid4(),
        )

        accepted = await orch.handle_handoff(request)
        assert accepted is False


# =============================================================================
# Default Orchestrator Tests
# =============================================================================


class TestDefaultOrchestrator:
    """Test default orchestrator configuration."""

    def test_create_default(self, default_orchestrator: AgentOrchestrator):
        """Test default orchestrator creation."""
        assert len(default_orchestrator._agents) == 4
        assert "research" in default_orchestrator._agents
        assert "creative" in default_orchestrator._agents
        assert "validator" in default_orchestrator._agents
        assert "planner" in default_orchestrator._agents

    @pytest.mark.asyncio
    async def test_research_agent(self, default_orchestrator: AgentOrchestrator):
        """Test research agent execution."""
        task = AgentTask(
            task_type=AgentTaskType.RESEARCH,
            input_context={"query": "test", "dimension": "4D"},
        )

        # This will fail without RAG setup, but should not crash
        result = await default_orchestrator.execute_task(task)
        # Result depends on RAG availability
        assert result.status in (AgentTaskStatus.COMPLETED, AgentTaskStatus.FAILED)

    @pytest.mark.asyncio
    async def test_validator_agent(self):
        """Test validator agent execution."""
        # Create orchestrator with explicit validator registration
        orch = AgentOrchestrator()
        orch.register_agent(ValidatorAgent())

        task = AgentTask(
            task_type=AgentTaskType.VALIDATE,
            input_context={"content": "This is valid content with enough length", "rules": []},
        )

        result = await orch.execute_task(task)

        assert result.status == AgentTaskStatus.COMPLETED
        assert result.result["valid"] is True
        assert result.result["issues"] == []

    @pytest.mark.asyncio
    async def test_planner_agent(self, default_orchestrator: AgentOrchestrator):
        """Test planner agent execution."""
        task = AgentTask(
            task_type=AgentTaskType.PLAN,
            input_context={"goal": "Create a movie scene"},
        )

        result = await default_orchestrator.execute_task(task)

        assert result.status == AgentTaskStatus.COMPLETED
        assert "steps" in result.result


# =============================================================================
# Integration Tests
# =============================================================================


class TestWorkflowExecution:
    """Test high-level workflow execution."""

    @pytest.mark.asyncio
    async def test_execute_workflow_basic(self):
        """Test basic workflow execution."""
        # Use mock orchestrator for predictable results
        config = OrchestratorConfig(max_concurrent_tasks=2)
        orch = AgentOrchestrator(config)

        # Register mock agents for all types
        for task_type in AgentTaskType:
            agent = MockAgent()
            agent.agent_id = f"mock_{task_type.value}"
            agent.supported_task_types = [task_type]
            orch.register_agent(agent)

        result = await execute_workflow_with_agents(
            goal="Create a test scene",
            context={"dimension": "4D"},
            orchestrator=orch,
        )

        assert "goal" in result
        assert "tasks" in result
        assert len(result["tasks"]) == 4  # plan, research, create, validate
