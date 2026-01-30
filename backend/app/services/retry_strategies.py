"""
Tenacity-based Retry Strategies for External API Resilience

Provides standardized retry logic with:
- Exponential backoff with jitter
- Circuit breaker integration
- Provider-specific configurations
- Metrics and logging

Usage:
    @resilient_retry(RetryConfig.GEMINI)
    async def call_gemini_api():
        ...

    # With circuit breaker integration
    @resilient_retry(RetryConfig.NOTEBOOKLM, breaker=NOTEBOOKLM_BREAKER)
    async def call_notebooklm_api():
        ...
"""
from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Optional, Sequence, Type

from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Retry Configuration
# =============================================================================

@dataclass
class RetryStrategyConfig:
    """Configuration for a retry strategy."""
    max_attempts: int = 3
    initial_wait: float = 1.0  # seconds
    max_wait: float = 10.0  # seconds
    jitter: float = 2.0  # max random jitter in seconds
    retryable_exceptions: Sequence[Type[Exception]] = field(
        default_factory=lambda: (Exception,)
    )
    # Specific exceptions that should NOT trigger retry
    non_retryable_exceptions: Sequence[Type[Exception]] = field(
        default_factory=tuple
    )


class RetryConfig:
    """Pre-configured retry strategies for different providers."""

    # Gemini API: Fast LLM calls, moderate retry
    GEMINI = RetryStrategyConfig(
        max_attempts=3,
        initial_wait=1.0,
        max_wait=10.0,
        jitter=2.0,
        retryable_exceptions=(
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        ),
    )

    # NotebookLM: Browser-based, slower recovery
    NOTEBOOKLM = RetryStrategyConfig(
        max_attempts=2,
        initial_wait=2.0,
        max_wait=30.0,
        jitter=5.0,
        retryable_exceptions=(
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        ),
    )

    # Veo: Video generation, very slow operations
    VEO = RetryStrategyConfig(
        max_attempts=2,
        initial_wait=5.0,
        max_wait=60.0,
        jitter=10.0,
        retryable_exceptions=(
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        ),
    )

    # Kling: Video generation API
    KLING = RetryStrategyConfig(
        max_attempts=3,
        initial_wait=3.0,
        max_wait=30.0,
        jitter=5.0,
        retryable_exceptions=(
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        ),
    )

    # Qdrant: Vector database, fast recovery
    QDRANT = RetryStrategyConfig(
        max_attempts=3,
        initial_wait=0.5,
        max_wait=5.0,
        jitter=1.0,
        retryable_exceptions=(
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        ),
    )

    # Redis: Cache operations, very fast retry
    REDIS = RetryStrategyConfig(
        max_attempts=3,
        initial_wait=0.1,
        max_wait=1.0,
        jitter=0.2,
        retryable_exceptions=(
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        ),
    )

    # HTTP Default: General HTTP client calls
    HTTP_DEFAULT = RetryStrategyConfig(
        max_attempts=3,
        initial_wait=1.0,
        max_wait=10.0,
        jitter=2.0,
        retryable_exceptions=(
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        ),
    )


# =============================================================================
# Retry Callbacks
# =============================================================================

def _log_retry_attempt(retry_state: RetryCallState) -> None:
    """Log retry attempts for observability."""
    attempt = retry_state.attempt_number
    exception = retry_state.outcome.exception() if retry_state.outcome else None
    fn_name = getattr(retry_state.fn, "__name__", "unknown")

    if exception:
        logger.warning(
            f"[RETRY] {fn_name} attempt {attempt} failed: {type(exception).__name__}: {exception}"
        )
    else:
        logger.debug(f"[RETRY] {fn_name} attempt {attempt} starting")


def _log_retry_exhausted(retry_state: RetryCallState) -> None:
    """Log when all retries are exhausted."""
    fn_name = getattr(retry_state.fn, "__name__", "unknown")
    exception = retry_state.outcome.exception() if retry_state.outcome else None

    logger.error(
        f"[RETRY] {fn_name} exhausted after {retry_state.attempt_number} attempts. "
        f"Last error: {type(exception).__name__}: {exception}"
    )


# =============================================================================
# Circuit Breaker Integration
# =============================================================================

