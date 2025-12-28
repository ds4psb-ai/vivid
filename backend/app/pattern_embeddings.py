"""Pattern embedding generator for semantic search.

This module provides embedding generation for PatternCandidates using Gemini API.
Embeddings are stored in Qdrant for similarity search.

Usage:
    from app.pattern_embeddings import embed_pattern, seed_patterns_collection

    # Generate embedding for text
    vector = await embed_pattern("vertical framing symbolizing oppression")

    # Seed all patterns to Qdrant
    await seed_patterns_collection(db)

References:
    - Spec: 36_MCP_INTEGRATION_SPEC_V1.md
    - Model: PatternCandidate (models.py:384-408)
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import PatternCandidate
from app.qdrant_client import QdrantClient, get_qdrant_client

# Collection name for patterns
PATTERNS_COLLECTION = "crebit_patterns"
EMBEDDING_SIZE = 768  # text-embedding-004 default


async def get_embedding(text: str) -> List[float]:
    """Generate embedding using Gemini API.

    Args:
        text: Text to embed.

    Returns:
        Embedding vector (768 dimensions).
    """
    import httpx

    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={settings.GEMINI_API_KEY}"

    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": text}]},
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

    return data["embedding"]["values"]


async def embed_pattern(pattern: PatternCandidate) -> List[float]:
    """Generate embedding for a PatternCandidate.

    Args:
        pattern: The pattern to embed.

    Returns:
        Embedding vector.
    """
    # Combine relevant fields for embedding
    text_parts = [
        pattern.pattern_name,
        pattern.pattern_type,
        pattern.description or "",
    ]
    text = " | ".join(filter(None, text_parts))

    return await get_embedding(text)


def pattern_to_id(pattern: PatternCandidate) -> str:
    """Generate stable ID for pattern in Qdrant.

    Args:
        pattern: The pattern.

    Returns:
        Hash-based ID string.
    """
    key = f"{pattern.source_id}:{pattern.pattern_name}:{pattern.pattern_type}"
    return hashlib.md5(key.encode()).hexdigest()


def pattern_to_payload(pattern: PatternCandidate) -> Dict[str, Any]:
    """Convert pattern to Qdrant payload.

    Args:
        pattern: The pattern.

    Returns:
        Payload dictionary.
    """
    return {
        "pattern_id": str(pattern.id),
        "source_id": pattern.source_id,
        "pattern_name": pattern.pattern_name,
        "pattern_type": pattern.pattern_type,
        "description": pattern.description,
        "weight": pattern.weight,
        "confidence": pattern.confidence,
        "status": pattern.status,
    }


async def ensure_patterns_collection(client: Optional[QdrantClient] = None) -> bool:
    """Ensure patterns collection exists in Qdrant.

    Args:
        client: Optional Qdrant client.

    Returns:
        True if collection exists or was created.
    """
    if client is None:
        client = get_qdrant_client()

    collections = await client.list_collections()
    if PATTERNS_COLLECTION not in collections:
        return await client.create_collection(
            name=PATTERNS_COLLECTION,
            vector_size=EMBEDDING_SIZE,
            distance="Cosine",
        )
    return True


async def seed_patterns_collection(
    db: AsyncSession,
    *,
    batch_size: int = 50,
    status_filter: Optional[str] = None,
) -> Dict[str, int]:
    """Seed all PatternCandidates to Qdrant.

    Args:
        db: Database session.
        batch_size: Number of patterns per batch.
        status_filter: Optional status filter (e.g., "validated").

    Returns:
        Statistics dict with counts.
    """
    client = get_qdrant_client()
    await ensure_patterns_collection(client)

    # Query patterns
    query = select(PatternCandidate)
    if status_filter:
        query = query.where(PatternCandidate.status == status_filter)

    result = await db.execute(query)
    patterns = result.scalars().all()

    if not patterns:
        return {"total": 0, "embedded": 0, "errors": 0}

    embedded = 0
    errors = 0
    points = []

    for pattern in patterns:
        try:
            vector = await embed_pattern(pattern)
            points.append({
                "id": pattern_to_id(pattern),
                "vector": vector,
                "payload": pattern_to_payload(pattern),
            })
            embedded += 1

            # Batch upsert
            if len(points) >= batch_size:
                await client.upsert_points(PATTERNS_COLLECTION, points)
                points = []

        except Exception as e:
            print(f"Error embedding pattern {pattern.pattern_name}: {e}")
            errors += 1

    # Final batch
    if points:
        await client.upsert_points(PATTERNS_COLLECTION, points)

    return {
        "total": len(patterns),
        "embedded": embedded,
        "errors": errors,
    }


async def search_similar_patterns(
    query_text: str,
    limit: int = 10,
    score_threshold: float = 0.7,
    pattern_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search for similar patterns by text.

    Args:
        query_text: Query text to find similar patterns.
        limit: Maximum results.
        score_threshold: Minimum similarity score.
        pattern_type: Optional filter by pattern type.

    Returns:
        List of similar patterns with scores.
    """
    client = get_qdrant_client()

    # Generate query embedding
    query_vector = await get_embedding(query_text)

    # Build filter if needed
    filter_ = None
    if pattern_type:
        filter_ = {
            "must": [
                {"key": "pattern_type", "match": {"value": pattern_type}}
            ]
        }

    # Search
    response = await client.search(
        collection=PATTERNS_COLLECTION,
        query_vector=query_vector,
        limit=limit,
        score_threshold=score_threshold,
        filter_=filter_,
    )

    return [
        {
            "pattern_id": r.payload.get("pattern_id"),
            "pattern_name": r.payload.get("pattern_name"),
            "pattern_type": r.payload.get("pattern_type"),
            "description": r.payload.get("description"),
            "score": r.score,
        }
        for r in response.results
    ]
