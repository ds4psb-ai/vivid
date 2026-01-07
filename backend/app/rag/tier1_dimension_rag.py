"""
Tier 1: 차원별 Qdrant RAG Service.

각 차원(1D-6D, QC, AD, AI, VEO)에 대한 전용 벡터 컬렉션 관리.
증분 업데이트 지원, 앱별 메타데이터 필터링.

Usage:
    rag = Tier1DimensionRAG("1D")
    await rag.ensure_collection()
    await rag.index_document("doc1", "cinematic style guide", {"app_key": "..."})
    results = await rag.search("dark mood lighting", app_key="dimension.aesthetic.direct")
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings
from app.services.embedder import get_embedder

logger = logging.getLogger(__name__)

# 차원별 컬렉션 정의
DIMENSION_COLLECTIONS: Dict[str, Dict[str, Any]] = {
    "1D": {
        "name": "dimension_1d_contexts",
        "description": "프롬프트, 미학, 페르소나 컨텍스트",
        "vector_size": 384,
    },
    "2D": {
        "name": "dimension_2d_contexts",
        "description": "스토리보드, 서사 구조 컨텍스트",
        "vector_size": 384,
    },
    "3D": {
        "name": "dimension_3d_contexts",
        "description": "이미지 스타일, 비주얼 가이드 컨텍스트",
        "vector_size": 384,
    },
    "4D": {
        "name": "dimension_4d_contexts",
        "description": "분석 프레임워크, VDG 기준 컨텍스트",
        "vector_size": 384,
    },
    "5D": {
        "name": "dimension_5d_contexts",
        "description": "영상 생성, 카메라 무브먼트 컨텍스트",
        "vector_size": 384,
    },
    "6D": {
        "name": "dimension_6d_contexts",
        "description": "음악, 사운드 디자인 컨텍스트",
        "vector_size": 384,
    },
    # Extended dimensions
    "QC": {
        "name": "dimension_qc_contexts",
        "description": "품질 검증 기준, VDG 스탠다드",
        "vector_size": 384,
    },
    "AD": {
        "name": "dimension_ad_contexts",
        "description": "미학 이론, 거장 스타일 가이드",
        "vector_size": 384,
    },
    "AI": {
        "name": "dimension_ai_contexts",
        "description": "페르소나 분석, MBTI/사주 이론",
        "vector_size": 384,
    },
    "VEO": {
        "name": "dimension_veo_contexts",
        "description": "Veo 프롬프트 템플릿, 영상 스타일",
        "vector_size": 384,
    },
}


class Tier1DimensionRAG:
    """차원별 Qdrant RAG 서비스.

    Features:
    - 차원별 전용 컬렉션
    - 앱별 메타데이터 필터링
    - 증분 업데이트 (upsert)
    - Graceful degradation (Qdrant 연결 실패 시)
    """

    def __init__(self, dimension: str):
        """Initialize dimension RAG.

        Args:
            dimension: 차원 ID (1D, 2D, ..., QC, AD, AI, VEO)
        """
        if dimension not in DIMENSION_COLLECTIONS:
            raise ValueError(f"Unknown dimension: {dimension}. Valid: {list(DIMENSION_COLLECTIONS.keys())}")

        self.dimension = dimension
        self.collection_config = DIMENSION_COLLECTIONS[dimension]
        self.collection_name = self.collection_config["name"]
        self.vector_size = self.collection_config["vector_size"]

        self._client: Optional[QdrantClient] = None
        self._available: bool = True
        self._embedder = None

    @property
    def embedder(self):
        """Lazy-load embedder."""
        if self._embedder is None:
            self._embedder = get_embedder()
        return self._embedder

    @property
    def client(self) -> Optional[QdrantClient]:
        """Lazy-initialize Qdrant client with graceful failure."""
        if not self._available:
            return None

        if self._client is None:
            try:
                self._client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                    timeout=5,
                )
                self._client.get_collections()
                logger.info(f"[{self.dimension}] Connected to Qdrant")
            except Exception as e:
                logger.warning(f"[{self.dimension}] Qdrant unavailable: {e}")
                self._available = False
                self._client = None
        return self._client

    def ensure_collection(self) -> bool:
        """컬렉션 존재 확인/생성.

        Returns:
            True if collection exists or was created
        """
        client = self.client
        if client is None:
            return False

        try:
            collections = client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)

            if not exists:
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qdrant_models.VectorParams(
                        size=self.vector_size,
                        distance=qdrant_models.Distance.COSINE,
                    ),
                )
                logger.info(f"[{self.dimension}] Created collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"[{self.dimension}] Failed to ensure collection: {e}")
            return False

    def _generate_point_id(self, doc_id: str) -> str:
        """문서 ID를 Qdrant point ID로 변환 (UUID 호환)."""
        # MD5 해시로 UUID 형식 생성
        hash_bytes = hashlib.md5(f"{self.dimension}:{doc_id}".encode()).hexdigest()
        return f"{hash_bytes[:8]}-{hash_bytes[8:12]}-{hash_bytes[12:16]}-{hash_bytes[16:20]}-{hash_bytes[20:32]}"

    def index_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """문서 인덱싱 (증분 업데이트).

        Args:
            doc_id: 문서 고유 ID
            content: 인덱싱할 텍스트 콘텐츠
            metadata: 추가 메타데이터 (app_key, tier, source 등)

        Returns:
            True if successful
        """
        client = self.client
        if client is None:
            logger.warning(f"[{self.dimension}] Qdrant unavailable, skipping index")
            return False

        try:
            self.ensure_collection()

            # 임베딩 생성
            vector = self.embedder.embed(content)

            # 페이로드 구성
            payload = {
                "doc_id": doc_id,
                "content": content[:2000],  # 최대 2000자 저장
                "dimension": self.dimension,
                "indexed_at": datetime.utcnow().isoformat(),
                **(metadata or {}),
            }

            # Upsert (증분 업데이트)
            point_id = self._generate_point_id(doc_id)
            client.upsert(
                collection_name=self.collection_name,
                points=[
                    qdrant_models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload,
                    )
                ],
            )
            logger.debug(f"[{self.dimension}] Indexed: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"[{self.dimension}] Index failed for {doc_id}: {e}")
            return False

    def search(
        self,
        query: str,
        limit: int = 5,
        app_key: Optional[str] = None,
        min_score: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """유사도 검색 (앱별 필터링 지원).

        Args:
            query: 검색 쿼리
            limit: 최대 결과 수
            app_key: 앱 키로 필터링 (선택)
            min_score: 최소 유사도 점수

        Returns:
            검색 결과 리스트 [{content, score, metadata}, ...]
        """
        client = self.client
        if client is None:
            logger.debug(f"[{self.dimension}] Qdrant unavailable, returning empty")
            return []

        try:
            # 쿼리 임베딩
            query_vector = self.embedder.embed(query)

            # 필터 조건
            filter_conditions = None
            if app_key:
                filter_conditions = qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="app_key",
                            match=qdrant_models.MatchValue(value=app_key),
                        )
                    ]
                )

            # 검색
            results = client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=filter_conditions,
                limit=limit,
                score_threshold=min_score,
            )

            return [
                {
                    "content": r.payload.get("content", ""),
                    "score": r.score,
                    "doc_id": r.payload.get("doc_id"),
                    "metadata": {
                        k: v for k, v in r.payload.items()
                        if k not in ("content", "doc_id")
                    },
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"[{self.dimension}] Search failed: {e}")
            return []

    def delete_document(self, doc_id: str) -> bool:
        """문서 삭제.

        Args:
            doc_id: 삭제할 문서 ID

        Returns:
            True if successful
        """
        client = self.client
        if client is None:
            return False

        try:
            point_id = self._generate_point_id(doc_id)
            client.delete(
                collection_name=self.collection_name,
                points_selector=qdrant_models.PointIdsList(points=[point_id]),
            )
            logger.debug(f"[{self.dimension}] Deleted: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"[{self.dimension}] Delete failed for {doc_id}: {e}")
            return False

    def get_collection_stats(self) -> Dict[str, Any]:
        """컬렉션 통계 조회."""
        client = self.client
        if client is None:
            return {"available": False}

        try:
            info = client.get_collection(self.collection_name)
            return {
                "available": True,
                "dimension": self.dimension,
                "collection": self.collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": info.status.value if info.status else "unknown",
            }
        except Exception as e:
            return {"available": False, "error": str(e)}


# 싱글톤 캐시
_dimension_rag_cache: Dict[str, Tier1DimensionRAG] = {}


def get_dimension_rag(dimension: str) -> Tier1DimensionRAG:
    """차원별 RAG 인스턴스 반환 (싱글톤).

    Args:
        dimension: 차원 ID (1D, 2D, ..., QC, AD, AI, VEO)

    Returns:
        Tier1DimensionRAG instance
    """
    if dimension not in _dimension_rag_cache:
        _dimension_rag_cache[dimension] = Tier1DimensionRAG(dimension)
    return _dimension_rag_cache[dimension]
