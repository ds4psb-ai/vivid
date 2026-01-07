#!/usr/bin/env python
"""RAG Corpus Setup Script.

Vertex AI RAG Engine에 Corpus 생성 및 문서 인덱싱.

Usage:
    # GCS 버킷에 문서 업로드
    python scripts/setup_rag_corpus.py upload

    # Corpus 생성
    python scripts/setup_rag_corpus.py create-corpus auteur_dna

    # 문서 인덱싱
    python scripts/setup_rag_corpus.py index auteur_dna

    # 전체 설정 (upload + create + index)
    python scripts/setup_rag_corpus.py setup-all

    # Corpus 목록 확인
    python scripts/setup_rag_corpus.py list

    # 테스트 쿼리
    python scripts/setup_rag_corpus.py query "봉준호 감독의 시각적 특징"
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

# ============================================================================
# Constants
# ============================================================================

PROJECT_ID = settings.GCP_PROJECT_ID
GCS_BUCKET = settings.GCS_BUCKET
LOCATION = settings.GCP_LOCATION

# Local document paths
RAG_DOCS_DIR = Path(__file__).parent.parent / "data" / "rag_docs"

# Corpus definitions with local file mappings
CORPUS_DEFINITIONS = {
    "auteur_dna": {
        "display_name": "Auteur DNA Collection",
        "description": "거장 감독들의 시각적 문법, 스타일 DNA",
        "local_files": [
            "aesthetic/auteur_styles.json",
            "aesthetic/vdg_standards.json",
        ],
        "gcs_prefix": "auteur_dna",
    },
    "meta_invariants": {
        "display_name": "Cinematic Invariants",
        "description": "영화적 진리의 불변 법칙",
        "local_files": [
            "quality/quality_criteria.json",
        ],
        "gcs_prefix": "meta_invariants",
    },
    "meta_vdg": {
        "display_name": "Visual Design Grammar",
        "description": "시각적 디자인 문법 표준",
        "local_files": [
            "aesthetic/vdg_standards.json",
        ],
        "gcs_prefix": "meta_vdg",
    },
    "dim_1d_prompts": {
        "display_name": "1D Veo Prompt Templates",
        "description": "Veo 프롬프트 생성 가이드라인",
        "local_files": [
            "origin/veo_prompt_templates.json",
        ],
        "gcs_prefix": "dim_1d",
    },
    "dim_2d_storyboard": {
        "display_name": "2D Storyboard Guide",
        "description": "스토리보드 제작 원칙과 예시",
        "local_files": [
            "blueprint/storyboard_formats.json",
        ],
        "gcs_prefix": "dim_2d",
    },
}


# ============================================================================
# GCS Upload
# ============================================================================

def upload_to_gcs(local_path: Path, gcs_prefix: str) -> str:
    """Upload file to GCS.

    Args:
        local_path: Local file path
        gcs_prefix: GCS prefix (folder name)

    Returns:
        GCS URI (gs://bucket/path)
    """
    from google.cloud import storage

    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(GCS_BUCKET)

    gcs_path = f"{gcs_prefix}/{local_path.name}"
    blob = bucket.blob(gcs_path)

    # Upload file
    blob.upload_from_filename(str(local_path))
    gcs_uri = f"gs://{GCS_BUCKET}/{gcs_path}"

    print(f"  ✓ Uploaded: {local_path.name} → {gcs_uri}")
    return gcs_uri


def upload_corpus_documents(corpus_name: str) -> List[str]:
    """Upload all documents for a corpus.

    Args:
        corpus_name: Corpus name

    Returns:
        List of GCS URIs
    """
    if corpus_name not in CORPUS_DEFINITIONS:
        print(f"❌ Unknown corpus: {corpus_name}")
        return []

    corpus_def = CORPUS_DEFINITIONS[corpus_name]
    gcs_uris = []

    print(f"\n📤 Uploading documents for corpus: {corpus_name}")

    for local_file in corpus_def["local_files"]:
        local_path = RAG_DOCS_DIR / local_file
        if local_path.exists():
            gcs_uri = upload_to_gcs(local_path, corpus_def["gcs_prefix"])
            gcs_uris.append(gcs_uri)
        else:
            print(f"  ⚠️ File not found: {local_path}")

    return gcs_uris


def upload_all_documents() -> dict:
    """Upload all corpus documents to GCS.

    Returns:
        Dict mapping corpus_name → list of GCS URIs
    """
    print("=" * 60)
    print("📤 Uploading all RAG documents to GCS")
    print("=" * 60)

    all_uris = {}
    for corpus_name in CORPUS_DEFINITIONS:
        gcs_uris = upload_corpus_documents(corpus_name)
        all_uris[corpus_name] = gcs_uris

    print(f"\n✅ Upload complete. Total files: {sum(len(v) for v in all_uris.values())}")
    return all_uris


# ============================================================================
# Vertex AI RAG Corpus Management
# ============================================================================

async def create_corpus(corpus_name: str) -> Optional[str]:
    """Create a RAG Corpus in Vertex AI.

    Args:
        corpus_name: Corpus name

    Returns:
        Corpus resource name if successful
    """
    if corpus_name not in CORPUS_DEFINITIONS:
        print(f"❌ Unknown corpus: {corpus_name}")
        return None

    corpus_def = CORPUS_DEFINITIONS[corpus_name]

    try:
        import vertexai
        from vertexai import rag

        vertexai.init(project=PROJECT_ID, location=LOCATION)

        print(f"\n📦 Creating corpus: {corpus_name}")
        print(f"  Display name: {corpus_def['display_name']}")
        print(f"  Description: {corpus_def['description']}")

        # Create corpus (new API - no embedding_model_config, uses default)
        corpus = rag.create_corpus(
            display_name=corpus_def["display_name"],
            description=corpus_def["description"],
        )

        print(f"  ✓ Corpus created: {corpus.name}")
        return corpus.name

    except Exception as e:
        print(f"  ❌ Failed to create corpus: {e}")
        return None


async def index_documents(corpus_name: str, gcs_uris: Optional[List[str]] = None) -> bool:
    """Index documents in a RAG Corpus.

    Args:
        corpus_name: Corpus name
        gcs_uris: List of GCS URIs (if None, uploads first)

    Returns:
        True if successful
    """
    if corpus_name not in CORPUS_DEFINITIONS:
        print(f"❌ Unknown corpus: {corpus_name}")
        return False

    # Get or upload GCS URIs
    if not gcs_uris:
        gcs_uris = upload_corpus_documents(corpus_name)

    if not gcs_uris:
        print(f"❌ No documents to index for corpus: {corpus_name}")
        return False

    try:
        import vertexai
        from vertexai import rag

        vertexai.init(project=PROJECT_ID, location=LOCATION)

        # Find corpus
        corpus_def = CORPUS_DEFINITIONS[corpus_name]
        target_corpus = None

        for corpus in rag.list_corpora():
            if corpus_def["display_name"].lower() in corpus.display_name.lower():
                target_corpus = corpus
                break

        if not target_corpus:
            print(f"❌ Corpus not found: {corpus_name}. Create it first.")
            return False

        print(f"\n📚 Indexing documents in corpus: {corpus_name}")
        print(f"  Corpus: {target_corpus.name}")
        print(f"  Documents: {len(gcs_uris)}")

        # Chunking config (new API)
        transformation_config = rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(
                chunk_size=1024,
                chunk_overlap=200,
            )
        )

        # Import files
        response = rag.import_files(
            corpus_name=target_corpus.name,
            paths=gcs_uris,
            transformation_config=transformation_config,
        )

        print(f"  ✓ Documents indexed successfully")
        return True

    except Exception as e:
        print(f"  ❌ Failed to index documents: {e}")
        return False


async def list_corpora():
    """List all RAG Corpora."""
    try:
        import vertexai
        from vertexai import rag

        vertexai.init(project=PROJECT_ID, location=LOCATION)

        print("\n📋 RAG Corpora in project:")
        print("=" * 60)

        for corpus in rag.list_corpora():
            print(f"\n  Name: {corpus.name}")
            print(f"  Display: {corpus.display_name}")
            if corpus.description:
                print(f"  Description: {corpus.description}")

    except Exception as e:
        print(f"❌ Failed to list corpora: {e}")


async def test_query(query: str, corpus_name: Optional[str] = None):
    """Test query against RAG corpus.

    Args:
        query: Query string
        corpus_name: Optional corpus to query (default: all)
    """
    from app.rag import get_vertex_rag_service

    print(f"\n🔍 Testing query: {query}")
    if corpus_name:
        print(f"  Corpus: {corpus_name}")

    service = get_vertex_rag_service()
    result = await service.query(
        query=query,
        corpus_name=corpus_name,
        use_grounding=False,
    )

    print("\n📝 Result:")
    print("-" * 60)
    print(result.answer[:500] if result.answer else "(No answer)")
    print("-" * 60)
    print(f"Confidence: {result.confidence}")
    print(f"Sources: {len(result.sources)}")
    print(f"Time: {result.query_time_ms}ms")


async def setup_all():
    """Setup all corpora (upload + create + index)."""
    print("=" * 60)
    print("🚀 Full RAG Corpus Setup")
    print("=" * 60)

    # 1. Upload all documents
    all_uris = upload_all_documents()

    # 2. Create and index each corpus
    for corpus_name, gcs_uris in all_uris.items():
        if gcs_uris:
            await create_corpus(corpus_name)
            await asyncio.sleep(2)  # Wait for corpus creation
            await index_documents(corpus_name, gcs_uris)

    print("\n✅ Setup complete!")


# ============================================================================
# CLI
# ============================================================================

def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="RAG Corpus Setup")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # upload
    upload_parser = subparsers.add_parser("upload", help="Upload documents to GCS")
    upload_parser.add_argument("corpus", nargs="?", help="Corpus name (default: all)")

    # create-corpus
    create_parser = subparsers.add_parser("create-corpus", help="Create RAG corpus")
    create_parser.add_argument("corpus", help="Corpus name")

    # index
    index_parser = subparsers.add_parser("index", help="Index documents in corpus")
    index_parser.add_argument("corpus", help="Corpus name")

    # list
    subparsers.add_parser("list", help="List all corpora")

    # query
    query_parser = subparsers.add_parser("query", help="Test query")
    query_parser.add_argument("query", help="Query string")
    query_parser.add_argument("--corpus", help="Corpus name")

    # setup-all
    subparsers.add_parser("setup-all", help="Full setup (upload + create + index)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Run command
    if args.command == "upload":
        if args.corpus:
            upload_corpus_documents(args.corpus)
        else:
            upload_all_documents()
    elif args.command == "create-corpus":
        asyncio.run(create_corpus(args.corpus))
    elif args.command == "index":
        asyncio.run(index_documents(args.corpus))
    elif args.command == "list":
        asyncio.run(list_corpora())
    elif args.command == "query":
        asyncio.run(test_query(args.query, args.corpus))
    elif args.command == "setup-all":
        asyncio.run(setup_all())


if __name__ == "__main__":
    main()
