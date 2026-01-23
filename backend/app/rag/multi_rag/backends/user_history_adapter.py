"""User History Backend Adapter (P1 2026).

사용자 과거 작업 히스토리에서 유사 컨텍스트 검색.

Features:
    - RAGSourceBackend Protocol 구현
    - CapsuleRun 테이블에서 과거 성공 결과 검색
    - 차원별, 앱별 필터링
    - 하이브리드 검색: Vector Similarity (0.7) + Keyword Matching (0.3)

Usage:
    from app.rag.multi_rag.backends import UserHistoryAdapter

    adapter = UserHistoryAdapter(db_session_factory)
    results = await adapter.query("이전에 만든 비슷한 스토리보드", filters={"user_id": "user_123"})
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embedder import get_embedder

logger = logging.getLogger(__name__)


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
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


class UserHistoryAdapter:
    """사용자 히스토리 RAG 백엔드 어댑터.

    사용자의 과거 작업 결과(CapsuleRun)에서 유사 컨텍스트를 검색합니다.

    Attributes:
        db_factory: AsyncSession 팩토리 (context manager)

    Example:
        >>> from app.database import get_db_context
        >>> adapter = UserHistoryAdapter(get_db_context)
        >>> results = await adapter.query(
        ...     "이전에 만든 스토리보드",
        ...     filters={"user_id": "user_123", "dimension": "2D"},
        ... )
    """

    def __init__(self, db_factory: Callable) -> None:
        """어댑터 초기화.

        Args:
            db_factory: AsyncSession을 반환하는 async context manager 팩토리
                       예: get_db_context
        """
        self.db_factory = db_factory

    async def query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """사용자 히스토리 하이브리드 검색.

        Vector Similarity (0.7) + Keyword Matching (0.3) 하이브리드 방식.

        Args:
            query: 검색 쿼리 (벡터 유사도 + 키워드 매칭)
            filters: 메타데이터 필터
                - user_id: (필수) 사용자 ID
                - dimension: (선택) 차원 코드
                - app_key: (선택) 앱 키
            limit: 최대 결과 수

        Returns:
            검색 결과 리스트. 각 결과는 다음 필드 포함:
            - id: CapsuleRun ID
            - content: 작업 결과 요약
            - score: 하이브리드 관련성 점수 (vector 0.7 + keyword 0.3)
            - metadata: 추가 메타데이터
        """
        filters = filters or {}
        user_id = filters.get("user_id")

        if not user_id:
            logger.warning("[UserHistoryAdapter] user_id is required")
            return []

        try:
            async with self.db_factory() as db:
                from app.models import CapsuleRun

                # 기본 쿼리: 성공한 실행 결과
                stmt = (
                    select(CapsuleRun)
                    .where(CapsuleRun.user_id == user_id)
                    .where(CapsuleRun.success == True)  # noqa: E712
                )

                # 차원 필터
                if dimension := filters.get("dimension"):
                    stmt = stmt.where(CapsuleRun.dimension == dimension.upper())

                # 앱 필터
                if app_key := filters.get("app_key"):
                    stmt = stmt.where(CapsuleRun.app_key == app_key)

                # 최신순 정렬 및 제한
                stmt = stmt.order_by(CapsuleRun.created_at.desc()).limit(limit * 2)

                result = await db.execute(stmt)
                runs = result.scalars().all()

                # 하이브리드 검색: Vector (0.7) + Keyword (0.3)
                embedder = get_embedder()
                query_vec = embedder.embed(query)

                documents: List[Dict[str, Any]] = []
                query_lower = query.lower()
                keywords = query_lower.split()

                for idx, run in enumerate(runs):
                    # 문서 콘텐츠 생성
                    output_str = str(run.output) if run.output else ""
                    input_str = str(run.input_params) if run.input_params else ""
                    combined = f"{output_str} {input_str}"
                    combined_lower = combined.lower()

                    # 1. 키워드 매칭 점수 (0.3 가중치)
                    match_count = sum(1 for kw in keywords if kw in combined_lower)
                    keyword_score = match_count / len(keywords) if keywords else 0.5

                    # 2. 벡터 유사도 점수 (0.7 가중치)
                    doc_vec = embedder.embed(combined[:1000])  # 1000자 제한
                    vector_score = _cosine_similarity(query_vec, doc_vec)

                    # 3. 하이브리드 점수
                    score = keyword_score * 0.3 + vector_score * 0.7

                    # 최소 임계값 (너무 낮은 점수 필터링)
                    if score < 0.1:
                        continue

                    # 결과 요약 생성
                    summary = run.output.get("summary", "") if run.output else ""
                    if not summary and run.output:
                        # output에서 첫 번째 텍스트 필드 추출
                        for key in ["text", "content", "result", "response"]:
                            if key in run.output and isinstance(run.output[key], str):
                                summary = run.output[key][:500]
                                break

                    documents.append({
                        "id": str(run.id),
                        "content": summary or f"[{run.dimension}] {run.app_key} 작업 결과",
                        "score": score,
                        "metadata": {
                            "dimension": run.dimension,
                            "app_key": run.app_key,
                            "created_at": run.created_at.isoformat() if run.created_at else None,
                            "user_id": user_id,
                            "source_type": "user_history",
                        },
                    })

                # 점수순 정렬
                documents.sort(key=lambda x: x["score"], reverse=True)
                documents = documents[:limit]

                logger.debug(
                    f"[UserHistoryAdapter] Query completed | "
                    f"user={user_id} | "
                    f"results={len(documents)}"
                )

                return documents

        except Exception as e:
            logger.error(f"[UserHistoryAdapter] Query failed: {e}")
            return []

    async def health_check(self) -> bool:
        """헬스 체크.

        Returns:
            True if database is healthy
        """
        try:
            async with self.db_factory() as db:
                await db.execute(select(1))
            return True
        except Exception as e:
            logger.warning(f"[UserHistoryAdapter] Health check failed: {e}")
            return False
