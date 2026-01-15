"""FastEmbed-based Sparse Embedding for Qdrant Hybrid Search.

Uses Qdrant/bm25 model via FastEmbed for sparse vector generation.
Server-side IDF calculation is handled by Qdrant with Modifier.IDF.

Usage:
    embedder = SparseEmbedder()
    indices, values = embedder.embed("INTJ 성격 유형 분석")
    # indices: [45, 129, 2048, ...]
    # values: [0.42, 0.38, 0.25, ...]
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)

# Lazy import to avoid loading model at module import time
_sparse_model = None


def _get_model():
    """Lazy-load sparse embedding model."""
    global _sparse_model
    if _sparse_model is None:
        try:
            from fastembed import SparseTextEmbedding
            _sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
            logger.info("[SparseEmbedder] Loaded Qdrant/bm25 model")
        except ImportError as e:
            logger.error(f"[SparseEmbedder] fastembed not installed: {e}")
            raise
        except Exception as e:
            logger.error(f"[SparseEmbedder] Failed to load model: {e}")
            raise
    return _sparse_model


class SparseEmbedder:
    """FastEmbed 기반 Sparse Embedding 생성기.

    Qdrant/bm25 모델을 사용하여 텍스트를 sparse vector로 변환.
    Server-side IDF (Modifier.IDF)와 함께 사용하면 전통적인 BM25 검색 효과.

    Attributes:
        model_name: 사용할 모델 이름 (기본값: "Qdrant/bm25")
    """

    def __init__(self, model_name: str = "Qdrant/bm25"):
        """Initialize sparse embedder.

        Args:
            model_name: FastEmbed sparse model name.
                       Options: "Qdrant/bm25", "prithivida/Splade_PP_en_v1"
        """
        self.model_name = model_name
        self._model: Optional[object] = None

    @property
    def model(self):
        """Lazy-load embedding model."""
        if self._model is None:
            try:
                from fastembed import SparseTextEmbedding
                self._model = SparseTextEmbedding(model_name=self.model_name)
                logger.info(f"[SparseEmbedder] Loaded model: {self.model_name}")
            except ImportError as e:
                logger.error(f"[SparseEmbedder] fastembed not installed: {e}")
                raise ImportError(
                    "fastembed is required for sparse embeddings. "
                    "Install with: pip install fastembed"
                ) from e
            except Exception as e:
                logger.error(f"[SparseEmbedder] Failed to load model: {e}")
                raise
        return self._model

    def embed(self, text: str) -> Tuple[List[int], List[float]]:
        """텍스트를 Sparse Vector로 변환.

        Args:
            text: 변환할 텍스트

        Returns:
            (indices, values) 튜플
            - indices: 활성화된 토큰의 인덱스 리스트
            - values: 각 토큰의 가중치 리스트

        Raises:
            ImportError: fastembed가 설치되지 않은 경우
            RuntimeError: 임베딩 생성 실패
        """
        if not text or not text.strip():
            logger.warning("[SparseEmbedder] Empty text provided, returning empty sparse vector")
            return [], []

        try:
            embeddings = list(self.model.embed([text]))[0]
            indices = embeddings.indices.tolist()
            values = embeddings.values.tolist()

            logger.debug(
                f"[SparseEmbedder] Generated sparse vector: "
                f"{len(indices)} non-zero terms"
            )
            return indices, values
        except Exception as e:
            logger.error(f"[SparseEmbedder] Embed failed: {e}")
            raise RuntimeError(f"Sparse embedding failed: {e}") from e

    def embed_batch(self, texts: List[str]) -> List[Tuple[List[int], List[float]]]:
        """배치 임베딩 생성.

        Args:
            texts: 변환할 텍스트 리스트

        Returns:
            [(indices, values), ...] 리스트
        """
        if not texts:
            return []

        try:
            embeddings = list(self.model.embed(texts))
            results = [
                (emb.indices.tolist(), emb.values.tolist())
                for emb in embeddings
            ]
            logger.debug(f"[SparseEmbedder] Batch embedded {len(texts)} texts")
            return results
        except Exception as e:
            logger.error(f"[SparseEmbedder] Batch embed failed: {e}")
            raise RuntimeError(f"Batch sparse embedding failed: {e}") from e
