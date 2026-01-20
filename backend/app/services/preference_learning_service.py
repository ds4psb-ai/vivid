"""Phase 8: Preference Learning Service.

Netflix-style user embedding service with PersonaMem-v2 compact memory.

Based on:
- Netflix Embeddings-as-a-Service pattern
- PersonaMem-v2: 2k-token compact memory for personas
- REBECA: Implicit feedback → User-conditioned embeddings

Usage:
    from app.services.preference_learning_service import PreferenceLearningService

    service = PreferenceLearningService()

    # Record interaction signal
    await service.record_signal(
        user_id="user123",
        signal_type="click",
        dimension="4D",
        auteur_key="bong",
    )

    # Get user context for personalization
    context = await service.get_user_context(user_id="user123")
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_context
from app.models_personalization import (
    USER_EMBEDDING_DIM,
    UserPreferenceProfile,
    UserInteractionSignal,
    SessionPreference,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Signal weights based on REBECA paper (2025)
SIGNAL_WEIGHTS = {
    "click": 1.0,
    "dwell_time": 0.5,  # Per 10 seconds
    "rating": 2.0,      # Per star
    "query": 0.3,
    "generation_complete": 1.5,
    "feedback": 2.5,
    "evidence_ref_opened": 1.2,
    "template_seeded": 0.8,
}

# Dimension hierarchy (for affinity inheritance)
DIMENSION_HIERARCHY = {
    "4D": ["AD", "3D", "2D", "1D"],  # 4D inherits from all
    "AD": ["4D"],                     # AD related to 4D
    "3D": ["2D", "1D"],               # 3D inherits from 2D, 1D
    "2D": ["1D"],                     # 2D inherits from 1D
    "1D": [],                         # 1D is base
    "VEO": ["4D", "3D"],              # VEO relates to 4D and 3D
    "AI": ["AD", "4D"],               # AI relates to AD and 4D
    "QC": ["4D", "AD"],               # QC relates to 4D and AD
    "STORY": ["4D", "2D"],            # Story relates to 4D and 2D
    "SOUND": ["3D", "4D"],            # Sound relates to 3D and 4D
}

# Default affinities
DEFAULT_DIMENSION_AFFINITIES = {
    "1D": 0.5,
    "2D": 0.5,
    "3D": 0.5,
    "4D": 0.5,
    "AD": 0.5,
    "VEO": 0.5,
    "AI": 0.5,
    "QC": 0.5,
    "STORY": 0.5,
    "SOUND": 0.5,
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class UserContext:
    """User context for personalized retrieval.

    Contains all preference data needed for personalization boost.
    """
    user_id: str
    embedding: Optional[List[float]] = None
    dimension_affinities: Dict[str, float] = field(default_factory=dict)
    auteur_preferences: Dict[str, float] = field(default_factory=dict)
    persona_memory: Optional[str] = None
    total_signals: int = 0
    is_cold_start: bool = True  # True if not enough signals
    session_affinities: Optional[Dict[str, float]] = None  # From session


@dataclass
class AffinityUpdate:
    """Result of affinity computation."""
    dimension_affinities: Dict[str, float]
    auteur_preferences: Dict[str, float]
    signals_processed: int
    decay_applied: bool


# =============================================================================
# Preference Learning Service
# =============================================================================

class PreferenceLearningService:
    """Netflix-style user embedding service.

    Implements:
    1. Implicit/explicit signal recording
    2. User embedding computation
    3. Dimension and auteur affinity calculation
    4. PersonaMem-v2 compact persona generation

    Attributes:
        DECAY_HALF_LIFE_DAYS: Half-life for preference decay (default 30 days)
        MIN_SIGNALS_FOR_EMBEDDING: Minimum signals before computing embedding
        EMBEDDING_UPDATE_INTERVAL: Hours between embedding updates
    """

    DECAY_HALF_LIFE_DAYS = 30
    MIN_SIGNALS_FOR_EMBEDDING = 10
    EMBEDDING_UPDATE_INTERVAL = 24  # hours

    async def record_signal(
        self,
        user_id: str,
        signal_type: str,
        value: float = 1.0,
        dimension: Optional[str] = None,
        auteur_key: Optional[str] = None,
        session_id: Optional[str] = None,
        query_text: Optional[str] = None,
        evidence_ref: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Record an interaction signal.

        Args:
            user_id: User identifier
            signal_type: Type of signal (click, rating, query, etc.)
            value: Signal strength (default 1.0)
            dimension: Associated dimension code
            auteur_key: Associated auteur key
            session_id: Session identifier (for session-level tracking)
            query_text: Query text (for query-type signals)
            evidence_ref: Evidence reference string
            meta: Additional metadata

        Returns:
            True if signal was recorded successfully
        """
        async with get_db_context() as db:
            try:
                # Apply signal weight
                weighted_value = value * SIGNAL_WEIGHTS.get(signal_type, 1.0)

                # Create signal record
                signal = UserInteractionSignal(
                    user_id=user_id,
                    session_id=session_id,
                    signal_type=signal_type,
                    dimension=dimension.upper() if dimension else None,
                    auteur_key=auteur_key.lower() if auteur_key else None,
                    value=weighted_value,
                    query_text=query_text,
                    evidence_ref=evidence_ref,
                    meta=meta or {},
                )

                # Generate query embedding if query provided
                if query_text:
                    signal.query_embedding = await self._generate_embedding(query_text)

                db.add(signal)

                # Update profile signal count
                await self._increment_signal_count(db, user_id)

                await db.commit()

                logger.debug(
                    f"[PreferenceLearning] Recorded signal: "
                    f"user={user_id} type={signal_type} dim={dimension} "
                    f"auteur={auteur_key} value={weighted_value:.2f}"
                )

                return True

            except Exception as e:
                logger.error(f"[PreferenceLearning] Failed to record signal: {e}")
                await db.rollback()
                return False

    async def get_user_context(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        include_embedding: bool = True,
    ) -> UserContext:
        """Get user context for personalized retrieval.

        Args:
            user_id: User identifier
            session_id: Optional session ID for session-level preferences
            include_embedding: Whether to include user embedding

        Returns:
            UserContext with all preference data
        """
        async with get_db_context() as db:
            # Get or create profile
            profile = await self._get_or_create_profile(db, user_id)

            # Check if cold start
            is_cold_start = profile.total_signals < self.MIN_SIGNALS_FOR_EMBEDDING

            # Get dimension affinities
            dimension_affinities = profile.dimension_affinities or DEFAULT_DIMENSION_AFFINITIES.copy()

            # Get auteur preferences
            auteur_preferences = profile.auteur_preferences or {}

            # Get session preferences if session_id provided
            session_affinities = None
            if session_id:
                session_prefs = await self._get_session_preferences(db, session_id)
                if session_prefs:
                    session_affinities = {
                        "dimensions": session_prefs.dimension_affinities,
                        "auteurs": session_prefs.auteur_affinities,
                    }

            # Get embedding if requested and available
            embedding = None
            if include_embedding and not is_cold_start:
                embedding = profile.embedding

            return UserContext(
                user_id=user_id,
                embedding=embedding,
                dimension_affinities=dimension_affinities,
                auteur_preferences=auteur_preferences,
                persona_memory=profile.persona_memory,
                total_signals=profile.total_signals,
                is_cold_start=is_cold_start,
                session_affinities=session_affinities,
            )

    async def update_user_embedding(
        self,
        user_id: str,
        force: bool = False,
    ) -> Optional[List[float]]:
        """Update user embedding from accumulated signals.

        Computes a weighted average of query embeddings and
        generates a user preference embedding.

        Args:
            user_id: User identifier
            force: Force update even if recently updated

        Returns:
            Updated embedding or None if not enough signals
        """
        async with get_db_context() as db:
            profile = await self._get_or_create_profile(db, user_id)

            # Check if update is needed
            if not force and profile.last_embedding_update:
                hours_since_update = (
                    datetime.utcnow() - profile.last_embedding_update
                ).total_seconds() / 3600
                if hours_since_update < self.EMBEDDING_UPDATE_INTERVAL:
                    logger.debug(
                        f"[PreferenceLearning] Skipping embedding update for {user_id}: "
                        f"last updated {hours_since_update:.1f}h ago"
                    )
                    return profile.embedding

            # Get recent signals with embeddings
            cutoff_date = datetime.utcnow() - timedelta(days=self.DECAY_HALF_LIFE_DAYS * 2)
            result = await db.execute(
                select(UserInteractionSignal)
                .where(
                    UserInteractionSignal.user_id == user_id,
                    UserInteractionSignal.query_embedding.isnot(None),
                    UserInteractionSignal.created_at >= cutoff_date,
                )
                .order_by(UserInteractionSignal.created_at.desc())
                .limit(100)  # Cap at recent 100 signals
            )
            signals = result.scalars().all()

            if len(signals) < self.MIN_SIGNALS_FOR_EMBEDDING:
                logger.debug(
                    f"[PreferenceLearning] Not enough signals for {user_id}: "
                    f"{len(signals)} < {self.MIN_SIGNALS_FOR_EMBEDDING}"
                )
                return None

            # Compute weighted average embedding with decay
            embedding = await self._compute_weighted_embedding(signals)
            if not embedding:
                return None

            # Update profile
            profile.embedding = embedding
            profile.last_embedding_update = datetime.utcnow()
            await db.commit()

            logger.info(
                f"[PreferenceLearning] Updated embedding for {user_id} "
                f"from {len(signals)} signals"
            )

            return embedding

    async def compute_dimension_affinities(
        self,
        user_id: str,
    ) -> Dict[str, float]:
        """Compute dimension affinities from signals.

        Calculates affinity scores for each dimension based on
        historical interactions with decay.

        Args:
            user_id: User identifier

        Returns:
            Dict mapping dimension -> affinity score (0-1)
        """
        async with get_db_context() as db:
            # Get signal counts by dimension
            cutoff_date = datetime.utcnow() - timedelta(days=self.DECAY_HALF_LIFE_DAYS * 2)
            result = await db.execute(
                select(
                    UserInteractionSignal.dimension,
                    func.sum(UserInteractionSignal.value).label("total_value"),
                    func.count(UserInteractionSignal.id).label("count"),
                )
                .where(
                    UserInteractionSignal.user_id == user_id,
                    UserInteractionSignal.dimension.isnot(None),
                    UserInteractionSignal.created_at >= cutoff_date,
                )
                .group_by(UserInteractionSignal.dimension)
            )
            dimension_stats = result.all()

            if not dimension_stats:
                return DEFAULT_DIMENSION_AFFINITIES.copy()

            # Calculate affinities
            affinities = DEFAULT_DIMENSION_AFFINITIES.copy()
            max_value = max((s.total_value or 0) for s in dimension_stats) or 1.0

            for stat in dimension_stats:
                if stat.dimension:
                    # Normalize to 0-1 range
                    raw_affinity = (stat.total_value or 0) / max_value
                    # Apply sigmoid smoothing
                    smoothed = 1 / (1 + math.exp(-4 * (raw_affinity - 0.5)))
                    affinities[stat.dimension] = round(smoothed, 3)

            # Apply hierarchy inheritance
            affinities = self._apply_hierarchy_inheritance(affinities)

            # Update profile
            profile = await self._get_or_create_profile(db, user_id)
            profile.dimension_affinities = affinities
            await db.commit()

            return affinities

    async def compute_auteur_preferences(
        self,
        user_id: str,
    ) -> Dict[str, float]:
        """Compute auteur preferences from signals.

        Args:
            user_id: User identifier

        Returns:
            Dict mapping auteur_key -> preference score (0-1)
        """
        async with get_db_context() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=self.DECAY_HALF_LIFE_DAYS * 2)
            result = await db.execute(
                select(
                    UserInteractionSignal.auteur_key,
                    func.sum(UserInteractionSignal.value).label("total_value"),
                    func.count(UserInteractionSignal.id).label("count"),
                )
                .where(
                    UserInteractionSignal.user_id == user_id,
                    UserInteractionSignal.auteur_key.isnot(None),
                    UserInteractionSignal.created_at >= cutoff_date,
                )
                .group_by(UserInteractionSignal.auteur_key)
            )
            auteur_stats = result.all()

            if not auteur_stats:
                return {}

            # Calculate preferences
            preferences: Dict[str, float] = {}
            max_value = max((s.total_value or 0) for s in auteur_stats) or 1.0

            for stat in auteur_stats:
                if stat.auteur_key:
                    raw_pref = (stat.total_value or 0) / max_value
                    smoothed = 1 / (1 + math.exp(-4 * (raw_pref - 0.5)))
                    preferences[stat.auteur_key] = round(smoothed, 3)

            # Update profile
            profile = await self._get_or_create_profile(db, user_id)
            profile.auteur_preferences = preferences
            await db.commit()

            return preferences

    async def generate_persona_memory(
        self,
        user_id: str,
        max_tokens: int = 2000,
    ) -> Optional[str]:
        """Generate PersonaMem-v2 style compact persona.

        Creates a compressed representation of user preferences
        suitable for context injection.

        Args:
            user_id: User identifier
            max_tokens: Maximum tokens for persona (default 2000)

        Returns:
            Persona memory string or None
        """
        async with get_db_context() as db:
            profile = await self._get_or_create_profile(db, user_id)

            # Get recent interaction summary
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            result = await db.execute(
                select(
                    UserInteractionSignal.signal_type,
                    UserInteractionSignal.dimension,
                    UserInteractionSignal.auteur_key,
                    func.count(UserInteractionSignal.id).label("count"),
                )
                .where(
                    UserInteractionSignal.user_id == user_id,
                    UserInteractionSignal.created_at >= cutoff_date,
                )
                .group_by(
                    UserInteractionSignal.signal_type,
                    UserInteractionSignal.dimension,
                    UserInteractionSignal.auteur_key,
                )
                .order_by(func.count(UserInteractionSignal.id).desc())
                .limit(50)
            )
            interaction_summary = result.all()

            if not interaction_summary:
                return None

            # Build persona memory
            persona_parts: List[str] = []

            # Dimension preferences
            if profile.dimension_affinities:
                top_dims = sorted(
                    profile.dimension_affinities.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:3]
                dim_str = ", ".join(f"{d}: {v:.0%}" for d, v in top_dims)
                persona_parts.append(f"Preferred dimensions: {dim_str}")

            # Auteur preferences
            if profile.auteur_preferences:
                top_auteurs = sorted(
                    profile.auteur_preferences.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:3]
                auteur_str = ", ".join(f"{a}: {v:.0%}" for a, v in top_auteurs)
                persona_parts.append(f"Preferred auteurs: {auteur_str}")

            # Interaction patterns
            signal_counts: Dict[str, int] = {}
            for row in interaction_summary:
                signal_type = row.signal_type
                signal_counts[signal_type] = signal_counts.get(signal_type, 0) + row.count

            if signal_counts:
                top_signals = sorted(signal_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                signals_str = ", ".join(f"{s}: {c}" for s, c in top_signals)
                persona_parts.append(f"Interaction patterns: {signals_str}")

            # Combine and truncate
            persona_memory = "\n".join(persona_parts)

            # Rough token estimate and truncation
            if len(persona_memory.split()) > max_tokens * 0.75:
                words = persona_memory.split()[:int(max_tokens * 0.75)]
                persona_memory = " ".join(words)

            # Update profile
            profile.persona_memory = persona_memory
            await db.commit()

            logger.info(f"[PreferenceLearning] Generated persona for {user_id}")

            return persona_memory

    async def apply_decay(
        self,
        user_id: str,
    ) -> bool:
        """Apply time-based decay to user preferences.

        Reduces preference scores based on time since last interaction.

        Args:
            user_id: User identifier

        Returns:
            True if decay was applied
        """
        async with get_db_context() as db:
            profile = await self._get_or_create_profile(db, user_id)

            # Calculate decay factor
            if profile.updated_at:
                days_since_update = (datetime.utcnow() - profile.updated_at).days
                decay = 0.5 ** (days_since_update / self.DECAY_HALF_LIFE_DAYS)
            else:
                decay = 1.0

            # Apply decay to affinities
            if profile.dimension_affinities:
                decayed_dims = {
                    k: v * decay
                    for k, v in profile.dimension_affinities.items()
                }
                profile.dimension_affinities = decayed_dims

            if profile.auteur_preferences:
                decayed_auteurs = {
                    k: v * decay
                    for k, v in profile.auteur_preferences.items()
                }
                profile.auteur_preferences = decayed_auteurs

            profile.decay_factor = decay
            await db.commit()

            return True

    async def cleanup_old_signals(
        self,
        days: int = 90,
    ) -> int:
        """Clean up old signals older than specified days.

        Args:
            days: Delete signals older than this many days

        Returns:
            Number of signals deleted
        """
        async with get_db_context() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            result = await db.execute(
                delete(UserInteractionSignal)
                .where(UserInteractionSignal.created_at < cutoff_date)
                .returning(UserInteractionSignal.id)
            )
            deleted_ids = result.scalars().all()
            await db.commit()

            count = len(deleted_ids)
            if count > 0:
                logger.info(f"[PreferenceLearning] Cleaned up {count} old signals")

            return count

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def _get_or_create_profile(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> UserPreferenceProfile:
        """Get or create user preference profile."""
        result = await db.execute(
            select(UserPreferenceProfile)
            .where(UserPreferenceProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            profile = UserPreferenceProfile(
                user_id=user_id,
                dimension_affinities=DEFAULT_DIMENSION_AFFINITIES.copy(),
                auteur_preferences={},
            )
            db.add(profile)
            await db.flush()

        return profile

    async def _increment_signal_count(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> None:
        """Increment total signals count for user."""
        result = await db.execute(
            select(UserPreferenceProfile)
            .where(UserPreferenceProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if profile:
            profile.total_signals = (profile.total_signals or 0) + 1
        else:
            profile = UserPreferenceProfile(
                user_id=user_id,
                total_signals=1,
                dimension_affinities=DEFAULT_DIMENSION_AFFINITIES.copy(),
            )
            db.add(profile)

    async def _get_session_preferences(
        self,
        db: AsyncSession,
        session_id: str,
    ) -> Optional[SessionPreference]:
        """Get session preferences if not expired."""
        result = await db.execute(
            select(SessionPreference)
            .where(
                SessionPreference.session_id == session_id,
                SessionPreference.expires_at > datetime.utcnow(),
            )
        )
        return result.scalar_one_or_none()

    async def _compute_weighted_embedding(
        self,
        signals: List[UserInteractionSignal],
    ) -> Optional[List[float]]:
        """Compute weighted average of signal embeddings."""
        if not signals:
            return None

        weighted_sum = [0.0] * USER_EMBEDDING_DIM
        total_weight = 0.0

        for signal in signals:
            if not signal.query_embedding:
                continue

            # Apply time decay
            days_old = (datetime.utcnow() - signal.created_at).days
            time_weight = 0.5 ** (days_old / self.DECAY_HALF_LIFE_DAYS)

            # Combined weight
            weight = signal.value * time_weight

            # Add to weighted sum
            for i, val in enumerate(signal.query_embedding):
                if i < USER_EMBEDDING_DIM:
                    weighted_sum[i] += val * weight

            total_weight += weight

        if total_weight == 0:
            return None

        # Normalize
        embedding = [v / total_weight for v in weighted_sum]

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in embedding))
        if norm > 0:
            embedding = [v / norm for v in embedding]

        return embedding

    async def _generate_embedding(
        self,
        text: str,
    ) -> Optional[List[float]]:
        """Generate embedding for text."""
        try:
            from app.rag.embeddings import get_embedding
            return await get_embedding(text)
        except Exception as e:
            logger.warning(f"[PreferenceLearning] Failed to generate embedding: {e}")
            return None

    def _apply_hierarchy_inheritance(
        self,
        affinities: Dict[str, float],
    ) -> Dict[str, float]:
        """Apply dimension hierarchy inheritance.

        Higher dimensions inherit some affinity from related dimensions.
        """
        for dim, related_dims in DIMENSION_HIERARCHY.items():
            if dim not in affinities:
                continue

            # Average with related dimensions (25% inheritance)
            related_scores = [
                affinities.get(rd, 0.5)
                for rd in related_dims
                if rd in affinities
            ]

            if related_scores:
                avg_related = sum(related_scores) / len(related_scores)
                # 75% own, 25% inherited
                affinities[dim] = round(
                    affinities[dim] * 0.75 + avg_related * 0.25,
                    3,
                )

        return affinities


# =============================================================================
# Singleton Instance
# =============================================================================

_preference_learning_service: Optional[PreferenceLearningService] = None


def get_preference_learning_service() -> PreferenceLearningService:
    """Get singleton preference learning service."""
    global _preference_learning_service
    if _preference_learning_service is None:
        _preference_learning_service = PreferenceLearningService()
    return _preference_learning_service


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "SIGNAL_WEIGHTS",
    "UserContext",
    "AffinityUpdate",
    "PreferenceLearningService",
    "get_preference_learning_service",
]
