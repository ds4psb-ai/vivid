"""Resilience patterns for LLM API calls (Phase 5.5).

Implements Circuit Breaker and Retry with Exponential Backoff.

2026 Best Practices:
- Circuit breakers prevent cascading failures
- Exponential backoff with jitter prevents thundering herd
- Provider isolation allows graceful degradation

References:
- Portkey: https://portkey.ai/blog/retries-fallbacks-and-circuit-breakers-in-llm-apps/
- resilient-llm: https://github.com/gitcommitshow/resilient-llm

Usage:
    from app.services.resilience import CircuitBreaker, retry_with_backoff

    # Circuit Breaker
    breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

    if breaker.can_execute():
        try:
            result = await call_llm_api()
            breaker.record_success()
        except Exception as e:
            breaker.record_failure()
            raise

    # Retry with Backoff
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    async def call_llm_api():
        ...
"""
from __future__ import annotations

import asyncio
import functools
import logging
import random
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, TypeVar

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

T = TypeVar("T")


# =============================================================================
# Circuit Breaker
# =============================================================================


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, requests allowed
    OPEN = "open"  # Failure threshold exceeded, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration."""

    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes in half-open to close
    recovery_timeout: float = 60.0  # Seconds before half-open
    half_open_max_calls: int = 3  # Max calls in half-open state


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, breaker_name: str, retry_after: float):
        self.breaker_name = breaker_name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker '{breaker_name}' is open. Retry after {retry_after:.1f}s"
        )


