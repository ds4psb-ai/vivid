"""Unified Reciprocal Rank Fusion (RRF) Implementation.

기존 4개 RRF 구현을 단일 함수로 통합:
- app/rag/hybrid_rag.py:_weighted_rrf_fusion
- app/rag/router/orchestrator.py:_rrf_fusion
- app/rag/multi_rag/retriever.py:reciprocal_rank_fusion
- app/rag/backends/graph_qdrant.py:_weighted_rrf_fusion

Algorithm:
    RRF Score = Σ (weight_i / (k + rank_i))

    - k: 순위 차이를 완화하는 상수 (기본 60)
    - weight: 소스별 가중치 (기본 1.0)

References:
- "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods"
  Cormack et al., SIGIR 2009

Usage:
    from app.core.utils.rrf import reciprocal_rank_fusion, weighted_rrf

    # 기본 RRF (동일 가중치)
    fused = reciprocal_rank_fusion([
        [("doc1", 0.9), ("doc2", 0.8)],  # 소스 1
        [("doc2", 0.95), ("doc3", 0.7)], # 소스 2
    ])

    # 가중치 RRF
    fused = weighted_rrf([
        ("notebooklm", 1.5, [doc1, doc2]),
        ("qdrant", 1.0, [doc3, doc4]),
    ])
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")


# =============================================================================
# Basic RRF (Ranked Lists of IDs)
# =============================================================================


def reciprocal_rank_fusion(
    ranked_lists: List[List[Tuple[str, float]]],
    *,
    k: int = 60,
    limit: Optional[int] = None,
    min_score: float = 0.0,
) -> List[Tuple[str, float]]:
    """Reciprocal Rank Fusion 알고리즘.

    여러 랭킹 리스트를 RRF로 융합합니다.

    Args:
        ranked_lists: [(doc_id, original_score), ...] 리스트의 리스트
                     각 리스트는 점수 내림차순 정렬 가정
        k: RRF 상수 (기본 60, 순위 차이 완화)
        limit: 반환할 최대 문서 수 (None이면 전체)
        min_score: 최소 RRF 스코어 임계값

    Returns:
        융합된 [(doc_id, rrf_score), ...] 리스트 (내림차순)

    Example:
        >>> lists = [
        ...     [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7)],
        ...     [("doc2", 0.95), ("doc1", 0.85), ("doc4", 0.6)],
        ... ]
        >>> reciprocal_rank_fusion(lists, k=60)
        [("doc1", 0.0328...), ("doc2", 0.0328...), ("doc3", 0.0163...), ("doc4", 0.0161...)]
    """
    rrf_scores: Dict[str, float] = {}

    for ranked_list in ranked_lists:
        for rank, (doc_id, _original_score) in enumerate(ranked_list, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank)

    # 스코어순 정렬
    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    # 최소 스코어 필터링
    if min_score > 0:
        sorted_results = [(doc_id, score) for doc_id, score in sorted_results if score >= min_score]

    # Limit 적용
    if limit is not None:
        sorted_results = sorted_results[:limit]

    return sorted_results


# =============================================================================
# Weighted RRF (With Source Weights)
# =============================================================================


@dataclass
class DocWithMeta:
    """문서와 메타데이터를 함께 저장."""

    doc_id: str
    content: str
    original_score: float
    source: str
    metadata: Dict[str, Any]


def weighted_rrf(
    source_results: List[Tuple[str, float, List[Any]]],
    *,
    k: int = 60,
    limit: int = 10,
    min_score: float = 0.0,
    id_extractor: Optional[Callable[[Any], str]] = None,
    score_extractor: Optional[Callable[[Any], float]] = None,
) -> List[Tuple[str, float, Any]]:
    """Weighted Reciprocal Rank Fusion.

    소스별 가중치를 적용한 RRF 융합.

    Args:
        source_results: [(source_id, weight, docs), ...] 형식
                       docs는 점수 내림차순 정렬 가정
        k: RRF 상수 (기본 60)
        limit: 반환할 최대 문서 수
        min_score: 최소 RRF 스코어 임계값
        id_extractor: 문서에서 ID 추출 함수 (기본: doc.id 또는 doc["id"])
        score_extractor: 문서에서 점수 추출 함수 (기본: doc.score 또는 doc["score"])

    Returns:
        [(doc_id, rrf_score, doc_object), ...] 리스트 (내림차순)

    Example:
        >>> results = [
        ...     ("notebooklm", 1.5, [doc1, doc2]),
        ...     ("qdrant", 1.0, [doc3, doc1]),
        ... ]
        >>> weighted_rrf(results, k=60, limit=5)
    """
    # 기본 추출 함수
    def default_id_extractor(doc: Any) -> str:
        if hasattr(doc, "id"):
            return doc.id
        if hasattr(doc, "doc_id"):
            return doc.doc_id
        if isinstance(doc, dict):
            return doc.get("id") or doc.get("doc_id", str(id(doc)))
        return str(id(doc))

    def default_score_extractor(doc: Any) -> float:
        if hasattr(doc, "score"):
            return float(doc.score)
        if isinstance(doc, dict):
            return float(doc.get("score", 0.0))
        return 0.0

    get_id = id_extractor or default_id_extractor
    get_score = score_extractor or default_score_extractor

    # RRF 스코어 및 문서 저장
    doc_scores: Dict[str, float] = {}
    doc_objects: Dict[str, Any] = {}  # 가장 높은 원본 점수의 문서 유지

    for source_id, weight, docs in source_results:
        for rank, doc in enumerate(docs, start=1):
            doc_id = get_id(doc)
            rrf_contribution = weight / (k + rank)

            doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + rrf_contribution

            # 더 높은 원본 점수의 문서 유지
            if doc_id not in doc_objects:
                doc_objects[doc_id] = doc
            else:
                existing_score = get_score(doc_objects[doc_id])
                new_score = get_score(doc)
                if new_score > existing_score:
                    doc_objects[doc_id] = doc

    # 스코어순 정렬
    sorted_ids = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)

    # 결과 구성
    results: List[Tuple[str, float, Any]] = []
    for doc_id in sorted_ids:
        score = doc_scores[doc_id]
        if score >= min_score:
            results.append((doc_id, score, doc_objects[doc_id]))
        if len(results) >= limit:
            break

    return results


# =============================================================================
# Merge and Dedupe (Utility)
# =============================================================================


def merge_and_dedupe(
    doc_lists: List[List[Any]],
    *,
    id_extractor: Optional[Callable[[Any], str]] = None,
    score_extractor: Optional[Callable[[Any], float]] = None,
    limit: Optional[int] = None,
) -> List[Any]:
    """여러 문서 리스트를 병합하고 중복 제거.

    RRF를 사용하지 않고 단순히 중복을 제거하고 점수순 정렬.

    Args:
        doc_lists: 문서 리스트의 리스트
        id_extractor: 문서에서 ID 추출 함수
        score_extractor: 문서에서 점수 추출 함수
        limit: 반환할 최대 문서 수

    Returns:
        중복 제거된 문서 리스트 (점수 내림차순)
    """
    def default_id_extractor(doc: Any) -> str:
        if hasattr(doc, "id"):
            return doc.id
        if hasattr(doc, "doc_id"):
            return doc.doc_id
        if isinstance(doc, dict):
            return doc.get("id") or doc.get("doc_id", str(id(doc)))
        return str(id(doc))

    def default_score_extractor(doc: Any) -> float:
        if hasattr(doc, "score"):
            return float(doc.score)
        if isinstance(doc, dict):
            return float(doc.get("score", 0.0))
        return 0.0

    get_id = id_extractor or default_id_extractor
    get_score = score_extractor or default_score_extractor

    # 중복 제거 (가장 높은 점수 유지)
    seen: Dict[str, Any] = {}
    for doc_list in doc_lists:
        for doc in doc_list:
            doc_id = get_id(doc)
            if doc_id not in seen:
                seen[doc_id] = doc
            else:
                if get_score(doc) > get_score(seen[doc_id]):
                    seen[doc_id] = doc

    # 점수순 정렬
    sorted_docs = sorted(seen.values(), key=get_score, reverse=True)

    if limit is not None:
        sorted_docs = sorted_docs[:limit]

    return sorted_docs


# =============================================================================
# Compatibility Wrappers
# =============================================================================


def rrf_from_retrieval_results(
    backend_results: List[Tuple[str, float, List[Any]]],
    *,
    k: int = 60,
    limit: int = 10,
    min_score: float = 0.0,
) -> List[Any]:
    """RetrievalResult 호환 RRF.

    기존 hybrid_rag.py의 _weighted_rrf_fusion과 호환되는 래퍼.

    Args:
        backend_results: [(backend_id, weight, List[RetrievalResult]), ...]
        k: RRF 상수
        limit: 최대 결과 수
        min_score: 최소 점수

    Returns:
        RRF 융합된 RetrievalResult 리스트
    """
    def id_extractor(r: Any) -> str:
        if hasattr(r, "doc_id"):
            return r.doc_id
        if isinstance(r, dict):
            return r.get("doc_id", str(id(r)))
        return str(id(r))

    def score_extractor(r: Any) -> float:
        if hasattr(r, "score"):
            return float(r.score)
        if isinstance(r, dict):
            return float(r.get("score", 0.0))
        return 0.0

    fused = weighted_rrf(
        backend_results,
        k=k,
        limit=limit,
        min_score=min_score,
        id_extractor=id_extractor,
        score_extractor=score_extractor,
    )

    # 원본 객체에 RRF 스코어 주입
    results = []
    for doc_id, rrf_score, doc in fused:
        # 새 객체 생성 대신 원본 반환 (필요시 score 수정)
        if hasattr(doc, "_replace"):  # namedtuple
            results.append(doc._replace(score=rrf_score))
        elif isinstance(doc, dict):
            doc_copy = dict(doc)
            doc_copy["rrf_score"] = rrf_score
            results.append(doc_copy)
        else:
            # 원본 반환 (RRF 스코어는 별도 추적)
            results.append(doc)

    return results


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    "reciprocal_rank_fusion",
    "weighted_rrf",
    "merge_and_dedupe",
    "rrf_from_retrieval_results",
    "DocWithMeta",
]
