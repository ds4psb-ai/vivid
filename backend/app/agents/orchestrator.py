"""Agent Orchestrator for Multi-Agent Coordination (Phase 4).

Manages agent swarm, task distribution, and execution flow.

Patterns supported:
- Supervisor: Main orchestrator coordinates specialist agents
- Sequential: Tasks execute in dependency order
- Concurrent: Independent tasks run in parallel
- Handoff: Context-preserving agent-to-agent transfer

Usage:
    from app.agents.orchestrator import AgentOrchestrator
    from app.agents.base_agent import ResearchAgent, CreativeAgent

    orchestrator = AgentOrchestrator()
    orchestrator.register_agent(ResearchAgent())
    orchestrator.register_agent(CreativeAgent())

    plan = TaskPlan()
    plan.add_task(AgentTaskType.RESEARCH, {"query": "봉준호 스타일"})
    plan.add_task(AgentTaskType.CREATE, {"prompt": "..."}, dependencies=[...])

    results = await orchestrator.execute_plan(plan)
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from app.schemas.agent_task import (
    AgentTask,
    AgentTaskStatus,
    AgentTaskType,
    HandoffRequest,
    OrchestratorConfig,
    TaskComplexity,
    TaskPlan,
)

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates multi-agent task execution.

    Responsibilities:
    - Agent registration and capability tracking
    - Task assignment based on agent capabilities
    - Parallel execution of independent tasks
    - Sequential execution respecting dependencies
    - Handoff coordination between agents
    - Cost tracking and budget enforcement
    """

    def __init__(self, config: OrchestratorConfig | None = None) -> None:
        """Initialize orchestrator with configuration.

        Args:
            config: Orchestrator configuration (uses defaults if not provided)
        """
        from app.agents.base_agent import BaseAgent

        self.config = config or OrchestratorConfig()
        self._agents: dict[str, BaseAgent] = {}
        self._task_history: list[AgentTask] = []
        self._total_cost: float = 0.0
        self._execution_count: int = 0

    def register_agent(self, agent: Any) -> None:
        """Register an agent with the orchestrator.

        Args:
            agent: Agent instance to register
        """
        from app.agents.base_agent import BaseAgent

        if not isinstance(agent, BaseAgent):
            raise TypeError(f"Expected BaseAgent, got {type(agent).__name__}")

        agent._orchestrator = self
        self._agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.agent_id} ({agent.name})")

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent.

        Args:
            agent_id: Agent ID to remove

        Returns:
            True if agent was removed
        """
        if agent_id in self._agents:
            agent = self._agents.pop(agent_id)
            agent._orchestrator = None
            logger.info(f"Unregistered agent: {agent_id}")
            return True
        return False

    def get_agent(self, agent_id: str) -> Any | None:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def find_agent_for_task(self, task: AgentTask) -> Any | None:
        """Find best available agent for a task.

        Selection criteria:
        1. Must support task type
        2. Must be available (under concurrent limit)
        3. Must handle task complexity
        4. Prefer agent with lowest cost multiplier
        """
        candidates = []

        for agent in self._agents.values():
            if agent.can_handle(task):
                candidates.append(agent)

        if not candidates:
            return None

        # Sort by cost multiplier (prefer cheaper agents)
        candidates.sort(key=lambda a: a.cost_multiplier)
        return candidates[0]

    async def execute_task(self, task: AgentTask) -> AgentTask:
        """Execute a single task with appropriate agent.

        Args:
            task: Task to execute

        Returns:
            Updated task with result or error
        """
        # Check budget
        if self.config.cost_budget is not None:
            if self._total_cost >= self.config.cost_budget:
                task.mark_failed("Cost budget exceeded")
                return task

        # Find agent
        agent = self.find_agent_for_task(task)
        if agent is None:
            task.mark_failed(f"No agent available for task type: {task.task_type.value}")
            return task

        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                agent.run(task),
                timeout=self.config.task_timeout_seconds,
            )

            # Track cost
            if result.actual_cost:
                self._total_cost += result.actual_cost

            self._task_history.append(result)
            self._execution_count += 1

            return result

        except asyncio.TimeoutError:
            task.mark_failed(f"Task timed out after {self.config.task_timeout_seconds}s")
            self._task_history.append(task)
            return task

    async def execute_plan(
        self,
        plan: TaskPlan,
        max_parallel: int | None = None,
    ) -> TaskPlan:
        """Execute a task plan with dependency resolution.

        Tasks are executed in topological order, with independent
        tasks running in parallel up to max_parallel limit.

        Args:
            plan: Task plan to execute
            max_parallel: Max parallel tasks (uses config default if not set)

        Returns:
            Updated plan with all task results
        """
        max_parallel = max_parallel or self.config.max_concurrent_tasks
        completed_tasks: set[UUID] = set()
        failed_critically = False

        logger.info(
            f"Starting plan {plan.plan_id} with {len(plan.tasks)} tasks "
            f"(max_parallel={max_parallel})"
        )

        while not plan.is_complete and not failed_critically:
            # Get ready tasks
            ready_tasks = plan.get_ready_tasks(completed_tasks)

            if not ready_tasks:
                # Check for deadlock
                pending = [t for t in plan.tasks if t.status == AgentTaskStatus.PENDING]
                if pending:
                    logger.error(
                        f"Deadlock detected: {len(pending)} pending tasks with unsatisfied dependencies"
                    )
                    for task in pending:
                        task.mark_failed("Deadlock: dependencies cannot be satisfied")
                break

            # Limit parallel execution
            batch = ready_tasks[:max_parallel]

            logger.debug(f"Executing batch of {len(batch)} tasks")

            # Execute batch in parallel
            results = await asyncio.gather(
                *[self.execute_task(task) for task in batch],
                return_exceptions=True,
            )

            # Process results
            for i, result in enumerate(results):
                task = batch[i]

                if isinstance(result, Exception):
                    task.mark_failed(f"Execution error: {result}")
                    logger.exception(f"Task {task.task_id} raised exception")

                if task.status == AgentTaskStatus.COMPLETED:
                    completed_tasks.add(task.task_id)
                elif task.status == AgentTaskStatus.FAILED:
                    # Check if this is a critical failure
                    # (other tasks depend on it)
                    dependents = [
                        t for t in plan.tasks
                        if task.task_id in t.dependencies
                    ]
                    if dependents:
                        logger.warning(
                            f"Critical task {task.task_id} failed, "
                            f"{len(dependents)} dependent tasks affected"
                        )

        # Log completion
        completed_count = sum(
            1 for t in plan.tasks if t.status == AgentTaskStatus.COMPLETED
        )
        failed_count = sum(
            1 for t in plan.tasks if t.status == AgentTaskStatus.FAILED
        )

        logger.info(
            f"Plan {plan.plan_id} finished: "
            f"{completed_count} completed, {failed_count} failed, "
            f"total_cost=${plan.total_actual_cost:.4f}"
        )

        return plan

    async def handle_handoff(self, request: HandoffRequest) -> bool:
        """Handle agent-to-agent task handoff.

        Args:
            request: Handoff request with source, target, and context

        Returns:
            True if handoff was accepted
        """
        if not self.config.handoff_enabled:
            logger.warning("Handoff rejected: handoffs disabled")
            return False

        target_agent = self._agents.get(request.target_agent)
        if target_agent is None:
            logger.warning(f"Handoff rejected: unknown target agent {request.target_agent}")
            return False

        # Find the task (in history or active)
        task = None
        for hist_task in self._task_history:
            if hist_task.task_id == request.task_id:
                task = hist_task
                break

        if task is None:
            logger.warning(f"Handoff rejected: task {request.task_id} not found")
            return False

        # Check if target can accept
        accepted = await target_agent.on_handoff(request, task)

        if accepted:
            # Update task state
            task.status = AgentTaskStatus.WAITING_HANDOFF
            task.input_context.update(request.context)

            logger.info(
                f"Handoff accepted: {request.source_agent} -> {request.target_agent} "
                f"(task={request.task_id}, reason={request.reason})"
            )

        return accepted

    def get_metrics(self) -> dict[str, Any]:
        """Get orchestrator metrics."""
        agent_metrics = {
            agent_id: agent.get_metrics()
            for agent_id, agent in self._agents.items()
        }

        return {
            "total_executions": self._execution_count,
            "total_cost": self._total_cost,
            "budget_remaining": (
                self.config.cost_budget - self._total_cost
                if self.config.cost_budget
                else None
            ),
            "agents": agent_metrics,
            "task_history_size": len(self._task_history),
        }

    def get_capabilities(self) -> list[dict[str, Any]]:
        """Get all registered agent capabilities."""
        return [agent.capability.model_dump() for agent in self._agents.values()]


# =============================================================================
# Factory Functions
# =============================================================================


def create_default_orchestrator() -> AgentOrchestrator:
    """Create orchestrator with default agent swarm.

    Includes:
    - ResearchAgent: RAG search
    - CreativeAgent: Content generation
    - ValidatorAgent: Quality control
    - PlannerAgent: Task decomposition
    """
    from app.agents.base_agent import (
        CreativeAgent,
        PlannerAgent,
        ResearchAgent,
        ValidatorAgent,
    )

    config = OrchestratorConfig(
        max_concurrent_tasks=5,
        task_timeout_seconds=300.0,
        retry_limit=3,
        handoff_enabled=True,
    )

    orchestrator = AgentOrchestrator(config)
    orchestrator.register_agent(ResearchAgent())
    orchestrator.register_agent(CreativeAgent())
    orchestrator.register_agent(ValidatorAgent())
    orchestrator.register_agent(PlannerAgent())

    return orchestrator


async def execute_workflow_with_agents(
    goal: str,
    context: dict[str, Any] | None = None,
    orchestrator: AgentOrchestrator | None = None,
) -> dict[str, Any]:
    """High-level workflow execution using multi-agent system.

    Decomposes goal into tasks, executes with agent swarm,
    and aggregates results.

    Args:
        goal: High-level goal description
        context: Additional context (auteur_key, dimension, etc.)
        orchestrator: Orchestrator instance (creates default if not provided)

    Returns:
        Aggregated workflow results
    """
    if orchestrator is None:
        orchestrator = create_default_orchestrator()

    context = context or {}

    # Create plan
    plan = TaskPlan(metadata={"goal": goal, **context})

    # Step 1: Plan the workflow
    plan_task = plan.add_task(
        task_type=AgentTaskType.PLAN,
        input_context={"goal": goal, "constraints": context.get("constraints", [])},
        complexity=TaskComplexity.MEDIUM,
        priority=1,
    )

    # Step 2: Research (depends on plan)
    research_task = plan.add_task(
        task_type=AgentTaskType.RESEARCH,
        input_context={
            "query": goal,
            "dimension": context.get("dimension", "4D"),
            "auteur_key": context.get("auteur_key"),
        },
        dependencies=[plan_task.task_id],
        complexity=TaskComplexity.MEDIUM,
        priority=2,
    )

    # Step 3: Create (depends on research)
    create_task = plan.add_task(
        task_type=AgentTaskType.CREATE,
        input_context={
            "prompt": goal,
            "style": context.get("style", "default"),
        },
        dependencies=[research_task.task_id],
        complexity=TaskComplexity.HIGH,
        priority=3,
    )

    # Step 4: Validate (depends on create)
    plan.add_task(
        task_type=AgentTaskType.VALIDATE,
        input_context={
            "content": "",  # Will be filled from create task
            "rules": context.get("validation_rules", []),
        },
        dependencies=[create_task.task_id],
        complexity=TaskComplexity.LOW,
        priority=4,
    )

    # Execute plan
    completed_plan = await orchestrator.execute_plan(plan)

    # Aggregate results
    results = {
        "goal": goal,
        "plan_id": str(completed_plan.plan_id),
        "success": completed_plan.is_complete and all(
            t.status == AgentTaskStatus.COMPLETED for t in completed_plan.tasks
        ),
        "total_cost": completed_plan.total_actual_cost,
        "tasks": [
            {
                "task_id": str(t.task_id),
                "type": t.task_type.value,
                "status": t.status.value,
                "result": t.result,
                "error": t.error,
                "cost": t.actual_cost,
            }
            for t in completed_plan.tasks
        ],
    }

    return results
