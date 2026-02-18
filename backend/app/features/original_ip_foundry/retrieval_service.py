"""4-pass retrieval: director_context, shot_reference, payload_filter, transition_rerank."""
from __future__ import annotations

import logging
from typing import Optional

from app.features.original_ip_foundry.memory_adapter import InMemoryDirectorMemoryStore
from app.features.original_ip_foundry.pattern_extraction_service import PatternExtractionService

logger = logging.getLogger(__name__)


class FoundryRetrievalService:
    """Route requests across 4 retrieval passes."""

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
        filters: Optional[dict] = None,
    ) -> dict:
        if query_type == "director_context":
            return self._pass_memory(tenant_id, project_id, query, limit)
        elif query_type == "shot_reference":
            return self._pass_pattern(project_id, query, limit)
        elif query_type == "payload_filter":
            return self._pass_payload_filter(project_id, query, limit, filters or {})
        elif query_type == "transition_rerank":
            return self._pass_transition_rerank(project_id, query, limit)
        else:
            return self._pass_pattern(project_id, query, limit)

    def _pass_memory(self, tenant_id: str, project_id: str, query: str, limit: int) -> dict:
        """Pass 1: Director context from OpenClaw memory."""
        items = self._memory_store.search(
            tenant_id=tenant_id,
            project_id=project_id,
            query=query,
            limit=limit,
        )
        return {"source": "openclaw_memory", "query_type": "director_context", "items": items}

    def _pass_pattern(self, project_id: str, query: str, limit: int) -> dict:
        """Pass 2: Shot reference from pattern atom corpus."""
        items = self._pattern_service.search_atoms(
            project_id=project_id, query=query, limit=limit,
        )
        return {"source": "foundry_shot_corpus", "query_type": "shot_reference", "items": items}

    def _pass_payload_filter(self, project_id: str, query: str, limit: int, filters: dict) -> dict:
        """Pass 3: Qdrant payload-filtered search (genre, movement, rights)."""
        items = self._pattern_service.search_atoms(
            project_id=project_id, query=query, limit=limit,
        )
        if not filters:
            return {"source": "foundry_payload_filter", "query_type": "payload_filter", "items": items}

        filtered = []
        for item in items:
            match = True
            for key, value in filters.items():
                item_value = item.get(key)
                if isinstance(value, list):
                    if item_value not in value:
                        match = False
                        break
                elif item_value != value:
                    match = False
                    break
            if match:
                filtered.append(item)
        return {
            "source": "foundry_payload_filter",
            "query_type": "payload_filter",
            "items": filtered[:limit],
            "filters_applied": filters,
        }

    def _pass_transition_rerank(self, project_id: str, query: str, limit: int) -> dict:
        """Pass 4: Pattern search + transition rule affinity reranking."""
        items = self._pattern_service.search_atoms(
            project_id=project_id, query=query, limit=max(limit * 3, 15),
        )
        # Rerank by transition affinity: prefer non-cut transitions
        transition_bonus = {
            "dissolve": 0.15,
            "match_cut": 0.12,
            "fade": 0.10,
            "wipe": 0.08,
            "cut": 0.0,
        }
        scored = []
        for item in items:
            base_confidence = item.get("confidence", 0.5)
            transition = item.get("transition", "cut")
            bonus = transition_bonus.get(transition, 0.05)
            scored.append((base_confidence + bonus, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return {
            "source": "foundry_transition_rerank",
            "query_type": "transition_rerank",
            "items": [item for _, item in scored[:limit]],
        }
