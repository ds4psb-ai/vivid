"""
Quality Evaluator - 거장 DNA + RAG 기반 품질 평가

2026 Best Practice:
- G-Eval: Chain-of-Thought LLM evaluation (NeurIPS 2023)
- LLM-as-Judge for Premium/Dev tier
- Rule-based scoring for Free tier (zero LLM cost)
- Async evaluation with caching
- Multi-dimensional evaluation: Groundedness, Relevance, Coherence, Creativity, Safety
"""

from __future__ import annotations

import re
from typing import Optional, TYPE_CHECKING, Literal

from app.uqsl.models import QualityScore, CandidateResult

if TYPE_CHECKING:
    from app.rag.hybrid_rag import HybridRAGResult


# =============================================================================
# G-Eval Evaluation Prompts (Chain-of-Thought)
# =============================================================================

GEVAL_PROMPTS = {
    "coherence": {
        "criteria": """Coherence (1-5): The collective quality of all sentences.
We align this dimension with the DUC quality criterion:
- Structuring: The text should be well-structured and well-organized.
- Logical Flow: The text should follow a logical flow of ideas.
- Transitions: The text should have smooth transitions between ideas.""",
        "steps": """Evaluation Steps:
1. Read the text carefully and identify the main topic and key points.
2. Check if the text has a clear beginning, middle, and end.
3. Assess if the ideas flow logically from one to the next.
4. Check for smooth transitions between sentences and paragraphs.
5. Rate the overall coherence on a scale of 1-5.""",
    },
    "creativity": {
        "criteria": """Creativity (1-5): The originality and novelty of the content.
Consider these dimensions:
- Originality: Novel ideas or unexpected connections.
- Expressiveness: Vivid language and imagery.
- Risk-taking: Willingness to explore unconventional approaches.
- Artistry: Aesthetic quality and craftsmanship.""",
        "steps": """Evaluation Steps:
1. Identify any novel or unexpected ideas in the text.
2. Look for vivid imagery, metaphors, or unique expressions.
3. Assess if the text takes creative risks or explores unconventional angles.
4. Evaluate the aesthetic quality and craft of the writing.
5. Rate the overall creativity on a scale of 1-5.""",
    },
    "relevance": {
        "criteria": """Relevance (1-5): How well the text addresses the given query or task.
Consider these dimensions:
- Topic Alignment: Does it address the main question/topic?
- Completeness: Does it cover all aspects of the query?
- Focus: Does it stay on topic without unnecessary tangents?
- Usefulness: Does it provide actionable or meaningful information?""",
        "steps": """Evaluation Steps:
1. Identify the main query or task the text should address.
2. Check if the text directly addresses the query.
3. Assess if all aspects of the query are covered.
4. Check for unnecessary tangents or off-topic content.
5. Rate the overall relevance on a scale of 1-5.""",
    },
    "groundedness": {
        "criteria": """Groundedness (1-5): How well the text is grounded in source material.
Consider these dimensions:
- Factual Accuracy: Information aligns with sources.
- Citation Quality: Proper attribution to sources.
- Hallucination Avoidance: No fabricated information.
- Source Integration: Smooth incorporation of source material.""",
        "steps": """Evaluation Steps:
1. Identify claims or facts stated in the text.
2. Check if each claim can be traced to a source.
3. Look for any fabricated or unsupported information.
4. Assess how smoothly source material is integrated.
5. Rate the overall groundedness on a scale of 1-5.""",
    },
}

GEVAL_SCORE_TEMPLATE = """You will be given a text to evaluate.

{criteria}

{steps}

Text to evaluate:
{text}

{context_info}

Think step by step about each criterion. Then provide your evaluation.
At the end, on a new line, output ONLY the score as a single number from 1 to 5.

Evaluation:"""


EvaluationMode = Literal["heuristic", "llm_simple", "geval"]


