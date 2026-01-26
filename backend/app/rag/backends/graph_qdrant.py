"""GraphRAG + Qdrant Hybrid Backend.

Phase 8: Combines GraphRAG entity/relationship search with Qdrant
vector similarity for multi-hop reasoning with semantic understanding.

Usage:
    from app.rag.backends import get_backend

    backend = get_backend("graph_qdrant")
    results = await backend.retrieve(
        query="강주노 롱테이크 기법",
        config={
            "graph_strategy": "hybrid",
            "graph_weight": 0.4,
            "auteur_keys": ["bong"],
        },
    )
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from app.rag.backends.base import BaseBackend, RetrievalResult

logger = logging.getLogger(__name__)


class GraphQdrantBackend(BaseBackend):
    """Hybrid backend combining GraphRAG with Qdrant vector search.

    This backend leverages:
    1. GraphRAG for entity-focused multi-hop reasoning
    2. Qdrant for semantic similarity search on text chunks

    The results are fused using RRF (Reciprocal Rank Fusion) to
    provide comprehensive retrieval.

    Config Options:
        graph_strategy: "local" | "global" | "hybrid" (default: "hybrid")
        graph_weight: Weight for graph results in fusion (default: 0.4)
        vector_weight: Weight for vector results in fusion (default: 0.6)
        auteur_keys: List of auteur keys to search
        dimension: Dimension filter for Qdrant
        max_hops: Maximum hops for local graph search (default: 2)
        community_level: Community level for global search (default: 1)
    """

    backend_id = "graph_qdrant"

    def __init__(self):
        self._qdrant_backend: Optional[BaseBackend] = None

    @property
    def qdrant_backend(self) -> BaseBackend:
        """Lazy-load Qdrant backend."""
        if self._qdrant_backend is None:
            from app.rag.backends import get_backend
            self._qdrant_backend = get_backend("qdrant_hybrid")
        return self._qdrant_backend

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """Retrieve using combined GraphRAG + Qdrant.

        Args:
            query: Search query
            limit: Maximum results to return
            filters: Metadata filters for Qdrant
            config: Backend-specific configuration
                - graph_strategy: "local" | "global" | "hybrid"
                - graph_weight: Weight for graph results (0-1)
                - vector_weight: Weight for vector results (0-1)
                - auteur_keys: List of auteur keys
                - dimension: Dimension code
                - max_hops: Max graph traversal hops
                - community_level: Community level for global search

        Returns:
            List of RetrievalResult objects
        """
        start_time = time.monotonic()
        config = config or {}

        # Extract config
        graph_strategy = config.get("graph_strategy", "hybrid")
        graph_weight = config.get("graph_weight", 0.4)
        vector_weight = config.get("vector_weight", 0.6)
        auteur_keys = config.get("auteur_keys")
        dimension = config.get("dimension")
        max_hops = config.get("max_hops", 2)
        community_level = config.get("community_level", 1)

        # Normalize weights
        total_weight = graph_weight + vector_weight
        graph_weight = graph_weight / total_weight
        vector_weight = vector_weight / total_weight

        # Run GraphRAG and Qdrant in parallel
        graph_task = self._graph_search(
            query=query,
            strategy=graph_strategy,
            auteur_keys=auteur_keys,
            limit=limit * 2,  # Over-fetch for fusion
            max_hops=max_hops,
            community_level=community_level,
        )

        qdrant_task = self._qdrant_search(
            query=query,
            limit=limit * 2,
            filters=filters,
            dimension=dimension,
        )

        graph_results, qdrant_results = await asyncio.gather(
            graph_task, qdrant_task, return_exceptions=True
        )

        # Handle errors
        if isinstance(graph_results, Exception):
            logger.warning(f"[GraphQdrant] Graph search failed: {graph_results}")
            graph_results = []
        if isinstance(qdrant_results, Exception):
            logger.warning(f"[GraphQdrant] Qdrant search failed: {qdrant_results}")
            qdrant_results = []

        # Fuse results using weighted RRF
        fused_results = self._weighted_rrf_fusion(
            [
                ("graph", graph_weight, graph_results),
                ("qdrant", vector_weight, qdrant_results),
            ],
            k=60,
            limit=limit,
        )

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            f"[GraphQdrant] Retrieved {len(fused_results)} results | "
            f"graph={len(graph_results)} | qdrant={len(qdrant_results)} | "
            f"strategy={graph_strategy} | time={elapsed_ms}ms"
        )

        return fused_results

    async def health_check(self) -> bool:
        """Check if both backends are healthy."""
        try:
            # Check Qdrant
            if self.qdrant_backend:
                qdrant_health = await self.qdrant_backend.health_check()
                if not qdrant_health:
                    return False

            # GraphRAG doesn't have a specific health check
            # Just verify module imports work
            from app.rag.graph_rag_search import GraphRAGSearcher
            _ = GraphRAGSearcher()

            return True
        except Exception as e:
            logger.error(f"[GraphQdrant] Health check failed: {e}")
            return False

    async def _graph_search(
        self,
        query: str,
        strategy: str,
        auteur_keys: Optional[List[str]],
        limit: int,
        max_hops: int,
        community_level: int,
    ) -> List[RetrievalResult]:
        """Execute GraphRAG search."""
        try:
            from app.rag.graph_rag_search import (
                GraphRAGSearcher,
                SearchStrategy,
                LocalSearchConfig,
                GlobalSearchConfig,
            )

            # Configure searcher
            local_config = LocalSearchConfig(max_entities=limit, max_hops=max_hops)
            global_config = GlobalSearchConfig(
                community_level=community_level,
                max_communities=limit,
            )

            searcher = GraphRAGSearcher(
                local_config=local_config,
                global_config=global_config,
            )

            # Execute search based on strategy
            if strategy == "local":
                result = await searcher.local_search(query, auteur_keys)
            elif strategy == "global":
                result = await searcher.global_search(query, auteur_keys)
            else:  # hybrid
                result = await searcher.hybrid_search(query, auteur_keys)

            # Convert to RetrievalResult
            retrieval_results: List[RetrievalResult] = []

            # Add entities as results
            for i, entity in enumerate(result.entities):
                text = f"{entity['name']} ({entity['type']})"
                if entity.get('properties'):
                    props_summary = str(entity['properties'])[:200]
                    text += f": {props_summary}"

                retrieval_results.append(RetrievalResult(
                    doc_id=f"graph_entity:{entity['id']}",
                    text=text,
                    score=result.confidence * (1.0 - i * 0.05),  # Decay by rank
                    source="graph_qdrant",
                    rank=i + 1,
                    metadata={
                        "type": "entity",
                        "entity_type": entity.get("type"),
                        "entity_id": entity.get("id"),
                        "graph_strategy": strategy,
                    },
                ))

            # Add community reports as results
            for i, report in enumerate(result.community_reports):
                retrieval_results.append(RetrievalResult(
                    doc_id=f"graph_community:{report['community_id']}",
                    text=f"{report['title']}: {report.get('summary', '')[:500]}",
                    score=report.get('rank', 0.5) * result.confidence,
                    source="graph_qdrant",
                    rank=len(result.entities) + i + 1,
                    metadata={
                        "type": "community",
                        "community_id": report.get("community_id"),
                        "level": report.get("level"),
                        "key_findings": report.get("key_findings", []),
                        "graph_strategy": strategy,
                    },
                ))

            return retrieval_results

        except Exception as e:
            logger.error(f"[GraphQdrant] Graph search error: {e}")
            return []

    async def _qdrant_search(
        self,
        query: str,
        limit: int,
        filters: Optional[Dict[str, Any]],
        dimension: Optional[str],
    ) -> List[RetrievalResult]:
        """Execute Qdrant vector search."""
        try:
            if not self.qdrant_backend:
                return []

            qdrant_config = {"dimension": dimension} if dimension else {}
            results = await self.qdrant_backend.retrieve(
                query=query,
                limit=limit,
                filters=filters,
                config=qdrant_config,
            )

            return results

        except Exception as e:
            logger.error(f"[GraphQdrant] Qdrant search error: {e}")
            return []

    def _weighted_rrf_fusion(
        self,
        backend_results: List[tuple],
        k: int = 60,
        limit: int = 10,
    ) -> List[RetrievalResult]:
        """Weighted Reciprocal Rank Fusion.

        Args:
            backend_results: List of (backend_id, weight, results)
            k: RRF constant (default 60)
            limit: Max results to return

        Returns:
            Fused and sorted RetrievalResult list
        """
        doc_scores: Dict[str, Dict[str, Any]] = {}

        for backend_id, weight, results in backend_results:
            for rank, result in enumerate(results, start=1):
                doc_id = result.doc_id
                rrf_score = weight / (k + rank)

                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {
                        "rrf_score": 0.0,
                        "best_result": result,
                        "sources": [],
                        "max_original_score": result.score,
                    }

                doc_scores[doc_id]["rrf_score"] += rrf_score
                doc_scores[doc_id]["sources"].append(backend_id)

                # Keep best scoring result
                if result.score > doc_scores[doc_id]["max_original_score"]:
                    doc_scores[doc_id]["best_result"] = result
                    doc_scores[doc_id]["max_original_score"] = result.score

        # Sort by RRF score
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1]["rrf_score"],
            reverse=True,
        )

        # Build final results
        fused_results: List[RetrievalResult] = []
        for i, (doc_id, data) in enumerate(sorted_docs[:limit], start=1):
            best = data["best_result"]
            fused_results.append(RetrievalResult(
                doc_id=best.doc_id,
                text=best.text,
                score=data["rrf_score"],
                source="graph_qdrant",
                rank=i,
                metadata={
                    **best.metadata,
                    "rrf_score": data["rrf_score"],
                    "fusion_sources": data["sources"],
                    "original_score": data["max_original_score"],
                },
            ))

        return fused_results


# =============================================================================
# Exports
# =============================================================================

__all__ = ["GraphQdrantBackend"]
