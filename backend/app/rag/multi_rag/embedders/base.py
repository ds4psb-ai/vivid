"""Base Multi-Modal Embedder (Abstract).

모든 멀티모달 임베더의 공통 인터페이스를 정의합니다.
이 추상 클래스를 상속하여 다양한 임베딩 모델을 구현합니다.

Supported Models (2026):
    - Google Gemini Multimodal
    - Meta ImageBind (6 modalities)
    - Voyage Multimodal-3
    - TwelveLabs Embed API
    - CLIP ViT-L/14
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from app.rag.multi_rag.types import (
    EmbeddingResult,
    Modality,
    SparseEmbeddingResult,
)


class EmbedderError(Exception):
    """임베더 관련 에러."""

    pass


class ModalityNotSupportedError(EmbedderError):
    """지원하지 않는 모달리티 에러."""

    def __init__(self, modality: Modality, model_name: str) -> None:
        self.modality = modality
        self.model_name = model_name
        super().__init__(
            f"Modality '{modality.value}' is not supported by {model_name}"
        )


class BaseMultiModalEmbedder(ABC):
    """멀티모달 임베더 베이스 클래스."""

    def __init__(
        self,
        model_name: str,
        embedding_dim: int,
        supported_modalities: list[Modality],
    ) -> None:
        """Initialize embedder.

        Args:
            model_name: 모델 이름
            embedding_dim: 임베딩 차원
            supported_modalities: 지원 모달리티 목록
        """
        self._model_name = model_name
        self._embedding_dim = embedding_dim
        self._supported_modalities = supported_modalities

    @property
    def model_name(self) -> str:
        """모델 이름."""
        return self._model_name

    @property
    def embedding_dim(self) -> int:
        """임베딩 차원."""
        return self._embedding_dim

    @property
    def supported_modalities(self) -> list[Modality]:
        """지원 모달리티."""
        return self._supported_modalities

    def supports_modality(self, modality: Modality) -> bool:
        """특정 모달리티 지원 여부."""
        return modality in self._supported_modalities

    def _validate_modality(self, modality: Modality) -> None:
        """모달리티 지원 여부 검증."""
        if not self.supports_modality(modality):
            raise ModalityNotSupportedError(modality, self._model_name)

    def _create_result(
        self,
        vector: list[float],
        modality: Modality,
        start_time: float,
        tokens_used: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EmbeddingResult:
        """EmbeddingResult 생성 헬퍼."""
        return EmbeddingResult(
            vector=vector,
            modality=modality,
            model=self._model_name,
            dimensions=len(vector),
            processing_time_ms=(time.time() - start_time) * 1000,
            tokens_used=tokens_used,
            metadata=metadata or {},
        )

    # =========================================================================
    # Abstract Methods (Must Implement)
    # =========================================================================

    @abstractmethod
    async def embed_text(self, text: str) -> EmbeddingResult:
        """텍스트 임베딩.

        Args:
            text: 임베딩할 텍스트

        Returns:
            EmbeddingResult with vector

        Raises:
            ModalityNotSupportedError: TEXT 미지원 시
            EmbedderError: 임베딩 실패 시
        """
        ...

    @abstractmethod
    async def embed_image(self, image: bytes) -> EmbeddingResult:
        """이미지 임베딩.

        Args:
            image: 이미지 바이트 데이터 (PNG, JPEG, WebP)

        Returns:
            EmbeddingResult with vector

        Raises:
            ModalityNotSupportedError: IMAGE 미지원 시
            EmbedderError: 임베딩 실패 시
        """
        ...

    @abstractmethod
    async def embed_audio(self, audio: bytes) -> EmbeddingResult:
        """오디오 임베딩.

        Args:
            audio: 오디오 바이트 데이터 (WAV, MP3)

        Returns:
            EmbeddingResult with vector

        Raises:
            ModalityNotSupportedError: AUDIO 미지원 시
            EmbedderError: 임베딩 실패 시
        """
        ...

    # =========================================================================
    # Optional Methods (Override if needed)
    # =========================================================================

    async def embed_video(self, video: bytes) -> EmbeddingResult:
        """비디오 임베딩 (선택적).

        기본 구현은 지원 불가 에러를 발생시킵니다.
        비디오를 지원하는 모델은 이 메서드를 오버라이드합니다.

        Args:
            video: 비디오 바이트 데이터

        Returns:
            EmbeddingResult with vector

        Raises:
            ModalityNotSupportedError: VIDEO 미지원 시
        """
        raise ModalityNotSupportedError(Modality.VIDEO, self._model_name)

    async def embed_batch(
        self,
        texts: list[str] | None = None,
        images: list[bytes] | None = None,
        audios: list[bytes] | None = None,
    ) -> list[EmbeddingResult]:
        """배치 임베딩 (선택적).

        기본 구현은 개별 호출을 순차적으로 수행합니다.
        배치 최적화가 가능한 모델은 이 메서드를 오버라이드합니다.

        Args:
            texts: 텍스트 목록
            images: 이미지 바이트 목록
            audios: 오디오 바이트 목록

        Returns:
            EmbeddingResult 목록
        """
        results: list[EmbeddingResult] = []

        if texts:
            for text in texts:
                results.append(await self.embed_text(text))

        if images:
            for image in images:
                results.append(await self.embed_image(image))

        if audios:
            for audio in audios:
                results.append(await self.embed_audio(audio))

        return results

    async def embed_by_modality(
        self,
        content: str | bytes,
        modality: Modality,
    ) -> EmbeddingResult:
        """모달리티에 따라 적절한 임베딩 메서드 호출.

        Args:
            content: 텍스트(str) 또는 바이너리(bytes) 콘텐츠
            modality: 모달리티 타입

        Returns:
            EmbeddingResult

        Raises:
            ModalityNotSupportedError: 미지원 모달리티
            ValueError: 콘텐츠 타입 불일치
        """
        self._validate_modality(modality)

        if modality == Modality.TEXT:
            if not isinstance(content, str):
                raise ValueError("TEXT modality requires str content")
            return await self.embed_text(content)

        if not isinstance(content, bytes):
            raise ValueError(f"{modality.value} modality requires bytes content")

        if modality == Modality.IMAGE:
            return await self.embed_image(content)
        if modality == Modality.AUDIO:
            return await self.embed_audio(content)
        if modality == Modality.VIDEO:
            return await self.embed_video(content)

        raise ModalityNotSupportedError(modality, self._model_name)

    # =========================================================================
    # Sparse Embedding (BM25)
    # =========================================================================

    _sparse_embedder = None  # Class-level lazy singleton

    @classmethod
    def _get_sparse_embedder(cls):
        """Lazy-load FastEmbed sparse embedder."""
        if cls._sparse_embedder is None:
            try:
                from app.rag.sparse import SparseEmbedder

                cls._sparse_embedder = SparseEmbedder()
            except ImportError:
                # Fallback: fastembed not installed
                cls._sparse_embedder = "unavailable"
        return cls._sparse_embedder

    async def embed_sparse(self, text: str) -> SparseEmbeddingResult:
        """Sparse 임베딩 (BM25).

        FastEmbed의 Qdrant/bm25 모델을 사용합니다.
        fastembed가 설치되지 않은 경우 간단한 토큰 빈도 기반 fallback을 사용합니다.

        Args:
            text: 임베딩할 텍스트

        Returns:
            SparseEmbeddingResult with indices and values
        """
        if not text or not text.strip():
            return SparseEmbeddingResult(indices=[], values=[], model="empty")

        sparse_embedder = self._get_sparse_embedder()

        # Use FastEmbed if available
        if sparse_embedder != "unavailable":
            try:
                indices, values = sparse_embedder.embed(text)
                return SparseEmbeddingResult(
                    indices=indices,
                    values=values,
                    model="Qdrant/bm25",
                )
            except Exception as e:
                import logging

                logging.getLogger(__name__).warning(
                    f"[SparseEmbed] FastEmbed failed, using fallback: {e}"
                )

        # Fallback: simple token frequency
        tokens = text.lower().split()
        token_freq: dict[str, int] = {}
        for token in tokens:
            # Filter out very short tokens
            if len(token) < 2:
                continue
            token_freq[token] = token_freq.get(token, 0) + 1

        # Convert to indices using consistent hash
        indices: list[int] = []
        values: list[float] = []
        for token, freq in token_freq.items():
            # Use positive hash modulo vocabulary size
            idx = abs(hash(token)) % 100000
            indices.append(idx)
            values.append(float(freq))

        return SparseEmbeddingResult(
            indices=indices,
            values=values,
            model="simple_tf_fallback",
        )


# =============================================================================
# Utility Functions
# =============================================================================


def normalize_vector(vector: list[float]) -> list[float]:
    """벡터 정규화 (L2 norm)."""
    import math

    magnitude = math.sqrt(sum(x * x for x in vector))
    if magnitude == 0:
        return vector
    return [x / magnitude for x in vector]


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """코사인 유사도 계산."""
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have same dimension")

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)
