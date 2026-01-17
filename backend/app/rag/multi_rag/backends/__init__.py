"""Multi-RAG Backend Adapters (P0 2026).

기존 RAG 백엔드를 Multi-RAG 시스템에 통합하기 위한 어댑터들.

Adapters:
    - NotebookLMAdapter: NotebookLM (Tier 0) 어댑터
    - QdrantAdapter: Qdrant Hybrid (Tier 1) 어댑터
    - UserHistoryAdapter: 사용자 히스토리 어댑터

Usage:
    from app.rag.multi_rag.backends import (
        NotebookLMAdapter,
        QdrantAdapter,
        UserHistoryAdapter,
    )

    # Create adapters
    nlm_adapter = NotebookLMAdapter(notebook_id="DNA_봉준호")
    qdrant_adapter = QdrantAdapter(dimension="4D")

    # Register with registry
    registry.register_sync(notebooklm_spec, nlm_adapter)
    registry.register_sync(qdrant_spec, qdrant_adapter)
"""
from app.rag.multi_rag.backends.notebooklm_adapter import NotebookLMAdapter
from app.rag.multi_rag.backends.qdrant_adapter import QdrantAdapter
from app.rag.multi_rag.backends.user_history_adapter import UserHistoryAdapter

__all__ = [
    "NotebookLMAdapter",
    "QdrantAdapter",
    "UserHistoryAdapter",
]
