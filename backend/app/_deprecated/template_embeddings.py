"""Template embedding generator for recommendation system.

This module provides embedding generation for Templates using Gemini API.
Embeddings are stored in Qdrant for similarity-based recommendation.

Usage:
    from app.template_embeddings import search_similar_templates, seed_templates_collection

    # Search similar templates
    results = await search_similar_templates("vertical framing class division drama")

    # Seed all templates to Qdrant
    await seed_templates_collection(db)

References:
    - Spec: 36_MCP_INTEGRATION_SPEC_V1.md §2.3
    - Model: Template (models.py:27-42)
    - UI: 13_UI_DESIGN_GUIDE_2025-12.md §6.1
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Template
from app.qdrant_client import QdrantClient, get_qdrant_client

# Collection name for templates
TEMPLATES_COLLECTION = "crebit_templates"
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


async def embed_template(template: Template) -> List[float]:
    """Generate embedding for a Template.

    Combines title, description, and tags for rich semantic representation.

    Args:
        template: The template to embed.

    Returns:
        Embedding vector.
    """
    # Extract metadata from graph_data if available
    meta = template.graph_data.get("meta", {}) if template.graph_data else {}
    guide_sources = meta.get("guide_sources", [])
    
    text_parts = [
        template.title,
        template.description or "",
        " ".join(template.tags) if template.tags else "",
        " ".join(guide_sources) if guide_sources else "",
    ]
    text = " | ".join(filter(None, text_parts))

    if not text.strip():
        text = f"Template {template.slug}"

    return await get_embedding(text)


def template_to_id(template: Template) -> str:
    """Generate stable ID for template in Qdrant.

    Args:
        template: The template.

    Returns:
        Hash-based ID string.
    """
    return hashlib.md5(template.slug.encode()).hexdigest()


def template_to_payload(template: Template) -> Dict[str, Any]:
    """Convert template to Qdrant payload.

    Args:
        template: The template.

    Returns:
        Payload dictionary.
    """
    meta = template.graph_data.get("meta", {}) if template.graph_data else {}
    
    return {
        "template_id": str(template.id),
        "slug": template.slug,
        "title": template.title,
        "description": template.description,
        "tags": template.tags,
        "is_public": template.is_public,
        "preview_video_url": template.preview_video_url,
        "version": template.version,
        "guide_sources": meta.get("guide_sources", []),
        "evidence_refs": meta.get("evidence_refs", []),
    }


async def ensure_templates_collection(client: Optional[QdrantClient] = None) -> bool:
    """Ensure templates collection exists in Qdrant.

    Args:
        client: Optional Qdrant client.

    Returns:
        True if collection exists or was created.
    """
    if client is None:
        client = get_qdrant_client()

    collections = await client.list_collections()
    if TEMPLATES_COLLECTION not in collections:
        return await client.create_collection(
            name=TEMPLATES_COLLECTION,
            vector_size=EMBEDDING_SIZE,
            distance="Cosine",
        )
    return True


async def seed_templates_collection(
    db: AsyncSession,
    *,
    batch_size: int = 50,
    public_only: bool = True,
) -> Dict[str, int]:
    """Seed all Templates to Qdrant.

    Args:
        db: Database session.
        batch_size: Number of records per batch.
        public_only: Only seed public templates.

    Returns:
        Statistics dict with counts.
    """
    client = get_qdrant_client()
    await ensure_templates_collection(client)

    # Query templates
    query = select(Template)
    if public_only:
        query = query.where(Template.is_public.is_(True))

    result = await db.execute(query)
    templates = result.scalars().all()

    if not templates:
        return {"total": 0, "embedded": 0, "errors": 0}

    embedded = 0
    errors = 0
    points = []

    for template in templates:
        try:
            vector = await embed_template(template)
            points.append({
                "id": template_to_id(template),
                "vector": vector,
                "payload": template_to_payload(template),
            })
            embedded += 1

            # Batch upsert
            if len(points) >= batch_size:
                await client.upsert_points(TEMPLATES_COLLECTION, points)
                points = []

        except Exception as e:
            print(f"Error embedding template {template.slug}: {e}")
            errors += 1

    # Final batch
    if points:
        await client.upsert_points(TEMPLATES_COLLECTION, points)

    return {
        "total": len(templates),
        "embedded": embedded,
        "errors": errors,
    }


async def search_similar_templates(
    query_text: str,
    limit: int = 10,
    score_threshold: float = 0.7,
    tags: Optional[List[str]] = None,
    public_only: bool = True,
) -> List[Dict[str, Any]]:
    """Search for similar templates by text.

    Args:
        query_text: Query text to find similar templates.
        limit: Maximum results.
        score_threshold: Minimum similarity score.
        tags: Optional filter by tags (any match).
        public_only: Only return public templates.

    Returns:
        List of similar templates with scores.
    """
    client = get_qdrant_client()

    # Generate query embedding
    query_vector = await get_embedding(query_text)

    # Build filter if needed
    must_conditions = []
    if public_only:
        must_conditions.append({"key": "is_public", "match": {"value": True}})
    
    # Note: Tag filtering would require should conditions in Qdrant

    filter_ = {"must": must_conditions} if must_conditions else None

    # Search
    response = await client.search(
        collection=TEMPLATES_COLLECTION,
        query_vector=query_vector,
        limit=limit,
        score_threshold=score_threshold,
        filter_=filter_,
    )

    return [
        {
            "template_id": r.payload.get("template_id"),
            "slug": r.payload.get("slug"),
            "title": r.payload.get("title"),
            "description": r.payload.get("description"),
            "tags": r.payload.get("tags"),
            "preview_video_url": r.payload.get("preview_video_url"),
            "score": r.score,
        }
        for r in response.results
    ]


async def recommend_templates_for_evidence(
    evidence_summary: str,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Recommend templates based on evidence summary.

    This is the primary recommendation API for the Canvas UI.

    Args:
        evidence_summary: Summary text from EvidenceRecord.
        limit: Maximum recommendations.

    Returns:
        List of recommended templates with scores.
    """
    return await search_similar_templates(
        query_text=evidence_summary,
        limit=limit,
        score_threshold=0.6,  # Lower threshold for recommendations
        public_only=True,
    )
