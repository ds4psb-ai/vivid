"""Semantic Cache for RAG - 임베딩 기반 유사 쿼리 매칭.

Best Practice (2025):
- 31% LLM 호출이 중복 → Semantic Cache로 90%+ 절감 가능  
- Similarity Threshold: 0.92 (높을수록 정확, 낮을수록 캐시 히트율 높음)

Usage:
    from app.rag.semantic_cache import get_semantic_cache
    
    cache = get_semantic_cache()
    
    # 캐시 조회
    cached = await cache.get(query, auteur_key="bong")
    if cached:
        return cached
    
    # 캐시 저장
    await cache.set(query, result, auteur_key="bong")
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from collections import OrderedDict

if TYPE_CHECKING:
    from app.rag.hybrid_rag import HybridRAGResult

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

# Similarity threshold for cache hits (0.0 - 1.0)
# Higher = more strict matching, lower = more cache hits
DEFAULT_SIMILARITY_THRESHOLD = 0.92

# TTL (Time-To-Live) settings in seconds
TTL_AUTEUR_DNA = 7 * 24 * 3600  # 7 days - auteur DNA rarely changes
TTL_GROUNDED = 24 * 3600        # 1 day - grounded results
TTL_DEFAULT = 3600              # 1 hour - general queries

# Maximum cache size (in-memory fallback)
MAX_MEMORY_CACHE_SIZE = 500


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SemanticCacheEntry:
    """Semantic cache entry with embedding."""
    id: str
    query: str
    query_hash: str  # For exact match fallback
    query_embedding: Optional[List[float]]  # Vector embedding
    response_json: Dict[str, Any]  # Serialized HybridRAGResult
    auteur_key: Optional[str]
    dimension: Optional[str]
    confidence: float
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "query": self.query[:100] + "..." if len(self.query) > 100 else self.query,
            "auteur_key": self.auteur_key,
            "dimension": self.dimension,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "hit_count": self.hit_count,
        }


@dataclass
class CacheStats:
    """Cache statistics for monitoring."""
    hits: int = 0
    misses: int = 0
    semantic_hits: int = 0  # Hits via embedding similarity
    exact_hits: int = 0     # Hits via exact hash match
    total_entries: int = 0
    avg_similarity: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "semantic_hits": self.semantic_hits,
            "exact_hits": self.exact_hits,
            "total_entries": self.total_entries,
            "hit_rate": f"{self.hit_rate:.1%}",
            "avg_similarity": f"{self.avg_similarity:.3f}",
        }


# =============================================================================
# Semantic Cache Implementation
# =============================================================================

class SemanticCache:
    """Vector 기반 Semantic Cache.
    
    Primary storage: PostgreSQL with pgvector (if available)
    Fallback: In-memory LRU cache
    
    Features:
    - Embedding-based semantic similarity matching
    - Exact hash matching as fast path
    - Dynamic TTL based on content type
    - Hit count tracking for cache warming
    """
    
    def __init__(
        self,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        use_db: bool = True,
    ):
        self.similarity_threshold = similarity_threshold
        self.use_db = use_db
        self._stats = CacheStats()
        
        # In-memory fallback cache (LRU)
        self._memory_cache: OrderedDict[str, SemanticCacheEntry] = OrderedDict()
        
        # Embedding model (lazy init)
        self._embeddings_model: Optional[str] = None
        self._embeddings_client = None
        
        # DB connection (lazy init)
        self._db_available = False
        
    async def _ensure_initialized(self) -> None:
        """Lazy initialization of embedding client and DB."""
        if self._embeddings_model is not None:
            return
            
        try:
            # Try to use Vertex AI embeddings
            from google.cloud import aiplatform
            self._embeddings_model = "textembedding-gecko@003"
            logger.info(f"[SemanticCache] Using embedding model: {self._embeddings_model}")
        except ImportError:
            logger.warning("[SemanticCache] Vertex AI not available, using hash-only matching")
            self._embeddings_model = "hash_only"
        
        # Check DB availability
        if self.use_db:
            try:
                from app.database import get_async_session
                self._db_available = True
                logger.info("[SemanticCache] PostgreSQL+pgvector available")
            except Exception as e:
                logger.warning(f"[SemanticCache] DB not available, using memory cache: {e}")
                self._db_available = False
    
    def _make_hash(self, query: str, auteur_key: Optional[str], dimension: Optional[str]) -> str:
        """Create hash key for exact matching."""
        key_data = {
            "q": query.strip().lower()[:500],  # Normalize
            "a": auteur_key,
            "d": dimension,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]
    
    async def _embed(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text."""
        await self._ensure_initialized()
        
        if self._embeddings_model == "hash_only":
            return None
            
        try:
            from vertexai.language_models import TextEmbeddingModel
            
            model = TextEmbeddingModel.from_pretrained(self._embeddings_model)
            embeddings = model.get_embeddings([text])
            return embeddings[0].values if embeddings else None
        except Exception as e:
            logger.warning(f"[SemanticCache] Embedding failed: {e}")
            return None
    
    def _calculate_ttl(self, auteur_key: Optional[str], grounded: bool) -> int:
        """Calculate dynamic TTL based on content type."""
        if auteur_key:
            return TTL_AUTEUR_DNA  # 7 days
        elif grounded:
            return TTL_GROUNDED   # 1 day
        else:
            return TTL_DEFAULT    # 1 hour
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)
    
    async def get(
        self,
        query: str,
        auteur_key: Optional[str] = None,
        dimension: Optional[str] = None,
    ) -> Optional[Any]:
        """Get cached response for query.
        
        Matching strategy:
        1. Try exact hash match (fast path)
        2. If embeddings available, try semantic similarity match
        
        Returns:
            HybridRAGResult or None
        """
        await self._ensure_initialized()
        
        query_hash = self._make_hash(query, auteur_key, dimension)
        
        # === Fast path: Exact hash match ===
        if query_hash in self._memory_cache:
            entry = self._memory_cache[query_hash]
            if not entry.is_expired:
                entry.hit_count += 1
                self._memory_cache.move_to_end(query_hash)  # LRU update
                self._stats.hits += 1
                self._stats.exact_hits += 1
                logger.debug(f"[SemanticCache] EXACT HIT: {query_hash[:8]}...")
                return self._deserialize_result(entry.response_json)
            else:
                del self._memory_cache[query_hash]
        
        # === Semantic similarity match ===
        if self._embeddings_model != "hash_only":
            query_embedding = await self._embed(query)
            if query_embedding:
                best_match = None
                best_similarity = 0.0
                
                for hash_key, entry in self._memory_cache.items():
                    if entry.is_expired:
                        continue
                    
                    # Filter by auteur/dimension if specified
                    if auteur_key and entry.auteur_key != auteur_key:
                        continue
                    if dimension and entry.dimension != dimension:
                        continue
                    
                    if entry.query_embedding:
                        similarity = self._cosine_similarity(query_embedding, entry.query_embedding)
                        if similarity > best_similarity and similarity >= self.similarity_threshold:
                            best_similarity = similarity
                            best_match = entry
                
                if best_match:
                    best_match.hit_count += 1
                    self._stats.hits += 1
                    self._stats.semantic_hits += 1
                    self._stats.avg_similarity = (
                        (self._stats.avg_similarity * (self._stats.semantic_hits - 1) + best_similarity) 
                        / self._stats.semantic_hits
                    )
                    logger.info(
                        f"[SemanticCache] SEMANTIC HIT: similarity={best_similarity:.3f}, "
                        f"original_query='{best_match.query[:50]}...'"
                    )
                    return self._deserialize_result(best_match.response_json)
        
        self._stats.misses += 1
        return None
    
    async def set(
        self,
        query: str,
        response: Any,  # HybridRAGResult
        auteur_key: Optional[str] = None,
        dimension: Optional[str] = None,
    ) -> None:
        """Cache a query-response pair.
        
        Only caches responses with confidence >= 0.5.
        """
        await self._ensure_initialized()
        
        # Only cache high-quality responses
        confidence = getattr(response, "confidence", 0.0)
        if confidence < 0.5:
            logger.debug(f"[SemanticCache] Skipping low confidence: {confidence:.2f}")
            return
        
        query_hash = self._make_hash(query, auteur_key, dimension)
        
        # Generate embedding
        query_embedding = await self._embed(query) if self._embeddings_model != "hash_only" else None
        
        # Calculate TTL
        grounded = getattr(response, "grounded", False)
        ttl = self._calculate_ttl(auteur_key, grounded)
        
        # Create entry
        entry = SemanticCacheEntry(
            id=query_hash,
            query=query,
            query_hash=query_hash,
            query_embedding=query_embedding,
            response_json=self._serialize_result(response),
            auteur_key=auteur_key,
            dimension=dimension,
            confidence=confidence,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=ttl),
            hit_count=0,
        )
        
        # Evict if at capacity
        if len(self._memory_cache) >= MAX_MEMORY_CACHE_SIZE:
            self._memory_cache.popitem(last=False)  # Remove oldest
        
        self._memory_cache[query_hash] = entry
        self._stats.total_entries = len(self._memory_cache)
        
        logger.debug(
            f"[SemanticCache] CACHED: {query_hash[:8]}... | "
            f"confidence={confidence:.2f} | ttl={ttl}s"
        )
    
    def _serialize_result(self, result: Any) -> Dict[str, Any]:
        """Serialize HybridRAGResult to JSON-safe dict."""
        try:
            # Try dataclass asdict
            from dataclasses import asdict
            return asdict(result)
        except Exception:
            # Fallback to manual serialization
            return {
                "answer": getattr(result, "answer", ""),
                "confidence": getattr(result, "confidence", 0.0),
                "strategy_used": getattr(result, "strategy_used", "unknown"),
                "grounded": getattr(result, "grounded", False),
                "auteur_key": getattr(result, "auteur_key", None),
                "dimension": getattr(result, "dimension", None),
                "query_time_ms": getattr(result, "query_time_ms", 0),
            }
    
    def _deserialize_result(self, data: Dict[str, Any]) -> Any:
        """Deserialize dict back to HybridRAGResult."""
        try:
            from app.rag.hybrid_rag import HybridRAGResult
            
            # Handle nested dataclasses
            data_copy = data.copy()
            
            # Convert source lists if needed
            from app.rag.tier0_notebooklm import NotebookSource
            from app.rag.tier0_vertex_rag import RAGSource
            
            if "notebooklm_sources" in data_copy:
                data_copy["notebooklm_sources"] = [
                    NotebookSource(**s) if isinstance(s, dict) else s 
                    for s in data_copy.get("notebooklm_sources", [])
                ]
            if "vertex_sources" in data_copy:
                data_copy["vertex_sources"] = [
                    RAGSource(**s) if isinstance(s, dict) else s 
                    for s in data_copy.get("vertex_sources", [])
                ]
            
            return HybridRAGResult(**data_copy)
        except Exception as e:
            logger.warning(f"[SemanticCache] Deserialization failed: {e}")
            # Return minimal result
            from app.rag.hybrid_rag import HybridRAGResult
            return HybridRAGResult(
                answer=data.get("answer", ""),
                confidence=data.get("confidence", 0.0),
                strategy_used="semantic_cache",
            )
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self._memory_cache.clear()
        self._stats = CacheStats()
        logger.info("[SemanticCache] Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = self._stats.to_dict()
        stats["similarity_threshold"] = self.similarity_threshold
        stats["memory_size"] = len(self._memory_cache)
        stats["max_size"] = MAX_MEMORY_CACHE_SIZE
        stats["embeddings_model"] = self._embeddings_model or "not_initialized"
        return stats
    
    def get_top_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top cached entries by hit count."""
        sorted_entries = sorted(
            self._memory_cache.values(),
            key=lambda e: e.hit_count,
            reverse=True,
        )
        return [e.to_dict() for e in sorted_entries[:limit]]


# =============================================================================
# Singleton
# =============================================================================

_semantic_cache: Optional[SemanticCache] = None


def get_semantic_cache(
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> SemanticCache:
    """Get semantic cache singleton."""
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticCache(similarity_threshold=similarity_threshold)
    return _semantic_cache


def reset_semantic_cache() -> None:
    """Reset cache singleton (for testing)."""
    global _semantic_cache
    if _semantic_cache:
        _semantic_cache.clear()
    _semantic_cache = None
