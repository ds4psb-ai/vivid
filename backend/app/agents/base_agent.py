"""Base Agent class for Multi-Agent Orchestration (Phase 4).

Provides abstract interface for all specialized agents.

Usage:
    from app.agents.base_agent import BaseAgent

    class ResearchAgent(BaseAgent):
        agent_id = "research"
        supported_task_types = [AgentTaskType.RESEARCH]

        async def execute(self, task: AgentTask) -> AgentTask:
            # Implementation
            ...
"""
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar

from app.schemas.agent_task import (
    AgentCapability,
    AgentTask,
    AgentTaskStatus,
    AgentTaskType,
    HandoffRequest,
    TaskComplexity,
)

if TYPE_CHECKING:
    from app.agents.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents in the swarm.

    Subclasses must implement:
    - agent_id: Unique identifier
    - supported_task_types: List of task types this agent can handle
    - execute(): Main execution logic

    Optional overrides:
    - can_handle(): Custom task acceptance logic
    - estimate_cost(): Custom cost estimation
    - on_handoff(): Handle incoming handoffs
    """

    # Class-level configuration (override in subclasses)
    agent_id: ClassVar[str] = "base"
    name: ClassVar[str] = "Base Agent"
    supported_task_types: ClassVar[list[AgentTaskType]] = []
    max_complexity: ClassVar[TaskComplexity] = TaskComplexity.HIGH
    concurrent_limit: ClassVar[int] = 1
    cost_multiplier: ClassVar[float] = 1.0

    def __init__(self, orchestrator: AgentOrchestrator | None = None) -> None:
        """Initialize agent with optional orchestrator reference.

        Args:
            orchestrator: Parent orchestrator for handoff requests
        """
        self._orchestrator = orchestrator
        self._active_tasks: dict[str, AgentTask] = {}
        self._total_executions: int = 0
        self._total_failures: int = 0

    @property
    def capability(self) -> AgentCapability:
        """Get agent capability declaration."""
        return AgentCapability(
            agent_id=self.agent_id,
            name=self.name,
            task_types=list(self.supported_task_types),
            max_complexity=self.max_complexity,
            concurrent_limit=self.concurrent_limit,
            cost_multiplier=self.cost_multiplier,
        )

    @property
    def is_available(self) -> bool:
        """Check if agent can accept new tasks."""
        return len(self._active_tasks) < self.concurrent_limit

    @property
    def active_task_count(self) -> int:
        """Number of currently active tasks."""
        return len(self._active_tasks)

    def can_handle(self, task: AgentTask) -> bool:
        """Check if agent can handle the given task.

        Override for custom acceptance logic.
        """
        if task.task_type not in self.supported_task_types:
            return False

        if not self.is_available:
            return False

        # Check complexity
        complexity_order = [TaskComplexity.LOW, TaskComplexity.MEDIUM, TaskComplexity.HIGH]
        if complexity_order.index(task.complexity) > complexity_order.index(self.max_complexity):
            return False

        return True

    def estimate_cost(self, task: AgentTask) -> float:
        """Estimate execution cost for a task.

        Override for custom cost estimation.
        """
        base_cost = task.estimated_cost or 0.01
        return base_cost * self.cost_multiplier

    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentTask:
        """Execute the task and return updated task with result.

        Must be implemented by subclasses.

        Args:
            task: Task to execute

        Returns:
            Updated task with result or error
        """
        ...

    async def run(self, task: AgentTask) -> AgentTask:
        """Execute task with lifecycle management.

        Wraps execute() with tracking and error handling.
        """
        task_key = str(task.task_id)

        try:
            # Mark as running
            task.mark_running(self.agent_id)
            self._active_tasks[task_key] = task
            self._total_executions += 1

            logger.info(
                f"[{self.agent_id}] Starting task {task.task_id} "
                f"(type={task.task_type.value}, complexity={task.complexity.value})"
            )

            # Execute
            result_task = await self.execute(task)

            # Log completion
            if result_task.status == AgentTaskStatus.COMPLETED:
                logger.info(
                    f"[{self.agent_id}] Completed task {task.task_id} "
                    f"(cost=${result_task.actual_cost or 0:.4f})"
                )
            else:
                self._total_failures += 1
                logger.warning(
                    f"[{self.agent_id}] Task {task.task_id} finished with status "
                    f"{result_task.status.value}: {result_task.error}"
                )

            return result_task

        except asyncio.CancelledError:
            task.status = AgentTaskStatus.CANCELLED
            task.error = "Task was cancelled"
            task.completed_at = datetime.utcnow()
            self._total_failures += 1
            logger.warning(f"[{self.agent_id}] Task {task.task_id} cancelled")
            return task

        except Exception as e:
            task.mark_failed(f"{type(e).__name__}: {str(e)}")
            self._total_failures += 1
            logger.exception(f"[{self.agent_id}] Task {task.task_id} failed with error")
            return task

        finally:
            self._active_tasks.pop(task_key, None)

    async def request_handoff(
        self,
        task: AgentTask,
        target_agent: str,
        context: dict[str, Any] | None = None,
        reason: str = "",
    ) -> bool:
        """Request task handoff to another agent.

        Args:
            task: Task to hand off
            target_agent: Target agent ID
            context: Additional context for target agent
            reason: Reason for handoff

        Returns:
            True if handoff was accepted
        """
        if self._orchestrator is None:
            logger.warning(f"[{self.agent_id}] Cannot handoff: no orchestrator")
            return False

        request = HandoffRequest(
            source_agent=self.agent_id,
            target_agent=target_agent,
            task_id=task.task_id,
            context=context or {},
            reason=reason,
        )

        return await self._orchestrator.handle_handoff(request)

    async def on_handoff(self, request: HandoffRequest, task: AgentTask) -> bool:
        """Handle incoming handoff request.

        Override to implement custom handoff acceptance logic.

        Args:
            request: Handoff request details
            task: Task being handed off

        Returns:
            True if handoff accepted
        """
        return self.can_handle(task)

    def get_metrics(self) -> dict[str, Any]:
        """Get agent performance metrics."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "total_executions": self._total_executions,
            "total_failures": self._total_failures,
            "success_rate": (
                (self._total_executions - self._total_failures) / self._total_executions
                if self._total_executions > 0
                else 0.0
            ),
            "active_tasks": self.active_task_count,
            "is_available": self.is_available,
        }


