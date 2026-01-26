"""NotebookLM Backend Adapter (P0 2026).

기존 NotebookLM 서비스를 Multi-RAG Protocol에 맞게 어댑팅.

Features:
    - RAGSourceBackend Protocol 구현
    - 기존 tier0_notebooklm 서비스 래핑
    - 노트북 ID 동적 설정

Usage:
    from app.rag.multi_rag.backends import NotebookLMAdapter

    adapter = NotebookLMAdapter(notebook_id="DNA_강주노")
    results = await adapter.query("계단 연출 기법")
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class NotebookLMAdapter:
    """NotebookLM 백엔드 어댑터.

    기존 tier0_notebooklm.NotebookLMService를 Multi-RAG Protocol에 맞게 래핑합니다.

    Attributes:
        notebook_id: 노트북 ID (예: "DNA_강주노")
        _service: NotebookLM 서비스 인스턴스 (lazy loading)

    Example:
        >>> adapter = NotebookLMAdapter(notebook_id="DNA_강주노")
        >>> results = await adapter.query("계단 연출 기법", limit=5)
        >>> for r in results:
        ...     print(r["content"][:100])
    """

    def __init__(self, notebook_id: str) -> None:
        """어댑터 초기화.

        Args:
            notebook_id: 노트북 ID (예: "DNA_강주노")
        """
        self.notebook_id = notebook_id
        self._service = None

    @property
    def service(self):
        """NotebookLM 서비스 (lazy loading)."""
        if self._service is None:
            from app.rag.tier0_notebooklm import get_notebooklm_service
            self._service = get_notebooklm_service()
        return self._service

    async def query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """NotebookLM 쿼리 실행.

        Args:
            query: 검색 쿼리
            filters: 메타데이터 필터 (notebook_id 오버라이드 가능)
            limit: 최대 결과 수

        Returns:
            검색 결과 리스트. 각 결과는 다음 필드 포함:
            - id: 소스 ID
            - content: 문서 내용
            - score: 관련성 점수
            - metadata: 추가 메타데이터
        """
        # notebook_id 오버라이드 지원
        notebook_id = (
            filters.get("notebook_id", self.notebook_id)
            if filters else self.notebook_id
        )

        try:
            result = await self.service.query_notebook(
                notebook_id=notebook_id,
                query=query,
            )

            # NotebookSource → Dict 변환
            documents: List[Dict[str, Any]] = []
            for idx, source in enumerate(result.sources[:limit]):
                documents.append({
                    "id": source.source_id or f"nlm_{notebook_id}_{idx}",
                    "content": source.excerpt or source.citation_text or "",
                    "score": source.relevance_score,
                    "metadata": {
                        "title": source.title,
                        "notebook_id": notebook_id,
                        "source_type": "notebooklm",
                        "grounded": result.grounded,
                    },
                })

            logger.debug(
                f"[NotebookLMAdapter] Query completed | "
                f"notebook={notebook_id} | "
                f"results={len(documents)}"
            )

            return documents

        except Exception as e:
            logger.error(f"[NotebookLMAdapter] Query failed: {e}")
            return []

    async def health_check(self) -> bool:
        """헬스 체크.

        Returns:
            True if service is healthy
        """
        try:
            # 서비스 인스턴스 확인
            _ = self.service
            return True
        except Exception as e:
            logger.warning(f"[NotebookLMAdapter] Health check failed: {e}")
            return False
