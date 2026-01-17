"""Multi-Modal RAG Type Definitions (2026 Best Practices).

이 모듈은 Multi-Modal RAG 시스템의 핵심 타입을 정의합니다.
- 멀티모달 임베딩 (Text, Image, Audio, Video)
- Qdrant Named Vectors 기반 컬렉션 스키마
- 크로스모달 검색 쿼리/결과 타입
- Dimension별 모달리티 매핑

References:
    - Qdrant Named Vectors: https://qdrant.tech/documentation/concepts/vectors/
    - ImageBind (Meta): 6-modality unified embedding
    - Voyage Multimodal-3: 32K context multimodal
    - TwelveLabs Embed API: Video understanding
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class Modality(str, Enum):
    """지원되는 모달리티 타입."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"

    @classmethod
    def all(cls) -> list[Modality]:
        """모든 모달리티 반환."""
        return list(cls)


class ContentType(str, Enum):
    """콘텐츠 유형 (Dimension 기반)."""

    # Core creative content
    SHOT = "shot"  # 영상 샷
    SCENE = "scene"  # 씬 구성
    SEQUENCE = "sequence"  # 시퀀스
    TECHNIQUE = "technique"  # 촬영/연출 기법
    STYLE = "style"  # 비주얼 스타일

    # Reference materials
    REFERENCE = "reference"  # 레퍼런스 이미지/영상
    STORYBOARD = "storyboard"  # 스토리보드
    MOODBOARD = "moodboard"  # 무드보드

    # Audio content
    MUSIC = "music"  # 음악
    SFX = "sfx"  # 효과음
    DIALOGUE = "dialogue"  # 대사/나레이션
    AMBIENT = "ambient"  # 앰비언트 사운드

    # Story content
    NARRATIVE = "narrative"  # 내러티브 구조
    CHARACTER = "character"  # 캐릭터 설정
    THEME = "theme"  # 테마/주제

    # Auteur knowledge
    AUTEUR_INSIGHT = "auteur_insight"  # 거장 인사이트
    FILMOGRAPHY = "filmography"  # 필모그래피


class SearchStrategy(str, Enum):
    """검색 전략."""

    # Single modality
    DENSE_ONLY = "dense_only"  # Dense vector만 사용
    SPARSE_ONLY = "sparse_only"  # BM25만 사용

    # Hybrid strategies
    HYBRID_RRF = "hybrid_rrf"  # RRF (Reciprocal Rank Fusion)
    HYBRID_WEIGHTED = "hybrid_weighted"  # 가중치 기반 융합

    # Cross-modal
    CROSS_MODAL = "cross_modal"  # 크로스모달 검색
    MULTI_MODAL = "multi_modal"  # 다중 모달리티 동시 검색


class DistanceMetric(str, Enum):
    """벡터 거리 메트릭."""

    COSINE = "Cosine"
    EUCLID = "Euclid"
    DOT = "Dot"


# =============================================================================
# Vector Configuration
# =============================================================================


@dataclass
class VectorConfig:
    """Dense 벡터 설정."""

    name: str  # e.g., "text_embed", "image_embed"
    size: int  # 벡터 차원 (768 for unified space)
    distance: DistanceMetric = DistanceMetric.COSINE

    def to_qdrant_config(self) -> dict[str, Any]:
        """Qdrant 설정 형식으로 변환."""
        return {
            "size": self.size,
            "distance": self.distance.value,
        }


@dataclass
class SparseVectorConfig:
    """Sparse 벡터 설정 (BM25)."""

    name: str  # e.g., "text_bm25"
    modifier: str | None = None  # "idf" for BM25

    def to_qdrant_config(self) -> dict[str, Any]:
        """Qdrant 설정 형식으로 변환."""
        config: dict[str, Any] = {}
        if self.modifier:
            config["modifier"] = self.modifier
        return config


@dataclass
class CollectionSchema:
    """Multi-Modal 컬렉션 스키마."""

    name: str
    dense_vectors: list[VectorConfig] = field(default_factory=list)
    sparse_vectors: list[SparseVectorConfig] = field(default_factory=list)
    payload_schema: dict[str, str] = field(default_factory=dict)

    def to_qdrant_config(self) -> dict[str, Any]:
        """Qdrant 컬렉션 생성 설정으로 변환."""
        config: dict[str, Any] = {
            "collection_name": self.name,
        }

        # Named vectors config
        if self.dense_vectors:
            config["vectors_config"] = {
                vec.name: vec.to_qdrant_config() for vec in self.dense_vectors
            }

        # Sparse vectors config
        if self.sparse_vectors:
            config["sparse_vectors_config"] = {
                vec.name: vec.to_qdrant_config() for vec in self.sparse_vectors
            }

        return config


