"""RAG Caching Layer.

멀티레이어 캐싱으로 RAG 쿼리 효율성 극대화.
- 쿼리 결과 캐싱 (LRU + TTL)
- 히트율 모니터링
- Redis 통합 (선택적)

Usage:
    from app.rag.rag_cache import get_rag_cache
    
    cache = get_rag_cache()
    result = await cache.get_or_query(
        query="봉준호 감독 스타일",
        auteur_key="bong",
        dimension="AD"
    )
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from collections import OrderedDict

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """캐시 통계 - 프로덕션 모니터링용."""
    hits: int = 0
    misses: int = 0
    total_query_time_ms: float = 0.0
    auteur_hits: Dict[str, int] = field(default_factory=dict)
    dimension_hits: Dict[str, int] = field(default_factory=dict)
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def avg_query_time_ms(self) -> float:
        total = self.hits + self.misses
        return self.total_query_time_ms / total if total > 0 else 0.0
    
    def record_hit(self, auteur_key: Optional[str] = None, dimension: Optional[str] = None):
        self.hits += 1
        if auteur_key:
            self.auteur_hits[auteur_key] = self.auteur_hits.get(auteur_key, 0) + 1
        if dimension:
            self.dimension_hits[dimension] = self.dimension_hits.get(dimension, 0) + 1
    
    def record_miss(self, query_time_ms: float = 0.0):
        self.misses += 1
        self.total_query_time_ms += query_time_ms
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{self.hit_rate:.1%}",
            "avg_query_time_ms": round(self.avg_query_time_ms, 2),
            "top_auteurs": dict(sorted(self.auteur_hits.items(), key=lambda x: -x[1])[:5]),
            "top_dimensions": dict(sorted(self.dimension_hits.items(), key=lambda x: -x[1])[:5]),
        }


@dataclass
class CacheEntry:
    """캐시 엔트리."""
    value: Any
    created_at: datetime
    ttl_seconds: int
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)


class RAGCache:
    """LRU + TTL 기반 RAG 결과 캐시.
    
    Features:
    - LRU (Least Recently Used) 제거 정책
    - TTL 기반 자동 만료
    - 캐시 통계 제공
    """
    
    def __init__(
        self,
        max_size: int = 100,
        default_ttl: int = 3600,  # 1시간
    ):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._stats = CacheStats()
    
    def _make_key(
        self,
        query: str,
        auteur_key: Optional[str] = None,
        dimension: Optional[str] = None,
    ) -> str:
        """캐시 키 생성."""
        key_data = {
            "q": query[:200],  # 쿼리 앞부분만
            "a": auteur_key,
            "d": dimension,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회."""
        entry = self._cache.get(key)
        
        if entry is None:
            self._stats.misses += 1
            return None
        
        if entry.is_expired:
            del self._cache[key]
            self._stats.misses += 1
            return None
        
        # LRU: 최근 사용으로 이동
        self._cache.move_to_end(key)
        self._stats.hits += 1
        return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """캐시에 값 저장."""
        # 용량 초과 시 가장 오래된 항목 제거
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)
        
        self._cache[key] = CacheEntry(
            value=value,
            created_at=datetime.now(),
            ttl_seconds=ttl or self._default_ttl,
        )
    
    async def get_or_query(
        self,
        query: str,
        auteur_key: Optional[str] = None,
        dimension: Optional[str] = None,
        use_google_search: bool = False,
    ) -> Any:
        """캐시 조회 → 미스 시 RAG 쿼리 실행.
        
        이것이 주요 API입니다.
        """
        key = self._make_key(query, auteur_key, dimension)
        
        # 캐시 히트
        cached = self.get(key)
        if cached is not None:
            logger.debug(f"[RAG-Cache] HIT: {key[:8]}...")
            return cached
        
        # 캐시 미스 → RAG 쿼리
        logger.debug(f"[RAG-Cache] MISS: {key[:8]}... querying...")
        
        from app.rag.hybrid_rag import hybrid_query
        result = await hybrid_query(
            query=query,
            auteur_key=auteur_key,
            dimension=dimension,
            use_google_search=use_google_search,
        )
        
        # 높은 신뢰도만 캐싱 (낮은 신뢰도는 캐싱 가치 없음)
        if result.confidence >= 0.5:
            self.set(key, result)
            logger.debug(f"[RAG-Cache] Cached: confidence={result.confidence:.2f}")
        
        return result
    
    def clear(self) -> None:
        """캐시 비우기."""
        self._cache.clear()
        self._stats = CacheStats()
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환."""
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "hit_rate": f"{self._stats.hit_rate:.1%}",
            "default_ttl_seconds": self._default_ttl,
        }


# Singleton
_rag_cache: Optional[RAGCache] = None


def get_rag_cache() -> RAGCache:
    """RAG 캐시 싱글톤 반환."""
    global _rag_cache
    if _rag_cache is None:
        _rag_cache = RAGCache()
    return _rag_cache


def reset_rag_cache() -> None:
    """캐시 리셋 (테스트용)."""
    global _rag_cache
    _rag_cache = None