def _check_circuit_breaker(breaker: Any) -> None:
    """Check circuit breaker state before attempting call.

    Args:
        breaker: CircuitBreaker instance

    Raises:
        CircuitBreakerOpen: If circuit is open
    """
    if breaker is not None:
        breaker.check_state()


def _record_circuit_success(breaker: Any) -> None:
    """Record successful call in circuit breaker."""
    if breaker is not None:
        breaker.record_success()


def _record_circuit_failure(breaker: Any, error: Exception) -> None:
    """Record failed call in circuit breaker."""
    if breaker is not None:
        breaker.record_failure(error)


# =============================================================================
# Retry Decorator
# =============================================================================

def resilient_retry(
    config: RetryStrategyConfig,
    breaker: Optional[Any] = None,
    on_retry: Optional[Callable[[RetryCallState], None]] = None,
):
    """
    Decorator to wrap async functions with resilient retry logic.

    Features:
    - Exponential backoff with jitter
    - Circuit breaker integration
    - Configurable retry conditions
    - Comprehensive logging

    Args:
        config: RetryStrategyConfig with retry parameters
        breaker: Optional CircuitBreaker instance for integration
        on_retry: Optional callback for custom retry handling

    Usage:
        @resilient_retry(RetryConfig.GEMINI)
        async def call_gemini():
            ...

        @resilient_retry(RetryConfig.QDRANT, breaker=QDRANT_BREAKER)
        async def call_qdrant():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check circuit breaker before any attempts
            _check_circuit_breaker(breaker)

            # Build retry condition
            retry_condition = retry_if_exception_type(config.retryable_exceptions)

            # Configure retrying
            retrying = AsyncRetrying(
                stop=stop_after_attempt(config.max_attempts),
                wait=wait_exponential_jitter(
                    initial=config.initial_wait,
                    max=config.max_wait,
                    jitter=config.jitter,
                ),
                retry=retry_condition,
                before=_log_retry_attempt,
                after=on_retry or (lambda _: None),
                reraise=True,
            )

            try:
                async for attempt in retrying:
                    with attempt:
                        result = await func(*args, **kwargs)
                        _record_circuit_success(breaker)
                        return result
            except config.retryable_exceptions as e:
                _log_retry_exhausted(
                    RetryCallState(
                        retry_object=retrying,
                        fn=func,
                        args=args,
                        kwargs=kwargs,
                    )
                )
                _record_circuit_failure(breaker, e)
                raise
            except Exception as e:
                # Non-retryable exception - still record circuit failure
                _record_circuit_failure(breaker, e)
                raise

        return wrapper
    return decorator


def resilient_retry_sync(
    config: RetryStrategyConfig,
    breaker: Optional[Any] = None,
    on_retry: Optional[Callable[[RetryCallState], None]] = None,
):
    """
    Synchronous version of resilient_retry decorator.

    For use with synchronous functions.
    """
    from tenacity import Retrying

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _check_circuit_breaker(breaker)

            retry_condition = retry_if_exception_type(config.retryable_exceptions)

            retrying = Retrying(
                stop=stop_after_attempt(config.max_attempts),
                wait=wait_exponential_jitter(
                    initial=config.initial_wait,
                    max=config.max_wait,
                    jitter=config.jitter,
                ),
                retry=retry_condition,
                before=_log_retry_attempt,
                after=on_retry or (lambda _: None),
                reraise=True,
            )

            try:
                for attempt in retrying:
                    with attempt:
                        result = func(*args, **kwargs)
                        _record_circuit_success(breaker)
                        return result
            except config.retryable_exceptions as e:
                _record_circuit_failure(breaker, e)
                raise
            except Exception as e:
                _record_circuit_failure(breaker, e)
                raise

        return wrapper
    return decorator


# =============================================================================
# Contextual Retry (for inline use)
# =============================================================================

async def retry_operation(
    operation: Callable[..., Any],
    config: RetryStrategyConfig = RetryConfig.HTTP_DEFAULT,
    breaker: Optional[Any] = None,
    *args,
    **kwargs,
) -> Any:
    """
    Execute an operation with retry logic (inline version).

    Args:
        operation: Async callable to execute
        config: Retry configuration
        breaker: Optional circuit breaker
        *args, **kwargs: Arguments to pass to operation

    Returns:
        Result of operation

    Example:
        result = await retry_operation(
            fetch_data,
            config=RetryConfig.HTTP_DEFAULT,
            url="https://api.example.com/data",
        )
    """
    _check_circuit_breaker(breaker)

    retrying = AsyncRetrying(
        stop=stop_after_attempt(config.max_attempts),
        wait=wait_exponential_jitter(
            initial=config.initial_wait,
            max=config.max_wait,
            jitter=config.jitter,
        ),
        retry=retry_if_exception_type(config.retryable_exceptions),
        before=_log_retry_attempt,
        reraise=True,
    )

    try:
        async for attempt in retrying:
            with attempt:
                result = await operation(*args, **kwargs)
                _record_circuit_success(breaker)
                return result
    except Exception as e:
        _record_circuit_failure(breaker, e)
        raise


# =============================================================================
# Rate Limit Aware Retry
# =============================================================================

@dataclass
class RateLimitRetryConfig(RetryStrategyConfig):
    """Extended config for rate-limit-aware retry."""
    rate_limit_status_codes: Sequence[int] = field(
        default_factory=lambda: (429, 503)
    )
    rate_limit_initial_wait: float = 5.0
    rate_limit_max_wait: float = 60.0


def is_rate_limited(exception: Exception) -> bool:
    """Check if exception indicates rate limiting."""
    error_str = str(exception).lower()
    return any(term in error_str for term in ("429", "rate", "quota", "throttle"))


def resilient_retry_with_rate_limit(
    config: RateLimitRetryConfig,
    breaker: Optional[Any] = None,
):
    """
    Decorator with special handling for rate limits.

    When rate limited, uses longer backoff periods.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            _check_circuit_breaker(breaker)

            attempt_count = 0
            last_error = None

            while attempt_count < config.max_attempts:
                attempt_count += 1
                try:
                    result = await func(*args, **kwargs)
                    _record_circuit_success(breaker)
                    return result
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"[RETRY] {func.__name__} attempt {attempt_count} failed: {e}"
                    )

                    if not isinstance(e, config.retryable_exceptions):
                        _record_circuit_failure(breaker, e)
                        raise

                    if attempt_count >= config.max_attempts:
                        break

                    # Determine wait time based on error type
                    if is_rate_limited(e):
                        wait_time = min(
                            config.rate_limit_initial_wait * (2 ** (attempt_count - 1)),
                            config.rate_limit_max_wait,
                        )
                        logger.info(
                            f"[RETRY] Rate limited, waiting {wait_time}s before retry"
                        )
                    else:
                        wait_time = min(
                            config.initial_wait * (2 ** (attempt_count - 1)),
                            config.max_wait,
                        )
                        # Add jitter
                        wait_time += random.uniform(0, config.jitter)

                    await asyncio.sleep(wait_time)

            _record_circuit_failure(breaker, last_error)
            raise last_error

        return wrapper
    return decorator


