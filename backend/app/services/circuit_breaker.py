"""
Circuit Breaker for External API Resilience

Implements circuit breaker pattern to prevent cascading failures
when external services (Gemini API, etc.) experience outages.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Service is down, fail fast without calling
- HALF_OPEN: Testing if service recovered

Usage:
    breaker = CircuitBreaker("gemini_api")
    breaker.check_state()  # Raises if OPEN
    try:
        result = await api_call()
        breaker.record_success()
    except Exception as e:
        breaker.record_failure(e)
        raise
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing fast
    HALF_OPEN = "half_open" # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures to trip open
    success_threshold: int = 2          # Successes to close
    timeout_seconds: float = 60.0       # Open state duration
    half_open_max_calls: int = 3        # Max calls in half-open


@dataclass
class CircuitBreakerState:
    """Mutable state for a circuit breaker."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    last_state_change: float = field(default_factory=time.time)
    half_open_calls: int = 0


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit is open."""
    def __init__(self, name: str, remaining_seconds: float):
        self.name = name
        self.remaining_seconds = remaining_seconds
        super().__init__(
            f"Circuit '{name}' is OPEN. "
            f"Service unavailable for {remaining_seconds:.1f}s. "
            f"Please try again later."
        )


class CircuitBreaker:
    """
    Circuit Breaker implementation for external API calls.
    
    Thread-safe singleton per service name.
    """
    _instances: Dict[str, "CircuitBreaker"] = {}
    _lock = asyncio.Lock()
    
    def __new__(cls, name: str, config: Optional[CircuitBreakerConfig] = None):
        # Return existing instance if exists
        if name in cls._instances:
            return cls._instances[name]
        
        instance = super().__new__(cls)
        cls._instances[name] = instance
        return instance
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
        
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitBreakerState()
        self._initialized = True
        logger.info(f"Circuit breaker '{name}' initialized")
    
    @property
    def state(self) -> CircuitState:
        """Get current state with automatic timeout transition."""
        if self._state.state == CircuitState.OPEN:
            elapsed = time.time() - self._state.last_state_change
            if elapsed >= self.config.timeout_seconds:
                self._transition_to(CircuitState.HALF_OPEN)
        return self._state.state
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to a new state."""
        old_state = self._state.state
        self._state.state = new_state
        self._state.last_state_change = time.time()
        
        if new_state == CircuitState.HALF_OPEN:
            self._state.half_open_calls = 0
            self._state.success_count = 0
        elif new_state == CircuitState.CLOSED:
            self._state.failure_count = 0
            self._state.success_count = 0
        
        logger.warning(
            f"⚡ Circuit '{self.name}' state: {old_state.value} → {new_state.value}"
        )
    
    def check_state(self):
        """
        Check if request can proceed.
        
        Raises:
            CircuitBreakerOpen: If circuit is open
        """
        current_state = self.state
        
        if current_state == CircuitState.OPEN:
            elapsed = time.time() - self._state.last_state_change
            remaining = max(0, self.config.timeout_seconds - elapsed)
            raise CircuitBreakerOpen(self.name, remaining)
        
        if current_state == CircuitState.HALF_OPEN:
            if self._state.half_open_calls >= self.config.half_open_max_calls:
                logger.debug(f"Half-open call limit reached for '{self.name}'")
                raise CircuitBreakerOpen(self.name, 5.0)
            self._state.half_open_calls += 1
    
    def record_success(self):
        """Record a successful call."""
        current_state = self.state
        
        if current_state == CircuitState.HALF_OPEN:
            self._state.success_count += 1
            if self._state.success_count >= self.config.success_threshold:
                self._transition_to(CircuitState.CLOSED)
                logger.info(f"✅ Circuit '{self.name}' recovered - service is healthy")
        elif current_state == CircuitState.CLOSED:
            # Reset failure count on success
            self._state.failure_count = 0
    
    def record_failure(self, error: Optional[Exception] = None):
        """Record a failed call."""
        self._state.failure_count += 1
        self._state.last_failure_time = time.time()
        
        current_state = self.state
        
        if current_state == CircuitState.HALF_OPEN:
            # Immediate trip back to open
            self._transition_to(CircuitState.OPEN)
            logger.warning(f"❌ Circuit '{self.name}' re-opened after half-open failure")
        elif current_state == CircuitState.CLOSED:
            if self._state.failure_count >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)
                logger.error(
                    f"🔴 Circuit '{self.name}' OPENED after {self._state.failure_count} failures. "
                    f"Last error: {error}"
                )
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for monitoring."""
        current_state = self.state
        remaining = 0.0
        
        if current_state == CircuitState.OPEN:
            elapsed = time.time() - self._state.last_state_change
            remaining = max(0, self.config.timeout_seconds - elapsed)
        
        return {
            "name": self.name,
            "state": current_state.value,
            "failure_count": self._state.failure_count,
            "success_count": self._state.success_count,
            "last_failure": self._state.last_failure_time,
            "remaining_open_seconds": remaining,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_seconds": self.config.timeout_seconds,
            }
        }
    
    @classmethod
    def get_all_status(cls) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers."""
        return {name: cb.get_status() for name, cb in cls._instances.items()}
    
    @classmethod
    def reset(cls, name: str):
        """Reset a circuit breaker to closed state."""
        if name in cls._instances:
            cb = cls._instances[name]
            cb._transition_to(CircuitState.CLOSED)
            logger.info(f"Circuit '{name}' manually reset to CLOSED")


