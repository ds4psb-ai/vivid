"""Evidence embedding generator for semantic search.

This module provides embedding generation for EvidenceRecords using Gemini API.
Embeddings are stored in Qdrant for similarity search.

Usage:
    from app.evidence_embeddings import embed_evidence, seed_evidence_collection

    # Search similar evidence
    results = await search_similar_evidence("visual framing techniques for class division")

    # Seed all evidence to Qdrant
    await seed_evidence_collection(db)

References:
    - Spec: 36_MCP_INTEGRATION_SPEC_V1.md §2.3
    - Model: EvidenceRecord (models.py:257-315)
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import EvidenceRecord
from app.qdrant_client import QdrantClient, get_qdrant_client

# Collection name for evidence
EVIDENCE_COLLECTION = "crebit_evidence"
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


async def embed_evidence(evidence: EvidenceRecord) -> List[float]:
    """Generate embedding for an EvidenceRecord.

    Combines key fields for rich semantic representation.

    Args:
        evidence: The evidence record to embed.

    Returns:
        Embedding vector.
    """
    text_parts = [
        evidence.summary[:500] if evidence.summary else "",
        evidence.cluster_label or "",
        evidence.style_logic[:200] if evidence.style_logic else "",
        evidence.director_intent[:200] if evidence.director_intent else "",
        " ".join(evidence.labels) if evidence.labels else "",
    ]
    text = " | ".join(filter(None, text_parts))

    if not text.strip():
        text = f"Evidence from source {evidence.source_id}"

    return await get_embedding(text)


def evidence_to_id(evidence: EvidenceRecord) -> str:
    """Generate stable ID for evidence in Qdrant.

    Args:
        evidence: The evidence record.

    Returns:
        Hash-based ID string.
    """
    key = f"{evidence.source_id}:{evidence.output_type}:{evidence.output_language}"
    return hashlib.md5(key.encode()).hexdigest()


def evidence_to_payload(evidence: EvidenceRecord) -> Dict[str, Any]:
    """Convert evidence to Qdrant payload.

    Args:
        evidence: The evidence record.

    Returns:
        Payload dictionary.
    """
    return {
        "evidence_id": str(evidence.id),
        "source_id": evidence.source_id,
        "summary": evidence.summary[:500] if evidence.summary else None,
        "cluster_id": evidence.cluster_id,
        "cluster_label": evidence.cluster_label,
        "guide_type": evidence.guide_type,
        "output_type": evidence.output_type,
        "output_language": evidence.output_language,
        "labels": evidence.labels,
        "confidence": evidence.confidence,
    }


async def ensure_evidence_collection(client: Optional[QdrantClient] = None) -> bool:
    """Ensure evidence collection exists in Qdrant.

    Args:
        client: Optional Qdrant client.

    Returns:
        True if collection exists or was created.
    """
    if client is None:
        client = get_qdrant_client()

    collections = await client.list_collections()
    if EVIDENCE_COLLECTION not in collections:
        return await client.create_collection(
            name=EVIDENCE_COLLECTION,
            vector_size=EMBEDDING_SIZE,
            distance="Cosine",
        )
    return True


async def seed_evidence_collection(
    db: AsyncSession,
    *,
    batch_size: int = 50,
    output_type_filter: Optional[str] = None,
) -> Dict[str, int]:
    """Seed all EvidenceRecords to Qdrant.

    Args:
        db: Database session.
        batch_size: Number of records per batch.
        output_type_filter: Optional filter by output_type.

    Returns:
        Statistics dict with counts.
    """
    client = get_qdrant_client()
    await ensure_evidence_collection(client)

    # Query evidence
    query = select(EvidenceRecord)
    if output_type_filter:
        query = query.where(EvidenceRecord.output_type == output_type_filter)

    result = await db.execute(query)
    records = result.scalars().all()

    if not records:
        return {"total": 0, "embedded": 0, "errors": 0}

    embedded = 0
    errors = 0
    points = []

    for record in records:
        try:
            vector = await embed_evidence(record)
            points.append({
                "id": evidence_to_id(record),
                "vector": vector,
                "payload": evidence_to_payload(record),
            })
            embedded += 1

            # Batch upsert
            if len(points) >= batch_size:
                await client.upsert_points(EVIDENCE_COLLECTION, points)
                points = []

        except Exception as e:
            print(f"Error embedding evidence {record.source_id}: {e}")
            errors += 1

    # Final batch
    if points:
        await client.upsert_points(EVIDENCE_COLLECTION, points)

    return {
        "total": len(records),
        "embedded": embedded,
        "errors": errors,
    }


async def search_similar_evidence(
    query_text: str,
    limit: int = 10,
    score_threshold: float = 0.7,
    cluster_id: Optional[str] = None,
    output_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search for similar evidence by text.

    Args:
        query_text: Query text to find similar evidence.
        limit: Maximum results.
        score_threshold: Minimum similarity score.
        cluster_id: Optional filter by cluster.
        output_type: Optional filter by output type.

    Returns:
        List of similar evidence with scores.
    """
    client = get_qdrant_client()

    # Generate query embedding
    query_vector = await get_embedding(query_text)

    # Build filter if needed
    must_conditions = []
    if cluster_id:
        must_conditions.append({"key": "cluster_id", "match": {"value": cluster_id}})
    if output_type:
        must_conditions.append({"key": "output_type", "match": {"value": output_type}})

    filter_ = {"must": must_conditions} if must_conditions else None

    # Search
    response = await client.search(
        collection=EVIDENCE_COLLECTION,
        query_vector=query_vector,
        limit=limit,
        score_threshold=score_threshold,
        filter_=filter_,
    )

    return [
        {
            "evidence_id": r.payload.get("evidence_id"),
            "source_id": r.payload.get("source_id"),
            "summary": r.payload.get("summary"),
            "cluster_label": r.payload.get("cluster_label"),
            "score": r.score,
        }
        for r in response.results
    ]
