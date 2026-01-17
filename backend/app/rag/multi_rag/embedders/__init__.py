"""Multi-Modal Embedders Package.

이 패키지는 다양한 멀티모달 임베딩 모델을 제공합니다:
- BaseMultiModalEmbedder: 추상 베이스 클래스
- GeminiMultiModalEmbedder: Google Gemini 멀티모달 임베딩
- (Future) ImageBindEmbedder: Meta ImageBind 6-모달리티
- (Future) VoyageEmbedder: Voyage Multimodal-3
"""

from app.rag.multi_rag.embedders.base import (
    BaseMultiModalEmbedder,
    EmbedderError,
    ModalityNotSupportedError,
)
from app.rag.multi_rag.embedders.gemini_embedder import GeminiMultiModalEmbedder

__all__ = [
    "BaseMultiModalEmbedder",
    "GeminiMultiModalEmbedder",
    "EmbedderError",
    "ModalityNotSupportedError",
]
