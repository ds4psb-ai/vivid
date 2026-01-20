"""GraphRAG Community Detection Module.

Phase 8: Microsoft GraphRAG pattern - Louvain-based community detection
for hierarchical knowledge graph organization.

Based on: Microsoft GraphRAG (2024), achieving 87% multi-hop accuracy
vs 23% baseline RAG.

Usage:
    from app.rag.graph_rag_community import (
        CommunityDetector,
        Community,
        CommunityReport,
    )

    detector = CommunityDetector()
    communities = await detector.detect_communities(graph, max_levels=3)
    reports = await detector.generate_community_reports(communities, graph)
"""
from __future__ import annotations

import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from app.rag.graph_rag import AuteurGraph, Entity, Relationship

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Community:
    """Knowledge graph community."""
    id: str
    level: int  # 0=leaf, higher=abstract
    entity_ids: Set[str] = field(default_factory=set)
    title: str = ""
    summary: str = ""  # LLM-generated
    rank: float = 0.5  # Importance score (0-1)
    parent_id: Optional[str] = None  # Parent community at higher level
    child_ids: Set[str] = field(default_factory=set)  # Child communities

    @property
    def size(self) -> int:
        """Number of entities in community."""
        return len(self.entity_ids)

    def __hash__(self):
        return hash(self.id)


@dataclass
class CommunityReport:
    """Pre-computed community summary for global search."""
    community_id: str
    level: int
    title: str
    summary: str  # 200-500 tokens
    summary_embedding: Optional[List[float]] = None
    key_findings: List[str] = field(default_factory=list)
    rank: float = 0.5
    token_count: int = 0
    auteur_keys: List[str] = field(default_factory=list)


# =============================================================================
# Community Detection Algorithm
# =============================================================================

