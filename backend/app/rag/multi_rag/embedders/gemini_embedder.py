"""Gemini Multi-Modal Embedder.

Google Gemini API를 사용한 멀티모달 임베딩 생성기.
- Text, Image 지원 (Video는 프레임 추출 후 이미지로 처리)
- text-embedding-004 모델 사용 (768 dimensions)
- 이미지는 multimodal-embedding 모델 사용

References:
    - https://ai.google.dev/gemini-api/docs/embeddings
    - https://cloud.google.com/vertex-ai/docs/generative-ai/embeddings/get-multimodal-embeddings
"""

from __future__ import annotations

import base64
import logging
import time
from typing import Any

from app.config import settings
from app.rag.multi_rag.embedders.base import (
    BaseMultiModalEmbedder,
    EmbedderError,
    ModalityNotSupportedError,
)
from app.rag.multi_rag.types import EmbeddingResult, Modality

logger = logging.getLogger(__name__)

# Lazy-load genai client (google.genai - new library)
_genai_client = None


def _get_genai_client():
    """Lazy-load google.genai client via genai_utils."""
    global _genai_client
    if _genai_client is None:
        try:
            from app.services.genai_utils import get_genai_client
            _genai_client = get_genai_client()
        except ImportError:
            raise EmbedderError(
                "google-genai not installed. Run: pip install google-genai"
            )
    return _genai_client


# =============================================================================
# Gemini Embedder Configuration
# =============================================================================

# Gemini embedding models
GEMINI_TEXT_EMBEDDING_MODEL = "models/text-embedding-004"
GEMINI_EMBEDDING_DIM = 768

# Task types for text embedding
EMBEDDING_TASK_TYPES = {
    "retrieval_document": "RETRIEVAL_DOCUMENT",  # 문서 저장용
    "retrieval_query": "RETRIEVAL_QUERY",  # 쿼리용
    "semantic_similarity": "SEMANTIC_SIMILARITY",  # 유사도 비교
    "classification": "CLASSIFICATION",  # 분류
    "clustering": "CLUSTERING",  # 클러스터링
}


