"""
Graceful Shutdown Manager

Manages graceful shutdown of the application:
- Tracks in-flight requests
- Rejects new requests during shutdown
- Waits for active requests to complete
- Executes cleanup handlers

Usage:
    from app.services.shutdown_manager import ShutdownManager, get_shutdown_manager

    shutdown_mgr = get_shutdown_manager()

    # Track request
    shutdown_mgr.track_request(request_id)
    try:
        # Process request
        ...
    finally:
        shutdown_mgr.untrack_request(request_id)

    # Initiate shutdown
    await shutdown_mgr.initiate_shutdown("SIGTERM received")
"""
from __future__ import annotations

import asyncio
import logging
import signal
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# =============================================================================
# Shutdown States
# =============================================================================

class ShutdownState(Enum):
    """Server shutdown states."""
    RUNNING = "running"           # Normal operation
    DRAINING = "draining"         # Rejecting new, waiting for in-flight
    SHUTTING_DOWN = "shutting_down"  # Running cleanup handlers
    STOPPED = "stopped"           # Shutdown complete


@dataclass
class ShutdownConfig:
    """Shutdown configuration."""
    drain_timeout_seconds: float = 30.0  # Max wait for in-flight requests
    cleanup_timeout_seconds: float = 10.0  # Max time for cleanup handlers
    grace_period_seconds: float = 5.0  # Grace period before hard shutdown
    check_interval_seconds: float = 0.5  # Interval for checking in-flight count


# =============================================================================
# Request Tracker
# =============================================================================

@dataclass
class TrackedRequest:
    """Tracked request metadata."""
    request_id: str
    started_at: float
    path: str = ""
    method: str = ""


class RequestTracker:
    """
    Tracks in-flight requests for graceful shutdown.

    Thread-safe tracking of active requests with metadata.
    """

    def __init__(self):
        """Initialize request tracker."""
        self._requests: Dict[str, TrackedRequest] = {}
        self._lock = asyncio.Lock()

    async def track(
        self,
        request_id: str,
        path: str = "",
        method: str = "",
    ) -> None:
        """Start tracking a request.

        Args:
            request_id: Unique request identifier
            path: Request path
            method: HTTP method
        """
        async with self._lock:
            self._requests[request_id] = TrackedRequest(
                request_id=request_id,
                started_at=time.time(),
                path=path,
                method=method,
            )

    async def untrack(self, request_id: str) -> Optional[TrackedRequest]:
        """Stop tracking a request.

        Args:
            request_id: Request identifier

        Returns:
            Tracked request data or None if not found
        """
        async with self._lock:
            return self._requests.pop(request_id, None)

    @property
    def count(self) -> int:
        """Get current in-flight count."""
        return len(self._requests)

    def get_all(self) -> List[TrackedRequest]:
        """Get all tracked requests."""
        return list(self._requests.values())

    def get_long_running(self, threshold_seconds: float = 30.0) -> List[TrackedRequest]:
        """Get requests running longer than threshold.

        Args:
            threshold_seconds: Duration threshold

        Returns:
            List of long-running requests
        """
        now = time.time()
        return [
            req for req in self._requests.values()
            if now - req.started_at > threshold_seconds
        ]


# =============================================================================
# Cleanup Handler Registry
# =============================================================================

CleanupHandler = Callable[[], Coroutine[Any, Any, None]]


