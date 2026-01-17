"""Character Embedding Service.

Qdrant Named Vectors integration for character consistency.

Features:
- Named Vectors: face_embed (512D ArcFace), clip_embed (768D), style_embed (768D)
- Multi-modal similarity search
- 2026 Best Practices: Arc2Face, CoFE multi-expert fusion

References:
- StoryMem Paper: arXiv:2512.19539
- Arc2Face: arXiv:2403.11641
- CoFE: arXiv:2508.09476
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

COLLECTION_NAME = "character_embeddings"

# Named Vector dimensions (2026 best practices)
FACE_EMBED_DIM = 512   # ArcFace R100
CLIP_EMBED_DIM = 768   # CLIP ViT-L/14
STYLE_EMBED_DIM = 768  # Aesthetic predictor

# Similarity thresholds
FACE_THRESHOLD = 0.6
CLIP_THRESHOLD = 0.7
COMBINED_THRESHOLD = 0.65


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class CharacterEmbedding:
    """Character embedding data."""
    point_id: str
    character_id: str
    user_id: str
    face_embed: Optional[List[float]] = None
    clip_embed: Optional[List[float]] = None
    style_embed: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimilarityResult:
    """Similarity search result."""
    character_id: str
    score: float
    match_type: str  # face, clip, style, combined
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Character Embedding Service
# =============================================================================

class CharacterEmbeddingService:
    """Qdrant Named Vectors service for character embeddings.

    2026 Architecture:
    - face_embed: ArcFace R100 (512D) for identity matching
    - clip_embed: CLIP ViT-L/14 (768D) for visual similarity
    - style_embed: Aesthetic predictor (768D) for style matching

    Uses CoFE-style multi-expert fusion for comprehensive matching.
    """

    def __init__(self, client: Optional[QdrantClient] = None):
        """Initialize service.

        Args:
            client: Optional QdrantClient instance. If None, creates from settings.
        """
        self._client = client
        self._initialized = False

    @property
    def client(self) -> QdrantClient:
        """Lazy-loaded Qdrant client."""
        if self._client is None:
            self._client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=getattr(settings, 'QDRANT_API_KEY', None),
            )
        return self._client

    async def ensure_collection(self) -> bool:
        """Ensure character embeddings collection exists with named vectors.

        Returns:
            True if collection exists or was created.
        """
        if self._initialized:
            return True

        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == COLLECTION_NAME for c in collections)

            if not exists:
                logger.info(f"Creating collection: {COLLECTION_NAME}")

                # Create with named vectors (2026 best practice)
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config={
                        "face_embed": qmodels.VectorParams(
                            size=FACE_EMBED_DIM,
                            distance=qmodels.Distance.COSINE,
                        ),
                        "clip_embed": qmodels.VectorParams(
                            size=CLIP_EMBED_DIM,
                            distance=qmodels.Distance.COSINE,
                        ),
                        "style_embed": qmodels.VectorParams(
                            size=STYLE_EMBED_DIM,
                            distance=qmodels.Distance.COSINE,
                        ),
                    },
                    # Optimized HNSW settings for character search
                    hnsw_config=qmodels.HnswConfigDiff(
                        m=16,
                        ef_construct=100,
                    ),
                )

                # Create payload indexes for filtering
                self.client.create_payload_index(
                    collection_name=COLLECTION_NAME,
                    field_name="user_id",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                )
                self.client.create_payload_index(
                    collection_name=COLLECTION_NAME,
                    field_name="character_id",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                )
                self.client.create_payload_index(
                    collection_name=COLLECTION_NAME,
                    field_name="tags",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                )

                logger.info(f"Collection {COLLECTION_NAME} created with named vectors")

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            return False

    async def upsert_character(
        self,
        character_id: str,
        user_id: str,
        face_embed: Optional[List[float]] = None,
        clip_embed: Optional[List[float]] = None,
        style_embed: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Upsert character embeddings to Qdrant.

        Args:
            character_id: Character UUID
            user_id: Owner user ID
            face_embed: ArcFace embedding (512D)
            clip_embed: CLIP embedding (768D)
            style_embed: Style embedding (768D)
            metadata: Additional metadata (name, tags, etc.)

        Returns:
            Point ID if successful, None otherwise.
        """
        await self.ensure_collection()

        point_id = str(uuid.uuid4())

        # Build vectors dict (only include non-None vectors)
        vectors = {}
        if face_embed and len(face_embed) == FACE_EMBED_DIM:
            vectors["face_embed"] = face_embed
        if clip_embed and len(clip_embed) == CLIP_EMBED_DIM:
            vectors["clip_embed"] = clip_embed
        if style_embed and len(style_embed) == STYLE_EMBED_DIM:
            vectors["style_embed"] = style_embed

        if not vectors:
            logger.warning(f"No valid embeddings for character {character_id}")
            # Create placeholder with zero vectors
            vectors = {
                "face_embed": [0.0] * FACE_EMBED_DIM,
                "clip_embed": [0.0] * CLIP_EMBED_DIM,
                "style_embed": [0.0] * STYLE_EMBED_DIM,
            }

        # Build payload
        payload = {
            "character_id": character_id,
            "user_id": user_id,
            **(metadata or {}),
        }

        try:
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    qmodels.PointStruct(
                        id=point_id,
                        vector=vectors,
                        payload=payload,
                    )
                ],
            )
            logger.info(f"Upserted character {character_id} with point_id {point_id}")
            return point_id

        except Exception as e:
            logger.error(f"Failed to upsert character {character_id}: {e}")
            return None

    async def update_embeddings(
        self,
        point_id: str,
        face_embed: Optional[List[float]] = None,
        clip_embed: Optional[List[float]] = None,
        style_embed: Optional[List[float]] = None,
        metadata_update: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update existing character embeddings.

        Args:
            point_id: Existing Qdrant point ID
            face_embed: New face embedding
            clip_embed: New CLIP embedding
            style_embed: New style embedding
            metadata_update: Metadata fields to update

        Returns:
            True if successful.
        """
        await self.ensure_collection()

        try:
            # Update vectors
            vectors = {}
            if face_embed and len(face_embed) == FACE_EMBED_DIM:
                vectors["face_embed"] = face_embed
            if clip_embed and len(clip_embed) == CLIP_EMBED_DIM:
                vectors["clip_embed"] = clip_embed
            if style_embed and len(style_embed) == STYLE_EMBED_DIM:
                vectors["style_embed"] = style_embed

            if vectors:
                self.client.update_vectors(
                    collection_name=COLLECTION_NAME,
                    points=[
                        qmodels.PointVectors(
                            id=point_id,
                            vector=vectors,
                        )
                    ],
                )

            # Update payload
            if metadata_update:
                self.client.set_payload(
                    collection_name=COLLECTION_NAME,
                    payload=metadata_update,
                    points=[point_id],
                )

            return True

        except Exception as e:
            logger.error(f"Failed to update point {point_id}: {e}")
            return False

    async def delete_character(self, point_id: str) -> bool:
        """Delete character from Qdrant.

        Args:
            point_id: Qdrant point ID

        Returns:
            True if deleted successfully.
        """
        try:
            self.client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=qmodels.PointIdsList(points=[point_id]),
            )
            logger.info(f"Deleted point {point_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete point {point_id}: {e}")
            return False

    async def get_character_embedding(
        self,
        point_id: str,
    ) -> Optional[CharacterEmbedding]:
        """Retrieve character embedding by point ID.

        Args:
            point_id: Qdrant point ID

        Returns:
            CharacterEmbedding if found.
        """
        try:
            points = self.client.retrieve(
                collection_name=COLLECTION_NAME,
                ids=[point_id],
                with_vectors=True,
                with_payload=True,
            )

            if not points:
                return None

            point = points[0]
            vectors = point.vector or {}
            payload = point.payload or {}

            return CharacterEmbedding(
                point_id=str(point.id),
                character_id=payload.get("character_id", ""),
                user_id=payload.get("user_id", ""),
                face_embed=vectors.get("face_embed"),
                clip_embed=vectors.get("clip_embed"),
                style_embed=vectors.get("style_embed"),
                metadata=payload,
            )

        except Exception as e:
            logger.error(f"Failed to get point {point_id}: {e}")
            return None

    async def search_similar(
        self,
        query_embedding: CharacterEmbedding,
        user_id: str,
        limit: int = 5,
        vector_name: str = "combined",
        score_threshold: Optional[float] = None,
    ) -> List[SimilarityResult]:
        """Search for similar characters using CoFE-style multi-expert fusion.

        Args:
            query_embedding: Query character embedding
            user_id: Filter by user ownership
            limit: Maximum results
            vector_name: Which vector to use (face, clip, style, combined)
            score_threshold: Minimum similarity score

        Returns:
            List of similar characters.
        """
        await self.ensure_collection()

        # Set threshold based on vector type
        if score_threshold is None:
            thresholds = {
                "face": FACE_THRESHOLD,
                "clip": CLIP_THRESHOLD,
                "style": CLIP_THRESHOLD,
                "combined": COMBINED_THRESHOLD,
            }
            score_threshold = thresholds.get(vector_name, COMBINED_THRESHOLD)

        # User filter
        must_filter = [
            qmodels.FieldCondition(
                key="user_id",
                match=qmodels.MatchValue(value=user_id),
            )
        ]

        results = []

        if vector_name == "combined":
            # CoFE-style multi-expert fusion: search all vectors and merge
            search_tasks = []

            if query_embedding.face_embed:
                search_tasks.append(("face", query_embedding.face_embed, "face_embed"))
            if query_embedding.clip_embed:
                search_tasks.append(("clip", query_embedding.clip_embed, "clip_embed"))
            if query_embedding.style_embed:
                search_tasks.append(("style", query_embedding.style_embed, "style_embed"))

            # Aggregate scores across vectors
            score_map: Dict[str, Dict[str, float]] = {}

            for match_type, embedding, vec_name in search_tasks:
                try:
                    hits = self.client.search(
                        collection_name=COLLECTION_NAME,
                        query_vector=(vec_name, embedding),
                        query_filter=qmodels.Filter(must=must_filter),
                        limit=limit * 2,  # Get more to merge
                        with_payload=True,
                    )

                    for hit in hits:
                        char_id = hit.payload.get("character_id", str(hit.id))
                        if char_id not in score_map:
                            score_map[char_id] = {
                                "face": 0.0,
                                "clip": 0.0,
                                "style": 0.0,
                                "payload": hit.payload,
                            }
                        score_map[char_id][match_type] = max(
                            score_map[char_id][match_type],
                            hit.score,
                        )

                except Exception as e:
                    logger.warning(f"Search failed for {vec_name}: {e}")

            # CoFE fusion weights (identity-focused)
            WEIGHTS = {
                "face": 0.5,   # Identity (ArcFace) most important
                "clip": 0.3,   # Visual similarity
                "style": 0.2,  # Style consistency
            }

            for char_id, scores in score_map.items():
                combined_score = sum(
                    scores.get(k, 0.0) * w
                    for k, w in WEIGHTS.items()
                )

                if combined_score >= score_threshold:
                    results.append(SimilarityResult(
                        character_id=char_id,
                        score=combined_score,
                        match_type="combined",
                        metadata=scores.get("payload", {}),
                    ))

            # Sort by score descending
            results.sort(key=lambda x: x.score, reverse=True)
            results = results[:limit]

        else:
            # Single vector search
            vec_map = {
                "face": ("face_embed", query_embedding.face_embed),
                "clip": ("clip_embed", query_embedding.clip_embed),
                "style": ("style_embed", query_embedding.style_embed),
            }

            vec_name, embedding = vec_map.get(vector_name, (None, None))

            if not embedding:
                logger.warning(f"No embedding for vector type: {vector_name}")
                return []

            try:
                hits = self.client.search(
                    collection_name=COLLECTION_NAME,
                    query_vector=(vec_name, embedding),
                    query_filter=qmodels.Filter(must=must_filter),
                    limit=limit,
                    score_threshold=score_threshold,
                    with_payload=True,
                )

                for hit in hits:
                    results.append(SimilarityResult(
                        character_id=hit.payload.get("character_id", str(hit.id)),
                        score=hit.score,
                        match_type=vector_name,
                        metadata=hit.payload or {},
                    ))

            except Exception as e:
                logger.error(f"Search failed: {e}")

        return results

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics.

        Returns:
            Collection info dict.
        """
        try:
            info = self.client.get_collection(COLLECTION_NAME)
            return {
                "available": True,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "status": info.status.value if info.status else "unknown",
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
            }


# =============================================================================
# Singleton Instance
# =============================================================================

_service: Optional[CharacterEmbeddingService] = None


def get_character_embedding_service() -> CharacterEmbeddingService:
    """Get singleton service instance."""
    global _service
    if _service is None:
        _service = CharacterEmbeddingService()
    return _service
