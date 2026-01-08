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
# Entity Extraction (Hardened - 2025/2026 Best Practices)
# ============================================================================

# Comprehensive film database for entity extraction
FILM_DATABASE = {
    # Bong Joon-ho
    "parasite": {"korean": "기생충", "year": 2019, "auteur": "bong"},
    "memories_of_murder": {"korean": "살인의 추억", "year": 2003, "auteur": "bong"},
    "mother": {"korean": "마더", "year": 2009, "auteur": "bong"},
    "snowpiercer": {"korean": "설국열차", "year": 2013, "auteur": "bong"},
    "okja": {"korean": "옥자", "year": 2017, "auteur": "bong"},
    "the_host": {"korean": "괴물", "year": 2006, "auteur": "bong"},
    "barking_dogs": {"korean": "플란다스의 개", "year": 2000, "auteur": "bong"},
    # Christopher Nolan
    "inception": {"korean": "인셉션", "year": 2010, "auteur": "nolan"},
    "interstellar": {"korean": "인터스텔라", "year": 2014, "auteur": "nolan"},
    "dunkirk": {"korean": "덩케르크", "year": 2017, "auteur": "nolan"},
    "oppenheimer": {"korean": "오펜하이머", "year": 2023, "auteur": "nolan"},
    "tenet": {"korean": "테넷", "year": 2020, "auteur": "nolan"},
    "memento": {"korean": "메멘토", "year": 2000, "auteur": "nolan"},
    "the_dark_knight": {"korean": "다크 나이트", "year": 2008, "auteur": "nolan"},
    "the_dark_knight_rises": {"korean": "다크 나이트 라이즈", "year": 2012, "auteur": "nolan"},
    # Quentin Tarantino
    "pulp_fiction": {"korean": "펄프 픽션", "year": 1994, "auteur": "tarantino"},
    "kill_bill": {"korean": "킬 빌", "year": 2003, "auteur": "tarantino"},
    "kill_bill_vol_2": {"korean": "킬 빌 2", "year": 2004, "auteur": "tarantino"},
    "django_unchained": {"korean": "장고: 분노의 추적자", "year": 2012, "auteur": "tarantino"},
    "inglourious_basterds": {"korean": "바스터즈: 거친 녀석들", "year": 2009, "auteur": "tarantino"},
    "reservoir_dogs": {"korean": "저수지의 개들", "year": 1992, "auteur": "tarantino"},
    "once_upon_a_time_in_hollywood": {"korean": "원스 어폰 어 타임 인 할리우드", "year": 2019, "auteur": "tarantino"},
    # Denis Villeneuve
    "dune": {"korean": "듄", "year": 2021, "auteur": "villeneuve"},
    "dune_part_two": {"korean": "듄: 파트 2", "year": 2024, "auteur": "villeneuve"},
    "blade_runner_2049": {"korean": "블레이드 러너 2049", "year": 2017, "auteur": "villeneuve"},
    "arrival": {"korean": "컨택트", "year": 2016, "auteur": "villeneuve"},
    "sicario": {"korean": "시카리오", "year": 2015, "auteur": "villeneuve"},
    "incendies": {"korean": "그을린 사랑", "year": 2010, "auteur": "villeneuve"},
    "prisoners": {"korean": "프리즈너스", "year": 2013, "auteur": "villeneuve"},
    # Wong Kar-wai
    "in_the_mood_for_love": {"korean": "화양연화", "year": 2000, "auteur": "wong"},
    "chungking_express": {"korean": "중경삼림", "year": 1994, "auteur": "wong"},
    "fallen_angels": {"korean": "타락천사", "year": 1995, "auteur": "wong"},
    "happy_together": {"korean": "해피투게더", "year": 1997, "auteur": "wong"},
    "2046": {"korean": "2046", "year": 2004, "auteur": "wong"},
    "days_of_being_wild": {"korean": "아비정전", "year": 1990, "auteur": "wong"},
    "ashes_of_time": {"korean": "동사서독", "year": 1994, "auteur": "wong"},
    # Park Chan-wook
    "oldboy": {"korean": "올드보이", "year": 2003, "auteur": "park"},
    "the_handmaiden": {"korean": "아가씨", "year": 2016, "auteur": "park"},
    "decision_to_leave": {"korean": "헤어질 결심", "year": 2022, "auteur": "park"},
    "sympathy_for_mr_vengeance": {"korean": "복수는 나의 것", "year": 2002, "auteur": "park"},
}

