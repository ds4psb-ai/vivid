"""Qdrant-backed Pattern Atom Store for Original-IP Foundry."""
from __future__ import annotations

import logging
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

COLLECTION = "foundry_pattern_atoms"


class QdrantPatternAtomStore:
    """Persistent pattern atom storage backed by Qdrant foundry_pattern_atoms collection."""

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
                logger.warning(f"[PatternAtomStore] Qdrant unavailable: {e}")
                self._available = False
                return None
        return self._client

    def upsert_batch(
        self,
        *,
        project_id: str,
        scene_id: str,
        tenant_id: str = "default",
        atoms: list[dict],
    ) -> list[str]:
        """Upsert pattern atoms into Qdrant. Returns list of point_ids."""
        client = self._get_client()
        if client is None:
            logger.warning("[PatternAtomStore] Qdrant unavailable, atoms not persisted")
            return []

        if not atoms:
            return []

        texts = [
            f"{a.get('atom_id', '')} {a.get('camera_angle', '')} "
            f"{a.get('camera_movement', '')} {a.get('shot_size', '')} "
            f"{a.get('emotion_tone', '')}"
            for a in atoms
        ]
        vectors = self.embedder.embed_batch(texts)

        from qdrant_client.http import models as qdrant_models

        points = []
        point_ids = []
        for atom, vector in zip(atoms, vectors):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{atom.get('atom_id', '')}:{project_id}"))
            point_ids.append(point_id)

            payload = {
                "project_id": project_id,
                "scene_id": scene_id,
                "tenant_id": tenant_id,
                "atom_id": atom.get("atom_id", ""),
                "camera_angle": atom.get("camera_angle", ""),
                "camera_movement": atom.get("camera_movement", ""),
                "shot_size": atom.get("shot_size", ""),
                "emotion_tone": atom.get("emotion_tone", ""),
                "transition": atom.get("transition", ""),
                "frequency": atom.get("frequency", 0),
                "confidence": atom.get("confidence", 0.0),
            }

            points.append(qdrant_models.PointStruct(id=point_id, vector=vector, payload=payload))

        try:
            client.upsert(
                collection_name=COLLECTION,
                points=points,
                wait=True,
            )
            logger.debug(f"[PatternAtomStore] Upserted {len(points)} atoms for project {project_id}")
        except Exception as e:
            logger.warning(f"[PatternAtomStore] Upsert failed: {e}")
            return []

        return point_ids

    def search_atoms(
        self,
        *,
        project_id: str,
        query: str,
        limit: int = 5,
        tenant_id: str = "default",
    ) -> list[dict]:
        """Search pattern atoms by semantic query with project+tenant filter."""
        client = self._get_client()
        if client is None:
            return []

        vector = self.embedder.embed(query)

        from qdrant_client.http import models as qdrant_models

        query_filter = qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="project_id", match=qdrant_models.MatchValue(value=project_id),
                ),
                qdrant_models.FieldCondition(
                    key="tenant_id", match=qdrant_models.MatchValue(value=tenant_id),
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
            logger.warning(f"[PatternAtomStore] Search failed: {e}")
            return []
