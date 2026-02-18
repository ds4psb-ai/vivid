"""Dual-path retrieval (director memory first, shot corpus second)."""
from __future__ import annotations

from app.features.original_ip_foundry.memory_adapter import InMemoryDirectorMemoryStore
from app.features.original_ip_foundry.pattern_extraction_service import PatternExtractionService


class FoundryRetrievalService:
    """Route requests to memory search or shot/pattern corpus search."""

    def __init__(
        self,
        memory_store: InMemoryDirectorMemoryStore,
        pattern_service: PatternExtractionService,
    ):
        self._memory_store = memory_store
        self._pattern_service = pattern_service

    def query(
        self,
        *,
        tenant_id: str,
        project_id: str,
        query_type: str,
        query: str,
        limit: int = 5,
    ) -> dict:
        if query_type == "director_context":
            items = self._memory_store.search(
                tenant_id=tenant_id,
                project_id=project_id,
                query=query,
                limit=limit,
            )
            return {
                "source": "openclaw_memory",
                "query_type": query_type,
                "items": items,
            }

        items = self._pattern_service.search_atoms(project_id=project_id, query=query, limit=limit)
        return {
            "source": "foundry_shot_corpus",
            "query_type": query_type,
            "items": items,
        }