# =============================================================================
# Convenience Decorators
# =============================================================================

# Pre-configured decorators for common providers
gemini_retry = resilient_retry(RetryConfig.GEMINI)
notebooklm_retry = resilient_retry(RetryConfig.NOTEBOOKLM)
veo_retry = resilient_retry(RetryConfig.VEO)
kling_retry = resilient_retry(RetryConfig.KLING)
qdrant_retry = resilient_retry(RetryConfig.QDRANT)
redis_retry = resilient_retry(RetryConfig.REDIS)
http_retry = resilient_retry(RetryConfig.HTTP_DEFAULT)


def get_retry_config(provider: str) -> RetryStrategyConfig:
    """Get retry config for a provider name.

    Args:
        provider: Provider name (gemini, notebooklm, veo, kling, qdrant, redis)

    Returns:
        RetryStrategyConfig for the provider
    """
    configs = {
        "gemini": RetryConfig.GEMINI,
        "notebooklm": RetryConfig.NOTEBOOKLM,
        "veo": RetryConfig.VEO,
        "kling": RetryConfig.KLING,
        "qdrant": RetryConfig.QDRANT,
        "redis": RetryConfig.REDIS,
        "http": RetryConfig.HTTP_DEFAULT,
    }
    return configs.get(provider.lower(), RetryConfig.HTTP_DEFAULT)
