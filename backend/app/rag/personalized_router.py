"""Personalized RAG Router.

Phase 8: Applies user preferences to RAG results for personalized retrieval.

Personalization strategies:
1. Dimension Affinity Boost: Boost results matching user's preferred dimensions
2. Auteur Affinity Boost: Boost results from user's preferred auteurs
3. Embedding Similarity: Boost results similar to user's embedding vector
4. A/B Testing: Support controlled experiments

Usage:
    from app.rag.personalized_router import PersonalizedRAGRouter

    router = PersonalizedRAGRouter()
    result = await router.retrieve(
        query="강주노 롱테이크",
        user_id="user_123",
        session_id="sess_abc",
        limit=10,
    )
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.rag.backends.base import BaseBackend, RetrievalResult

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class PersonalizedRetrievalConfig:
    """Configuration for personalized retrieval.

    Attributes:
        dimension_affinity_boost: Score boost for matching dimension (0-1)
        auteur_affinity_boost: Score boost for matching auteur (0-1)
        user_embedding_weight: Weight for user embedding similarity (0-1)
        session_weight: Weight for session preferences vs user profile (0-1)
        min_affinity_threshold: Minimum affinity to apply boost (0-1)
        ab_test_enabled: Enable A/B testing mode
        ab_test_variant: A/B test variant ("control" | "treatment")
    """

    dimension_affinity_boost: float = 0.3
    auteur_affinity_boost: float = 0.25
    user_embedding_weight: float = 0.2
    session_weight: float = 0.4  # 40% session, 60% user profile
    min_affinity_threshold: float = 0.3
    ab_test_enabled: bool = False
    ab_test_variant: str = "control"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersonalizedRetrievalConfig":
        """Create config from dictionary."""
        return cls(
            dimension_affinity_boost=data.get("dimension_affinity_boost", 0.3),
            auteur_affinity_boost=data.get("auteur_affinity_boost", 0.25),
            user_embedding_weight=data.get("user_embedding_weight", 0.2),
            session_weight=data.get("session_weight", 0.4),
            min_affinity_threshold=data.get("min_affinity_threshold", 0.3),
            ab_test_enabled=data.get("ab_test_enabled", False),
            ab_test_variant=data.get("ab_test_variant", "control"),
        )


@dataclass
class PersonalizedResult:
    """Result from personalized retrieval.

    Attributes:
        documents: Personalized document list
        user_context_applied: Whether user context was applied
        session_context_applied: Whether session context was applied
        personalization_scores: Per-document personalization scores
        retrieval_time_ms: Total retrieval time
        ab_variant: A/B test variant used (if any)
    """

    documents: List[RetrievalResult] = field(default_factory=list)
    user_context_applied: bool = False
    session_context_applied: bool = False
    personalization_scores: Dict[str, float] = field(default_factory=dict)
    retrieval_time_ms: int = 0
    ab_variant: Optional[str] = None
    config_used: Optional[PersonalizedRetrievalConfig] = None


# =============================================================================
# Personalized Router
# =============================================================================

class PersonalizedRAGRouter:
    """Router that applies personalization to RAG results.

    This router wraps existing backends and applies user preference boosts
    to the retrieved documents.

    Attributes:
        config: Default personalization configuration
        backend: Underlying RAG backend to use
    """

    def __init__(
        self,
        backend: Optional[BaseBackend] = None,
        config: Optional[PersonalizedRetrievalConfig] = None,
    ):
        """Initialize the personalized router.

        Args:
            backend: Backend to use for retrieval (default: graph_qdrant)
            config: Default personalization configuration
        """
        self._backend = backend
        self.config = config or PersonalizedRetrievalConfig()
        self._preference_service = None

    @property
    def backend(self) -> BaseBackend:
        """Lazy-load the default backend."""
        if self._backend is None:
            from app.rag.backends import get_backend
            self._backend = get_backend("graph_qdrant")
        return self._backend

    @property
    def preference_service(self):
        """Lazy-load preference learning service."""
        if self._preference_service is None:
            from app.services.preference_learning_service import PreferenceLearningService
            self._preference_service = PreferenceLearningService()
        return self._preference_service

    async def retrieve(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        backend_config: Optional[Dict[str, Any]] = None,
        personalization_config: Optional[Dict[str, Any]] = None,
    ) -> PersonalizedResult:
        """Retrieve documents with personalization boosts.

        Args:
            query: Search query
            user_id: User identifier for personalization
            session_id: Session identifier for real-time adaptation
            limit: Maximum results to return
            filters: Metadata filters for backend
            backend_config: Backend-specific configuration
            personalization_config: Override personalization settings

        Returns:
            PersonalizedResult with boosted documents
        """
        start_time = time.monotonic()

        # Merge configuration
        config = self.config
        if personalization_config:
            config = PersonalizedRetrievalConfig.from_dict({
                **{
                    "dimension_affinity_boost": config.dimension_affinity_boost,
                    "auteur_affinity_boost": config.auteur_affinity_boost,
                    "user_embedding_weight": config.user_embedding_weight,
                    "session_weight": config.session_weight,
                    "min_affinity_threshold": config.min_affinity_threshold,
                    "ab_test_enabled": config.ab_test_enabled,
                    "ab_test_variant": config.ab_test_variant,
                },
                **personalization_config,
            })

        # A/B Testing: Skip personalization for control group
        if config.ab_test_enabled and config.ab_test_variant == "control":
            documents = await self.backend.retrieve(
                query=query,
                limit=limit,
                filters=filters,
                config=backend_config,
            )
            elapsed_ms = int((time.monotonic() - start_time) * 1000)

            logger.info(
                f"[PersonalizedRouter] A/B control group | "
                f"docs={len(documents)} | time={elapsed_ms}ms"
            )

            return PersonalizedResult(
                documents=documents,
                user_context_applied=False,
                session_context_applied=False,
                retrieval_time_ms=elapsed_ms,
                ab_variant="control",
                config_used=config,
            )

        # Get user context
        user_context = None
        session_context = None

        if user_id:
            try:
                user_context = await self.preference_service.get_user_context(
                    user_id=user_id,
                    session_id=session_id,
                )
            except Exception as e:
                logger.warning(f"[PersonalizedRouter] Failed to get user context: {e}")

        # Retrieve documents
        # Over-fetch to allow for re-ranking
        fetch_limit = min(limit * 2, 50)
        documents = await self.backend.retrieve(
            query=query,
            limit=fetch_limit,
            filters=filters,
            config=backend_config,
        )

        if not documents:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return PersonalizedResult(
                documents=[],
                retrieval_time_ms=elapsed_ms,
                config_used=config,
            )

        # Apply personalization if we have user context
        personalization_scores: Dict[str, float] = {}
        user_context_applied = False
        session_context_applied = False

        if user_context:
            documents, personalization_scores = self._apply_personalization(
                documents=documents,
                user_context=user_context,
                config=config,
            )
            user_context_applied = True

            # Check if session context was used
            if user_context.session_embedding is not None:
                session_context_applied = True

        # Re-sort by boosted score and limit
        documents = sorted(documents, key=lambda d: d.score, reverse=True)[:limit]

        # Update ranks
        for i, doc in enumerate(documents):
            doc.rank = i + 1

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        logger.info(
            f"[PersonalizedRouter] Retrieved {len(documents)} docs | "
            f"user_ctx={user_context_applied} | session_ctx={session_context_applied} | "
            f"time={elapsed_ms}ms"
        )

        return PersonalizedResult(
            documents=documents,
            user_context_applied=user_context_applied,
            session_context_applied=session_context_applied,
            personalization_scores=personalization_scores,
            retrieval_time_ms=elapsed_ms,
            ab_variant="treatment" if config.ab_test_enabled else None,
            config_used=config,
        )

    def _apply_personalization(
        self,
        documents: List[RetrievalResult],
        user_context: Any,
        config: PersonalizedRetrievalConfig,
    ) -> tuple[List[RetrievalResult], Dict[str, float]]:
        """Apply personalization boosts to documents.

        Args:
            documents: Retrieved documents
            user_context: User context from preference service
            config: Personalization configuration

        Returns:
            Tuple of (boosted documents, personalization scores)
        """
        personalization_scores: Dict[str, float] = {}

        for doc in documents:
            original_score = doc.score
            boost = 0.0

            # 1. Dimension affinity boost
            doc_dimension = doc.metadata.get("dimension")
            if doc_dimension and hasattr(user_context, "dimension_affinities"):
                dimension_affinity = user_context.dimension_affinities.get(doc_dimension, 0.0)
                if dimension_affinity >= config.min_affinity_threshold:
                    boost += config.dimension_affinity_boost * dimension_affinity

            # 2. Auteur affinity boost
            doc_auteur = doc.metadata.get("auteur_key")
            if doc_auteur and hasattr(user_context, "auteur_affinities"):
                auteur_affinity = user_context.auteur_affinities.get(doc_auteur, 0.0)
                if auteur_affinity >= config.min_affinity_threshold:
                    boost += config.auteur_affinity_boost * auteur_affinity

            # 3. User embedding similarity boost
            if hasattr(user_context, "user_embedding") and user_context.user_embedding is not None:
                doc_embedding = doc.metadata.get("embedding")
                if doc_embedding:
                    similarity = self._cosine_similarity(
                        user_context.user_embedding, doc_embedding
                    )
                    # Similarity can be negative, normalize to 0-1
                    similarity = (similarity + 1) / 2
                    boost += config.user_embedding_weight * similarity

            # Apply boost (multiplicative + additive hybrid)
            # New score = original * (1 + boost) to preserve relative ordering
            new_score = original_score * (1 + boost)
            doc.score = new_score

            # Store personalization score
            personalization_scores[doc.doc_id] = boost

            # Add personalization metadata
            doc.metadata["personalization_boost"] = boost
            doc.metadata["original_score"] = original_score

        return documents, personalization_scores

    def _apply_affinity_boost(
        self,
        documents: List[RetrievalResult],
        user_context: Any,
        config: PersonalizedRetrievalConfig,
    ) -> List[RetrievalResult]:
        """Apply dimension and auteur affinity boosts.

        Args:
            documents: Retrieved documents
            user_context: User context with affinities
            config: Personalization configuration

        Returns:
            Documents with affinity boosts applied
        """
        for doc in documents:
            boost = 0.0

            # Dimension boost
            doc_dimension = doc.metadata.get("dimension")
            if doc_dimension and hasattr(user_context, "dimension_affinities"):
                affinity = user_context.dimension_affinities.get(doc_dimension, 0.0)
                if affinity >= config.min_affinity_threshold:
                    boost += config.dimension_affinity_boost * affinity

            # Auteur boost
            doc_auteur = doc.metadata.get("auteur_key")
            if doc_auteur and hasattr(user_context, "auteur_affinities"):
                affinity = user_context.auteur_affinities.get(doc_auteur, 0.0)
                if affinity >= config.min_affinity_threshold:
                    boost += config.auteur_affinity_boost * affinity

            doc.score *= (1 + boost)

        return documents

    def _apply_embedding_similarity(
        self,
        documents: List[RetrievalResult],
        user_context: Any,
        config: PersonalizedRetrievalConfig,
    ) -> List[RetrievalResult]:
        """Boost results similar to user embedding.

        Args:
            documents: Retrieved documents
            user_context: User context with embedding
            config: Personalization configuration

        Returns:
            Documents with embedding similarity boosts
        """
        if not hasattr(user_context, "user_embedding") or user_context.user_embedding is None:
            return documents

        user_embedding = user_context.user_embedding

        for doc in documents:
            doc_embedding = doc.metadata.get("embedding")
            if doc_embedding:
                similarity = self._cosine_similarity(user_embedding, doc_embedding)
                # Normalize similarity to 0-1 range
                similarity = (similarity + 1) / 2
                boost = config.user_embedding_weight * similarity
                doc.score *= (1 + boost)

        return documents

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity (-1 to 1)
        """
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


