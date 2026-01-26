"""Tavily Research Pipeline for RAG Corpus Collection.

This module implements the research pipeline for collecting and processing
external content for RAG indexing:

    Tavily Search → Tavily Extract → Dedup/License → source_packs → Qdrant/NotebookLM

Usage:
    from app.rag.research_pipeline import ResearchPipeline

    pipeline = ResearchPipeline()
    results = await pipeline.research(
        query="강주노 촬영 기법",
        auteur_key="bong",
        dimension="4D",
    )

References:
    - SPEC: RAG_DATA_PIPELINE_SPEC_2026.md Section 10
    - Tavily: https://tavily.com (1,000 free credits/month)
"""

from __future__ import annotations

import asyncio
import inspect
import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

import httpx

from app.tavily_client import (
    TavilyClient,
    TavilySearchResult,
    TavilyExtractResult,
    get_tavily_client,
)

logger = logging.getLogger(__name__)

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SOURCE_PACKS_DIR = PROJECT_ROOT / "data" / "source_packs"
RESEARCH_OUTPUT_DIR = SOURCE_PACKS_DIR / "research"

# License indicators (2026 best practices)
PERMISSIVE_INDICATORS = [
    "creative commons",
    "cc by",
    "cc-by",
    "cc0",
    "public domain",
    "mit license",
    "apache license",
    "open access",
    "arxiv.org",
    "wikipedia.org",
    "wikimedia.org",
    ".edu",
    ".gov",
    "fair use",
]

RESTRICTED_INDICATORS = [
    "all rights reserved",
    "copyright ©",
    "proprietary",
    "subscription required",
    "paywall",
    "login required",
]

# Domain reputation (for grounding quality)
HIGH_QUALITY_DOMAINS = [
    "arxiv.org",
    "scholar.google.com",
    "wikipedia.org",
    "imdb.com",
    "criterion.com",
    "bfi.org.uk",
    "filmcomment.com",
    "sensesofcinema.com",
    "rogerebert.com",
]

# Extract heuristics
EXTRACT_MAX_URLS = 20
EXTRACT_MIN_CONTENT_LEN = 800
EXTRACT_MIN_SCORE = 0.55
RECENCY_KEYWORDS = [
    "오늘",
    "최근",
    "현재",
    "뉴스",
    "업데이트",
    "출시",
    "latest",
    "today",
    "now",
    "news",
    "update",
    "release",
    "2024",
    "2025",
    "2026",
]


@dataclass
class ResearchDocument:
    """A single research document from web search."""

    id: str
    title: str
    url: str
    content: str
    content_hash: str
    source_domain: str

    # Metadata
    query: str
    auteur_key: Optional[str] = None
    dimension: Optional[str] = None

    # Quality indicators
    relevance_score: float = 0.0
    license_status: str = "unknown"  # permissive, restricted, unknown
    quality_tier: str = "standard"  # high, standard, low

    # Timestamps
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Raw data
    raw_content: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "content_hash": self.content_hash,
            "source_domain": self.source_domain,
            "query": self.query,
            "auteur_key": self.auteur_key,
            "dimension": self.dimension,
            "relevance_score": self.relevance_score,
            "license_status": self.license_status,
            "quality_tier": self.quality_tier,
            "fetched_at": self.fetched_at,
            "tags": self.tags,
        }


@dataclass
class ResearchResult:
    """Result of a research pipeline run."""

    query: str
    total_found: int
    documents: List[ResearchDocument]
    duplicates_removed: int
    license_filtered: int
    saved_to: Optional[str] = None

    # Stats
    high_quality_count: int = 0
    permissive_license_count: int = 0

    def summary(self) -> str:
        """Human-readable summary."""
        return (
            f"Research: '{self.query}'\n"
            f"  Found: {self.total_found}, Saved: {len(self.documents)}\n"
            f"  Duplicates: {self.duplicates_removed}, License filtered: {self.license_filtered}\n"
            f"  High quality: {self.high_quality_count}, Permissive: {self.permissive_license_count}\n"
            f"  Output: {self.saved_to or 'not saved'}"
        )


