"""
Tests for shutdown_manager module.

Tests cover:
- ShutdownManager state transitions
- Request tracking
- Cleanup handler execution
- Graceful shutdown flow
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.shutdown_manager import (
    ShutdownManager,
    ShutdownState,
    ShutdownConfig,
    RequestTracker,
    CleanupRegistry,
    get_shutdown_manager,
    reset_shutdown_manager,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def reset_manager():
    """Reset singleton before and after each test."""
    reset_shutdown_manager()
    yield
    reset_shutdown_manager()


@pytest.fixture
def shutdown_manager(reset_manager):
    """Get fresh ShutdownManager instance."""
    config = ShutdownConfig(
        drain_timeout_seconds=2.0,
        cleanup_timeout_seconds=2.0,
        check_interval_seconds=0.1,
    )
    return ShutdownManager(config)


# =============================================================================
# RequestTracker Tests
# =============================================================================

class TestRequestTracker:
    """Tests for RequestTracker."""

    @pytest.mark.asyncio
    async def test_track_and_untrack(self):
        """Should track and untrack requests."""
        tracker = RequestTracker()

        await tracker.track("req-1", "/api/test", "GET")
        assert tracker.count == 1

        await tracker.track("req-2", "/api/other", "POST")
        assert tracker.count == 2

        result = await tracker.untrack("req-1")
        assert result is not None
        assert result.request_id == "req-1"
        assert tracker.count == 1

    @pytest.mark.asyncio
    async def test_untrack_nonexistent(self):
        """Should return None for nonexistent request."""
        tracker = RequestTracker()

        result = await tracker.untrack("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_requests(self):
        """Should return all tracked requests."""
        tracker = RequestTracker()

        await tracker.track("req-1")
        await tracker.track("req-2")
        await tracker.track("req-3")

        all_requests = tracker.get_all()
        assert len(all_requests) == 3

    @pytest.mark.asyncio
    async def test_get_long_running(self):
        """Should identify long-running requests."""
        tracker = RequestTracker()

        await tracker.track("req-1")
        # Manually set started_at to past time
        tracker._requests["req-1"].started_at = 0  # Unix epoch

        await tracker.track("req-2")  # Recent request

        long_running = tracker.get_long_running(threshold_seconds=1.0)
        assert len(long_running) == 1
        assert long_running[0].request_id == "req-1"


# =============================================================================
# CleanupRegistry Tests
# =============================================================================

class TestCleanupRegistry:
    """Tests for CleanupRegistry."""

    @pytest.mark.asyncio
    async def test_register_and_execute(self):
        """Should register and execute cleanup handlers."""
        registry = CleanupRegistry()
        executed = []

        async def handler1():
            executed.append("handler1")

        async def handler2():
            executed.append("handler2")

        registry.register("handler1", handler1, priority=10)
        registry.register("handler2", handler2, priority=20)

        results = await registry.execute_all(timeout=5.0)

        assert results["handler1"] is True
        assert results["handler2"] is True
        assert executed == ["handler1", "handler2"]  # Ordered by priority

    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Handlers should execute in priority order."""
        registry = CleanupRegistry()
        order = []

        async def low_priority():
            order.append("low")

        async def high_priority():
            order.append("high")

        registry.register("low", low_priority, priority=100)
        registry.register("high", high_priority, priority=10)

        await registry.execute_all(timeout=5.0)

        assert order == ["high", "low"]

    @pytest.mark.asyncio
    async def test_handler_failure_continues(self):
        """Failed handler should not stop others."""
        registry = CleanupRegistry()
        executed = []

        async def failing_handler():
            raise Exception("Handler failed")

        async def good_handler():
            executed.append("good")

        registry.register("failing", failing_handler, priority=10)
        registry.register("good", good_handler, priority=20)

        results = await registry.execute_all(timeout=5.0)

        assert results["failing"] is False
        assert results["good"] is True
        assert "good" in executed


# =============================================================================
# ShutdownManager Tests
# =============================================================================