class CleanupRegistry:
    """Registry for cleanup handlers executed during shutdown."""

    def __init__(self):
        """Initialize cleanup registry."""
        self._handlers: List[tuple[str, CleanupHandler, int]] = []

    def register(
        self,
        name: str,
        handler: CleanupHandler,
        priority: int = 100,
    ) -> None:
        """Register a cleanup handler.

        Args:
            name: Handler name for logging
            handler: Async cleanup function
            priority: Execution priority (lower = earlier)
        """
        self._handlers.append((name, handler, priority))
        # Sort by priority
        self._handlers.sort(key=lambda x: x[2])
        logger.debug(f"[SHUTDOWN] Registered cleanup handler: {name} (priority={priority})")

    async def execute_all(self, timeout: float = 10.0) -> Dict[str, bool]:
        """Execute all cleanup handlers.

        Args:
            timeout: Total timeout for all handlers

        Returns:
            Dict of handler name -> success status
        """
        results: Dict[str, bool] = {}

        for name, handler, _ in self._handlers:
            try:
                logger.info(f"[SHUTDOWN] Running cleanup: {name}")
                await asyncio.wait_for(handler(), timeout=timeout / len(self._handlers))
                results[name] = True
                logger.info(f"[SHUTDOWN] Cleanup complete: {name}")
            except asyncio.TimeoutError:
                logger.warning(f"[SHUTDOWN] Cleanup timeout: {name}")
                results[name] = False
            except Exception as e:
                logger.error(f"[SHUTDOWN] Cleanup failed: {name} - {e}")
                results[name] = False

        return results


# =============================================================================
# Shutdown Manager
# =============================================================================

