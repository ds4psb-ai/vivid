"""Retrieval Node - 통합 검색기.

2개 검색 오케스트레이터를 통합:
1. app/rag/router/orchestrator.py - MultiRAG 오케스트레이터
2. app/rag/multi_rag/retriever.py - 멀티모달 리트리버

검색 흐름:
1. 선택된 소스에 병렬 쿼리
2. RRF 융합
3. (선택적) Reranker 적용
4. P0 Security: Content sanitization + Attribution metadata
5. Evidence refs 생성

Usage:
    from app.core.nodes.retrieve import retrieve_node

    result_state = await retrieve_node(state)
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from app.core.unified_schemas import (
    Dimension,
    QueryType,
    RetrievedDoc,
)
from app.core.unified_state import UnifiedState, state_with_retrieval, should_skip_node
from app.core.utils.rrf import weighted_rrf
from app.core.utils.sanitize import sanitize_retrieved_docs
from app.core.utils.attribution import format_evidence_refs, AttributedSource

logger = logging.getLogger(__name__)

# 소스별 타임아웃 (ms)
SOURCE_TIMEOUT_MS = 10000

# 소스별 기본 가중치
SOURCE_WEIGHTS = {
    "notebooklm": 1.5,  # 거장 지식 우선
    "qdrant": 1.0,
    "vertex": 0.8,
    "web": 0.6,
}

# RRF 파라미터
RRF_K = 60
DEFAULT_TOP_K = 10


async def retrieve_node(state: UnifiedState) -> UnifiedState:
    """검색 노드.

    선택된 소스에서 병렬로 검색하고 RRF로 융합합니다.

    Args:
        state: 현재 상태 (query, selected_sources 필수)

    Returns:
        업데이트된 상태 (retrieved_docs, evidence_refs)
    """
    # Skip retrieval 체크
    if should_skip_node(state, "retrieve") or state.get("skip_retrieval", False):
        logger.info("Skipping retrieval (skip_retrieval=True)")
        return state

    start_time = time.perf_counter()

    query = state.get("query", "")
    sources = state.get("selected_sources", ["qdrant"])
    dimension = state.get("dimension")
    auteur_key = state.get("auteur_key")
    sub_queries = state.get("sub_queries", [])

    if not query:
        return state

    try:
        # 1. 병렬 검색
        source_results = await _parallel_retrieve(
            query=query,
            sources=sources,
            dimension=dimension,
            auteur_key=auteur_key,
            sub_queries=sub_queries,
        )

        # 2. RRF 융합
        fused_results = _apply_rrf_fusion(source_results)

        # 3. (선택적) Reranker
        query_type = state.get("query_type", QueryType.AMBIGUOUS)
        if query_type in [QueryType.MULTI_HOP, QueryType.DOMAIN_SPECIFIC]:
            fused_results = await _apply_reranker(query, fused_results)

        # 4. 문서 변환
        retrieved_docs = [
            {
                "id": doc_id,
                "content": doc.get("content", ""),
                "score": score,
                "source": doc.get("source", "unknown"),
                "metadata": doc.get("metadata", {}),
            }
            for doc_id, score, doc in fused_results[:DEFAULT_TOP_K]
        ]

        # =====================================================================
        # P0 Security: Content Sanitization + Attribution
        # =====================================================================

        # 5a. 검색 결과 정제 (간접 프롬프트 주입 방지)
        retrieved_docs = sanitize_retrieved_docs(
            retrieved_docs,
            content_key="content",
            max_content_length=8000,
        )

        # 5b. Attribution metadata 추가
        for doc in retrieved_docs:
            attributed = AttributedSource.from_doc(doc)
            doc["_attribution"] = {
                "trust_level": attributed.trust_level,
                "content_hash": attributed.content_hash,
                "source_type": attributed.source_type,
            }

        logger.debug(
            f"[P0 Security] Sanitized {len(retrieved_docs)} docs, "
            f"trust_levels: {[d.get('_attribution', {}).get('trust_level') for d in retrieved_docs[:3]]}"
        )

        # 6. Evidence refs 생성 (Vivid 표준 형식)
        evidence_refs = format_evidence_refs(retrieved_docs)

        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Retrieval complete: {len(retrieved_docs)} docs from {len(sources)} sources, "
            f"latency={latency_ms:.1f}ms"
        )

        return state_with_retrieval(
            state,
            retrieved_docs=retrieved_docs,
            evidence_refs=evidence_refs,
            source_results={s: r for s, r in source_results},
            rrf_scores={doc_id: score for doc_id, score, _ in fused_results},
        )

    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        return state_with_retrieval(
            state,
            retrieved_docs=[],
            evidence_refs=[],
        )


async def _parallel_retrieve(
    *,
    query: str,
    sources: List[str],
    dimension: Optional[Dimension],
    auteur_key: Optional[str],
    sub_queries: List[str],
) -> List[Tuple[str, List[Dict[str, Any]]]]:
    """선택된 소스에서 병렬 검색.

    Returns:
        [(source_name, [doc, ...]), ...]
    """
    tasks = []

    for source in sources:
        task = _retrieve_from_source(
            source=source,
            query=query,
            dimension=dimension,
            auteur_key=auteur_key,
        )
        tasks.append((source, task))

    # 서브쿼리도 검색 (있는 경우)
    for i, sub_query in enumerate(sub_queries[:3]):  # 최대 3개
        task = _retrieve_from_source(
            source=sources[0] if sources else "qdrant",
            query=sub_query,
            dimension=dimension,
            auteur_key=auteur_key,
        )
        tasks.append((f"sub_{i}", task))

    # 병렬 실행 (타임아웃 적용)
    results = []
    async_tasks = [task for _, task in tasks]
    task_names = [name for name, _ in tasks]

    try:
        completed = await asyncio.wait_for(
            asyncio.gather(*async_tasks, return_exceptions=True),
            timeout=SOURCE_TIMEOUT_MS / 1000,
        )

        for name, result in zip(task_names, completed):
            if isinstance(result, Exception):
                logger.warning(f"Source {name} failed: {result}")
                continue
            if result:
                results.append((name, result))

    except asyncio.TimeoutError:
        logger.warning(f"Parallel retrieval timed out after {SOURCE_TIMEOUT_MS}ms")

    return results


async def _retrieve_from_source(
    *,
    source: str,
    query: str,
    dimension: Optional[Dimension],
    auteur_key: Optional[str],
) -> List[Dict[str, Any]]:
    """특정 소스에서 검색."""
    try:
        if source == "notebooklm":
            return await _retrieve_notebooklm(query, dimension, auteur_key)
        elif source == "qdrant":
            return await _retrieve_qdrant(query, dimension, auteur_key)
        elif source == "vertex":
            return await _retrieve_vertex(query, dimension, auteur_key)
        elif source == "web":
            return await _retrieve_web(query)
        else:
            logger.warning(f"Unknown source: {source}")
            return []
    except Exception as e:
        logger.error(f"Failed to retrieve from {source}: {e}")
        return []


async def _retrieve_notebooklm(
    query: str,
    dimension: Optional[Dimension],
    auteur_key: Optional[str],
) -> List[Dict[str, Any]]:
    """NotebookLM (Tier0)에서 검색."""
    try:
        from app.rag.tier0_notebooklm import query_notebooklm

        results = await query_notebooklm(
            query=query,
            auteur_key=auteur_key,
            dimension=dimension.value if dimension else None,
        )

        return [
            {
                "id": f"notebooklm:{i}",
                "content": r.content if hasattr(r, "content") else str(r),
                "score": r.score if hasattr(r, "score") else 1.0,
                "source": "notebooklm",
                "metadata": r.metadata if hasattr(r, "metadata") else {},
            }
            for i, r in enumerate(results or [])
        ]

    except ImportError:
        logger.debug("NotebookLM not available")
        return []
    except Exception as e:
        logger.error(f"NotebookLM query failed: {e}")
        return []


async def _retrieve_qdrant(
    query: str,
    dimension: Optional[Dimension],
    auteur_key: Optional[str],
) -> List[Dict[str, Any]]:
    """Qdrant (Tier1)에서 검색."""
    try:
        from app.rag.tier1_dimension_rag import search_dimension_rag

        results = await search_dimension_rag(
            query=query,
            dimension=dimension.value if dimension else None,
            auteur_key=auteur_key,
            top_k=DEFAULT_TOP_K,
        )

        return [
            {
                "id": r.doc_id if hasattr(r, "doc_id") else f"qdrant:{i}",
                "content": r.content if hasattr(r, "content") else str(r),
                "score": r.score if hasattr(r, "score") else 0.5,
                "source": "qdrant",
                "metadata": r.metadata if hasattr(r, "metadata") else {},
            }
            for i, r in enumerate(results or [])
        ]

    except ImportError:
        logger.debug("Qdrant RAG not available")
        return []
    except Exception as e:
        logger.error(f"Qdrant query failed: {e}")
        return []


async def _retrieve_vertex(
    query: str,
    dimension: Optional[Dimension],
    auteur_key: Optional[str],
) -> List[Dict[str, Any]]:
    """Vertex AI Search에서 검색."""
    try:
        from app.rag.backends.vertex_search import search_vertex

        results = await search_vertex(
            query=query,
            top_k=DEFAULT_TOP_K,
        )

        return [
            {
                "id": r.doc_id if hasattr(r, "doc_id") else f"vertex:{i}",
                "content": r.content if hasattr(r, "content") else str(r),
                "score": r.score if hasattr(r, "score") else 0.5,
                "source": "vertex",
                "metadata": r.metadata if hasattr(r, "metadata") else {},
            }
            for i, r in enumerate(results or [])
        ]

    except ImportError:
        logger.debug("Vertex Search not available")
        return []
    except Exception as e:
        logger.error(f"Vertex query failed: {e}")
        return []


async def _retrieve_web(query: str) -> List[Dict[str, Any]]:
    """Web 검색 (Google Grounding)."""
    try:
        from app.rag.backends.web_grounding import search_web

        results = await search_web(query=query, top_k=5)

        return [
            {
                "id": f"web:{i}",
                "content": r.content if hasattr(r, "content") else str(r),
                "score": r.score if hasattr(r, "score") else 0.3,
                "source": "web",
                "metadata": {
                    "url": r.url if hasattr(r, "url") else None,
                    "title": r.title if hasattr(r, "title") else None,
                },
            }
            for i, r in enumerate(results or [])
        ]

    except ImportError:
        logger.debug("Web grounding not available")
        return []
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return []


def _apply_rrf_fusion(
    source_results: List[Tuple[str, List[Dict[str, Any]]]],
) -> List[Tuple[str, float, Dict[str, Any]]]:
    """RRF 융합 적용.

    Returns:
        [(doc_id, rrf_score, doc), ...]
    """
    if not source_results:
        return []

    # weighted_rrf 형식으로 변환
    weighted_inputs = []
    for source_name, docs in source_results:
        weight = SOURCE_WEIGHTS.get(source_name.split("_")[0], 1.0)
        weighted_inputs.append((source_name, weight, docs))

    # ID 추출 함수
    def id_extractor(doc: Dict[str, Any]) -> str:
        return doc.get("id", str(id(doc)))

    def score_extractor(doc: Dict[str, Any]) -> float:
        return doc.get("score", 0.0)

    return weighted_rrf(
        weighted_inputs,
        k=RRF_K,
        limit=DEFAULT_TOP_K * 2,  # Reranker를 위해 여유 있게
        id_extractor=id_extractor,
        score_extractor=score_extractor,
    )


async def _apply_reranker(
    query: str,
    results: List[Tuple[str, float, Dict[str, Any]]],
) -> List[Tuple[str, float, Dict[str, Any]]]:
    """Reranker 적용."""
    if not results:
        return results

    try:
        from app.rag.reranker import rerank_documents

        docs = [doc for _, _, doc in results]
        reranked = await rerank_documents(query, docs)

        # 재정렬된 결과 반환
        return [
            (r.get("id", f"reranked:{i}"), r.get("rerank_score", 0.0), r)
            for i, r in enumerate(reranked)
        ]

    except ImportError:
        logger.debug("Reranker not available")
        return results
    except Exception as e:
        logger.warning(f"Reranking failed: {e}")
        return results


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    "retrieve_node",
]
