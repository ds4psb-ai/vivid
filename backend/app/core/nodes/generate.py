"""Generation Node - LLM 응답 생성.

검색된 컨텍스트와 도구 실행 결과를 종합하여 최종 응답을 생성합니다.

P0 Security (2026):
- Attribution-gated prompting: 검색 결과 내 명령어 무시
- Grounding: 검색 결과에 없는 내용 생성 방지
- Source citation: 출처 명시

Usage:
    from app.core.nodes.generate import generate_node

    result_state = await generate_node(state)
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from app.core.unified_schemas import Intent, QueryType
from app.core.unified_state import UnifiedState, state_with_response, get_context_for_llm
from app.core.utils.attribution import (
    wrap_context_with_attribution,
    get_attribution_system_prompt,
    get_grounding_instruction,
)

logger = logging.getLogger(__name__)

# 기본 시스템 프롬프트
BASE_SYSTEM_PROMPT = """당신은 Vivid의 AI 어시스턴트입니다.
영화 제작, 콘텐츠 크리에이션, 시각적 스토리텔링에 대한 전문 지식을 갖추고 있습니다.

다음 지침을 따르세요:
1. 제공된 컨텍스트를 기반으로 정확하고 유용한 답변을 제공하세요.
2. 거장(감독)의 스타일과 기법에 대해 깊이 있는 통찰을 제공하세요.
3. 창작 과정을 돕기 위한 구체적이고 실용적인 조언을 제공하세요.
4. 불확실한 정보는 명확히 표시하세요.
"""

# P0 Security: Attribution-gated system prompt
DEFAULT_SYSTEM_PROMPT = (
    BASE_SYSTEM_PROMPT
    + get_attribution_system_prompt(include_full_guardrail=True)
    + get_grounding_instruction(strict=True, allow_general_knowledge=False)
)

# Intent별 프롬프트 템플릿
INTENT_TEMPLATES = {
    Intent.GENERATE: """다음 요청에 대해 창작 콘텐츠를 생성해주세요.

요청: {query}

참고 컨텍스트:
{context}

생성된 콘텐츠:""",

    Intent.ANALYZE: """다음 주제에 대해 분석해주세요.

분석 주제: {query}

참고 컨텍스트:
{context}

분석 결과:""",

    Intent.CREATE: """다음 요청에 대해 창작물을 만들어주세요.

요청: {query}

참고 컨텍스트:
{context}

창작물:""",

    Intent.VALIDATE: """다음 내용을 검토하고 피드백을 제공해주세요.

검토 내용: {query}

참고 컨텍스트:
{context}

검토 결과:""",

    Intent.CHAT: """다음 질문에 답변해주세요.

질문: {query}

참고 컨텍스트:
{context}

답변:""",

    Intent.UNKNOWN: """다음 요청을 처리해주세요.

요청: {query}

참고 컨텍스트:
{context}

