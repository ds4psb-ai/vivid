#!/usr/bin/env python3
"""Migrate Dense-only collections to Hybrid (Dense + Sparse) collections.

P0.5: Collection Migration Script with IDF Modifier.

This script:
1. Creates new collections with Dense + Sparse named vectors
2. Migrates existing documents with sparse embeddings
3. Applies Modifier.IDF for server-side BM25 scoring

Usage:
    # Migrate specific dimensions
    python scripts/migrate_to_hybrid_collection.py --dimensions AI AD 4D

    # Migrate all dimensions
    python scripts/migrate_to_hybrid_collection.py --all

    # Dry run (preview only)
    python scripts/migrate_to_hybrid_collection.py --dimensions AI --dry-run

Requirements:
    pip install fastembed
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings
from app.rag.tier1_dimension_rag import DIMENSION_COLLECTIONS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class HybridCollectionMigrator:
    """Migrate Dense-only collections to Dense + Sparse hybrid collections."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.client: Optional[QdrantClient] = None
        self._sparse_embedder = None

    @property
    def sparse_embedder(self):
        """Lazy-load sparse embedder."""
        if self._sparse_embedder is None:
            try:
                from app.rag.sparse import SparseEmbedder
                self._sparse_embedder = SparseEmbedder()
                logger.info("Loaded SparseEmbedder")
            except ImportError as e:
                logger.error(f"Failed to load SparseEmbedder: {e}")
                logger.error("Install fastembed: pip install fastembed")
                raise
        return self._sparse_embedder

    def connect(self) -> bool:
        """Connect to Qdrant."""
        try:
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                timeout=30,
            )
            self.client.get_collections()
            logger.info(f"Connected to Qdrant at {settings.QDRANT_URL}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            return False

    def collection_exists(self, name: str) -> bool:
        """Check if collection exists."""
        if self.client is None:
            return False
        try:
            collections = self.client.get_collections()
            return any(c.name == name for c in collections.collections)
        except Exception:
            return False

    def collection_has_sparse(self, name: str) -> bool:
        """Check if collection already has sparse vectors configured."""
        if self.client is None:
            return False
        try:
            info = self.client.get_collection(name)
            # Check if sparse_vectors_config exists
            return info.config.params.sparse_vectors is not None
        except Exception:
            return False

    def create_hybrid_collection(
        self,
        dimension: str,
        config: dict,
    ) -> bool:
        """Create new hybrid collection with Dense + Sparse vectors.

        Args:
            dimension: Dimension ID (AI, AD, 4D, etc.)
            config: Collection config from DIMENSION_COLLECTIONS

        Returns:
            True if created successfully
        """
        if self.client is None:
            return False

        new_name = f"{config['name']}_hybrid"
        vector_size = config.get("vector_size", 384)

        if self.collection_exists(new_name):
            logger.warning(f"[{dimension}] Collection {new_name} already exists, skipping creation")
            return True

        logger.info(f"[{dimension}] Creating hybrid collection: {new_name}")

        if self.dry_run:
            logger.info(f"[DRY RUN] Would create collection {new_name}")
            return True

        try:
            self.client.create_collection(
                collection_name=new_name,
                vectors_config={
                    "dense": models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE,
                    ),
                },
                # CRITICAL: IDF Modifier for BM25 scoring
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(
                        modifier=models.Modifier.IDF,
                    ),
                },
            )
            logger.info(f"[{dimension}] Created hybrid collection with IDF modifier")
            return True
        except Exception as e:
            logger.error(f"[{dimension}] Failed to create collection: {e}")
            return False

    def migrate_dimension(
        self,
        dimension: str,
        batch_size: int = 100,
    ) -> int:
        """Migrate all documents from old collection to new hybrid collection.

        Args:
            dimension: Dimension ID
            batch_size: Number of documents per batch

        Returns:
            Number of migrated documents
        """
        if self.client is None:
            return 0

        config = DIMENSION_COLLECTIONS.get(dimension)
        if not config:
            logger.error(f"Unknown dimension: {dimension}")
            return 0

        old_name = config["name"]
        new_name = f"{old_name}_hybrid"

        if not self.collection_exists(old_name):
            logger.warning(f"[{dimension}] Source collection {old_name} does not exist")
            return 0

        # Create new collection if needed
        if not self.create_hybrid_collection(dimension, config):
            return 0

        logger.info(f"[{dimension}] Migrating {old_name} -> {new_name}")

        if self.dry_run:
            try:
                info = self.client.get_collection(old_name)
                count = info.points_count or 0
                logger.info(f"[DRY RUN] Would migrate {count} documents")
                return count
            except Exception:
                return 0

        # Scroll through old collection and migrate
        offset = None
        total = 0

        try:
            while True:
                points, offset = self.client.scroll(
                    collection_name=old_name,
                    limit=batch_size,
                    offset=offset,
                    with_vectors=True,
                    with_payload=True,
                )

                if not points:
                    break

                # Generate sparse embeddings and create new points
                new_points = []
                for point in points:
                    text = ""
                    if point.payload:
                        text = point.payload.get("content", "")

                    # Generate sparse embedding
                    sparse_indices, sparse_values = self.sparse_embedder.embed(text)

                    # Handle vector format (could be dict or list)
                    dense_vector = point.vector
                    if isinstance(dense_vector, dict):
                        # Already named vectors
                        dense_vector = dense_vector.get("dense", dense_vector.get("", []))

                    new_points.append(
                        models.PointStruct(
                            id=point.id,
                            vector={
                                "dense": dense_vector,
                                "sparse": models.SparseVector(
                                    indices=sparse_indices,
                                    values=sparse_values,
                                ),
                            },
                            payload=point.payload,
                        )
                    )

                # Upsert batch
                self.client.upsert(
                    collection_name=new_name,
                    points=new_points,
                )

                total += len(new_points)
                logger.info(f"[{dimension}] Migrated {total} documents...")

                if offset is None:
                    break

        except Exception as e:
            logger.error(f"[{dimension}] Migration failed: {e}")
            return total

        logger.info(f"[{dimension}] Migration complete: {total} documents")
        return total

    def verify_collection(self, dimension: str) -> dict:
        """Verify hybrid collection configuration.

        Args:
            dimension: Dimension ID

        Returns:
            Verification results
        """
        if self.client is None:
            return {"success": False, "error": "Not connected"}

        config = DIMENSION_COLLECTIONS.get(dimension)
        if not config:
            return {"success": False, "error": f"Unknown dimension: {dimension}"}

        new_name = f"{config['name']}_hybrid"

        try:
            info = self.client.get_collection(new_name)

            # Check sparse vectors config
            sparse_config = info.config.params.sparse_vectors
            has_idf = False
            if sparse_config and "sparse" in sparse_config:
                modifier = sparse_config["sparse"].modifier
                has_idf = modifier == models.Modifier.IDF

            return {
                "success": True,
                "collection": new_name,
                "points_count": info.points_count,
                "has_dense": "dense" in (info.config.params.vectors or {}),
                "has_sparse": sparse_config is not None,
                "has_idf_modifier": has_idf,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Migrate Qdrant collections to hybrid (Dense + Sparse)"
    )
    parser.add_argument(
        "--dimensions",
        nargs="+",
        help="Dimensions to migrate (e.g., AI AD 4D)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Migrate all dimensions",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Documents per batch (default: 100)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing hybrid collections",
    )

    args = parser.parse_args()

    if not args.dimensions and not args.all and not args.verify_only:
        parser.error("Specify --dimensions or --all")

    dimensions = list(DIMENSION_COLLECTIONS.keys()) if args.all else (args.dimensions or [])

    migrator = HybridCollectionMigrator(dry_run=args.dry_run)

    if not migrator.connect():
        logger.error("Failed to connect to Qdrant, exiting")
        sys.exit(1)

    if args.verify_only:
        logger.info("Verifying hybrid collections...")
        for dim in dimensions:
            result = migrator.verify_collection(dim)
            if result["success"]:
                logger.info(
                    f"[{dim}] {result['collection']}: "
                    f"points={result['points_count']}, "
                    f"dense={result['has_dense']}, "
                    f"sparse={result['has_sparse']}, "
                    f"idf={result['has_idf_modifier']}"
                )
            else:
                logger.warning(f"[{dim}] Verification failed: {result.get('error')}")
        return

    total_migrated = 0
    for dim in dimensions:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing dimension: {dim}")
        logger.info(f"{'='*60}")

        count = migrator.migrate_dimension(dim, batch_size=args.batch_size)
        total_migrated += count

        # Verify after migration
        result = migrator.verify_collection(dim)
        if result["success"]:
            logger.info(f"[{dim}] Verification: IDF modifier = {result['has_idf_modifier']}")
        else:
            logger.warning(f"[{dim}] Verification failed: {result.get('error')}")

    logger.info(f"\n{'='*60}")
    logger.info(f"Migration Summary: {total_migrated} total documents migrated")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
