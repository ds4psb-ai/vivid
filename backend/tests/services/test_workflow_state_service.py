"""Tests for WorkflowStateService.

Tests cover:
- Create workflow state
- Update progress
- Update context snapshot
- Complete/fail/pause/resume workflow
- Get recoverable workflows
"""
import uuid
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base
from app.models import AgentSession, WorkflowState
from app.services.workflow_state_service import WorkflowStateService, get_workflow_state_service


@pytest_asyncio.fixture
async def test_db() -> AsyncSession:
    """In-memory SQLite for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_agent_session(test_db: AsyncSession) -> AgentSession:
    """Create a test agent session."""
    session = AgentSession(
        id=uuid.uuid4(),
        status="active",
        title="Test Session",
        owner_id="test-user",
        meta={},
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)
    return session


class TestWorkflowStateCreate:
    """Test workflow state creation."""
    
    @pytest.mark.asyncio
    async def test_create_basic(self, test_db, test_agent_session):
        """Should create workflow state with defaults."""
        service = WorkflowStateService(test_db)
        
        state = await service.create(
            session_id=test_agent_session.id,
            user_id="test-user",
        )
        
        assert state.id is not None
        assert state.session_id == test_agent_session.id
        assert state.status == "pending"
        assert state.current_step_index == 0
    
    @pytest.mark.asyncio
    async def test_create_with_workflow_definition(self, test_db, test_agent_session):
        """Should create with workflow definition and count steps."""
        service = WorkflowStateService(test_db)
        
        workflow_def = {
            "steps": [
                {"tool": "generate_prompt", "dimension": "1D"},
                {"tool": "generate_image", "dimension": "2D"},
                {"tool": "generate_video", "dimension": "4D"},
            ]
        }
        
        state = await service.create(
            session_id=test_agent_session.id,
            workflow_definition=workflow_def,
        )
        
        assert state.total_steps == 3
        assert state.workflow_definition == workflow_def


class TestWorkflowStateProgress:
    """Test workflow progress updates."""
    
    @pytest.mark.asyncio
    async def test_update_progress(self, test_db, test_agent_session):
        """Should update current step and tool."""
        service = WorkflowStateService(test_db)
        
        state = await service.create(session_id=test_agent_session.id)
        
        updated = await service.update_progress(
            session_id=test_agent_session.id,
            current_step_index=1,
            current_tool="generate_image",
        )
        
        assert updated.current_step_index == 1
        assert updated.current_tool == "generate_image"
        assert updated.status == "running"  # Should transition from pending
    
    @pytest.mark.asyncio
    async def test_update_progress_appends_step_result(self, test_db, test_agent_session):
        """Should append step results."""
        service = WorkflowStateService(test_db)
        
        await service.create(session_id=test_agent_session.id)
        
        await service.update_progress(
            session_id=test_agent_session.id,
            current_step_index=1,
            step_result={"tool": "step1", "output": "result1"},
        )
        
        updated = await service.update_progress(
            session_id=test_agent_session.id,
            current_step_index=2,
            step_result={"tool": "step2", "output": "result2"},
        )
        
        assert len(updated.step_results) == 2
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_session(self, test_db):
        """Should return None for nonexistent session."""
        service = WorkflowStateService(test_db)
        
        result = await service.update_progress(
            session_id=uuid.uuid4(),
            current_step_index=1,
        )
        
        assert result is None


class TestWorkflowStateContext:
    """Test context snapshot updates."""
    
    @pytest.mark.asyncio
    async def test_update_context(self, test_db, test_agent_session):
        """Should update context snapshot."""
        service = WorkflowStateService(test_db)
        
        await service.create(session_id=test_agent_session.id)
        
        context = {
            "session": {"key": "value"},
            "step": {"current": "data"},
        }
        
        updated = await service.update_context(
            session_id=test_agent_session.id,
            context_snapshot=context,
        )
        
        assert updated.context_snapshot == context
        assert updated.last_checkpoint_at is not None


class TestWorkflowStateLifecycle:
    """Test workflow lifecycle methods."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, test_db, test_agent_session):
        """Should mark workflow as completed."""
        service = WorkflowStateService(test_db)
        
        await service.create(session_id=test_agent_session.id)
        
        completed = await service.complete(
            session_id=test_agent_session.id,
            total_credits_used=50,
            total_execution_ms=5000,
        )
        
        assert completed.status == "completed"
        assert completed.completed_at is not None
        assert completed.total_credits_used == 50
        assert completed.total_execution_ms == 5000
    
    @pytest.mark.asyncio
    async def test_fail_workflow(self, test_db, test_agent_session):
        """Should mark workflow as failed with error."""
        service = WorkflowStateService(test_db)
        
        await service.create(session_id=test_agent_session.id)
        
        failed = await service.fail(
            session_id=test_agent_session.id,
            error_message="Tool execution failed",
        )
        
        assert failed.status == "failed"
        assert failed.error_message == "Tool execution failed"
        assert failed.retry_count == 1
    
    @pytest.mark.asyncio
    async def test_pause_and_resume(self, test_db, test_agent_session):
        """Should pause and resume workflow."""
        service = WorkflowStateService(test_db)
        
        await service.create(session_id=test_agent_session.id)
        await service.update_progress(
            session_id=test_agent_session.id,
            current_step_index=1,
        )
        
        paused = await service.pause(session_id=test_agent_session.id)
        assert paused.status == "paused"
        
        resumed = await service.resume(session_id=test_agent_session.id)
        assert resumed.status == "running"


class TestWorkflowStateRecovery:
    """Test recoverable workflow queries."""
    
    @pytest.mark.asyncio
    async def test_get_recoverable_empty(self, test_db):
        """Should return empty list when no recoverable workflows."""
        service = WorkflowStateService(test_db)
        
        result = await service.get_recoverable()
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_recoverable_finds_paused(self, test_db, test_agent_session):
        """Should find paused workflows."""
        service = WorkflowStateService(test_db)
        
        await service.create(session_id=test_agent_session.id, user_id="test-user")
        await service.pause(session_id=test_agent_session.id)
        
        result = await service.get_recoverable(user_id="test-user")
        
        assert len(result) == 1
        assert result[0].status == "paused"
    
    @pytest.mark.asyncio
    async def test_get_recoverable_finds_failed(self, test_db, test_agent_session):
        """Should find failed workflows."""
        service = WorkflowStateService(test_db)
        
        await service.create(session_id=test_agent_session.id, user_id="test-user")
        await service.fail(session_id=test_agent_session.id, error_message="Error")
        
        result = await service.get_recoverable(user_id="test-user")
        
        assert len(result) == 1
        assert result[0].status == "failed"
    
    @pytest.mark.asyncio
    async def test_get_recoverable_excludes_completed(self, test_db, test_agent_session):
        """Should NOT find completed workflows."""
        service = WorkflowStateService(test_db)
        
        await service.create(session_id=test_agent_session.id)
        await service.complete(session_id=test_agent_session.id)
        
        result = await service.get_recoverable()
        
        assert len(result) == 0