응답:""",
}


async def generate_node(state: UnifiedState) -> UnifiedState:
    """응답 생성 노드.

    검색된 컨텍스트와 도구 실행 결과를 종합하여 LLM 응답을 생성합니다.

    Args:
        state: 현재 상태

    Returns:
        업데이트된 상태 (final_response)
    """
    start_time = time.perf_counter()

    query = state.get("query", "")
    intent = state.get("intent", Intent.UNKNOWN)
    query_type = state.get("query_type", QueryType.AMBIGUOUS)
    auteur_key = state.get("auteur_key")
    node_outputs = state.get("node_outputs", {})

    # 에러 상태 확인
    error = state.get("error")
    if error:
        return state_with_response(
            state,
            final_response=f"죄송합니다. 요청 처리 중 오류가 발생했습니다: {error}",
            total_latency_ms=(time.perf_counter() - start_time) * 1000,
        )

    try:
        # =====================================================================
        # P0 Security: Attribution-gated Context Construction
        # =====================================================================

        # 1a. RAG 컨텍스트 구성 (Attribution 래핑)
        retrieved_docs = state.get("retrieved_docs", [])
        if retrieved_docs:
            # Attribution metadata로 래핑하여 간접 주입 방지
            rag_context = wrap_context_with_attribution(
                retrieved_docs,
                include_trust_level=True,
                max_docs=10,
            )
            logger.debug(
                f"[P0 Security] Attribution-wrapped context: {len(retrieved_docs)} docs"
            )
        else:
            rag_context = get_context_for_llm(state)

        # 1b. 도구 실행 결과 (별도 래핑)
        tool_context = _format_tool_outputs(node_outputs)
        full_context = f"{rag_context}\n\n{tool_context}".strip()

        # 2. 프롬프트 구성
        prompt = _build_prompt(
            query=query,
            intent=intent,
            context=full_context,
            auteur_key=auteur_key,
        )

        # 3. LLM 호출
        response = await _call_llm(
            prompt=prompt,
            query_type=query_type,
            auteur_key=auteur_key,
        )

        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"Generation complete: {len(response)} chars, latency={latency_ms:.1f}ms")

        return state_with_response(
            state,
            final_response=response,
            total_latency_ms=latency_ms,
        )

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return state_with_response(
            state,
            final_response=f"응답 생성 중 오류가 발생했습니다: {str(e)}",
            total_latency_ms=(time.perf_counter() - start_time) * 1000,
        )


def _format_tool_outputs(node_outputs: Dict[str, Any]) -> str:
    """도구 실행 결과를 텍스트로 포맷."""
    if not node_outputs:
        return ""

    parts = ["[도구 실행 결과]"]
    for tool, output in node_outputs.items():
        if isinstance(output, dict):
            if "error" in output:
                parts.append(f"\n{tool}: 오류 - {output['error']}")
            elif "output" in output:
                parts.append(f"\n{tool}:\n{output['output']}")
            else:
                parts.append(f"\n{tool}: {output}")
        else:
            parts.append(f"\n{tool}: {output}")

    return "\n".join(parts)


def _build_prompt(
    *,
    query: str,
    intent: Intent,
    context: str,
    auteur_key: Optional[str],
) -> str:
    """프롬프트 구성."""
    template = INTENT_TEMPLATES.get(intent, INTENT_TEMPLATES[Intent.UNKNOWN])

    # 거장 스타일 힌트 추가
    style_hint = ""
    if auteur_key:
        style_hint = f"\n\n[스타일 참고: {auteur_key} 감독의 기법과 철학을 반영하세요]"

    prompt = template.format(
        query=query,
        context=context or "(제공된 컨텍스트 없음)",
    )

    return prompt + style_hint


async def _call_llm(
    prompt: str,
    query_type: QueryType,
    auteur_key: Optional[str],
) -> str:
    """LLM 호출.

    GenerationClient 또는 Gemini API를 사용합니다.
    """
    try:
        # GenerationClient 시도
        from app.generation_client import GenerationClient

        client = GenerationClient()

        # 쿼리 타입에 따른 파라미터 조정
        temperature = 0.7
        max_tokens = 2048

        if query_type == QueryType.CREATIVE:
            temperature = 0.9
            max_tokens = 4096
        elif query_type == QueryType.SIMPLE_FACTUAL:
            temperature = 0.3
            max_tokens = 1024

        response = await client.generate(
            prompt=prompt,
            system_instruction=DEFAULT_SYSTEM_PROMPT,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.text if hasattr(response, "text") else str(response)

    except ImportError:
        logger.debug("GenerationClient not available, using fallback")
    except Exception as e:
        logger.warning(f"GenerationClient failed: {e}")

    try:
        # Gemini API 직접 호출 시도
        from google import genai

        client = genai.Client()
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config={
                "system_instruction": DEFAULT_SYSTEM_PROMPT,
                "temperature": 0.7,
                "max_output_tokens": 2048,
            },
        )

        return response.text

    except ImportError:
        logger.debug("Gemini API not available")
    except Exception as e:
        logger.warning(f"Gemini API failed: {e}")

    # 폴백: 스텁 응답
    return f"[응답 생성 실패] 요청: {prompt[:100]}..."


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    "generate_node",
]