# Known collaborator database for cross-auteur linking
COLLABORATOR_DATABASE = {
    "hong_kyung_pyo": {"name": "홍경표", "role": "Cinematographer", "worked_with": ["bong"]},
    "hoyte_van_hoytema": {"name": "Hoyte van Hoytema", "role": "Cinematographer", "worked_with": ["nolan", "villeneuve"]},
    "wally_pfister": {"name": "Wally Pfister", "role": "Cinematographer", "worked_with": ["nolan"]},
    "roger_deakins": {"name": "Roger Deakins", "role": "Cinematographer", "worked_with": ["villeneuve"]},
    "christopher_doyle": {"name": "Christopher Doyle", "role": "Cinematographer", "worked_with": ["wong", "park"]},
    "hans_zimmer": {"name": "Hans Zimmer", "role": "Composer", "worked_with": ["nolan", "villeneuve"]},
    "johnny_greenwood": {"name": "Jonny Greenwood", "role": "Composer", "worked_with": ["villeneuve"]},
    "william_chang": {"name": "William Chang", "role": "Editor/Production Designer", "worked_with": ["wong"]},
    "robert_richardson": {"name": "Robert Richardson", "role": "Cinematographer", "worked_with": ["tarantino"]},
    "sally_menke": {"name": "Sally Menke", "role": "Editor", "worked_with": ["tarantino"]},
    "jung_jung_hoon": {"name": "정정훈", "role": "Composer", "worked_with": ["bong"]},
    "tilda_swinton": {"name": "Tilda Swinton", "role": "Actor", "worked_with": ["bong"]},
    "song_kang_ho": {"name": "송강호", "role": "Actor", "worked_with": ["bong", "park"]},
}


def _normalize_film_name(name: str) -> Optional[str]:
    """Normalize film name to database key."""
    name_lower = name.lower().strip()
    
    # Direct match
    if name_lower in FILM_DATABASE:
        return name_lower
    
    # Match by Korean name
    for film_id, data in FILM_DATABASE.items():
        if name == data["korean"] or name_lower == data["korean"].lower():
            return film_id
    
    # Fuzzy match (remove common words)
    name_clean = name_lower.replace("the ", "").replace(" ", "_")
    for film_id in FILM_DATABASE:
        if name_clean in film_id or film_id in name_clean:
            return film_id
    
    return None


def _extract_films_from_text(text: str, auteur_key: str) -> List[Tuple[str, str]]:
    """Extract film references from text content."""
    films = []
    text_lower = text.lower()
    
    for film_id, data in FILM_DATABASE.items():
        # Check Korean name
        if data["korean"] in text:
            films.append((film_id, data["korean"]))
        # Check English name (with underscores as spaces)
        english_name = film_id.replace("_", " ")
        if english_name in text_lower:
            films.append((film_id, data["korean"]))
    
    return list(set(films))


def _extract_collaborators_from_section(
    collaborators_data: Dict[str, Any],
    auteur_id: str,
) -> Tuple[List[Entity], List[Relationship]]:
    """Extract collaborators from explicit collaborators section."""
    entities = []
    relationships = []
    
    for collab_key, collab_data in collaborators_data.items():
        if isinstance(collab_data, dict):
            collab_id = f"collaborator:{collab_key}"
            collab_name = collab_key.replace("_", " ").title()
            role = collab_data.get("role", "Unknown")
            
            # Check if in database for canonical name
            if collab_key in COLLABORATOR_DATABASE:
                db_entry = COLLABORATOR_DATABASE[collab_key]
                collab_name = db_entry["name"]
                role = db_entry["role"]
            
            collab_entity = Entity(
                id=collab_id,
                type="Collaborator",
                name=collab_name,
                properties={
                    "role": role,
                    "contribution": collab_data.get("contribution", ""),
                    "films": collab_data.get("films", []),
                },
            )
            entities.append(collab_entity)
            relationships.append(Relationship(
                source_id=auteur_id,
                target_id=collab_id,
                type="COLLABORATES_WITH",
                properties={"role": role},
            ))
    
    return entities, relationships


