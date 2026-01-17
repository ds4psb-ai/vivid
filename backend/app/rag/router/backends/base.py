"""RAG Source Backend Protocol (Abstract).

모든 RAG 소스 백엔드가 구현해야 하는 인터페이스.
LlamaIndex QueryEngineTool + LangChain Agent 패턴 참조.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from app.rag.router.types import RAGDocument, RAGSourceType


@runtime_checkable
class RAGSourceBackend(Protocol):
    """RAG 소스 백엔드 프로토콜 (Duck Typing).

    모든 RAG 소스 어댑터가 구현해야 하는 인터페이스.
    """

    @property
    def source_type(self) -> RAGSourceType:
        """소스 타입 반환."""
        ...

    async def query(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[RAGDocument]:
        """쿼리 실행.

        Args:
            query: 검색 쿼리
            filters: 필터 조건 (dimension, auteur_key, user_id 등)
            limit: 최대 결과 수

        Returns:
            RAGDocument 리스트
        """
        ...

    async def health_check(self) -> bool:
        """헬스 체크.

        Returns:
            True if healthy, False otherwise
        """
        ...


class BaseRAGBackend(ABC):
    """RAG 백엔드 기본 추상 클래스.

    공통 로직을 포함한 추상 클래스.
    Protocol 대신 상속이 필요한 경우 사용.
    """

    _source_type: RAGSourceType

    @property
    def source_type(self) -> RAGSourceType:
        """소스 타입."""
        return self._source_type

    @abstractmethod
    async def query(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[RAGDocument]:
        """쿼리 실행."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """헬스 체크."""
        ...

    def _build_evidence_ref(
        self,
        doc_id: str,
        prefix: str,
        **kwargs: Any,
    ) -> str:
        """evidence_ref 생성 헬퍼.

        Args:
            doc_id: 문서 ID
            prefix: 접두사 (예: "notebooklm", "qdrant")
            **kwargs: 추가 경로 요소

        Returns:
            evidence_ref 문자열 (예: "db:notebooklm:bong:doc_123")
        """
        parts = ["db", prefix]
        for key, value in kwargs.items():
            if value is not None:
                parts.append(str(value))
        parts.append(doc_id)
        return ":".join(parts)
