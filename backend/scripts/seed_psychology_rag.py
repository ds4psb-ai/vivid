#!/usr/bin/env python
"""Seed Psychology RAG data into Qdrant.

P1: Dataset-level routing을 위한 심리학 데이터 시딩.
각 문서에 dataset_id를 포함하여 라우팅 가능하게 함.

Usage:
    cd backend
    source venv/bin/activate
    python scripts/seed_psychology_rag.py

    # Verify indexing
    python scripts/seed_psychology_rag.py --verify
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.tier1_dimension_rag import get_dimension_rag

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Data paths
RAG_DOCS_DIR = Path(__file__).parent.parent / "data" / "rag_docs"
PSYCHOLOGY_DIR = RAG_DOCS_DIR / "psychology"

# Dataset files mapping
DATASET_FILES = {
    "psych_core": PSYCHOLOGY_DIR / "psych_core.json",
    "attachment": PSYCHOLOGY_DIR / "attachment.json",
    "mbti": PSYCHOLOGY_DIR / "mbti.json",
    "enneagram": PSYCHOLOGY_DIR / "enneagram.json",
}


def index_psychology_dataset(rag, dataset_id: str, file_path: Path) -> int:
    """Index a psychology dataset.
    
    Args:
        rag: Dimension RAG instance
        dataset_id: Dataset identifier
        file_path: Path to JSON file
        
    Returns:
        Number of documents indexed
    """
    if not file_path.exists():
        logger.warning(f"Dataset file not found: {file_path}")
        return 0
    
    with open(file_path, "r", encoding="utf-8") as f:
        documents = json.load(f)
    
    count = 0
    for doc in documents:
        doc_id = doc.get("id", f"{dataset_id}_{count}")
        
        # Build content from document fields
        content = f"""
{doc.get('title', '')}

{doc.get('content', '')}

Source: {doc.get('source', 'Unknown')}
Tags: {', '.join(doc.get('dataset_tags', []))}
        """.strip()
        
        # P1: Include dataset_id in metadata for routing
        metadata = {
            "app_key": "dimension.persona.analyze",
            "content_type": "psychology",
            "dataset_id": dataset_id,  # P1: 핵심 필드
            "dataset_tags": doc.get("dataset_tags", []),
            "source": doc.get("source", "Unknown"),
            "author": doc.get("author", "Unknown"),
        }
        
        if rag.index_document(doc_id, content, metadata):
            logger.info(f"  ✓ Indexed [{dataset_id}]: {doc.get('title', doc_id)}")
            count += 1
        else:
            logger.error(f"  ✗ Failed [{dataset_id}]: {doc.get('title', doc_id)}")
    
    return count


def seed_all_datasets() -> Dict[str, int]:
    """Seed all psychology datasets.
    
    Returns:
        Dict mapping dataset_id to indexed count
    """
    # Get RAG for AI dimension (psychology/persona data)
    rag = get_dimension_rag("AI")
    
    results = {}
    total = 0
    
    logger.info("=" * 60)
    logger.info("Seeding Psychology RAG Data (P1: Dataset Routing)")
    logger.info("=" * 60)
    
    for dataset_id, file_path in DATASET_FILES.items():
        logger.info(f"\n📚 Dataset: {dataset_id}")
        count = index_psychology_dataset(rag, dataset_id, file_path)
        results[dataset_id] = count
        total += count
        logger.info(f"   Indexed: {count} documents")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Total indexed: {total} documents")
    logger.info("=" * 60)
    
    return results


def verify_datasets() -> None:
    """Verify indexed datasets by querying."""
    rag = get_dimension_rag("AI")
    
    logger.info("=" * 60)
    logger.info("Verifying Psychology RAG Data")
    logger.info("=" * 60)
    
    test_queries = [
        ("애착 이론 불안형", "attachment"),
        ("MBTI INTJ 성격", "mbti"),
        ("심리학 동기부여", "psych_core"),
    ]
    
    for query, expected_dataset in test_queries:
        logger.info(f"\n🔍 Query: '{query}'")
        logger.info(f"   Expected dataset: {expected_dataset}")
        
        # Search with dataset filter
        results = rag.search(
            query=query,
            limit=2,
            metadata_filters={"dataset_id": expected_dataset}
        )
        
        if results:
            for r in results:
                logger.info(f"   ✓ Found: {r.get('content', '')[:80]}...")
        else:
            logger.warning(f"   ✗ No results for {expected_dataset}")


def main():
    parser = argparse.ArgumentParser(description="Seed Psychology RAG data")
    parser.add_argument("--verify", action="store_true", help="Verify indexed data")
    args = parser.parse_args()
    
    if args.verify:
        verify_datasets()
    else:
        results = seed_all_datasets()
        
        # Summary
        logger.info("\n📊 Summary:")
        for dataset_id, count in results.items():
            status = "✓" if count > 0 else "✗"
            logger.info(f"   {status} {dataset_id}: {count} docs")


if __name__ == "__main__":
    main()
