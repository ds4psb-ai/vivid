"""
Circuit Breaker Tests

Tests for the circuit breaker pattern implementation including:
- State transitions (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)
- Failure threshold behavior
- Recovery timeout behavior
- Thread safety with async operations
"""
import asyncio
import pytest
import time
from unittest.mock import MagicMock, patch

from app.services.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpen,
    CircuitState,
    GEMINI_BREAKER,
    QDRANT_BREAKER,
    NOTEBOOKLM_BREAKER,
    VEO_BREAKER,
    with_circuit_breaker,
    get_circuit_health,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def fresh_breaker():
    """Create a fresh circuit breaker for testing."""
    # Generate unique name to avoid singleton conflicts
    name = f"test_breaker_{time.time()}"
    config = CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout_seconds=1.0,  # Short timeout for testing
        half_open_max_calls=2,
    )
    breaker = CircuitBreaker(name, config)
    yield breaker
    # Cleanup
    if name in CircuitBreaker._instances:
        del CircuitBreaker._instances[name]


@pytest.fixture
def quick_breaker():
    """Create a breaker with very short timeouts for testing."""
    name = f"quick_breaker_{time.time()}"
    config = CircuitBreakerConfig(
        failure_threshold=2,
        success_threshold=1,
        timeout_seconds=0.1,  # Very short for testing
        half_open_max_calls=1,
    )
    breaker = CircuitBreaker(name, config)
    yield breaker
    if name in CircuitBreaker._instances:
        del CircuitBreaker._instances[name]


# =============================================================================
# State Transition Tests
# =============================================================================

class TestStateTransitions:
    """Test circuit breaker state transitions."""

    def test_initial_state_is_closed(self, fresh_breaker):
        """Test that circuit starts in CLOSED state."""
        assert fresh_breaker.state == CircuitState.CLOSED

    def test_stays_closed_on_success(self, fresh_breaker):
        """Test that circuit stays closed on successful calls."""
        fresh_breaker.record_success()
        assert fresh_breaker.state == CircuitState.CLOSED

    def test_opens_after_failure_threshold(self, fresh_breaker):
        """Test that circuit opens after reaching failure threshold."""
        # Record failures up to threshold
        for _ in range(fresh_breaker.config.failure_threshold):
            fresh_breaker.record_failure(Exception("test"))

        assert fresh_breaker.state == CircuitState.OPEN

    def test_transitions_to_half_open_after_timeout(self, quick_breaker):
        """Test that circuit transitions to HALF_OPEN after timeout."""
        # Trip the circuit
        for _ in range(quick_breaker.config.failure_threshold):
            quick_breaker.record_failure(Exception("test"))
        assert quick_breaker.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(0.15)

        # Check state (should transition to HALF_OPEN)
        assert quick_breaker.state == CircuitState.HALF_OPEN

    def test_closes_after_success_threshold_in_half_open(self, quick_breaker):
        """Test that circuit closes after success threshold in HALF_OPEN."""
        # Trip and wait for half-open
        for _ in range(quick_breaker.config.failure_threshold):
            quick_breaker.record_failure(Exception("test"))
        time.sleep(0.15)
        assert quick_breaker.state == CircuitState.HALF_OPEN

        # Record successes
        for _ in range(quick_breaker.config.success_threshold):
            quick_breaker.record_success()

        assert quick_breaker.state == CircuitState.CLOSED

    def test_reopens_on_failure_in_half_open(self, quick_breaker):
        """Test that circuit reopens on failure in HALF_OPEN."""
        # Trip and wait for half-open
        for _ in range(quick_breaker.config.failure_threshold):
            quick_breaker.record_failure(Exception("test"))
        time.sleep(0.15)
        assert quick_breaker.state == CircuitState.HALF_OPEN

        # Record failure
        quick_breaker.record_failure(Exception("test"))

        assert quick_breaker.state == CircuitState.OPEN


# =============================================================================
# Check State Tests
# =============================================================================