class TestShutdownManager:
    """Tests for ShutdownManager."""

    def test_initial_state_is_running(self, shutdown_manager):
        """Should start in RUNNING state."""
        assert shutdown_manager.state == ShutdownState.RUNNING
        assert shutdown_manager.is_shutting_down is False

    @pytest.mark.asyncio
    async def test_track_request_when_running(self, shutdown_manager):
        """Should track requests when running."""
        result = shutdown_manager.track_request("req-1", "/api/test", "GET")
        assert result is True
        # Give time for the fire-and-forget task to complete
        await asyncio.sleep(0.05)

    @pytest.mark.asyncio
    async def test_reject_requests_during_shutdown(self, shutdown_manager):
        """Should reject new requests during shutdown."""
        # Start shutdown
        shutdown_manager._state = ShutdownState.DRAINING

        result = shutdown_manager.track_request("req-new")
        assert result is False

    @pytest.mark.asyncio
    async def test_initiate_shutdown_changes_state(self, shutdown_manager):
        """Shutdown should transition through states."""
        await shutdown_manager.initiate_shutdown("test shutdown")

        assert shutdown_manager.state == ShutdownState.STOPPED

    @pytest.mark.asyncio
    async def test_shutdown_waits_for_requests(self, shutdown_manager):
        """Shutdown should wait for in-flight requests."""
        # Track a request - need to await the internal tracker
        await shutdown_manager._tracker.track("req-1", "/api/test", "GET")

        # Start shutdown in background
        shutdown_task = asyncio.create_task(
            shutdown_manager.initiate_shutdown("test")
        )

        # Give it time to start draining
        await asyncio.sleep(0.2)
        assert shutdown_manager.state == ShutdownState.DRAINING

        # Complete the request
        await shutdown_manager._tracker.untrack("req-1")

        # Wait for shutdown to complete
        await shutdown_task

        assert shutdown_manager.state == ShutdownState.STOPPED

    @pytest.mark.asyncio
    async def test_shutdown_runs_cleanup_handlers(self, shutdown_manager):
        """Shutdown should execute cleanup handlers."""
        cleanup_executed = False

        async def cleanup_handler():
            nonlocal cleanup_executed
            cleanup_executed = True

        shutdown_manager.register_cleanup("test_cleanup", cleanup_handler)

        await shutdown_manager.initiate_shutdown("test")

        assert cleanup_executed is True

    @pytest.mark.asyncio
    async def test_shutdown_timeout_for_stuck_requests(self, shutdown_manager):
        """Shutdown should timeout if requests don't complete."""
        # Track a request that won't complete - directly on tracker
        await shutdown_manager._tracker.track("stuck-req", "/api/stuck", "GET")

        # Shutdown with short timeout (already configured in fixture)
        await shutdown_manager.initiate_shutdown("test timeout")

        # Should complete despite stuck request (due to timeout)
        assert shutdown_manager.state == ShutdownState.STOPPED
        assert shutdown_manager.in_flight_count == 1  # Request still tracked

    def test_get_status(self, shutdown_manager):
        """Should return status information."""
        status = shutdown_manager.get_status()

        assert status["state"] == "running"
        assert status["is_shutting_down"] is False
        assert status["in_flight_requests"] == 0
        assert "config" in status

    @pytest.mark.asyncio
    async def test_double_shutdown_ignored(self, shutdown_manager):
        """Second shutdown request should be ignored."""
        # First shutdown
        task1 = asyncio.create_task(
            shutdown_manager.initiate_shutdown("first")
        )

        # Wait for state to change (shutdown starts almost immediately)
        await asyncio.sleep(0.05)

        # Second shutdown (should be ignored since already not RUNNING)
        # Note: initiate_shutdown returns immediately if not in RUNNING state
        await shutdown_manager.initiate_shutdown("second")

        await task1

        # Should only record first reason - the second call was ignored
        # because the state was not RUNNING when it was called
        assert shutdown_manager._shutdown_reason == "first"


# =============================================================================
# Singleton Tests
# =============================================================================

class TestSingleton:
    """Tests for singleton behavior."""

    def test_get_shutdown_manager_returns_singleton(self, reset_manager):
        """get_shutdown_manager should return same instance."""
        mgr1 = get_shutdown_manager()
        mgr2 = get_shutdown_manager()
        assert mgr1 is mgr2

    def test_reset_clears_singleton(self, reset_manager):
        """reset_shutdown_manager should clear singleton."""
        mgr1 = get_shutdown_manager()
        reset_shutdown_manager()
        mgr2 = get_shutdown_manager()
        assert mgr1 is not mgr2


# =============================================================================
# Integration Tests
# =============================================================================

class TestShutdownIntegration:
    """Integration tests for shutdown flow."""

    @pytest.mark.asyncio
    async def test_full_shutdown_flow(self, reset_manager):
        """Test complete shutdown flow with requests and cleanup."""
        manager = get_shutdown_manager()
        cleanup_order = []

        # Register cleanup handlers
        async def db_cleanup():
            await asyncio.sleep(0.1)
            cleanup_order.append("db")

        async def cache_cleanup():
            cleanup_order.append("cache")

        manager.register_cleanup("database", db_cleanup, priority=20)
        manager.register_cleanup("cache", cache_cleanup, priority=10)

        # Track some requests
        manager.track_request("req-1", "/api/test", "GET")
        manager.track_request("req-2", "/api/other", "POST")

        # Start shutdown
        shutdown_task = asyncio.create_task(
            manager.initiate_shutdown("integration test")
        )

        # Simulate requests completing
        await asyncio.sleep(0.2)
        manager.untrack_request("req-1")
        await asyncio.sleep(0.1)
        manager.untrack_request("req-2")

        # Wait for shutdown
        await shutdown_task

        # Verify
        assert manager.state == ShutdownState.STOPPED
        assert cleanup_order == ["cache", "db"]  # Priority order

    @pytest.mark.asyncio
    async def test_shutdown_with_alert(self, reset_manager):
        """Test that shutdown sends alert."""
        manager = get_shutdown_manager()

        with patch.dict(
            "sys.modules",
            {"app.services.alert_manager": MagicMock()}
        ):
            mock_alert_manager = MagicMock()
            mock_alert_manager.shutdown_initiated = AsyncMock()

            with patch(
                "app.services.alert_manager.get_alert_manager",
                return_value=mock_alert_manager,
            ):
                await manager.initiate_shutdown("test alert")

                mock_alert_manager.shutdown_initiated.assert_called_once()
