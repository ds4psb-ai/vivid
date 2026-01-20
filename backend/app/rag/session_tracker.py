"""Real-Time Session Preference Tracker.

Phase 8: Redis-backed session tracking for real-time personalization.

Features:
- Two-level caching: Local LRU + Redis
- TTL: 1 hour for personalization sessions
- Graceful degradation to in-memory on Redis failure
- Real-time affinity updates based on interactions
- Precomputed recommendations

Usage:
    from app.rag.session_tracker import get_session_tracker

    tracker = get_session_tracker()
    state = await tracker.track_interaction(
        session_id="sess_abc",
        interaction_type="click",
        dimension="AD",
        auteur_key="bong",
    )
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)

# Session TTL: 1 hour (Phase 8 requirement)
SESSION_TTL_SECONDS = 60 * 60

# Local cache size (LRU for hot sessions)
LOCAL_CACHE_SIZE = 500

# Interaction weights for affinity calculation
INTERACTION_WEIGHTS = {
    "click": 1.0,
    "view": 0.3,
    "dwell": 0.5,  # Per 10 seconds
    "rating": 2.0,
    "generation_complete": 1.5,
    "feedback": 2.5,
    "query": 0.5,
}

# Decay factor per hour for session affinities
SESSION_DECAY_PER_HOUR = 0.9


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SessionInteraction:
    """Record of a single interaction."""

    interaction_type: str
    dimension: Optional[str] = None
    auteur_key: Optional[str] = None
    value: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionState:
    """Current session state for personalization.

    Attributes:
        session_id: Unique session identifier
        user_id: Optional linked user ID
        dimension_affinities: Current dimension preferences
        auteur_affinities: Current auteur preferences
        interaction_count: Total interactions in session
        last_interaction_at: Time of last interaction
        recent_interactions: List of recent interactions
        recommendations: Precomputed recommendations
        created_at: Session creation time
    """

    session_id: str
    user_id: Optional[str] = None
    dimension_affinities: Dict[str, float] = field(default_factory=dict)
    auteur_affinities: Dict[str, float] = field(default_factory=dict)
    interaction_count: int = 0
    last_interaction_at: Optional[datetime] = None
    recent_interactions: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "dimension_affinities": self.dimension_affinities,
            "auteur_affinities": self.auteur_affinities,
            "interaction_count": self.interaction_count,
            "last_interaction_at": (
                self.last_interaction_at.isoformat()
                if self.last_interaction_at else None
            ),
            "recent_interactions": self.recent_interactions[-20:],  # Keep last 20
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        """Create from dictionary."""
        last_interaction = None
        if data.get("last_interaction_at"):
            try:
                last_interaction = datetime.fromisoformat(data["last_interaction_at"])
            except (ValueError, TypeError):
                pass

        created_at = datetime.utcnow()
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                pass

        return cls(
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id"),
            dimension_affinities=data.get("dimension_affinities", {}),
            auteur_affinities=data.get("auteur_affinities", {}),
            interaction_count=data.get("interaction_count", 0),
            last_interaction_at=last_interaction,
            recent_interactions=data.get("recent_interactions", []),
            recommendations=data.get("recommendations", []),
            created_at=created_at,
        )


# =============================================================================
# Session Preference Tracker
# =============================================================================

class SessionPreferenceTracker:
    """Real-time session tracker using Redis.

    2026 Best Practices:
    - Two-level caching (local LRU + Redis) for reduced latency
    - Graceful fallback to in-memory if Redis unavailable
    - Connection health monitoring
    - Automatic TTL management
    - Affinity decay for time-sensitive personalization
    """

    KEY_PREFIX = "vivid:session:"

    def __init__(
        self,
        redis_url: str = "redis://localhost:6380",
        ttl_seconds: int = SESSION_TTL_SECONDS,
        local_cache_size: int = LOCAL_CACHE_SIZE,
    ):
        """Initialize session tracker.

        Args:
            redis_url: Redis connection URL
            ttl_seconds: Session TTL in seconds
            local_cache_size: Maximum local cache entries
        """
        self._redis_url = redis_url
        self._ttl = ttl_seconds
        self._local_cache_size = local_cache_size

        # Redis client (lazy initialization)
        self._redis: Optional["Redis"] = None
        self._redis_healthy = False
        self._last_health_check: Optional[datetime] = None
        self._health_check_interval = timedelta(seconds=30)

        # Fallback in-memory storage
        self._fallback_memory: Dict[str, Dict[str, Any]] = {}

        # Local LRU cache for hot sessions
        self._local_cache: Dict[str, tuple[SessionState, datetime]] = {}

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def _get_redis(self) -> Optional["Redis"]:
        """Get Redis client with lazy initialization and health check."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                )
                self._redis_healthy = True
                logger.info("[SessionTracker] Redis connection established")
            except Exception as e:
                logger.warning(f"[SessionTracker] Failed to connect to Redis: {e}")
                self._redis_healthy = False
                return None

        # Periodic health check
        now = datetime.utcnow()
        if (
            self._last_health_check is None
            or now - self._last_health_check > self._health_check_interval
        ):
            try:
                await self._redis.ping()
                self._redis_healthy = True
                self._last_health_check = now
            except Exception as e:
                logger.warning(f"[SessionTracker] Redis health check failed: {e}")
                self._redis_healthy = False
                return None

        return self._redis if self._redis_healthy else None

    def _make_key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"{self.KEY_PREFIX}{session_id}"

    async def track_interaction(
        self,
        session_id: str,
        interaction_type: str,
        dimension: Optional[str] = None,
        auteur_key: Optional[str] = None,
        value: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> SessionState:
        """Track interaction and update session state.

        Args:
            session_id: Unique session identifier
            interaction_type: Type of interaction (click, view, etc.)
            dimension: Associated dimension
            auteur_key: Associated auteur
            value: Interaction value/weight
            metadata: Additional interaction metadata
            user_id: Optional user ID to link

        Returns:
            Updated SessionState
        """
        async with self._lock:
            # Get or create session state
            state = await self._get_session_state(session_id)
            if state is None:
                state = SessionState(session_id=session_id, user_id=user_id)

            # Update user_id if provided
            if user_id and not state.user_id:
                state.user_id = user_id

            # Calculate interaction weight
            weight = INTERACTION_WEIGHTS.get(interaction_type, 1.0) * value

            # Apply time decay to existing affinities
            state = self._apply_decay(state)

            # Update dimension affinity
            if dimension:
                current_affinity = state.dimension_affinities.get(dimension, 0.0)
                # Additive with diminishing returns
                new_affinity = min(1.0, current_affinity + weight * (1 - current_affinity * 0.1))
                state.dimension_affinities[dimension] = new_affinity

            # Update auteur affinity
            if auteur_key:
                current_affinity = state.auteur_affinities.get(auteur_key, 0.0)
                new_affinity = min(1.0, current_affinity + weight * (1 - current_affinity * 0.1))
                state.auteur_affinities[auteur_key] = new_affinity

            # Record interaction
            state.interaction_count += 1
            state.last_interaction_at = datetime.utcnow()
            state.recent_interactions.append({
                "type": interaction_type,
                "dimension": dimension,
                "auteur_key": auteur_key,
                "value": value,
                "timestamp": state.last_interaction_at.isoformat(),
                "metadata": metadata or {},
            })

            # Keep only last 20 interactions
            if len(state.recent_interactions) > 20:
                state.recent_interactions = state.recent_interactions[-20:]

            # Save state
            await self._save_session_state(session_id, state)

            logger.debug(
                f"[SessionTracker] Interaction tracked | "
                f"session={session_id[:8]}... | "
                f"type={interaction_type} | "
                f"count={state.interaction_count}"
            )

            return state

    async def get_session_state(self, session_id: str) -> Optional[SessionState]:
        """Get current session state from Redis.

        Args:
            session_id: Session identifier

        Returns:
            SessionState if exists, None otherwise
        """
        return await self._get_session_state(session_id)

    async def _get_session_state(self, session_id: str) -> Optional[SessionState]:
        """Internal method to get session state."""
        # Check local cache first
        if session_id in self._local_cache:
            state, cached_at = self._local_cache[session_id]
            if datetime.utcnow() - cached_at < timedelta(seconds=self._ttl):
                return state
            else:
                del self._local_cache[session_id]

        # Try Redis
        redis = await self._get_redis()
        if redis:
            try:
                key = self._make_key(session_id)
                data = await redis.get(key)
                if data:
                    state_dict = json.loads(data)
                    state = SessionState.from_dict(state_dict)
                    self._update_local_cache(session_id, state)
                    return state
            except Exception as e:
                logger.warning(f"[SessionTracker] Redis get failed: {e}")

        # Fallback to in-memory
        if session_id in self._fallback_memory:
            return SessionState.from_dict(self._fallback_memory[session_id])

        return None

    async def _save_session_state(self, session_id: str, state: SessionState) -> bool:
        """Save session state to storage."""
        state_dict = state.to_dict()

        # Update local cache
        self._update_local_cache(session_id, state)

        # Try Redis
        redis = await self._get_redis()
        if redis:
            try:
                key = self._make_key(session_id)
                await redis.setex(key, self._ttl, json.dumps(state_dict))
                return True
            except Exception as e:
                logger.warning(f"[SessionTracker] Redis set failed: {e}")

        # Fallback to in-memory
        self._fallback_memory[session_id] = state_dict
        self._cleanup_fallback()

        return True

    def _update_local_cache(self, session_id: str, state: SessionState) -> None:
        """Update local LRU cache."""
        now = datetime.utcnow()

        # Simple LRU: Remove oldest if at capacity
        if len(self._local_cache) >= self._local_cache_size:
            oldest_key = min(
                self._local_cache.keys(),
                key=lambda k: self._local_cache[k][1]
            )
            del self._local_cache[oldest_key]

        self._local_cache[session_id] = (state, now)

    def _apply_decay(self, state: SessionState) -> SessionState:
        """Apply time decay to session affinities."""
        if not state.last_interaction_at:
            return state

        hours_since_last = (
            datetime.utcnow() - state.last_interaction_at
        ).total_seconds() / 3600

        if hours_since_last < 0.1:  # Less than 6 minutes
            return state

        decay = SESSION_DECAY_PER_HOUR ** hours_since_last

        # Apply decay to dimension affinities
        state.dimension_affinities = {
            k: v * decay for k, v in state.dimension_affinities.items()
            if v * decay >= 0.1  # Remove very low affinities
        }

        # Apply decay to auteur affinities
        state.auteur_affinities = {
            k: v * decay for k, v in state.auteur_affinities.items()
            if v * decay >= 0.1
        }

        return state

    def _cleanup_fallback(self) -> None:
        """Remove expired entries from fallback memory."""
        now = datetime.utcnow()
        expired = []

        for session_id, data in self._fallback_memory.items():
            created_at_str = data.get("created_at")
            if created_at_str:
                try:
                    created = datetime.fromisoformat(created_at_str)
                    if now - created > timedelta(seconds=self._ttl):
                        expired.append(session_id)
                except ValueError:
                    pass

        for session_id in expired:
            del self._fallback_memory[session_id]

    async def precompute_recommendations(
        self,
        session_id: str,
        limit: int = 10,
    ) -> List[str]:
        """Precompute recommendations based on session affinities.

        Args:
            session_id: Session identifier
            limit: Maximum recommendations to generate

        Returns:
            List of recommended evidence_ref strings
        """
        state = await self.get_session_state(session_id)
        if not state:
            return []

        recommendations: List[str] = []

        # Get top dimensions
        top_dimensions = sorted(
            state.dimension_affinities.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:3]

        # Get top auteurs
        top_auteurs = sorted(
            state.auteur_affinities.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:3]

        # Generate recommendation refs based on affinities
        for dim, score in top_dimensions:
            if score >= 0.3:
                recommendations.append(f"recommend:dimension:{dim}")

        for auteur, score in top_auteurs:
            if score >= 0.3:
                recommendations.append(f"recommend:auteur:{auteur}")

        # Limit results
        recommendations = recommendations[:limit]

        # Update state with recommendations
        async with self._lock:
            current_state = await self._get_session_state(session_id)
            if current_state:
                current_state.recommendations = recommendations
                await self._save_session_state(session_id, current_state)

        return recommendations

    async def merge_with_user_profile(
        self,
        session_id: str,
        user_id: str,
    ) -> bool:
        """Merge session preferences with user profile.

        Called when a user logs in during a session.

        Args:
            session_id: Session identifier
            user_id: User identifier

        Returns:
            True if merge was successful
        """
        try:
            from app.services.preference_learning_service import PreferenceLearningService

            state = await self.get_session_state(session_id)
            if not state:
                return False

            pref_service = PreferenceLearningService()

            # Record session interactions as user signals
            for interaction in state.recent_interactions:
                await pref_service.record_signal(
                    user_id=user_id,
                    signal_type=interaction.get("type", "click"),
                    value=interaction.get("value", 1.0),
                    dimension=interaction.get("dimension"),
                    auteur_key=interaction.get("auteur_key"),
                )

            # Update session with user_id
            async with self._lock:
                state.user_id = user_id
                await self._save_session_state(session_id, state)

            logger.info(
                f"[SessionTracker] Merged session with user | "
                f"session={session_id[:8]}... | "
                f"user={user_id[:8]}... | "
                f"interactions={len(state.recent_interactions)}"
            )

            return True

        except Exception as e:
            logger.error(f"[SessionTracker] Merge failed: {e}")
            return False

    async def delete_session(self, session_id: str) -> bool:
        """Delete session data."""
        async with self._lock:
            # Remove from local cache
            self._local_cache.pop(session_id, None)

            # Remove from fallback
            self._fallback_memory.pop(session_id, None)

            # Remove from Redis
            redis = await self._get_redis()
            if redis:
                try:
                    key = self._make_key(session_id)
                    await redis.delete(key)
                except Exception as e:
                    logger.warning(f"[SessionTracker] Redis delete failed: {e}")

            return True

    async def get_stats(self) -> Dict[str, Any]:
        """Get tracker statistics."""
        redis = await self._get_redis()

        return {
            "local_cache_size": len(self._local_cache),
            "local_cache_max": self._local_cache_size,
            "fallback_size": len(self._fallback_memory),
            "redis_healthy": self._redis_healthy,
            "ttl_seconds": self._ttl,
        }

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            self._redis_healthy = False


# =============================================================================
# Singleton Instance
# =============================================================================

_session_tracker: Optional[SessionPreferenceTracker] = None


def get_session_tracker() -> SessionPreferenceTracker:
    """Get or create singleton session tracker."""
    global _session_tracker
    if _session_tracker is None:
        from app.config import settings
        _session_tracker = SessionPreferenceTracker(redis_url=settings.REDIS_URL)
    return _session_tracker


async def init_session_tracker() -> SessionPreferenceTracker:
    """Initialize session tracker (call at startup)."""
    tracker = get_session_tracker()
    await tracker._get_redis()
    return tracker


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "SessionInteraction",
    "SessionState",
    "SessionPreferenceTracker",
    "get_session_tracker",
    "init_session_tracker",
    "SESSION_TTL_SECONDS",
    "INTERACTION_WEIGHTS",
]