class TestCheckState:
    """Test check_state() method behavior."""

    def test_allows_call_when_closed(self, fresh_breaker):
        """Test that check_state allows calls when closed."""
        # Should not raise
        fresh_breaker.check_state()

    def test_raises_when_open(self, fresh_breaker):
        """Test that check_state raises when circuit is open."""
        # Trip the circuit
        for _ in range(fresh_breaker.config.failure_threshold):
            fresh_breaker.record_failure(Exception("test"))

        with pytest.raises(CircuitBreakerOpen) as exc_info:
            fresh_breaker.check_state()

        assert fresh_breaker.name in str(exc_info.value)

    def test_allows_limited_calls_in_half_open(self, quick_breaker):
        """Test that check_state allows limited calls in HALF_OPEN."""
        # Trip and wait for half-open
        for _ in range(quick_breaker.config.failure_threshold):
            quick_breaker.record_failure(Exception("test"))
        time.sleep(0.15)

        # Should allow first call
        quick_breaker.check_state()

        # Should raise on exceeding half_open_max_calls
        with pytest.raises(CircuitBreakerOpen):
            quick_breaker.check_state()


# =============================================================================
# Status and Monitoring Tests
# =============================================================================

class TestStatusMonitoring:
    """Test status and monitoring methods."""

    def test_get_status_returns_correct_info(self, fresh_breaker):
        """Test that get_status returns correct information."""
        status = fresh_breaker.get_status()

        assert status["name"] == fresh_breaker.name
        assert status["state"] == "closed"
        assert status["failure_count"] == 0
        assert status["success_count"] == 0
        assert "config" in status

    def test_get_status_after_failures(self, fresh_breaker):
        """Test status after recording failures."""
        fresh_breaker.record_failure(Exception("test"))
        fresh_breaker.record_failure(Exception("test"))

        status = fresh_breaker.get_status()

        assert status["failure_count"] == 2
        assert status["state"] == "closed"  # Not yet tripped

    def test_get_all_status_includes_all_breakers(self):
        """Test that get_all_status includes all registered breakers."""
        all_status = CircuitBreaker.get_all_status()

        # Should include pre-configured breakers
        assert "gemini_api" in all_status
        assert "qdrant" in all_status

    def test_get_circuit_health_healthy(self):
        """Test circuit health when all circuits are healthy."""
        # Reset all breakers
        for name, breaker in CircuitBreaker._instances.items():
            CircuitBreaker.reset(name)

        health = get_circuit_health()

        assert health["healthy"] is True
        assert len(health["open_circuits"]) == 0


# =============================================================================
# Decorator Tests
# =============================================================================

class TestDecorator:
    """Test with_circuit_breaker decorator."""

    @pytest.mark.asyncio
    async def test_decorator_records_success(self):
        """Test that decorator records success."""
        name = f"decorator_test_{time.time()}"
        call_count = 0

        @with_circuit_breaker(name)
        async def successful_call():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_call()

        assert result == "success"
        assert call_count == 1

        # Check breaker state
        breaker = CircuitBreaker._instances[name]
        assert breaker.state == CircuitState.CLOSED

        # Cleanup
        del CircuitBreaker._instances[name]

    @pytest.mark.asyncio
    async def test_decorator_records_failure(self):
        """Test that decorator records failure."""
        name = f"decorator_fail_test_{time.time()}"

        @with_circuit_breaker(
            name,
            CircuitBreakerConfig(failure_threshold=2, timeout_seconds=1.0)
        )
        async def failing_call():
            raise ValueError("test error")

        # First failure
        with pytest.raises(ValueError):
            await failing_call()

        # Second failure - should trip
        with pytest.raises(ValueError):
            await failing_call()

        # Third call - should raise CircuitBreakerOpen
        with pytest.raises(CircuitBreakerOpen):
            await failing_call()

        # Cleanup
        del CircuitBreaker._instances[name]

    @pytest.mark.asyncio
    async def test_decorator_allows_calls_after_recovery(self):
        """Test that decorator allows calls after circuit recovers."""
        name = f"decorator_recovery_test_{time.time()}"

        @with_circuit_breaker(
            name,
            CircuitBreakerConfig(
                failure_threshold=1,
                success_threshold=1,
                timeout_seconds=0.1,
            )
        )
        async def call_that_fails_then_succeeds():
            return "success"

        # Trip the circuit manually
        breaker = CircuitBreaker._instances[name]
        breaker.record_failure(Exception("test"))

        # Wait for half-open
        await asyncio.sleep(0.15)

        # Should succeed now
        result = await call_that_fails_then_succeeds()
        assert result == "success"

        # Cleanup
        del CircuitBreaker._instances[name]


