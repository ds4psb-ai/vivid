"""
P5: LLM Classifier - Gemini-based Query Classification Fallback.

SemanticRouter의 신뢰도가 임계값 미만일 때 사용되는 LLM 기반 분류기.

Architecture:
    1. SemanticRouter: Fast Path (~15ms) - Embedding-based
    2. LLM Classifier: Slow Path (~200ms) - Gemini-based (Fallback)

Performance:
    - 지연: 150-300ms (Gemini API 호출)
    - 정확도: 높음 (자연어 이해 기반)
    - 비용: ~$0.0002/query

Usage:
    from app.rag.llm_classifier import classify_with_llm

    query_type, confidence = await classify_with_llm("왜 기생충이 성공했나?")
    # QueryType.MULTI_HOP, 0.92
"""
from __future__ import annotations

import json
import logging
import time
from typing import Tuple

from app.rag.query_classifier import QueryType

logger = logging.getLogger(__name__)


# ============================================================================
# Classification Prompt
# ============================================================================

CLASSIFICATION_PROMPT = """You are a query classifier for a RAG (Retrieval-Augmented Generation) system specialized in film/director knowledge.

Classify the following query into ONE of these types:

1. **simple_factual**: General knowledge queries that can be answered from LLM's parametric knowledge without retrieval.
   - Examples: "What is Python?", "HTTP status code 200 meaning", "What is AI?"
   - Characteristics: Common knowledge, definitions, basic facts

2. **domain_specific**: Queries about film/director domain knowledge (Vivid's specialty).
   - Examples: "Bong Joon-ho's long take technique", "Parasite staircase scene", "Wong Kar-wai color style"
   - Characteristics: Specific director styles, film techniques, cinematography

3. **recency_required**: Queries requiring up-to-date or real-time information.
   - Examples: "2026 AI trends", "Latest Gemini features", "Recent movies"
   - Characteristics: Time-sensitive, current events, latest updates

4. **multi_hop**: Complex queries requiring multi-step reasoning, comparison, or deep analysis.
   - Examples: "Why is Parasite's staircase symbolic?", "Compare Bong vs Epoch styles"
   - Characteristics: "Why", "Compare", "Analyze", requires multiple knowledge pieces

5. **creative**: Creative/generative queries where retrieval is less important.
   - Examples: "Write a movie synopsis", "Suggest character names", "Create dialogue"
   - Characteristics: Writing, brainstorming, creative generation

Query to classify:
"{query}"

Respond with a JSON object containing:
- "query_type": one of ["simple_factual", "domain_specific", "recency_required", "multi_hop", "creative"]
- "confidence": float between 0.0 and 1.0
- "reasoning": brief explanation (1-2 sentences)

JSON Response:"""


# ============================================================================
# LLM Classification Function
# ============================================================================


async def classify_with_llm(
    query: str,
    model_name: str = "gemini-2.0-flash",
) -> Tuple[QueryType, float]:
    """Gemini를 사용하여 쿼리 분류.

    SemanticRouter의 폴백으로 사용됩니다.

    Args:
        query: 입력 쿼리
        model_name: Gemini 모델 ID

    Returns:
        (QueryType, confidence) 튜플

    Raises:
        Exception: Gemini API 호출 실패 시
    """
    start = time.time()

    try:
        from app.services.genai_utils import get_genai_client

        client = get_genai_client()
        prompt = CLASSIFICATION_PROMPT.format(query=query)

        # Gemini API 호출 (google.genai - new library)
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
            config={
                "temperature": 0.1,  # 낮은 temperature로 일관된 분류
                "max_output_tokens": 256,
                "response_mime_type": "application/json",
            },
        )

        # Parse JSON response
        result = _parse_classification_response(response.text)

        latency_ms = (time.time() - start) * 1000
        logger.debug(
            f"[LLMClassifier] Classified '{query[:30]}...' as {result[0].value} "
            f"(confidence={result[1]:.2f}, latency={latency_ms:.0f}ms)"
        )

        return result

    except Exception as e:
        logger.error(f"[LLMClassifier] Classification failed: {e}")
        # Fallback to AMBIGUOUS on error
        return (QueryType.AMBIGUOUS, 0.5)


