#!/usr/bin/env python3
"""Test script for MCP clients (Qdrant, Tavily).

Usage:
    cd backend && python scripts/test_mcp_clients.py

This script verifies that MCP clients are properly configured and functional.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings


async def test_qdrant() -> bool:
    """Test Qdrant vector database connection."""
    print("\n=== Testing Qdrant ===")
    print(f"URL: {settings.QDRANT_URL}")

    try:
        from app.qdrant_client import QdrantClient

        client = QdrantClient(base_url=settings.QDRANT_URL)
        healthy = await client.health_check()

        if healthy:
            print("✅ Qdrant health check: PASSED")
            collections = await client.list_collections()
            print(f"   Collections: {collections or '(none)'}")
            return True
        else:
            print("❌ Qdrant health check: FAILED")
            return False
    except Exception as e:
        print(f"❌ Qdrant error: {e}")
        return False


async def test_tavily() -> bool:
    """Test Tavily search API."""
    print("\n=== Testing Tavily ===")

    if not settings.TAVILY_API_KEY:
        print("⚠️  TAVILY_API_KEY not set - skipping")
        print("   Get free key at https://tavily.com (1,000 credits/month)")
        return True  # Not a failure, just not configured

    try:
        from app.tavily_client import TavilyClient

        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        response = await client.search(
            "test query",
            max_results=1,
            search_depth="basic",
        )

        if response.results:
            print("✅ Tavily search: PASSED")
            print(f"   Sample result: {response.results[0].title}")
            return True
        else:
            print("⚠️  Tavily returned no results")
            return True  # API works, just no results
    except Exception as e:
        print(f"❌ Tavily error: {e}")
        return False


async def test_qdrant_collection() -> bool:
    """Test Qdrant collection creation."""
    print("\n=== Testing Qdrant Collection ===")

    try:
        from app.qdrant_client import QdrantClient

        client = QdrantClient(base_url=settings.QDRANT_URL)

        # Check if test collection exists
        collections = await client.list_collections()
        test_collection = "crebit_test"

        if test_collection not in collections:
            print(f"   Creating collection: {test_collection}")
            success = await client.create_collection(
                name=test_collection,
                vector_size=768,  # Standard embedding size
                distance="Cosine",
            )
            if success:
                print(f"✅ Collection '{test_collection}' created")
            else:
                print(f"❌ Failed to create collection")
                return False
        else:
            print(f"✅ Collection '{test_collection}' already exists")

        return True
    except Exception as e:
        print(f"❌ Collection error: {e}")
        return False


async def main() -> int:
    """Run all tests."""
    print("=" * 50)
    print("MCP Client Test Suite")
    print("=" * 50)

    results = []

    # Test Qdrant
    results.append(await test_qdrant())

    if results[0]:  # Only test collection if Qdrant is up
        results.append(await test_qdrant_collection())

    # Test Tavily
    results.append(await test_tavily())

    # Summary
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if all(results):
        print("✅ All tests PASSED")
        return 0
    else:
        print("❌ Some tests FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
