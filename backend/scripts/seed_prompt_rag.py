#!/usr/bin/env python
"""Seed 1D (Prompt Alchemy) RAG collection into Qdrant.

Indexes data for prompt engineering patterns and templates:
- Platform-specific prompt patterns (VEO, Runway, Kling, Sora)
- Cinema-to-prompt conversion rules
- Auteur text style characteristics

Usage:
    cd backend
    source venv/bin/activate
    python scripts/seed_prompt_rag.py

    # Verify collection
    python scripts/seed_prompt_rag.py --verify

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


def seed_1d_from_prompt_patterns() -> int:
    """Seed 1D collection from prompt_patterns.json.

    Returns:
        Number of documents indexed
    """
    logger.info("\n✍️ Seeding 1D (Prompt Alchemy) from prompt_patterns.json...")
    rag = get_dimension_rag("1D")
    rag.ensure_collection()
    count = 0

    prompt_path = RAG_DOCS_DIR / "prompt" / "prompt_patterns.json"
    if not prompt_path.exists():
        logger.warning(f"  ⚠️ prompt_patterns.json not found at {prompt_path}")
        return 0

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Index platform patterns
        patterns = data.get("patterns", {})
        for platform, pattern_data in patterns.items():
            content_parts = [
                f"Platform: {pattern_data.get('platform', platform)}",
                "",
                "Structure:",
            ]
            for key, desc in pattern_data.get("structure", {}).items():
                content_parts.append(f"  - {key}: {desc}")

            content_parts.extend(["", "Best Practices:"])
            for practice in pattern_data.get("best_practices", []):
                content_parts.append(f"  - {practice}")

            if "example" in pattern_data:
                content_parts.extend(["", f"Example: {pattern_data['example']}"])

            content = "\n".join(content_parts)
            doc_id = f"1d_prompt_pattern_{platform}"
            metadata = {
                "app_key": "dimension.1d.prompt",
                "content_type": "prompt_pattern",
                "platform": platform,
                "source": "prompt_patterns.json",
                "dimension": "1D",
            }

            if rag.index_document(doc_id, content, metadata):
                logger.info(f"  ✓ Platform pattern: {platform}")
                count += 1

        # Index cinema-to-prompt rules
        rules = data.get("cinema_to_prompt_rules", {})

        # Shot types
        shot_types = rules.get("shot_types", {})
        if shot_types:
            content_parts = ["Cinema Shot Types to Prompt Keywords:", ""]
            for shot, prompt_equiv in shot_types.items():
                content_parts.append(f"  {shot}: {prompt_equiv}")

            content = "\n".join(content_parts)
            doc_id = "1d_cinema_shot_types"
            metadata = {
                "app_key": "dimension.1d.prompt",
                "content_type": "cinema_rules",
                "rule_type": "shot_types",
                "source": "prompt_patterns.json",
                "dimension": "1D",
            }

            if rag.index_document(doc_id, content, metadata):
                logger.info("  ✓ Cinema rules: shot_types")
                count += 1

        # Camera movements
        camera_moves = rules.get("camera_movements", {})
        if camera_moves:
            content_parts = ["Camera Movement to Prompt Keywords:", ""]
            for move, prompt_equiv in camera_moves.items():
                content_parts.append(f"  {move}: {prompt_equiv}")

            content = "\n".join(content_parts)
            doc_id = "1d_cinema_camera_movements"
            metadata = {
                "app_key": "dimension.1d.prompt",
                "content_type": "cinema_rules",
                "rule_type": "camera_movements",
                "source": "prompt_patterns.json",
                "dimension": "1D",
            }

            if rag.index_document(doc_id, content, metadata):
                logger.info("  ✓ Cinema rules: camera_movements")
                count += 1

        # Lighting keys
        lighting_keys = rules.get("lighting_keys", {})
        if lighting_keys:
            content_parts = ["Lighting Keys to Prompt Keywords:", ""]
            for key, prompt_equiv in lighting_keys.items():
                content_parts.append(f"  {key}: {prompt_equiv}")

            content = "\n".join(content_parts)
            doc_id = "1d_cinema_lighting_keys"
            metadata = {
                "app_key": "dimension.1d.prompt",
                "content_type": "cinema_rules",
                "rule_type": "lighting_keys",
                "source": "prompt_patterns.json",
                "dimension": "1D",
            }

            if rag.index_document(doc_id, content, metadata):
                logger.info("  ✓ Cinema rules: lighting_keys")
                count += 1

    except Exception as e:
        logger.error(f"  ✗ Failed to process prompt_patterns.json: {e}")

    return count


def seed_1d_from_auteur_prompts() -> int:
    """Seed 1D from auteur-specific prompt data in source_packs.

    Returns:
        Number of documents indexed
    """
    logger.info("\n✍️ Seeding 1D from auteur source packs...")
    rag = get_dimension_rag("1D")
    rag.ensure_collection()
    count = 0

    # Look for prompt-related files in source packs
    for auteur_dir in SOURCE_PACKS_DIR.iterdir():
        if not auteur_dir.is_dir() or auteur_dir.name.startswith('.'):
            continue

        auteur = auteur_dir.name

        # Find VEO prompt files
        for json_file in auteur_dir.glob("*veo*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                content_parts = [f"Auteur: {auteur}"]

                # Extract VEO keywords
                if "content" in data and "veo_prompt_keywords" in data.get("content", {}):
                    keywords = data["content"]["veo_prompt_keywords"]
                    content_parts.append(f"VEO Keywords: {', '.join(keywords)}")

                # Extract prompt patterns
                if "veo_prompt_pattern" in data.get("content", {}):
                    content_parts.append(f"Pattern: {data['content']['veo_prompt_pattern']}")

                content = "\n".join(content_parts)
                doc_id = f"1d_auteur_veo_{auteur}_{json_file.stem}"
                metadata = {
                    "app_key": "dimension.1d.prompt",
                    "content_type": "auteur_veo",
                    "auteur": auteur,
                    "source": json_file.name,
                    "dimension": "1D",
                }

                if rag.index_document(doc_id, content, metadata):
                    logger.info(f"  ✓ {auteur}: {json_file.name}")
                    count += 1
            except Exception as e:
                logger.error(f"  ✗ Failed {json_file}: {e}")

    return count


def verify_1d_collection() -> None:
    """Verify 1D collection contents."""
    logger.info("\n🔍 Verifying 1D collection...")
    rag = get_dimension_rag("1D")

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
    parser = argparse.ArgumentParser(description="Seed 1D (Prompt Alchemy) RAG collection")
    parser.add_argument("--verify", action="store_true", help="Verify collection only")
    args = parser.parse_args()

    if args.verify:
        verify_1d_collection()
        return

    total = 0

    # Seed from prompt patterns
    total += seed_1d_from_prompt_patterns()

    # Seed from auteur prompts
    total += seed_1d_from_auteur_prompts()

    logger.info(f"\n✅ Total 1D documents indexed: {total}")

    # Verify after seeding
    verify_1d_collection()


if __name__ == "__main__":
    main()
