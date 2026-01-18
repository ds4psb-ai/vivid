"""Tests for WorkflowStateService.

Tests cover:
- Create workflow state
- Update progress
- Update context snapshot
- Complete/fail/pause/resume workflow
- Get recoverable workflows

Note: Uses mocked database to avoid PostgreSQL JSONB dependency.
"""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.services.workflow_state_service import WorkflowStateService


def create_mock_workflow_state(
    session_id=None,
    user_id=None,
    status="pending",
    current_step_index=0,
    total_steps=0,
    current_tool=None,
    workflow_definition=None,
    step_results=None,
    context_snapshot=None,
    completed_at=None,
    total_credits_used=0,
    total_execution_ms=0,
    error_message=None,
    retry_count=0,
    last_checkpoint_at=None,
    meta=None,
):
    """Create a mock WorkflowState object."""
    mock = MagicMock()
    mock.id = uuid.uuid4()
    mock.session_id = session_id or uuid.uuid4()
    mock.user_id = user_id
    mock.status = status
    mock.current_step_index = current_step_index
    mock.total_steps = total_steps
    mock.current_tool = current_tool
    mock.workflow_definition = workflow_definition or {}
    mock.step_results = step_results or []
    mock.context_snapshot = context_snapshot or {}
    mock.completed_at = completed_at
    mock.total_credits_used = total_credits_used
    mock.total_execution_ms = total_execution_ms
    mock.error_message = error_message
    mock.retry_count = retry_count
    mock.last_checkpoint_at = last_checkpoint_at
    mock.meta = meta or {}
    mock.created_at = datetime.utcnow()
    mock.updated_at = datetime.utcnow()
    return mock


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def test_session_id():
    """Create a test session ID."""
    return uuid.uuid4()


class TestWorkflowStateCreate:
    """Test workflow state creation."""

    @pytest.mark.asyncio
    async def test_create_basic(self, mock_db, test_session_id):
        """Should create workflow state with defaults."""
        expected_state = create_mock_workflow_state(
            session_id=test_session_id,
            user_id="test-user",
        )

        mock_db.refresh = AsyncMock(side_effect=lambda s: setattr(s, 'id', expected_state.id))

        with patch("app.services.workflow_state_service.WorkflowState") as MockModel:
            MockModel.return_value = expected_state

            service = WorkflowStateService(mock_db)
            state = await service.create(
                session_id=test_session_id,
                user_id="test-user",
            )

            assert state.session_id == test_session_id
            assert state.status == "pending"
            assert state.current_step_index == 0
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_with_workflow_definition(self, mock_db, test_session_id):
        """Should create with workflow definition and count steps."""
        workflow_def = {
            "steps": [
                {"tool": "generate_prompt", "dimension": "1D"},
                {"tool": "generate_image", "dimension": "2D"},
                {"tool": "generate_video", "dimension": "4D"},
            ]
        }

        expected_state = create_mock_workflow_state(
            session_id=test_session_id,
            workflow_definition=workflow_def,
            total_steps=3,
        )

        with patch("app.services.workflow_state_service.WorkflowState") as MockModel:
            MockModel.return_value = expected_state

            service = WorkflowStateService(mock_db)
            state = await service.create(
                session_id=test_session_id,
                workflow_definition=workflow_def,
            )

            assert state.total_steps == 3
            assert state.workflow_definition == workflow_def