class CircuitBreaker:
    """Circuit breaker for LLM API calls.

    State transitions:
    - CLOSED → OPEN: When failure_threshold reached
    - OPEN → HALF_OPEN: After recovery_timeout
    - HALF_OPEN → CLOSED: When success_threshold reached
    - HALF_OPEN → OPEN: On any failure

    Usage:
        breaker = CircuitBreaker("gemini-api")

        async def call_api():
            if not breaker.can_execute():
                raise CircuitBreakerOpenError(breaker.name, breaker.retry_after)

            try:
                result = await actual_api_call()
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise
    """

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: datetime | None = None
        self._half_open_calls = 0

        # Metrics
        self._total_calls = 0
        self._total_failures = 0
        self._total_blocked = 0

    @property
    def state(self) -> CircuitState:
        """Get current state, checking for recovery timeout."""
        if self._state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self._transition_to(CircuitState.HALF_OPEN)
        return self._state

    @property
    def retry_after(self) -> float:
        """Seconds until circuit might close."""
        if self._state != CircuitState.OPEN:
            return 0.0
        if self._last_failure_time is None:
            return 0.0

        elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
        return max(0.0, self.config.recovery_timeout - elapsed)

    def can_execute(self) -> bool:
        """Check if a call can be executed."""
        current_state = self.state  # Triggers state check

        if current_state == CircuitState.CLOSED:
            return True

        if current_state == CircuitState.HALF_OPEN:
            if self._half_open_calls < self.config.half_open_max_calls:
                return True
            return False

        # OPEN state
        return False

    def record_success(self) -> None:
        """Record a successful call."""
        self._total_calls += 1

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            self._half_open_calls += 1

            if self._success_count >= self.config.success_threshold:
                self._transition_to(CircuitState.CLOSED)
        else:
            # Reset failure count on success in CLOSED state
            self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        self._total_calls += 1
        self._total_failures += 1
        self._last_failure_time = datetime.utcnow()

        if self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open reopens the circuit
            self._transition_to(CircuitState.OPEN)
            self._half_open_calls += 1
        else:
            self._failure_count += 1

            if self._failure_count >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)

    def _should_attempt_recovery(self) -> bool:
        """Check if recovery timeout has passed."""
        if self._last_failure_time is None:
            return True

        elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
        return elapsed >= self.config.recovery_timeout

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        old_state = self._state
        self._state = new_state

        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._success_count = 0
            self._half_open_calls = 0
        elif new_state == CircuitState.OPEN:
            self._total_blocked += 1

        logger.info(
            f"Circuit breaker '{self.name}' transitioned: {old_state.value} → {new_state.value}"
        )

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0
        logger.info(f"Circuit breaker '{self.name}' reset to CLOSED")

    def get_metrics(self) -> dict[str, Any]:
        """Get circuit breaker metrics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "total_calls": self._total_calls,
            "total_failures": self._total_failures,
            "total_blocked": self._total_blocked,
            "retry_after": self.retry_after,
        }


# =============================================================================
# Retry with Exponential Backoff
# =============================================================================


class RetryConfig(BaseModel):
    """Retry configuration."""

    max_retries: int = 3
    base_delay: float = 1.0  # Initial delay in seconds
    max_delay: float = 60.0  # Maximum delay cap
    exponential_base: float = 2.0  # Multiplier for exponential backoff
    jitter: bool = True  # Add random jitter to prevent thundering herd
    retryable_exceptions: tuple[type[Exception], ...] = Field(
        default=(Exception,), exclude=True
    )


class RetryExhaustedError(Exception):
    """Raised when all retries are exhausted."""

    def __init__(self, attempts: int, last_exception: Exception):
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(
            f"All {attempts} retry attempts exhausted. Last error: {last_exception}"
        )


def calculate_backoff_delay(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
) -> float:
    """Calculate delay for exponential backoff with optional jitter.

    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        exponential_base: Multiplier for exponential growth
        jitter: Add random jitter (0-100% of delay)

    Returns:
        Delay in seconds
    """
    # Exponential backoff: base_delay * (exponential_base ^ attempt)
    delay = base_delay * (exponential_base**attempt)

    # Cap at max_delay
    delay = min(delay, max_delay)

    # Add jitter (0 to 100% of delay)
    if jitter:
        delay = delay * (0.5 + random.random())

    return delay


async def retry_with_backoff_async(
    func: Callable[..., Any],
    *args: Any,
    config: RetryConfig | None = None,
    **kwargs: Any,
) -> Any:
    """Execute async function with retry and exponential backoff.

    Args:
        func: Async function to execute
        *args: Positional arguments for func
        config: Retry configuration
        **kwargs: Keyword arguments for func

    Returns:
        Result from func

    Raises:
        RetryExhaustedError: When all retries exhausted
    """
    config = config or RetryConfig()
    last_exception: Exception | None = None

    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except config.retryable_exceptions as e:
            last_exception = e

            if attempt == config.max_retries:
                # Last attempt failed
                break

            delay = calculate_backoff_delay(
                attempt=attempt,
                base_delay=config.base_delay,
                max_delay=config.max_delay,
                exponential_base=config.exponential_base,
                jitter=config.jitter,
            )

            logger.warning(
                f"Attempt {attempt + 1}/{config.max_retries + 1} failed: {e}. "
                f"Retrying in {delay:.2f}s..."
            )

            await asyncio.sleep(delay)

    raise RetryExhaustedError(config.max_retries + 1, last_exception)  # type: ignore


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retry with exponential backoff.

    Usage:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        async def call_api():
            return await api.call()

    Args:
        max_retries: Maximum number of retries
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        exponential_base: Multiplier for exponential growth
        jitter: Add random jitter
        retryable_exceptions: Exceptions to retry on

    Returns:
        Decorated function
    """
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        retryable_exceptions=retryable_exceptions,
    )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_with_backoff_async(func, *args, config=config, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            # For sync functions, use sync retry
            last_exception: Exception | None = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e

                    if attempt == config.max_retries:
                        break

                    delay = calculate_backoff_delay(
                        attempt=attempt,
                        base_delay=config.base_delay,
                        max_delay=config.max_delay,
                        exponential_base=config.exponential_base,
                        jitter=config.jitter,
                    )

                    logger.warning(
                        f"Attempt {attempt + 1}/{config.max_retries + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    time.sleep(delay)

            raise RetryExhaustedError(config.max_retries + 1, last_exception)  # type: ignore

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


# =============================================================================
# Combined Resilient Executor
# =============================================================================


class ResilientExecutor:
    """Combines circuit breaker and retry for resilient execution.

    Usage:
        executor = ResilientExecutor("gemini-api")

        result = await executor.execute(
            call_llm_api,
            prompt="Hello",
        )
    """

    def __init__(
        self,
        name: str,
        circuit_config: CircuitBreakerConfig | None = None,
        retry_config: RetryConfig | None = None,
    ):
        self.name = name
        self.circuit_breaker = CircuitBreaker(name, circuit_config)
        self.retry_config = retry_config or RetryConfig()

    async def execute(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute function with circuit breaker and retry.

        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result from func

        Raises:
            CircuitBreakerOpenError: If circuit is open
            RetryExhaustedError: If all retries fail
        """
        if not self.circuit_breaker.can_execute():
            raise CircuitBreakerOpenError(
                self.name, self.circuit_breaker.retry_after
            )

        async def wrapped() -> Any:
            try:
                result = await func(*args, **kwargs)
                self.circuit_breaker.record_success()
                return result
            except Exception as e:
                self.circuit_breaker.record_failure()
                raise

        return await retry_with_backoff_async(wrapped, config=self.retry_config)

    def get_metrics(self) -> dict[str, Any]:
        """Get executor metrics."""
        return {
            "name": self.name,
            "circuit_breaker": self.circuit_breaker.get_metrics(),
            "retry_config": {
                "max_retries": self.retry_config.max_retries,
                "base_delay": self.retry_config.base_delay,
            },
        }


# =============================================================================
# Provider Registry (Multi-Provider Support)
# =============================================================================


class ProviderRegistry:
    """Registry of circuit breakers for multiple LLM providers.

    Usage:
        registry = ProviderRegistry()
        registry.register("gemini", CircuitBreakerConfig(failure_threshold=5))
        registry.register("openai", CircuitBreakerConfig(failure_threshold=3))

        # Get healthy provider
        provider = registry.get_healthy_provider(["gemini", "openai"])
    """

    def __init__(self):
        self._executors: dict[str, ResilientExecutor] = {}

    def register(
        self,
        provider_name: str,
        circuit_config: CircuitBreakerConfig | None = None,
        retry_config: RetryConfig | None = None,
    ) -> ResilientExecutor:
        """Register a provider with resilience configuration."""
        executor = ResilientExecutor(provider_name, circuit_config, retry_config)
        self._executors[provider_name] = executor
        logger.info(f"Registered provider: {provider_name}")
        return executor

    def get(self, provider_name: str) -> ResilientExecutor | None:
        """Get executor for a provider."""
        return self._executors.get(provider_name)

    def get_healthy_provider(
        self,
        preferred_order: list[str],
    ) -> str | None:
        """Get first healthy provider from preferred list.

        Args:
            preferred_order: List of provider names in preference order

        Returns:
            First healthy provider name, or None if all unhealthy
        """
        for provider_name in preferred_order:
            executor = self._executors.get(provider_name)
            if executor and executor.circuit_breaker.can_execute():
                return provider_name

        return None

    def get_all_metrics(self) -> dict[str, Any]:
        """Get metrics for all providers."""
        return {
            name: executor.get_metrics()
            for name, executor in self._executors.items()
        }


# Singleton registry
_default_registry: ProviderRegistry | None = None


def get_provider_registry() -> ProviderRegistry:
    """Get default provider registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ProviderRegistry()
    return _default_registry