# =============================================================================
# Document Types
# =============================================================================


@dataclass
class MultiModalDocument:
    """멀티모달 문서."""

    doc_id: str
    dimension: str  # "3D", "4D", "AD", "Story", etc.
    modality: Modality
    content_type: ContentType

    # Content
    text_content: str | None = None
    image_data: bytes | None = None
    audio_data: bytes | None = None
    video_data: bytes | None = None
    content_url: str | None = None  # 외부 저장소 URL

    # Embeddings (modality name -> vector)
    embeddings: dict[str, list[float]] = field(default_factory=dict)
    sparse_embeddings: dict[str, dict[int, float]] = field(default_factory=dict)

    # Metadata
    auteur_key: str | None = None
    title: str | None = None
    description: str | None = None
    source: str | None = None  # "notebooklm", "qdrant", "upload"
    timestamp: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_evidence_ref(self) -> str:
        """evidence_ref 문자열 생성."""
        base = f"db:rag_docs:multimodal:{self.dimension}"
        if self.auteur_key:
            base += f":{self.auteur_key}"
        return f"{base}:{self.doc_id}"

    def has_modality_embedding(self, modality: Modality) -> bool:
        """특정 모달리티 임베딩 존재 여부."""
        embed_key = f"{modality.value}_embed"
        return embed_key in self.embeddings and len(self.embeddings[embed_key]) > 0


@dataclass
class EmbeddingResult:
    """임베딩 결과."""

    vector: list[float]
    modality: Modality
    model: str
    dimensions: int
    processing_time_ms: float = 0.0
    tokens_used: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SparseEmbeddingResult:
    """Sparse 임베딩 결과 (BM25)."""

    indices: list[int]
    values: list[float]
    model: str = "bm25"

    def to_dict(self) -> dict[int, float]:
        """인덱스-값 딕셔너리로 변환."""
        return dict(zip(self.indices, self.values))


# =============================================================================
# Query Types
# =============================================================================


@dataclass
class MultiModalQuery:
    """멀티모달 검색 쿼리."""

    # Query content (at least one required)
    query_text: str | None = None
    query_image: bytes | None = None
    query_audio: bytes | None = None
    query_video: bytes | None = None

    # Search configuration
    target_modalities: list[Modality] = field(default_factory=lambda: [Modality.TEXT])
    search_strategy: SearchStrategy = SearchStrategy.HYBRID_RRF
    top_k: int = 10

    # Filters
    dimension_filter: str | None = None
    auteur_filter: str | None = None
    content_type_filter: list[ContentType] | None = None

    # Hybrid search weights
    dense_weight: float = 0.7
    sparse_weight: float = 0.3

    # Cross-modal config
    cross_modal_boost: float = 1.0  # 크로스모달 결과 부스트

    def get_query_modality(self) -> Modality:
        """쿼리의 주 모달리티 반환."""
        if self.query_text:
            return Modality.TEXT
        if self.query_image:
            return Modality.IMAGE
        if self.query_audio:
            return Modality.AUDIO
        if self.query_video:
            return Modality.VIDEO
        return Modality.TEXT


@dataclass
class RetrievalResult:
    """검색 결과."""

    doc_id: str
    score: float
    modality: Modality
    content_type: ContentType
    dimension: str

    # Content preview
    text_preview: str | None = None
    content_url: str | None = None

    # Evidence
    evidence_ref: str = ""

    # Metadata
    auteur_key: str | None = None
    title: str | None = None
    source: str | None = None
    matched_vector: str | None = None  # 매칭된 벡터 이름
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiModalSearchResult:
    """멀티모달 검색 전체 결과."""

    query: MultiModalQuery
    results: list[RetrievalResult] = field(default_factory=list)
    total_found: int = 0
    search_time_ms: float = 0.0

    # Strategy info
    strategy_used: SearchStrategy = SearchStrategy.HYBRID_RRF
    modalities_searched: list[Modality] = field(default_factory=list)

    # Fusion info (for hybrid)
    rrf_k: int = 60  # RRF k parameter
    dense_results_count: int = 0
    sparse_results_count: int = 0


# =============================================================================
# Embedder Protocol
# =============================================================================