def _extract_films_from_array(
    films_array: List[str],
    auteur_id: str,
) -> Tuple[List[Entity], List[Relationship]]:
    """Extract films from films_together or similar arrays."""
    entities = []
    relationships = []
    
    for film_name in films_array:
        film_id_key = _normalize_film_name(film_name)
        if film_id_key:
            film_id = f"film:{film_id_key}"
            film_data = FILM_DATABASE.get(film_id_key, {})
            film_entity = Entity(
                id=film_id,
                type="Film",
                name=film_data.get("korean", film_name),
                properties={
                    "english_id": film_id_key,
                    "year": film_data.get("year"),
                },
            )
            entities.append(film_entity)
            relationships.append(Relationship(
                source_id=auteur_id,
                target_id=film_id,
                type="DIRECTED",
            ))
        else:
            # Unknown film - still add with normalized ID
            clean_name = film_name.lower().replace(" ", "_").replace("'", "")
            film_id = f"film:{clean_name}"
            film_entity = Entity(
                id=film_id,
                type="Film",
                name=film_name,
                properties={"english_id": clean_name},
            )
            entities.append(film_entity)
            relationships.append(Relationship(
                source_id=auteur_id,
                target_id=film_id,
                type="DIRECTED",
            ))
    
    return entities, relationships


