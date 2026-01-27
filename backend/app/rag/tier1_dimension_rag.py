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

from qdrant_client import QdrantClient, models
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings
from app.services.embedder import get_embedder
from app.services.circuit_breaker import QDRANT_BREAKER, CircuitBreakerOpen  # P6-3
from app.rag.qdrant_tracing import traced_qdrant_operation, set_results_count  # P8

# Lazy import for sparse embedder (P0: Hybrid Search)
_sparse_embedder = None


def _get_sparse_embedder():
    """Lazy-load sparse embedder for hybrid search."""
    global _sparse_embedder
    if _sparse_embedder is None:
        try:
            from app.rag.sparse import SparseEmbedder
            _sparse_embedder = SparseEmbedder()
        except ImportError:
            logger.warning("[Tier1RAG] fastembed not installed, hybrid search disabled")
            return None
    return _sparse_embedder


logger = logging.getLogger(__name__)

# 차원별 컬렉션 정의
# P0.5: use_hybrid 플래그로 Hybrid 컬렉션 자동 선택
DIMENSION_COLLECTIONS: Dict[str, Dict[str, Any]] = {
    "1D": {
        "name": "dimension_1d_contexts",
        "name_hybrid": "dimension_1d_contexts_hybrid",
        "use_hybrid": True,
        "description": "프롬프트, 미학, 페르소나 컨텍스트",
        "vector_size": 384,
    },
    "2D": {
        "name": "dimension_2d_contexts",
        "name_hybrid": "dimension_2d_contexts_hybrid",
        "use_hybrid": True,
        "description": "스토리보드, 서사 구조 컨텍스트",
        "vector_size": 384,
    },
    "3D": {
        "name": "dimension_3d_contexts",
        "name_hybrid": "dimension_3d_contexts_hybrid",
        "use_hybrid": True,
        "description": "이미지 스타일, 비주얼 가이드 컨텍스트",
        "vector_size": 384,
    },
    "4D": {
        "name": "dimension_4d_contexts",
        "name_hybrid": "dimension_4d_contexts_hybrid",
        "use_hybrid": True,
        "description": "분석 프레임워크, VDG 기준 컨텍스트",
        "vector_size": 384,
    },
    "5D": {
        "name": "dimension_5d_contexts",
        "name_hybrid": "dimension_5d_contexts_hybrid",
        "use_hybrid": True,
        "description": "영상 생성, 카메라 무브먼트 컨텍스트",
        "vector_size": 384,
    },
    "6D": {
        "name": "dimension_6d_contexts",
        "name_hybrid": "dimension_6d_contexts_hybrid",
        "use_hybrid": True,
        "description": "음악, 사운드 디자인 컨텍스트",
        "vector_size": 384,
    },
    # Extended dimensions
    "QC": {
        "name": "dimension_qc_contexts",
        "name_hybrid": "dimension_qc_contexts_hybrid",
        "use_hybrid": True,
        "description": "품질 검증 기준, VDG 스탠다드",
        "vector_size": 384,
    },
    "AD": {
        "name": "dimension_ad_contexts",
        "name_hybrid": "dimension_ad_contexts_hybrid",
        "use_hybrid": True,
        "description": "미학 이론, 거장 스타일 가이드",
        "vector_size": 384,
    },
    "AI": {
        "name": "dimension_ai_contexts",
        "name_hybrid": "dimension_ai_contexts_hybrid",
        "use_hybrid": True,
        "description": "페르소나 분석, MBTI/사주 이론",
        "vector_size": 384,
    },
    "VEO": {
        "name": "dimension_veo_contexts",
        "name_hybrid": "dimension_veo_contexts_hybrid",
        "use_hybrid": True,
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
    def sparse_embedder(self):
        """Lazy-load sparse embedder for hybrid search (P0)."""
        return _get_sparse_embedder()

    @property
    def client(self) -> Optional[QdrantClient]:
        """Lazy-initialize Qdrant client with graceful failure."""
        if not self._available:
            return None

        if self._client is None:
            try:
                # H1.3: SecretStr - use .get_secret_value() for actual API key
                qdrant_api_key = settings.QDRANT_API_KEY.get_secret_value() if settings.QDRANT_API_KEY else None
                self._client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=qdrant_api_key if qdrant_api_key else None,
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

            # P2-3: Hybrid collection도 함께 생성 (use_hybrid=True인 경우)
            if self.collection_config.get("use_hybrid"):
                self._ensure_hybrid_collection(client, collections)

            return True
        except Exception as e:
            logger.error(f"[{self.dimension}] Failed to ensure collection: {e}")
            return False

    def _ensure_hybrid_collection(
        self, client: QdrantClient, collections=None
    ) -> bool:
        """Hybrid 컬렉션 생성 (Dense + Sparse with IDF).

        2026 Best Practice: Named vectors + Modifier.IDF for BM25.

        Args:
            client: Qdrant client
            collections: Cached collections list (optional)

        Returns:
            True if hybrid collection exists or was created
        """
        hybrid_name = self.collection_config.get("name_hybrid")
        if not hybrid_name:
            return False

        try:
            if collections is None:
                collections = client.get_collections()

            exists = any(c.name == hybrid_name for c in collections.collections)

            if not exists:
                # 2026 Best Practice: Named vectors with sparse IDF
                client.create_collection(
                    collection_name=hybrid_name,
                    vectors_config={
                        "dense": qdrant_models.VectorParams(
                            size=self.vector_size,
                            distance=qdrant_models.Distance.COSINE,
                        )
                    },
                    sparse_vectors_config={
                        "sparse": qdrant_models.SparseVectorParams(
                            modifier=qdrant_models.Modifier.IDF,
                        )
                    },
                )
                logger.info(
                    f"[{self.dimension}] Created hybrid collection: {hybrid_name} "
                    "(dense + sparse with IDF)"
                )
            return True
        except Exception as e:
            logger.error(f"[{self.dimension}] Failed to create hybrid collection: {e}")
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
        # P6-3: Circuit breaker check
        try:
            QDRANT_BREAKER.check_state()
        except CircuitBreakerOpen:
            logger.warning(f"[{self.dimension}] Qdrant circuit open, skipping index")
            return False

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

            # Upsert (증분 업데이트) - Dense-only collection
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

            # P2-3: Hybrid collection에도 인덱싱 (use_hybrid=True인 경우)
            if self.collection_config.get("use_hybrid"):
                self._index_to_hybrid_collection(
                    client, point_id, content, vector, payload
                )

            QDRANT_BREAKER.record_success()  # P6-3
            logger.debug(f"[{self.dimension}] Indexed: {doc_id}")
            return True
        except Exception as e:
            QDRANT_BREAKER.record_failure(e)  # P6-3
            logger.error(f"[{self.dimension}] Index failed for {doc_id}: {e}")
            return False

    def _index_to_hybrid_collection(
        self,
        client: QdrantClient,
        point_id: str,
        content: str,
        dense_vector: List[float],
        payload: Dict[str, Any],
    ) -> bool:
        """Hybrid 컬렉션에 Dense + Sparse 벡터 저장.

        2026 Best Practice: Named vectors로 dual indexing.

        Args:
            client: Qdrant client
            point_id: Point ID (same as dense-only collection)
            content: Text content for sparse embedding
            dense_vector: Pre-computed dense vector
            payload: Metadata payload

        Returns:
            True if successful
        """
        hybrid_name = self.collection_config.get("name_hybrid")
        if not hybrid_name:
            return False

        sparse_embedder = self.sparse_embedder
        if sparse_embedder is None:
            logger.debug(f"[{self.dimension}] Sparse embedder unavailable, skipping hybrid index")
            return False

        try:
            # Sparse embedding 생성 (BM25)
            sparse_indices, sparse_values = sparse_embedder.embed(content)

            # Named vectors로 upsert (dense + sparse)
            client.upsert(
                collection_name=hybrid_name,
                points=[
                    qdrant_models.PointStruct(
                        id=point_id,
                        vector={
                            "dense": dense_vector,
                            "sparse": qdrant_models.SparseVector(
                                indices=sparse_indices,
                                values=sparse_values,
                            ),
                        },
                        payload=payload,
                    )
                ],
            )
            logger.debug(
                f"[{self.dimension}] Hybrid indexed: {payload.get('doc_id')} "
                f"(dense={len(dense_vector)}d, sparse={len(sparse_indices)} terms)"
            )
            return True
        except Exception as e:
            logger.warning(f"[{self.dimension}] Hybrid index failed: {e}")
            return False

    def search(
        self,
        query: str,
        limit: int = 5,
        app_key: Optional[str] = None,
        min_score: float = 0.5,
        metadata_filters: Optional[Dict[str, Any]] = None,  # P1: dataset routing
    ) -> List[Dict[str, Any]]:
        """유사도 검색 (앱별 필터링 지원).

        Args:
            query: 검색 쿼리
            limit: 최대 결과 수
            app_key: 앱 키로 필터링 (선택)
            min_score: 최소 유사도 점수
            metadata_filters: P1 - 추가 메타데이터 필터 (dataset_id 등)

        Returns:
            검색 결과 리스트 [{content, score, metadata}, ...]
        """
        # P6-3: Circuit breaker check
        try:
            QDRANT_BREAKER.check_state()
        except CircuitBreakerOpen:
            logger.warning(f"[{self.dimension}] Qdrant circuit open, returning empty")
            return []
            
        client = self.client
        if client is None:
            logger.debug(f"[{self.dimension}] Qdrant unavailable, returning empty")
            return []

        # P8: OpenTelemetry tracing for Qdrant search
        with traced_qdrant_operation(
            operation="search",
            collection=self.collection_name,
            dimension=self.dimension,
            query_length=len(query),
            limit=limit,
            is_hybrid=False,
            filters={"app_key": app_key} if app_key else metadata_filters,
        ) as span:
            try:
                # 쿼리 임베딩
                query_vector = self.embedder.embed(query)

                # 필터 조건 구성
                must_conditions = []

                # 기존 app_key 필터
                if app_key:
                    must_conditions.append(
                        qdrant_models.FieldCondition(
                            key="app_key",
                            match=qdrant_models.MatchValue(value=app_key),
                        )
                    )

                # P1: metadata_filters 처리 (dataset_id 등)
                if metadata_filters:
                    for key, value in metadata_filters.items():
                        if isinstance(value, dict) and "$in" in value:
                            # $in 연산자: 여러 값 중 하나 매칭
                            must_conditions.append(
                                qdrant_models.FieldCondition(
                                    key=key,
                                    match=qdrant_models.MatchAny(any=value["$in"]),
                                )
                            )
                        else:
                            # 단일 값 매칭
                            must_conditions.append(
                                qdrant_models.FieldCondition(
                                    key=key,
                                    match=qdrant_models.MatchValue(value=value),
                                )
                            )

                filter_conditions = qdrant_models.Filter(must=must_conditions) if must_conditions else None

                # 검색 (qdrant-client 1.16+ uses query_points instead of search)
                response = client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=filter_conditions,
                    limit=limit,
                    score_threshold=min_score,
                    with_payload=True,
                )

                QDRANT_BREAKER.record_success()  # P6-3

                results = [
                    {
                        "content": r.payload.get("content", "") if r.payload else "",
                        "score": r.score,
                        "doc_id": r.payload.get("doc_id") if r.payload else None,
                        "metadata": {
                            k: v for k, v in (r.payload or {}).items()
                            if k not in ("content", "doc_id")
                        },
                    }
                    for r in response.points
                ]

                # P8: Record results count
                set_results_count(span, len(results))
                return results

            except Exception as e:
                QDRANT_BREAKER.record_failure(e)  # P6-3
                logger.error(f"[{self.dimension}] Search failed: {e}")
                raise

    def hybrid_search(
        self,
        query: str,
        limit: int = 5,
        prefetch_limit: int = 20,
        app_key: Optional[str] = None,
        min_score: float = 0.0,
        metadata_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Qdrant Native Hybrid Search (Dense + Sparse + RRF).

        P0: Server-side fusion으로 성능 최적화.
        Collection에 Modifier.IDF가 설정되어 있어야 sparse 검색 효과 있음.

        Sparse embedder가 없거나 실패 시 기존 dense-only search로 fallback.

        Args:
            query: 검색 쿼리
            limit: 최종 결과 수
            prefetch_limit: Dense/Sparse 각각의 prefetch 수 (RRF 융합 전)
            app_key: 앱 키로 필터링 (선택)
            min_score: 최소 점수 (RRF 점수, 0.0 권장)
            metadata_filters: 추가 메타데이터 필터

        Returns:
            검색 결과 리스트 [{content, score, doc_id, metadata}, ...]
        """
        # Sparse embedder 확인 - 없으면 dense-only fallback
        sparse_embedder = self.sparse_embedder
        if sparse_embedder is None:
            logger.debug(f"[{self.dimension}] Sparse embedder unavailable, using dense-only")
            return self.search(
                query, limit, app_key=app_key,
                min_score=0.5, metadata_filters=metadata_filters
            )

        # Circuit breaker check
        try:
            QDRANT_BREAKER.check_state()
        except CircuitBreakerOpen:
            logger.warning(f"[{self.dimension}] Qdrant circuit open, falling back to dense-only")
            return self.search(
                query, limit, app_key=app_key,
                min_score=0.5, metadata_filters=metadata_filters
            )

        client = self.client
        if client is None:
            logger.debug(f"[{self.dimension}] Qdrant unavailable, returning empty")
            return []

        # P0.5: use_hybrid 플래그에 따라 컬렉션 선택
        if self.collection_config.get("use_hybrid"):
            collection_name = self.collection_config.get("name_hybrid", self.collection_name)
        else:
            collection_name = self.collection_name

        # P8: OpenTelemetry tracing for Qdrant hybrid search
        with traced_qdrant_operation(
            operation="hybrid_search",
            collection=collection_name,
            dimension=self.dimension,
            query_length=len(query),
            limit=limit,
            is_hybrid=True,
            prefetch_limit=prefetch_limit,
            filters={"app_key": app_key} if app_key else metadata_filters,
        ) as span:
            try:
                # 임베딩 생성 (Dense + Sparse)
                dense_vector = self.embedder.embed(query)
                sparse_indices, sparse_values = sparse_embedder.embed(query)

                # 필터 조건 구성
                must_conditions = []
                if app_key:
                    must_conditions.append(
                        qdrant_models.FieldCondition(
                            key="app_key",
                            match=qdrant_models.MatchValue(value=app_key),
                        )
                    )
                if metadata_filters:
                    for key, value in metadata_filters.items():
                        if isinstance(value, dict) and "$in" in value:
                            must_conditions.append(
                                qdrant_models.FieldCondition(
                                    key=key,
                                    match=qdrant_models.MatchAny(any=value["$in"]),
                                )
                            )
                        else:
                            must_conditions.append(
                                qdrant_models.FieldCondition(
                                    key=key,
                                    match=qdrant_models.MatchValue(value=value),
                                )
                            )

                query_filter = qdrant_models.Filter(must=must_conditions) if must_conditions else None

                # Qdrant Native Hybrid Search with Prefetch + RRF Fusion
                response = client.query_points(
                    collection_name=collection_name,
                    prefetch=[
                        # Dense search prefetch
                        models.Prefetch(
                            query=dense_vector,
                            using="dense",
                            limit=prefetch_limit,
                        ),
                        # Sparse search prefetch
                        models.Prefetch(
                            query=models.SparseVector(
                                indices=sparse_indices,
                                values=sparse_values,
                            ),
                            using="sparse",
                            limit=prefetch_limit,
                        ),
                    ],
                    query=models.FusionQuery(fusion=models.Fusion.RRF),
                    limit=limit,
                    query_filter=query_filter,
                    with_payload=True,
                )

                QDRANT_BREAKER.record_success()

                results = [
                    {
                        "content": r.payload.get("content", "") if r.payload else "",
                        "score": r.score,
                        "doc_id": r.payload.get("doc_id") if r.payload else None,
                        "metadata": {
                            k: v for k, v in (r.payload or {}).items()
                            if k not in ("content", "doc_id")
                        },
                    }
                    for r in response.points
                ]

                # P8: Record results count
                set_results_count(span, len(results))

                logger.debug(
                    f"[{self.dimension}] Hybrid search: collection={collection_name} "
                    f"query='{query[:30]}...' prefetch={prefetch_limit} results={len(results)}"
                )
                return results

            except Exception as e:
                QDRANT_BREAKER.record_failure(e)
                logger.warning(
                    f"[{self.dimension}] Hybrid search failed ({e}), "
                    "falling back to dense-only"
                )
                # Fallback to dense-only search
                return self.search(
                    query, limit, app_key=app_key,
                    min_score=0.5, metadata_filters=metadata_filters
                )

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

            # Dense-only collection에서 삭제
            client.delete(
                collection_name=self.collection_name,
                points_selector=qdrant_models.PointIdsList(points=[point_id]),
            )

            # P2-3: Hybrid collection에서도 삭제
            if self.collection_config.get("use_hybrid"):
                hybrid_name = self.collection_config.get("name_hybrid")
                if hybrid_name:
                    try:
                        client.delete(
                            collection_name=hybrid_name,
                            points_selector=qdrant_models.PointIdsList(points=[point_id]),
                        )
                    except Exception:
                        pass  # Hybrid collection이 없을 수도 있음

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
            stats = {
                "available": True,
                "dimension": self.dimension,
                "collection": self.collection_name,
                "points_count": info.points_count,
                # vectors_count removed in qdrant-client 1.7+ (use points_count)
                "status": info.status.value if info.status else "unknown",
            }

            # P2-3: Hybrid collection 통계 추가
            if self.collection_config.get("use_hybrid"):
                hybrid_name = self.collection_config.get("name_hybrid")
                if hybrid_name:
                    try:
                        hybrid_info = client.get_collection(hybrid_name)
                        stats["hybrid"] = {
                            "collection": hybrid_name,
                            "points_count": hybrid_info.points_count,
                            "status": hybrid_info.status.value if hybrid_info.status else "unknown",
                        }
                    except Exception:
                        stats["hybrid"] = {"available": False}

            return stats
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
