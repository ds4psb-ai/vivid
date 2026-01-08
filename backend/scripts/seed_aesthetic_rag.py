#!/usr/bin/env python
"""Seed Aesthetic Director RAG data into Qdrant.

Indexes auteur style data, VDG standards, and aesthetic theory
into the AD dimension collection.

Usage:
    cd backend
    source venv/bin/activate
    python scripts/seed_aesthetic_rag.py

    # Verify indexing
    python scripts/seed_aesthetic_rag.py --verify
"""
import argparse
import json
import logging
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.tier1_dimension_rag import get_dimension_rag

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Data paths
RAG_DOCS_DIR = Path(__file__).parent.parent / "data" / "rag_docs"
AUTEUR_STYLES_PATH = RAG_DOCS_DIR / "aesthetic" / "auteur_styles.json"
VDG_STANDARDS_PATH = RAG_DOCS_DIR / "aesthetic" / "vdg_standards.json"


def index_auteur_styles(rag) -> int:
    """Index auteur style guide documents.

    Returns:
        Number of documents indexed
    """
    if not AUTEUR_STYLES_PATH.exists():
        logger.warning(f"Auteur styles file not found: {AUTEUR_STYLES_PATH}")
        return 0

    with open(AUTEUR_STYLES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    auteurs = data.get("auteurs", {})

    for key, auteur in auteurs.items():
        # Create rich content for embedding
        content = f"""
Auteur: {auteur.get('name', key)}
Nationality: {auteur.get('nationality', 'Unknown')}
Signature Style: {auteur.get('signature', '')}

Visual Grammar:
- Palette Bias: {auteur.get('palette_bias', 'neutral')}
- Pacing: {auteur.get('pacing', 'medium')}
- Camera Style: {auteur.get('camera_style', 'standard')}

Techniques: {', '.join(auteur.get('techniques', []))}

Avoid Elements: {', '.join(auteur.get('avoid_elements', []))}

Reference Films: {', '.join(auteur.get('reference_films', []))}

Color Palette: {', '.join(auteur.get('color_palette', []))}

Visual Composition: {auteur.get('visual_grammar', {}).get('composition', '')}
Lighting: {auteur.get('visual_grammar', {}).get('lighting', '')}
Depth: {auteur.get('visual_grammar', {}).get('depth', '')}
        """.strip()

        doc_id = f"auteur_{key}"
        metadata = {
            "app_key": "dimension.aesthetic.direct",
            "content_type": "auteur_style",
            "auteur_key": key,
            "auteur_name": auteur.get("name", key),
            "source": "auteur_styles.json",
        }

        if rag.index_document(doc_id, content, metadata):
            logger.info(f"  ✓ Indexed: {auteur.get('name', key)}")
            count += 1
        else:
            logger.error(f"  ✗ Failed: {auteur.get('name', key)}")

    return count


def index_vdg_standards(rag) -> int:
    """Index VDG (Visual Design Grammar) standards.

    Returns:
        Number of documents indexed
    """
    if not VDG_STANDARDS_PATH.exists():
        logger.warning(f"VDG standards file not found: {VDG_STANDARDS_PATH}")
        return 0

    with open(VDG_STANDARDS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    standards = data.get("standards", [])

    for i, standard in enumerate(standards):
        # Create content for embedding
        content = f"""
VDG Standard: {standard.get('name', f'Standard {i+1}')}
Category: {standard.get('category', 'general')}

Description: {standard.get('description', '')}

Principles:
{chr(10).join(f'- {p}' for p in standard.get('principles', []))}

Application: {standard.get('application', '')}

Examples: {', '.join(standard.get('examples', []))}
        """.strip()

        doc_id = f"vdg_{i}_{standard.get('name', 'standard').replace(' ', '_').lower()}"
        metadata = {
            "app_key": "dimension.aesthetic.direct",
            "content_type": "aesthetic_theory",
            "category": standard.get("category", "general"),
            "source": "vdg_standards.json",
        }

        if rag.index_document(doc_id, content, metadata):
            logger.info(f"  ✓ Indexed: {standard.get('name', f'Standard {i+1}')}")
            count += 1
        else:
            logger.error(f"  ✗ Failed: {standard.get('name', f'Standard {i+1}')}")

    return count


# ========================================
# 4-Layer Source Pack Indexing (Bong Joon-ho)
# ========================================
SOURCE_PACKS_DIR = Path(__file__).parent.parent.parent / "data" / "source_packs"


def index_layer0_shot_analysis(rag, auteur: str = "bong") -> int:
    """Index Layer0 shot analysis chunks for an auteur.

    Returns:
        Number of documents indexed
    """
    layer0_path = SOURCE_PACKS_DIR / auteur / "layer0_raw" / "shot_analysis_chunks.json"
    if not layer0_path.exists():
        logger.warning(f"Layer0 not found: {layer0_path}")
        return 0

    with open(layer0_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    chunks = data.get("chunks", [])

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id", "")
        metadata_info = chunk.get("metadata", {})
        content_info = chunk.get("content", {})
        visual = content_info.get("visual_schema", {})
        audio = content_info.get("audio_schema", {})

        # Build rich content
        content = f"""
Shot: {chunk_id}
Film: {metadata_info.get('film_title', '')} ({metadata_info.get('film_year', '')})
Phase: {metadata_info.get('temporal_phase', '')}
Scene: {metadata_info.get('scene_range', '')}

Transcript: {content_info.get('transcript', '')}

Visual:
- Composition: {visual.get('composition', '')}
- Lighting: {visual.get('lighting', '')}
- Camera: {visual.get('camera_motion', '')}
- Pacing: {visual.get('pacing', '')}
- Colors: {', '.join(visual.get('color_palette', []))}

Audio: {audio.get('sound_design', '')}, {audio.get('music_mood', '')}

Motifs: {', '.join(content_info.get('motifs', []))}
        """.strip()

        doc_id = f"layer0_{chunk_id}"
        metadata = {
            "app_key": "dimension.aesthetic.direct",
            "content_type": "shot_analysis",
            "auteur": auteur,
            "layer": "layer0_raw",
            "film": metadata_info.get("film_title", ""),
            "phase": metadata_info.get("temporal_phase", ""),
            "source": "shot_analysis_chunks.json",
        }

        if rag.index_document(doc_id, content, metadata):
            logger.info(f"  ✓ Layer0: {chunk_id}")
            count += 1

    return count


def index_layer1_logic_persona(rag, auteur: str = "bong") -> int:
    """Index Layer1 Logic Vector + Persona Vector.

    Returns:
        Number of documents indexed
    """
    layer1_path = SOURCE_PACKS_DIR / auteur / "layer1_structured" / "logic_persona_vectors.json"
    if not layer1_path.exists():
        logger.warning(f"Layer1 not found: {layer1_path}")
        return 0

    with open(layer1_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    auteur_name = data.get("auteur", auteur)

    # Index Logic Vector
    logic = data.get("logic_vector", {})
    if logic:
        cadence = logic.get("cadence", {})
        composition = logic.get("composition", {})
        camera = logic.get("camera_motion", {})

        logic_content = f"""
{auteur_name} Logic Vector

Cadence:
- Shot Length: median {cadence.get('shot_length_ms', {}).get('median', 'N/A')}ms ({cadence.get('shot_length_ms', {}).get('signature', '')})
- Cut Density: HOOK {cadence.get('cut_density', {}).get('hook', '')} → CLIMAX {cadence.get('cut_density', {}).get('climax', '')}
- Transitions: {', '.join(f"{k} {int(v*100)}%" for k, v in cadence.get('transition_types', {}).items())}

Composition:
- Primary Strategy: {composition.get('primary_strategy', '')}
- Symmetry Score: {composition.get('symmetry_score', '')}
- Depth Usage: {composition.get('depth_usage', '')}
- Framing: {', '.join(f"{k} {int(v*100)}%" for k, v in composition.get('framing_ratio', {}).items())}
- Signature Compositions: {', '.join(composition.get('signature_compositions', []))}

Camera Motion:
- {', '.join(f"{k} {int(v*100)}%" for k, v in camera.items() if k != 'signature')}
- Signature: {camera.get('signature', '')}
        """.strip()

        doc_id = f"layer1_logic_{auteur}"
        metadata = {
            "app_key": "dimension.aesthetic.direct",
            "content_type": "logic_vector",
            "auteur": auteur,
            "layer": "layer1_structured",
            "source": "logic_persona_vectors.json",
        }

        if rag.index_document(doc_id, logic_content, metadata):
            logger.info(f"  ✓ Layer1 Logic Vector: {auteur}")
            count += 1

    # Index Persona Vector
    persona = data.get("persona_vector", {})
    if persona:
        emotion_arc = persona.get("emotion_arc", [])
        emotion_desc = "; ".join(
            f"t={e.get('t', 0)}: {e.get('label', '')} (valence {e.get('valence', 0)})"
            for e in emotion_arc
        )

        persona_content = f"""
{auteur_name} Persona Vector

Tone: {', '.join(persona.get('tone', []))}

Emotion Arc:
{emotion_desc}

Sentence Rhythm: {persona.get('sentence_rhythm', {}).get('signature', '')}
Interpretation Frame: {', '.join(persona.get('interpretation_frame', []))}

Tonal Shifts:
- Comedy to Horror: {persona.get('tonal_shifts', {}).get('comedy_to_horror', '')}
- Mundane to Violent: {persona.get('tonal_shifts', {}).get('mundane_to_violent', '')}
- Hope to Despair: {persona.get('tonal_shifts', {}).get('hope_to_despair', '')}
        """.strip()

        doc_id = f"layer1_persona_{auteur}"
        metadata = {
            "app_key": "dimension.aesthetic.direct",
            "content_type": "persona_vector",
            "auteur": auteur,
            "layer": "layer1_structured",
            "source": "logic_persona_vectors.json",
        }

        if rag.index_document(doc_id, persona_content, metadata):
            logger.info(f"  ✓ Layer1 Persona Vector: {auteur}")
            count += 1

    # Index Pattern Rules
    rules = data.get("pattern_rules", [])
    for rule in rules:
        rule_content = f"""
{auteur_name} Pattern Rule: {rule.get('name', '')}

Description: {rule.get('description', '')}
Application: {rule.get('application_condition', '')}
        """.strip()

        doc_id = f"layer1_rule_{rule.get('rule_id', '')}"
        metadata = {
            "app_key": "dimension.aesthetic.direct",
            "content_type": "pattern_rule",
            "auteur": auteur,
            "layer": "layer1_structured",
            "source": "logic_persona_vectors.json",
        }

        if rag.index_document(doc_id, rule_content, metadata):
            logger.info(f"  ✓ Layer1 Rule: {rule.get('name', '')}")
            count += 1

    return count


def index_layer2_variation_guide(rag, auteur: str = "bong") -> int:
    """Index Layer2 variation guide markdown.

    Returns:
        Number of documents indexed
    """
    layer2_path = SOURCE_PACKS_DIR / auteur / "layer2_synthesized" / "variation_guide_ko.md"
    if not layer2_path.exists():
        logger.warning(f"Layer2 not found: {layer2_path}")
        return 0

    with open(layer2_path, "r", encoding="utf-8") as f:
        content = f.read()

    doc_id = f"layer2_variation_guide_{auteur}"
    metadata = {
        "app_key": "dimension.aesthetic.direct",
        "content_type": "variation_guide",
        "auteur": auteur,
        "layer": "layer2_synthesized",
        "source": "variation_guide_ko.md",
    }

    if rag.index_document(doc_id, content, metadata):
        logger.info(f"  ✓ Layer2 Variation Guide: {auteur}")
        return 1
    return 0


def verify_indexing(rag) -> bool:
    """Verify that data was indexed correctly."""
    logger.info("\n📊 Verifying AD collection...")

    # Test searches
    queries = [
        ("봉준호 시각적 스타일 구도", "layer0"),
        ("박찬욱 대칭성과 색감", "layer1")
    ]
    
    success = True
    for query, expected in queries:
        logger.info(f"\n  Query: '{query}'")
        results = rag.search(query, limit=3, min_score=0.0)
        if results:
            logger.info(f"    ✓ Search returned {len(results)} results")
            for r in results:
                logger.info(f"      - [{r['score']:.3f}] {r.get('metadata', {}).get('auteur_name', r['doc_id'][:40])}")
        else:
            logger.warning(f"    ✗ Search returned no results")
            success = False
            
    return success


def main():
    parser = argparse.ArgumentParser(description="Seed Aesthetic RAG data")
    parser.add_argument("--verify", action="store_true", help="Only verify existing data")
    args = parser.parse_args()

    logger.info("🎨 Aesthetic Director RAG Seeder")
    logger.info("=" * 50)

    # Get AD (Aesthetic Director) dimension RAG
    try:
        rag = get_dimension_rag("AD")
    except Exception as e:
        logger.error(f"Failed to initialize AD RAG: {e}")
        logger.info("Make sure Qdrant is running (docker start crebit-qdrant)")
        sys.exit(1)

    if args.verify:
        success = verify_indexing(rag)
        sys.exit(0 if success else 1)

    # Ensure collection exists
    logger.info("\n📁 Ensuring AD collection exists...")
    if not rag.ensure_collection():
        logger.error("Failed to create/verify AD collection")
        sys.exit(1)
    logger.info("  ✓ Collection ready")

    # Index auteur styles
    logger.info("\n📝 Indexing auteur style guides...")
    auteur_count = index_auteur_styles(rag)
    logger.info(f"  Total auteurs indexed: {auteur_count}")

    # Index VDG standards
    logger.info("\n📐 Indexing VDG standards...")
    vdg_count = index_vdg_standards(rag)
    logger.info(f"  Total VDG standards indexed: {vdg_count}")

    # Index 4-Layer Source Packs
    logger.info("\n🎬 Indexing 4-Layer Source Packs...")
    
    total_layer0 = 0
    total_layer1 = 0
    total_layer2 = 0
    
    # Iterate over all subdirectories in SOURCE_PACKS_DIR
    if SOURCE_PACKS_DIR.exists():
        for auteur_dir in SOURCE_PACKS_DIR.iterdir():
            if auteur_dir.is_dir() and not auteur_dir.name.startswith('.'):
                auteur_name = auteur_dir.name
                logger.info(f"\n  Found Source Pack: {auteur_name}")
                
                # Index Layer0
                l0 = index_layer0_shot_analysis(rag, auteur_name)
                total_layer0 += l0
                logger.info(f"    - Layer0: {l0} docs")
                
                # Index Layer1
                l1 = index_layer1_logic_persona(rag, auteur_name)
                total_layer1 += l1
                logger.info(f"    - Layer1: {l1} docs")
                
                # Index Layer2
                l2 = index_layer2_variation_guide(rag, auteur_name)
                total_layer2 += l2
                logger.info(f"    - Layer2: {l2} docs")

    total_layered_docs = total_layer0 + total_layer1 + total_layer2

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info(f"✅ Indexing complete!")
    logger.info(f"   - Auteur styles: {auteur_count}")
    logger.info(f"   - VDG standards: {vdg_count}")
    logger.info(f"   - 4-Layer Source Packs:")
    logger.info(f"     Layer0 (Shots):   {total_layer0}")
    logger.info(f"     Layer1 (Vectors): {total_layer1}")
    logger.info(f"     Layer2 (Guides):  {total_layer2}")
    logger.info(f"   - Total documents: {auteur_count + vdg_count + total_layered_docs}")

    # Verify
    verify_indexing(rag)


if __name__ == "__main__":
    main()