class ResearchPipeline:
    """Tavily-based research pipeline for RAG corpus collection.

    Implements the full pipeline:
    1. Search - Tavily web search
    2. Extract - Get full content from URLs
    3. Dedup - Content hash deduplication
    4. License - Basic license/copyright heuristics
    5. Save - Write to source_packs

    Attributes:
        tavily: Tavily API client
        seen_hashes: Set of content hashes for deduplication
        output_dir: Directory for saving research results
    """

    def __init__(
        self,
        tavily_client: Optional[TavilyClient] = None,
        output_dir: Optional[Path] = None,
    ) -> None:
        """Initialize research pipeline.

        Args:
            tavily_client: Optional Tavily client (creates new if not provided)
            output_dir: Output directory for saved documents
        """
        self.tavily = tavily_client
        self.output_dir = output_dir or RESEARCH_OUTPUT_DIR
        self.seen_hashes: Set[str] = set()
        self._load_existing_hashes()

    def _load_existing_hashes(self) -> None:
        """Load content hashes from existing documents for dedup."""
        if not self.output_dir.exists():
            return

        for json_file in self.output_dir.glob("**/*.json"):
            try:
                data = json.loads(json_file.read_text())
                if isinstance(data, list):
                    for doc in data:
                        if h := doc.get("content_hash"):
                            self.seen_hashes.add(h)
                elif h := data.get("content_hash"):
                    self.seen_hashes.add(h)
            except Exception:
                continue

        logger.info(f"Loaded {len(self.seen_hashes)} existing content hashes")

    def _get_tavily(self) -> TavilyClient:
        """Get or create Tavily client."""
        if self.tavily is None:
            self.tavily = get_tavily_client()
        return self.tavily

    @staticmethod
    def _is_recency_query(query: str) -> bool:
        q = query.lower()
        return any(kw in q for kw in RECENCY_KEYWORDS)

    @staticmethod
    def _complexity_score(query: str) -> int:
        q = query.lower()
        score = 0
        if len(query) > 120:
            score += 1
        if len(query.split()) > 20:
            score += 1
        if any(
            kw in q
            for kw in (
                "compare",
                "comparison",
                "vs",
                "difference",
                "analysis",
                "benchmark",
                "survey",
                "state of the art",
                "sota",
                "논문",
                "비교",
                "분석",
                "벤치마크",
            )
        ):
            score += 1
        return score

    def _should_extract(
        self,
        result: TavilySearchResult,
        query: str,
        *,
        allowlist: Optional[List[str]],
    ) -> bool:
        """Decide whether to run Tavily Extract for a result."""
        if self._is_recency_query(query):
            return False

        if result.score < EXTRACT_MIN_SCORE:
            return False

        content = result.raw_content or result.content or ""
        if len(content) >= EXTRACT_MIN_CONTENT_LEN:
            return False

        domain = self._extract_domain(result.url)
        if allowlist:
            if not any(domain.endswith(d) or domain == d for d in allowlist):
                return False

        # License heuristic: avoid extracting known restricted pages
        if self._check_license(content, result.url) == "restricted":
            return False

        return True

    async def _extract_with_tavily(
        self,
        urls: List[str],
        *,
        query: str,
        depth: str,
        chunks_per_source: int,
    ) -> Dict[str, TavilyExtractResult]:
        """Batch extract via Tavily and return url -> extract result map."""
        if not urls:
            return {}

        tavily = self._get_tavily()
        response = tavily.extract(
            urls=urls[:EXTRACT_MAX_URLS],
            extract_depth=depth,
            query=query,
            chunks_per_source=chunks_per_source,
            include_images=False,
            include_favicon=False,
            format="markdown",
        )
        if inspect.isawaitable(response):
            response = await response

        return {item.url: item for item in response.results if item.url}

    @staticmethod
    def _compute_hash(content: str) -> str:
        """Compute content hash for deduplication."""
        # Normalize whitespace before hashing
        normalized = re.sub(r'\s+', ' ', content.strip().lower())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace("www.", "")
            return domain if domain else "unknown"
        except Exception:
            return "unknown"

    @staticmethod
    def _check_license(content: str, url: str) -> str:
        """Check license status based on content and URL heuristics.

        Returns:
            "permissive" - likely okay to use
            "restricted" - may have copyright issues
            "unknown" - needs manual review
        """
        combined = (content + " " + url).lower()

        # Check for permissive indicators
        for indicator in PERMISSIVE_INDICATORS:
            if indicator in combined:
                return "permissive"

        # Check for restricted indicators
        for indicator in RESTRICTED_INDICATORS:
            if indicator in combined:
                return "restricted"

        return "unknown"

    @staticmethod
    def _assess_quality(url: str, score: float) -> str:
        """Assess document quality tier.

        Args:
            url: Source URL
            score: Tavily relevance score

        Returns:
            "high", "standard", or "low"
        """
        domain = ResearchPipeline._extract_domain(url)

        # High quality: reputable domains or high relevance
        for hq_domain in HIGH_QUALITY_DOMAINS:
            if hq_domain in domain:
                return "high"

        if score >= 0.8:
            return "high"
        elif score >= 0.5:
            return "standard"
        else:
            return "low"

    @staticmethod
    def _generate_id(query: str, url: str) -> str:
        """Generate unique document ID."""
        combined = f"{query}:{url}"
        hash_part = hashlib.md5(combined.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"research_{timestamp}_{hash_part}"

    @staticmethod
    def _extract_tags(content: str, auteur_key: Optional[str] = None) -> List[str]:
        """Extract semantic tags from content."""
        tags = []

        # Auteur tag
        if auteur_key:
            tags.append(auteur_key)

        # Cinematography keywords
        cinematography_keywords = [
            "cinematography", "shot", "framing", "composition",
            "lighting", "color", "camera", "lens", "focus",
            "editing", "montage", "mise-en-scene", "visual style",
        ]

        content_lower = content.lower()
        for keyword in cinematography_keywords:
            if keyword in content_lower:
                tags.append(keyword.replace(" ", "_"))

        return list(set(tags))[:10]  # Max 10 tags

    async def search(
        self,
        query: str,
        max_results: int = 10,
        search_depth: str = "advanced",
        include_raw_content: bool = False,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> List[TavilySearchResult]:
        """Step 1: Search using Tavily API.

        Args:
            query: Search query
            max_results: Maximum results to return
            search_depth: "basic" or "advanced"
            include_domains: Only include these domains
            exclude_domains: Exclude these domains

        Returns:
            List of Tavily search results
        """
        tavily = self._get_tavily()

        logger.info(f"Searching: '{query}' (max={max_results}, depth={search_depth})")

        response = await tavily.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_raw_content=include_raw_content,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
        )

        logger.info(f"Found {len(response.results)} results")
        return response.results

    async def extract(
        self,
        results: List[TavilySearchResult],
        query: str,
        auteur_key: Optional[str] = None,
        dimension: Optional[str] = None,
        extract_mode: str = "auto",
        extract_allowlist: Optional[List[str]] = None,
    ) -> List[ResearchDocument]:
        """Step 2: Extract and process search results.

        Args:
            results: Tavily search results
            query: Original search query
            auteur_key: Optional auteur identifier
            dimension: Optional dimension (4D, AD, etc.)

        Returns:
            List of processed research documents
        """
        documents: List[ResearchDocument] = []

        # Decide allowlist for extraction
        allowlist = extract_allowlist or HIGH_QUALITY_DOMAINS
        complexity = self._complexity_score(query)
        extract_depth = "advanced" if complexity >= 2 else "basic"
        chunks_per_source = 3 if complexity >= 2 else 2

        # Identify URLs to extract
        extract_urls: List[str] = []
        if extract_mode != "off":
            for result in results:
                if self._should_extract(result, query, allowlist=allowlist):
                    extract_urls.append(result.url)

        # Batch extract (max 20 per call)
        extracted_map: Dict[str, TavilyExtractResult] = {}
        if extract_mode == "force":
            extract_urls = [r.url for r in results]
        if extract_urls:
            for i in range(0, len(extract_urls), EXTRACT_MAX_URLS):
                batch = extract_urls[i : i + EXTRACT_MAX_URLS]
                extracted_map.update(
                    await self._extract_with_tavily(
                        urls=batch,
                        query=query,
                        depth=extract_depth,
                        chunks_per_source=chunks_per_source,
                    )
                )

        for result in results:
            extracted = extracted_map.get(result.url)
            content = None
            if extracted and extracted.raw_content:
                content = extracted.raw_content
            else:
                content = result.raw_content or result.content

            if not content or len(content) < 100:
                continue

            content_hash = self._compute_hash(content)
            domain = self._extract_domain(result.url)

            doc = ResearchDocument(
                id=self._generate_id(query, result.url),
                title=result.title,
                url=result.url,
                content=content[:50000],  # Limit content size
                content_hash=content_hash,
                source_domain=domain,
                query=query,
                auteur_key=auteur_key,
                dimension=dimension,
                relevance_score=result.score,
                license_status=self._check_license(content, result.url),
                quality_tier=self._assess_quality(result.url, result.score),
                tags=self._extract_tags(content, auteur_key),
            )

            documents.append(doc)

        return documents

    def dedup(self, documents: List[ResearchDocument]) -> tuple[List[ResearchDocument], int]:
        """Step 3: Remove duplicates based on content hash.

        Args:
            documents: List of documents to dedup

        Returns:
            Tuple of (deduplicated docs, count of duplicates removed)
        """
        unique_docs = []
        duplicates = 0

        for doc in documents:
            if doc.content_hash not in self.seen_hashes:
                self.seen_hashes.add(doc.content_hash)
                unique_docs.append(doc)
            else:
                duplicates += 1
                logger.debug(f"Duplicate removed: {doc.url}")

        return unique_docs, duplicates

    def filter_by_license(
        self,
        documents: List[ResearchDocument],
        allow_unknown: bool = True,
    ) -> tuple[List[ResearchDocument], int]:
        """Step 4: Filter documents by license status.

        Args:
            documents: Documents to filter
            allow_unknown: Whether to include "unknown" license docs

        Returns:
            Tuple of (filtered docs, count of filtered out)
        """
        allowed = []
        filtered = 0

        for doc in documents:
            if doc.license_status == "restricted":
                filtered += 1
                logger.warning(f"License restricted: {doc.url}")
            elif doc.license_status == "unknown" and not allow_unknown:
                filtered += 1
            else:
                allowed.append(doc)

        return allowed, filtered

    def save(
        self,
        documents: List[ResearchDocument],
        filename: Optional[str] = None,
    ) -> str:
        """Step 5: Save documents to source_packs.

        Args:
            documents: Documents to save
            filename: Optional filename (auto-generated if not provided)

        Returns:
            Path to saved file
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_{timestamp}.json"

        output_path = self.output_dir / filename

        data = [doc.to_dict() for doc in documents]
        output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

        logger.info(f"Saved {len(documents)} documents to {output_path}")
        return str(output_path)

    async def research(
        self,
        query: str,
        auteur_key: Optional[str] = None,
        dimension: Optional[str] = None,
        max_results: int = 10,
        search_depth: str = "advanced",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        extract_mode: str = "auto",
        allow_unknown_license: bool = True,
        save_results: bool = True,
    ) -> ResearchResult:
        """Run the full research pipeline.

        Pipeline: Search → Extract → Dedup → License Filter → Save

        Args:
            query: Search query
            auteur_key: Optional auteur identifier (bong, epoch, etc.)
            dimension: Optional dimension (4D, AD, etc.)
            max_results: Maximum search results
            search_depth: "basic" or "advanced"
            include_domains: Only include these domains
            exclude_domains: Exclude these domains
            allow_unknown_license: Include docs with unknown license
            save_results: Whether to save to source_packs

        Returns:
            ResearchResult with all processed documents and stats
        """
        logger.info(f"Starting research pipeline: '{query}'")

        # Step 1: Search
        search_results = await self.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_raw_content=(extract_mode == "off"),
            include_domains=include_domains,
            exclude_domains=exclude_domains,
        )
        total_found = len(search_results)

        # Step 2: Extract
        documents = await self.extract(
            results=search_results,
            query=query,
            auteur_key=auteur_key,
            dimension=dimension,
            extract_mode=extract_mode,
            extract_allowlist=include_domains,
        )

        # Step 3: Dedup
        documents, duplicates_removed = self.dedup(documents)

        # Step 4: License filter
        documents, license_filtered = self.filter_by_license(
            documents,
            allow_unknown=allow_unknown_license,
        )

        # Step 5: Save
        saved_to = None
        if save_results and documents:
            safe_query = re.sub(r'[^\w\s-]', '', query)[:30].strip().replace(' ', '_')
            filename = f"research_{safe_query}_{datetime.now().strftime('%Y%m%d')}.json"
            saved_to = self.save(documents, filename)

        # Calculate stats
        high_quality_count = sum(1 for d in documents if d.quality_tier == "high")
        permissive_count = sum(1 for d in documents if d.license_status == "permissive")

        result = ResearchResult(
            query=query,
            total_found=total_found,
            documents=documents,
            duplicates_removed=duplicates_removed,
            license_filtered=license_filtered,
            saved_to=saved_to,
            high_quality_count=high_quality_count,
            permissive_license_count=permissive_count,
        )

        logger.info(result.summary())
        return result


# Convenience functions
async def research_auteur(
    auteur_key: str,
    topics: Optional[List[str]] = None,
    max_results_per_topic: int = 5,
) -> List[ResearchResult]:
    """Research an auteur across multiple topics.

    Args:
        auteur_key: Auteur identifier (bong, epoch, wong, etc.)
        topics: List of topics to research (default: cinematography-related)
        max_results_per_topic: Max results per topic

    Returns:
        List of ResearchResult for each topic
    """
    if topics is None:
        topics = [
            "cinematography style",
            "visual techniques",
            "lighting approach",
            "camera movement",
            "color palette",
            "editing rhythm",
        ]

    auteur_names = {
        "bong": "강주노 Bong Joon-ho",
        "epoch": "Christopher Epoch",
        "wong": "렌 벨벳 Wong Kar-wai",
        "voltage": "Quentin Voltage",
        "abyss": "Denis Abyss",
        "park": "박찬욱 Park Chan-wook",
        "prism": "Stanley Prism",
    }

    auteur_name = auteur_names.get(auteur_key, auteur_key)
    pipeline = ResearchPipeline()
    results = []

    for topic in topics:
        query = f"{auteur_name} {topic}"
        result = await pipeline.research(
            query=query,
            auteur_key=auteur_key,
            dimension="4D",
            max_results=max_results_per_topic,
        )
        results.append(result)

        # Rate limiting
        await asyncio.sleep(1)

    return results


async def research_dimension(
    dimension: str,
    queries: List[str],
    max_results_per_query: int = 5,
) -> List[ResearchResult]:
    """Research content for a specific dimension.

    Args:
        dimension: Dimension ID (1D, 2D, 4D, 5D, 6D, AD, etc.)
        queries: List of search queries
        max_results_per_query: Max results per query

    Returns:
        List of ResearchResult for each query
    """
    pipeline = ResearchPipeline()
    results = []

    for query in queries:
        result = await pipeline.research(
            query=query,
            dimension=dimension,
            max_results=max_results_per_query,
        )
        results.append(result)

        # Rate limiting
        await asyncio.sleep(1)

    return results


# CLI interface
if __name__ == "__main__":
    import sys

    async def main():
        if len(sys.argv) < 2:
            print("Usage: python -m app.rag.research_pipeline <query> [auteur_key]")
            print("Example: python -m app.rag.research_pipeline '강주노 촬영 기법' bong")
            sys.exit(1)

        query = sys.argv[1]
        auteur_key = sys.argv[2] if len(sys.argv) > 2 else None

        pipeline = ResearchPipeline()
        result = await pipeline.research(
            query=query,
            auteur_key=auteur_key,
            max_results=10,
        )

        print("\n" + result.summary())
        print(f"\nDocuments ({len(result.documents)}):")
        for doc in result.documents:
            print(f"  - [{doc.quality_tier}] {doc.title[:60]}...")
            print(f"    URL: {doc.url}")
            print(f"    License: {doc.license_status}, Score: {doc.relevance_score:.2f}")

    asyncio.run(main())
