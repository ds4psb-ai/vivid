"""User History Backend Adapter.

사용자의 과거 작업 히스토리에서 유사 컨텍스트를 검색합니다.
PostgreSQL CapsuleRun 테이블 기반.
"""

from __future__ import annotations

import logging
from typing import Any

from app.rag.router.backends.base import BaseRAGBackend
from app.rag.router.types import RAGDocument, RAGSourceType

logger = logging.getLogger(__name__)


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
        """사용자 히스토리 검색.

        Args:
            query: 검색 쿼리 (키워드 매칭)
            filters: 필터 조건
                - user_id: 사용자 ID (필수)
                - dimension: 차원 (선택)
            limit: 최대 결과 수

        Returns:
            RAGDocument 리스트
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

                # 키워드 검색 (output JSON 내)
                # TODO: 향후 Vector similarity 추가
                query_lower = query.lower()
                keywords = query_lower.split()

                # 최근순 정렬
                stmt = stmt.order_by(desc(CapsuleRun.created_at)).limit(limit * 2)

                result = await db.execute(stmt)
                runs = result.scalars().all()

                # 간단한 키워드 매칭 점수 계산
                documents = []
                for run in runs:
                    output = run.output or {}
                    summary = str(output.get("summary", "")).lower()
                    prompt = str(output.get("prompt", "")).lower()
                    content = summary + " " + prompt

                    # 키워드 매칭 점수
                    match_count = sum(1 for kw in keywords if kw in content)
                    if match_count == 0:
                        continue

                    score = match_count / len(keywords) if keywords else 0.5

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
