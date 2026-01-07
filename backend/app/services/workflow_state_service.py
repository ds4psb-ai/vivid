"""P1-4: Workflow State Persistence Service.

Provides persistence and recovery for agent workflow execution state.
Enables session continuity and failure recovery.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models import WorkflowState

logger = get_logger("workflow_state_service")


class WorkflowStateService:
    """Service for managing workflow state persistence.
    
    P1-4: Provides CRUD operations for WorkflowState records,
    enabling agent session recovery and workflow continuity.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        session_id: uuid.UUID,
        user_id: Optional[str] = None,
        workflow_definition: Optional[Dict[str, Any]] = None,
        context_snapshot: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> WorkflowState:
        """Create a new workflow state record.
        
        Args:
            session_id: Agent session ID
            user_id: Optional user ID
            workflow_definition: Planned workflow steps
            context_snapshot: Initial TieredContext state
            meta: Additional metadata
            
        Returns:
            Created WorkflowState record
        """
        total_steps = 0
        if workflow_definition and "steps" in workflow_definition:
            total_steps = len(workflow_definition.get("steps", []))
        
        state = WorkflowState(
            session_id=session_id,
            user_id=user_id,
            status="pending",
            workflow_definition=workflow_definition or {},
            context_snapshot=context_snapshot or {},
            total_steps=total_steps,
            meta=meta or {},
        )
        
        self.db.add(state)
        await self.db.commit()
        await self.db.refresh(state)
        
        logger.info(
            f"Created workflow state: {state.id}",
            extra={"session_id": str(session_id), "total_steps": total_steps}
        )
        return state
    
    async def get_by_session(self, session_id: uuid.UUID) -> Optional[WorkflowState]:
        """Get workflow state by session ID.
        
        Args:
            session_id: Agent session ID
            
        Returns:
            WorkflowState if found, None otherwise
        """
        result = await self.db.execute(
            select(WorkflowState).where(WorkflowState.session_id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, state_id: uuid.UUID) -> Optional[WorkflowState]:
        """Get workflow state by ID."""
        result = await self.db.execute(
            select(WorkflowState).where(WorkflowState.id == state_id)
        )
        return result.scalar_one_or_none()
    
    async def update_progress(
        self,
        session_id: uuid.UUID,
        current_step_index: int,
        current_tool: Optional[str] = None,
        step_result: Optional[Dict[str, Any]] = None,
    ) -> Optional[WorkflowState]:
        """Update workflow progress after step completion.
        
        Args:
            session_id: Agent session ID
            current_step_index: Updated step index
            current_tool: Current tool being executed
            step_result: Result of completed step (appended to step_results)
            
        Returns:
            Updated WorkflowState or None if not found
        """
        state = await self.get_by_session(session_id)
        if not state:
            logger.warning(f"Workflow state not found for session: {session_id}")
            return None
        
        state.current_step_index = current_step_index
        state.current_tool = current_tool
        state.last_checkpoint_at = datetime.utcnow()
        
        if step_result:
            step_results = list(state.step_results or [])
            step_results.append(step_result)
            state.step_results = step_results
        
        if state.status == "pending":
            state.status = "running"
            state.started_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(state)
        
        logger.debug(
            f"Updated workflow progress: step {current_step_index}/{state.total_steps}",
            extra={"session_id": str(session_id), "tool": current_tool}
        )
        return state
    
    async def update_context(
        self,
        session_id: uuid.UUID,
        context_snapshot: Dict[str, Any],
    ) -> Optional[WorkflowState]:
        """Update context snapshot for recovery.
        
        Args:
            session_id: Agent session ID
            context_snapshot: Serialized TieredContext
            
        Returns:
            Updated WorkflowState or None
        """
        state = await self.get_by_session(session_id)
        if not state:
            return None
        
        state.context_snapshot = context_snapshot
        state.last_checkpoint_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(state)
        return state
    
    async def complete(
        self,
        session_id: uuid.UUID,
        total_credits_used: int = 0,
        total_execution_ms: int = 0,
    ) -> Optional[WorkflowState]:
        """Mark workflow as completed.
        
        Args:
            session_id: Agent session ID
            total_credits_used: Total credits consumed
            total_execution_ms: Total execution time
            
        Returns:
            Updated WorkflowState or None
        """
        state = await self.get_by_session(session_id)
        if not state:
            return None
        
        state.status = "completed"
        state.completed_at = datetime.utcnow()
        state.total_credits_used = total_credits_used
        state.total_execution_ms = total_execution_ms
        
        await self.db.commit()
        await self.db.refresh(state)
        
        logger.info(
            f"Workflow completed: {state.id}",
            extra={
                "session_id": str(session_id),
                "credits": total_credits_used,
                "duration_ms": total_execution_ms,
            }
        )
        return state
    
    async def fail(
        self,
        session_id: uuid.UUID,
        error_message: str,
        increment_retry: bool = True,
    ) -> Optional[WorkflowState]:
        """Mark workflow as failed.
        
        Args:
            session_id: Agent session ID
            error_message: Error description
            increment_retry: Whether to increment retry count
            
        Returns:
            Updated WorkflowState or None
        """
        state = await self.get_by_session(session_id)
        if not state:
            return None
        
        state.status = "failed"
        state.error_message = error_message
        if increment_retry:
            state.retry_count += 1
        
        await self.db.commit()
        await self.db.refresh(state)
        
        logger.error(
            f"Workflow failed: {state.id}",
            extra={
                "session_id": str(session_id),
                "error": error_message,
                "retry_count": state.retry_count,
            }
        )
        return state
    
    async def pause(self, session_id: uuid.UUID) -> Optional[WorkflowState]:
        """Pause workflow execution."""
        state = await self.get_by_session(session_id)
        if not state:
            return None
        
        state.status = "paused"
        state.last_checkpoint_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(state)
        return state
    
    async def resume(self, session_id: uuid.UUID) -> Optional[WorkflowState]:
        """Resume paused workflow."""
        state = await self.get_by_session(session_id)
        if not state or state.status != "paused":
            return None
        
        state.status = "running"
        
        await self.db.commit()
        await self.db.refresh(state)
        
        logger.info(
            f"Workflow resumed: {state.id}",
            extra={"session_id": str(session_id), "step": state.current_step_index}
        )
        return state
    
    async def get_recoverable(
        self,
        user_id: Optional[str] = None,
        max_age_hours: int = 24,
    ) -> List[WorkflowState]:
        """Get workflows that can be recovered.
        
        Args:
            user_id: Optional filter by user
            max_age_hours: Maximum age of recoverable workflows
            
        Returns:
            List of recoverable WorkflowState records
        """
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        query = select(WorkflowState).where(
            WorkflowState.status.in_(["paused", "failed"]),
            WorkflowState.updated_at >= cutoff,
        )
        
        if user_id:
            query = query.where(WorkflowState.user_id == user_id)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())


def get_workflow_state_service(db: AsyncSession) -> WorkflowStateService:
    """Factory function for WorkflowStateService."""
    return WorkflowStateService(db)
