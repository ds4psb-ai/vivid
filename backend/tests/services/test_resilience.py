"""Tests for Resilience service (Phase 5.5).

Tests cover:
- Circuit Breaker state transitions
- Retry with exponential backoff
- Resilient executor combination
- Provider registry
"""
import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.services.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
    RetryConfig,
    RetryExhaustedError,
    ResilientExecutor,
    ProviderRegistry,
    calculate_backoff_delay,
    retry_with_backoff,
    retry_with_backoff_async,
    get_provider_registry,
)


# =============================================================================
# Circuit Breaker Tests
# =============================================================================


class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig."""

    def test_default_config(self):
        """Default config should have sensible values."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.recovery_timeout == 60.0
        assert config.half_open_max_calls == 3

    def test_custom_config(self):
        """Should accept custom values."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=1,
            recovery_timeout=30.0,
        )
        assert config.failure_threshold == 3
        assert config.recovery_timeout == 30.0


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    @pytest.fixture
    def breaker(self):
        return CircuitBreaker("test-api")

    def test_initial_state_closed(self, breaker):
        """Initial state should be CLOSED."""
        assert breaker.state == CircuitState.CLOSED
        assert breaker.can_execute() is True

    def test_record_success_resets_failure_count(self, breaker):
        """Success should reset failure count."""
        breaker.record_failure()
        breaker.record_failure()
        assert breaker._failure_count == 2

        breaker.record_success()
        assert breaker._failure_count == 0

    def test_opens_after_threshold_failures(self, breaker):
        """Should open after failure_threshold failures."""
        for _ in range(5):
            breaker.record_failure()

        assert breaker.state == CircuitState.OPEN
        assert breaker.can_execute() is False

    def test_blocks_calls_when_open(self, breaker):
        """Should block calls when OPEN."""
        # Force open
        for _ in range(5):
            breaker.record_failure()

        assert breaker.can_execute() is False
        assert breaker.retry_after > 0

    def test_transitions_to_half_open_after_timeout(self, breaker):
        """Should transition to HALF_OPEN after recovery_timeout."""
        breaker.config.recovery_timeout = 0.01  # 10ms

        # Open the circuit
        for _ in range(5):
            breaker.record_failure()
        assert breaker._state == CircuitState.OPEN

        # Wait for recovery timeout
        import time
        time.sleep(0.02)

        # Check state triggers transition
        assert breaker.state == CircuitState.HALF_OPEN
        assert breaker.can_execute() is True

    def test_half_open_limits_calls(self):
        """Should limit calls in HALF_OPEN state."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.01,
            half_open_max_calls=2,
        )
        breaker = CircuitBreaker("test", config)

        # Open circuit
        breaker.record_failure()
        breaker.record_failure()

        # Wait for half-open
        import time
        time.sleep(0.02)
        assert breaker.state == CircuitState.HALF_OPEN

        # First 2 calls allowed
        assert breaker.can_execute() is True
        breaker.record_success()
        assert breaker.can_execute() is True
        breaker.record_success()

        # Circuit should be closed now (success_threshold=2)
        assert breaker.state == CircuitState.CLOSED

    def test_half_open_failure_reopens(self):
        """Failure in HALF_OPEN should reopen circuit."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.01,
        )
        breaker = CircuitBreaker("test", config)

        # Open circuit
        breaker.record_failure()
        breaker.record_failure()

        # Wait for half-open
        import time
        time.sleep(0.02)
        assert breaker.state == CircuitState.HALF_OPEN

        # Record failure - should reopen
        breaker.record_failure()
        assert breaker._state == CircuitState.OPEN

    def test_reset_clears_state(self, breaker):
        """Reset should clear all state."""
        for _ in range(5):
            breaker.record_failure()
        assert breaker._state == CircuitState.OPEN

        breaker.reset()
        assert breaker.state == CircuitState.CLOSED
        assert breaker._failure_count == 0

    def test_get_metrics(self, breaker):
        """Should return metrics dict."""
        breaker.record_success()
        breaker.record_failure()

        metrics = breaker.get_metrics()
        assert metrics["name"] == "test-api"
        assert metrics["state"] == "closed"
        assert metrics["total_calls"] == 2
        assert metrics["total_failures"] == 1


# =============================================================================
# Retry with Backoff Tests
# =============================================================================


class TestCalculateBackoffDelay:
    """Tests for calculate_backoff_delay."""

    def test_exponential_growth(self):
        """Delay should grow exponentially."""
        delay_0 = calculate_backoff_delay(0, base_delay=1.0, jitter=False)
        delay_1 = calculate_backoff_delay(1, base_delay=1.0, jitter=False)
        delay_2 = calculate_backoff_delay(2, base_delay=1.0, jitter=False)

        assert delay_0 == 1.0
        assert delay_1 == 2.0
        assert delay_2 == 4.0

    def test_max_delay_cap(self):
        """Delay should not exceed max_delay."""
        delay = calculate_backoff_delay(
            10,  # Would be 1024 without cap
            base_delay=1.0,
            max_delay=60.0,
            jitter=False,
        )
        assert delay == 60.0

    def test_jitter_adds_randomness(self):
        """Jitter should add randomness."""
        delays = [
            calculate_backoff_delay(0, base_delay=1.0, jitter=True)
            for _ in range(10)
        ]
        # With jitter, delays should vary
        assert len(set(delays)) > 1


class TestRetryWithBackoff:
    """Tests for retry_with_backoff."""

    @pytest.mark.asyncio
    async def test_succeeds_on_first_try(self):
        """Should return immediately on success."""
        call_count = 0

        async def succeed():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await retry_with_backoff_async(succeed)
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_failure(self):
        """Should retry on failure."""
        call_count = 0

        async def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "success"

        config = RetryConfig(max_retries=3, base_delay=0.01)
        result = await retry_with_backoff_async(fail_twice, config=config)

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self):
        """Should raise RetryExhaustedError after max retries."""
        async def always_fail():
            raise ValueError("always fails")

        config = RetryConfig(max_retries=2, base_delay=0.01)

        with pytest.raises(RetryExhaustedError) as exc_info:
            await retry_with_backoff_async(always_fail, config=config)

        assert exc_info.value.attempts == 3  # Initial + 2 retries
        assert isinstance(exc_info.value.last_exception, ValueError)

    @pytest.mark.asyncio
    async def test_decorator_async(self):
        """Should work as decorator for async functions."""
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("fail")
            return "success"

        result = await flaky_func()
        assert result == "success"
        assert call_count == 2

    def test_decorator_sync(self):
        """Should work as decorator for sync functions."""
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("fail")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 2


# =============================================================================
# Resilient Executor Tests
# =============================================================================


class TestResilientExecutor:
    """Tests for ResilientExecutor."""

    @pytest.fixture
    def executor(self):
        return ResilientExecutor(
            "test-executor",
            circuit_config=CircuitBreakerConfig(failure_threshold=3),
            retry_config=RetryConfig(max_retries=2, base_delay=0.01),
        )

    @pytest.mark.asyncio
    async def test_execute_success(self, executor):
        """Should execute successfully."""
        async def success():
            return "ok"

        result = await executor.execute(success)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_execute_with_retry(self, executor):
        """Should retry on failure."""
        call_count = 0

        async def fail_once():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("fail")
            return "ok"

        result = await executor.execute(fail_once)
        assert result == "ok"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self, executor):
        """Circuit should open after repeated failures."""
        async def always_fail():
            raise ValueError("fail")

        # Exhaust retries multiple times to trip circuit
        for _ in range(3):
            try:
                await executor.execute(always_fail)
            except (RetryExhaustedError, CircuitBreakerOpenError):
                pass

        # Circuit should now be open
        assert executor.circuit_breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_raises_circuit_open_error(self, executor):
        """Should raise CircuitBreakerOpenError when circuit open."""
        # Force circuit open
        for _ in range(3):
            executor.circuit_breaker.record_failure()

        async def any_func():
            return "ok"

        with pytest.raises(CircuitBreakerOpenError):
            await executor.execute(any_func)

    def test_get_metrics(self, executor):
        """Should return combined metrics."""
        metrics = executor.get_metrics()
        assert "name" in metrics
        assert "circuit_breaker" in metrics
        assert "retry_config" in metrics


# =============================================================================
# Provider Registry Tests
# =============================================================================


class TestProviderRegistry:
    """Tests for ProviderRegistry."""

    @pytest.fixture
    def registry(self):
        registry = ProviderRegistry()
        registry.register("gemini")
        registry.register("openai")
        return registry

    def test_register_provider(self, registry):
        """Should register providers."""
        assert registry.get("gemini") is not None
        assert registry.get("openai") is not None
        assert registry.get("unknown") is None

    def test_get_healthy_provider(self, registry):
        """Should return first healthy provider."""
        provider = registry.get_healthy_provider(["gemini", "openai"])
        assert provider == "gemini"

    def test_get_healthy_provider_skips_unhealthy(self, registry):
        """Should skip unhealthy providers."""
        # Make gemini unhealthy
        gemini = registry.get("gemini")
        for _ in range(5):
            gemini.circuit_breaker.record_failure()

        provider = registry.get_healthy_provider(["gemini", "openai"])
        assert provider == "openai"

    def test_get_healthy_provider_none_available(self, registry):
        """Should return None if no healthy providers."""
        # Make all unhealthy
        for name in ["gemini", "openai"]:
            executor = registry.get(name)
            for _ in range(5):
                executor.circuit_breaker.record_failure()

        provider = registry.get_healthy_provider(["gemini", "openai"])
        assert provider is None

    def test_get_all_metrics(self, registry):
        """Should return metrics for all providers."""
        metrics = registry.get_all_metrics()
        assert "gemini" in metrics
        assert "openai" in metrics


class TestProviderRegistrySingleton:
    """Tests for singleton pattern."""

    def test_get_provider_registry_returns_same_instance(self):
        """Should return same instance."""
        reg1 = get_provider_registry()
        reg2 = get_provider_registry()
        assert reg1 is reg2
