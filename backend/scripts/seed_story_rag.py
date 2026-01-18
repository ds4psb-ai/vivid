#!/usr/bin/env python
"""Seed Story (Story Architect) RAG collection into Qdrant 2D.

Indexes data for narrative structure and story architecture:
- Three-act structure
- Hero's Journey (Monomyth)
- Save the Cat beat sheet
- Kishotenketsu (East Asian structure)
- Character arc patterns

Usage:
    cd backend
    source venv/bin/activate
    python scripts/seed_story_rag.py

    # Verify collection
    python scripts/seed_story_rag.py --verify

2026 Best Practices Applied:
- Batch upsert for efficiency
- Rich content with structured metadata
- Consistent doc_id patterns for deduplication
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
SOURCE_PACKS_DIR = Path(__file__).parent.parent.parent / "data" / "source_packs"


def seed_story_structures() -> int:
    """Seed 2D collection from story_structures.json.

    Returns:
        Number of documents indexed
    """
    logger.info("\n📖 Seeding Story (2D) from story_structures.json...")
    rag = get_dimension_rag("2D")
    rag.ensure_collection()
    count = 0

    story_path = RAG_DOCS_DIR / "story" / "story_structures.json"
    if not story_path.exists():
        logger.warning(f"  ⚠️ story_structures.json not found at {story_path}")
        return 0

    try:
        with open(story_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Index narrative structures
        structures = data.get("structures", {})
        for struct_key, struct_data in structures.items():
            content_parts = [
                f"Narrative Structure: {struct_data.get('name', struct_key)}",
                f"Description: {struct_data.get('description', '')}",
                "",
            ]

            # Three-act structure
            if "acts" in struct_data:
                content_parts.append("Acts:")
                for act_key, act_data in struct_data["acts"].items():
                    content_parts.append(f"  {act_data.get('name', act_key)} ({act_data.get('percentage', '')})")
                    for element in act_data.get("elements", []):
                        content_parts.append(f"    - {element}")

            # Hero's Journey stages
            if "stages" in struct_data:
                content_parts.append("Stages:")
                for phase_data in struct_data["stages"]:
                    content_parts.append(f"  {phase_data.get('phase', '')}:")
                    for stage in phase_data.get("stages", []):
                        content_parts.append(f"    - {stage}")

            # Save the Cat beats
            if "beats" in struct_data:
                content_parts.append("Beats:")
                for beat in struct_data["beats"]:
                    page_info = f" (Page {beat.get('page', '')})" if beat.get('page') else ""
                    content_parts.append(f"  - {beat.get('beat', '')}{page_info}: {beat.get('description', '')}")

            content = "\n".join(content_parts)
            doc_id = f"story_structure_{struct_key}"
            metadata = {
                "app_key": "dimension.story.architect",
                "content_type": "narrative_structure",
                "structure_type": struct_key,
                "source": "story_structures.json",
                "dimension": "2D",
            }

            if rag.index_document(doc_id, content, metadata):
                logger.info(f"  ✓ Structure: {struct_data.get('name', struct_key)}")
                count += 1

        # Index character arcs
        character_arcs = data.get("character_arcs", {})
        if character_arcs:
            content_parts = ["Character Arc Patterns:", ""]
            for arc_key, arc_data in character_arcs.items():
                content_parts.append(f"{arc_data.get('name', arc_key)}:")
                if "stages" in arc_data:
                    for stage in arc_data["stages"]:
                        content_parts.append(f"  - {stage}")
                if "description" in arc_data:
                    content_parts.append(f"  Description: {arc_data['description']}")
                content_parts.append("")

            content = "\n".join(content_parts)
            doc_id = "story_character_arcs"
            metadata = {
                "app_key": "dimension.story.architect",
                "content_type": "character_arc",
                "source": "story_structures.json",
                "dimension": "2D",
            }

            if rag.index_document(doc_id, content, metadata):
                logger.info("  ✓ Character arcs")
                count += 1

        # Index scene structure
        scene_structure = data.get("scene_structure", {})
        if scene_structure:
            content_parts = ["Scene Structure:", ""]
            for key, value in scene_structure.items():
                content_parts.append(f"  {key}: {value}")

            content = "\n".join(content_parts)
            doc_id = "story_scene_structure"
            metadata = {
                "app_key": "dimension.story.architect",
                "content_type": "scene_structure",
                "source": "story_structures.json",
                "dimension": "2D",
            }

            if rag.index_document(doc_id, content, metadata):
                logger.info("  ✓ Scene structure")
                count += 1

    except Exception as e:
        logger.error(f"  ✗ Failed to process story_structures.json: {e}")

    return count


def seed_story_from_auteur_analysis() -> int:
    """Seed story data from auteur thematic analysis in source_packs.

    Returns:
        Number of documents indexed
    """
    logger.info("\n📖 Seeding Story from auteur source packs...")
    rag = get_dimension_rag("2D")
    rag.ensure_collection()
    count = 0

    # Look for story/narrative-related files in source packs
    for auteur_dir in SOURCE_PACKS_DIR.iterdir():
        if not auteur_dir.is_dir() or auteur_dir.name.startswith('.'):
            continue

        auteur = auteur_dir.name

        # Find storyboard files
        for json_file in auteur_dir.glob("*storyboard*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                content_parts = [f"Auteur: {auteur}"]

                # Extract storyboard content
                if "content" in data:
                    content_data = data["content"]
                    if isinstance(content_data, dict):
                        for key, value in content_data.items():
                            if isinstance(value, list):
                                content_parts.append(f"{key}: {', '.join(str(v) for v in value)}")
                            else:
                                content_parts.append(f"{key}: {value}")

                content = "\n".join(content_parts)
                doc_id = f"story_auteur_{auteur}_{json_file.stem}"
                metadata = {
                    "app_key": "dimension.story.architect",
                    "content_type": "auteur_storyboard",
                    "auteur": auteur,
                    "source": json_file.name,
                    "dimension": "2D",
                }

                if rag.index_document(doc_id, content, metadata):
                    logger.info(f"  ✓ {auteur}: {json_file.name}")
                    count += 1
            except Exception as e:
                logger.error(f"  ✗ Failed {json_file}: {e}")

        # Find genre blending files (narrative patterns)
        for json_file in auteur_dir.glob("*genre*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                content_parts = [f"Auteur: {auteur}", f"Title: {data.get('title', '')}"]

                if "content" in data:
                    content_data = data["content"]
                    if isinstance(content_data, dict):
                        for key, value in content_data.items():
                            if isinstance(value, list):
                                content_parts.append(f"{key}: {', '.join(str(v) for v in value)}")
                            else:
                                content_parts.append(f"{key}: {value}")

                content = "\n".join(content_parts)
                doc_id = f"story_genre_{auteur}_{json_file.stem}"
                metadata = {
                    "app_key": "dimension.story.architect",
                    "content_type": "genre_blending",
                    "auteur": auteur,
                    "source": json_file.name,
                    "dimension": "2D",
                }

                if rag.index_document(doc_id, content, metadata):
                    logger.info(f"  ✓ {auteur}: {json_file.name}")
                    count += 1
            except Exception as e:
                logger.error(f"  ✗ Failed {json_file}: {e}")

    return count


def verify_story_collection() -> None:
    """Verify 2D (Story) collection contents."""
    logger.info("\n🔍 Verifying Story (2D) collection...")
    rag = get_dimension_rag("2D")

    try:
        stats = rag.get_collection_stats()
        if stats:
            logger.info(f"  Collection: {rag.collection_name}")
            logger.info(f"  Points: {stats.get('points_count', 0)}")
            logger.info(f"  Status: {stats.get('status', 'unknown')}")
        else:
            logger.warning("  Collection not found or empty")
    except Exception as e:
        logger.error(f"  Verification failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Seed Story (2D) RAG collection")
    parser.add_argument("--verify", action="store_true", help="Verify collection only")
    args = parser.parse_args()

    if args.verify:
        verify_story_collection()
        return

    total = 0

    # Seed from story structures
    total += seed_story_structures()

    # Seed from auteur analysis
    total += seed_story_from_auteur_analysis()

    logger.info(f"\n✅ Total Story documents indexed: {total}")

    # Verify after seeding
    verify_story_collection()


if __name__ == "__main__":
    main()