# =============================================================================
# Decorator for easy integration
# =============================================================================

def with_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
):
    """
    Decorator to wrap async functions with circuit breaker protection.
    
    Usage:
        @with_circuit_breaker("gemini_api")
        async def call_gemini(prompt: str) -> str:
            ...
    """
    breaker = CircuitBreaker(name, config)
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            breaker.check_state()
            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure(e)
                raise
        return wrapper
    return decorator


# =============================================================================
# Pre-configured circuit breakers
# =============================================================================

# Gemini API circuit breaker with aggressive settings
GEMINI_BREAKER = CircuitBreaker(
    "gemini_api",
    CircuitBreakerConfig(
        failure_threshold=3,      # Trip after 3 failures
        success_threshold=2,      # Require 2 successes to close
        timeout_seconds=30.0,     # 30 second timeout
        half_open_max_calls=2,    # Test with 2 calls
    )
)

# Video generation (slower, less critical)
VIDEO_GEN_BREAKER = CircuitBreaker(
    "video_generation",
    CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout_seconds=120.0,
        half_open_max_calls=1,
    )
)

# P6-3: Qdrant vector database circuit breaker
QDRANT_BREAKER = CircuitBreaker(
    "qdrant",
    CircuitBreakerConfig(
        failure_threshold=3,      # Trip after 3 failures
        success_threshold=2,      # Require 2 successes to close
        timeout_seconds=60.0,     # 60 second cooldown
        half_open_max_calls=2,    # Test with 2 calls
    )
)

# NotebookLM circuit breaker (more fragile, longer recovery)
NOTEBOOKLM_BREAKER = CircuitBreaker(
    "notebooklm",
    CircuitBreakerConfig(
        failure_threshold=3,      # Trip after 3 failures
        success_threshold=2,      # Require 2 successes to close
        timeout_seconds=60.0,     # 60 second cooldown (browser-based)
        half_open_max_calls=1,    # Test with 1 call only
    )
)

# Veo Video Generation circuit breaker
VEO_BREAKER = CircuitBreaker(
    "veo",
    CircuitBreakerConfig(
        failure_threshold=3,      # Trip after 3 failures
        success_threshold=1,      # 1 success to close (slow service)
        timeout_seconds=120.0,    # 2 minute cooldown (video gen is slow)
        half_open_max_calls=1,    # Test with 1 call
    )
)


def get_circuit_health() -> Dict[str, Any]:
    """Get aggregated health status of all circuit breakers.

    Returns:
        Dict with overall health and individual circuit states
    """
    all_status = CircuitBreaker.get_all_status()
    open_circuits = [
        name for name, status in all_status.items()
        if status["state"] == "open"
    ]

    return {
        "healthy": len(open_circuits) == 0,
        "open_circuits": open_circuits,
        "circuits": all_status,
    }