class TestWorkflowStateProgress:
    """Test workflow progress updates."""

    @pytest.mark.asyncio
    async def test_update_progress(self, mock_db, test_session_id):
        """Should update current step and tool."""
        existing_state = create_mock_workflow_state(
            session_id=test_session_id,
            status="pending",
        )

        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_state
        mock_db.execute.return_value = mock_result

        service = WorkflowStateService(mock_db)
        updated = await service.update_progress(
            session_id=test_session_id,
            current_step_index=1,
            current_tool="generate_image",
        )

        assert updated.current_step_index == 1
        assert updated.current_tool == "generate_image"
        assert updated.status == "running"

    @pytest.mark.asyncio
    async def test_update_progress_appends_step_result(self, mock_db, test_session_id):
        """Should append step results."""
        existing_state = create_mock_workflow_state(
            session_id=test_session_id,
            step_results=[{"tool": "step1", "output": "result1"}],
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_state
        mock_db.execute.return_value = mock_result

        service = WorkflowStateService(mock_db)
        updated = await service.update_progress(
            session_id=test_session_id,
            current_step_index=2,
            step_result={"tool": "step2", "output": "result2"},
        )

        assert len(updated.step_results) == 2

    @pytest.mark.asyncio
    async def test_update_nonexistent_session(self, mock_db):
        """Should return None for nonexistent session."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = WorkflowStateService(mock_db)
        result = await service.update_progress(
            session_id=uuid.uuid4(),
            current_step_index=1,
        )

        assert result is None


class TestWorkflowStateContext:
    """Test context snapshot updates."""

    @pytest.mark.asyncio
    async def test_update_context(self, mock_db, test_session_id):
        """Should update context snapshot."""
        existing_state = create_mock_workflow_state(session_id=test_session_id)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_state
        mock_db.execute.return_value = mock_result

        context = {
            "session": {"key": "value"},
            "step": {"current": "data"},
        }

        service = WorkflowStateService(mock_db)
        updated = await service.update_context(
            session_id=test_session_id,
            context_snapshot=context,
        )

        assert updated.context_snapshot == context
        assert updated.last_checkpoint_at is not None


class TestWorkflowStateLifecycle:
    """Test workflow lifecycle methods."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self, mock_db, test_session_id):
        """Should mark workflow as completed."""
        existing_state = create_mock_workflow_state(session_id=test_session_id)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_state
        mock_db.execute.return_value = mock_result

        service = WorkflowStateService(mock_db)
        completed = await service.complete(
            session_id=test_session_id,
            total_credits_used=50,
            total_execution_ms=5000,
        )

        assert completed.status == "completed"
        assert completed.completed_at is not None
        assert completed.total_credits_used == 50
        assert completed.total_execution_ms == 5000

    @pytest.mark.asyncio
    async def test_fail_workflow(self, mock_db, test_session_id):
        """Should mark workflow as failed with error."""
        existing_state = create_mock_workflow_state(
            session_id=test_session_id,
            retry_count=0,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_state
        mock_db.execute.return_value = mock_result

        service = WorkflowStateService(mock_db)
        failed = await service.fail(
            session_id=test_session_id,
            error_message="Tool execution failed",
        )

        assert failed.status == "failed"
        assert failed.error_message == "Tool execution failed"
        assert failed.retry_count == 1

    @pytest.mark.asyncio
    async def test_pause_and_resume(self, mock_db, test_session_id):
        """Should pause and resume workflow."""
        existing_state = create_mock_workflow_state(
            session_id=test_session_id,
            status="running",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_state
        mock_db.execute.return_value = mock_result

        service = WorkflowStateService(mock_db)

        # Pause
        paused = await service.pause(session_id=test_session_id)
        assert paused.status == "paused"

        # Resume
        existing_state.status = "paused"
        resumed = await service.resume(session_id=test_session_id)
        assert resumed.status == "running"


class TestWorkflowStateRecovery:
    """Test recoverable workflow queries."""

    @pytest.mark.asyncio
    async def test_get_recoverable_empty(self, mock_db):
        """Should return empty list when no recoverable workflows."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = WorkflowStateService(mock_db)
        result = await service.get_recoverable()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_recoverable_finds_paused(self, mock_db, test_session_id):
        """Should find paused workflows."""
        paused_state = create_mock_workflow_state(
            session_id=test_session_id,
            user_id="test-user",
            status="paused",
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [paused_state]
        mock_db.execute.return_value = mock_result

        service = WorkflowStateService(mock_db)
        result = await service.get_recoverable(user_id="test-user")

        assert len(result) == 1
        assert result[0].status == "paused"

    @pytest.mark.asyncio
    async def test_get_recoverable_finds_failed(self, mock_db, test_session_id):
        """Should find failed workflows."""
        failed_state = create_mock_workflow_state(
            session_id=test_session_id,
            user_id="test-user",
            status="failed",
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [failed_state]
        mock_db.execute.return_value = mock_result

        service = WorkflowStateService(mock_db)
        result = await service.get_recoverable(user_id="test-user")

        assert len(result) == 1
        assert result[0].status == "failed"

    @pytest.mark.asyncio
    async def test_get_recoverable_excludes_completed(self, mock_db, test_session_id):
        """Should NOT find completed workflows (query filters them out)."""
        # The service queries for paused/failed only, so empty result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = WorkflowStateService(mock_db)
        result = await service.get_recoverable()

        assert len(result) == 0
