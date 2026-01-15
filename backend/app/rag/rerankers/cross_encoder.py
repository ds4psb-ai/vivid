"""Local Cross-Encoder Reranker.

P4: LocalCrossEncoderReranker Backend
sentence-transformers CrossEncoder를 사용한 로컬 리랭킹.

Models:
- BAAI/bge-reranker-base: 빠름, 메모리 적음, 다국어 지원 (기본값)
- BAAI/bge-reranker-large: 느림, 정확도 높음, 다국어 지원
- BAAI/bge-reranker-v2-m3: 최신, 다국어 SOTA
- cross-encoder/ms-marco-MiniLM-L-6-v2: 가장 빠름, 영어 최적화

Usage:
    from app.rag.rerankers import get_reranker

    reranker = get_reranker("local_cross_encoder")
    result = await reranker.rerank(
        query="봉준호 감독의 계단 상징",
        documents=[DocumentToRerank(id="1", text="기생충에서...")],
        top_k=5,
    )

Reference:
- https://www.sbert.net/docs/cross_encoder/usage/usage.html
- https://huggingface.co/BAAI/bge-reranker-base
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from app.rag.rerankers.base import (
    BaseReranker,
    DocumentToRerank,
    RerankResult,
    RerankerError,
)

logger = logging.getLogger(__name__)

# Lazy import for sentence_transformers (optional dependency)
_CrossEncoder = None

# ============================================================================
# Constants
# ============================================================================

# Supported models with aliases
MODEL_ALIASES: Dict[str, str] = {
    # BGE Rerankers (multilingual, recommended)
    "bge-base": "BAAI/bge-reranker-base",
    "bge-large": "BAAI/bge-reranker-large",
    "bge-v2-m3": "BAAI/bge-reranker-v2-m3",
    # MS-MARCO (English optimized, fastest)
    "ms-marco": "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "ms-marco-large": "cross-encoder/ms-marco-MiniLM-L-12-v2",
    # Jina (multilingual)
    "jina-v2": "jinaai/jina-reranker-v2-base-multilingual",
}

DEFAULT_MODEL = "bge-base"
MAX_TEXT_LENGTH = 512  # Max tokens per document


def _get_cross_encoder():
    """Lazy import CrossEncoder."""
    global _CrossEncoder
    if _CrossEncoder is None:
        try:
            from sentence_transformers import CrossEncoder

            _CrossEncoder = CrossEncoder
        except ImportError:
            raise RerankerError(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
    return _CrossEncoder


# ============================================================================
# Local Cross-Encoder Reranker Backend
# ============================================================================


class LocalCrossEncoderReranker(BaseReranker):
    """Local Cross-Encoder Reranker (BGE, ms-marco).

    sentence-transformers CrossEncoder를 사용한 로컬 리랭킹.
    GPU가 있으면 자동으로 활용합니다.

    Attributes:
        backend_id: "local_cross_encoder"
        model_name: HuggingFace 모델 이름 또는 별칭
        max_length: 최대 텍스트 길이

    Performance:
        - bge-base: ~50ms (CPU), ~10ms (GPU) per batch
        - ms-marco: ~30ms (CPU), ~5ms (GPU) per batch
        - Memory: ~500MB (base), ~1.5GB (large)
    """

    backend_id: str = "local_cross_encoder"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        max_length: int = MAX_TEXT_LENGTH,
        device: Optional[str] = None,
    ):
        """LocalCrossEncoderReranker 초기화.

        Args:
            model: 모델 이름 또는 별칭 (bge-base, ms-marco 등)
            max_length: 최대 텍스트 길이
            device: 디바이스 (None이면 자동 선택)
        """
        # Resolve alias to full model name
        self.model_name = MODEL_ALIASES.get(model, model)
        self.max_length = max_length
        self.device = device
        self._model = None

    @property
    def model(self):
        """Lazy model loading."""
        if self._model is None:
            CrossEncoder = _get_cross_encoder()
            logger.info(
                f"[LocalCrossEncoderReranker] Loading model: {self.model_name}"
            )
            self._model = CrossEncoder(
                self.model_name,
                max_length=self.max_length,
                device=self.device,
            )
            logger.info(
                f"[LocalCrossEncoderReranker] Model loaded on device: {self._model.model.device}"
            )
        return self._model

    async def rerank(
        self,
        query: str,
        documents: List[DocumentToRerank],
        top_k: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> RerankResult:
        """Cross-Encoder로 문서 리랭킹.

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
                model=self.model_name,
                latency_ms=0,
                original_count=0,
                reranked_count=0,
            )

        start_time = time.monotonic()

        try:
            # Create query-document pairs
            pairs = [
                [query, doc.text[: self.max_length]] for doc in documents
            ]

            # Run prediction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(
                None, lambda: self.model.predict(pairs)
            )

            latency_ms = int((time.monotonic() - start_time) * 1000)

            # Combine scores with documents and sort
            scored_docs = list(zip(scores, documents))
            scored_docs.sort(key=lambda x: x[0], reverse=True)

            # Apply top_k
            if top_k:
                scored_docs = scored_docs[:top_k]

            # Build result
            reranked_docs = [
                {
                    "id": doc.id,
                    "text": doc.text,
                    "rerank_score": float(score),
                    "metadata": doc.metadata or {},
                }
                for score, doc in scored_docs
            ]

            logger.info(
                f"[LocalCrossEncoderReranker] Reranked {len(documents)} → {len(reranked_docs)} docs "
                f"in {latency_ms}ms (model={self.model_name})"
            )

            return RerankResult(
                documents=reranked_docs,
                query=query,
                model=self.model_name,
                latency_ms=latency_ms,
                original_count=len(documents),
                reranked_count=len(reranked_docs),
            )

        except RerankerError:
            raise
        except Exception as e:
            latency_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(f"[LocalCrossEncoderReranker] Error: {e}")

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
                model=self.model_name,
                latency_ms=latency_ms,
                original_count=len(documents),
                reranked_count=len(fallback_docs),
                metadata={"fallback": True, "error": str(e)},
            )

    async def health_check(self) -> bool:
        """헬스 체크 - 모델 로드 가능 여부."""
        try:
            _ = self.model
            return True
        except Exception as e:
            logger.warning(f"[LocalCrossEncoderReranker] Health check failed: {e}")
            return False


__all__ = [
    "LocalCrossEncoderReranker",
    "MODEL_ALIASES",
    "DEFAULT_MODEL",
]
