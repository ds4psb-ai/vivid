"""Base Reranker ABC for Plugin-Registry Pattern.

P4: Reranker Backend Abstraction
모든 reranker backend가 구현해야 하는 인터페이스 정의.

Usage:
    from app.rag.rerankers.base import BaseReranker, RerankResult

    class MyReranker(BaseReranker):
        backend_id = "my_reranker"

        async def rerank(self, query, documents, top_k, config):
            ...
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RerankResult:
    """리랭킹 결과 데이터클래스.

    Attributes:
        documents: 리랭킹된 문서 목록 (rerank_score 포함)
        query: 원본 검색 쿼리
        model: 사용된 모델 이름
        latency_ms: 리랭킹 소요 시간 (밀리초)
        original_count: 원본 문서 수
        reranked_count: 리랭킹 후 문서 수
        metadata: 추가 메타데이터
    """

    documents: List[Dict[str, Any]]
    query: str
    model: str
    latency_ms: int
    original_count: int
    reranked_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentToRerank:
    """리랭킹할 문서 데이터클래스.

    Attributes:
        id: 문서 고유 식별자
        text: 문서 텍스트 (리랭킹에 사용)
        metadata: 추가 메타데이터 (보존됨)
    """

    id: str
    text: str
    metadata: Optional[Dict[str, Any]] = None


class BaseReranker(ABC):
    """Reranker Backend ABC.

    모든 reranker backend가 구현해야 하는 추상 베이스 클래스.
    Plugin-Registry 패턴으로 auto-discovery 지원.

    Class Attributes:
        backend_id: 고유 백엔드 식별자 (YAML config에서 참조)

    Example:
        class VertexReranker(BaseReranker):
            backend_id = "vertex"

            async def rerank(self, query, documents, top_k, config):
                # Vertex AI Ranking API 호출
                ...
    """

    backend_id: str = "base"

    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: List[DocumentToRerank],
        top_k: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> RerankResult:
        """문서 리랭킹 수행.

        Args:
            query: 검색 쿼리
            documents: 리랭킹할 문서 목록
            top_k: 반환할 상위 문서 수 (None이면 전체)
            config: 백엔드별 추가 설정

        Returns:
            RerankResult: 리랭킹 결과

        Raises:
            RerankerError: 리랭킹 실패 시
        """
        pass

    async def health_check(self) -> bool:
        """헬스 체크.

        Returns:
            True if healthy, False otherwise
        """
        return True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} backend_id={self.backend_id}>"


class RerankerError(Exception):
    """Reranker 관련 예외."""

    pass


__all__ = [
    "BaseReranker",
    "RerankResult",
    "DocumentToRerank",
    "RerankerError",
]
