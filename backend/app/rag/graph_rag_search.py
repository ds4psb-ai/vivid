"""GraphRAG Search Module.

Phase 8: Microsoft GraphRAG search strategies - Local (entity-focused)
and Global (community-based) search for multi-hop queries.

Based on: Microsoft GraphRAG achieving 87% multi-hop accuracy.

Usage:
    from app.rag.graph_rag_search import (
        GraphRAGSearcher,
        SearchStrategy,
        GraphSearchResult,
    )

    searcher = GraphRAGSearcher()

    # Local search (entity-focused, 2-hop traversal)
    result = await searcher.local_search("강주노 롱테이크", auteur_keys=["bong"])

    # Global search (community-based map-reduce)
    result = await searcher.global_search("영화 감독들의 공통 기법", community_level=1)

    # Hybrid search (combines both)
    result = await searcher.hybrid_search("렉스 볼티지와 강주노의 대화 스타일")
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from app.rag.graph_rag import (
    AuteurGraph,
    Entity,
    Relationship,
    build_auteur_graph,
    get_cached_graph,
)
from app.rag.graph_rag_community import (
    Community,
    CommunityReport,
    CommunityDetector,
)
from app.rag.observability import trace_rag

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================

class SearchStrategy(str, Enum):
    """GraphRAG search strategies."""
    LOCAL = "local"    # Entity-focused + text chunks (2-hop traversal)
    GLOBAL = "global"  # Community reports map-reduce
    HYBRID = "hybrid"  # Combined local + global


@dataclass
class GraphSearchResult:
    """Result from GraphRAG search."""
    answer: str
    entities: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Tuple[str, str, str]] = field(default_factory=list)
    community_reports: List[Dict[str, Any]] = field(default_factory=list)
    paths: List[List[str]] = field(default_factory=list)  # Traversal paths
    strategy_used: str = "unknown"
    query_time_ms: int = 0
    confidence: float = 0.0
    # Metadata
    auteur_keys: List[str] = field(default_factory=list)
    entity_count: int = 0
    relationship_count: int = 0
    hop_depth: int = 0


@dataclass
class LocalSearchConfig:
    """Configuration for local search."""
    max_entities: int = 10
    max_hops: int = 2
    include_text_chunks: bool = True
    entity_score_threshold: float = 0.1


@dataclass
class GlobalSearchConfig:
    """Configuration for global search."""
    community_level: int = 1
    max_communities: int = 5
    map_reduce_enabled: bool = True
    summary_max_tokens: int = 500


# =============================================================================
# Community Cache
# =============================================================================

_community_cache: Dict[str, Tuple[Dict[int, List[Community]], List[CommunityReport]]] = {}


async def get_communities_for_auteur(
    auteur_key: str,
    max_levels: int = 3,
) -> Tuple[Dict[int, List[Community]], List[CommunityReport]]:
    """Get cached communities and reports for an auteur."""
    if auteur_key in _community_cache:
        return _community_cache[auteur_key]

    graph = await build_auteur_graph(auteur_key)
    if not graph.entities:
        return {}, []

    detector = CommunityDetector()
    communities = await detector.detect_communities(graph, max_levels=max_levels)
    reports = await detector.generate_community_reports(communities, graph)

    _community_cache[auteur_key] = (communities, reports)
    return communities, reports


def clear_community_cache(auteur_key: Optional[str] = None) -> None:
    """Clear community cache."""
    global _community_cache
    if auteur_key:
        _community_cache.pop(auteur_key, None)
    else:
        _community_cache.clear()


# =============================================================================
# GraphRAG Searcher
# =============================================================================

class GraphRAGSearcher:
    """GraphRAG searcher with local/global strategies.

    Implements Microsoft GraphRAG search patterns:
    - Local: Entity-focused search with 2-hop traversal
    - Global: Community-based map-reduce search
    - Hybrid: Combined approach for comprehensive results

    Attributes:
        local_config: Configuration for local search
        global_config: Configuration for global search
    """

    def __init__(
        self,
        local_config: Optional[LocalSearchConfig] = None,
        global_config: Optional[GlobalSearchConfig] = None,
    ):
        self.local_config = local_config or LocalSearchConfig()
        self.global_config = global_config or GlobalSearchConfig()
        self._keyword_cache: Dict[str, Set[str]] = {}

    @trace_rag(name="graphrag_local_search", tags=["graphrag", "local"])
    async def local_search(
        self,
        query: str,
        auteur_keys: Optional[List[str]] = None,
        max_entities: Optional[int] = None,
        max_hops: Optional[int] = None,
    ) -> GraphSearchResult:
        """Entity-focused search with N-hop traversal.

        Local search is optimized for queries about specific entities,
        techniques, or relationships between known concepts.

        Algorithm:
        1. Extract entities from query (keyword matching + embedding similarity)
        2. Traverse N hops from matched entities
        3. Collect related entities and relationships
        4. Score and rank results

        Args:
            query: Natural language query
            auteur_keys: List of auteur keys to search (None = all)
            max_entities: Override max entities to return
            max_hops: Override hop depth

        Returns:
            GraphSearchResult with matched entities and relationships
        """
        start_time = time.monotonic()

        max_entities = max_entities or self.local_config.max_entities
        max_hops = max_hops or self.local_config.max_hops

        # Build/get graphs for requested auteurs
        graphs = await self._get_graphs(auteur_keys)
        if not graphs:
            return GraphSearchResult(
                answer="No graph data available.",
                strategy_used="local",
                query_time_ms=int((time.monotonic() - start_time) * 1000),
            )

        # Step 1: Entity extraction from query
        matched_entities: List[Tuple[Entity, float]] = []  # (entity, score)
        for graph in graphs:
            matches = await self._extract_entities_from_query(query, graph)
            matched_entities.extend(matches)

        if not matched_entities:
            return GraphSearchResult(
                answer=f"No entities found matching query: {query}",
                strategy_used="local",
                auteur_keys=auteur_keys or [],
                query_time_ms=int((time.monotonic() - start_time) * 1000),
            )

        # Sort by score and deduplicate
        matched_entities.sort(key=lambda x: x[1], reverse=True)
        seen_ids: Set[str] = set()
        unique_matches: List[Tuple[Entity, float]] = []
        for entity, score in matched_entities:
            if entity.id not in seen_ids:
                seen_ids.add(entity.id)
                unique_matches.append((entity, score))

        # Step 2: N-hop traversal
        all_entities: Dict[str, Entity] = {}
        all_relationships: List[Tuple[str, str, str]] = []
        traversal_paths: List[List[str]] = []

        for entity, _ in unique_matches[:max_entities]:
            for graph in graphs:
                if entity.id in graph.entities:
                    entities, relationships, paths = self._traverse_hops(
                        graph, entity.id, max_hops
                    )
                    all_entities.update(entities)
                    all_relationships.extend(relationships)
                    traversal_paths.extend(paths)

        # Deduplicate relationships
        unique_relationships = list(set(all_relationships))

        # Step 3: Build answer
        answer = self._build_local_answer(
            query, list(all_entities.values()), unique_relationships
        )

        # Calculate confidence based on match quality
        confidence = self._calculate_local_confidence(
            unique_matches, len(all_entities), len(unique_relationships)
        )

        return GraphSearchResult(
            answer=answer,
            entities=[
                {"id": e.id, "type": e.type, "name": e.name, "properties": e.properties}
                for e in list(all_entities.values())[:max_entities]
            ],
            relationships=unique_relationships[:max_entities * 2],
            paths=traversal_paths[:10],
            strategy_used="local",
            query_time_ms=int((time.monotonic() - start_time) * 1000),
            confidence=confidence,
            auteur_keys=auteur_keys or [],
            entity_count=len(all_entities),
            relationship_count=len(unique_relationships),
            hop_depth=max_hops,
        )

    @trace_rag(name="graphrag_global_search", tags=["graphrag", "global"])
    async def global_search(
        self,
        query: str,
        auteur_keys: Optional[List[str]] = None,
        community_level: Optional[int] = None,
        max_communities: Optional[int] = None,
    ) -> GraphSearchResult:
        """Community-based map-reduce search.

        Global search is optimized for high-level queries about themes,
        patterns, or comparisons across the knowledge graph.

        Algorithm:
        1. Retrieve relevant community reports at specified level
        2. Map: Score each community against query
        3. Reduce: Aggregate top community summaries into answer

        Args:
            query: Natural language query
            auteur_keys: List of auteur keys to search (None = all)
            community_level: Hierarchy level (0=leaf, higher=abstract)
            max_communities: Maximum communities to include

        Returns:
            GraphSearchResult with community-based answer
        """
        start_time = time.monotonic()

        community_level = community_level or self.global_config.community_level
        max_communities = max_communities or self.global_config.max_communities

        # Get communities for all requested auteurs
        all_reports: List[CommunityReport] = []
        effective_auteur_keys = auteur_keys or await self._get_available_auteurs()

        for auteur_key in effective_auteur_keys:
            _, reports = await get_communities_for_auteur(auteur_key)
            # Filter by level
            level_reports = [r for r in reports if r.level == community_level]
            all_reports.extend(level_reports)

        if not all_reports:
            # Try lower level if no reports at requested level
            for auteur_key in effective_auteur_keys:
                _, reports = await get_communities_for_auteur(auteur_key)
                level_0_reports = [r for r in reports if r.level == 0]
                all_reports.extend(level_0_reports)

        if not all_reports:
            return GraphSearchResult(
                answer="No community reports available.",
                strategy_used="global",
                auteur_keys=effective_auteur_keys,
                query_time_ms=int((time.monotonic() - start_time) * 1000),
            )

        # Step 1: Map - Score communities against query
        scored_reports = await self._score_communities(query, all_reports)

        # Step 2: Select top communities
        top_reports = scored_reports[:max_communities]

        # Step 3: Reduce - Aggregate into answer
        answer = self._build_global_answer(query, top_reports)

        # Calculate confidence
        confidence = self._calculate_global_confidence(top_reports)

        return GraphSearchResult(
            answer=answer,
            community_reports=[
                {
                    "community_id": r.community_id,
                    "title": r.title,
                    "level": r.level,
                    "summary": r.summary[:500],
                    "key_findings": r.key_findings,
                    "rank": r.rank,
                }
                for r, _ in top_reports
            ],
            strategy_used="global",
            query_time_ms=int((time.monotonic() - start_time) * 1000),
            confidence=confidence,
            auteur_keys=effective_auteur_keys,
        )

    @trace_rag(name="graphrag_hybrid_search", tags=["graphrag", "hybrid"])
    async def hybrid_search(
        self,
        query: str,
        auteur_keys: Optional[List[str]] = None,
        local_weight: float = 0.6,
        global_weight: float = 0.4,
    ) -> GraphSearchResult:
        """Combined local + global search.

        Hybrid search leverages both entity-focused and community-based
        approaches for comprehensive results.

        Args:
            query: Natural language query
            auteur_keys: List of auteur keys to search
            local_weight: Weight for local search results (0-1)
            global_weight: Weight for global search results (0-1)

        Returns:
            GraphSearchResult with combined results
        """
        start_time = time.monotonic()

        # Run local and global in parallel
        local_task = self.local_search(query, auteur_keys)
        global_task = self.global_search(query, auteur_keys)

        local_result, global_result = await asyncio.gather(local_task, global_task)

        # Combine results
        combined_answer = self._combine_answers(
            local_result.answer,
            global_result.answer,
            local_weight,
            global_weight,
        )

        # Calculate combined confidence
        combined_confidence = (
            local_result.confidence * local_weight +
            global_result.confidence * global_weight
        )

        return GraphSearchResult(
            answer=combined_answer,
            entities=local_result.entities,
            relationships=local_result.relationships,
            community_reports=global_result.community_reports,
            paths=local_result.paths,
            strategy_used="hybrid",
            query_time_ms=int((time.monotonic() - start_time) * 1000),
            confidence=combined_confidence,
            auteur_keys=auteur_keys or [],
            entity_count=local_result.entity_count,
            relationship_count=local_result.relationship_count,
            hop_depth=local_result.hop_depth,
        )

    # =========================================================================
    # Internal Methods
    # =========================================================================

    async def _get_graphs(
        self,
        auteur_keys: Optional[List[str]],
    ) -> List[AuteurGraph]:
        """Get graphs for specified auteurs."""
        effective_keys = auteur_keys or await self._get_available_auteurs()
        graphs: List[AuteurGraph] = []

        for key in effective_keys:
            graph = await build_auteur_graph(key)
            if graph.entities:
                graphs.append(graph)

        return graphs

    async def _get_available_auteurs(self) -> List[str]:
        """Get list of available auteur keys."""
        from app.rag.graph_rag import get_all_auteurs
        return await get_all_auteurs()

    async def _extract_entities_from_query(
        self,
        query: str,
        graph: AuteurGraph,
    ) -> List[Tuple[Entity, float]]:
        """Extract entities from query using keyword matching and similarity.

        Returns list of (entity, score) tuples.
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        matches: List[Tuple[Entity, float]] = []

        for entity in graph.entities.values():
            score = 0.0
            entity_name_lower = entity.name.lower()
            entity_words = set(entity_name_lower.split())

            # Exact name match
            if entity_name_lower in query_lower:
                score += 1.0

            # Word overlap
            overlap = len(query_words & entity_words)
            if overlap > 0:
                score += overlap * 0.3

            # Partial match
            for word in query_words:
                if len(word) > 2 and word in entity_name_lower:
                    score += 0.2

            # Check properties for matches
            props_str = str(entity.properties).lower()
            for word in query_words:
                if len(word) > 3 and word in props_str:
                    score += 0.1

            if score >= self.local_config.entity_score_threshold:
                matches.append((entity, score))

        return matches

    def _traverse_hops(
        self,
        graph: AuteurGraph,
        start_entity_id: str,
        max_hops: int,
    ) -> Tuple[Dict[str, Entity], List[Tuple[str, str, str]], List[List[str]]]:
        """Traverse N hops from start entity.

        Returns:
            Tuple of (entities dict, relationships list, paths list)
        """
        entities: Dict[str, Entity] = {}
        relationships: List[Tuple[str, str, str]] = []
        paths: List[List[str]] = []

        visited: Set[str] = set()
        queue: List[Tuple[str, int, List[str]]] = [(start_entity_id, 0, [start_entity_id])]

        while queue:
            current_id, hop, path = queue.pop(0)

            if current_id in visited:
                continue
            visited.add(current_id)

            # Add entity
            if current_id in graph.entities:
                entities[current_id] = graph.entities[current_id]

            # Save path
            if hop > 0:
                paths.append(path)

            # Stop if max hops reached
            if hop >= max_hops:
                continue

            # Get neighbors
            for rel in graph.relationships:
                neighbor_id = None
                if rel.source_id == current_id:
                    neighbor_id = rel.target_id
                    relationships.append((
                        graph.entities[rel.source_id].name if rel.source_id in graph.entities else rel.source_id,
                        rel.type,
                        graph.entities[rel.target_id].name if rel.target_id in graph.entities else rel.target_id,
                    ))
                elif rel.target_id == current_id:
                    neighbor_id = rel.source_id
                    relationships.append((
                        graph.entities[rel.source_id].name if rel.source_id in graph.entities else rel.source_id,
                        rel.type,
                        graph.entities[rel.target_id].name if rel.target_id in graph.entities else rel.target_id,
                    ))

                if neighbor_id and neighbor_id not in visited:
                    queue.append((neighbor_id, hop + 1, path + [neighbor_id]))

        return entities, relationships, paths

    async def _score_communities(
        self,
        query: str,
        reports: List[CommunityReport],
    ) -> List[Tuple[CommunityReport, float]]:
        """Score communities against query.

        Uses keyword matching and embedding similarity (if available).
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        scored: List[Tuple[CommunityReport, float]] = []

        for report in reports:
            score = 0.0

            # Title match
            if any(word in report.title.lower() for word in query_words if len(word) > 2):
                score += 0.5

            # Summary match
            summary_lower = report.summary.lower()
            for word in query_words:
                if len(word) > 2 and word in summary_lower:
                    score += 0.2

            # Key findings match
            findings_text = " ".join(report.key_findings).lower()
            for word in query_words:
                if len(word) > 2 and word in findings_text:
                    score += 0.15

            # Embedding similarity (if available)
            if report.summary_embedding:
                # In production, compute cosine similarity with query embedding
                # For now, use rank as proxy
                score += report.rank * 0.3

            scored.append((report, score))

        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def _build_local_answer(
        self,
        query: str,
        entities: List[Entity],
        relationships: List[Tuple[str, str, str]],
    ) -> str:
        """Build answer from local search results."""
        if not entities:
            return f"No entities found for: {query}"

        # Build entity summary
        entity_summary = ", ".join(e.name for e in entities[:10])

        # Build relationship summary
        rel_summary = ""
        if relationships:
            unique_rels = list(set(relationships))[:5]
            rel_summary = "\n".join(f"  - {s} → [{r}] → {t}" for s, r, t in unique_rels)

        answer = f"""Found {len(entities)} related entities: {entity_summary}