# =============================================================================
# Singleton Instance
# =============================================================================

_personalized_router: Optional[PersonalizedRAGRouter] = None


def get_personalized_router() -> PersonalizedRAGRouter:
    """Get singleton personalized router instance."""
    global _personalized_router
    if _personalized_router is None:
        _personalized_router = PersonalizedRAGRouter()
    return _personalized_router


# =============================================================================
# Convenience Function
# =============================================================================

async def personalized_query(
    query: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None,
    backend_config: Optional[Dict[str, Any]] = None,
    personalization_config: Optional[Dict[str, Any]] = None,
) -> PersonalizedResult:
    """Convenience function for personalized retrieval.

    Args:
        query: Search query
        user_id: User identifier
        session_id: Session identifier
        limit: Maximum results
        filters: Metadata filters
        backend_config: Backend configuration
        personalization_config: Personalization settings

    Returns:
        PersonalizedResult with boosted documents
    """
    router = get_personalized_router()
    return await router.retrieve(
        query=query,
        user_id=user_id,
        session_id=session_id,
        limit=limit,
        filters=filters,
        backend_config=backend_config,
        personalization_config=personalization_config,
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "PersonalizedRetrievalConfig",
    "PersonalizedResult",
    "PersonalizedRAGRouter",
    "get_personalized_router",
    "personalized_query",
]
