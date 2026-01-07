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


def verify_indexing(rag) -> bool:
    """Verify that data was indexed correctly."""
    logger.info("\n📊 Verifying AD collection...")

    # Test search for Bong Joon-ho (lower min_score for mock embeddings)
    results = rag.search("봉준호 시각적 스타일 구도", limit=3, min_score=0.0)
    if results:
        logger.info(f"  ✓ Search returned {len(results)} results")
        for r in results:
            logger.info(f"    - [{r['score']:.3f}] {r.get('metadata', {}).get('auteur_name', r['doc_id'][:30])}")
        return True
    else:
        logger.warning("  ✗ Search returned no results")
        return False


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

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info(f"✅ Indexing complete!")
    logger.info(f"   - Auteur styles: {auteur_count}")
    logger.info(f"   - VDG standards: {vdg_count}")
    logger.info(f"   - Total documents: {auteur_count + vdg_count}")

    # Verify
    verify_indexing(rag)


if __name__ == "__main__":
    main()
