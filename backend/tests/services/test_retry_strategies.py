"""
Tests for retry_strategies module.

Tests cover:
- RetryConfig presets
- resilient_retry decorator
- Circuit breaker integration
- Rate limit handling
- Sync and async variants
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.retry_strategies import (
    RetryConfig,
    RetryStrategyConfig,
    RateLimitRetryConfig,
    resilient_retry,
    resilient_retry_sync,
    resilient_retry_with_rate_limit,
    retry_operation,
    is_rate_limited,
    get_retry_config,
    gemini_retry,
    qdrant_retry,
)


# =============================================================================
# RetryConfig Tests
# =============================================================================

class TestRetryConfig:
    """Tests for RetryConfig presets."""

    def test_gemini_config_has_correct_values(self):
        """Gemini config should have moderate retry settings."""
        config = RetryConfig.GEMINI
        assert config.max_attempts == 3
        assert config.initial_wait == 1.0
        assert config.max_wait == 10.0
        assert config.jitter == 2.0

    def test_notebooklm_config_has_longer_waits(self):
        """NotebookLM config should have longer waits for browser-based ops."""
        config = RetryConfig.NOTEBOOKLM
        assert config.max_attempts == 2
        assert config.initial_wait == 2.0
        assert config.max_wait == 30.0

    def test_veo_config_for_video_operations(self):
        """Veo config should have very long waits for video generation."""
        config = RetryConfig.VEO
        assert config.max_attempts == 2
        assert config.initial_wait == 5.0
        assert config.max_wait == 60.0

    def test_qdrant_config_for_fast_recovery(self):
        """Qdrant config should have fast retry for vector operations."""
        config = RetryConfig.QDRANT
        assert config.max_attempts == 3
        assert config.initial_wait == 0.5
        assert config.max_wait == 5.0

    def test_redis_config_for_cache_operations(self):
        """Redis config should have very fast retry."""
        config = RetryConfig.REDIS
        assert config.max_attempts == 3
        assert config.initial_wait == 0.1
        assert config.max_wait == 1.0

    def test_all_configs_have_retryable_exceptions(self):
        """All configs should have retryable exceptions defined."""
        configs = [
            RetryConfig.GEMINI,
            RetryConfig.NOTEBOOKLM,
            RetryConfig.VEO,
            RetryConfig.KLING,
            RetryConfig.QDRANT,
            RetryConfig.REDIS,
            RetryConfig.HTTP_DEFAULT,
        ]
        for config in configs:
            assert len(config.retryable_exceptions) > 0
            assert ConnectionError in config.retryable_exceptions
            assert TimeoutError in config.retryable_exceptions


# =============================================================================
# resilient_retry Decorator Tests
# =============================================================================

class TestResilientRetryDecorator:
    """Tests for resilient_retry decorator."""

    @pytest.mark.asyncio
    async def test_successful_call_returns_result(self):
        """Successful call should return result without retry."""
        call_count = 0

        @resilient_retry(RetryConfig.GEMINI)
        async def successful_operation():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_operation()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_retryable_exception(self):
        """Should retry on retryable exceptions."""
        call_count = 0

        config = RetryStrategyConfig(
            max_attempts=3,
            initial_wait=0.01,  # Fast for tests
            max_wait=0.1,
            jitter=0.01,
            retryable_exceptions=(ConnectionError,),
        )

        @resilient_retry(config)
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"

        result = await flaky_operation()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self):
        """Should raise after max retries exhausted."""
        call_count = 0

        config = RetryStrategyConfig(
            max_attempts=2,
            initial_wait=0.01,
            max_wait=0.1,
            jitter=0.01,
            retryable_exceptions=(ConnectionError,),
        )

        @resilient_retry(config)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError):
            await always_fails()

        assert call_count == 2

    @pytest.mark.asyncio
    async def test_does_not_retry_non_retryable_exception(self):
        """Should not retry non-retryable exceptions."""
        call_count = 0

        config = RetryStrategyConfig(
            max_attempts=3,
            initial_wait=0.01,
            max_wait=0.1,
            jitter=0.01,
            retryable_exceptions=(ConnectionError,),
        )

        @resilient_retry(config)
        async def raises_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retryable")

        with pytest.raises(ValueError):
            await raises_value_error()

        assert call_count == 1  # No retry


# =============================================================================
# Circuit Breaker Integration Tests
# =============================================================================

class TestCircuitBreakerIntegration:
    """Tests for circuit breaker integration."""

    @pytest.mark.asyncio
    async def test_checks_circuit_before_call(self):
        """Should check circuit breaker state before making call."""
        mock_breaker = MagicMock()
        mock_breaker.check_state = MagicMock()
        mock_breaker.record_success = MagicMock()

        @resilient_retry(RetryConfig.GEMINI, breaker=mock_breaker)
        async def operation():
            return "success"

        await operation()
        mock_breaker.check_state.assert_called_once()
        mock_breaker.record_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_records_success_on_circuit_breaker(self):
        """Should record success in circuit breaker."""
        mock_breaker = MagicMock()
        mock_breaker.check_state = MagicMock()
        mock_breaker.record_success = MagicMock()

        @resilient_retry(RetryConfig.GEMINI, breaker=mock_breaker)
        async def operation():
            return "success"

        await operation()
        mock_breaker.record_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_records_failure_on_circuit_breaker(self):
        """Should record failure in circuit breaker after exhausting retries."""
        mock_breaker = MagicMock()
        mock_breaker.check_state = MagicMock()
        mock_breaker.record_failure = MagicMock()

        config = RetryStrategyConfig(
            max_attempts=2,
            initial_wait=0.01,
            max_wait=0.1,
            jitter=0.01,
            retryable_exceptions=(ConnectionError,),
        )

        @resilient_retry(config, breaker=mock_breaker)
        async def always_fails():
            raise ConnectionError("Fails")

        with pytest.raises(ConnectionError):
            await always_fails()

        mock_breaker.record_failure.assert_called()

    @pytest.mark.asyncio
    async def test_respects_open_circuit(self):
        """Should not call function when circuit is open."""
        from app.services.circuit_breaker import CircuitBreakerOpen

        mock_breaker = MagicMock()
        mock_breaker.check_state = MagicMock(
            side_effect=CircuitBreakerOpen("test", 30.0)
        )

        call_count = 0

        @resilient_retry(RetryConfig.GEMINI, breaker=mock_breaker)
        async def operation():
            nonlocal call_count
            call_count += 1
            return "success"

        with pytest.raises(CircuitBreakerOpen):
            await operation()

        assert call_count == 0  # Function never called


# =============================================================================
# Rate Limit Tests
# =============================================================================

class TestRateLimitHandling:
    """Tests for rate limit detection and handling."""

    def test_is_rate_limited_detects_429(self):
        """Should detect 429 status code."""
        error = Exception("Error 429: Too Many Requests")
        assert is_rate_limited(error) is True

    def test_is_rate_limited_detects_rate_keyword(self):
        """Should detect 'rate' keyword."""
        error = Exception("Rate limit exceeded")
        assert is_rate_limited(error) is True

    def test_is_rate_limited_detects_quota(self):
        """Should detect quota exceeded."""
        error = Exception("Quota exceeded for the day")
        assert is_rate_limited(error) is True

    def test_is_rate_limited_detects_throttle(self):
        """Should detect throttle keyword."""
        error = Exception("Request throttled")
        assert is_rate_limited(error) is True

    def test_is_rate_limited_returns_false_for_other_errors(self):
        """Should return False for non-rate-limit errors."""
        error = Exception("Connection refused")
        assert is_rate_limited(error) is False


# =============================================================================
# Sync Decorator Tests
# =============================================================================

class TestResilientRetrySyncDecorator:
    """Tests for synchronous retry decorator."""

    def test_successful_sync_call(self):
        """Successful sync call should return result."""
        call_count = 0

        @resilient_retry_sync(RetryConfig.GEMINI)
        def successful_operation():
            nonlocal call_count
            call_count += 1
            return "sync_success"

        result = successful_operation()
        assert result == "sync_success"
        assert call_count == 1

    def test_sync_retries_on_exception(self):
        """Sync decorator should retry on retryable exceptions."""
        call_count = 0

        config = RetryStrategyConfig(
            max_attempts=3,
            initial_wait=0.01,
            max_wait=0.1,
            jitter=0.01,
            retryable_exceptions=(ConnectionError,),
        )

        @resilient_retry_sync(config)
        def flaky_sync_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Sync connection failed")
            return "success"

        result = flaky_sync_operation()
        assert result == "success"
        assert call_count == 2


# =============================================================================
# retry_operation Function Tests
# =============================================================================

class TestRetryOperation:
    """Tests for inline retry_operation function."""

    @pytest.mark.asyncio
    async def test_retry_operation_success(self):
        """retry_operation should return result on success."""
        async def operation():
            return "inline_success"

        result = await retry_operation(operation)
        assert result == "inline_success"

    @pytest.mark.asyncio
    async def test_retry_operation_with_args(self):
        """retry_operation should pass args to operation."""
        async def operation(x, y):
            return x + y

        result = await retry_operation(operation, config=RetryConfig.HTTP_DEFAULT, x=1, y=2)
        assert result == 3

    @pytest.mark.asyncio
    async def test_retry_operation_retries_on_failure(self):
        """retry_operation should retry on failure."""
        call_count = 0

        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Inline failure")
            return "recovered"

        config = RetryStrategyConfig(
            max_attempts=3,
            initial_wait=0.01,
            max_wait=0.1,
            jitter=0.01,
            retryable_exceptions=(ConnectionError,),
        )

        result = await retry_operation(flaky_operation, config=config)
        assert result == "recovered"
        assert call_count == 2


# =============================================================================
# get_retry_config Tests
# =============================================================================

class TestGetRetryConfig:
    """Tests for get_retry_config function."""

    def test_get_gemini_config(self):
        """Should return Gemini config."""
        config = get_retry_config("gemini")
        assert config == RetryConfig.GEMINI

    def test_get_qdrant_config(self):
        """Should return Qdrant config."""
        config = get_retry_config("qdrant")
        assert config == RetryConfig.QDRANT

    def test_get_config_case_insensitive(self):
        """Should work case-insensitively."""
        assert get_retry_config("GEMINI") == RetryConfig.GEMINI
        assert get_retry_config("Qdrant") == RetryConfig.QDRANT

    def test_unknown_provider_returns_default(self):
        """Unknown provider should return HTTP_DEFAULT."""
        config = get_retry_config("unknown_provider")
        assert config == RetryConfig.HTTP_DEFAULT


# =============================================================================
# Convenience Decorator Tests
# =============================================================================

class TestConvenienceDecorators:
    """Tests for pre-configured convenience decorators."""

    @pytest.mark.asyncio
    async def test_gemini_retry_decorator(self):
        """gemini_retry decorator should work."""
        @gemini_retry
        async def gemini_call():
            return "gemini_result"

        result = await gemini_call()
        assert result == "gemini_result"

    @pytest.mark.asyncio
    async def test_qdrant_retry_decorator(self):
        """qdrant_retry decorator should work."""
        @qdrant_retry
        async def qdrant_call():
            return "qdrant_result"

        result = await qdrant_call()
        assert result == "qdrant_result"
