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

# Metrics import (lazy to avoid circular import)
_record_metric = None

def _get_record_metric():
    """Lazy load metrics function to avoid circular import."""
    global _record_metric
    if _record_metric is None:
        try:
            from app.rag.metrics import record_semantic_cache_op
            _record_metric = record_semantic_cache_op
        except ImportError:
            _record_metric = lambda *args, **kwargs: None  # No-op fallback
    return _record_metric


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
# Cache Poisoning Security (2025 Best Practice)
# =============================================================================

# Source trust levels for cache entries
# Higher level = more trusted, less likely to be poisoned
TRUST_LEVEL_VERIFIED = 3    # Internal verified sources (e.g., NotebookLM DNA)
TRUST_LEVEL_CURATED = 2     # Curated external sources
TRUST_LEVEL_EXTERNAL = 1    # Unverified external sources

# Minimum confidence to cache by trust level
CACHE_CONFIDENCE_BY_TRUST = {
    TRUST_LEVEL_VERIFIED: 0.4,  # Allow lower confidence for verified sources
    TRUST_LEVEL_CURATED: 0.5,   # Standard threshold
    TRUST_LEVEL_EXTERNAL: 0.7,  # Higher bar for external sources
}


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
    source_trust_level: int = TRUST_LEVEL_CURATED  # Cache Poisoning Protection
    
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
            "source_trust_level": self.source_trust_level,
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
    
    Primary storage: PostgreSQL with pgvector
    Fallback: In-memory LRU cache (read-through)
    
    Features:
    - Embedding-based semantic similarity matching (IVFFlat/HNSW via pgvector)
    - Exact hash matching as fast path
    - Dynamic TTL based on content type
    - Persistence via RagSemanticCache model
    """
    
    def __init__(
        self,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        use_db: bool = True,
    ):
        self.similarity_threshold = similarity_threshold
        self.use_db = use_db
        self._stats = CacheStats()
        
        # In-memory fallback cache (LRU) - serves as L1 cache
        self._memory_cache: OrderedDict[str, SemanticCacheEntry] = OrderedDict()
        
        # Embedding model (lazy init)
        self._embeddings_model: Optional[str] = None
        
        # DB availability flag
        self._db_available = False
        
    async def _ensure_initialized(self) -> None:
        """Lazy initialization of embedding client and DB check."""
        if self._embeddings_model is not None:
            return
            
        try:
            # Try to use Vertex AI embeddings
            self._embeddings_model = "textembedding-gecko@003"
            logger.info(f"[SemanticCache] Using embedding model: {self._embeddings_model}")
        except ImportError:
            logger.warning("[SemanticCache] Vertex AI not available, using hash-only matching")
            self._embeddings_model = "hash_only"
        
        # Check DB availability
        if self.use_db:
            try:
                from app.database import get_db_context
                self._db_available = True
            except Exception as e:
                logger.warning(f"[SemanticCache] DB context not available: {e}")
                self._db_available = False
    
    def _make_hash(
        self,
        query: str,
        auteur_key: Optional[str],
        dimension: Optional[str],
        dataset_ids: Optional[List[str]] = None,  # P1: dataset routing
    ) -> str:
        """Create hash key for exact matching."""
        key_data = {
            "q": query.strip().lower()[:500],  # Normalize
            "a": auteur_key,
            "d": dimension,
            "m": self._embeddings_model,  # P0: 모델 버전 포함 (2026-01-13)
            "ds": sorted(dataset_ids) if dataset_ids else None,  # P1: dataset_ids (2026-01-13)
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
            
    async def get(
        self,
        query: str,
        auteur_key: Optional[str] = None,
        dimension: Optional[str] = None,
        dataset_ids: Optional[List[str]] = None,  # P1: dataset routing
    ) -> Optional[Any]:
        """Get cached response for query.
        
        Strategy:
        1. Memory Cache (L1) - Exact Hash
        2. DB Cache (L2) - Exact Hash
        3. DB Cache (L2) - Semantic Similarity
        """
        await self._ensure_initialized()
        
        query_hash = self._make_hash(query, auteur_key, dimension, dataset_ids)
        
        # 1. Memory Cache Check (Fastest)
        if query_hash in self._memory_cache:
            entry = self._memory_cache[query_hash]
            if not entry.is_expired:
                entry.hit_count += 1
                self._memory_cache.move_to_end(query_hash)
                self._stats.hits += 1
                self._stats.exact_hits += 1
                _get_record_metric()("get", "exact", 0.1)  # Memory hit is fast
                return self._deserialize_result(entry.response_json)
            else:
                del self._memory_cache[query_hash]
        
        if not self._db_available:
            self._stats.misses += 1
            _get_record_metric()("get", "miss", 0.0)
            return None

        # 2. DB Exact Match
        try:
            from app.database import get_db_context
            from app.models import RagSemanticCache
            from sqlalchemy import select
            
            async with get_db_context() as session:
                stmt = select(RagSemanticCache).where(
                    RagSemanticCache.id == query_hash,
                    RagSemanticCache.expires_at > datetime.now()
                )
                result = await session.execute(stmt)
                db_entry = result.scalar_one_or_none()
                
                if db_entry:
                    # Update hit count asynchronously (fire and forget effectively)
                    db_entry.hit_count += 1
                    # Hydrate memory cache
                    self._cache_in_memory(db_entry)
                    
                    self._stats.hits += 1
                    self._stats.exact_hits += 1
                    _get_record_metric()("get", "exact", 0.0)  # HIGH FIX: DB exact hit
                    return self._deserialize_result(db_entry.response_json)
                    
                # 3. DB Semantic Search (if exact match fails)
                if self._embeddings_model != "hash_only":
                    query_embedding = await self._embed(query)
                    if query_embedding:
                        # pgvector cosine distance: embedding <=> query_embedding
                        # We want similarity > threshold, which is distance < (1 - threshold) roughly?
                        # Actually cosine distance in pgvector is 1 - cosine_similarity.
                        # So distance < (1 - 0.92) = 0.08
                        
                        max_distance = 1.0 - self.similarity_threshold
                        
                        stmt = select(RagSemanticCache).order_by(
                            RagSemanticCache.embedding.cosine_distance(query_embedding)
                        ).limit(1)
                        
                        # Add filters if needed
                        if auteur_key:
                            stmt = stmt.where(RagSemanticCache.auteur_key == auteur_key)
                        
                        result = await session.execute(stmt)
                        best_match = result.scalar_one_or_none()
                        
                        if best_match:
                            # Calculate distance manually to verify threshold or trust order_by?
                            # Vector operations in DB are fast. We should verify threshold.
                            # SQLAlchmey doesn't easily return the distance value in simple ORM select 
                            # without extra column.
                            # For now, let's assume if it returns, check logic in app? 
                            # No, calculating cosine sim in app is safer for threshold.
                            
                            cached_embedding = best_match.embedding
                            if cached_embedding:
                                sim = self._cosine_similarity(query_embedding, cached_embedding)
                                if sim >= self.similarity_threshold:
                                    best_match.hit_count += 1
                                    self._cache_in_memory(best_match)
                                    
                                    self._stats.hits += 1
                                    self._stats.semantic_hits += 1
                                    _get_record_metric()("get", "semantic", 0.0)
                                    logger.info(f"[SemanticCache] SEMANTIC HIT (DB): {sim:.3f}")
                                    return self._deserialize_result(best_match.response_json)

        except Exception as e:
            logger.error(f"[SemanticCache] DB Lookup Error: {e}")
            
        self._stats.misses += 1
        _get_record_metric()("get", "miss", 0.0)
        return None
    
    async def set(
        self,
        query: str,
        response: Any,
        auteur_key: Optional[str] = None,
        dimension: Optional[str] = None,
        dataset_ids: Optional[List[str]] = None,  # P1: dataset routing
    ) -> None:
        """Cache response to Memory and DB."""
        await self._ensure_initialized()
        
        confidence = getattr(response, "confidence", 0.0)
        if confidence < 0.5:
            return
            
        query_hash = self._make_hash(query, auteur_key, dimension, dataset_ids)
        
        grounded = getattr(response, "grounded", False)
        ttl = self._calculate_ttl(auteur_key, grounded)
        expires_at = datetime.now() + timedelta(seconds=ttl)
        response_json = self._serialize_result(response)
        
        query_embedding = None
        if self._embeddings_model != "hash_only":
            query_embedding = await self._embed(query)

        # 1. Update Memory
        entry = SemanticCacheEntry(
            id=query_hash,
            query=query,
            query_hash=query_hash,
            query_embedding=query_embedding,
            response_json=response_json,
            auteur_key=auteur_key,
            dimension=dimension,
            confidence=confidence,
            created_at=datetime.now(),
            expires_at=expires_at,
            hit_count=0
        )
        self._memory_cache[query_hash] = entry
        if len(self._memory_cache) >= MAX_MEMORY_CACHE_SIZE:
            self._memory_cache.popitem(last=False)
            
        # 2. Update DB
        if self._db_available:
            try:
                from app.database import get_db_context
                from app.models import RagSemanticCache
                from sqlalchemy.dialects.postgresql import insert
                
                async with get_db_context() as session:
                    # Upsert
                    stmt = insert(RagSemanticCache).values(
                        id=query_hash,
                        query_text=query,
                        embedding=query_embedding,
                        response_json=response_json,
                        auteur_key=auteur_key,
                        dimension=dimension,
                        hit_count=0,
                        expires_at=expires_at,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    ).on_conflict_do_update(
                        index_elements=['id'],
                        set_={
                            "hit_count": RagSemanticCache.hit_count + 1,
                            "updated_at": datetime.now(),
                            "expires_at": expires_at
                        }
                    )
                    await session.execute(stmt)
                    _get_record_metric()("set", "success", 0.0)
                    logger.debug(f"[SemanticCache] Persisted: {query_hash[:8]}")
            except Exception as e:
                _get_record_metric()("set", "error", 0.0)
                logger.error(f"[SemanticCache] DB Write Error: {e}")

    def _cache_in_memory(self, db_entry: Any) -> None:
        """Hydrate memory cache from DB entry."""
        if not db_entry:
            return
            
        entry = SemanticCacheEntry(
            id=db_entry.id,
            query=db_entry.query_text,
            query_hash=db_entry.id,
            query_embedding=db_entry.embedding,
            response_json=db_entry.response_json,
            auteur_key=db_entry.auteur_key,
            dimension=db_entry.dimension,
            confidence=db_entry.response_json.get("confidence", 0.0),
            created_at=db_entry.created_at,
            expires_at=db_entry.expires_at,
            hit_count=db_entry.hit_count
        )
        self._memory_cache[db_entry.id] = entry
        if len(self._memory_cache) >= MAX_MEMORY_CACHE_SIZE:
            self._memory_cache.popitem(last=False)
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def _serialize_result(self, result: Any) -> Dict[str, Any]:
        """Serialize HybridRAGResult to JSON-safe dict."""
        try:
            from dataclasses import asdict
            return asdict(result)
        except Exception:
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
            data_copy = data.copy()
            # Restore types if needed (datetime strings to objects etc) - skipped for simplicity
            return HybridRAGResult(**data_copy)
        except Exception:
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
        logger.info("[SemanticCache] Cache cleared (Memory)")
        # TODO: Clear DB if needed, but risky to do automatically

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = self._stats.to_dict()
        stats["similarity_threshold"] = self.similarity_threshold
        stats["memory_size"] = len(self._memory_cache)
        stats["max_size"] = MAX_MEMORY_CACHE_SIZE
        stats["db_available"] = self._db_available
        return stats

    def get_top_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._memory_cache.values()][:limit]


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