class QualityEvaluator:
    """
    거장 DNA + RAG 기반 품질 평가 (2026 G-Eval + LLM-as-Judge)

    Tiers:
    - Free: Rule-based heuristics only (no LLM cost)
    - Premium: G-Eval Chain-of-Thought for creativity/coherence
    - Dev: Full G-Eval evaluation with detailed reasoning

    G-Eval (NeurIPS 2023):
    - Chain-of-Thought prompting for better evaluation reasoning
    - Structured criteria and evaluation steps
    - 1-5 scale normalized to 0-1
    """

    def __init__(
        self,
        use_llm_judge: bool = False,
        tier: str = "free",
        use_geval: bool = True,
    ):
        self.use_llm_judge = use_llm_judge
        self.tier = tier
        self.use_geval = use_geval
        self._reranker = None  # Lazy load

    @property
    def evaluation_mode(self) -> EvaluationMode:
        """Determine evaluation mode based on tier and settings."""
        if not self.use_llm_judge:
            return "heuristic"
        if self.use_geval and self.tier in ("premium", "dev"):
            return "geval"
        return "llm_simple"

    async def evaluate(
        self,
        candidate: CandidateResult,
        context: Optional["HybridRAGResult"] = None,
        query: Optional[str] = None,
    ) -> QualityScore:
        """
        단일 후보 품질 평가

        Args:
            candidate: Candidate result to evaluate
            context: RAG context for groundedness checking
            query: Original query for relevance evaluation

        Returns:
            QualityScore with all dimensions
        """
        content = candidate.content
        mode = self.evaluation_mode

        # 1. Safety check (always rule-based)
        safety = await self._safety_check(content)

        # 2. Evaluate based on mode
        if mode == "geval":
            # G-Eval: Chain-of-Thought evaluation
            scores = await self._geval_evaluate(content, context, query)
            return QualityScore(
                groundedness=scores.get("groundedness", 0.5),
                relevance=scores.get("relevance", 0.5),
                coherence=scores.get("coherence", 0.5),
                creativity=scores.get("creativity", 0.5),
                safety=safety,
            )
        elif mode == "llm_simple":
            # Simple LLM-as-Judge
            relevance = await self._compute_relevance(content, context)
            groundedness = await self._check_groundedness(content, context)
            coherence = await self._llm_judge_coherence(content)
            creativity = await self._llm_judge_creativity(content)
        else:
            # Heuristic (Free tier)
            relevance = await self._compute_relevance(content, context)
            groundedness = await self._check_groundedness(content, context)
            coherence = self._compute_coherence_heuristic(content)
            creativity = self._compute_creativity_heuristic(content)

        return QualityScore(
            groundedness=groundedness,
            relevance=relevance,
            coherence=coherence,
            creativity=creativity,
            safety=safety,
        )

    async def _geval_evaluate(
        self,
        text: str,
        context: Optional["HybridRAGResult"] = None,
        query: Optional[str] = None,
    ) -> dict[str, float]:
        """
        G-Eval Chain-of-Thought evaluation (Premium/Dev tier).

        Uses structured prompts with evaluation criteria and steps.
        Returns all dimension scores in parallel for efficiency.
        """
        import asyncio

        async def evaluate_dimension(dimension: str) -> tuple[str, float]:
            try:
                prompt_config = GEVAL_PROMPTS.get(dimension)
                if not prompt_config:
                    return dimension, 0.5

                # Build context info
                context_info = ""
                if dimension in ("groundedness", "relevance") and context:
                    sources = getattr(context, "notebooklm_sources", []) or []
                    if sources:
                        source_texts = [getattr(s, "content", "")[:200] for s in sources[:3]]
                        context_info = f"Source materials:\n" + "\n---\n".join(source_texts)
                if dimension == "relevance" and query:
                    context_info = f"Original query: {query}\n{context_info}"

                prompt = GEVAL_SCORE_TEMPLATE.format(
                    criteria=prompt_config["criteria"],
                    steps=prompt_config["steps"],
                    text=text[:2000],  # Limit text length
                    context_info=context_info,
                )

                from app.generation_client import generate_with_gemini
                result = await generate_with_gemini(prompt, temperature=0.0)

                # Parse score (1-5) and normalize to (0-1)
                score = self._parse_geval_score(result)
                return dimension, score

            except Exception:
                # Fallback to heuristic
                if dimension == "coherence":
                    return dimension, self._compute_coherence_heuristic(text)
                elif dimension == "creativity":
                    return dimension, self._compute_creativity_heuristic(text)
                elif dimension == "relevance":
                    return dimension, await self._compute_relevance(text, context)
                elif dimension == "groundedness":
                    return dimension, await self._check_groundedness(text, context)
                return dimension, 0.5

        # Evaluate all dimensions in parallel
        dimensions = ["coherence", "creativity", "relevance", "groundedness"]
        results = await asyncio.gather(*[evaluate_dimension(d) for d in dimensions])

        return dict(results)

    def _parse_geval_score(self, result: str) -> float:
        """Parse G-Eval score (1-5) and normalize to (0-1)."""
        try:
            # Find last number in response (G-Eval outputs reasoning then score)
            lines = result.strip().split("\n")
            for line in reversed(lines):
                match = re.search(r'\b([1-5])\b', line.strip())
                if match:
                    score = int(match.group(1))
                    # Normalize 1-5 to 0-1
                    return (score - 1) / 4.0
            return 0.5
        except (ValueError, AttributeError):
            return 0.5

    async def evaluate_batch(
        self,
        candidates: list[CandidateResult],
        context: Optional["HybridRAGResult"] = None,
        query: Optional[str] = None,
    ) -> list[QualityScore]:
        """Evaluate multiple candidates in parallel."""
        import asyncio
        return await asyncio.gather(*[
            self.evaluate(c, context, query) for c in candidates
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
def get_quality_evaluator(
    tier: str = "free",
    use_geval: bool = True,
) -> QualityEvaluator:
    """
    Get quality evaluator for tier.

    Args:
        tier: User tier (free/premium/dev)
        use_geval: Use G-Eval Chain-of-Thought (default: True for premium/dev)

    Returns:
        Configured QualityEvaluator instance
    """
    use_llm = tier in ("premium", "dev")
    return QualityEvaluator(
        use_llm_judge=use_llm,
        tier=tier,
        use_geval=use_geval,
    )
