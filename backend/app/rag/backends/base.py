"""RAG Backend Abstract Base Class.

모든 RAG 백엔드가 구현해야 하는 인터페이스 정의.

Usage:
    from app.rag.backends import BaseBackend, RetrievalResult

    class MyBackend(BaseBackend):
        backend_id = "my_backend"

        async def retrieve(self, query, limit, filters, config):
            ...
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RetrievalResult:
    """통합 검색 결과.

    모든 백엔드에서 반환하는 표준 결과 형식.

    Attributes:
        doc_id: 문서 고유 ID
        text: 문서 텍스트 (또는 요약)
        score: 관련성 점수 (0.0 ~ 1.0, 백엔드별 정규화)
        source: 백엔드 ID (예: "qdrant_hybrid", "notebooklm")
        rank: 해당 백엔드 내 순위 (1부터 시작)
        metadata: 추가 메타데이터 (dimension, app_key 등)
    """

    doc_id: str
    text: str
    score: float
    source: str
    rank: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseBackend(ABC):
    """RAG 백엔드 기본 인터페이스.

    모든 백엔드 구현체는 이 클래스를 상속해야 합니다.

    Class Attributes:
        backend_id: 고유 백엔드 식별자 (예: "qdrant_hybrid", "notebooklm")
                    YAML manifest의 backends[].id와 매칭됨
    """

    backend_id: str = ""  # 서브클래스에서 오버라이드

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """검색 실행.

        Args:
            query: 검색 쿼리
            limit: 최대 결과 수
            filters: 메타데이터 필터 (app_key, dataset_id 등)
            config: 백엔드별 추가 설정 (dimension, collection 등)

        Returns:
            RetrievalResult 리스트 (score 내림차순)
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """백엔드 상태 확인.

        Returns:
            True if healthy, False otherwise
        """
        pass

    async def index_document(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """문서 인덱싱 (선택적 구현).

        인덱싱을 지원하지 않는 백엔드는 False 반환.

        Args:
            doc_id: 문서 ID
            text: 문서 텍스트
            metadata: 추가 메타데이터

        Returns:
            True if successful, False if not supported or failed
        """
        return False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(backend_id='{self.backend_id}')>"
