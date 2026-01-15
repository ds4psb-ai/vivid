"""
Ensemble++ 3-Way Router - NeurIPS 2025 기반 앙상블

2026 Best Practice:
- arXiv:2407.13195 (Ensemble++ framework) 구현
- Reciprocal Rank Fusion (RRF) for merging ranked results
- Confidence-aware weighted blending
- Query-type adaptive merging

핵심 아이디어:
- A 단독: Backend A만 사용 (빠름)
- B 단독: Backend B만 사용 (정확)
- A+B 앙상블: 둘 다 실행 후 결합 (최적 조합)

Thompson Sampling으로 어떤 전략이 더 좋은지 학습합니다.

References:
- arXiv:2407.13195: Ensemble++ for Multi-Armed Bandits
- NeurIPS 2024: Hybrid RAG Ensemble Methods
- SIGIR 2025: Reciprocal Rank Fusion Best Practices
"""

from __future__ import annotations

import asyncio
import re
from typing import Literal, Optional, TYPE_CHECKING

from scipy.stats import beta as beta_dist

from app.uqsl.models import CandidateResult, ThreeWayResult
from app.uqsl.thompson_sampling import ThompsonSamplingRouter

if TYPE_CHECKING:
    from app.rag.hybrid_rag import HybridRAGResult


# =============================================================================
# Merge Strategy Types
# =============================================================================

MergeStrategy = Literal[
    "weighted_blend",      # Confidence-weighted blending
    "rrf",                 # Reciprocal Rank Fusion
    "b_primary",           # B (NotebookLM) as primary, A as supplement
    "quality_gate",        # Use higher quality result
    "adaptive",            # Query-type adaptive selection
]


