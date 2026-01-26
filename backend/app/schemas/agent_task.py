"""Agent Task schemas for Multi-Agent Orchestration (Phase 4).

Provides task decomposition and agent coordination primitives.

Usage:
    from app.schemas.agent_task import AgentTask, AgentTaskStatus, TaskPlan

    task = AgentTask(
        task_type="research",
        input_context={"query": "강주노 스타일"},
        estimated_cost=0.01,
    )
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentTaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_HANDOFF = "waiting_handoff"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentTaskType(str, Enum):
    """Specialized task types for agent routing."""

    RESEARCH = "research"      # RAG 검색, 정보 수집
    CREATE = "create"          # 콘텐츠 생성
    ANALYZE = "analyze"        # 분석, 평가
    VALIDATE = "validate"      # 검증, QC
    PLAN = "plan"              # 계획 수립
    TRANSFORM = "transform"    # 데이터 변환


class TaskComplexity(str, Enum):
    """Task complexity for model routing."""

    LOW = "low"       # Gemini Flash 적합
    MEDIUM = "medium" # Gemini Pro 적합
    HIGH = "high"     # Gemini Ultra 적합


class AgentTask(BaseModel):
    """Individual task for agent execution.

    Attributes:
        task_id: Unique task identifier
        task_type: Type of task (research, create, etc.)
        input_context: Input data for task execution
        dependencies: List of task IDs that must complete first
        assigned_agent: Agent ID handling this task
        status: Current execution status
        result: Task output after completion
        error: Error message if failed
        complexity: Estimated complexity for model routing
        estimated_cost: Estimated API cost in USD
        actual_cost: Actual API cost after execution
        priority: Execution priority (lower = higher priority)
        created_at: Task creation timestamp
        started_at: Execution start timestamp
        completed_at: Execution completion timestamp
    """

    task_id: UUID = Field(default_factory=uuid4)
    task_type: AgentTaskType
    input_context: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[UUID] = Field(default_factory=list)
    assigned_agent: str | None = None
    status: AgentTaskStatus = AgentTaskStatus.PENDING
    result: dict[str, Any] | None = None
    error: str | None = None
    complexity: TaskComplexity = TaskComplexity.MEDIUM
    estimated_cost: float = 0.0
    actual_cost: float | None = None
    priority: int = 10  # 1 = highest, 100 = lowest
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def is_ready(self, completed_tasks: set[UUID]) -> bool:
        """Check if all dependencies are satisfied."""
        return all(dep in completed_tasks for dep in self.dependencies)

    def mark_running(self, agent_id: str) -> None:
        """Mark task as running with assigned agent."""
        self.status = AgentTaskStatus.RUNNING
        self.assigned_agent = agent_id
        self.started_at = datetime.utcnow()

    def mark_completed(self, result: dict[str, Any], cost: float | None = None) -> None:
        """Mark task as completed with result."""
        self.status = AgentTaskStatus.COMPLETED
        self.result = result
        self.actual_cost = cost
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """Mark task as failed with error."""
        self.status = AgentTaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()


class TaskPlan(BaseModel):
    """Execution plan with multiple tasks.

    Represents a DAG of tasks with dependencies.
    """

    plan_id: UUID = Field(default_factory=uuid4)
    tasks: list[AgentTask] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def add_task(
        self,
        task_type: AgentTaskType,
        input_context: dict[str, Any],
        dependencies: list[UUID] | None = None,
        complexity: TaskComplexity = TaskComplexity.MEDIUM,
        priority: int = 10,
    ) -> AgentTask:
        """Add a new task to the plan."""
        task = AgentTask(
            task_type=task_type,
            input_context=input_context,
            dependencies=dependencies or [],
            complexity=complexity,
            priority=priority,
        )
        self.tasks.append(task)
        return task

    def get_ready_tasks(self, completed_tasks: set[UUID] | None = None) -> list[AgentTask]:
        """Get tasks ready for execution (dependencies satisfied)."""
        completed = completed_tasks or set()
        return [
            task for task in self.tasks
            if task.status == AgentTaskStatus.PENDING and task.is_ready(completed)
        ]

    def get_task(self, task_id: UUID) -> AgentTask | None:
        """Get task by ID."""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None

    @property
    def is_complete(self) -> bool:
        """Check if all tasks are completed or failed."""
        return all(
            task.status in (AgentTaskStatus.COMPLETED, AgentTaskStatus.FAILED, AgentTaskStatus.CANCELLED)
            for task in self.tasks
        )

    @property
    def total_estimated_cost(self) -> float:
        """Sum of estimated costs."""
        return sum(task.estimated_cost for task in self.tasks)

    @property
    def total_actual_cost(self) -> float:
        """Sum of actual costs (completed tasks only)."""
        return sum(
            task.actual_cost or 0.0
            for task in self.tasks
            if task.actual_cost is not None
        )


class HandoffRequest(BaseModel):
    """Request to handoff task to another agent.

    Used in Handoff Pattern for agent-to-agent task transfer.
    """

    source_agent: str
    target_agent: str
    task_id: UUID
    context: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""


class AgentCapability(BaseModel):
    """Agent capability declaration.

    Used for task routing decisions.
    """

    agent_id: str
    name: str
    task_types: list[AgentTaskType]
    max_complexity: TaskComplexity = TaskComplexity.HIGH
    concurrent_limit: int = 1
    cost_multiplier: float = 1.0  # For cost estimation


class OrchestratorConfig(BaseModel):
    """Configuration for agent orchestrator."""

    max_concurrent_tasks: int = 5
    task_timeout_seconds: float = 300.0
    retry_limit: int = 3
    handoff_enabled: bool = True
    cost_budget: float | None = None  # USD budget limit
    agents: list[AgentCapability] = Field(default_factory=list)
