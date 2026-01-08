"""GraphRAG Module for Auteur DNA.

Phase 5: Knowledge graph-based retrieval for multi-hop queries
about auteurs, films, techniques, and collaborators.

Usage:
    from app.rag.graph_rag import graph_query, build_auteur_graph
    
    # Build graph from source packs
    await build_auteur_graph("bong")
    
    # Query using graph traversal
    result = await graph_query(
        query="봉준호와 타란티노의 공통 촬영 기법",
        auteur_keys=["bong", "tarantino"],
    )

Entity Types:
- Auteur: Director/filmmaker
- Film: Movie/work
- Technique: Cinematography/editing technique
- Collaborator: DP, editor, composer

Relationship Types:
- DIRECTED: Auteur → Film
- USES_TECHNIQUE: Auteur → Technique
- SEEN_IN: Technique → Film
- COLLABORATES_WITH: Auteur → Collaborator
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from app.config import settings
from app.rag.observability import trace_rag

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

SOURCE_PACKS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "source_packs"

# Entity type definitions
ENTITY_TYPES = {"Auteur", "Film", "Technique", "Collaborator", "Camera", "Style"}

# Relationship type definitions
RELATIONSHIP_TYPES = {
    "DIRECTED",           # Auteur → Film
    "USES_TECHNIQUE",     # Auteur → Technique
    "SEEN_IN",            # Technique → Film  
    "COLLABORATES_WITH",  # Auteur → Collaborator
    "USES_CAMERA",        # Film → Camera
    "HAS_STYLE",          # Auteur → Style
}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class Entity:
    """Graph entity (node)."""
    id: str
    type: str  # Auteur, Film, Technique, etc.
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class Relationship:
    """Graph relationship (edge)."""
    source_id: str
    target_id: str
    type: str  # DIRECTED, USES_TECHNIQUE, etc.
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphRAGResult:
    """Result from graph-based query."""
    answer: str
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Tuple[str, str, str]] = field(default_factory=list)  # (source, rel, target)
    paths: List[List[str]] = field(default_factory=list)  # Traversal paths
    query_time_ms: int = 0
    strategy_used: str = "graph"


@dataclass
class AuteurGraph:
    """In-memory graph for an auteur."""
    auteur_key: str
    entities: Dict[str, Entity] = field(default_factory=dict)
    relationships: List[Relationship] = field(default_factory=list)
    
    def add_entity(self, entity: Entity):
        """Add entity to graph."""
        self.entities[entity.id] = entity
    
    def add_relationship(self, rel: Relationship):
        """Add relationship to graph."""
        self.relationships.append(rel)
    
    def get_related(self, entity_id: str, rel_type: Optional[str] = None) -> List[Entity]:
        """Get entities related to given entity."""
        related_ids = []
        for rel in self.relationships:
            if rel.source_id == entity_id:
                if rel_type is None or rel.type == rel_type:
                    related_ids.append(rel.target_id)
            elif rel.target_id == entity_id:
                if rel_type is None or rel.type == rel_type:
                    related_ids.append(rel.source_id)
        return [self.entities[eid] for eid in related_ids if eid in self.entities]


# ============================================================================
# Graph Cache
# ============================================================================

_graph_cache: Dict[str, AuteurGraph] = {}


def get_cached_graph(auteur_key: str) -> Optional[AuteurGraph]:
    """Get cached graph for auteur."""
    return _graph_cache.get(auteur_key)


def cache_graph(graph: AuteurGraph):
    """Cache graph for auteur."""
    _graph_cache[graph.auteur_key] = graph


# ============================================================================
# Entity Extraction
# ============================================================================

def extract_entities_from_source_pack(
    source_pack: Dict[str, Any],
    auteur_key: str,
) -> Tuple[List[Entity], List[Relationship]]:
    """
    Extract entities and relationships from a source pack JSON.
    
    Args:
        source_pack: Loaded source pack JSON
        auteur_key: Auteur identifier
        
    Returns:
        Tuple of (entities, relationships)
    """
    entities: List[Entity] = []
    relationships: List[Relationship] = []
    
    # Extract auteur entity
    auteur_name = source_pack.get("auteur", auteur_key)
    auteur_id = f"auteur:{auteur_key}"
    auteur_entity = Entity(
        id=auteur_id,
        type="Auteur",
        name=auteur_name,
        properties={"key": auteur_key},
    )
    entities.append(auteur_entity)
    
    content = source_pack.get("content", {})
    
    # Extract camera/equipment entities
    if "camera_equipment" in content:
        equip = content["camera_equipment"]
        if "camera" in equip:
            camera_id = f"camera:{equip['camera'].lower().replace(' ', '_')}"
            camera_entity = Entity(
                id=camera_id,
                type="Camera",
                name=equip["camera"],
                properties={"lenses": equip.get("lenses", "")},
            )
            entities.append(camera_entity)
            relationships.append(Relationship(
                source_id=auteur_id,
                target_id=camera_id,
                type="USES_CAMERA",
            ))
    
    # Extract techniques from various sections
    technique_sections = [
        "camera_movement_symbolism",
        "composition_techniques",
        "cinematography_techniques",
        "lighting_techniques",
        "editing_techniques",
    ]
    
    for section_name in technique_sections:
        if section_name in content:
            section = content[section_name]
            for tech_key, tech_data in section.items():
                if isinstance(tech_data, dict):
                    tech_id = f"technique:{tech_key}"
                    tech_name = tech_key.replace("_", " ").title()
                    
                    tech_entity = Entity(
                        id=tech_id,
                        type="Technique",
                        name=tech_name,
                        properties={
                            "description": tech_data.get("technique", tech_data.get("description", "")),
                            "meaning": tech_data.get("meaning", ""),
                            "effect": tech_data.get("effect", ""),
                        },
                    )
                    entities.append(tech_entity)
                    relationships.append(Relationship(
                        source_id=auteur_id,
                        target_id=tech_id,
                        type="USES_TECHNIQUE",
                    ))
    
    # Extract films from various references
    film_refs = set()
    
    # Look for film names in the content
    content_str = json.dumps(content, ensure_ascii=False)
    
    # Known film patterns (could be expanded)
    known_films = {
        "기생충": "parasite",
        "살인의 추억": "memories_of_murder",
        "마더": "mother",
        "설국열차": "snowpiercer",
        "옥자": "okja",
        "인셉션": "inception",
        "인터스텔라": "interstellar",
        "덩케르크": "dunkirk",
        "오펜하이머": "oppenheimer",
        "테넷": "tenet",
        "펄프 픽션": "pulp_fiction",
        "킬 빌": "kill_bill",
        "듄": "dune",
        "블레이드 러너 2049": "blade_runner_2049",
        "화양연화": "in_the_mood_for_love",
    }
    
    for korean_name, english_id in known_films.items():
        if korean_name in content_str:
            film_refs.add((korean_name, english_id))
    
    for korean_name, english_id in film_refs:
        film_id = f"film:{english_id}"
        film_entity = Entity(
            id=film_id,
            type="Film",
            name=korean_name,
            properties={"english_id": english_id},
        )
        entities.append(film_entity)
        relationships.append(Relationship(
            source_id=auteur_id,
            target_id=film_id,
            type="DIRECTED",
        ))
    
    # Extract Veo prompt keywords as style traits
    if "veo_prompt_keywords" in content:
        for keyword in content["veo_prompt_keywords"][:5]:  # Limit to top 5
            style_id = f"style:{keyword.lower().replace(' ', '_')}"
            style_entity = Entity(
                id=style_id,
                type="Style",
                name=keyword,
            )
            entities.append(style_entity)
            relationships.append(Relationship(
                source_id=auteur_id,
                target_id=style_id,
                type="HAS_STYLE",
            ))
    
    return entities, relationships


# ============================================================================
# Graph Building
# ============================================================================

async def build_auteur_graph(auteur_key: str) -> AuteurGraph:
    """
    Build knowledge graph from source packs for an auteur.
    
    Args:
        auteur_key: Auteur identifier (e.g., "bong", "nolan")
        
    Returns:
        AuteurGraph with entities and relationships
    """
    # Check cache first
    cached = get_cached_graph(auteur_key)
    if cached:
        logger.debug(f"[GraphRAG] Using cached graph for {auteur_key}")
        return cached
    
    graph = AuteurGraph(auteur_key=auteur_key)
    
    # Find source pack directory
    auteur_dir = SOURCE_PACKS_DIR / auteur_key
    if not auteur_dir.exists():
        logger.warning(f"[GraphRAG] No source packs found for {auteur_key}")
        return graph
    
    # Process all JSON files
    json_files = list(auteur_dir.glob("*.json"))
    logger.info(f"[GraphRAG] Building graph for {auteur_key} from {len(json_files)} source packs")
    
    all_entities: Dict[str, Entity] = {}
    all_relationships: List[Relationship] = []
    
    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                source_pack = json.load(f)
            
            entities, relationships = extract_entities_from_source_pack(
                source_pack, auteur_key
            )
            
            # Deduplicate entities by ID
            for entity in entities:
                if entity.id not in all_entities:
                    all_entities[entity.id] = entity
            
            all_relationships.extend(relationships)
            
        except Exception as e:
            logger.error(f"[GraphRAG] Error processing {json_file}: {e}")
    
    # Populate graph
    for entity in all_entities.values():
        graph.add_entity(entity)
    
    for rel in all_relationships:
        graph.add_relationship(rel)
    
    # Cache the graph
    cache_graph(graph)
    
    logger.info(
        f"[GraphRAG] Built graph for {auteur_key}: "
        f"{len(graph.entities)} entities, {len(graph.relationships)} relationships"
    )
    
    return graph


# ============================================================================
# Graph Querying
# ============================================================================

@trace_rag(name="graph_query", tags=["rag", "graph"])
async def graph_query(
    query: str,
    auteur_keys: Optional[List[str]] = None,
    max_hops: int = 2,
) -> GraphRAGResult:
    """
    Query using graph traversal.
    
    Args:
        query: Natural language query
        auteur_keys: List of auteur keys to include (None = all)
        max_hops: Maximum relationship hops
        
    Returns:
        GraphRAGResult with entities and relationships
    """
    import time
    start_time = time.monotonic()
    
    # Build graphs for requested auteurs
    if auteur_keys is None:
        # Auto-detect from available source packs
        auteur_keys = [d.name for d in SOURCE_PACKS_DIR.iterdir() if d.is_dir()]
    
    graphs: List[AuteurGraph] = []
    for key in auteur_keys:
        graph = await build_auteur_graph(key)
        if graph.entities:
            graphs.append(graph)
    
    if not graphs:
        return GraphRAGResult(
            answer="No graph data available for the requested auteurs.",
            query_time_ms=int((time.monotonic() - start_time) * 1000),
        )
    
    # Simple keyword-based entity matching (MVP approach)
    query_lower = query.lower()
    matched_entities: List[Entity] = []
    matched_relationships: List[Tuple[str, str, str]] = []
    
    for graph in graphs:
        for entity in graph.entities.values():
            entity_name_lower = entity.name.lower()
            # Check if entity name appears in query or vice versa
            if entity_name_lower in query_lower or any(
                word in entity_name_lower 
                for word in query_lower.split() 
                if len(word) > 2
            ):
                matched_entities.append(entity)
                
                # Get related entities (1-hop)
                related = graph.get_related(entity.id)
                for rel_entity in related[:5]:  # Limit related
                    matched_entities.append(rel_entity)
                    # Find the relationship
                    for rel in graph.relationships:
                        if (rel.source_id == entity.id and rel.target_id == rel_entity.id) or \
                           (rel.target_id == entity.id and rel.source_id == rel_entity.id):
                            matched_relationships.append((
                                entity.name,
                                rel.type,
                                rel_entity.name,
                            ))
                            break
    
    # Deduplicate entities
    seen_ids: Set[str] = set()
    unique_entities: List[Entity] = []
    for entity in matched_entities:
        if entity.id not in seen_ids:
            seen_ids.add(entity.id)
            unique_entities.append(entity)
    
    # Generate answer summary
    if not unique_entities:
        answer = f"No specific entities found for query: {query}"
    else:
        entity_summary = ", ".join([e.name for e in unique_entities[:10]])
        rel_summary = " | ".join([f"{s} -{r}-> {t}" for s, r, t in matched_relationships[:5]])
        answer = f"Found {len(unique_entities)} entities: {entity_summary}\n\nRelationships: {rel_summary}"
    
    query_time_ms = int((time.monotonic() - start_time) * 1000)
    
    logger.info(
        f"[GraphRAG] Query completed | "
        f"entities={len(unique_entities)} | "
        f"relationships={len(matched_relationships)} | "
        f"time={query_time_ms}ms"
    )
    
    return GraphRAGResult(
        answer=answer,
        entities=unique_entities,
        relationships=matched_relationships,
        query_time_ms=query_time_ms,
    )


# ============================================================================
# Utility Functions
# ============================================================================

async def get_all_auteurs() -> List[str]:
    """Get list of available auteur keys."""
    return [d.name for d in SOURCE_PACKS_DIR.iterdir() if d.is_dir()]


async def get_graph_stats(auteur_key: str) -> Dict[str, int]:
    """Get statistics for an auteur's graph."""
    graph = await build_auteur_graph(auteur_key)
    
    entity_counts = {}
    for entity in graph.entities.values():
        entity_counts[entity.type] = entity_counts.get(entity.type, 0) + 1
    
    rel_counts = {}
    for rel in graph.relationships:
        rel_counts[rel.type] = rel_counts.get(rel.type, 0) + 1
    
    return {
        "total_entities": len(graph.entities),
        "total_relationships": len(graph.relationships),
        "entity_types": entity_counts,
        "relationship_types": rel_counts,
    }


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "graph_query",
    "build_auteur_graph",
    "get_all_auteurs",
    "get_graph_stats",
    "GraphRAGResult",
    "AuteurGraph",
    "Entity",
    "Relationship",
]