Key Relationships:
{rel_summary if rel_summary else "  (No direct relationships found)"}"""

        return answer

    def _build_global_answer(
        self,
        query: str,
        scored_reports: List[Tuple[CommunityReport, float]],
    ) -> str:
        """Build answer from global search results."""
        if not scored_reports:
            return f"No community information found for: {query}"

        # Aggregate summaries
        summaries: List[str] = []
        for report, score in scored_reports:
            summary_excerpt = report.summary[:300] + "..." if len(report.summary) > 300 else report.summary
            summaries.append(f"**{report.title}** (Level {report.level}):\n{summary_excerpt}")

        combined = "\n\n".join(summaries)

        # Add key findings
        all_findings: List[str] = []
        for report, _ in scored_reports[:3]:
            all_findings.extend(report.key_findings[:2])

        findings_text = ""
        if all_findings:
            findings_text = "\n\nKey Findings:\n" + "\n".join(f"• {f}" for f in all_findings[:5])

        return f"""Community Analysis for: {query}

{combined}
{findings_text}"""

    def _combine_answers(
        self,
        local_answer: str,
        global_answer: str,
        local_weight: float,
        global_weight: float,
    ) -> str:
        """Combine local and global answers."""
        return f"""## Entity-Level Analysis (Local Search)

{local_answer}

