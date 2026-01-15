"""
Quality Evaluator - 거장 DNA + RAG 기반 품질 평가

2026 Best Practice:
- LLM-as-Judge for Premium/Dev tier
- Rule-based scoring for Free tier (zero LLM cost)
- Async evaluation with caching
"""

from __future__ import annotations

import re
from typing import Optional, TYPE_CHECKING

from app.uqsl.models import QualityScore, CandidateResult

if TYPE_CHECKING:
    from app.rag.hybrid_rag import HybridRAGResult


class QualityEvaluator:
    """
    거장 DNA + RAG 기반 품질 평가 (2026 LLM-as-Judge Best Practice)

    Tiers:
    - Free: Rule-based heuristics only (no LLM cost)
    - Premium: LLM-as-Judge for creativity/coherence
    - Dev: Full LLM evaluation with explanations
    """

    def __init__(self, use_llm_judge: bool = False, tier: str = "free"):
        self.use_llm_judge = use_llm_judge
        self.tier = tier
        self._reranker = None  # Lazy load

    async def evaluate(
        self,
        candidate: CandidateResult,
        context: Optional["HybridRAGResult"] = None,
    ) -> QualityScore:
        """
        단일 후보 품질 평가

        Args:
            candidate: Candidate result to evaluate
            context: RAG context for groundedness checking

        Returns:
            QualityScore with all dimensions
        """
        content = candidate.content

        # 1. Rule-based scores (Free tier - no LLM)
        relevance = await self._compute_relevance(content, context)
        groundedness = await self._check_groundedness(content, context)
        safety = await self._safety_check(content)

        # 2. Coherence and Creativity
        if self.use_llm_judge and self.tier in ("premium", "dev"):
            coherence = await self._llm_judge_coherence(content)
            creativity = await self._llm_judge_creativity(content)
        else:
            coherence = self._compute_coherence_heuristic(content)
            creativity = self._compute_creativity_heuristic(content)

        return QualityScore(
            groundedness=groundedness,
            relevance=relevance,
            coherence=coherence,
            creativity=creativity,
            safety=safety,
        )

    async def evaluate_batch(
        self,
        candidates: list[CandidateResult],
        context: Optional["HybridRAGResult"] = None,
    ) -> list[QualityScore]:
        """Evaluate multiple candidates"""
        import asyncio
        return await asyncio.gather(*[
            self.evaluate(c, context) for c in candidates
        ])

    async def _compute_relevance(
        self,
        text: str,
        context: Optional["HybridRAGResult"],
    ) -> float:
        """
        P4 Reranker 기반 관련도 (Cross-encoder)

        Uses BAAI/bge-reranker-base or similar model.
        """
        if not context or not context.query:
            return 0.5  # Neutral without context

        try:
            if self._reranker is None:
                from app.rag.reranker import get_reranker
                self._reranker = await get_reranker()

            score = await self._reranker.score(query=context.query, document=text)
            return max(0.0, min(1.0, score))
        except Exception:
            # Fallback to simple keyword matching
            return self._simple_relevance(text, context.query)

    def _simple_relevance(self, text: str, query: str) -> float:
        """Simple keyword-based relevance fallback"""
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        if not query_words:
            return 0.5
        overlap = len(query_words & text_words)
        return min(1.0, overlap / len(query_words) * 1.5)

    async def _check_groundedness(
        self,
        text: str,
        context: Optional["HybridRAGResult"],
    ) -> float:
        """
        거장 DNA 그라운딩 체크 (Tier0 NotebookLM 소스 기반)

        Checks if generated content references source materials.
        """
        if not context:
            return 0.5  # Neutral without context

        sources = getattr(context, "notebooklm_sources", []) or []
        if not sources:
            return 0.5

        # Count source references in text
        text_lower = text.lower()
        citation_count = 0

        for source in sources:
            # Check for title/name mentions
            title = getattr(source, "title", "") or ""
            if title.lower() in text_lower:
                citation_count += 1
                continue

            # Check for content overlap (simple)
            source_content = getattr(source, "content", "") or ""
            if source_content:
                # Check if any significant phrase from source appears
                phrases = [p.strip() for p in source_content.split(".") if len(p.strip()) > 20]
                for phrase in phrases[:5]:  # Check first 5 phrases
                    if phrase.lower() in text_lower:
                        citation_count += 0.5
                        break

        # Normalize score
        base_score = min(1.0, citation_count / max(len(sources), 1) + 0.3)
        return base_score

    def _compute_coherence_heuristic(self, text: str) -> float:
        """
        규칙 기반 일관성 (Free tier)

        Checks:
        - Sentence structure
        - Logical flow markers
        - Proper punctuation
        """
        if not text:
            return 0.0

        sentences = [s.strip() for s in text.split(".") if s.strip()]
        if len(sentences) < 2:
            return 0.4

        score = 0.5

        # Check for transition words (coherence markers)
        coherence_markers = [
            "therefore", "however", "moreover", "furthermore", "consequently",
            "그래서", "하지만", "또한", "따라서", "결과적으로", "왜냐하면",
        ]
        text_lower = text.lower()
        marker_count = sum(1 for m in coherence_markers if m in text_lower)
        score += min(0.2, marker_count * 0.05)

        # Check average sentence length (too short or too long is bad)
        avg_len = sum(len(s) for s in sentences) / len(sentences)
        if 30 < avg_len < 150:
            score += 0.2
        elif 20 < avg_len < 200:
            score += 0.1

        # Check for proper paragraph structure
        if "\n\n" in text or len(text) < 500:
            score += 0.1

        return min(1.0, score)

    def _compute_creativity_heuristic(self, text: str) -> float:
        """
        규칙 기반 창의성 (Free tier)

        Measures vocabulary diversity (type-token ratio).
        """
        if not text:
            return 0.0

        # Tokenize (simple split)
        words = re.findall(r'\w+', text.lower())
        if len(words) < 10:
            return 0.3

        # Type-token ratio (vocabulary diversity)
        unique_words = set(words)
        ttr = len(unique_words) / len(words)

        # Creative language markers
        creative_markers = [
            "imagine", "envision", "transform", "unexpected", "unique",
            "상상", "독특", "창의", "새로운", "혁신", "예상치 못한",
        ]
        text_lower = text.lower()
        marker_count = sum(1 for m in creative_markers if m in text_lower)

        # Base score from TTR
        base_score = min(1.0, ttr * 1.5)

        # Boost for creative markers
        base_score += min(0.2, marker_count * 0.05)

        return min(1.0, base_score)

    async def _llm_judge_creativity(self, text: str) -> float:
        """LLM-as-Judge 창의성 평가 (Premium/Dev tier)"""
        try:
            from app.generation_client import generate_with_gemini

            prompt = f"""Rate the creativity of this text on a scale of 0 to 1.
Consider: originality, unexpected connections, novel expressions, vivid imagery.

Text:
{text[:1500]}

Return ONLY a decimal number between 0 and 1, nothing else."""

            result = await generate_with_gemini(prompt, temperature=0.0)
            return self._parse_score(result)
        except Exception:
            return self._compute_creativity_heuristic(text)

    async def _llm_judge_coherence(self, text: str) -> float:
        """LLM-as-Judge 일관성 평가 (Premium/Dev tier)"""
        try:
            from app.generation_client import generate_with_gemini

            prompt = f"""Rate the coherence of this text on a scale of 0 to 1.
Consider: logical flow, consistency, clear structure, smooth transitions.

Text:
{text[:1500]}

Return ONLY a decimal number between 0 and 1, nothing else."""

            result = await generate_with_gemini(prompt, temperature=0.0)
            return self._parse_score(result)
        except Exception:
            return self._compute_coherence_heuristic(text)

    async def _safety_check(self, text: str) -> float:
        """
        안전성 체크 (규칙 기반)

        Basic keyword filtering. Expand with proper content moderation in production.
        """
        if not text:
            return 1.0

        text_lower = text.lower()

        # Basic unsafe patterns (expand in production)
        unsafe_patterns = [
            "hack", "exploit", "attack", "illegal", "weapon",
            "불법", "해킹", "공격", "무기",
        ]

        violations = sum(1 for p in unsafe_patterns if p in text_lower)

        # High penalty for violations
        return max(0.0, 1.0 - violations * 0.25)

    def _parse_score(self, result: str) -> float:
        """Parse LLM score output"""
        try:
            # Extract first number from response
            match = re.search(r'(\d+\.?\d*)', result.strip())
            if match:
                score = float(match.group(1))
                return max(0.0, min(1.0, score))
            return 0.5
        except (ValueError, AttributeError):
            return 0.5


# Factory function
def get_quality_evaluator(tier: str = "free") -> QualityEvaluator:
    """Get quality evaluator for tier"""
    use_llm = tier in ("premium", "dev")
    return QualityEvaluator(use_llm_judge=use_llm, tier=tier)
