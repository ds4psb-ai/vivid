"""Qdrant-backed Director Memory Store (replaces InMemoryDirectorMemoryStore)."""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from app.features.original_ip_foundry.memory_adapter import MemoryEntry

logger = logging.getLogger(__name__)

COLLECTION = "foundry_director_memory"


class QdrantDirectorMemoryStore:
    """Persistent director memory backed by Qdrant foundry_director_memory collection."""

    def __init__(self):
        self._embedder = None
        self._client = None
        self._available = True

    @property
    def embedder(self):
        if self._embedder is None:
            from app.services.embedder import get_embedder
            self._embedder = get_embedder()
        return self._embedder

    def _get_client(self):
        if not self._available:
            return None
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                from app.config import settings

                qdrant_api_key = (
                    settings.QDRANT_API_KEY.get_secret_value() if settings.QDRANT_API_KEY else None
                )
                self._client = QdrantClient(
                    url=settings.QDRANT_URL, api_key=qdrant_api_key, timeout=5,
                )
            except Exception as e:
                logger.warning(f"[DirectorMemory] Qdrant unavailable: {e}")
                self._available = False
                return None
        return self._client

    def put(self, entry: MemoryEntry) -> str:
        """Store a memory entry. Returns point_id (empty string on failure)."""
        client = self._get_client()
        if client is None:
            logger.warning("[DirectorMemory] Qdrant unavailable, memory not persisted")
            return ""

        text = f"{entry.note} {' '.join(entry.intent_tags)}"
        vector = self.embedder.embed(text)
        point_id = str(uuid.uuid4())

        from qdrant_client.http import models as qdrant_models

        payload = {
            "tenant_id": entry.tenant_id,
            "project_id": entry.project_id,
            "scene_id": entry.scene_id,
            "source_channel": entry.source_channel,
            "note": entry.note,
            "intent_tags": entry.intent_tags,
            "mise_en_scene_tags": entry.mise_en_scene_tags,
            "characters": entry.characters,
            "attachments": entry.attachments,
            "created_at": entry.created_at.isoformat(),
        }

        try:
            client.upsert(
                collection_name=COLLECTION,
                points=[qdrant_models.PointStruct(id=point_id, vector=vector, payload=payload)],
                wait=True,
            )
            logger.debug(f"[DirectorMemory] Stored point {point_id}")
        except Exception as e:
            logger.warning(f"[DirectorMemory] Upsert failed: {e}")

        return point_id

    def search(self, tenant_id: str, project_id: str, query: str, limit: int = 5) -> list[dict]:
        """Search director memory by semantic query with tenant+project filter."""
        client = self._get_client()
        if client is None:
            return []

        vector = self.embedder.embed(query)

        from qdrant_client.http import models as qdrant_models

        query_filter = qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="tenant_id", match=qdrant_models.MatchValue(value=tenant_id),
                ),
                qdrant_models.FieldCondition(
                    key="project_id", match=qdrant_models.MatchValue(value=project_id),
                ),
            ]
        )

        try:
            results = client.search(
                collection_name=COLLECTION,
                query_vector=vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
            )
            return [hit.payload for hit in results]
        except Exception as e:
            logger.warning(f"[DirectorMemory] Search failed: {e}")
            return []
