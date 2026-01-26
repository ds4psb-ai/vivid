#!/usr/bin/env python3
"""Seed RAG from Tavily Research Pipeline.

This script runs the research pipeline and indexes results into Qdrant.

Usage:
    # Research a specific auteur
    python scripts/seed_research_rag.py --auteur bong

    # Research with custom query
    python scripts/seed_research_rag.py --query "cinematography techniques" --dimension 4D

    # Research all auteurs (rate limited)
    python scripts/seed_research_rag.py --all-auteurs

    # Dry run (no indexing)
    python scripts/seed_research_rag.py --auteur wong --dry-run
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.research_pipeline import (
    ResearchDocument,
    ResearchPipeline,
    ResearchResult,
    research_auteur,
    research_dimension,
)
from app.rag.tier1_dimension_rag import DimensionRAG, get_dimension_rag

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Default research topics per dimension
DIMENSION_TOPICS = {
    "1D": [
        "video generation prompt engineering",
        "text to video prompt best practices",
        "AI video prompt examples",
        "VEO prompt guide",
        "Runway Gen-3 prompting",
    ],
    "2D": [
        "storyboard narrative structure",
        "visual storytelling techniques",
        "screenplay scene breakdown",
        "story beat mapping",
    ],
    "4D": [
        "film analysis framework",
        "cinematography analysis methods",
        "shot composition analysis",
        "film visual language",
    ],
    "5D": [
        "video generation camera movement",
        "AI video motion control",
        "VEO camera techniques",
        "video transition effects",
    ],
    "6D": [
        "film sound design principles",
        "movie score composition",
        "diegetic non-diegetic sound",
        "audio visual synchronization",
    ],
    "AD": [
        "aesthetic film theory",
        "visual style analysis",
        "color grading philosophy",
        "cinematographer techniques",
    ],
}

# Auteur-specific research topics
AUTEUR_TOPICS = [
    "cinematography style",
    "visual techniques analysis",
    "signature shots",
    "lighting approach",
    "camera movement style",
    "color palette film",
    "editing rhythm pacing",
]


def index_documents_to_rag(
    documents: List[ResearchDocument],
    dimension: str,
    dry_run: bool = False,
) -> int:
    """Index research documents into Qdrant.

    Args:
        documents: Research documents to index
        dimension: Target dimension (4D, 5D, etc.)
        dry_run: If True, don't actually index

    Returns:
        Number of documents indexed
    """
    if dry_run:
        logger.info(f"[DRY RUN] Would index {len(documents)} documents to {dimension}")
        return len(documents)

    rag = get_dimension_rag(dimension)
    rag.ensure_collection()

    indexed = 0
    for doc in documents:
        try:
            # Prepare metadata
            metadata = {
                "source": "tavily_research",
                "url": doc.url,
                "domain": doc.source_domain,
                "quality_tier": doc.quality_tier,
                "license_status": doc.license_status,
                "fetched_at": doc.fetched_at,
                "relevance_score": doc.relevance_score,
            }

            if doc.auteur_key:
                metadata["auteur_key"] = doc.auteur_key
            if doc.tags:
                metadata["tags"] = doc.tags

            # Index the document
            rag.index_document(
                doc_id=doc.id,
                content=f"{doc.title}\n\n{doc.content}",
                metadata=metadata,
            )
            indexed += 1

        except Exception as e:
            logger.error(f"Failed to index {doc.id}: {e}")

    logger.info(f"Indexed {indexed}/{len(documents)} documents to {dimension}")
    return indexed


async def research_and_seed_auteur(
    auteur_key: str,
    dimension: str = "4D",
    max_results: int = 5,
    dry_run: bool = False,
) -> dict:
    """Research an auteur and seed to RAG.

    Args:
        auteur_key: Auteur identifier (bong, epoch, etc.)
        dimension: Target dimension
        max_results: Max results per topic
        dry_run: If True, don't actually index

    Returns:
        Stats dictionary
    """
    logger.info(f"Researching auteur: {auteur_key}")

    results = await research_auteur(
        auteur_key=auteur_key,
        topics=AUTEUR_TOPICS,
        max_results_per_topic=max_results,
    )

    # Collect all documents
    all_docs = []
    for result in results:
        all_docs.extend(result.documents)

    # Index to RAG
    indexed = index_documents_to_rag(all_docs, dimension, dry_run)

    return {
        "auteur_key": auteur_key,
        "topics_searched": len(results),
        "documents_found": sum(r.total_found for r in results),
        "documents_saved": len(all_docs),
        "documents_indexed": indexed,
    }


async def research_and_seed_dimension(
    dimension: str,
    custom_queries: Optional[List[str]] = None,
    max_results: int = 5,
    dry_run: bool = False,
) -> dict:
    """Research content for a dimension and seed to RAG.

    Args:
        dimension: Target dimension (1D, 2D, 4D, etc.)
        custom_queries: Optional custom queries (uses defaults if not provided)
        max_results: Max results per query
        dry_run: If True, don't actually index

    Returns:
        Stats dictionary
    """
    queries = custom_queries or DIMENSION_TOPICS.get(dimension, [])
    if not queries:
        logger.warning(f"No topics defined for dimension {dimension}")
        return {"dimension": dimension, "error": "No topics defined"}

    logger.info(f"Researching dimension: {dimension} ({len(queries)} queries)")

    results = await research_dimension(
        dimension=dimension,
        queries=queries,
        max_results_per_query=max_results,
    )

    # Collect all documents
    all_docs = []
    for result in results:
        all_docs.extend(result.documents)

    # Index to RAG
    indexed = index_documents_to_rag(all_docs, dimension, dry_run)

    return {
        "dimension": dimension,
        "queries_searched": len(results),
        "documents_found": sum(r.total_found for r in results),
        "documents_saved": len(all_docs),
        "documents_indexed": indexed,
    }


async def research_custom_query(
    query: str,
    dimension: str,
    auteur_key: Optional[str] = None,
    max_results: int = 10,
    dry_run: bool = False,
) -> dict:
    """Research a custom query and seed to RAG.

    Args:
        query: Search query
        dimension: Target dimension
        auteur_key: Optional auteur key
        max_results: Max results
        dry_run: If True, don't actually index

    Returns:
        Stats dictionary
    """
    pipeline = ResearchPipeline()
    result = await pipeline.research(
        query=query,
        auteur_key=auteur_key,
        dimension=dimension,
        max_results=max_results,
    )

    indexed = index_documents_to_rag(result.documents, dimension, dry_run)

    return {
        "query": query,
        "dimension": dimension,
        "auteur_key": auteur_key,
        "documents_found": result.total_found,
        "documents_saved": len(result.documents),
        "documents_indexed": indexed,
        "high_quality": result.high_quality_count,
        "permissive_license": result.permissive_license_count,
    }


async def research_all_auteurs(
    max_results: int = 3,
    dry_run: bool = False,
) -> List[dict]:
    """Research all known auteurs.

    Args:
        max_results: Max results per topic per auteur
        dry_run: If True, don't actually index

    Returns:
        List of stats for each auteur
    """
    auteurs = ["bong", "epoch", "wong", "voltage", "abyss", "park"]
    results = []

    for auteur in auteurs:
        logger.info(f"\n{'='*50}")
        logger.info(f"Processing auteur: {auteur}")
        logger.info(f"{'='*50}")

        stats = await research_and_seed_auteur(
            auteur_key=auteur,
            max_results=max_results,
            dry_run=dry_run,
        )
        results.append(stats)

        # Rate limiting between auteurs
        logger.info("Waiting 5 seconds before next auteur...")
        await asyncio.sleep(5)

    return results


def print_stats(stats: dict | List[dict]) -> None:
    """Print research stats."""
    if isinstance(stats, list):
        print("\n" + "=" * 60)
        print("RESEARCH SUMMARY")
        print("=" * 60)
        total_indexed = 0
        for s in stats:
            key = s.get("auteur_key") or s.get("dimension") or s.get("query", "unknown")
            indexed = s.get("documents_indexed", 0)
            total_indexed += indexed
            print(f"  {key}: {indexed} documents indexed")
        print("-" * 60)
        print(f"  TOTAL: {total_indexed} documents indexed")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("RESEARCH RESULT")
        print("=" * 60)
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print("=" * 60)


async def main():
    parser = argparse.ArgumentParser(
        description="Seed RAG from Tavily Research Pipeline"
    )

    # Research mode
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--auteur",
        type=str,
        help="Research a specific auteur (bong, epoch, wong, etc.)",
    )
    mode_group.add_argument(
        "--dimension",
        type=str,
        help="Research content for a dimension (1D, 2D, 4D, 5D, 6D, AD)",
    )
    mode_group.add_argument(
        "--query",
        type=str,
        help="Research a custom query",
    )
    mode_group.add_argument(
        "--all-auteurs",
        action="store_true",
        help="Research all known auteurs",
    )

    # Options
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Max results per query/topic (default: 5)",
    )
    parser.add_argument(
        "--target-dimension",
        type=str,
        default="4D",
        help="Target dimension for indexing (default: 4D)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually index to Qdrant",
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("TAVILY RESEARCH PIPELINE → RAG SEEDER")
    print("=" * 60)
    print(f"Mode: ", end="")
    if args.auteur:
        print(f"Auteur research ({args.auteur})")
    elif args.dimension:
        print(f"Dimension research ({args.dimension})")
    elif args.query:
        print(f"Custom query")
    elif args.all_auteurs:
        print(f"All auteurs")
    print(f"Max results: {args.max_results}")
    print(f"Dry run: {args.dry_run}")
    print("=" * 60 + "\n")

    try:
        if args.auteur:
            stats = await research_and_seed_auteur(
                auteur_key=args.auteur,
                dimension=args.target_dimension,
                max_results=args.max_results,
                dry_run=args.dry_run,
            )
        elif args.dimension:
            stats = await research_and_seed_dimension(
                dimension=args.dimension,
                max_results=args.max_results,
                dry_run=args.dry_run,
            )
        elif args.query:
            stats = await research_custom_query(
                query=args.query,
                dimension=args.target_dimension,
                max_results=args.max_results,
                dry_run=args.dry_run,
            )
        elif args.all_auteurs:
            stats = await research_all_auteurs(
                max_results=args.max_results,
                dry_run=args.dry_run,
            )

        print_stats(stats)

    except Exception as e:
        logger.error(f"Research failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
