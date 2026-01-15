"""
Tests for LLM Cost Optimizer Module

Tests the three pillars of cost optimization:
1. SemanticLLMCache - Two-tier semantic caching
2. ModelRouter - Task complexity routing
3. PromptCompressor - Long prompt compression
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from app.llm.cost_optimizer import (
    SemanticLLMCache,
    ModelRouter,
    PromptCompressor,
    LLMCostOptimizer,
    get_cost_optimizer,
    reset_cost_optimizer,
    TaskComplexity,
    RouteResult,
    CacheEntry,
    DEFAULT_MODELS,
    MODEL_TIERS,
)


# =============================================================================
# SemanticLLMCache Tests
# =============================================================================

class TestSemanticLLMCache:
    """Tests for semantic LLM response caching."""

    @pytest.fixture
    def cache(self):
        """Create a fresh cache instance."""
        return SemanticLLMCache(
            similarity_threshold=0.85,
            ttl_seconds=60,
            max_entries=100,
        )

    @pytest.mark.asyncio
    async def test_exact_match_hit(self, cache):
        """Test exact match cache hit."""
        prompt = "What is the capital of France?"
        response = "Paris is the capital of France."

        # Set cache
        await cache.set(prompt, response, model="test-model")

        # Get should hit
        result, hit_type, similarity = await cache.get(prompt, model="test-model")

        assert result == response
        assert hit_type == "exact"
        assert similarity == 1.0

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        """Test cache miss for new prompt."""
        prompt = "What is quantum computing?"

        result, hit_type, similarity = await cache.get(prompt)

        assert result is None
        assert hit_type is None
        assert similarity is None

    @pytest.mark.asyncio
    async def test_expired_entry_miss(self, cache):
        """Test that expired entries return miss."""
        cache.ttl_seconds = -1  # Already expired

        await cache.set("test prompt", "test response")

        result, hit_type, _ = await cache.get("test prompt")

        assert result is None
        assert hit_type is None

    @pytest.mark.asyncio
    async def test_semantic_match_with_embedder(self, cache):
        """Test semantic similarity matching with embedder."""
        # Mock embedder to return consistent embeddings
        mock_embedder = MagicMock()
        mock_embedder.embed = MagicMock(side_effect=lambda x: [0.1, 0.2, 0.3] * 128)

        with patch.object(cache, "_get_embedder", return_value=mock_embedder):
            await cache.set("What is AI?", "AI is artificial intelligence")
            result, hit_type, similarity = await cache.get("What is artificial intelligence?")

            # Should get semantic hit due to same embedding
            assert result == "AI is artificial intelligence"
            assert hit_type == "semantic"
            assert similarity == 1.0  # Same embeddings = perfect similarity

    @pytest.mark.asyncio
    async def test_cache_stats(self, cache):
        """Test cache statistics tracking."""
        await cache.set("prompt1", "response1")
        await cache.get("prompt1")  # Hit
        await cache.get("prompt2")  # Miss

        stats = cache.get_stats()

        assert stats["cache_sets"] == 1
        assert stats["memory_entries"] == 1
        assert "hit_rate" in stats

    @pytest.mark.asyncio
    async def test_max_entries_eviction(self, cache):
        """Test that old entries are evicted when limit reached."""
        cache.max_entries = 3

        for i in range(5):
            await cache.set(f"prompt_{i}", f"response_{i}")

        assert len(cache._memory_cache) == 3
        # Oldest entries (0, 1) should be evicted
        assert "prompt_0" not in str(cache._memory_cache)


# =============================================================================
# ModelRouter Tests
# =============================================================================

class TestModelRouter:
    """Tests for model routing based on task complexity."""

    @pytest.fixture
    def router(self):
        """Create a router instance."""
        return ModelRouter()

    def test_simple_task_routing(self, router):
        """Test that simple tasks route to fast model."""
        simple_prompts = [
            "What is the capital of France?",
            "Define machine learning",
            "Summarize this text",
            "Translate hello to Spanish",
        ]

        for prompt in simple_prompts:
            model, complexity, _ = router.route(prompt)
            assert model == DEFAULT_MODELS["fast"], f"Failed for: {prompt}"
            assert complexity in [TaskComplexity.SIMPLE, TaskComplexity.MODERATE]

    def test_complex_task_routing(self, router):
        """Test that complex tasks route to powerful model."""
        complex_prompts = [
            "Analyze the economic implications of climate change",
            "Create a detailed marketing strategy",
            "Write a Python function to implement quicksort",
            "Why does the theory of relativity matter?",
        ]

        for prompt in complex_prompts:
            model, complexity, _ = router.route(prompt)
            assert model == DEFAULT_MODELS["powerful"], f"Failed for: {prompt}"
            assert complexity == TaskComplexity.COMPLEX

    def test_task_type_hint_override(self, router):
        """Test that task_type hint overrides prompt analysis."""
        # Simple prompt but marked as critical
        model, complexity, _ = router.route(
            "What is 2+2?",
            task_type="critical"
        )
        assert model == DEFAULT_MODELS["powerful"]
        assert complexity == TaskComplexity.CRITICAL

    def test_force_model_override(self, router):
        """Test that force_model bypasses routing logic."""
        model, _, reason = router.route(
            "Complex analysis task",
            force_model="gemini-3-flash-preview"
        )
        assert model == "gemini-3-flash-preview"
        assert "forced" in reason.lower()

    def test_min_quality_upgrade(self, router):
        """Test that high min_quality upgrades to powerful model."""
        model, _, _ = router.route(
            "Simple question",
            min_quality=0.9
        )
        assert model == DEFAULT_MODELS["powerful"]

    def test_routing_stats(self, router):
        """Test routing statistics collection."""
        router.route("Simple prompt")
        router.route("Complex analysis required")

        stats = router.get_stats()
        assert stats["total_routes"] == 2
        assert "cost_savings_estimate" in stats


# =============================================================================
# PromptCompressor Tests
# =============================================================================

class TestPromptCompressor:
    """Tests for prompt compression."""

    @pytest.fixture
    def compressor(self):
        """Create a compressor instance."""
        return PromptCompressor(min_tokens=100, target_ratio=0.7)

    def test_short_prompt_not_compressed(self, compressor):
        """Test that short prompts are not modified."""
        short_prompt = "What is AI?"

        result, compressed, original, new = compressor.compress(short_prompt)

        assert result == short_prompt
        assert compressed is False
        assert original == new

    def test_whitespace_normalization(self, compressor):
        """Test whitespace normalization."""
        compressor.min_tokens = 0  # Force compression

        messy = "Hello    world\n\n\n\n\ntest   spaces  "
        result, compressed, _, _ = compressor.compress(messy)

        assert "    " not in result
        assert "\n\n\n" not in result
        assert compressed is True

    def test_phrase_abbreviation(self, compressor):
        """Test common phrase abbreviations."""
        compressor.min_tokens = 0

        verbose = "Please could you summarize the following text in order to make it shorter"
        result, _, _, _ = compressor.compress(verbose)

        assert "please" not in result.lower()
        assert "could you" not in result.lower()
        assert "in order to" not in result.lower()

    def test_example_truncation(self, compressor):
        """Test that long code examples are truncated."""
        compressor.min_tokens = 0

        long_example = "Here is code:\n```\n" + "x = 1\n" * 200 + "```"
        result, _, _, _ = compressor.compress(long_example)

        assert len(result) < len(long_example)
        assert "[truncated]" in result

    def test_token_reduction(self, compressor):
        """Test that compression reduces token count."""
        compressor.min_tokens = 0

        verbose = """
        Please could you help me with the following task.
        I would like you to analyze this text and in order to
        understand it better, please make sure to explain
        the main concepts in detail.
        """

        result, compressed, original, new = compressor.compress(verbose)

        assert compressed is True
        assert new < original


# =============================================================================
# LLMCostOptimizer Integration Tests
# =============================================================================

class TestLLMCostOptimizer:
    """Integration tests for the unified cost optimizer."""

    @pytest.fixture
    def optimizer(self):
        """Create optimizer instance."""
        reset_cost_optimizer()
        return LLMCostOptimizer(
            enable_cache=True,
            enable_routing=True,
            enable_compression=True,
        )

    @pytest.mark.asyncio
    async def test_route_request_no_cache(self, optimizer):
        """Test routing a new request without cache hit."""
        result = await optimizer.route_request(
            "What is machine learning?",
            task_type="simple_qa"
        )

        assert result.cached_response is None
        assert result.model == DEFAULT_MODELS["fast"]
        assert result.complexity == TaskComplexity.SIMPLE

    @pytest.mark.asyncio
    async def test_route_request_with_cache_hit(self, optimizer):
        """Test routing with cache hit."""
        prompt = "Explain quantum computing"
        response = "Quantum computing uses qubits..."

        # Cache the response first
        await optimizer.cache_response(prompt, response, model="test")

        # Route request should hit cache
        result = await optimizer.route_request(prompt)

        assert result.cached_response == response
        # Can be either exact or semantic depending on embedder availability
        assert result.cache_hit_type in ("exact", "semantic")

    @pytest.mark.asyncio
    async def test_cost_savings_estimate(self, optimizer):
        """Test cost savings estimation."""
        # Cached response = 100% savings
        await optimizer.cache_response("test", "response")
        result = await optimizer.route_request("test")
        assert result.cost_savings_estimate == 1.0

        # Simple task routed to fast model = some savings
        result = await optimizer.route_request(
            "What is 2+2?",
            skip_cache=True
        )
        assert result.cost_savings_estimate > 0

    @pytest.mark.asyncio
    async def test_stats_collection(self, optimizer):
        """Test comprehensive stats collection."""
        # First request - miss
        await optimizer.route_request("prompt1")
        # Cache the response
        await optimizer.cache_response("prompt1", "response1")
        # Second request - should hit cache
        await optimizer.route_request("prompt1")

        stats = optimizer.get_stats()

        assert stats["total_requests"] == 2
        # Can be 1 or 2 depending on semantic match behavior
        assert stats["cache_hits"] >= 1
        assert "cache" in stats
        assert "router" in stats

    @pytest.mark.asyncio
    async def test_skip_cache_option(self, optimizer):
        """Test skip_cache bypasses cache lookup."""
        await optimizer.cache_response("prompt", "cached_response")

        result = await optimizer.route_request("prompt", skip_cache=True)

        assert result.cached_response is None

    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        """Test get_cost_optimizer returns singleton."""
        reset_cost_optimizer()

        opt1 = get_cost_optimizer()
        opt2 = get_cost_optimizer()

        assert opt1 is opt2


# =============================================================================
# RouteResult Tests
# =============================================================================

class TestRouteResult:
    """Tests for RouteResult data class."""

    def test_cost_savings_from_cache(self):
        """Test cost savings calculation for cached response."""
        result = RouteResult(
            model="gemini-3-flash-preview",
            prompt="test",
            complexity=TaskComplexity.SIMPLE,
            cached_response="cached",
        )
        assert result.cost_savings_estimate == 1.0

    def test_cost_savings_from_routing(self):
        """Test cost savings calculation from model routing."""
        # Fast model saves ~90% vs powerful
        result = RouteResult(
            model="gemini-3-flash-preview",
            prompt="test",
            complexity=TaskComplexity.SIMPLE,
            cached_response=None,
        )
        assert result.cost_savings_estimate > 0.8

    def test_cost_savings_no_savings(self):
        """Test no savings when using powerful model."""
        result = RouteResult(
            model="gemini-3-pro-preview",
            prompt="test",
            complexity=TaskComplexity.COMPLEX,
            cached_response=None,
        )
        # Should have minimal or no savings
        assert result.cost_savings_estimate < 0.2


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_prompt_handling(self):
        """Test handling of empty prompts."""
        cache = SemanticLLMCache()
        result, _, _ = await cache.get("")
        assert result is None

    def test_router_unknown_task_type(self):
        """Test router handles unknown task types gracefully."""
        router = ModelRouter()
        model, _, _ = router.route("test", task_type="unknown_type")
        assert model in MODEL_TIERS

    @pytest.mark.asyncio
    async def test_redis_unavailable_fallback(self):
        """Test graceful fallback when Redis is unavailable."""
        cache = SemanticLLMCache()

        # Even without Redis, memory cache should work
        await cache.set("test", "response")
        result, hit_type, _ = await cache.get("test")

        assert result == "response"
        assert hit_type == "exact"