class ResearchAgent(BaseAgent):
    """Agent specialized for RAG search and information gathering."""

    agent_id = "research"
    name = "Research Agent"
    supported_task_types = [AgentTaskType.RESEARCH, AgentTaskType.ANALYZE]
    max_complexity = TaskComplexity.MEDIUM
    concurrent_limit = 3
    cost_multiplier = 0.5  # Uses cheaper models

    async def execute(self, task: AgentTask) -> AgentTask:
        """Execute research task using RAG."""
        from app.rag.hybrid_rag import hybrid_query

        query = task.input_context.get("query", "")
        dimension = task.input_context.get("dimension", "4D")
        auteur_key = task.input_context.get("auteur_key")

        try:
            result = await hybrid_query(
                query=query,
                dimension=dimension,
                auteur_key=auteur_key,
            )

            task.mark_completed(
                result={
                    "sources": [s.model_dump() for s in result.sources[:5]],
                    "confidence": result.confidence,
                    "grounded": result.grounded,
                },
                cost=0.001,  # RAG is cheap
            )

        except Exception as e:
            task.mark_failed(str(e))

        return task


class CreativeAgent(BaseAgent):
    """Agent specialized for content creation."""

    agent_id = "creative"
    name = "Creative Agent"
    supported_task_types = [AgentTaskType.CREATE, AgentTaskType.TRANSFORM]
    max_complexity = TaskComplexity.HIGH
    concurrent_limit = 2
    cost_multiplier = 1.5  # Uses more expensive models

    async def execute(self, task: AgentTask) -> AgentTask:
        """Execute creative task using LLM."""
        # Placeholder - actual implementation would use dimension tools
        prompt = task.input_context.get("prompt", "")
        style = task.input_context.get("style", "default")

        try:
            # TODO: Integrate with actual dimension tools
            task.mark_completed(
                result={
                    "generated": f"[Creative output for: {prompt[:50]}...]",
                    "style_applied": style,
                },
                cost=0.02,
            )

        except Exception as e:
            task.mark_failed(str(e))

        return task


class ValidatorAgent(BaseAgent):
    """Agent specialized for validation and quality control."""

    agent_id = "validator"
    name = "Validator Agent"
    supported_task_types = [AgentTaskType.VALIDATE]
    max_complexity = TaskComplexity.MEDIUM  # Accept up to medium complexity
    concurrent_limit = 5
    cost_multiplier = 0.3  # Uses cheapest models

    async def execute(self, task: AgentTask) -> AgentTask:
        """Execute validation task."""
        content = task.input_context.get("content", "")
        rules = task.input_context.get("rules", [])

        try:
            # Simple validation logic
            issues: list[str] = []
            if not content:
                issues.append("Content is empty")
            if len(content) < 10:
                issues.append("Content too short")

            task.mark_completed(
                result={
                    "valid": len(issues) == 0,
                    "issues": issues,
                    "rules_checked": len(rules),
                },
                cost=0.0005,
            )

        except Exception as e:
            task.mark_failed(str(e))

        return task


class PlannerAgent(BaseAgent):
    """Agent specialized for task planning and decomposition."""

    agent_id = "planner"
    name = "Planner Agent"
    supported_task_types = [AgentTaskType.PLAN]
    max_complexity = TaskComplexity.MEDIUM
    concurrent_limit = 1
    cost_multiplier = 0.8

    async def execute(self, task: AgentTask) -> AgentTask:
        """Execute planning task to decompose complex requests."""
        goal = task.input_context.get("goal", "")
        constraints = task.input_context.get("constraints", [])

        try:
            # TODO: Use LLM for actual planning
            # For now, return a simple decomposition
            steps = [
                {"step": 1, "action": "research", "description": f"Research: {goal[:30]}..."},
                {"step": 2, "action": "create", "description": "Generate content"},
                {"step": 3, "action": "validate", "description": "Validate output"},
            ]

            task.mark_completed(
                result={
                    "steps": steps,
                    "estimated_total_cost": 0.05,
                    "constraints_applied": len(constraints),
                },
                cost=0.005,
            )

        except Exception as e:
            task.mark_failed(str(e))

        return task