class CommunityDetector:
    """Louvain-based community detection for knowledge graphs.

    Implements a simplified Louvain algorithm adapted for
    knowledge graph structures with hierarchical community detection.

    Attributes:
        resolution: Modularity resolution parameter (higher = smaller communities)
        min_community_size: Minimum entities per community
    """

    def __init__(
        self,
        resolution: float = 1.0,
        min_community_size: int = 2,
    ):
        self.resolution = resolution
        self.min_community_size = min_community_size

    async def detect_communities(
        self,
        graph: AuteurGraph,
        max_levels: int = 3,
    ) -> Dict[int, List[Community]]:
        """Detect hierarchical communities in the graph.

        Args:
            graph: AuteurGraph to analyze
            max_levels: Maximum hierarchy levels (0=leaf, max-1=most abstract)

        Returns:
            Dict mapping level -> list of communities at that level
        """
        if not graph.entities:
            logger.warning("[CommunityDetector] Empty graph, no communities to detect")
            return {}

        # Build adjacency list from relationships
        adjacency = self._build_adjacency(graph)

        # Level 0: Initial partition using Louvain-like algorithm
        level_0_communities = self._louvain_partition(graph.entities, adjacency)

        communities_by_level: Dict[int, List[Community]] = {0: level_0_communities}

        # Higher levels: Aggregate smaller communities
        current_communities = level_0_communities
        for level in range(1, max_levels):
            if len(current_communities) <= 1:
                break  # Can't aggregate further

            aggregated = self._aggregate_communities(current_communities, level)
            if not aggregated or len(aggregated) == len(current_communities):
                break  # No further aggregation possible

            communities_by_level[level] = aggregated
            current_communities = aggregated

        # Log results
        total_communities = sum(len(c) for c in communities_by_level.values())
        logger.info(
            f"[CommunityDetector] Detected {total_communities} communities "
            f"across {len(communities_by_level)} levels for {graph.auteur_key}"
        )

        return communities_by_level

    def _build_adjacency(
        self,
        graph: AuteurGraph,
    ) -> Dict[str, Set[str]]:
        """Build adjacency list from relationships."""
        adjacency: Dict[str, Set[str]] = defaultdict(set)

        for rel in graph.relationships:
            adjacency[rel.source_id].add(rel.target_id)
            adjacency[rel.target_id].add(rel.source_id)

        return adjacency

    def _louvain_partition(
        self,
        entities: Dict[str, Entity],
        adjacency: Dict[str, Set[str]],
    ) -> List[Community]:
        """Simplified Louvain-style community detection.

        Uses greedy modularity optimization to partition entities.
        """
        # Initialize: each entity in its own community
        entity_to_community: Dict[str, str] = {}
        community_entities: Dict[str, Set[str]] = {}

        for entity_id in entities.keys():
            comm_id = f"comm_0_{entity_id[:8]}"
            entity_to_community[entity_id] = comm_id
            community_entities[comm_id] = {entity_id}

        # Greedy optimization: merge communities for better modularity
        changed = True
        max_iterations = 10
        iteration = 0

        while changed and iteration < max_iterations:
            changed = False
            iteration += 1

            for entity_id in entities.keys():
                current_comm = entity_to_community[entity_id]

                # Find best community to join (greedy)
                best_comm = current_comm
                best_gain = 0.0

                # Check neighbors' communities
                neighbor_comms: Set[str] = set()
                for neighbor_id in adjacency.get(entity_id, set()):
                    if neighbor_id in entity_to_community:
                        neighbor_comms.add(entity_to_community[neighbor_id])

                for target_comm in neighbor_comms:
                    if target_comm == current_comm:
                        continue

                    # Calculate modularity gain (simplified)
                    gain = self._modularity_gain(
                        entity_id,
                        current_comm,
                        target_comm,
                        entity_to_community,
                        community_entities,
                        adjacency,
                    )

                    if gain > best_gain:
                        best_gain = gain
                        best_comm = target_comm

                # Move to best community if gain > 0
                if best_comm != current_comm and best_gain > 0:
                    # Remove from current
                    community_entities[current_comm].discard(entity_id)
                    if not community_entities[current_comm]:
                        del community_entities[current_comm]

                    # Add to new
                    if best_comm not in community_entities:
                        community_entities[best_comm] = set()
                    community_entities[best_comm].add(entity_id)
                    entity_to_community[entity_id] = best_comm
                    changed = True

        # Filter small communities and merge into nearest
        final_communities = self._filter_small_communities(
            community_entities,
            adjacency,
        )

        # Create Community objects
        communities: List[Community] = []
        for comm_id, entity_ids in final_communities.items():
            # Generate title from entity types
            entity_types = set()
            for eid in entity_ids:
                if eid in entities:
                    entity_types.add(entities[eid].type)

            community = Community(
                id=comm_id,
                level=0,
                entity_ids=entity_ids,
                title=self._generate_community_title(entity_ids, entities),
                rank=len(entity_ids) / len(entities),  # Size-based rank
            )
            communities.append(community)

        logger.debug(
            f"[CommunityDetector] Level 0: {len(communities)} communities "
            f"after {iteration} iterations"
        )

        return communities

    def _modularity_gain(
        self,
        entity_id: str,
        current_comm: str,
        target_comm: str,
        entity_to_community: Dict[str, str],
        community_entities: Dict[str, Set[str]],
        adjacency: Dict[str, Set[str]],
    ) -> float:
        """Calculate modularity gain for moving entity to target community.

        Simplified modularity calculation based on internal vs external edges.
        """
        neighbors = adjacency.get(entity_id, set())

        # Count edges to current and target communities
        edges_to_current = sum(
            1 for n in neighbors
            if entity_to_community.get(n) == current_comm
        )
        edges_to_target = sum(
            1 for n in neighbors
            if entity_to_community.get(n) == target_comm
        )

        # Gain = edges gained - edges lost (simplified)
        gain = (edges_to_target - edges_to_current) * self.resolution

        return gain

    def _filter_small_communities(
        self,
        community_entities: Dict[str, Set[str]],
        adjacency: Dict[str, Set[str]],
    ) -> Dict[str, Set[str]]:
        """Merge small communities into nearest larger communities."""
        large_communities = {
            cid: entities
            for cid, entities in community_entities.items()
            if len(entities) >= self.min_community_size
        }

        small_communities = {
            cid: entities
            for cid, entities in community_entities.items()
            if len(entities) < self.min_community_size
        }

        # Merge small into nearest large
        for small_cid, small_entities in small_communities.items():
            best_target = None
            best_connection = 0

            for large_cid, large_entities in large_communities.items():
                # Count edges between small and large
                connection = 0
                for entity_id in small_entities:
                    for neighbor in adjacency.get(entity_id, set()):
                        if neighbor in large_entities:
                            connection += 1

                if connection > best_connection:
                    best_connection = connection
                    best_target = large_cid

            if best_target:
                large_communities[best_target].update(small_entities)
            elif large_communities:
                # No connection found, merge into largest
                largest_cid = max(large_communities.keys(), key=lambda c: len(large_communities[c]))
                large_communities[largest_cid].update(small_entities)
            else:
                # No large communities, keep small as-is
                large_communities[small_cid] = small_entities

        return large_communities

    def _aggregate_communities(
        self,
        communities: List[Community],
        level: int,
    ) -> List[Community]:
        """Aggregate communities into higher-level abstract communities.

        Uses community similarity (shared entity types, overlap) to merge.
        """
        if len(communities) <= 2:
            return []  # Can't aggregate further meaningfully

        # Simple aggregation: pair similar communities
        aggregated: List[Community] = []
        used: Set[str] = set()

        sorted_communities = sorted(communities, key=lambda c: c.size, reverse=True)

        for i, comm_a in enumerate(sorted_communities):
            if comm_a.id in used:
                continue

            # Find best partner
            best_partner = None
            best_similarity = 0.0

            for j, comm_b in enumerate(sorted_communities):
                if i >= j or comm_b.id in used:
                    continue

                similarity = self._community_similarity(comm_a, comm_b)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_partner = comm_b

            if best_partner and best_similarity > 0.1:
                # Merge communities
                merged_id = f"comm_{level}_{hashlib.md5((comm_a.id + best_partner.id).encode()).hexdigest()[:8]}"
                merged = Community(
                    id=merged_id,
                    level=level,
                    entity_ids=comm_a.entity_ids | best_partner.entity_ids,
                    title=f"{comm_a.title} & {best_partner.title}",
                    rank=(comm_a.rank + best_partner.rank) / 2,
                    child_ids={comm_a.id, best_partner.id},
                )
                aggregated.append(merged)
                used.add(comm_a.id)
                used.add(best_partner.id)

                # Set parent references
                comm_a.parent_id = merged_id
                best_partner.parent_id = merged_id
            else:
                # No good partner, promote as-is
                promoted = Community(
                    id=f"comm_{level}_{comm_a.id[-8:]}",
                    level=level,
                    entity_ids=comm_a.entity_ids,
                    title=comm_a.title,
                    rank=comm_a.rank,
                    child_ids={comm_a.id},
                )
                aggregated.append(promoted)
                used.add(comm_a.id)
                comm_a.parent_id = promoted.id

        return aggregated

    def _community_similarity(
        self,
        comm_a: Community,
        comm_b: Community,
    ) -> float:
        """Calculate similarity between two communities.

        Based on Jaccard similarity of entity IDs.
        """
        if not comm_a.entity_ids or not comm_b.entity_ids:
            return 0.0

        intersection = len(comm_a.entity_ids & comm_b.entity_ids)
        union = len(comm_a.entity_ids | comm_b.entity_ids)

        return intersection / union if union > 0 else 0.0

    def _generate_community_title(
        self,
        entity_ids: Set[str],
        entities: Dict[str, Entity],
    ) -> str:
        """Generate a descriptive title for a community."""
        # Collect entity types and names
        types: Dict[str, int] = defaultdict(int)
        names: List[str] = []

        for eid in list(entity_ids)[:5]:  # Sample first 5
            if eid in entities:
                entity = entities[eid]
                types[entity.type] += 1
                names.append(entity.name)

        # Build title from most common type and sample names
        if types:
            dominant_type = max(types.keys(), key=lambda t: types[t])
            sample_names = ", ".join(names[:3])
            return f"{dominant_type}s: {sample_names}"

        return f"Community ({len(entity_ids)} entities)"

    async def generate_community_reports(
        self,
        communities: Dict[int, List[Community]],
        graph: AuteurGraph,
        generate_embeddings: bool = True,
    ) -> List[CommunityReport]:
        """Generate LLM summaries for each community.

        Args:
            communities: Dict of level -> communities
            graph: Source graph for entity details
            generate_embeddings: Whether to generate summary embeddings

        Returns:
            List of CommunityReport objects
        """
        reports: List[CommunityReport] = []

        for level, level_communities in communities.items():
            for community in level_communities:
                report = await self._generate_single_report(
                    community,
                    graph,
                    generate_embeddings,
                )
                reports.append(report)

        logger.info(
            f"[CommunityDetector] Generated {len(reports)} community reports "
            f"for {graph.auteur_key}"
        )

        return reports

    async def _generate_single_report(
        self,
        community: Community,
        graph: AuteurGraph,
        generate_embeddings: bool,
    ) -> CommunityReport:
        """Generate report for a single community."""
        # Collect entity details
        entity_details: List[str] = []
        auteur_keys: Set[str] = set()

        for entity_id in list(community.entity_ids)[:20]:  # Limit for prompt
            if entity_id in graph.entities:
                entity = graph.entities[entity_id]
                entity_details.append(f"- {entity.name} ({entity.type})")

                # Extract auteur key if present
                if entity_id.startswith("auteur:"):
                    auteur_keys.add(entity_id.split(":")[-1])

        # Build summary (simple aggregation for now)
        # In production, this would call an LLM
        entity_list = "\n".join(entity_details)
        summary = self._build_summary_template(community, entity_list)

        # Generate key findings
        key_findings = self._extract_key_findings(community, graph)

        # Calculate token count (rough estimate)
        token_count = len(summary.split()) * 1.3  # Rough token estimate

        # Generate embedding if requested
        summary_embedding = None
        if generate_embeddings:
            summary_embedding = await self._generate_embedding(summary)

        return CommunityReport(
            community_id=community.id,
            level=community.level,
            title=community.title,
            summary=summary,
            summary_embedding=summary_embedding,
            key_findings=key_findings,
            rank=community.rank,
            token_count=int(token_count),
            auteur_keys=list(auteur_keys),
        )

    def _build_summary_template(
        self,
        community: Community,
        entity_list: str,
    ) -> str:
        """Build a summary template for the community.

        In production, this would be replaced with LLM generation.
        """
        return f"""Community: {community.title}
Level: {community.level} ({'Leaf' if community.level == 0 else 'Abstract'})
Size: {community.size} entities

Entities:
{entity_list}

This community represents a group of related concepts in the knowledge graph.
The entities share common relationships and thematic connections."""

    def _extract_key_findings(
        self,
        community: Community,
        graph: AuteurGraph,
    ) -> List[str]:
        """Extract key findings from community entities."""
        findings: List[str] = []

        # Count relationship types within community
        rel_types: Dict[str, int] = defaultdict(int)
        for rel in graph.relationships:
            if rel.source_id in community.entity_ids and rel.target_id in community.entity_ids:
                rel_types[rel.type] += 1

        for rel_type, count in sorted(rel_types.items(), key=lambda x: -x[1])[:3]:
            findings.append(f"Contains {count} {rel_type} relationships")

        # Entity type distribution
        entity_types: Dict[str, int] = defaultdict(int)
        for entity_id in community.entity_ids:
            if entity_id in graph.entities:
                entity_types[graph.entities[entity_id].type] += 1

        for etype, count in sorted(entity_types.items(), key=lambda x: -x[1])[:3]:
            findings.append(f"Includes {count} {etype} entities")

        return findings

    async def _generate_embedding(
        self,
        text: str,
    ) -> Optional[List[float]]:
        """Generate embedding for text.

        Uses Google's text-embedding-004 model.
        """
        try:
            from app.rag.embeddings import get_embedding

            return await get_embedding(text)
        except Exception as e:
            logger.warning(f"[CommunityDetector] Failed to generate embedding: {e}")
            return None


# =============================================================================
# Utility Functions
# =============================================================================

async def detect_and_report(
    graph: AuteurGraph,
    max_levels: int = 3,
    resolution: float = 1.0,
) -> Tuple[Dict[int, List[Community]], List[CommunityReport]]:
    """Convenience function: detect communities and generate reports.

    Args:
        graph: AuteurGraph to analyze
        max_levels: Maximum hierarchy levels
        resolution: Louvain resolution parameter

    Returns:
        Tuple of (communities by level, reports)
    """
    detector = CommunityDetector(resolution=resolution)
    communities = await detector.detect_communities(graph, max_levels=max_levels)
    reports = await detector.generate_community_reports(communities, graph)
    return communities, reports


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "Community",
    "CommunityReport",
    "CommunityDetector",
    "detect_and_report",
]
