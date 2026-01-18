"""Tavily Web Grounding Backend.

Provides web search grounding results for recency queries.
Uses app.tavily_client (async) and returns RetrievalResult entries.
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from .base import BaseBackend, RetrievalResult

logger = logging.getLogger(__name__)

# Recency detection keywords (lightweight heuristic)
RECENCY_KEYWORDS = (
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
)

APP_DEFAULTS: Dict[str, Dict[str, Any]] = {
    # Story / Narrative
    "dimension.story.architect": {
        "topic": "news",
        "time_range": "month",
        "domain_allowlist": [
            "imdb.com",
            "bfi.org.uk",
            "criterion.com",
            "rogerebert.com",
            "sensesofcinema.com",
            "filmcomment.com",
            "variety.com",
            "hollywoodreporter.com",
            "indiewire.com",
        ],
    },
    # Reference Analysis
    "teaching.reference.analyze": {
        "topic": "news",
        "time_range": "month",
        "domain_allowlist": [
            "imdb.com",
            "bfi.org.uk",
            "criterion.com",
            "rogerebert.com",
            "sensesofcinema.com",
            "filmcomment.com",
            "arxiv.org",
            "variety.com",
            "hollywoodreporter.com",
        ],
    },
    # Video / Veo (model updates)
    "dimension.video.generate": {
        "topic": "general",
        "time_range": "month",
        "domain_allowlist": [
            "deepmind.google",
            "docs.cloud.google.com",
            "ai.google.dev",
            "openai.com",
            "runwayml.com",
            "help.runwayml.com",
        ],
    },
    "veo.video.generate": {
        "topic": "general",
        "time_range": "month",
        "domain_allowlist": [
            "deepmind.google",
            "docs.cloud.google.com",
            "ai.google.dev",
            "openai.com",
            "runwayml.com",
            "help.runwayml.com",
        ],
    },
}

DIMENSION_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "STORY": APP_DEFAULTS["dimension.story.architect"],
    "4D": APP_DEFAULTS["teaching.reference.analyze"],
    "5D": APP_DEFAULTS["dimension.video.generate"],
    "VEO": APP_DEFAULTS["veo.video.generate"],
}


def _is_recency_query(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in RECENCY_KEYWORDS)


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


def _normalize_domain(url: str) -> str:
    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        return ""
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def _domain_allowed(domain: str, allowlist: List[str]) -> bool:
    if not domain:
        return False
    for allowed in allowlist:
        if domain == allowed or domain.endswith(f".{allowed}"):
            return True
    return False


def _resolve_defaults(app_key: Optional[str], dimension: Optional[str]) -> Dict[str, Any]:
    if app_key and app_key in APP_DEFAULTS:
        return APP_DEFAULTS[app_key]
    if dimension and dimension.upper() in DIMENSION_DEFAULTS:
        return DIMENSION_DEFAULTS[dimension.upper()]
    return {}


def _select_search_depth(
    *,
    query: str,
    explicit_depth: Optional[str],
) -> str:
    """Heuristic to choose Tavily search depth.

    Rules (only applied when explicit_depth is None):
    - Recency query -> advanced
    - Complexity >= 2 -> advanced
    - Complexity == 1 -> basic
    - Complexity == 0 -> fast (lower latency)
    """
    if explicit_depth:
        return explicit_depth

    if _is_recency_query(query):
        return "advanced"

    score = _complexity_score(query)
    if score >= 2:
        return "advanced"
    if score == 1:
        return "basic"
    return "fast"


def _select_chunks_per_source(
    *,
    search_depth: str,
    explicit_chunks: Optional[int],
    complexity_score: int,
    include_raw_content: bool,
) -> Optional[int]:
    """Heuristic to choose chunks_per_source.

    Only valid for advanced search; otherwise returns None.
    """
    if explicit_chunks is not None:
        return explicit_chunks

    if search_depth != "advanced":
        return None

    # Keep content size bounded
    if include_raw_content:
        return 2 if complexity_score >= 1 else 1

    if complexity_score >= 2:
        return 3
    if complexity_score == 1:
        return 2
    return 1


class TavilyGroundingBackend(BaseBackend):
    """Tavily Web Search Grounding Backend.

    Features:
    - Web search grounding for 최신/실시간 쿼리
    - Result metadata includes url/title/type=web_search
    - Graceful degradation when API key is missing
    """

    backend_id = "tavily_grounding"

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """Search via Tavily API.

        Config options:
            search_depth: "basic" | "advanced"
            include_answer: bool
            include_raw_content: bool
            include_domains: List[str]
            exclude_domains: List[str]
        """
        config = config or {}

        try:
            from app.tavily_client import get_tavily_client
        except Exception as exc:
            logger.warning(f"[TavilyGrounding] Tavily client unavailable: {exc}")
            return []

        try:
            tavily = get_tavily_client()
        except Exception as exc:
            logger.warning(f"[TavilyGrounding] API key missing or invalid: {exc}")
            return []

        explicit_depth = config.get("search_depth")
        search_depth = _select_search_depth(query=query, explicit_depth=explicit_depth)
        include_answer = config.get("include_answer", False)
        include_raw_content = config.get("include_raw_content", False)
        topic = config.get("topic")
        time_range = config.get("time_range")
        days = config.get("days")
        start_date = config.get("start_date")
        end_date = config.get("end_date")
        country = config.get("country")
        auto_parameters = config.get("auto_parameters")
        include_usage = config.get("include_usage")
        include_images = config.get("include_images")
        include_image_descriptions = config.get("include_image_descriptions")
        include_favicon = config.get("include_favicon")
        explicit_chunks = config.get("chunks_per_source")
        include_domains = config.get("include_domains")
        exclude_domains = config.get("exclude_domains")
        app_key = config.get("app_key")
        dimension = config.get("dimension")

        # Quality gate configuration
        min_score = config.get("min_score", 0.35)
        quality_gate = config.get("quality_gate", True)
        domain_gate = config.get("domain_gate", True)
        domain_allowlist = config.get("domain_allowlist")

        complexity = _complexity_score(query)

        # Apply per-app defaults if not explicitly set
        defaults = _resolve_defaults(app_key, dimension)
        if topic is None:
            topic = defaults.get("topic")
        if time_range is None:
            time_range = defaults.get("time_range")
        if domain_allowlist is None:
            domain_allowlist = defaults.get("domain_allowlist")

        # Recency-aware auto parameter mapping (only if not explicitly set)
        if _is_recency_query(query):
            if topic is None:
                topic = "news"
            if time_range is None:
                time_range = "week"
            if auto_parameters is None:
                auto_parameters = True

        # News topic default days if time_range not specified
        if topic == "news" and time_range is None and days is None:
            days = 3

        chunks_per_source = _select_chunks_per_source(
            search_depth=search_depth,
            explicit_chunks=explicit_chunks,
            complexity_score=complexity,
            include_raw_content=include_raw_content,
        )

        try:
            response = await tavily.search(
                query=query,
                search_depth=search_depth,
                max_results=limit,
                include_answer=include_answer,
                include_raw_content=include_raw_content,
                topic=topic,
                time_range=time_range,
                days=days,
                start_date=start_date,
                end_date=end_date,
                country=country,
                auto_parameters=auto_parameters,
                include_usage=include_usage,
                include_images=include_images,
                include_image_descriptions=include_image_descriptions,
                include_favicon=include_favicon,
                chunks_per_source=chunks_per_source,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
            )
        except Exception as exc:
            logger.warning(f"[TavilyGrounding] Search failed: {exc}")
            return []

        # Determine domain allowlist
        if domain_allowlist is None and domain_gate:
            try:
                from app.rag.research_pipeline import HIGH_QUALITY_DOMAINS

                domain_allowlist = list(HIGH_QUALITY_DOMAINS)
            except Exception:
                domain_allowlist = []

        filtered_results: List[Tuple[int, Any]] = []
        for idx, item in enumerate(response.results):
            if quality_gate and min_score is not None and item.score < float(min_score):
                continue

            if domain_gate and domain_allowlist:
                domain = _normalize_domain(item.url)
                if not _domain_allowed(domain, domain_allowlist):
                    continue

            filtered_results.append((idx, item))

        # Fallback: if domain gate removed everything, relax domain gate
        if quality_gate and domain_gate and not filtered_results and response.results:
            for idx, item in enumerate(response.results):
                if min_score is not None and item.score < float(min_score):
                    continue
                filtered_results.append((idx, item))

        results: List[RetrievalResult] = []
        for rank, (idx, item) in enumerate(filtered_results, start=1):
            url_hash = hashlib.md5(item.url.encode("utf-8")).hexdigest()[:12]
            results.append(
                RetrievalResult(
                    doc_id=f"tavily_{url_hash}",
                    text=item.content or "",
                    score=item.score or 0.0,
                    source=self.backend_id,
                    rank=rank,
                    metadata={
                        "url": item.url,
                        "title": item.title,
                        "type": "web_search",
                        "favicon": item.favicon,
                    },
                )
            )

        return results

    async def health_check(self) -> bool:
        """Tavily 연결 상태 확인."""
        try:
            from app.tavily_client import get_tavily_client

            _ = get_tavily_client()
            return True
        except Exception:
            return False