def _parse_classification_response(response_text: str) -> Tuple[QueryType, float]:
    """Gemini 응답 파싱.

    Args:
        response_text: Gemini JSON 응답

    Returns:
        (QueryType, confidence) 튜플
    """
    try:
        # Clean response (remove markdown code blocks if present)
        text = response_text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        data = json.loads(text)

        query_type_str = data.get("query_type", "ambiguous")
        confidence = float(data.get("confidence", 0.5))

        # Map string to QueryType
        type_mapping = {
            "simple_factual": QueryType.SIMPLE_FACTUAL,
            "domain_specific": QueryType.DOMAIN_SPECIFIC,
            "recency_required": QueryType.RECENCY_REQUIRED,
            "multi_hop": QueryType.MULTI_HOP,
            "creative": QueryType.CREATIVE,
            "ambiguous": QueryType.AMBIGUOUS,
        }

        query_type = type_mapping.get(query_type_str, QueryType.AMBIGUOUS)

        # Clamp confidence to [0, 1]
        confidence = max(0.0, min(1.0, confidence))

        return (query_type, confidence)

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f"[LLMClassifier] Failed to parse response: {e}")
        return (QueryType.AMBIGUOUS, 0.5)


# ============================================================================
# Batch Classification (Optional, for analytics)
# ============================================================================


async def classify_batch(
    queries: list[str],
    model: str = "gemini-2.0-flash",
) -> list[Tuple[QueryType, float]]:
    """여러 쿼리 일괄 분류 (분석용).

    Args:
        queries: 쿼리 목록
        model: Gemini 모델 ID

    Returns:
        [(QueryType, confidence), ...] 목록
    """
    import asyncio

    tasks = [classify_with_llm(q, model) for q in queries]
    return await asyncio.gather(*tasks)


# ============================================================================
# Mock Classifier (for testing without API calls)
# ============================================================================


class MockLLMClassifier:
    """테스트용 Mock LLM Classifier."""

    def __init__(self, default_type: QueryType = QueryType.DOMAIN_SPECIFIC):
        self.default_type = default_type
        self.call_count = 0

    async def classify(self, query: str) -> Tuple[QueryType, float]:
        """Mock 분류 (간단한 키워드 기반)."""
        self.call_count += 1

        query_lower = query.lower()

        # Simple keyword-based classification
        if any(kw in query_lower for kw in ["what is", "뭐야", "란?", "정의"]):
            return (QueryType.SIMPLE_FACTUAL, 0.85)

        if any(kw in query_lower for kw in ["최신", "2026", "latest", "recent"]):
            return (QueryType.RECENCY_REQUIRED, 0.80)

        if any(kw in query_lower for kw in ["왜", "why", "비교", "compare", "분석"]):
            return (QueryType.MULTI_HOP, 0.78)

        if any(kw in query_lower for kw in ["써줘", "만들어", "write", "create"]):
            return (QueryType.CREATIVE, 0.82)

        if any(
            kw in query_lower
            for kw in ["강주노", "렌 벨벳", "감독", "기법", "촬영", "영화"]
        ):
            return (QueryType.DOMAIN_SPECIFIC, 0.88)

        return (self.default_type, 0.70)


# Global mock instance for testing
_mock_classifier: MockLLMClassifier | None = None


def set_mock_classifier(mock: MockLLMClassifier | None) -> None:
    """Mock classifier 설정 (테스트용)."""
    global _mock_classifier
    _mock_classifier = mock


async def classify_with_llm_or_mock(query: str) -> Tuple[QueryType, float]:
    """LLM 또는 Mock classifier 사용.

    테스트 환경에서는 Mock을, 프로덕션에서는 실제 LLM을 사용합니다.
    """
    if _mock_classifier is not None:
        return await _mock_classifier.classify(query)
    return await classify_with_llm(query)
