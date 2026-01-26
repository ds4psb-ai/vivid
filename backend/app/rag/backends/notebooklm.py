"""NotebookLM Backend.

NotebookLM Enterprise API를 통한 Grounded RAG.
tier0_notebooklm.py를 래핑.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .base import BaseBackend, RetrievalResult

if TYPE_CHECKING:
    from app.rag.tier0_notebooklm import NotebookLMService

logger = logging.getLogger(__name__)


class NotebookLMBackend(BaseBackend):
    """NotebookLM Grounded RAG Backend.

    Features:
    - 거장 DNA 노트북 검색
    - 자동 인라인 인용
    - 환각률 13% (vs GPT-4o 40%)
    """

    backend_id = "notebooklm"

    def __init__(self) -> None:
        self._service: Optional["NotebookLMService"] = None

    def _get_service(self) -> "NotebookLMService":
        """NotebookLM 서비스 (lazy load)."""
        if self._service is None:
            from app.rag.tier0_notebooklm import get_notebooklm_service

            self._service = get_notebooklm_service()
        return self._service

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """NotebookLM 검색.

        Config options:
            notebook_id: 노트북 ID (예: "DNA_강주노") - 필수
            source_filter: 소스 필터 (예: "auteur_dna")
        """
        config = config or {}

        notebook_id = config.get("notebook_id")
        if not notebook_id:
            logger.warning("[NotebookLMBackend] notebook_id not specified")
            return []

        try:
            service = self._get_service()
            result = await service.query_notebook(
                notebook_id=notebook_id,
                query=query,
                max_sources=limit,
            )

            return [
                RetrievalResult(
                    doc_id=src.source_id,
                    text=src.excerpt or src.citation_text,
                    score=result.confidence * (1.0 - idx * 0.05),  # 순위별 감소
                    source=self.backend_id,
                    rank=idx + 1,
                    metadata={
                        "notebook_id": notebook_id,
                        "grounded": result.grounded,
                        "title": src.title,
                    },
                )
                for idx, src in enumerate(result.sources[:limit])
            ]
        except Exception as e:
            logger.error(f"[NotebookLMBackend] Retrieve failed: {e}")
            return []

    async def health_check(self) -> bool:
        """NotebookLM 연결 상태 확인."""
        try:
            service = self._get_service()
            return service is not None
        except Exception:
            return False