class GeminiMultiModalEmbedder(BaseMultiModalEmbedder):
    """Gemini 멀티모달 임베더.

    Google Gemini API를 사용하여 텍스트와 이미지를 동일한 768차원 공간에 임베딩합니다.

    Features:
        - 텍스트: text-embedding-004 모델 (768d)
        - 이미지: 향후 multimodal-embedding 모델 지원
        - 배치 처리 지원 (최대 100개)
        - 태스크 타입 기반 최적화 (retrieval_document, retrieval_query 등)

    Usage:
        embedder = GeminiMultiModalEmbedder()
        text_result = await embedder.embed_text("영화적 프레이밍")
        # image_result = await embedder.embed_image(image_bytes)
    """

    def __init__(
        self,
        task_type: str = "retrieval_document",
        output_dimensionality: int | None = None,
    ) -> None:
        """Initialize Gemini embedder.

        Args:
            task_type: 임베딩 태스크 타입 (retrieval_document, retrieval_query 등)
            output_dimensionality: 출력 차원 (기본 768, 최소 1)
        """
        super().__init__(
            model_name=GEMINI_TEXT_EMBEDDING_MODEL,
            embedding_dim=output_dimensionality or GEMINI_EMBEDDING_DIM,
            supported_modalities=[Modality.TEXT, Modality.IMAGE],
        )
        self._task_type = EMBEDDING_TASK_TYPES.get(task_type, task_type)
        self._output_dimensionality = output_dimensionality
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure genai client is configured."""
        if self._initialized:
            return

        try:
            _get_genai_client()
            self._initialized = True
            logger.info(
                f"[GeminiEmbedder] Initialized with model={self._model_name}, "
                f"task_type={self._task_type}, dim={self._embedding_dim}"
            )
        except Exception as e:
            raise EmbedderError(f"Failed to initialize Gemini: {e}") from e

    async def embed_text(self, text: str) -> EmbeddingResult:
        """텍스트 임베딩.

        Args:
            text: 임베딩할 텍스트 (최대 2048 토큰 권장)

        Returns:
            EmbeddingResult with 768-dim vector

        Raises:
            EmbedderError: API 호출 실패 시
        """
        self._validate_modality(Modality.TEXT)
        self._ensure_initialized()

        if not text or not text.strip():
            raise EmbedderError("Empty text provided")

        start_time = time.time()

        try:
            client = _get_genai_client()

            # Gemini embed_content API (google.genai - new library)
            result = client.models.embed_content(
                model=self._model_name,
                contents=text,
                config={
                    "task_type": self._task_type,
                    "output_dimensionality": self._output_dimensionality,
                } if self._output_dimensionality else {"task_type": self._task_type},
            )

            vector = result.embeddings[0].values

            # Validate dimensions
            if len(vector) != self._embedding_dim:
                logger.warning(
                    f"[GeminiEmbedder] Dimension mismatch: expected {self._embedding_dim}, "
                    f"got {len(vector)}"
                )

            return self._create_result(
                vector=vector,
                modality=Modality.TEXT,
                start_time=start_time,
                tokens_used=len(text.split()),  # Approximate
                metadata={
                    "task_type": self._task_type,
                    "text_length": len(text),
                },
            )

        except Exception as e:
            logger.error(f"[GeminiEmbedder] Text embedding failed: {e}")
            raise EmbedderError(f"Text embedding failed: {e}") from e

    async def embed_image(self, image: bytes) -> EmbeddingResult:
        """이미지 임베딩.

        현재 Gemini API에서는 직접적인 이미지 임베딩을 지원하지 않습니다.
        대안으로 이미지 설명을 생성한 후 텍스트 임베딩을 수행합니다.

        Args:
            image: 이미지 바이트 데이터 (PNG, JPEG, WebP)

        Returns:
            EmbeddingResult with 768-dim vector

        Raises:
            EmbedderError: 처리 실패 시
        """
        self._validate_modality(Modality.IMAGE)
        self._ensure_initialized()

        start_time = time.time()

        try:
            from google.genai import types as genai_types

            client = _get_genai_client()

            # 이미지를 base64로 인코딩
            image_b64 = base64.b64encode(image).decode("utf-8")

            # 이미지 타입 추정
            mime_type = "image/jpeg"
            if image[:8] == b"\x89PNG\r\n\x1a\n":
                mime_type = "image/png"
            elif image[:4] == b"RIFF" and image[8:12] == b"WEBP":
                mime_type = "image/webp"

            # Gemini Vision으로 이미지 설명 생성 (google.genai - new library)
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[
                    genai_types.Part.from_bytes(data=image, mime_type=mime_type),
                    "Describe this image in detail for cinematic analysis. "
                    "Focus on: composition, lighting, color palette, mood, camera angle, "
                    "subject positioning, and visual storytelling elements. "
                    "Be concise but comprehensive (max 200 words).",
                ],
            )

            image_description = response.text

            # 설명 텍스트를 임베딩 (google.genai - new library)
            result = client.models.embed_content(
                model=self._model_name,
                contents=image_description,
                config={
                    "task_type": self._task_type,
                    "output_dimensionality": self._output_dimensionality,
                } if self._output_dimensionality else {"task_type": self._task_type},
            )

            vector = result.embeddings[0].values

            return self._create_result(
                vector=vector,
                modality=Modality.IMAGE,
                start_time=start_time,
                metadata={
                    "method": "vision_to_text_embedding",
                    "description_length": len(image_description),
                    "image_size_bytes": len(image),
                    "mime_type": mime_type,
                },
            )

        except Exception as e:
            logger.error(f"[GeminiEmbedder] Image embedding failed: {e}")
            raise EmbedderError(f"Image embedding failed: {e}") from e

    async def embed_audio(self, audio: bytes) -> EmbeddingResult:
        """오디오 임베딩 (미지원).

        Gemini는 현재 오디오 임베딩을 직접 지원하지 않습니다.

        Raises:
            ModalityNotSupportedError: 항상 발생
        """
        raise ModalityNotSupportedError(Modality.AUDIO, self._model_name)

    async def embed_batch(
        self,
        texts: list[str] | None = None,
        images: list[bytes] | None = None,
        audios: list[bytes] | None = None,
    ) -> list[EmbeddingResult]:
        """배치 텍스트 임베딩.

        Gemini API는 배치 임베딩을 지원합니다 (최대 100개).

        Args:
            texts: 텍스트 목록
            images: 이미지는 순차 처리됨
            audios: 미지원

        Returns:
            EmbeddingResult 목록
        """
        self._ensure_initialized()
        results: list[EmbeddingResult] = []

        # 텍스트 배치 처리
        if texts:
            start_time = time.time()
            try:
                client = _get_genai_client()

                # Gemini 배치 임베딩 (google.genai - new library)
                batch_result = client.models.embed_content(
                    model=self._model_name,
                    contents=texts,
                    config={
                        "task_type": self._task_type,
                        "output_dimensionality": self._output_dimensionality,
                    } if self._output_dimensionality else {"task_type": self._task_type},
                )

                embeddings = [e.values for e in batch_result.embeddings]
                processing_time = (time.time() - start_time) * 1000

                for i, (text, vector) in enumerate(zip(texts, embeddings)):
                    results.append(
                        EmbeddingResult(
                            vector=vector,
                            modality=Modality.TEXT,
                            model=self._model_name,
                            dimensions=len(vector),
                            processing_time_ms=processing_time / len(texts),
                            tokens_used=len(text.split()),
                            metadata={"batch_index": i, "batch_size": len(texts)},
                        )
                    )

                logger.info(
                    f"[GeminiEmbedder] Batch embedded {len(texts)} texts in {processing_time:.0f}ms"
                )

            except Exception as e:
                logger.error(f"[GeminiEmbedder] Batch embedding failed: {e}")
                # Fallback to sequential
                for text in texts:
                    results.append(await self.embed_text(text))

        # 이미지는 순차 처리
        if images:
            for image in images:
                results.append(await self.embed_image(image))

        return results

    async def embed_for_retrieval(
        self,
        text: str,
        is_query: bool = True,
    ) -> EmbeddingResult:
        """검색용 임베딩.

        쿼리와 문서에 다른 태스크 타입을 적용합니다.

        Args:
            text: 텍스트
            is_query: True면 RETRIEVAL_QUERY, False면 RETRIEVAL_DOCUMENT

        Returns:
            EmbeddingResult
        """
        original_task_type = self._task_type

        try:
            self._task_type = (
                "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
            )
            return await self.embed_text(text)
        finally:
            self._task_type = original_task_type


# =============================================================================
# Factory Function
# =============================================================================


def create_gemini_embedder(
    task_type: str = "retrieval_document",
    output_dimensionality: int | None = None,
) -> GeminiMultiModalEmbedder:
    """Gemini 임베더 팩토리 함수.

    Args:
        task_type: 태스크 타입 (retrieval_document, retrieval_query, 등)
        output_dimensionality: 출력 차원 (기본 768)

    Returns:
        GeminiMultiModalEmbedder 인스턴스
    """
    return GeminiMultiModalEmbedder(
        task_type=task_type,
        output_dimensionality=output_dimensionality,
    )


# =============================================================================
# Query vs Document Embedder Pair
# =============================================================================


class GeminiEmbedderPair:
    """쿼리/문서 임베더 쌍.

    검색 시스템에서 쿼리와 문서에 다른 태스크 타입을 적용하기 위한 래퍼.
    """

    def __init__(self, output_dimensionality: int | None = None) -> None:
        self.query_embedder = GeminiMultiModalEmbedder(
            task_type="retrieval_query",
            output_dimensionality=output_dimensionality,
        )
        self.document_embedder = GeminiMultiModalEmbedder(
            task_type="retrieval_document",
            output_dimensionality=output_dimensionality,
        )

    async def embed_query(self, text: str) -> EmbeddingResult:
        """쿼리 임베딩."""
        return await self.query_embedder.embed_text(text)

    async def embed_document(self, text: str) -> EmbeddingResult:
        """문서 임베딩."""
        return await self.document_embedder.embed_text(text)

    async def embed_documents(self, texts: list[str]) -> list[EmbeddingResult]:
        """문서 배치 임베딩."""
        return await self.document_embedder.embed_batch(texts=texts)
