"""
Source Type Resolver

domain_sources (ContentDomain) → 적절한 RAG 소스 라우팅.
Intent의 domain_sources 값에 따라 NotebookLM, Dimension RAG, 또는 특수 소스를 선택합니다.

Architecture:
    CreativeIntent.domain_sources 
        → SourceTypeResolver.resolve() 
        → RAG 소스 선택 + 쿼리 실행
        → Context injection into Capsule Resolver
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

from app.schemas.creative_intent import ContentDomain, CreativeIntent

logger = logging.getLogger(__name__)


# =========================================================================
# Source Type Definitions
# =========================================================================

class RAGSourceType(str, Enum):
    """사용 가능한 RAG 소스 타입"""
    NOTEBOOKLM = "notebooklm"       # Tier 0: NotebookLM
    DIMENSION_RAG = "dimension"     # Tier 1: Dimension-specific
    LIGHTRAG = "lightrag"           # Graph-based entity search
    SAJU_DB = "saju"                # Future: 사주 데이터베이스
    PAPER_DB = "paper"              # Future: 학술 논문
    BOOK_DB = "book"                # Future: 책/문헌


@dataclass
class ResolvedSource:
    """Resolver가 반환하는 RAG 소스 정보"""
    source_type: RAGSourceType
    notebook_id: Optional[str] = None  # NotebookLM용
    corpus_id: Optional[str] = None    # VertexRAG용
    dimension_code: Optional[str] = None  # Dimension RAG용
    query_hints: List[str] = field(default_factory=list)
    priority: int = 0  # 높을수록 우선


@dataclass
class RAGContextResult:
    """RAG 조회 결과"""
    sources_used: List[str]
    context: Dict[str, Any]
    formatted_context: str
    total_results: int = 0
    latency_ms: int = 0


# =========================================================================
# Domain → Source Mapping
# =========================================================================

# ContentDomain → RAGSourceType 매핑
DOMAIN_TO_SOURCES: Dict[ContentDomain, List[ResolvedSource]] = {
    # Auteur 스타일 → NotebookLM DNA notebooks
    ContentDomain.AUTEUR_BONG: [
        ResolvedSource(
            source_type=RAGSourceType.NOTEBOOKLM,
            notebook_id="DNA_봉준호",
            query_hints=["visual grammar", "composition", "tension"],
            priority=10,
        ),
    ],
    ContentDomain.AUTEUR_TARANTINO: [
        ResolvedSource(
            source_type=RAGSourceType.NOTEBOOKLM,
            notebook_id="DNA_타란티노",
            query_hints=["dialogue", "violence aesthetic", "nonlinear"],
            priority=10,
        ),
    ],
    ContentDomain.AUTEUR_NOLAN: [
        ResolvedSource(
            source_type=RAGSourceType.NOTEBOOKLM,
            notebook_id="DNA_놀란",
            query_hints=["temporal structure", "practical effects", "IMAX"],
            priority=10,
        ),
    ],
    ContentDomain.AUTEUR_VILLENEUVE: [
        ResolvedSource(
            source_type=RAGSourceType.NOTEBOOKLM,
            notebook_id="DNA_빌뇌브",
            query_hints=["atmosphere", "scale", "minimalism"],
            priority=10,
        ),
    ],
    ContentDomain.AUTEUR_WONG: [
        ResolvedSource(
            source_type=RAGSourceType.NOTEBOOKLM,
            notebook_id="DNA_왕가위",
            query_hints=["neon", "slow motion", "urban romance"],
            priority=10,
        ),
    ],
    
    # 장르 기반 → Dimension RAG
    ContentDomain.GENRE_DRAMA: [
        ResolvedSource(
            source_type=RAGSourceType.DIMENSION_RAG,
            dimension_code="STORY",
            query_hints=["character arc", "emotional conflict"],
            priority=7,
        ),
    ],
    ContentDomain.GENRE_THRILLER: [
        ResolvedSource(
            source_type=RAGSourceType.DIMENSION_RAG,
            dimension_code="1D",
            query_hints=["tension", "suspense", "pacing"],
            priority=7,
        ),
    ],
    ContentDomain.GENRE_COMEDY: [
        ResolvedSource(
            source_type=RAGSourceType.DIMENSION_RAG,
            dimension_code="STORY",
            query_hints=["timing", "setup-payoff", "physical comedy"],
            priority=7,
        ),
    ],
    ContentDomain.GENRE_HORROR: [
        ResolvedSource(
            source_type=RAGSourceType.DIMENSION_RAG,
            dimension_code="1D",
            query_hints=["dread", "jump scare", "atmosphere"],
            priority=7,
        ),
    ],
    ContentDomain.GENRE_SCIFI: [
        ResolvedSource(
            source_type=RAGSourceType.DIMENSION_RAG,
            dimension_code="3D",
            query_hints=["worldbuilding", "technology", "visual effects"],
            priority=7,
        ),
    ],
    ContentDomain.GENRE_DOCUMENTARY: [
        ResolvedSource(
            source_type=RAGSourceType.DIMENSION_RAG,
            dimension_code="4D",
            query_hints=["authenticity", "interview", "b-roll"],
            priority=7,
        ),
    ],
    
    # 특수 소스 → Future integration
    ContentDomain.SOURCE_SAJU: [
        ResolvedSource(
            source_type=RAGSourceType.SAJU_DB,
            query_hints=["오행", "일간", "운세"],
            priority=8,
        ),
        # Fallback to NotebookLM if SAJU_DB not available
        ResolvedSource(
            source_type=RAGSourceType.NOTEBOOKLM,
            notebook_id="사주_기초",
            priority=3,
        ),
    ],
    ContentDomain.SOURCE_PAPER: [
        ResolvedSource(
            source_type=RAGSourceType.PAPER_DB,
            query_hints=["methodology", "findings", "citation"],
            priority=8,
        ),
    ],
    ContentDomain.SOURCE_BOOK: [
        ResolvedSource(
            source_type=RAGSourceType.BOOK_DB,
            query_hints=["excerpt", "theme", "analysis"],
            priority=8,
        ),
    ],
    ContentDomain.SOURCE_PHILOSOPHY: [
        ResolvedSource(
            source_type=RAGSourceType.LIGHTRAG,
            query_hints=["주역", "concept", "principle"],
            priority=8,
        ),
    ],
}


# =========================================================================
# Source Type Resolver
# =========================================================================

class SourceTypeResolver:
    """
    domain_sources → RAG 소스 라우팅 Resolver
    
    Usage:
        ```python
        resolver = SourceTypeResolver()
        
        # Intent에서 소스 결정
        sources = resolver.resolve_sources(intent)
        
        # RAG 컨텍스트 조회
        context = await resolver.get_rag_context(intent, query="visual style")
        ```
    """
    
    def __init__(self):
        self._available_sources: Set[RAGSourceType] = {
            RAGSourceType.NOTEBOOKLM,
            RAGSourceType.DIMENSION_RAG,
            RAGSourceType.LIGHTRAG,
        }
        # Future sources (not yet implemented)
        self._future_sources: Set[RAGSourceType] = {
            RAGSourceType.SAJU_DB,
            RAGSourceType.PAPER_DB,
            RAGSourceType.BOOK_DB,
        }
    
    def resolve_sources(
        self, 
        intent: CreativeIntent,
    ) -> List[ResolvedSource]:
        """
        Intent의 domain_sources에서 사용할 RAG 소스 결정
        
        Returns:
            우선순위 순으로 정렬된 ResolvedSource 리스트
        """
        sources: List[ResolvedSource] = []
        
        for domain in intent.domain_sources:
            domain_sources = DOMAIN_TO_SOURCES.get(domain, [])
            for source in domain_sources:
                # 사용 가능한 소스만 포함
                if source.source_type in self._available_sources:
                    sources.append(source)
                elif source.source_type in self._future_sources:
                    logger.debug(f"Source {source.source_type.value} not yet available")
        
        # 기본 Dimension RAG 추가 (domain_sources 비어있을 때)
        if not sources:
            sources.append(ResolvedSource(
                source_type=RAGSourceType.DIMENSION_RAG,
                dimension_code="1D",  # Default to prompt dimension
                priority=1,
            ))
        
        # 우선순위 내림차순 정렬
        sources.sort(key=lambda s: s.priority, reverse=True)
        
        logger.debug(f"Resolved {len(sources)} sources for intent: {[s.source_type.value for s in sources]}")
        return sources
    
    async def get_rag_context(
        self,
        intent: CreativeIntent,
        query: str,
        max_sources: int = 3,
    ) -> RAGContextResult:
        """
        Intent 기반 RAG 컨텍스트 조회
        
        Args:
            intent: 창작 의도
            query: 검색 쿼리
            max_sources: 최대 소스 수
            
        Returns:
            통합된 RAG 컨텍스트
        """
        import time
        start = time.monotonic()
        
        sources = self.resolve_sources(intent)[:max_sources]
        contexts: Dict[str, Any] = {}
        formatted_parts: List[str] = []
        total_results = 0
        sources_used: List[str] = []
        
        for source in sources:
            try:
                result = await self._query_source(source, query, intent)
                if result:
                    contexts[source.source_type.value] = result
                    formatted_parts.append(result.get("formatted", ""))
                    total_results += result.get("count", 0)
                    sources_used.append(source.source_type.value)
            except Exception as e:
                logger.warning(f"Source {source.source_type.value} query failed: {e}")
        
        latency_ms = int((time.monotonic() - start) * 1000)
        
        return RAGContextResult(
            sources_used=sources_used,
            context=contexts,
            formatted_context="\n\n".join(formatted_parts),
            total_results=total_results,
            latency_ms=latency_ms,
        )
    
    async def _query_source(
        self,
        source: ResolvedSource,
        query: str,
        intent: CreativeIntent,
    ) -> Optional[Dict[str, Any]]:
        """개별 소스 쿼리"""
        
        # Query hints 추가
        enhanced_query = query
        if source.query_hints:
            hints = " ".join(source.query_hints[:2])
            enhanced_query = f"{query} {hints}"
        
        if source.source_type == RAGSourceType.NOTEBOOKLM:
            return await self._query_notebooklm(source.notebook_id, enhanced_query)

        elif source.source_type == RAGSourceType.DIMENSION_RAG:
            return await self._query_dimension_rag(source.dimension_code, enhanced_query)
        
        elif source.source_type == RAGSourceType.LIGHTRAG:
            return await self._query_lightrag(enhanced_query)
        
        return None
    
    async def _query_notebooklm(
        self, 
        notebook_id: Optional[str], 
        query: str
    ) -> Optional[Dict[str, Any]]:
        """NotebookLM 쿼리"""
        try:
            from app.rag import get_notebooklm_service
            service = get_notebooklm_service()
            
            if notebook_id:
                result = await service.query_notebook(notebook_id, query)
            else:
                result = await service.search(query)
            
            return {
                "formatted": result.formatted_context if hasattr(result, 'formatted_context') else str(result),
                "count": 1,
                "source": "notebooklm",
            }
        except Exception as e:
            logger.debug(f"NotebookLM query failed: {e}")
            return None

    async def _query_dimension_rag(
        self, 
        dimension_code: Optional[str], 
        query: str
    ) -> Optional[Dict[str, Any]]:
        """Dimension RAG 쿼리"""
        try:
            from app.rag import get_dimension_rag
            rag = get_dimension_rag(dimension_code or "1D")
            
            results = rag.search(query, limit=3)
            
            if results:
                formatted = "\n".join([r.get("content", "") for r in results[:3]])
                return {
                    "formatted": formatted,
                    "count": len(results),
                    "source": f"dimension_{dimension_code}",
                }
        except Exception as e:
            logger.debug(f"DimensionRAG query failed: {e}")
        return None
    
    async def _query_lightrag(self, query: str) -> Optional[Dict[str, Any]]:
        """LightRAG 그래프 검색"""
        try:
            from app.rag import get_lightrag_adapter
            adapter = get_lightrag_adapter()
            
            result = await adapter.search(query, search_level="hybrid")
            
            return {
                "formatted": result.formatted_text if hasattr(result, 'formatted_text') else str(result),
                "count": len(result.entities) if hasattr(result, 'entities') else 1,
                "source": "lightrag",
            }
        except Exception as e:
            logger.debug(f"LightRAG query failed: {e}")
            return None


# =========================================================================
# Convenience Functions
# =========================================================================

_resolver_instance: Optional[SourceTypeResolver] = None


def get_source_resolver() -> SourceTypeResolver:
    """싱글톤 SourceTypeResolver 반환"""
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = SourceTypeResolver()
    return _resolver_instance


async def get_intent_rag_context(
    intent: CreativeIntent,
    query: str,
) -> Dict[str, Any]:
    """
    Intent 기반 RAG 컨텍스트 조회 (헬퍼 함수)
    
    Resolver integration에서 사용:
    ```python
    rag_context = await get_intent_rag_context(intent, query="visual style")
    params = await resolver.resolve_from_intent(intent, rag_context)
    ```
    """
    resolver = get_source_resolver()
    result = await resolver.get_rag_context(intent, query)
    
    return {
        "sources_used": result.sources_used,
        "formatted_context": result.formatted_context,
        "total_results": result.total_results,
        "latency_ms": result.latency_ms,
        **result.context,
    }


# =========================================================================
# Exports
# =========================================================================

__all__ = [
    "RAGSourceType",
    "ResolvedSource",
    "RAGContextResult",
    "SourceTypeResolver",
    "get_source_resolver",
    "get_intent_rag_context",
    "DOMAIN_TO_SOURCES",
]
