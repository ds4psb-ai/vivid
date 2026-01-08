"""Query Expansion Module.

LLM 기반 쿼리 확장을 통해 검색 품질을 향상시킵니다.

Strategies:
- LLM Expansion: Gemini를 사용하여 동의어, 관련 용어 추가
- HyDE: Hypothetical Document Embedding (가상 문서 생성)

Usage:
    from app.rag.query_expansion import expand_query
    
    expanded = await expand_query(
        query="봉준호 영화의 계단",
        strategy="llm",
    )
    # ["봉준호 영화의 계단", "기생충 계단 장면", "수직 공간 상징"]
"""
from __future__ import annotations

import logging
from typing import List, Literal, Optional

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

EXPANSION_STRATEGIES = Literal["llm", "hyde", "none"]
DEFAULT_STRATEGY = "llm"
MAX_EXPANSIONS = 3


# ============================================================================
# Expansion Prompts
# ============================================================================

EXPANSION_SYSTEM_PROMPT = """당신은 검색 쿼리 확장 전문가입니다.
사용자의 원본 쿼리를 분석하고, 검색 결과를 개선할 수 있는 관련 쿼리를 생성합니다.

규칙:
1. 원본 쿼리의 의도를 유지하면서 다양한 표현으로 확장
2. 동의어, 관련 용어, 다른 관점의 표현 포함
3. 한국어와 영어를 적절히 혼합 (검색 범위 확장)
4. 최대 {max_expansions}개의 확장 쿼리 생성

출력 형식: 각 쿼리를 새로운 줄에 출력 (번호 없이)"""

HYDE_SYSTEM_PROMPT = """당신은 문서 생성 전문가입니다.
사용자의 질문에 답변하는 가상의 문서 단락을 작성합니다.
이 문서는 검색 임베딩 생성에 사용됩니다.

규칙:
1. 질문에 직접 답변하는 형태로 작성
2. 구체적이고 사실적인 톤 유지
3. 100-150 단어 이내
4. 전문적인 용어와 일상 용어 모두 포함"""


# ============================================================================
# Query Expansion Functions
# ============================================================================

async def expand_query(
    query: str,
    strategy: EXPANSION_STRATEGIES = DEFAULT_STRATEGY,
    max_expansions: int = MAX_EXPANSIONS,
    model: str = "gemini-2.0-flash-exp",
) -> List[str]:
    """쿼리를 확장하여 검색 품질 향상.
    
    Args:
        query: 원본 검색 쿼리
        strategy: 확장 전략 ("llm", "hyde", "none")
        max_expansions: 최대 확장 쿼리 수
        model: 사용할 LLM 모델
        
    Returns:
        확장된 쿼리 목록 (원본 포함)
    """
    if strategy == "none":
        return [query]
    
    try:
        if strategy == "llm":
            expansions = await _expand_with_llm(query, max_expansions, model)
        elif strategy == "hyde":
            expansions = await _expand_with_hyde(query, model)
        else:
            expansions = []
        
        # Always include original query first
        result = [query] + [e for e in expansions if e != query]
        
        logger.info(
            f"[QueryExpansion] strategy={strategy} | "
            f"original='{query[:50]}...' | "
            f"expanded={len(result)} queries"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"[QueryExpansion] Error: {e}")
        return [query]  # Fallback to original


async def _expand_with_llm(
    query: str,
    max_expansions: int,
    model: str,
) -> List[str]:
    """LLM을 사용한 쿼리 확장."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    system_prompt = EXPANSION_SYSTEM_PROMPT.format(max_expansions=max_expansions)
    
    response = await client.aio.models.generate_content(
        model=model,
        contents=f"원본 쿼리: {query}",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
            max_output_tokens=200,
        ),
    )
    
    if not response.text:
        return []
    
    # Parse response: each line is a query
    lines = response.text.strip().split("\n")
    expansions = [line.strip() for line in lines if line.strip()]
    
    return expansions[:max_expansions]


async def _expand_with_hyde(
    query: str,
    model: str,
) -> List[str]:
    """HyDE: 가상 문서 생성을 통한 확장."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    response = await client.aio.models.generate_content(
        model=model,
        contents=f"질문: {query}",
        config=types.GenerateContentConfig(
            system_instruction=HYDE_SYSTEM_PROMPT,
            temperature=0.5,
            max_output_tokens=300,
        ),
    )
    
    if not response.text:
        return []
    
    # HyDE returns a single hypothetical document
    return [response.text.strip()]


# ============================================================================
# Integration Helper
# ============================================================================

async def get_expanded_queries(
    query: str,
    pipeline_hints: Optional[dict] = None,
) -> List[str]:
    """PipelineHints를 고려한 쿼리 확장.
    
    Args:
        query: 원본 쿼리
        pipeline_hints: PipelineHints 딕셔너리 (to_resolver_context() 결과)
        
    Returns:
        확장된 쿼리 목록
    """
    if not pipeline_hints:
        return [query]
    
    # Check if expansion is enabled in hints
    # Default: enabled for semantic strategy
    strategy = pipeline_hints.get("retrieval_strategy", "hybrid")
    
    if strategy in ["semantic", "hybrid"]:
        return await expand_query(query, strategy="llm", max_expansions=2)
    
    return [query]


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "expand_query",
    "get_expanded_queries",
    "EXPANSION_STRATEGIES",
]
