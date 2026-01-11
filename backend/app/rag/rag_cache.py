"""
DEPRECATED: Use hybrid_query(use_semantic_cache=True) directly.

This module exists only for backward compatibility.
Will be removed in v2.1.

Migration:
    # Before (deprecated)
    from app.rag.rag_cache import get_rag_cache
    cache = get_rag_cache()
    result = await cache.get_or_query(query, auteur_key="bong")
    
    # After (recommended)
    from app.rag.hybrid_rag import hybrid_query
    result = await hybrid_query(query, auteur_key="bong", use_semantic_cache=True)
"""
from __future__ import annotations

import warnings
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def get_or_query(
    query: str,
    auteur_key: Optional[str] = None,
    dimension: Optional[str] = None,
    use_google_search: bool = False,
    **kwargs,
) -> Any:
    """Deprecated: redirect to hybrid_query.
    
    .. deprecated::
        Use `hybrid_query(use_semantic_cache=True)` directly.
    """
    warnings.warn(
        "rag_cache.get_or_query is deprecated. "
        "Use 'from app.rag.hybrid_rag import hybrid_query' directly.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    from app.rag.hybrid_rag import hybrid_query
    
    logger.debug(f"[rag_cache] DEPRECATED shim called, redirecting to hybrid_query")
    
    return await hybrid_query(
        query=query,
        auteur_key=auteur_key,
        dimension=dimension,
        use_google_search=use_google_search,
        use_semantic_cache=True,
    )


# =============================================================================
# Legacy Compatibility (for existing imports)
# =============================================================================

class RAGCache:
    """Deprecated wrapper class.
    
    .. deprecated::
        This class is a thin shim. Use `hybrid_query` directly.
    """
    
    async def get_or_query(
        self,
        query: str,
        auteur_key: Optional[str] = None,
        dimension: Optional[str] = None,
        use_google_search: bool = False,
        **kwargs,
    ) -> Any:
        """Redirect to module-level function."""
        return await get_or_query(
            query=query,
            auteur_key=auteur_key,
            dimension=dimension,
            use_google_search=use_google_search,
            **kwargs,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Return empty stats (deprecated)."""
        return {
            "deprecated": True,
            "message": "Use semantic_cache stats instead",
        }
    
    def clear(self) -> None:
        """No-op (deprecated)."""
        pass


_rag_cache: Optional[RAGCache] = None


def get_rag_cache() -> RAGCache:
    """Deprecated: returns shim instance.
    
    .. deprecated::
        Use `hybrid_query(use_semantic_cache=True)` directly.
    """
    global _rag_cache
    if _rag_cache is None:
        _rag_cache = RAGCache()
    return _rag_cache


def reset_rag_cache() -> None:
    """Reset cache (for testing)."""
    global _rag_cache
    _rag_cache = None
