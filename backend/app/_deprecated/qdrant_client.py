"""Qdrant vector database client for semantic search.

This module provides a Qdrant-based vector search client for AI/RAG pipelines.
Used for semantic similarity matching of PatternCandidates, Evidence, and Templates.

Usage:
    from app.qdrant_client import get_qdrant_client, search_similar

    # Simple similarity search
    results = await search_similar(
        collection="patterns",
        query_vector=embedding,
        limit=10,
    )

References:
    - Spec: 36_MCP_INTEGRATION_SPEC_V1.md
    - Docker: docker-compose.yml (port 6333)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

# Import settings for centralized config
try:
    from app.config import settings
    QDRANT_URL = settings.QDRANT_URL
    QDRANT_API_KEY = settings.QDRANT_API_KEY
except ImportError:
    # Fallback for standalone usage
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")


@dataclass
class QdrantSearchResult:
    """Single search result from Qdrant."""

    id: str
    score: float
    payload: Dict[str, Any]
    vector: Optional[List[float]] = None


@dataclass
class QdrantSearchResponse:
    """Response from Qdrant search."""

    results: List[QdrantSearchResult]
    time_ms: float


class QdrantClient:
    """Qdrant vector database client.

    Attributes:
        base_url: Qdrant server URL (default: localhost:6333)
        api_key: Optional API key for cloud deployments

    Example:
        client = QdrantClient()
        await client.create_collection("patterns", vector_size=768)
        results = await client.search("patterns", query_vector, limit=5)
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize Qdrant client.

        Args:
            base_url: Qdrant server URL.
            api_key: Optional API key for auth.
        """
        self.base_url = (base_url or QDRANT_URL).rstrip("/")
        self.api_key = api_key or QDRANT_API_KEY

    def _headers(self) -> Dict[str, str]:
        """Build request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key
        return headers

    async def health_check(self) -> bool:
        """Check if Qdrant server is healthy.

        Returns:
            True if server is healthy.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/healthz",
                    headers=self._headers(),
                )
                return response.status_code == 200
        except Exception:
            return False

    async def list_collections(self) -> List[str]:
        """List all collections.

        Returns:
            List of collection names.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/collections",
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json()
            return [c["name"] for c in data.get("result", {}).get("collections", [])]

    async def create_collection(
        self,
        name: str,
        vector_size: int,
        distance: str = "Cosine",
    ) -> bool:
        """Create a new collection.

        Args:
            name: Collection name.
            vector_size: Dimension of vectors.
            distance: Distance metric (Cosine, Euclid, Dot).

        Returns:
            True if created successfully.
        """
        payload = {
            "vectors": {
                "size": vector_size,
                "distance": distance,
            }
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.put(
                f"{self.base_url}/collections/{name}",
                json=payload,
                headers=self._headers(),
            )
            return response.status_code in (200, 201)

    async def upsert_points(
        self,
        collection: str,
        points: List[Dict[str, Any]],
    ) -> bool:
        """Upsert points into collection.

        Args:
            collection: Collection name.
            points: List of {"id": str, "vector": [...], "payload": {...}}

        Returns:
            True if successful.
        """
        payload = {"points": points}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{self.base_url}/collections/{collection}/points",
                json=payload,
                headers=self._headers(),
            )
            response.raise_for_status()
            return True

    async def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_: Optional[Dict[str, Any]] = None,
        with_payload: bool = True,
        with_vector: bool = False,
    ) -> QdrantSearchResponse:
        """Search for similar vectors.

        Args:
            collection: Collection name.
            query_vector: Query embedding vector.
            limit: Maximum results.
            score_threshold: Minimum score filter.
            filter_: Optional payload filter.
            with_payload: Include payload in results.
            with_vector: Include vector in results.

        Returns:
            QdrantSearchResponse with results.
        """
        payload: Dict[str, Any] = {
            "vector": query_vector,
            "limit": limit,
            "with_payload": with_payload,
            "with_vector": with_vector,
        }
        if score_threshold is not None:
            payload["score_threshold"] = score_threshold
        if filter_:
            payload["filter"] = filter_

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/collections/{collection}/points/search",
                json=payload,
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json()

        results = [
            QdrantSearchResult(
                id=str(r.get("id")),
                score=r.get("score", 0.0),
                payload=r.get("payload", {}),
                vector=r.get("vector") if with_vector else None,
            )
            for r in data.get("result", [])
        ]

        return QdrantSearchResponse(
            results=results,
            time_ms=data.get("time", 0.0) * 1000,
        )


# Module-level singleton
_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """Get or create Qdrant client singleton.

    Returns:
        QdrantClient instance.
    """
    global _client
    if _client is None:
        _client = QdrantClient()
    return _client


async def search_similar(
    collection: str,
    query_vector: List[float],
    limit: int = 10,
    score_threshold: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Convenience function for similarity search.

    Args:
        collection: Collection name.
        query_vector: Query embedding.
        limit: Maximum results.
        score_threshold: Minimum score.

    Returns:
        List of result dictionaries.
    """
    client = get_qdrant_client()
    response = await client.search(
        collection,
        query_vector,
        limit=limit,
        score_threshold=score_threshold,
    )
    return [
        {
            "id": r.id,
            "score": r.score,
            "payload": r.payload,
        }
        for r in response.results
    ]
