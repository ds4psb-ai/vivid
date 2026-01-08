"""Vertex AI Ranking API Reranker.

Vertex AI Ranking API를 사용한 문서 리랭킹 서비스.
검색 결과의 관련성을 향상시키기 위한 2-stage retrieval의 2단계.

Models:
- semantic-ranker-default-004: 정확도 최적화 (기본)
- semantic-ranker-fast-004: 지연시간 최적화

Usage:
    from app.rag.reranker import rerank_documents
    
    reranked = await rerank_documents(
        query="봉준호 감독의 계단 상징",
        documents=[{"text": "기생충에서 계단은...", "id": "1"}, ...],
        top_k=5,
    )

Reference:
- https://cloud.google.com/generative-ai-app-builder/docs/ranking
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING

from app.config import settings

logger = logging.getLogger(__name__)

# Lazy import for discoveryengine (optional dependency)
_discoveryengine = None


# ============================================================================
# Constants
# ============================================================================

RERANKER_MODELS = Literal["semantic-ranker-default-004", "semantic-ranker-fast-004"]
DEFAULT_MODEL = "semantic-ranker-default-004"
MAX_RECORDS_PER_REQUEST = 200
MAX_TOKENS_PER_REQUEST = 200000


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class RerankResult:
    """리랭킹 결과."""
    documents: List[Dict[str, Any]]  # 리랭킹된 문서 목록 (score 포함)
    query: str
    model: str
    latency_ms: int
    original_count: int
    reranked_count: int


@dataclass
class DocumentToRank:
    """리랭킹할 문서."""
    id: str
    text: str
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# Reranker Service
# ============================================================================

class VertexReranker:
    """Vertex AI Ranking API 기반 리랭커."""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "global",
        model: RERANKER_MODELS = DEFAULT_MODEL,
    ):
        self.project_id = project_id or settings.GOOGLE_CLOUD_PROJECT
        self.location = location
        self.model = model
        self._client: Optional[Any] = None
    
    @property
    def client(self) -> Any:
        """Lazy initialization of client with lazy package import."""
        if self._client is None:
            global _discoveryengine
            if _discoveryengine is None:
                try:
                    from google.cloud import discoveryengine_v1alpha
                    _discoveryengine = discoveryengine_v1alpha
                except ImportError:
                    raise ImportError(
                        "google-cloud-discoveryengine not installed. "
                        "Run: pip install google-cloud-discoveryengine"
                    )
            self._client = _discoveryengine.RankServiceClient()
        return self._client
    
    @property
    def ranking_config(self) -> str:
        """Get ranking config resource name."""
        return (
            f"projects/{self.project_id}"
            f"/locations/{self.location}"
            f"/rankingConfigs/default_ranking_config"
        )
    
    async def rerank(
        self,
        query: str,
        documents: List[DocumentToRank],
        top_k: Optional[int] = None,
    ) -> RerankResult:
        """문서 리랭킹 수행.
        
        Args:
            query: 검색 쿼리
            documents: 리랭킹할 문서 목록
            top_k: 반환할 상위 문서 수 (None이면 전체)
            
        Returns:
            RerankResult with reranked documents
        """
        if not documents:
            return RerankResult(
                documents=[],
                query=query,
                model=self.model,
                latency_ms=0,
                original_count=0,
                reranked_count=0,
            )
        
        start_time = time.monotonic()
        
        try:
            # Ensure client is initialized (triggers lazy import)
            _ = self.client
            
            # Prepare records
            records = [
                _discoveryengine.RankingRecord(
                    id=doc.id,
                    content=doc.text[:1024],  # Max 1024 tokens per record
                )
                for doc in documents[:MAX_RECORDS_PER_REQUEST]
            ]
            
            # Build request
            request = _discoveryengine.RankRequest(
                ranking_config=self.ranking_config,
                model=self.model,
                query=query,
                records=records,
                top_n=top_k or len(records),
            )
            
            # Call API
            response = self.client.rank(request=request)
            
            latency_ms = int((time.monotonic() - start_time) * 1000)
            
            # Build result with scores
            reranked_docs = []
            doc_map = {doc.id: doc for doc in documents}
            
            for record in response.records:
                if record.id in doc_map:
                    original_doc = doc_map[record.id]
                    reranked_docs.append({
                        "id": record.id,
                        "text": original_doc.text,
                        "score": record.score,
                        "metadata": original_doc.metadata,
                    })
            
            logger.info(
                f"[Reranker] Reranked {len(documents)} → {len(reranked_docs)} docs "
                f"in {latency_ms}ms (model={self.model})"
            )
            
            return RerankResult(
                documents=reranked_docs,
                query=query,
                model=self.model,
                latency_ms=latency_ms,
                original_count=len(documents),
                reranked_count=len(reranked_docs),
            )
            
        except Exception as e:
            latency_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(f"[Reranker] Error: {e}")
            
            # Fallback: return original order with no scores
            docs_to_return = documents[:top_k] if top_k else documents
            fallback_docs = [
                {
                    "id": doc.id,
                    "text": doc.text,
                    "score": 0.0,
                    "metadata": doc.metadata,
                }
                for doc in docs_to_return
            ]
            
            return RerankResult(
                documents=fallback_docs,
                query=query,
                model=self.model,
                latency_ms=latency_ms,
                original_count=len(documents),
                reranked_count=len(fallback_docs),
            )


# ============================================================================
# Convenience Functions
# ============================================================================

_reranker: Optional[VertexReranker] = None


def get_reranker(model: RERANKER_MODELS = DEFAULT_MODEL) -> VertexReranker:
    """리랭커 싱글톤 반환."""
    global _reranker
    if _reranker is None or _reranker.model != model:
        _reranker = VertexReranker(model=model)
    return _reranker


async def rerank_documents(
    query: str,
    documents: List[Dict[str, Any]],
    top_k: Optional[int] = None,
    model: RERANKER_MODELS = DEFAULT_MODEL,
    text_key: str = "text",
    id_key: str = "id",
) -> List[Dict[str, Any]]:
    """간편한 리랭킹 함수.
    
    Args:
        query: 검색 쿼리
        documents: 문서 목록 (text, id 키 필요)
        top_k: 반환할 상위 문서 수
        model: 리랭킹 모델
        text_key: 문서 텍스트 키
        id_key: 문서 ID 키
        
    Returns:
        리랭킹된 문서 목록 (score 추가됨)
    """
    if not documents:
        return []
    
    # Convert to DocumentToRank
    docs_to_rank = []
    for i, doc in enumerate(documents):
        doc_id = str(doc.get(id_key, i))
        doc_text = doc.get(text_key, "")
        docs_to_rank.append(DocumentToRank(
            id=doc_id,
            text=doc_text,
            metadata={k: v for k, v in doc.items() if k not in [text_key, id_key]},
        ))
    
    reranker = get_reranker(model)
    result = await reranker.rerank(query, docs_to_rank, top_k)
    
    return result.documents


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "VertexReranker",
    "RerankResult",
    "DocumentToRank",
    "get_reranker",
    "rerank_documents",
    "RERANKER_MODELS",
    "DEFAULT_MODEL",
]
