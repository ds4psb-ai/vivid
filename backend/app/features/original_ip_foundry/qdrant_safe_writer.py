"""Qdrant write helper with optimistic revision checks for Foundry collections."""
from __future__ import annotations

from typing import Any, Sequence

try:
    from qdrant_client import models as qdrant_models  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    qdrant_models = None


class FoundryQdrantSafeWriter:
    """Best-effort conditional update strategy for Qdrant 1.16+ clients."""

    def __init__(self, client):
        self.client = client

    def upsert_point(
        self,
        *,
        collection_name: str,
        point_id: str,
        vector: Sequence[float],
        payload: dict[str, Any],
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        if self.client is None:
            return {"status": "disabled", "reason": "qdrant_client_unavailable"}

        existing = self.client.retrieve(
            collection_name=collection_name,
            ids=[point_id],
            with_payload=True,
            with_vectors=False,
        )
        if existing:
            current_revision = int((existing[0].payload or {}).get("revision", 0))
        else:
            current_revision = 0

        if expected_revision is not None and current_revision != expected_revision:
            return {
                "status": "conflict",
                "point_id": point_id,
                "expected_revision": expected_revision,
                "current_revision": current_revision,
            }

        next_revision = current_revision + 1
        merged_payload = {
            **payload,
            "revision": next_revision,
        }

        ordering = "strong"
        if qdrant_models is not None and hasattr(qdrant_models, "WriteOrdering"):
            ordering = qdrant_models.WriteOrdering.STRONG

        if qdrant_models is not None and hasattr(qdrant_models, "PointStruct"):
            point = qdrant_models.PointStruct(
                id=point_id,
                vector=list(vector),
                payload=merged_payload,
            )
        else:
            point = {
                "id": point_id,
                "vector": list(vector),
                "payload": merged_payload,
            }

        self.client.upsert(
            collection_name=collection_name,
            points=[point],
            wait=True,
            ordering=ordering,
        )
        return {
            "status": "ok",
            "point_id": point_id,
            "revision": next_revision,
        }