class ShutdownManager:
    """
    Manages graceful shutdown of the application.

    Features:
    - Request tracking and draining
    - Configurable timeouts
    - Cleanup handler registry
    - Signal handling integration
    """

    _instance: Optional["ShutdownManager"] = None

    def __new__(cls, config: Optional[ShutdownConfig] = None):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[ShutdownConfig] = None):
        """Initialize shutdown manager.

        Args:
            config: Shutdown configuration
        """
        if self._initialized:
            return

        self.config = config or ShutdownConfig()
        self._state = ShutdownState.RUNNING
        self._tracker = RequestTracker()
        self._cleanup = CleanupRegistry()
        self._shutdown_reason: Optional[str] = None
        self._shutdown_started: Optional[float] = None
        self._initialized = True

    @property
    def state(self) -> ShutdownState:
        """Get current shutdown state."""
        return self._state

    @property
    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self._state != ShutdownState.RUNNING

    @property
    def in_flight_count(self) -> int:
        """Get number of in-flight requests."""
        return self._tracker.count

    def track_request(
        self,
        request_id: str,
        path: str = "",
        method: str = "",
    ) -> bool:
        """Track a new request.

        Args:
            request_id: Unique request identifier
            path: Request path
            method: HTTP method

        Returns:
            True if request was tracked, False if rejecting (shutdown)
        """
        if self.is_shutting_down:
            return False

        # Fire-and-forget tracking (non-blocking)
        asyncio.create_task(self._tracker.track(request_id, path, method))
        return True

    def untrack_request(self, request_id: str) -> None:
        """Stop tracking a request.

        Args:
            request_id: Request identifier
        """
        asyncio.create_task(self._tracker.untrack(request_id))

    def register_cleanup(
        self,
        name: str,
        handler: CleanupHandler,
        priority: int = 100,
    ) -> None:
        """Register a cleanup handler.

        Args:
            name: Handler name
            handler: Async cleanup function
            priority: Execution priority (lower = earlier)
        """
        self._cleanup.register(name, handler, priority)

    async def initiate_shutdown(self, reason: str = "shutdown requested") -> None:
        """
        Initiate graceful shutdown.

        1. Set state to DRAINING (reject new requests)
        2. Wait for in-flight requests to complete
        3. Run cleanup handlers
        4. Set state to STOPPED

        Args:
            reason: Reason for shutdown
        """
        if self._state != ShutdownState.RUNNING:
            logger.warning(f"[SHUTDOWN] Already shutting down, ignoring: {reason}")
            return

        self._shutdown_reason = reason
        self._shutdown_started = time.time()

        # Phase 1: Draining - change state FIRST to prevent concurrent shutdowns
        self._state = ShutdownState.DRAINING

        logger.info(f"[SHUTDOWN] Initiating graceful shutdown: {reason}")
        logger.info(f"[SHUTDOWN] {self._tracker.count} requests in flight")

        # Send alert (non-blocking to avoid delays)
        try:
            from app.services.alert_manager import get_alert_manager
            await get_alert_manager().shutdown_initiated(reason, self._tracker.count)
        except Exception:
            pass
        await self._drain_requests()

        # Phase 2: Cleanup
        self._state = ShutdownState.SHUTTING_DOWN
        await self._run_cleanup()

        # Phase 3: Done
        self._state = ShutdownState.STOPPED

        elapsed = time.time() - self._shutdown_started
        logger.info(f"[SHUTDOWN] Graceful shutdown complete in {elapsed:.1f}s")

    async def _drain_requests(self) -> None:
        """Wait for in-flight requests to complete."""
        start = time.time()
        timeout = self.config.drain_timeout_seconds

        while self._tracker.count > 0:
            elapsed = time.time() - start
            if elapsed >= timeout:
                logger.warning(
                    f"[SHUTDOWN] Drain timeout after {timeout}s. "
                    f"{self._tracker.count} requests still in flight."
                )
                # Log long-running requests
                for req in self._tracker.get_long_running(10.0):
                    logger.warning(
                        f"[SHUTDOWN] Long-running request: {req.request_id} "
                        f"({req.method} {req.path}) running for {time.time() - req.started_at:.1f}s"
                    )
                break

            remaining = self._tracker.count
            if remaining > 0:
                logger.info(f"[SHUTDOWN] Waiting for {remaining} requests ({elapsed:.1f}s elapsed)")

            await asyncio.sleep(self.config.check_interval_seconds)

    async def _run_cleanup(self) -> None:
        """Run cleanup handlers."""
        logger.info("[SHUTDOWN] Running cleanup handlers...")
        results = await self._cleanup.execute_all(
            timeout=self.config.cleanup_timeout_seconds
        )

        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        logger.info(f"[SHUTDOWN] Cleanup complete: {success_count}/{total_count} successful")

    def get_status(self) -> Dict[str, Any]:
        """Get shutdown manager status.

        Returns:
            Dict with state, in-flight count, etc.
        """
        return {
            "state": self._state.value,
            "is_shutting_down": self.is_shutting_down,
            "in_flight_requests": self._tracker.count,
            "shutdown_reason": self._shutdown_reason,
            "shutdown_started": self._shutdown_started,
            "config": {
                "drain_timeout_seconds": self.config.drain_timeout_seconds,
                "cleanup_timeout_seconds": self.config.cleanup_timeout_seconds,
            },
        }


# =============================================================================
# Signal Handler Integration
# =============================================================================

def setup_signal_handlers(shutdown_manager: ShutdownManager) -> None:
    """
    Setup signal handlers for graceful shutdown.

    Args:
        shutdown_manager: ShutdownManager instance
    """
    import signal

    def handle_signal(signum: int, frame: Any) -> None:
        """Handle shutdown signal."""
        signal_name = signal.Signals(signum).name
        logger.info(f"[SHUTDOWN] Received {signal_name}")

        # Create shutdown task
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(
                shutdown_manager.initiate_shutdown(f"Signal {signal_name}")
            )

    # Register handlers
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    logger.info("[SHUTDOWN] Signal handlers registered (SIGTERM, SIGINT)")


# =============================================================================
# Singleton Instance
# =============================================================================

_shutdown_manager: Optional[ShutdownManager] = None


def get_shutdown_manager() -> ShutdownManager:
    """Get singleton ShutdownManager instance."""
    global _shutdown_manager
    if _shutdown_manager is None:
        _shutdown_manager = ShutdownManager()
    return _shutdown_manager


def reset_shutdown_manager() -> None:
    """Reset shutdown manager (for testing)."""
    global _shutdown_manager
    ShutdownManager._instance = None
    _shutdown_manager = None
