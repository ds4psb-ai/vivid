"""
LLM Cost Optimization Module - 2026 Best Practices

This module provides production-ready LLM cost optimization:
1. SemanticCache - Embedding-based response caching (50-70% cost reduction)
2. ModelRouter - Intelligent model routing (30-85% cost reduction)
3. PromptCompressor - Long prompt compression (20-40% token reduction)

Usage:
    from app.llm import get_cost_optimizer

    optimizer = get_cost_optimizer()

    # Route request and check cache
    routed = await optimizer.route_request(prompt, task_type="generation")
    if routed.cached_response:
        return routed.cached_response

    # Make LLM call with routed model
    response = await call_llm(routed.model, routed.prompt)

    # Cache successful response
    await optimizer.cache_response(prompt, response)
"""

from app.llm.cost_optimizer import (
    LLMCostOptimizer,
    SemanticLLMCache,
    ModelRouter,
    PromptCompressor,
    get_cost_optimizer,
    RouteResult,
    CacheStats,
    TaskComplexity,
)

__all__ = [
    "LLMCostOptimizer",
    "SemanticLLMCache",
    "ModelRouter",
    "PromptCompressor",
    "get_cost_optimizer",
    "RouteResult",
    "CacheStats",
    "TaskComplexity",
]