---

## Thematic Analysis (Global Search)

{global_answer}"""

    def _calculate_local_confidence(
        self,
        matches: List[Tuple[Entity, float]],
        entity_count: int,
        relationship_count: int,
    ) -> float:
        """Calculate confidence for local search."""
        if not matches:
            return 0.0

        # Base confidence from match scores
        max_match_score = matches[0][1] if matches else 0
        base_confidence = min(max_match_score / 2.0, 0.5)

        # Bonus for more results
        coverage_bonus = min(entity_count / 20, 0.3)
        relationship_bonus = min(relationship_count / 30, 0.2)

        return min(base_confidence + coverage_bonus + relationship_bonus, 0.95)

    def _calculate_global_confidence(
        self,
        scored_reports: List[Tuple[CommunityReport, float]],
    ) -> float:
        """Calculate confidence for global search."""
        if not scored_reports:
            return 0.0

        # Average of top scores
        top_scores = [score for _, score in scored_reports[:3]]
        avg_score = sum(top_scores) / len(top_scores) if top_scores else 0

        # Normalize to 0-1 range
        return min(avg_score / 2.0, 0.95)


# =============================================================================
# Convenience Functions
# =============================================================================

async def graph_search(
    query: str,
    strategy: SearchStrategy = SearchStrategy.HYBRID,
    auteur_keys: Optional[List[str]] = None,
    **kwargs,
) -> GraphSearchResult:
    """Convenience function for GraphRAG search.

    Args:
        query: Natural language query
        strategy: Search strategy (local, global, hybrid)
        auteur_keys: Optional list of auteur keys
        **kwargs: Strategy-specific options

    Returns:
        GraphSearchResult
    """
    searcher = GraphRAGSearcher()

    if strategy == SearchStrategy.LOCAL:
        return await searcher.local_search(query, auteur_keys, **kwargs)
    elif strategy == SearchStrategy.GLOBAL:
        return await searcher.global_search(query, auteur_keys, **kwargs)
    else:
        return await searcher.hybrid_search(query, auteur_keys, **kwargs)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "SearchStrategy",
    "GraphSearchResult",
    "LocalSearchConfig",
    "GlobalSearchConfig",
    "GraphRAGSearcher",
    "graph_search",
    "get_communities_for_auteur",
    "clear_community_cache",
]
