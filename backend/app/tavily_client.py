"""Tavily API client for web search (Exa alternative).

This module provides a Tavily-based web search client for LLM/RAG pipelines.
Tavily offers 1,000 free credits/month with 93.3% grounding accuracy.

Usage:
    from app.tavily_client import search_web, get_tavily_client

    # Simple search
    results = await search_web("봉준호 감독 촬영 기법")

    # Advanced search with options
    client = get_tavily_client()
    results = await client.search(
        query="parasite cinematography techniques",
        search_depth="advanced",
        max_results=10,
    )

References:
    - Spec: 36_MCP_INTEGRATION_SPEC_V1.md
    - Pricing: https://tavily.com (1,000 credits/month free)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

TAVILY_API_URL = "https://api.tavily.com/search"

# Import settings for centralized config
try:
    from app.config import settings
    TAVILY_API_KEY = settings.TAVILY_API_KEY
except ImportError:
    # Fallback for standalone usage
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


@dataclass
class TavilySearchResult:
    """Single search result from Tavily API."""

    title: str
    url: str
    content: str
    score: float
    raw_content: Optional[str] = None
    favicon: Optional[str] = None


@dataclass
class TavilySearchResponse:
    """Response from Tavily search API."""

    query: str
    results: List[TavilySearchResult]
    answer: Optional[str] = None
    follow_up_questions: Optional[List[str]] = None
    response_time: Optional[float] = None
    auto_parameters: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class TavilyClient:
    """Tavily API client for web search.

    Attributes:
        api_key: Tavily API key (from TAVILY_API_KEY env var)
        base_url: API endpoint URL

    Example:
        client = TavilyClient()
        response = await client.search("AI pipeline best practices")
        for result in response.results:
            print(f"{result.title}: {result.url}")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = TAVILY_API_URL,
    ) -> None:
        """Initialize Tavily client.

        Args:
            api_key: Tavily API key. Defaults to TAVILY_API_KEY env var.
            base_url: API endpoint URL.

        Raises:
            ValueError: If no API key provided.
        """
        self.api_key = api_key or TAVILY_API_KEY
        self.base_url = base_url
        if not self.api_key:
            raise ValueError(
                "TAVILY_API_KEY not set. Get your free key at https://tavily.com"
            )

    async def search(
        self,
        query: str,
        *,
        search_depth: str = "basic",
        max_results: int = 5,
        include_answer: bool = True,
        include_raw_content: bool = False,
        topic: Optional[str] = None,
        time_range: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        country: Optional[str] = None,
        auto_parameters: Optional[bool] = None,
        include_usage: Optional[bool] = None,
        include_images: Optional[bool] = None,
        include_image_descriptions: Optional[bool] = None,
        include_favicon: Optional[bool] = None,
        chunks_per_source: Optional[int] = None,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> TavilySearchResponse:
        """Search the web using Tavily API.

        Args:
            query: Search query string.
            search_depth: "basic" or "advanced". Advanced costs more credits.
            max_results: Maximum number of results (1-20).
            include_answer: Include AI-generated answer.
            include_raw_content: Include full page content.
            include_domains: Limit to specific domains.
            exclude_domains: Exclude specific domains.

        Returns:
            TavilySearchResponse with results and optional answer.

        Raises:
            httpx.HTTPStatusError: If API request fails.
        """
        payload: Dict[str, Any] = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": min(max_results, 20),
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
        }
        if topic:
            payload["topic"] = topic
        if time_range:
            payload["time_range"] = time_range
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date
        if country:
            payload["country"] = country
        if auto_parameters is not None:
            payload["auto_parameters"] = auto_parameters
        if include_usage is not None:
            payload["include_usage"] = include_usage
        if include_images is not None:
            payload["include_images"] = include_images
        if include_image_descriptions is not None:
            payload["include_image_descriptions"] = include_image_descriptions
        if include_favicon is not None:
            payload["include_favicon"] = include_favicon
        if chunks_per_source is not None:
            payload["chunks_per_source"] = chunks_per_source
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.base_url, json=payload)
            response.raise_for_status()
            data = response.json()

        results = [
            TavilySearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content=r.get("content", ""),
                score=r.get("score", 0.0),
                raw_content=r.get("raw_content"),
                favicon=r.get("favicon"),
            )
            for r in data.get("results", [])
        ]

        return TavilySearchResponse(
            query=data.get("query", query),
            results=results,
            answer=data.get("answer"),
            follow_up_questions=data.get("follow_up_questions"),
            response_time=data.get("response_time"),
            auto_parameters=data.get("auto_parameters"),
            usage=data.get("usage"),
            request_id=data.get("request_id"),
        )


# Module-level singleton
_client: Optional[TavilyClient] = None


def get_tavily_client() -> TavilyClient:
    """Get or create Tavily client singleton.

    Returns:
        TavilyClient instance.
    """
    global _client
    if _client is None:
        _client = TavilyClient()
    return _client


async def search_web(
    query: str,
    *,
    max_results: int = 5,
    search_depth: str = "basic",
) -> List[Dict[str, Any]]:
    """Convenience function for web search.

    Args:
        query: Search query.
        max_results: Maximum results.
        search_depth: "basic" or "advanced".

    Returns:
        List of result dictionaries.
    """
    client = get_tavily_client()
    response = await client.search(
        query,
        max_results=max_results,
        search_depth=search_depth,
    )
    return [
        {
            "title": r.title,
            "url": r.url,
            "content": r.content,
            "score": r.score,
        }
        for r in response.results
    ]
