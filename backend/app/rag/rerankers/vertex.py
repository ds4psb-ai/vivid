"""Vertex AI Ranking API Reranker.

P4: VertexReranker Backend (migrated from app/rag/reranker.py)
Vertex AI Ranking API를 사용한 문서 리랭킹 서비스.

Models:
- semantic-ranker-default-004: 정확도 최적화 (기본)
- semantic-ranker-fast-004: 지연시간 최적화

Usage:
    from app.rag.rerankers import get_reranker

    reranker = get_reranker("vertex")
    result = await reranker.rerank(
        query="봉준호 감독의 계단 상징",
        documents=[DocumentToRerank(id="1", text="기생충에서...")],
        top_k=5,
    )

Reference:
- https://cloud.google.com/generative-ai-app-builder/docs/ranking
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Literal, Optional

from app.config import settings
from app.rag.observability import trace_rag
from app.rag.rerankers.base import (
    BaseReranker,
    DocumentToRerank,
    RerankResult,
    RerankerError,
)

logger = logging.getLogger(__name__)

# Lazy import for discoveryengine (optional dependency)
_discoveryengine = None

# ============================================================================
# Constants
# ============================================================================

RERANKER_MODELS = Literal["semantic-ranker-default-004", "semantic-ranker-fast-004"]
DEFAULT_MODEL = "semantic-ranker-default-004"
MAX_RECORDS_PER_REQUEST = 200
MAX_TOKENS_PER_RECORD = 1024


# ============================================================================
# Vertex Reranker Backend
# ============================================================================


class VertexReranker(BaseReranker):
    """Vertex AI Ranking API 기반 리랭커.

    Google Cloud Discovery Engine의 Ranking API를 사용하여
    문서를 리랭킹합니다.

    Attributes:
        backend_id: "vertex"
        project_id: Google Cloud 프로젝트 ID
        location: API 위치 (기본값 "global")
        model: 리랭킹 모델
    """

    backend_id: str = "vertex"

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "global",
        model: RERANKER_MODELS = DEFAULT_MODEL,
    ):
        """VertexReranker 초기화.

        Args:
            project_id: Google Cloud 프로젝트 ID (기본값: settings.GOOGLE_CLOUD_PROJECT)
            location: API 위치 (기본값 "global")
            model: 리랭킹 모델
        """
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
                    raise RerankerError(
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

    @trace_rag(name="vertex_rerank", tags=["rag", "reranker", "vertex"])
    async def rerank(
        self,
        query: str,
        documents: List[DocumentToRerank],
        top_k: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> RerankResult:
        """Vertex AI Ranking API로 문서 리랭킹.

        Args:
            query: 검색 쿼리
            documents: 리랭킹할 문서 목록
            top_k: 반환할 상위 문서 수 (None이면 전체)
            config: 추가 설정 (model 오버라이드 등)

        Returns:
            RerankResult: 리랭킹 결과
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
        model = config.get("model", self.model) if config else self.model

        try:
            # Ensure client is initialized (triggers lazy import)
            _ = self.client

            # Prepare records
            records = [
                _discoveryengine.RankingRecord(
                    id=doc.id,
                    content=doc.text[:MAX_TOKENS_PER_RECORD],
                )
                for doc in documents[:MAX_RECORDS_PER_REQUEST]
            ]

            # Build request
            request = _discoveryengine.RankRequest(
                ranking_config=self.ranking_config,
                model=model,
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
                    reranked_docs.append(
                        {
                            "id": record.id,
                            "text": original_doc.text,
                            "rerank_score": record.score,
                            "metadata": original_doc.metadata or {},
                        }
                    )

            logger.info(
                f"[VertexReranker] Reranked {len(documents)} → {len(reranked_docs)} docs "
                f"in {latency_ms}ms (model={model})"
            )

            return RerankResult(
                documents=reranked_docs,
                query=query,
                model=model,
                latency_ms=latency_ms,
                original_count=len(documents),
                reranked_count=len(reranked_docs),
            )

        except RerankerError:
            raise
        except Exception as e:
            latency_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(f"[VertexReranker] Error: {e}")

            # Fallback: return original order with no scores
            docs_to_return = documents[:top_k] if top_k else documents
            fallback_docs = [
                {
                    "id": doc.id,
                    "text": doc.text,
                    "rerank_score": 0.0,
                    "metadata": doc.metadata or {},
                }
                for doc in docs_to_return
            ]

            return RerankResult(
                documents=fallback_docs,
                query=query,
                model=model,
                latency_ms=latency_ms,
                original_count=len(documents),
                reranked_count=len(fallback_docs),
                metadata={"fallback": True, "error": str(e)},
            )

    async def health_check(self) -> bool:
        """Vertex AI Ranking API 헬스 체크."""
        try:
            _ = self.client
            return True
        except Exception as e:
            logger.warning(f"[VertexReranker] Health check failed: {e}")
            return False


__all__ = [
    "VertexReranker",
    "RERANKER_MODELS",
    "DEFAULT_MODEL",
]
