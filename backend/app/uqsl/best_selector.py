"""
Best Selector - 최적 결과 선택기

4가지 선택 전략:
- auto: Quality Score 기반 자동 선택
- hitl: 사용자 선택 대기
- hybrid: 상위 N개 필터 후 사용자/자동 선택
- llm_judge: LLM으로 최적 선택 (Dev tier)
"""

from __future__ import annotations

import uuid
from typing import Literal

from app.uqsl.models import CandidateResult, QualityScore, SelectionResult


class BestSelector:
    """최적 결과 선택기 (4가지 전략)"""

    async def select_best(
        self,
        candidates: list[CandidateResult],
        scores: list[QualityScore],
        strategy: Literal["auto", "hitl", "hybrid", "llm_judge"] = "auto",
        auto_threshold: float = 0.85,
        top_k_for_hybrid: int = 2,
    ) -> SelectionResult:
        """
        최적 후보 선택

        Args:
            candidates: List of generated candidates
            scores: Quality scores for each candidate
            strategy: Selection strategy
            auto_threshold: Score threshold for auto-selection in hybrid mode
            top_k_for_hybrid: Number of top candidates for HITL

        Returns:
            SelectionResult with selected candidate and metadata
        """
        session_id = str(uuid.uuid4())

        # Attach scores to candidates
        for c, s in zip(candidates, scores):
            c.quality_score = s

        if strategy == "auto":
            return await self._auto_select(session_id, candidates, scores)
        elif strategy == "hitl":
            return await self._hitl_select(session_id, candidates)
        elif strategy == "hybrid":
            return await self._hybrid_select(
                session_id, candidates, scores, auto_threshold, top_k_for_hybrid
            )
        elif strategy == "llm_judge":
            return await self._llm_judge_select(session_id, candidates)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    async def _auto_select(
        self,
        session_id: str,
        candidates: list[CandidateResult],
        scores: list[QualityScore],
    ) -> SelectionResult:
        """
        자동 선택: Quality Score 최고점

        Zero human interaction, fully automated based on quality scores.
        """
        if not candidates or not scores:
            raise ValueError("No candidates to select from")

        best_idx = max(range(len(scores)), key=lambda i: scores[i].total_score)

        return SelectionResult(
            session_id=session_id,
            selected=candidates[best_idx],
            method="auto",
            confidence=scores[best_idx].total_score,
            arms_used=[c.backend_used for c in candidates],
            all_candidates=candidates,
        )

    async def _hitl_select(
        self,
        session_id: str,
        candidates: list[CandidateResult],
    ) -> SelectionResult:
        """
        HITL: 사용자 선택 대기

        Returns all candidates for user selection.
        The actual selection is made via /uqsl/select endpoint.
        """
        if not candidates:
            raise ValueError("No candidates to select from")

        return SelectionResult(
            session_id=session_id,
            selected=candidates[0],  # Placeholder - user will override
            method="hitl",
            confidence=0.0,  # User decides
            arms_used=[c.backend_used for c in candidates],
            all_candidates=candidates,
        )

    async def _hybrid_select(
        self,
        session_id: str,
        candidates: list[CandidateResult],
        scores: list[QualityScore],
        threshold: float,
        top_k: int,
    ) -> SelectionResult:
        """
        하이브리드: 상위 N개 필터 후 자동/사용자 선택

        If top score exceeds threshold, auto-select.
        Otherwise, return top K for user selection.
        """
        if not candidates or not scores:
            raise ValueError("No candidates to select from")

        # Sort by score (descending)
        sorted_pairs = sorted(
            zip(candidates, scores),
            key=lambda x: x[1].total_score,
            reverse=True,
        )

        top_candidates = [c for c, _ in sorted_pairs[:top_k]]
        top_scores = [s for _, s in sorted_pairs[:top_k]]

        # If top score exceeds threshold, auto-select
        if top_scores[0].total_score >= threshold:
            return SelectionResult(
                session_id=session_id,
                selected=top_candidates[0],
                method="auto",  # Promoted from hybrid to auto
                confidence=top_scores[0].total_score,
                arms_used=[c.backend_used for c in candidates],
                all_candidates=top_candidates,  # Only return filtered candidates
            )

        # Otherwise, return top K for HITL
        return SelectionResult(
            session_id=session_id,
            selected=top_candidates[0],  # Placeholder for HITL
            method="hybrid",
            confidence=top_scores[0].total_score,
            arms_used=[c.backend_used for c in candidates],
            all_candidates=top_candidates,
        )

    async def _llm_judge_select(
        self,
        session_id: str,
        candidates: list[CandidateResult],
    ) -> SelectionResult:
        """
        LLM Judge: LLM으로 최고 선택 (Dev tier)

        Uses LLM to compare candidates and select the best one.
        """
        if not candidates:
            raise ValueError("No candidates to select from")

        if len(candidates) == 1:
            return SelectionResult(
                session_id=session_id,
                selected=candidates[0],
                method="llm_judge",
                confidence=0.9,
                arms_used=[candidates[0].backend_used],
                all_candidates=candidates,
            )

        try:
            from app.generation_client import generate_with_gemini

            # Build comparison prompt
            candidates_text = "\n\n".join([
                f"[Option {c.idx}]:\n{c.content[:500]}..."
                if len(c.content) > 500 else f"[Option {c.idx}]:\n{c.content}"
                for c in candidates
            ])

            prompt = f"""You are an expert content judge. Compare these options and select the BEST one.
Consider: quality, coherence, creativity, usefulness, and clarity.

{candidates_text}

Return ONLY the option number (0, 1, 2, etc.) of the best option, nothing else."""

            result = await generate_with_gemini(prompt, temperature=0.0)

            # Parse result
            try:
                best_idx = int(result.strip().split()[0])
                best_idx = max(0, min(best_idx, len(candidates) - 1))
            except (ValueError, IndexError):
                best_idx = 0

            return SelectionResult(
                session_id=session_id,
                selected=candidates[best_idx],
                method="llm_judge",
                confidence=0.9,  # High confidence from LLM
                arms_used=[c.backend_used for c in candidates],
                all_candidates=candidates,
            )

        except Exception as e:
            # Fallback to auto-select with quality scores
            import logging
            logging.warning(f"LLM judge failed, falling back to auto: {e}")

            # Use quality scores if available
            if all(c.quality_score for c in candidates):
                best_idx = max(
                    range(len(candidates)),
                    key=lambda i: candidates[i].quality_score.total_score
                )
            else:
                best_idx = 0

            return SelectionResult(
                session_id=session_id,
                selected=candidates[best_idx],
                method="auto",  # Fallback
                confidence=0.7,
                arms_used=[c.backend_used for c in candidates],
                all_candidates=candidates,
            )


# Factory function
def get_best_selector() -> BestSelector:
    """Get best selector instance"""
    return BestSelector()
