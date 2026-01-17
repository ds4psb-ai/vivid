"""Qdrant Backend Adapter (P0 2026).

기존 Qdrant Hybrid 백엔드를 Multi-RAG Protocol에 맞게 어댑팅.

Features:
    - RAGSourceBackend Protocol 구현
    - 기존 tier1_dimension_rag 서비스 래핑
    - 차원별 컬렉션 자동 선택

Usage:
    from app.rag.multi_rag.backends import QdrantAdapter

    adapter = QdrantAdapter(dimension="4D")
    results = await adapter.query("레퍼런스 분석 기법")
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class QdrantAdapter:
    """Qdrant Hybrid 백엔드 어댑터.

    기존 tier1_dimension_rag를 Multi-RAG Protocol에 맞게 래핑합니다.

    Attributes:
        dimension: 차원 코드 (예: "4D", "AD")
        _rag: DimensionRAG 인스턴스 (lazy loading)

    Example:
        >>> adapter = QdrantAdapter(dimension="4D")
        >>> results = await adapter.query("구도 분석 방법", limit=5)
        >>> for r in results:
        ...     print(r["content"][:100])
    """

    def __init__(self, dimension: str = "1D") -> None:
        """어댑터 초기화.

        Args:
            dimension: 차원 코드 (예: "4D", "AD", "STORY")
        """
        self.dimension = dimension.upper()
        self._rag = None

    @property
    def rag(self):
        """DimensionRAG 인스턴스 (lazy loading)."""
        if self._rag is None:
            from app.rag.tier1_dimension_rag import get_dimension_rag
            self._rag = get_dimension_rag(self.dimension)
        return self._rag

    async def query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Qdrant Hybrid 쿼리 실행.

        Args:
            query: 검색 쿼리
            filters: 메타데이터 필터 (dimension 오버라이드 가능)
            limit: 최대 결과 수

        Returns:
            검색 결과 리스트. 각 결과는 다음 필드 포함:
            - id: 문서 ID
            - content: 문서 내용
            - score: 관련성 점수
            - metadata: 추가 메타데이터
        """
        # dimension 오버라이드 지원
        dimension = (
            filters.get("dimension", self.dimension).upper()
            if filters else self.dimension
        )

        try:
            # 동적 dimension 처리
            if dimension != self.dimension:
                from app.rag.tier1_dimension_rag import get_dimension_rag
                rag = get_dimension_rag(dimension)
            else:
                rag = self.rag

            # Hybrid search 실행 (sync → async 래핑)
            # tier1_dimension_rag.hybrid_search는 sync 함수
            import asyncio
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: rag.hybrid_search(query=query, limit=limit),
            )

            # Dict 형식으로 변환
            documents: List[Dict[str, Any]] = []
            for idx, doc in enumerate(results[:limit]):
                documents.append({
                    "id": doc.get("doc_id", f"qdrant_{dimension}_{idx}"),
                    "content": doc.get("content", ""),
                    "score": doc.get("score", 0.0),
                    "metadata": {
                        **doc.get("metadata", {}),
                        "dimension": dimension,
                        "source_type": "qdrant_hybrid",
                    },
                })

            logger.debug(
                f"[QdrantAdapter] Query completed | "
                f"dimension={dimension} | "
                f"results={len(documents)}"
            )

            return documents

        except Exception as e:
            logger.error(f"[QdrantAdapter] Query failed: {e}")
            return []

    async def health_check(self) -> bool:
        """헬스 체크.

        Returns:
            True if Qdrant is healthy
        """
        try:
            from app.rag.tier1_dimension_rag import get_qdrant_client
            client = get_qdrant_client()
            # Collection 존재 확인
            collections = client.get_collections()
            return len(collections.collections) > 0
        except Exception as e:
            logger.warning(f"[QdrantAdapter] Health check failed: {e}")
            return False
