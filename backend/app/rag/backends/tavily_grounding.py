"""Tavily Web Grounding Backend.

Provides web search grounding results for recency queries.
Uses app.tavily_client (async) and returns RetrievalResult entries.
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional

from .base import BaseBackend, RetrievalResult

logger = logging.getLogger(__name__)


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

        search_depth = config.get("search_depth", "basic")
        include_answer = config.get("include_answer", False)
        include_raw_content = config.get("include_raw_content", False)
        topic = config.get("topic")
        time_range = config.get("time_range")
        start_date = config.get("start_date")
        end_date = config.get("end_date")
        country = config.get("country")
        auto_parameters = config.get("auto_parameters")
        include_usage = config.get("include_usage")
        include_images = config.get("include_images")
        include_image_descriptions = config.get("include_image_descriptions")
        include_favicon = config.get("include_favicon")
        chunks_per_source = config.get("chunks_per_source")
        include_domains = config.get("include_domains")
        exclude_domains = config.get("exclude_domains")

        try:
            response = await tavily.search(
                query=query,
                search_depth=search_depth,
                max_results=limit,
                include_answer=include_answer,
                include_raw_content=include_raw_content,
                topic=topic,
                time_range=time_range,
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

        results: List[RetrievalResult] = []
        for idx, item in enumerate(response.results):
            url_hash = hashlib.md5(item.url.encode("utf-8")).hexdigest()[:12]
            results.append(
                RetrievalResult(
                    doc_id=f"tavily_{url_hash}",
                    text=item.content or "",
                    score=item.score or 0.0,
                    source=self.backend_id,
                    rank=idx + 1,
                    metadata={
                        "url": item.url,
                        "title": item.title,
                        "type": "web_search",
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