def _deep_extract_films_from_content(
    content: Dict[str, Any],
    auteur_id: str,
    auteur_key: str,
) -> Tuple[List[Entity], List[Relationship]]:
    """Deep extraction of films from nested content structures."""
    entities = []
    relationships = []
    content_str = json.dumps(content, ensure_ascii=False)
    
    # Extract from all examples sections
    def find_examples(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "examples" and isinstance(value, (dict, list)):
                    if isinstance(value, dict):
                        for film_ref in value.keys():
                            film_id_key = _normalize_film_name(film_ref)
                            if film_id_key:
                                yield (film_id_key, FILM_DATABASE.get(film_id_key, {}).get("korean", film_ref))
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, str):
                                # Extract film name from strings like "Rotating hallway (Inception)"
                                import re
                                match = re.search(r'\(([^)]+)\)', item)
                                if match:
                                    film_name = match.group(1)
                                    film_id_key = _normalize_film_name(film_name)
                                    if film_id_key:
                                        yield (film_id_key, FILM_DATABASE.get(film_id_key, {}).get("korean", film_name))
                else:
                    yield from find_examples(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                yield from find_examples(item, f"{path}[{i}]")
    
    found_films = set(find_examples(content))
    
    # Also search the entire content string for known films
    for film_id_key, data in FILM_DATABASE.items():
        if data.get("auteur") == auteur_key:
            if data["korean"] in content_str or film_id_key.replace("_", " ") in content_str.lower():
                found_films.add((film_id_key, data["korean"]))
    
    for film_id_key, film_name in found_films:
        film_id = f"film:{film_id_key}"
        film_data = FILM_DATABASE.get(film_id_key, {})
        film_entity = Entity(
            id=film_id,
            type="Film",
            name=film_name,
            properties={
                "english_id": film_id_key,
                "year": film_data.get("year"),
            },
        )
        entities.append(film_entity)
        relationships.append(Relationship(
            source_id=auteur_id,
            target_id=film_id,
            type="DIRECTED",
        ))
    
    return entities, relationships


def extract_entities_from_source_pack(
    source_pack: Dict[str, Any],
    auteur_key: str,
) -> Tuple[List[Entity], List[Relationship]]:
    """
    Extract entities and relationships from a source pack JSON.
    
    Hardened version with deep extraction for:
    - Explicit collaborators sections
    - films_together arrays
    - Examples with film references
    - Cross-auteur collaborator linking
    
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
        properties={
            "key": auteur_key,
            "category": source_pack.get("category", "unknown"),
        },
    )
    entities.append(auteur_entity)
    
    content = source_pack.get("content", {})
    
    # === 1. Extract Camera/Equipment ===
    if "camera_equipment" in content:
        equip = content["camera_equipment"]
        if "camera" in equip:
            camera_id = f"camera:{equip['camera'].lower().replace(' ', '_')}"
            camera_entity = Entity(
                id=camera_id,
                type="Camera",
                name=equip["camera"],
                properties={
                    "lenses": equip.get("lenses", ""),
                    "effect": equip.get("effect", ""),
                },
            )
            entities.append(camera_entity)
            relationships.append(Relationship(
                source_id=auteur_id,
                target_id=camera_id,
                type="USES_CAMERA",
            ))
    
    # === 2. Extract Techniques (Deep) ===
    technique_sections = [
        "camera_movement_symbolism",
        "composition_techniques", 
        "cinematography_techniques",
        "cinematography_signature",
        "lighting_techniques",
        "lighting_approach",
        "editing_techniques",
        "narrative_structure",
        "mathematical_imagery",
        "thematic_obsessions",
        "genre_hybridity",
        "dark_comedy",
        "thriller_elements",
        "horror_elements",
        "tone_shifts",
        "color_philosophy",
        "improvisation_approach",
    ]
    
    for section_name in technique_sections:
        if section_name in content:
            section = content[section_name]
            if isinstance(section, dict):
                for tech_key, tech_data in section.items():
                    if isinstance(tech_data, dict):
                        tech_id = f"technique:{section_name}_{tech_key}"
                        tech_name = f"{section_name.replace('_', ' ').title()}: {tech_key.replace('_', ' ').title()}"
                        
                        tech_entity = Entity(
                            id=tech_id,
                            type="Technique",
                            name=tech_name,
                            properties={
                                "category": section_name,
                                "description": tech_data.get("technique", tech_data.get("description", tech_data.get("philosophy", ""))),
                                "meaning": tech_data.get("meaning", ""),
                                "effect": tech_data.get("effect", tech_data.get("purpose", "")),
                                "examples": tech_data.get("examples", []),
                            },
                        )
                        entities.append(tech_entity)
                        relationships.append(Relationship(
                            source_id=auteur_id,
                            target_id=tech_id,
                            type="USES_TECHNIQUE",
                        ))
    
    # === 3. Extract Collaborators (Explicit Section) ===
    if "collaborators" in content:
        collab_entities, collab_rels = _extract_collaborators_from_section(
            content["collaborators"], auteur_id
        )
        entities.extend(collab_entities)
        relationships.extend(collab_rels)
    
    # === 4. Extract Partnership/Collaboration ===
    if "partnership" in content:
        partnership = content["partnership"]
        # Extract films_together
        if "films_together" in partnership:
            film_entities, film_rels = _extract_films_from_array(
                partnership["films_together"], auteur_id
            )
            entities.extend(film_entities)
            relationships.extend(film_rels)
    
    # === 5. Deep Film Extraction ===
    film_entities, film_rels = _deep_extract_films_from_content(
        content, auteur_id, auteur_key
    )
    entities.extend(film_entities)
    relationships.extend(film_rels)
    
    # === 6. Extract Veo Prompt Keywords as Styles (Limit 8) ===
    veo_keys = content.get("veo_prompt_keywords", content.get("prompt_generation_keywords", []))
    for keyword in veo_keys[:8]:
        style_id = f"style:{auteur_key}_{keyword.lower().replace(' ', '_')}"
        style_entity = Entity(
            id=style_id,
            type="Style",
            name=keyword,
            properties={"auteur": auteur_key},
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