# =============================================================================
# Pre-configured Breakers Tests
# =============================================================================

class TestPreConfiguredBreakers:
    """Test pre-configured circuit breakers."""

    def test_gemini_breaker_exists(self):
        """Test that GEMINI_BREAKER is configured."""
        assert GEMINI_BREAKER is not None
        assert GEMINI_BREAKER.name == "gemini_api"
        assert GEMINI_BREAKER.config.failure_threshold == 3

    def test_qdrant_breaker_exists(self):
        """Test that QDRANT_BREAKER is configured."""
        assert QDRANT_BREAKER is not None
        assert QDRANT_BREAKER.name == "qdrant"
        assert QDRANT_BREAKER.config.failure_threshold == 3

    def test_notebooklm_breaker_exists(self):
        """Test that NOTEBOOKLM_BREAKER is configured."""
        assert NOTEBOOKLM_BREAKER is not None
        assert NOTEBOOKLM_BREAKER.name == "notebooklm"

    def test_veo_breaker_exists(self):
        """Test that VEO_BREAKER is configured."""
        assert VEO_BREAKER is not None
        assert VEO_BREAKER.name == "veo"
        assert VEO_BREAKER.config.timeout_seconds == 120.0

    def test_breakers_are_singletons(self):
        """Test that breakers are singletons."""
        breaker1 = CircuitBreaker("gemini_api")
        breaker2 = CircuitBreaker("gemini_api")

        assert breaker1 is breaker2

    def test_reset_breaker(self):
        """Test manual reset of a breaker."""
        # Trip GEMINI_BREAKER
        for _ in range(GEMINI_BREAKER.config.failure_threshold):
            GEMINI_BREAKER.record_failure(Exception("test"))

        assert GEMINI_BREAKER.state == CircuitState.OPEN

        # Reset
        CircuitBreaker.reset("gemini_api")

        assert GEMINI_BREAKER.state == CircuitState.CLOSED


# =============================================================================
# Concurrency Tests
# =============================================================================

class TestConcurrency:
    """Test circuit breaker behavior under concurrent access."""

    @pytest.mark.asyncio
    async def test_concurrent_failures(self, fresh_breaker):
        """Test circuit behavior under concurrent failures."""
        async def record_failure():
            fresh_breaker.record_failure(Exception("concurrent"))

        # Record failures concurrently
        await asyncio.gather(*[record_failure() for _ in range(10)])

        # Should be open after threshold
        assert fresh_breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_concurrent_check_and_record(self, fresh_breaker):
        """Test concurrent check_state and record operations."""
        errors = []

        async def check_and_maybe_fail(should_fail: bool):
            try:
                fresh_breaker.check_state()
                if should_fail:
                    fresh_breaker.record_failure(Exception("test"))
                else:
                    fresh_breaker.record_success()
            except CircuitBreakerOpen:
                errors.append("open")

        # Mix of success and failure
        tasks = [
            check_and_maybe_fail(i % 2 == 0) for i in range(20)
        ]
        await asyncio.gather(*tasks)

        # Should have some "open" errors if circuit tripped
        # The exact behavior depends on timing
        assert fresh_breaker.state in [CircuitState.CLOSED, CircuitState.OPEN]
