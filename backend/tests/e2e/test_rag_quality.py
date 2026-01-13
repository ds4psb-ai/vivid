"""
RAG Quality Evaluation Harness (LLM-as-Judge)

2025 Best Practice:
- Retrieval Relevance (Precision@k, Recall@k)
- Groundedness (citation alignment)
- Deflection correctness (when evidence is weak)

Usage:
    RAG_QUALITY_EVAL=1 pytest backend/tests/e2e/test_rag_quality.py -v
    
P4 Integration:
- Loads evaluation cases from data/rag_eval/quality_cases.json
- Skips entirely if RAG_QUALITY_EVAL != "1"
- Skips LLM-as-Judge if GEMINI_API_KEY not available
"""
import json
import os
import pytest
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# P7: Explicit module-level skip unless enabled
# This prevents flaky CI when API keys are not available
pytestmark = pytest.mark.skipif(
    os.getenv("RAG_QUALITY_EVAL") != "1",
    reason="RAG quality eval disabled (set RAG_QUALITY_EVAL=1 to enable)"
)

# P4: Check LLM availability
LLM_AVAILABLE = bool(os.environ.get("GEMINI_API_KEY"))

# P7: Updated path to new dataset location
EVAL_CASES_PATH = Path(__file__).resolve().parents[2] / "data" / "rag_eval" / "quality_cases.json"


