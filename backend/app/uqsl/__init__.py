"""
UQSL - Universal Quality Selection Layer

A multi-tier quality selection system for Vivid's RAG-based generation.

Tiers:
- Free: Thompson Sampling + HITL (no LLM cost)
- Premium: LLM-as-Judge + Quality Scores
- Dev: Full LLM Judge + Analytics

Components:
- models.py: Pydantic v2 models
- multi_generate.py: N-candidate parallel generation
- quality_evaluator.py: Quality scoring (rule-based + LLM)
- best_selector.py: Selection strategies
- thompson_sampling.py: Beta distribution MAB
- ensemble_plus_plus.py: NeurIPS 2025 3-way comparison
"""

from app.uqsl.models import (
    QualityDimension,
    QualityScore,
    CandidateResult,
    SelectionResult,
    UQSLConfig,
)

__all__ = [
    "QualityDimension",
    "QualityScore",
    "CandidateResult",
    "SelectionResult",
    "UQSLConfig",
]
