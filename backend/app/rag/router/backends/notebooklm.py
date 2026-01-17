"""NotebookLM Backend Adapter (Tier0).

거장 DNA 지식베이스 접근을 위한 어댑터.
기존 tier0_notebooklm.py 클라이언트를 래핑합니다.
"""

from __future__ import annotations

import logging
from typing import Any

from app.rag.router.backends.base import BaseRAGBackend
from app.rag.router.types import RAGDocument, RAGSourceType

logger = logging.getLogger(__name__)


class NotebookLMBackend(BaseRAGBackend):
    """NotebookLM RAG 백엔드 (Tier0 거장 DNA)."""

    _source_type = RAGSourceType.AUTEUR_DNA

    def __init__(self, tier0_client: Any = None):
        """Initialize with Tier0 client.

        Args:
            tier0_client: 기존 tier0_notebooklm 클라이언트
                         None이면 lazy import
        """
        self._client = tier0_client
        self._initialized = tier0_client is not None

    def _ensure_client(self) -> Any:
        """클라이언트 lazy initialization."""
        if self._client is None:
            try:
                from app.rag.tier0_notebooklm import get_notebooklm_client

                self._client = get_notebooklm_client()
                self._initialized = True
            except ImportError:
                logger.warning(
                    "[NotebookLMBackend] tier0_notebooklm not available"
                )
                self._client = None
        return self._client

    async def query(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[RAGDocument]:
        """NotebookLM 쿼리 실행.

        Args:
            query: 검색 쿼리
            filters: 필터 조건
                - auteur_key: 거장 키 (필수)
            limit: 최대 결과 수

        Returns:
            RAGDocument 리스트
        """
        client = self._ensure_client()
        if client is None:
            logger.warning("[NotebookLMBackend] Client not available")
            return []

        auteur_key = (filters or {}).get("auteur_key")
        if not auteur_key:
            logger.warning("[NotebookLMBackend] auteur_key required")
            return []

        try:
            # 기존 Tier0 클라이언트 호출
            result = await client.query(
                query=query,
                auteur_key=auteur_key,
                max_results=limit,
            )

            documents = []
            for i, src in enumerate(result.sources or []):
                doc = RAGDocument(
                    id=src.source_id or f"nbm_{auteur_key}_{i}",
                    content=src.content or "",
                    score=src.relevance_score or (1.0 - i * 0.1),
                    metadata={
                        "auteur_key": auteur_key,
                        "source_title": src.title,
                    },
                    evidence_ref=self._build_evidence_ref(
                        doc_id=src.source_id or f"{i}",
                        prefix="notebooklm",
                        auteur_key=auteur_key,
                    ),
                    source_id="notebooklm",
                    source_type=RAGSourceType.AUTEUR_DNA,
                )
                documents.append(doc)

            return documents

        except Exception as e:
            logger.error(f"[NotebookLMBackend] Query failed: {e}")
            return []

    async def health_check(self) -> bool:
        """헬스 체크."""
        client = self._ensure_client()
        if client is None:
            return False

        try:
            # 간단한 ping 또는 리스트 조회
            return await client.is_connected()
        except Exception:
            return False


class MockNotebookLMBackend(BaseRAGBackend):
    """테스트용 Mock NotebookLM 백엔드."""

    _source_type = RAGSourceType.AUTEUR_DNA

    def __init__(self, mock_responses: dict[str, list[RAGDocument]] | None = None):
        self._mock_responses = mock_responses or {}

    async def query(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[RAGDocument]:
        """Mock 쿼리."""
        auteur_key = (filters or {}).get("auteur_key", "default")

        if auteur_key in self._mock_responses:
            return self._mock_responses[auteur_key][:limit]

        # 기본 mock 응답
        return [
            RAGDocument(
                id=f"mock_{auteur_key}_1",
                content=f"Mock content for {auteur_key} about {query}",
                score=0.9,
                metadata={"auteur_key": auteur_key},
                evidence_ref=f"db:notebooklm:{auteur_key}:mock_1",
                source_id="notebooklm",
                source_type=RAGSourceType.AUTEUR_DNA,
            )
        ]

    async def health_check(self) -> bool:
        """항상 True."""
        return True
