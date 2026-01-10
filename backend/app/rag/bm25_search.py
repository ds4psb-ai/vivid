"""BM25 Keyword Search with Reciprocal Rank Fusion (RRF).

Provides keyword-based search to complement vector similarity search.
Combines results using Reciprocal Rank Fusion for optimal hybrid retrieval.

Key Features:
- BM25 scoring using rank_bm25 library
- Real-time index updates
- RRF fusion for combining keyword + vector results
- Dimension-specific indexes

Usage:
    from app.rag.bm25_search import BM25Index, reciprocal_rank_fusion
    
    # Create index
    index = BM25Index()
    index.add_documents([
        {"id": "1", "text": "봉준호 감독의 계단 상징"},
        {"id": "2", "text": "기생충 영화 분석"},
    ])
    
    # Search
    results = index.search("봉준호 계단", top_k=5)
    
    # Combine with vector search via RRF
    hybrid = reciprocal_rank_fusion(
        keyword_results=keyword_results,
        vector_results=vector_results,
        k=60
    )
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Lazy import for rank_bm25 (optional dependency)
_bm25_module = None


def _get_bm25():
    """Lazy load rank_bm25 module."""
    global _bm25_module
    if _bm25_module is None:
        try:
            import rank_bm25
            _bm25_module = rank_bm25
        except ImportError:
            raise ImportError(
                "rank_bm25 not installed. "
                "Run: pip install rank-bm25"
            )
    return _bm25_module


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class BM25Result:
    """BM25 검색 결과."""
    id: str
    text: str
    score: float
    rank: int
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class FusedResult:
    """RRF 융합 결과."""
    id: str
    text: str
    rrf_score: float
    keyword_score: float = 0.0
    vector_score: float = 0.0
    keyword_rank: Optional[int] = None
    vector_rank: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# Tokenizer
# ============================================================================

class KoreanTokenizer:
    """한국어 토크나이저 (형태소 분석 없는 간단 버전)."""
    
    # 한글 자모 분리 패턴
    HANGUL_PATTERN = re.compile(r'[가-힣]+')
    WORD_PATTERN = re.compile(r'\b\w+\b')
    
    @staticmethod
    def tokenize(text: str) -> List[str]:
        """텍스트를 토큰으로 분리.
        
        한글은 2-gram으로, 영문은 단어 단위로 분리.
        """
        tokens = []
        text = text.lower()
        
        # 한글 처리: bi-gram for better matching
        korean_words = KoreanTokenizer.HANGUL_PATTERN.findall(text)
        for word in korean_words:
            tokens.append(word)
            # Add bi-grams for Korean
            if len(word) >= 2:
                for i in range(len(word) - 1):
                    tokens.append(word[i:i+2])
        
        # 영문/숫자 처리: 단어 단위
        english_words = re.findall(r'[a-z0-9]+', text)
        tokens.extend(english_words)
        
        return tokens


# ============================================================================
# BM25 Index
# ============================================================================

class BM25Index:
    """BM25 기반 키워드 검색 인덱스."""
    
    def __init__(
        self,
        tokenizer: Optional[KoreanTokenizer] = None,
        k1: float = 1.5,
        b: float = 0.75,
    ):
        """Initialize BM25 index.
        
        Args:
            tokenizer: 토크나이저 (None이면 KoreanTokenizer 사용)
            k1: BM25 k1 파라미터 (term frequency saturation)
            b: BM25 b 파라미터 (length normalization)
        """
        self.tokenizer = tokenizer or KoreanTokenizer()
        self.k1 = k1
        self.b = b
        
        self._documents: List[Dict[str, Any]] = []
        self._tokenized_corpus: List[List[str]] = []
        self._bm25 = None
    
    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        text_key: str = "text",
        id_key: str = "id",
    ) -> None:
        """문서 추가.
        
        Args:
            documents: 문서 리스트 (text, id 키 필요)
            text_key: 텍스트 필드 키
            id_key: ID 필드 키
        """
        rank_bm25 = _get_bm25()
        
        for doc in documents:
            text = doc.get(text_key, "")
            tokens = self.tokenizer.tokenize(text)
            
            self._documents.append(doc)
            self._tokenized_corpus.append(tokens)
        
        # Rebuild BM25 index
        if self._tokenized_corpus:
            self._bm25 = rank_bm25.BM25Okapi(
                self._tokenized_corpus,
                k1=self.k1,
                b=self.b,
            )
        
        logger.debug(f"[BM25] Added {len(documents)} documents, total={len(self._documents)}")
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.0,
    ) -> List[BM25Result]:
        """BM25 검색.
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            min_score: 최소 점수 임계값
            
        Returns:
            BM25Result 리스트 (점수 내림차순)
        """
        if not self._bm25 or not self._documents:
            return []
        
        query_tokens = self.tokenizer.tokenize(query)
        scores = self._bm25.get_scores(query_tokens)
        
        # Get sorted indices
        scored_indices = [
            (idx, score) for idx, score in enumerate(scores)
            if score > min_score
        ]
        scored_indices.sort(key=lambda x: x[1], reverse=True)
        
        # Build results
        results = []
        for rank, (idx, score) in enumerate(scored_indices[:top_k], start=1):
            doc = self._documents[idx]
            results.append(BM25Result(
                id=doc.get("id", str(idx)),
                text=doc.get("text", ""),
                score=score,
                rank=rank,
                metadata={k: v for k, v in doc.items() if k not in ["id", "text"]},
            ))
        
        logger.debug(f"[BM25] Query '{query[:30]}...' returned {len(results)} results")
        return results
    
    def clear(self) -> None:
        """인덱스 초기화."""
        self._documents = []
        self._tokenized_corpus = []
        self._bm25 = None
    
    @property
    def size(self) -> int:
        """인덱스 문서 수."""
        return len(self._documents)


# ============================================================================
# Reciprocal Rank Fusion (RRF)
# ============================================================================

def reciprocal_rank_fusion(
    result_lists: List[List[Dict[str, Any]]],
    k: int = 60,
    id_key: str = "id",
    score_key: str = "score",
) -> List[FusedResult]:
    """Reciprocal Rank Fusion으로 여러 검색 결과 융합.
    
    RRF Score = Σ (1 / (k + rank_i))
    
    Args:
        result_lists: 융합할 결과 리스트들
        k: RRF 상수 (기본 60, 높을수록 상위 결과 보정 약화)
        id_key: 문서 ID 키
        score_key: 점수 키
        
    Returns:
        FusedResult 리스트 (RRF 점수 내림차순)
    """
    # Collect all document scores and ranks
    doc_data: Dict[str, Dict[str, Any]] = {}  # id -> {text, metadata, scores, ranks}
    
    for list_idx, results in enumerate(result_lists):
        for rank, doc in enumerate(results, start=1):
            doc_id = doc.get(id_key, str(rank))
            
            if doc_id not in doc_data:
                doc_data[doc_id] = {
                    "text": doc.get("text", ""),
                    "metadata": {k: v for k, v in doc.items() if k not in [id_key, "text", score_key]},
                    "rrf_contributions": [],
                    "scores": [],
                    "ranks": [],
                }
            
            # Calculate RRF contribution for this list
            rrf_contribution = 1.0 / (k + rank)
            doc_data[doc_id]["rrf_contributions"].append(rrf_contribution)
            doc_data[doc_id]["scores"].append(doc.get(score_key, 0.0))
            doc_data[doc_id]["ranks"].append((list_idx, rank))
    
    # Calculate final RRF scores
    fused_results = []
    for doc_id, data in doc_data.items():
        rrf_score = sum(data["rrf_contributions"])
        
        # Determine keyword vs vector scores
        keyword_score = data["scores"][0] if len(data["scores"]) > 0 else 0.0
        vector_score = data["scores"][1] if len(data["scores"]) > 1 else 0.0
        
        # Get ranks
        keyword_rank = None
        vector_rank = None
        for list_idx, rank in data["ranks"]:
            if list_idx == 0:
                keyword_rank = rank
            elif list_idx == 1:
                vector_rank = rank
        
        fused_results.append(FusedResult(
            id=doc_id,
            text=data["text"],
            rrf_score=rrf_score,
            keyword_score=keyword_score,
            vector_score=vector_score,
            keyword_rank=keyword_rank,
            vector_rank=vector_rank,
            metadata=data["metadata"],
        ))
    
    # Sort by RRF score
    fused_results.sort(key=lambda x: x.rrf_score, reverse=True)
    
    logger.info(
        f"[RRF] Fused {len(result_lists)} result lists, "
        f"total unique docs={len(fused_results)}"
    )
    
    return fused_results


def hybrid_search_with_rrf(
    keyword_results: List[BM25Result],
    vector_results: List[Dict[str, Any]],
    k: int = 60,
    top_k: int = 10,
) -> List[FusedResult]:
    """BM25 + 벡터 검색 결과를 RRF로 융합.
    
    Args:
        keyword_results: BM25 검색 결과
        vector_results: 벡터 검색 결과
        k: RRF 상수
        top_k: 반환할 최대 결과 수
        
    Returns:
        FusedResult 리스트
    """
    # Convert BM25 results to dict format
    keyword_dicts = [
        {
            "id": r.id,
            "text": r.text,
            "score": r.score,
            **(r.metadata or {}),
        }
        for r in keyword_results
    ]
    
    fused = reciprocal_rank_fusion(
        result_lists=[keyword_dicts, vector_results],
        k=k,
    )
    
    return fused[:top_k]


# ============================================================================
# Dimension-specific Index Cache
# ============================================================================

_dimension_indexes: Dict[str, BM25Index] = {}


def get_dimension_bm25_index(dimension: str) -> BM25Index:
    """차원별 BM25 인덱스 반환 (싱글톤).
    
    Args:
        dimension: 차원 코드 (1D, 2D, AD, etc.)
        
    Returns:
        BM25Index for the dimension
    """
    if dimension not in _dimension_indexes:
        _dimension_indexes[dimension] = BM25Index()
        logger.info(f"[BM25] Created index for dimension: {dimension}")
    return _dimension_indexes[dimension]


def clear_dimension_index(dimension: str) -> None:
    """차원별 인덱스 초기화."""
    if dimension in _dimension_indexes:
        _dimension_indexes[dimension].clear()
        logger.info(f"[BM25] Cleared index for dimension: {dimension}")


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "BM25Index",
    "BM25Result",
    "FusedResult",
    "KoreanTokenizer",
    "reciprocal_rank_fusion",
    "hybrid_search_with_rrf",
    "get_dimension_bm25_index",
    "clear_dimension_index",
]
