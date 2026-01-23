"""Core utilities for unified orchestration."""
from app.core.utils.rrf import (
    reciprocal_rank_fusion,
    weighted_rrf,
    merge_and_dedupe,
)
from app.core.utils.sanitize import (
    sanitize_query,
    sanitize_context,
    sanitize_retrieved_docs,
    detect_injection_attempt,
    calculate_risk_score,
)
from app.core.utils.attribution import (
    wrap_context_with_attribution,
    format_evidence_refs,
    get_attribution_system_prompt,
    get_grounding_instruction,
    AttributedSource,
)

__all__ = [
    # RRF
    "reciprocal_rank_fusion",
    "weighted_rrf",
    "merge_and_dedupe",
    # Sanitization (P0)
    "sanitize_query",
    "sanitize_context",
    "sanitize_retrieved_docs",
    "detect_injection_attempt",
    "calculate_risk_score",
    # Attribution (P0)
    "wrap_context_with_attribution",
    "format_evidence_refs",
    "get_attribution_system_prompt",
    "get_grounding_instruction",
    "AttributedSource",
]
