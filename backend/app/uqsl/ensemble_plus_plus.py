"""
Ensemble++ 3-Way Router - NeurIPS 2025 기반 앙상블

arXiv:2407.13195 (Ensemble++ framework) 구현

핵심 아이디어:
- A 단독: Backend A만 사용 (빠름)
- B 단독: Backend B만 사용 (정확)
- A+B 앙상블: 둘 다 실행 후 결합 (최적 조합)

Thompson Sampling으로 어떤 전략이 더 좋은지 학습합니다.
"""

from __future__ import annotations

import asyncio
from typing import Literal, Optional, TYPE_CHECKING

from scipy.stats import beta as beta_dist

from app.uqsl.models import CandidateResult, ThreeWayResult
from app.uqsl.thompson_sampling import ThompsonSamplingRouter

if TYPE_CHECKING:
    from app.rag.hybrid_rag import HybridRAGResult


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
    ) -> "HybridRAGResult":
        """
        스마트 앙상블: 각 시스템의 강점 결합

        Strategy:
        - Use NotebookLM's answer as base (more grounded)
        - Augment with Qdrant's additional context
        - Preserve source references from both
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

        # Extract answers
        answer_a = getattr(result_a, "answer", str(result_a))
        answer_b = getattr(result_b, "answer", str(result_b))

        # Merge strategy: B as primary, A as supplementary
        if len(answer_b) > 100:
            merged_answer = f"{answer_b}\n\n---\n\n**추가 컨텍스트 (벡터 검색)**\n{answer_a[:500]}"
        else:
            merged_answer = f"{answer_a}\n\n**거장 인사이트**\n{answer_b}"

        # Calculate confidence
        conf_a = getattr(result_a, "confidence", 0.5)
        conf_b = getattr(result_b, "confidence", 0.5)
        merged_confidence = (conf_a + conf_b) / 2 + 0.1  # Ensemble bonus

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
            strategy_used="ensemble_ab",
            retrieval_count=(
                getattr(result_a, "retrieval_count", 0) +
                getattr(result_b, "retrieval_count", 0)
            ),
        )

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