@runtime_checkable
class MultiModalEmbedder(Protocol):
    """멀티모달 임베더 프로토콜."""

    @property
    def model_name(self) -> str:
        """모델 이름."""
        ...

    @property
    def embedding_dim(self) -> int:
        """임베딩 차원."""
        ...

    @property
    def supported_modalities(self) -> list[Modality]:
        """지원 모달리티."""
        ...

    async def embed_text(self, text: str) -> EmbeddingResult:
        """텍스트 임베딩."""
        ...

    async def embed_image(self, image: bytes) -> EmbeddingResult:
        """이미지 임베딩."""
        ...

    async def embed_audio(self, audio: bytes) -> EmbeddingResult:
        """오디오 임베딩."""
        ...

    async def embed_batch(
        self,
        texts: list[str] | None = None,
        images: list[bytes] | None = None,
    ) -> list[EmbeddingResult]:
        """배치 임베딩."""
        ...


# =============================================================================
# Dimension-Modality Mapping
# =============================================================================

# Dimension별 주요 모달리티 매핑
DIMENSION_MODALITY_MAP: dict[str, list[Modality]] = {
    # Visual dimensions
    "1D": [Modality.TEXT],  # 텍스트 기반 분석
    "2D": [Modality.IMAGE, Modality.TEXT],  # 이미지 생성
    "3D": [Modality.IMAGE, Modality.TEXT],  # 프레임/샷 분석
    "4D": [Modality.VIDEO, Modality.IMAGE, Modality.TEXT],  # 비디오 분석
    # Audio dimension
    "AD": [Modality.AUDIO, Modality.TEXT],  # 사운드 디자인
    # Story dimension
    "Story": [Modality.TEXT],  # 스토리/내러티브
    # Quality/Technical
    "QD": [Modality.VIDEO, Modality.IMAGE, Modality.TEXT],  # 품질 분석
    # AI/VEO
    "AI": [Modality.TEXT, Modality.IMAGE],  # AI 추천
    "VEO": [Modality.VIDEO, Modality.TEXT],  # Veo 비디오 생성
}


def get_modalities_for_dimension(dimension: str) -> list[Modality]:
    """Dimension에 해당하는 모달리티 목록 반환."""
    return DIMENSION_MODALITY_MAP.get(dimension, [Modality.TEXT])


# =============================================================================
# Default Schema Factory
# =============================================================================

# 통합 임베딩 차원 (CLIP, ImageBind 기반)
UNIFIED_EMBEDDING_DIM = 768


def get_default_multimodal_schema(
    collection_name: str = "vivid_multimodal_auteur",
) -> CollectionSchema:
    """기본 멀티모달 컬렉션 스키마 생성."""
    return CollectionSchema(
        name=collection_name,
        dense_vectors=[
            VectorConfig("text_embed", UNIFIED_EMBEDDING_DIM, DistanceMetric.COSINE),
            VectorConfig("image_embed", UNIFIED_EMBEDDING_DIM, DistanceMetric.COSINE),
            VectorConfig("audio_embed", UNIFIED_EMBEDDING_DIM, DistanceMetric.COSINE),
            VectorConfig("video_embed", UNIFIED_EMBEDDING_DIM, DistanceMetric.COSINE),
        ],
        sparse_vectors=[
            SparseVectorConfig("text_bm25", modifier="idf"),
        ],
        payload_schema={
            "doc_id": "keyword",
            "dimension": "keyword",
            "auteur_key": "keyword",
            "content_type": "keyword",
            "modality": "keyword",
            "title": "text",
            "description": "text",
            "source": "keyword",
            "timestamp": "datetime",
        },
    )


def get_dimension_collection_name(dimension: str) -> str:
    """Dimension별 컬렉션 이름 생성."""
    return f"vivid_multimodal_{dimension.lower()}"


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Enums
    "Modality",
    "ContentType",
    "SearchStrategy",
    "DistanceMetric",
    # Vector Config
    "VectorConfig",
    "SparseVectorConfig",
    "CollectionSchema",
    # Documents
    "MultiModalDocument",
    "EmbeddingResult",
    "SparseEmbeddingResult",
    # Query/Result
    "MultiModalQuery",
    "RetrievalResult",
    "MultiModalSearchResult",
    # Protocol
    "MultiModalEmbedder",
    # Constants
    "DIMENSION_MODALITY_MAP",
    "UNIFIED_EMBEDDING_DIM",
    # Helpers
    "get_modalities_for_dimension",
    "get_default_multimodal_schema",
    "get_dimension_collection_name",
]