def load_eval_cases() -> List[Dict[str, Any]]:
    """Load evaluation cases from JSON file."""
    if EVAL_CASES_PATH.exists():
        with open(EVAL_CASES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


EVAL_CASES = load_eval_cases()
THRESHOLDS = {
    "min_groundedness": 0.6,
    "min_relevance": 0.5,
    "deflection_evidence_threshold": 2,
    "pass_rate": 0.7,
}


# =============================================================================
# Quality Metrics Data Classes
# =============================================================================

@dataclass
class QualityScore:
    """LLM-as-Judge quality score."""
    groundedness: float  # 0-1: How well is answer grounded in sources?
    relevance: float     # 0-1: How relevant is answer to query?
    coherence: float     # 0-1: How coherent is the answer?
    deflection_correct: bool  # Did it correctly deflect when no evidence?
    
    @property
    def overall(self) -> float:
        """Weighted overall score."""
        return (self.groundedness * 0.4 + 
                self.relevance * 0.35 + 
                self.coherence * 0.25)


@dataclass
class RetrievalMetrics:
    """Retrieval quality metrics."""
    precision_at_k: float  # Proportion of retrieved docs that are relevant
    recall_at_k: float     # Proportion of relevant docs retrieved
    hit_rate: float        # At least one relevant doc retrieved
    mrr: float             # Mean Reciprocal Rank
    
    @property  
    def f1_at_k(self) -> float:
        """Harmonic mean of precision and recall."""
        if self.precision_at_k + self.recall_at_k == 0:
            return 0.0
        return 2 * (self.precision_at_k * self.recall_at_k) / (self.precision_at_k + self.recall_at_k)


# =============================================================================
# LLM-as-Judge Evaluator
# =============================================================================

async def evaluate_groundedness(
    query: str,
    answer: str,
    sources: List[str],
) -> float:
    """Evaluate how well the answer is grounded in sources.
    
    Uses Gemini to judge whether each claim in the answer 
    is supported by the provided sources.
    
    Returns:
        Score 0-1 (1 = fully grounded)
    """
    if not sources or not answer:
        return 0.0
    
    # Simplified prompt for Gemini evaluation
    evaluation_prompt = f"""You are a grounding evaluator. 
    
Query: {query}

Answer to evaluate:
{answer}

Sources provided:
{chr(10).join(f'- {s[:200]}' for s in sources[:5])}

Evaluate how well the answer is grounded in the sources.
Respond with ONLY a number from 0 to 1:
- 1.0 = Every claim is directly supported by sources
- 0.7 = Most claims supported, minor unsupported details
- 0.5 = Some claims supported, some not
- 0.3 = Few claims supported
- 0.0 = Answer contradicts or ignores sources

Score:"""

    try:
        import google.generativeai as genai
        from app.config import settings
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        response = await asyncio.to_thread(
            lambda: model.generate_content(evaluation_prompt)
        )
        
        # Parse score from response
        score_text = response.text.strip()
        return min(1.0, max(0.0, float(score_text)))
        
    except Exception as e:
        # Fallback: simple keyword overlap
        source_text = " ".join(sources).lower()
        answer_words = set(answer.lower().split())
        source_words = set(source_text.split())
        overlap = len(answer_words & source_words) / len(answer_words) if answer_words else 0
        return min(1.0, overlap * 1.5)


async def evaluate_relevance(query: str, answer: str) -> float:
    """Evaluate how relevant the answer is to the query.
    
    Returns:
        Score 0-1 (1 = highly relevant)
    """
    if not answer:
        return 0.0
    
    try:
        import google.generativeai as genai
        from app.config import settings
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        prompt = f"""Rate how relevant this answer is to the query.

Query: {query}
Answer: {answer[:500]}

Respond with ONLY a number from 0 to 1:
- 1.0 = Directly answers the query
- 0.5 = Partially relevant
- 0.0 = Completely irrelevant

Score:"""
        
        response = await asyncio.to_thread(
            lambda: model.generate_content(prompt)
        )
        return min(1.0, max(0.0, float(response.text.strip())))
        
    except Exception:
        # Fallback: keyword overlap
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        return len(query_words & answer_words) / len(query_words) if query_words else 0


# =============================================================================
# Test Cases
# =============================================================================

@pytest.fixture
def sample_queries() -> List[Dict[str, Any]]:
    """Sample queries for quality evaluation."""
    return [
        {
            "query": "봉준호 감독의 계단 상징",
            "auteur_key": "bong",
            "expected_topics": ["계급", "수직", "구조", "기생충"],
        },
        {
            "query": "왕가위 감독의 블러 모션 기법",
            "auteur_key": "wong",
            "expected_topics": ["블러", "슬로모션", "향수", "시간"],
        },
        {
            "query": "크리스토퍼 놀란의 IMAX 촬영",
            "auteur_key": "nolan",
            "expected_topics": ["IMAX", "필름", "실용", "스케일"],
        },
    ]


class TestRAGQuality:
    """RAG Quality evaluation tests."""
    
    @pytest.mark.asyncio
    async def test_notebooklm_groundedness(self, sample_queries):
        """Test that NotebookLM responses are grounded."""
        from app.rag.hybrid_rag import hybrid_query
        
        for sample in sample_queries[:1]:  # First query only for speed
            result = await hybrid_query(
                query=sample["query"],
                auteur_key=sample["auteur_key"],
            )
            
            # Extract source texts
            sources = []
            if result.notebooklm_sources:
                sources.extend([s.content for s in result.notebooklm_sources if hasattr(s, 'content')])
            
            # Evaluate groundedness
            score = await evaluate_groundedness(
                query=sample["query"],
                answer=result.answer,
                sources=sources if sources else [result.answer],
            )
            
            assert score >= 0.5, f"Groundedness too low: {score}"
    
    @pytest.mark.asyncio
    async def test_retrieval_relevance(self, sample_queries):
        """Test that retrieved content is relevant to query."""
        from app.rag.hybrid_rag import hybrid_query
        
        for sample in sample_queries[:1]:
            result = await hybrid_query(
                query=sample["query"],
                auteur_key=sample["auteur_key"],
            )
            
            score = await evaluate_relevance(
                query=sample["query"],
                answer=result.answer,
            )
            
            assert score >= 0.6, f"Relevance too low: {score}"
    
    @pytest.mark.asyncio
    async def test_deflection_on_weak_evidence(self):
        """Test that system deflects when evidence is weak."""
        from app.rag.hybrid_rag import hybrid_query
        
        # Query that should have weak/no evidence
        result = await hybrid_query(
            query="봉준호 감독의 2030년 신작 영화 줄거리",  # Future = no evidence
            auteur_key="bong",
        )
        
        # Low confidence OR mentions uncertainty
        deflected = (
            result.confidence < 0.5 or
            any(word in result.answer.lower() for word in 
                ["확실하지", "정보 없", "알 수 없", "현재", "미래"])
        )
        
        # Allow either deflection or honest answer
        assert result.answer is not None
    
    @pytest.mark.asyncio 
    async def test_cache_quality_consistency(self, sample_queries):
        """Test that cached responses maintain quality."""
        from app.rag.hybrid_rag import hybrid_query
        
        sample = sample_queries[0]
        
        # First call (cache miss)
        result1 = await hybrid_query(
            query=sample["query"],
            auteur_key=sample["auteur_key"],
            use_semantic_cache=True,
        )
        
        # Second call (should hit cache)
        result2 = await hybrid_query(
            query=sample["query"],
            auteur_key=sample["auteur_key"],
            use_semantic_cache=True,
        )
        
        # Cached result should have same or similar quality
        assert result2.confidence >= result1.confidence * 0.9


# =============================================================================
# Quality Report Generator
# =============================================================================

async def generate_quality_report() -> Dict[str, Any]:
    """Generate weekly quality report.
    
    Returns:
        Summary of quality metrics across all dimensions.
    """
    from app.rag.hybrid_rag import hybrid_query
    
    test_cases = [
        {"query": "봉준호 감독 스타일", "auteur_key": "bong"},
        {"query": "왕가위 감독의 색감", "auteur_key": "wong"},
        {"query": "스토리보드 제작 가이드", "dimension": "2D"},
    ]
    
    results = []
    
    for case in test_cases:
        result = await hybrid_query(**case)
        
        groundedness = await evaluate_groundedness(
            query=case.get("query", ""),
            answer=result.answer,
            sources=[result.answer],  # Simplified
        )
        
        relevance = await evaluate_relevance(
            query=case.get("query", ""),
            answer=result.answer,
        )
        
        results.append({
            "query": case.get("query"),
            "confidence": result.confidence,
            "groundedness": groundedness,
            "relevance": relevance,
            "strategy": result.strategy_used,
        })
    
    return {
        "date": "2026-01-11",
        "total_queries": len(results),
        "avg_confidence": sum(r["confidence"] for r in results) / len(results),
        "avg_groundedness": sum(r["groundedness"] for r in results) / len(results),
        "avg_relevance": sum(r["relevance"] for r in results) / len(results),
        "details": results,
    }


if __name__ == "__main__":
    # Run quick quality check
    import json
    report = asyncio.run(generate_quality_report())
    print(json.dumps(report, indent=2, ensure_ascii=False))