class EnsemblePlusPlusRouter:
    """
    Ensemble++ 프레임워크 (NeurIPS 2025 - arXiv:2407.13195)

    3-way 비교를 통해 최적의 백엔드 조합을 학습합니다.
    - A: Qdrant 하이브리드 검색 (빠름, 벡터 기반)
    - B: NotebookLM (정확, 거장 DNA 기반)
    - AB: 앙상블 (둘의 강점 결합)
    """

    def __init__(self):
        # Thompson Sampling arms for 3-way selection
        self.arms = {
            "qdrant_only": {"alpha": 1, "beta": 1},
            "notebooklm_only": {"alpha": 1, "beta": 1},
            "ensemble_ab": {"alpha": 2, "beta": 1},  # Slight prior for ensemble
        }
        self.thompson = ThompsonSamplingRouter()

    async def get_three_way_results(
        self,
        query: str,
        dimension: str,
        auteur_key: Optional[str] = None,
    ) -> dict[Literal["a", "b", "ab"], CandidateResult]:
        """
        A, B, A+B 3가지 결과 동시 생성

        Args:
            query: User query
            dimension: Dimension code (e.g., "AD", "1D")
            auteur_key: Optional auteur key for NotebookLM

        Returns:
            Dict with 'a', 'b', 'ab' keys containing CandidateResult
        """
        import time

        # Parallel execution of A and B
        start = time.perf_counter()
        result_a, result_b = await asyncio.gather(
            self._retrieve_qdrant_only(query, dimension),
            self._retrieve_notebooklm_only(query, auteur_key),
        )
        parallel_time = int((time.perf_counter() - start) * 1000)

        # Smart merge for AB
        result_ab = self._smart_merge(result_a, result_b, query)

        # Convert to CandidateResult format
        return {
            "a": CandidateResult(
                idx=0,
                content=result_a.answer if hasattr(result_a, "answer") else str(result_a),
                metadata={
                    "backend": "qdrant_hybrid",
                    "confidence": getattr(result_a, "confidence", 0.5),
                },
                latency_ms=parallel_time,
                backend_used="qdrant_hybrid",
            ),
            "b": CandidateResult(
                idx=1,
                content=result_b.answer if hasattr(result_b, "answer") else str(result_b),
                metadata={
                    "backend": "notebooklm",
                    "confidence": getattr(result_b, "confidence", 0.5),
                    "auteur_key": auteur_key,
                },
                latency_ms=parallel_time,
                backend_used="notebooklm",
            ),
            "ab": CandidateResult(
                idx=2,
                content=result_ab.answer if hasattr(result_ab, "answer") else str(result_ab),
                metadata={
                    "backend": "ensemble_ab",
                    "confidence": max(
                        getattr(result_a, "confidence", 0.5),
                        getattr(result_b, "confidence", 0.5),
                    ),
                    "source_backends": ["qdrant_hybrid", "notebooklm"],
                },
                latency_ms=parallel_time,
                backend_used="ensemble_ab",
            ),
        }

    async def select_best_arm(self) -> Literal["a", "b", "ab"]:
        """Thompson Sampling으로 최적 arm 선택"""
        samples = {
            "a": beta_dist.rvs(
                self.arms["qdrant_only"]["alpha"],
                self.arms["qdrant_only"]["beta"],
            ),
            "b": beta_dist.rvs(
                self.arms["notebooklm_only"]["alpha"],
                self.arms["notebooklm_only"]["beta"],
            ),
            "ab": beta_dist.rvs(
                self.arms["ensemble_ab"]["alpha"],
                self.arms["ensemble_ab"]["beta"],
            ),
        }

        return max(samples, key=samples.get)

    async def get_recommended_result(
        self,
        query: str,
        dimension: str,
        auteur_key: Optional[str] = None,
    ) -> ThreeWayResult:
        """Get all three results with recommendation"""
        results = await self.get_three_way_results(query, dimension, auteur_key)
        recommended = await self.select_best_arm()

        return ThreeWayResult(
            query=query,
            results=results,
            recommended=recommended,
            arms_stats={
                arm_key: self.arms[arm_key]
                for arm_key in self.arms
            },
        )

    def _smart_merge(
        self,
        result_a: "HybridRAGResult",
        result_b: "HybridRAGResult",
        query: str,
        strategy: MergeStrategy = "adaptive",
    ) -> "HybridRAGResult":
        """
        스마트 앙상블: 각 시스템의 강점 결합 (2026 Enhanced)

        Strategies:
        - weighted_blend: Confidence-weighted answer blending
        - rrf: Reciprocal Rank Fusion for source ranking
        - b_primary: NotebookLM primary, Qdrant supplementary
        - quality_gate: Use higher confidence result
        - adaptive: Query-type based strategy selection
        """
        from dataclasses import dataclass

        @dataclass
        class MergedResult:
            query: str
            answer: str
            confidence: float
            notebooklm_sources: list
            vertex_sources: list
            grounding_sources: list
            strategy_used: str
            retrieval_count: int

        # Extract answers and confidence
        answer_a = getattr(result_a, "answer", str(result_a))
        answer_b = getattr(result_b, "answer", str(result_b))
        conf_a = getattr(result_a, "confidence", 0.5)
        conf_b = getattr(result_b, "confidence", 0.5)

        # Adaptive strategy selection based on query type
        if strategy == "adaptive":
            strategy = self._select_adaptive_strategy(query, conf_a, conf_b, answer_a, answer_b)

        # Apply selected merge strategy
        if strategy == "weighted_blend":
            merged_answer, merged_confidence = self._weighted_blend(
                answer_a, answer_b, conf_a, conf_b
            )
        elif strategy == "rrf":
            merged_answer, merged_confidence = self._rrf_merge(
                result_a, result_b, query
            )
        elif strategy == "quality_gate":
            merged_answer, merged_confidence = self._quality_gate_merge(
                answer_a, answer_b, conf_a, conf_b
            )
        else:  # b_primary (default)
            merged_answer, merged_confidence = self._b_primary_merge(
                answer_a, answer_b, conf_a, conf_b
            )

        return MergedResult(
            query=query,
            answer=merged_answer,
            confidence=min(1.0, merged_confidence),
            notebooklm_sources=getattr(result_b, "notebooklm_sources", []),
            vertex_sources=getattr(result_a, "vertex_sources", []),
            grounding_sources=(
                getattr(result_a, "grounding_sources", []) +
                getattr(result_b, "grounding_sources", [])
            ),
            strategy_used=f"ensemble_ab:{strategy}",
            retrieval_count=(
                getattr(result_a, "retrieval_count", 0) +
                getattr(result_b, "retrieval_count", 0)
            ),
        )

    def _select_adaptive_strategy(
        self,
        query: str,
        conf_a: float,
        conf_b: float,
        answer_a: str,
        answer_b: str,
    ) -> MergeStrategy:
        """
        Query-type adaptive strategy selection (2026 Best Practice)

        Based on query characteristics, select optimal merge strategy.
        """
        query_lower = query.lower()

        # 거장/스타일 관련 쿼리 → NotebookLM 우선
        auteur_keywords = ["봉준호", "구로사와", "kubrick", "spielberg", "스타일", "style", "거장", "감독"]
        if any(kw in query_lower for kw in auteur_keywords):
            return "b_primary"

        # 기술적/구체적 쿼리 → Quality Gate
        technical_keywords = ["how to", "방법", "코드", "구현", "설정", "config"]
        if any(kw in query_lower for kw in technical_keywords):
            return "quality_gate"

        # 짧은 답변은 둘 다 활용 → Weighted Blend
        if len(answer_a) < 200 and len(answer_b) < 200:
            return "weighted_blend"

        # 신뢰도 차이가 큰 경우 → Quality Gate
        if abs(conf_a - conf_b) > 0.3:
            return "quality_gate"

        # Default: B primary (NotebookLM has grounding)
        return "b_primary"

    def _weighted_blend(
        self,
        answer_a: str,
        answer_b: str,
        conf_a: float,
        conf_b: float,
    ) -> tuple[str, float]:
        """Confidence-weighted blending"""
        total_conf = conf_a + conf_b
        if total_conf == 0:
            total_conf = 1.0

        weight_a = conf_a / total_conf
        weight_b = conf_b / total_conf

        # Order answers by weight
        if weight_b >= weight_a:
            merged = f"{answer_b}\n\n---\n\n**추가 관점** (신뢰도: {conf_a:.0%})\n{answer_a}"
        else:
            merged = f"{answer_a}\n\n---\n\n**거장 인사이트** (신뢰도: {conf_b:.0%})\n{answer_b}"

        merged_conf = (conf_a * weight_a + conf_b * weight_b) + 0.05  # Small ensemble bonus
        return merged, merged_conf

    def _rrf_merge(
        self,
        result_a: "HybridRAGResult",
        result_b: "HybridRAGResult",
        query: str,
        k: int = 60,
    ) -> tuple[str, float]:
        """
        Reciprocal Rank Fusion (2025 Standard)

        RRF Score = Σ 1/(k + rank_i)
        """
        answer_a = getattr(result_a, "answer", str(result_a))
        answer_b = getattr(result_b, "answer", str(result_b))

        # Get sources from both results
        sources_a = getattr(result_a, "grounding_sources", [])
        sources_b = getattr(result_b, "notebooklm_sources", [])

        # Calculate RRF scores for sources
        rrf_scores = {}

        for i, src in enumerate(sources_a):
            src_id = str(src) if not hasattr(src, "id") else src.id
            rrf_scores[src_id] = rrf_scores.get(src_id, 0) + 1.0 / (k + i + 1)

        for i, src in enumerate(sources_b):
            src_id = str(src) if not hasattr(src, "id") else src.id
            rrf_scores[src_id] = rrf_scores.get(src_id, 0) + 1.0 / (k + i + 1)

        # Merge answers with RRF confidence
        total_rrf = sum(rrf_scores.values()) if rrf_scores else 1.0
        normalized_rrf = min(1.0, total_rrf / 2)  # Normalize

        merged = f"{answer_b}\n\n---\n\n**검색 기반 컨텍스트**\n{answer_a}"
        return merged, 0.5 + normalized_rrf * 0.4  # Base 0.5 + RRF bonus

    def _quality_gate_merge(
        self,
        answer_a: str,
        answer_b: str,
        conf_a: float,
        conf_b: float,
    ) -> tuple[str, float]:
        """Quality gate: Use higher confidence result as primary"""
        if conf_b >= conf_a:
            merged = f"{answer_b}"
            if conf_a > 0.5 and answer_a:
                merged += f"\n\n---\n\n**보충 자료** (신뢰도: {conf_a:.0%})\n{answer_a[:300]}..."
            return merged, conf_b + 0.05
        else:
            merged = f"{answer_a}"
            if conf_b > 0.5 and answer_b:
                merged += f"\n\n---\n\n**거장 관점** (신뢰도: {conf_b:.0%})\n{answer_b[:300]}..."
            return merged, conf_a + 0.05

    def _b_primary_merge(
        self,
        answer_a: str,
        answer_b: str,
        conf_a: float,
        conf_b: float,
    ) -> tuple[str, float]:
        """B (NotebookLM) as primary, A as supplement"""
        if len(answer_b) > 100:
            merged = f"{answer_b}\n\n---\n\n**추가 컨텍스트 (벡터 검색)**\n{answer_a[:500]}"
        else:
            merged = f"{answer_a}\n\n**거장 인사이트**\n{answer_b}"

        merged_conf = (conf_a + conf_b) / 2 + 0.1  # Ensemble bonus
        return merged, merged_conf

    async def update_arm(
        self,
        arm: Literal["a", "b", "ab"],
        reward: bool,
    ) -> None:
        """피드백으로 arm 업데이트"""
        arm_map = {
            "a": "qdrant_only",
            "b": "notebooklm_only",
            "ab": "ensemble_ab",
        }
        arm_id = arm_map[arm]

        if reward:
            self.arms[arm_id]["alpha"] += 1
        else:
            self.arms[arm_id]["beta"] += 1

    async def _retrieve_qdrant_only(
        self,
        query: str,
        dimension: str,
    ) -> "HybridRAGResult":
        """Qdrant만 사용하는 검색"""
        try:
            from app.rag.hybrid_rag import hybrid_query

            return await hybrid_query(
                query=query,
                dimension=dimension,
                backends=["qdrant"],
            )
        except ImportError:
            # Mock for testing
            return self._mock_result(query, "qdrant")

    async def _retrieve_notebooklm_only(
        self,
        query: str,
        auteur_key: Optional[str],
    ) -> "HybridRAGResult":
        """NotebookLM만 사용하는 검색"""
        try:
            from app.rag.hybrid_rag import hybrid_query

            return await hybrid_query(
                query=query,
                auteur_key=auteur_key,
                backends=["notebooklm"],
            )
        except ImportError:
            # Mock for testing
            return self._mock_result(query, "notebooklm")

    def _mock_result(self, query: str, backend: str):
        """Mock result for testing"""
        from dataclasses import dataclass

        @dataclass
        class MockResult:
            query: str
            answer: str
            confidence: float
            notebooklm_sources: list
            vertex_sources: list
            grounding_sources: list
            strategy_used: str
            retrieval_count: int

        return MockResult(
            query=query,
            answer=f"[{backend}] Mock answer for: {query[:50]}...",
            confidence=0.7,
            notebooklm_sources=[],
            vertex_sources=[],
            grounding_sources=[],
            strategy_used=backend,
            retrieval_count=5,
        )

    def get_arm_stats(self) -> dict:
        """Get current arm statistics"""
        stats = {}
        for arm_key, arm_data in self.arms.items():
            alpha = arm_data["alpha"]
            beta = arm_data["beta"]
            total = alpha + beta - 2  # Subtract priors
            success_rate = alpha / (alpha + beta)

            stats[arm_key] = {
                "alpha": alpha,
                "beta": beta,
                "total_trials": total,
                "success_rate": success_rate,
            }
        return stats


# Singleton instance
_router: Optional[EnsemblePlusPlusRouter] = None


def get_ensemble_router() -> EnsemblePlusPlusRouter:
    """Get or create Ensemble++ router singleton"""
    global _router
    if _router is None:
        _router = EnsemblePlusPlusRouter()
    return _router
