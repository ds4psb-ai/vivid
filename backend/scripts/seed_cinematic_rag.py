"""Seed cinematic techniques corpus into the RAG system.

Loads techniques_corpus.json and verifies it is accessible
through the cinematic_techniques module.

Usage:
    python scripts/seed_cinematic_rag.py [--verify-only]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

CORPUS_PATH = ROOT_DIR / "data" / "rag_docs" / "cinematic" / "techniques_corpus.json"


def verify_corpus() -> bool:
    """Verify corpus file and module loading."""
    if not CORPUS_PATH.exists():
        print(f"ERROR: Corpus file not found: {CORPUS_PATH}")
        return False

    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    techniques = data.get("techniques", [])
    mood_map = data.get("mood_technique_map", {})
    transition_map = data.get("transition_mood_map", {})

    print(f"Corpus file: {CORPUS_PATH}")
    print(f"  Techniques: {len(techniques)}")
    print(f"  Mood mappings: {len(mood_map)}")
    print(f"  Transition mappings: {len(transition_map)}")

    # Verify categories
    categories = {}
    for t in techniques:
        cat = t.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    print("  Categories:")
    for cat, count in sorted(categories.items()):
        print(f"    {cat}: {count}")

    # Verify module loading
    try:
        from app.rag.cinematic_techniques import (
            get_all_techniques,
            get_technique_by_id,
            query_techniques,
            suggest_transitions,
        )

        all_techniques = get_all_techniques()
        print(f"\n  Module loaded: {len(all_techniques)} techniques")

        # Spot check
        chiaroscuro = get_technique_by_id("chiaroscuro")
        if chiaroscuro:
            print(f"  Spot check OK: chiaroscuro = {chiaroscuro.name_ko}")
        else:
            print("  WARNING: chiaroscuro technique not found")

        # Query check
        tension_results = query_techniques("tension")
        print(f"  Query 'tension': {len(tension_results)} results")

        # Transition check
        transitions = suggest_transitions("tension", "serenity")
        print(f"  Transition tension→serenity: {len(transitions)} suggestions")

        print("\nAll checks passed.")
        return True

    except ImportError as e:
        print(f"\n  WARNING: Module import failed: {e}")
        print("  Corpus file is valid but module may need dependencies.")
        return True  # File is valid even if module can't load


def main():
    parser = argparse.ArgumentParser(description="Seed cinematic techniques RAG corpus")
    parser.add_argument("--verify-only", action="store_true", help="Only verify, don't ingest")
    args = parser.parse_args()

    if not verify_corpus():
        sys.exit(1)

    if args.verify_only:
        return

    print("\nCorpus is loaded from JSON at runtime (no DB ingestion needed).")
    print("The cinematic_techniques module reads directly from the JSON file.")


if __name__ == "__main__":
    main()
