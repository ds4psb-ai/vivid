"""VPE (Video Parsing Engine) Storage Service.

Manages storage and retrieval of Logic Vectors in Qdrant.

Features:
- Logic Vector indexing with dense+sparse embeddings
- Auteur-filtered search
- Batch operations for bulk imports
- Graceful degradation when Qdrant unavailable

Usage:
    from app.services.vpe_storage import VPEStorage, get_vpe_storage

    storage = get_vpe_storage()
    doc_id = await storage.store_logic_vector(logic_vector)
    results = await storage.search_by_style("cinematic noir lighting", auteur_filter="nolan")
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient, models
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings
from app.schemas.vpe import LogicVector, VPEQueryResult
from app.services.embedder import get_embedder
from app.services.circuit_breaker import QDRANT_BREAKER, CircuitBreakerOpen

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

VPE_COLLECTION_NAME = "vpe_logic_vectors"
VPE_COLLECTION_HYBRID = "vpe_logic_vectors_hybrid"
VECTOR_SIZE = 384  # MiniLM-L6-v2

# Sparse embedder (lazy loaded)
_sparse_embedder = None


def _get_sparse_embedder():
    """Lazy-load sparse embedder for hybrid search."""
    global _sparse_embedder
    if _sparse_embedder is None:
        try:
            from app.rag.sparse import SparseEmbedder
            _sparse_embedder = SparseEmbedder()
        except ImportError:
            logger.warning("[VPEStorage] fastembed not installed, hybrid search disabled")
            return None
    return _sparse_embedder


# =============================================================================
# VPE Storage Service
# =============================================================================

class VPEStorage:
    """Storage service for VPE Logic Vectors using Qdrant."""

    def __init__(self, use_hybrid: bool = True):
        """Initialize VPE storage.

        Args:
            use_hybrid: Whether to use hybrid (dense + sparse) embeddings
        """
        self.use_hybrid = use_hybrid
        self.collection_name = VPE_COLLECTION_HYBRID if use_hybrid else VPE_COLLECTION_NAME

        self._client: Optional[QdrantClient] = None
        self._available: bool = True
        self._embedder = None

    def _get_client(self) -> Optional[QdrantClient]:
        """Get or create Qdrant client."""
        if self._client is None:
            try:
                self._client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY.get_secret_value() if settings.QDRANT_API_KEY else None,
                    timeout=10,
                )
                self._available = True
            except Exception as e:
                logger.warning(f"[VPEStorage] Failed to connect to Qdrant: {e}")
                self._available = False
                return None
        return self._client

    def _get_embedder(self):
        """Get or create embedder."""
        if self._embedder is None:
            self._embedder = get_embedder()
        return self._embedder

    async def ensure_collection(self) -> bool:
        """Ensure the VPE collection exists.

        Returns:
            True if collection exists/created, False on error
        """
        client = self._get_client()
        if not client:
            return False

        try:
            collections = client.get_collections()
            existing = [c.name for c in collections.collections]

            if self.collection_name in existing:
                return True

            # Create collection with hybrid vectors if enabled
            if self.use_hybrid:
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        "dense": models.VectorParams(
                            size=VECTOR_SIZE,
                            distance=models.Distance.COSINE,
                        ),
                    },
                    sparse_vectors_config={
                        "sparse": models.SparseVectorParams(
                            modifier=models.Modifier.IDF,
                        ),
                    },
                )
            else:
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=VECTOR_SIZE,
                        distance=models.Distance.COSINE,
                    ),
                )

            # Create payload indexes for filtering
            client.create_payload_index(
                collection_name=self.collection_name,
                field_name="auteur_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            client.create_payload_index(
                collection_name=self.collection_name,
                field_name="created_at",
                field_schema=models.PayloadSchemaType.DATETIME,
            )

            logger.info(f"[VPEStorage] Created collection: {self.collection_name}")
            return True

        except Exception as e:
            logger.error(f"[VPEStorage] Failed to ensure collection: {e}")
            return False

    async def store_logic_vector(
        self,
        logic_vector: LogicVector,
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Store a Logic Vector in Qdrant.

        Args:
            logic_vector: LogicVector to store
            doc_id: Optional document ID (generated if not provided)
            metadata: Optional additional metadata

        Returns:
            Document ID if stored, None on error
        """
        if not await self.ensure_collection():
            return None

        client = self._get_client()
        if not client:
            return None

        try:
            # Generate doc_id if not provided
            if not doc_id:
                content_hash = hashlib.sha256(
                    logic_vector.model_dump_json().encode()
                ).hexdigest()[:16]
                doc_id = f"vpe_{logic_vector.auteur_id}_{content_hash}"

            # Create text representation for embedding
            text_repr = self._logic_vector_to_text(logic_vector)

            # Generate dense embedding
            embedder = self._get_embedder()
            dense_vector = await embedder.embed_async(text_repr)

            # Build payload
            payload = {
                "auteur_id": logic_vector.auteur_id,
                "logic_vector": logic_vector.model_dump(),
                "text_representation": text_repr,
                "created_at": datetime.utcnow().isoformat(),
                "source_video": logic_vector.source_video,
                "confidence": logic_vector.confidence,
            }
            if metadata:
                payload["metadata"] = metadata

            # Create point with hybrid vectors if enabled
            if self.use_hybrid:
                sparse_embedder = _get_sparse_embedder()
                if sparse_embedder:
                    sparse_result = sparse_embedder.encode([text_repr])[0]
                    sparse_vector = models.SparseVector(
                        indices=sparse_result.indices.tolist(),
                        values=sparse_result.values.tolist(),
                    )

                    point = models.PointStruct(
                        id=doc_id,
                        vector={
                            "dense": dense_vector,
                            "sparse": sparse_vector,
                        },
                        payload=payload,
                    )
                else:
                    # Fallback to dense only
                    point = models.PointStruct(
                        id=doc_id,
                        vector={"dense": dense_vector},
                        payload=payload,
                    )
            else:
                point = models.PointStruct(
                    id=doc_id,
                    vector=dense_vector,
                    payload=payload,
                )

            # Upsert to Qdrant
            client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )

            logger.info(f"[VPEStorage] Stored Logic Vector: {doc_id}")
            return doc_id

        except CircuitBreakerOpen:
            logger.warning("[VPEStorage] Circuit breaker open, skipping store")
            return None
        except Exception as e:
            logger.error(f"[VPEStorage] Failed to store Logic Vector: {e}")
            return None

    async def search_by_style(
        self,
        query: str,
        auteur_filter: Optional[str] = None,
        top_k: int = 5,
    ) -> List[VPEQueryResult]:
        """Search for similar Logic Vectors by style description.

        Args:
            query: Natural language query describing desired style
            auteur_filter: Optional auteur ID to filter by
            top_k: Number of results to return

        Returns:
            List of VPEQueryResult with matched Logic Vectors
        """
        if not await self.ensure_collection():
            return []

        client = self._get_client()
        if not client:
            return []

        try:
            # Generate query embedding
            embedder = self._get_embedder()
            query_vector = await embedder.embed_async(query)

            # Build filter if auteur specified
            query_filter = None
            if auteur_filter:
                query_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="auteur_id",
                            match=models.MatchValue(value=auteur_filter),
                        ),
                    ],
                )

            # Search
            if self.use_hybrid:
                # Hybrid search with RRF
                sparse_embedder = _get_sparse_embedder()
                if sparse_embedder:
                    sparse_result = sparse_embedder.encode([query])[0]
                    sparse_vector = models.SparseVector(
                        indices=sparse_result.indices.tolist(),
                        values=sparse_result.values.tolist(),
                    )

                    results = client.query_points(
                        collection_name=self.collection_name,
                        prefetch=[
                            models.Prefetch(
                                query=query_vector,
                                using="dense",
                                limit=top_k * 2,
                            ),
                            models.Prefetch(
                                query=sparse_vector,
                                using="sparse",
                                limit=top_k * 2,
                            ),
                        ],
                        query=models.FusionQuery(fusion=models.Fusion.RRF),
                        filter=query_filter,
                        limit=top_k,
                        with_payload=True,
                    )
                else:
                    # Dense only fallback
                    results = client.search(
                        collection_name=self.collection_name,
                        query_vector=("dense", query_vector),
                        query_filter=query_filter,
                        limit=top_k,
                        with_payload=True,
                    )
            else:
                # Dense only
                results = client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=top_k,
                    with_payload=True,
                )

            # Parse results
            query_results = []
            points = getattr(results, 'points', results)

            for point in points:
                try:
                    payload = point.payload
                    lv_data = payload.get("logic_vector", {})

                    logic_vector = LogicVector(**lv_data)
                    score = point.score if hasattr(point, 'score') else 0.0

                    query_results.append(VPEQueryResult(
                        logic_vector=logic_vector,
                        score=min(1.0, max(0.0, score)),
                        doc_id=str(point.id),
                    ))
                except Exception as e:
                    logger.warning(f"[VPEStorage] Failed to parse result: {e}")

            return query_results

        except CircuitBreakerOpen:
            logger.warning("[VPEStorage] Circuit breaker open, skipping search")
            return []
        except Exception as e:
            logger.error(f"[VPEStorage] Failed to search: {e}")
            return []

    async def get_by_auteur(
        self,
        auteur_id: str,
        limit: int = 10,
    ) -> List[VPEQueryResult]:
        """Get all Logic Vectors for a specific auteur.

        Args:
            auteur_id: Auteur ID to filter by
            limit: Maximum results to return

        Returns:
            List of VPEQueryResult
        """
        if not await self.ensure_collection():
            return []

        client = self._get_client()
        if not client:
            return []

        try:
            results = client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="auteur_id",
                            match=models.MatchValue(value=auteur_id),
                        ),
                    ],
                ),
                limit=limit,
                with_payload=True,
            )

            query_results = []
            points, _ = results

            for point in points:
                try:
                    payload = point.payload
                    lv_data = payload.get("logic_vector", {})
                    logic_vector = LogicVector(**lv_data)

                    query_results.append(VPEQueryResult(
                        logic_vector=logic_vector,
                        score=1.0,  # No ranking for scroll
                        doc_id=str(point.id),
                    ))
                except Exception as e:
                    logger.warning(f"[VPEStorage] Failed to parse result: {e}")

            return query_results

        except Exception as e:
            logger.error(f"[VPEStorage] Failed to get by auteur: {e}")
            return []

    async def delete_logic_vector(self, doc_id: str) -> bool:
        """Delete a Logic Vector by ID.

        Args:
            doc_id: Document ID to delete

        Returns:
            True if deleted, False on error
        """
        client = self._get_client()
        if not client:
            return False

        try:
            client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[doc_id],
                ),
            )
            logger.info(f"[VPEStorage] Deleted Logic Vector: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"[VPEStorage] Failed to delete: {e}")
            return False

    def _logic_vector_to_text(self, lv: LogicVector) -> str:
        """Convert Logic Vector to text for embedding.

        Creates a rich text representation of the Logic Vector
        suitable for semantic search.
        """
        parts = [
            f"Director style: {lv.auteur_id}",
        ]

        # Cadence
        if lv.cadence.rhythm_pattern:
            parts.append(f"Rhythm pattern: {lv.cadence.rhythm_pattern}")
        if lv.cadence.tempo:
            parts.append(f"Tempo: {lv.cadence.tempo}")

        # Composition
        parts.append(f"Composition strategy: {lv.composition.primary_strategy}")
        parts.append(f"Symmetry: {'high' if lv.composition.symmetry_score > 0.7 else 'low' if lv.composition.symmetry_score < 0.3 else 'balanced'}")

        # Camera movements
        camera_parts = []
        grammar = lv.camera_grammar.model_dump()
        for k, v in sorted(grammar.items(), key=lambda x: -x[1]):
            if v >= 0.1:
                camera_parts.append(k)
        if camera_parts:
            parts.append(f"Camera movements: {', '.join(camera_parts[:4])}")

        # Lighting
        parts.append(f"Lighting: {lv.lighting_physics.key_light}")
        if lv.lighting_physics.shadow_quality:
            parts.append(f"Shadows: {lv.lighting_physics.shadow_quality}")

        # Color
        if lv.color_science.lut_reference:
            parts.append(f"Color grade: {lv.color_science.lut_reference}")
        if lv.color_science.palette:
            parts.append(f"Palette: {', '.join(lv.color_science.palette[:3])}")
        if lv.color_science.saturation_level:
            parts.append(f"Saturation: {lv.color_science.saturation_level}")

        return ". ".join(parts)


# =============================================================================
# Module-level convenience functions
# =============================================================================

_default_storage: Optional[VPEStorage] = None


def get_vpe_storage(use_hybrid: bool = True) -> VPEStorage:
    """Get or create the default VPE storage instance.

    Args:
        use_hybrid: Whether to use hybrid embeddings

    Returns:
        VPEStorage instance
    """
    global _default_storage
    if _default_storage is None:
        _default_storage = VPEStorage(use_hybrid=use_hybrid)
    return _default_storage


async def store_logic_vector(
    logic_vector: LogicVector,
    doc_id: Optional[str] = None,
) -> Optional[str]:
    """Convenience function to store a Logic Vector.

    Args:
        logic_vector: LogicVector to store
        doc_id: Optional document ID

    Returns:
        Document ID if stored
    """
    storage = get_vpe_storage()
    return await storage.store_logic_vector(logic_vector, doc_id)


async def search_logic_vectors(
    query: str,
    auteur_filter: Optional[str] = None,
    top_k: int = 5,
) -> List[VPEQueryResult]:
    """Convenience function to search Logic Vectors.

    Args:
        query: Search query
        auteur_filter: Optional auteur filter
        top_k: Number of results

    Returns:
        List of VPEQueryResult
    """
    storage = get_vpe_storage()
    return await storage.search_by_style(query, auteur_filter, top_k)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "VPEStorage",
    "VPE_COLLECTION_NAME",
    "VPE_COLLECTION_HYBRID",
    "get_vpe_storage",
    "store_logic_vector",
    "search_logic_vectors",
]
