"""User History Backend Adapter.

사용자의 과거 작업 히스토리에서 유사 컨텍스트를 검색합니다.
PostgreSQL CapsuleRun 테이블 기반.

Features (P1 2026):
    - 하이브리드 검색: Vector Similarity (0.7) + Keyword Matching (0.3)
    - SentenceTransformers all-MiniLM-L6-v2 (384 dimensions)
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from app.rag.router.backends.base import BaseRAGBackend
from app.rag.router.types import RAGDocument, RAGSourceType
from app.services.embedder import get_embedder

logger = logging.getLogger(__name__)


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        vec_a: First vector
        vec_b: Second vector

    Returns:
        Cosine similarity score (0.0 ~ 1.0)
    """
    a = np.array(vec_a)
    b = np.array(vec_b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a < 1e-8 or norm_b < 1e-8:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class UserHistoryBackend(BaseRAGBackend):
    """사용자 히스토리 RAG 백엔드."""

    _source_type = RAGSourceType.USER_HISTORY

    def __init__(self, db_session_factory: Any = None):
        """Initialize with DB session factory.

        Args:
            db_session_factory: async session factory
        """
        self._db_factory = db_session_factory

    async def query(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[RAGDocument]:
        """사용자 히스토리 하이브리드 검색.

        Vector Similarity (0.7) + Keyword Matching (0.3) 하이브리드 방식.

        Args:
            query: 검색 쿼리 (벡터 유사도 + 키워드 매칭)
            filters: 필터 조건
                - user_id: 사용자 ID (필수)
                - dimension: 차원 (선택)
            limit: 최대 결과 수

        Returns:
            RAGDocument 리스트 (하이브리드 점수순)
        """
        user_id = (filters or {}).get("user_id")
        if not user_id:
            logger.warning("[UserHistoryBackend] user_id required")
            return []

        if self._db_factory is None:
            logger.warning("[UserHistoryBackend] DB factory not set")
            return []

        dimension = (filters or {}).get("dimension")

        try:
            from sqlalchemy import select, or_, desc
            from app.models import CapsuleRun

            async with self._db_factory() as db:
                stmt = (
                    select(CapsuleRun)
                    .where(CapsuleRun.user_id == user_id)
                    .where(CapsuleRun.success == True)  # noqa: E712
                )

                # Dimension 필터
                if dimension:
                    stmt = stmt.where(CapsuleRun.dimension == dimension)

                # 하이브리드 검색: Vector (0.7) + Keyword (0.3)
                query_lower = query.lower()
                keywords = query_lower.split()

                # 쿼리 벡터 생성 (한 번만)
                embedder = get_embedder()
                query_vec = embedder.embed(query)

                # 최근순 정렬
                stmt = stmt.order_by(desc(CapsuleRun.created_at)).limit(limit * 2)

                result = await db.execute(stmt)
                runs = result.scalars().all()

                # 하이브리드 점수 계산
                documents = []
                for run in runs:
                    output = run.output or {}
                    summary = str(output.get("summary", ""))
                    prompt = str(output.get("prompt", ""))
                    content = summary + " " + prompt
                    content_lower = content.lower()

                    # 1. 키워드 매칭 점수 (0.3 가중치)
                    match_count = sum(1 for kw in keywords if kw in content_lower)
                    keyword_score = match_count / len(keywords) if keywords else 0.5

                    # 2. 벡터 유사도 점수 (0.7 가중치)
                    doc_vec = embedder.embed(content[:1000])  # 1000자 제한
                    vector_score = _cosine_similarity(query_vec, doc_vec)

                    # 3. 하이브리드 점수
                    score = keyword_score * 0.3 + vector_score * 0.7

                    # 최소 임계값 (너무 낮은 점수 필터링)
                    if score < 0.1:
                        continue

                    doc = RAGDocument(
                        id=str(run.id),
                        content=output.get("summary", "")[:500],  # 요약 500자
                        score=score,
                        metadata={
                            "dimension": run.dimension,
                            "created_at": run.created_at.isoformat(),
                            "app_id": run.app_id,
                        },
                        evidence_ref=f"db:capsule_runs:{run.id}",
                        source_id="user_history",
                        source_type=RAGSourceType.USER_HISTORY,
                    )
                    documents.append(doc)

                # 점수순 정렬 후 limit
                documents.sort(key=lambda x: -x.score)
                return documents[:limit]

        except Exception as e:
            logger.error(f"[UserHistoryBackend] Query failed: {e}")
            return []

    async def health_check(self) -> bool:
        """헬스 체크."""
        if self._db_factory is None:
            return False

        try:
            from sqlalchemy import select

            async with self._db_factory() as db:
                await db.execute(select(1))
            return True
        except Exception:
            return False


class MockUserHistoryBackend(BaseRAGBackend):
    """테스트용 Mock User History 백엔드."""

    _source_type = RAGSourceType.USER_HISTORY

    def __init__(
        self, mock_responses: dict[str, list[RAGDocument]] | None = None
    ):
        self._mock_responses = mock_responses or {}

    async def query(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[RAGDocument]:
        """Mock 쿼리."""
        user_id = (filters or {}).get("user_id", "default")

        if user_id in self._mock_responses:
            return self._mock_responses[user_id][:limit]

        return [
            RAGDocument(
                id=f"mock_history_{user_id}_1",
                content=f"Previous work related to: {query}",
                score=0.7,
                metadata={"user_id": user_id, "dimension": "4D"},
                evidence_ref=f"db:capsule_runs:mock_{user_id}_1",
                source_id="user_history",
                source_type=RAGSourceType.USER_HISTORY,
            )
        ]

    async def health_check(self) -> bool:
        """항상 True."""
        return True
