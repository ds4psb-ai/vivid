"""
LLM Cost Optimizer - 2026 Best Practices Implementation

Comprehensive LLM cost optimization with:
1. Two-tier semantic caching (exact + embedding similarity)
2. Model routing based on task complexity
3. Prompt compression for long inputs

References:
- https://redis.io/blog/10-techniques-for-semantic-cache-optimization/
- https://www.burnwise.io/blog/llm-model-routing-guide
- https://venturebeat.com/why-your-llm-bill-is-exploding-and-how-semantic-caching-can-cut-it-by-73

Cost Reduction Targets:
- Semantic Cache: 50-70% reduction on repeated/similar queries
- Model Routing: 30-85% reduction by using appropriate model tiers
- Combined: Up to 90% reduction in optimal scenarios
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

# Model tiers with pricing (relative cost per 1K tokens)
MODEL_TIERS = {
    "gemini-3-flash-preview": {
        "tier": "fast",
        "cost_multiplier": 1.0,
        "max_complexity": 0.4,
        "max_tokens": 8192,
        "best_for": ["simple_qa", "classification", "summarization", "formatting"],
    },
    "gemini-3-pro-preview": {
        "tier": "powerful",
        "cost_multiplier": 10.0,  # ~10x more expensive
        "max_complexity": 1.0,
        "max_tokens": 32768,
        "best_for": ["complex_reasoning", "creative_writing", "code_generation", "analysis"],
    },
}

# Default model for each tier
DEFAULT_MODELS = {
    "fast": "gemini-3-flash-preview",
    "powerful": "gemini-3-pro-preview",
}

# Semantic cache settings
SEMANTIC_CACHE_SIMILARITY_THRESHOLD = 0.88  # Balance between accuracy and hit rate
SEMANTIC_CACHE_TTL_SECONDS = 3600  # 1 hour default
SEMANTIC_CACHE_MAX_ENTRIES = 10000

# Prompt compression settings
COMPRESSION_MIN_TOKENS = 2000  # Only compress prompts longer than this
COMPRESSION_TARGET_RATIO = 0.7  # Target 30% reduction


# =============================================================================
# Enums and Data Classes
# =============================================================================

class TaskComplexity(str, Enum):
    """Task complexity levels for model routing."""
    SIMPLE = "simple"       # FAQ, formatting, classification
    MODERATE = "moderate"   # Summarization, translation, simple Q&A
    COMPLEX = "complex"     # Analysis, reasoning, creative tasks
    CRITICAL = "critical"   # High-stakes outputs requiring best model


@dataclass
class RouteResult:
    """Result of routing decision."""
    model: str
    prompt: str
    complexity: TaskComplexity
    cached_response: Optional[str] = None
    cache_hit_type: Optional[str] = None  # "exact" or "semantic"
    similarity_score: Optional[float] = None
    compression_applied: bool = False
    original_token_count: int = 0
    compressed_token_count: int = 0
    routing_reason: str = ""

    @property
    def cost_savings_estimate(self) -> float:
        """Estimate cost savings from this route decision."""
        if self.cached_response:
            return 1.0  # 100% savings from cache

        model_info = MODEL_TIERS.get(self.model, {})
        base_cost = MODEL_TIERS.get(DEFAULT_MODELS["powerful"], {}).get("cost_multiplier", 10.0)
        route_cost = model_info.get("cost_multiplier", base_cost)

        model_savings = 1 - (route_cost / base_cost)
        compression_savings = 0
        if self.compression_applied and self.original_token_count > 0:
            compression_savings = 1 - (self.compressed_token_count / self.original_token_count)

        # Combined savings (multiplicative)
        return 1 - ((1 - model_savings) * (1 - compression_savings * 0.3))


@dataclass
class CacheStats:
    """Cache performance statistics."""
    total_requests: int = 0
    exact_hits: int = 0
    semantic_hits: int = 0
    misses: int = 0
    cache_sets: int = 0
    avg_similarity: float = 0.0
    total_similarity_checks: int = 0

    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.exact_hits + self.semantic_hits) / self.total_requests

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "exact_hits": self.exact_hits,
            "semantic_hits": self.semantic_hits,
            "misses": self.misses,
            "cache_sets": self.cache_sets,
            "hit_rate": f"{self.hit_rate:.1%}",
            "avg_similarity": f"{self.avg_similarity:.3f}" if self.total_similarity_checks > 0 else "N/A",
        }


@dataclass
class CacheEntry:
    """Semantic cache entry."""
    key: str
    prompt_hash: str
    embedding: Optional[List[float]]
    response: str
    model_used: str
    token_count: int
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at


# =============================================================================
# Semantic LLM Cache
# =============================================================================

class SemanticLLMCache:
    """
    Two-tier semantic cache for LLM responses.

    Tier 1: Exact hash matching (instant, ~1ms)
    Tier 2: Embedding similarity matching (~10-50ms)

    Storage:
    - Primary: Redis (production)
    - Fallback: In-memory LRU (development)
    """

    def __init__(
        self,
        similarity_threshold: float = SEMANTIC_CACHE_SIMILARITY_THRESHOLD,
        ttl_seconds: int = SEMANTIC_CACHE_TTL_SECONDS,
        max_entries: int = SEMANTIC_CACHE_MAX_ENTRIES,
    ):
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._stats = CacheStats()

        # In-memory cache (L1)
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._embedding_index: List[Tuple[str, List[float]]] = []  # For similarity search

        # Redis connection (lazy init)
        self._redis = None
        self._redis_available = False

        # Embedder (lazy init)
        self._embedder = None

    async def _ensure_redis(self) -> bool:
        """Lazily initialize Redis connection."""
        if self._redis is not None:
            return self._redis_available

        try:
            import redis.asyncio as redis
            self._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis.ping()
            self._redis_available = True
            logger.info("[SemanticLLMCache] Redis connected")
        except Exception as e:
            logger.warning(f"[SemanticLLMCache] Redis unavailable, using memory: {e}")
            self._redis = None
            self._redis_available = False

        return self._redis_available

    def _get_embedder(self):
        """Get embedder instance (lazy loading)."""
        if self._embedder is None:
            try:
                from app.services.embedder import get_embedder
                self._embedder = get_embedder()
            except ImportError:
                logger.warning("[SemanticLLMCache] Embedder unavailable, hash-only mode")
                self._embedder = "unavailable"
        return self._embedder

    def _hash_prompt(self, prompt: str, model: str = "") -> str:
        """Create hash key for exact matching."""
        normalized = prompt.strip().lower()[:2000]  # Limit for hash stability
        key_data = f"{normalized}|{model}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]

    def _embed_prompt(self, prompt: str) -> Optional[List[float]]:
        """Generate embedding for prompt."""
        embedder = self._get_embedder()
        if embedder == "unavailable":
            return None
        try:
            return embedder.embed(prompt[:1000])  # Limit for performance
        except Exception as e:
            logger.debug(f"[SemanticLLMCache] Embedding failed: {e}")
            return None

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        if not a or not b or len(a) != len(b):
            return 0.0
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    async def get(
        self,
        prompt: str,
        model: str = "",
    ) -> Tuple[Optional[str], Optional[str], Optional[float]]:
        """
        Get cached response for prompt.

        Returns:
            Tuple of (response, hit_type, similarity_score)
            hit_type: "exact", "semantic", or None
        """
        self._stats.total_requests += 1
        prompt_hash = self._hash_prompt(prompt, model)

        # Tier 1: Exact match (memory)
        if prompt_hash in self._memory_cache:
            entry = self._memory_cache[prompt_hash]
            if not entry.is_expired:
                entry.hit_count += 1
                self._stats.exact_hits += 1
                logger.debug(f"[SemanticLLMCache] EXACT HIT (memory): {prompt_hash[:8]}")
                return entry.response, "exact", 1.0
            else:
                del self._memory_cache[prompt_hash]

        # Tier 1: Exact match (Redis)
        await self._ensure_redis()
        if self._redis_available:
            try:
                redis_key = f"llm_cache:{prompt_hash}"
                cached = await self._redis.get(redis_key)
                if cached:
                    data = json.loads(cached)
                    self._stats.exact_hits += 1
                    # Hydrate memory cache
                    self._hydrate_memory(prompt_hash, data)
                    logger.debug(f"[SemanticLLMCache] EXACT HIT (redis): {prompt_hash[:8]}")
                    return data["response"], "exact", 1.0
            except Exception as e:
                logger.warning(f"[SemanticLLMCache] Redis get error: {e}")

        # Tier 2: Semantic similarity search
        query_embedding = self._embed_prompt(prompt)
        if query_embedding:
            best_match = None
            best_similarity = 0.0

            # Search in-memory embedding index
            for cached_hash, cached_embedding in self._embedding_index:
                if cached_hash not in self._memory_cache:
                    continue
                entry = self._memory_cache[cached_hash]
                if entry.is_expired:
                    continue

                similarity = self._cosine_similarity(query_embedding, cached_embedding)
                self._stats.total_similarity_checks += 1
                self._stats.avg_similarity = (
                    (self._stats.avg_similarity * (self._stats.total_similarity_checks - 1) + similarity)
                    / self._stats.total_similarity_checks
                )

                if similarity >= self.similarity_threshold and similarity > best_similarity:
                    best_match = entry
                    best_similarity = similarity

            if best_match:
                best_match.hit_count += 1
                self._stats.semantic_hits += 1
                logger.info(
                    f"[SemanticLLMCache] SEMANTIC HIT: similarity={best_similarity:.3f}, "
                    f"prompt={prompt[:50]}..."
                )
                return best_match.response, "semantic", best_similarity

        self._stats.misses += 1
        return None, None, None

    async def set(
        self,
        prompt: str,
        response: str,
        model: str = "",
        token_count: int = 0,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Cache LLM response."""
        prompt_hash = self._hash_prompt(prompt, model)
        ttl = ttl or self.ttl_seconds
        expires_at = datetime.now() + timedelta(seconds=ttl)

        embedding = self._embed_prompt(prompt)

        entry = CacheEntry(
            key=prompt_hash,
            prompt_hash=prompt_hash,
            embedding=embedding,
            response=response,
            model_used=model,
            token_count=token_count,
            created_at=datetime.now(),
            expires_at=expires_at,
            hit_count=0,
            metadata=metadata or {},
        )

        # Update memory cache
        self._memory_cache[prompt_hash] = entry
        if embedding:
            self._embedding_index.append((prompt_hash, embedding))

        # Evict oldest if over limit
        while len(self._memory_cache) > self.max_entries:
            oldest_key = next(iter(self._memory_cache))
            del self._memory_cache[oldest_key]
            self._embedding_index = [
                (k, e) for k, e in self._embedding_index if k != oldest_key
            ]

        # Persist to Redis
        await self._ensure_redis()
        if self._redis_available:
            try:
                redis_key = f"llm_cache:{prompt_hash}"
                data = {
                    "response": response,
                    "model": model,
                    "token_count": token_count,
                    "created_at": datetime.now().isoformat(),
                    "metadata": metadata or {},
                }
                await self._redis.setex(redis_key, ttl, json.dumps(data))
            except Exception as e:
                logger.warning(f"[SemanticLLMCache] Redis set error: {e}")

        self._stats.cache_sets += 1
        logger.debug(f"[SemanticLLMCache] CACHED: {prompt_hash[:8]}, ttl={ttl}s")

    def _hydrate_memory(self, prompt_hash: str, data: Dict[str, Any]) -> None:
        """Hydrate memory cache from Redis data."""
        entry = CacheEntry(
            key=prompt_hash,
            prompt_hash=prompt_hash,
            embedding=None,
            response=data["response"],
            model_used=data.get("model", ""),
            token_count=data.get("token_count", 0),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            expires_at=datetime.now() + timedelta(seconds=self.ttl_seconds),
            metadata=data.get("metadata", {}),
        )
        self._memory_cache[prompt_hash] = entry

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = self._stats.to_dict()
        stats["memory_entries"] = len(self._memory_cache)
        stats["embedding_index_size"] = len(self._embedding_index)
        stats["redis_available"] = self._redis_available
        stats["similarity_threshold"] = self.similarity_threshold
        return stats

    async def clear(self) -> None:
        """Clear all cached entries."""
        self._memory_cache.clear()
        self._embedding_index.clear()
        self._stats = CacheStats()

        if self._redis_available:
            try:
                # Clear only LLM cache keys
                async for key in self._redis.scan_iter("llm_cache:*"):
                    await self._redis.delete(key)
            except Exception as e:
                logger.warning(f"[SemanticLLMCache] Redis clear error: {e}")


# =============================================================================
# Model Router
# =============================================================================

class ModelRouter:
    """
    Intelligent model routing based on task complexity.

    Routes simple tasks to fast/cheap models, complex tasks to powerful models.
    Can reduce costs by 30-85% while maintaining quality.
    """

    # Keywords indicating simple tasks (prioritize exact phrases)
    SIMPLE_INDICATORS = [
        r"^what is\s",  # Start with "what is"
        r"\bdefine\b",
        r"\blist\b",
        r"\bformat\b",
        r"\btranslate\b",
        r"\bconvert\b",
        r"\bextract\b",
        r"\bparse\b",
        r"\bclassify\b",
        r"\bcategorize\b",
        r"\blabel\b",
        r"\byes or no\b",
        r"\btrue or false\b",
    ]

    # Keywords indicating complex tasks (higher weight)
    COMPLEX_INDICATORS = [
        r"\banalyze\b",
        r"\banalysis\b",
        r"\bcompare\b",
        r"\bevaluate\b",
        r"\bassess\b",
        r"\bimplications\b",  # Analysis indicator
        r"\bcreate\b",
        r"\bgenerate\b",
        r"\bwrite\b",
        r"\bcompose\b",
        r"\bdesign\b",
        r"\bwhy\b",
        r"\bhow does\b",
        r"\bexplain why\b",
        r"\breason\b",
        r"\bstrategy\b",
        r"\bplan\b",
        r"\boptimize\b",
        r"\bimprove\b",
        r"\bcode\b",
        r"\bfunction\b",
        r"\balgorithm\b",
        r"\bimplement\b",
        r"\bdetailed\b",  # Indicates need for depth
    ]

    # Task type to complexity mapping
    TASK_COMPLEXITY_MAP = {
        "simple_qa": TaskComplexity.SIMPLE,
        "classification": TaskComplexity.SIMPLE,
        "formatting": TaskComplexity.SIMPLE,
        "translation": TaskComplexity.MODERATE,
        "summarization": TaskComplexity.MODERATE,
        "generation": TaskComplexity.COMPLEX,
        "analysis": TaskComplexity.COMPLEX,
        "code_generation": TaskComplexity.COMPLEX,
        "creative_writing": TaskComplexity.COMPLEX,
        "reasoning": TaskComplexity.COMPLEX,
        "critical": TaskComplexity.CRITICAL,
    }

    def __init__(self, default_model: str = "gemini-3-flash-preview"):
        self.default_model = default_model
        self._route_counts: Dict[str, int] = {}

    def route(
        self,
        prompt: str,
        task_type: Optional[str] = None,
        force_model: Optional[str] = None,
        min_quality: Optional[float] = None,
    ) -> Tuple[str, TaskComplexity, str]:
        """
        Determine best model for the given prompt.

        Args:
            prompt: The prompt to route
            task_type: Optional task type hint
            force_model: Force a specific model
            min_quality: Minimum quality requirement (0-1, higher = use better model)

        Returns:
            Tuple of (model_name, complexity, routing_reason)
        """
        if force_model and force_model in MODEL_TIERS:
            self._record_route(force_model)
            return force_model, TaskComplexity.MODERATE, f"forced: {force_model}"

        # Determine complexity
        complexity = self._classify_complexity(prompt, task_type)

        # Adjust for quality requirement
        if min_quality is not None and min_quality > 0.8:
            complexity = TaskComplexity.COMPLEX

        # Select model based on complexity
        model, reason = self._select_model(complexity)
        self._record_route(model)

        return model, complexity, reason

    def _classify_complexity(
        self,
        prompt: str,
        task_type: Optional[str] = None,
    ) -> TaskComplexity:
        """Classify prompt complexity."""
        # Task type hint takes precedence
        if task_type:
            mapped = self.TASK_COMPLEXITY_MAP.get(task_type.lower())
            if mapped:
                return mapped

        prompt_lower = prompt.lower()

        # Score based on indicators (complex indicators have higher weight)
        simple_score = sum(
            1 for pattern in self.SIMPLE_INDICATORS
            if re.search(pattern, prompt_lower)
        )
        # Complex indicators are weighted 2x
        complex_score = sum(
            2 for pattern in self.COMPLEX_INDICATORS
            if re.search(pattern, prompt_lower)
        )

        # Length heuristic
        word_count = len(prompt.split())
        if word_count < 20:
            simple_score += 1
        elif word_count > 100:
            complex_score += 2

        # Determine complexity (favor complex when in doubt for quality)
        if complex_score >= 2:  # Any complex indicator triggers complex
            return TaskComplexity.COMPLEX
        elif simple_score > 0 and complex_score == 0:
            return TaskComplexity.SIMPLE
        else:
            return TaskComplexity.MODERATE

    def _select_model(self, complexity: TaskComplexity) -> Tuple[str, str]:
        """Select model based on complexity."""
        if complexity == TaskComplexity.CRITICAL:
            return DEFAULT_MODELS["powerful"], "critical task requires best model"
        elif complexity == TaskComplexity.COMPLEX:
            return DEFAULT_MODELS["powerful"], "complex task routed to powerful model"
        elif complexity == TaskComplexity.MODERATE:
            # Use fast model for moderate tasks to save cost
            return DEFAULT_MODELS["fast"], "moderate task optimized to fast model"
        else:  # SIMPLE
            return DEFAULT_MODELS["fast"], "simple task uses cost-effective model"

    def _record_route(self, model: str) -> None:
        """Record routing decision for metrics."""
        self._route_counts[model] = self._route_counts.get(model, 0) + 1

    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        total = sum(self._route_counts.values())
        return {
            "route_counts": self._route_counts,
            "total_routes": total,
            "fast_model_ratio": (
                self._route_counts.get(DEFAULT_MODELS["fast"], 0) / total
                if total > 0 else 0
            ),
            "cost_savings_estimate": self._estimate_savings(),
        }

    def _estimate_savings(self) -> float:
        """Estimate cost savings from routing decisions."""
        fast_count = self._route_counts.get(DEFAULT_MODELS["fast"], 0)
        powerful_count = self._route_counts.get(DEFAULT_MODELS["powerful"], 0)
        total = fast_count + powerful_count

        if total == 0:
            return 0.0

        # If everything went to powerful model
        baseline_cost = total * MODEL_TIERS[DEFAULT_MODELS["powerful"]]["cost_multiplier"]

        # Actual cost with routing
        actual_cost = (
            fast_count * MODEL_TIERS[DEFAULT_MODELS["fast"]]["cost_multiplier"]
            + powerful_count * MODEL_TIERS[DEFAULT_MODELS["powerful"]]["cost_multiplier"]
        )

        return 1 - (actual_cost / baseline_cost) if baseline_cost > 0 else 0.0


# =============================================================================
# Prompt Compressor
# =============================================================================

class PromptCompressor:
    """
    Compress long prompts to reduce token usage.

    Techniques:
    1. Remove redundant whitespace
    2. Abbreviate common phrases
    3. Truncate examples to essential parts
    """

    # Common phrase abbreviations
    ABBREVIATIONS = [
        (r"please\s+", ""),
        (r"could you\s+", ""),
        (r"i would like you to\s+", ""),
        (r"the following\s+", "this "),
        (r"in order to\s+", "to "),
        (r"make sure to\s+", ""),
        (r"it is important to note that\s+", "note: "),
    ]

    def __init__(
        self,
        min_tokens: int = COMPRESSION_MIN_TOKENS,
        target_ratio: float = COMPRESSION_TARGET_RATIO,
    ):
        self.min_tokens = min_tokens
        self.target_ratio = target_ratio

    def compress(self, prompt: str) -> Tuple[str, bool, int, int]:
        """
        Compress prompt if it exceeds minimum token threshold.

        Returns:
            Tuple of (compressed_prompt, was_compressed, original_tokens, new_tokens)
        """
        original_tokens = self._estimate_tokens(prompt)

        if original_tokens < self.min_tokens:
            return prompt, False, original_tokens, original_tokens

        compressed = prompt

        # 1. Normalize whitespace
        compressed = self._normalize_whitespace(compressed)

        # 2. Apply abbreviations
        compressed = self._apply_abbreviations(compressed)

        # 3. Truncate long examples
        compressed = self._truncate_examples(compressed)

        new_tokens = self._estimate_tokens(compressed)
        was_compressed = new_tokens < original_tokens

        if was_compressed:
            logger.debug(
                f"[PromptCompressor] Compressed: {original_tokens} -> {new_tokens} tokens "
                f"({(1 - new_tokens/original_tokens):.1%} reduction)"
            )

        return compressed, was_compressed, original_tokens, new_tokens

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: ~4 chars per token)."""
        return len(text) // 4

    def _normalize_whitespace(self, text: str) -> str:
        """Remove redundant whitespace."""
        # Multiple spaces to single
        text = re.sub(r" +", " ", text)
        # Multiple newlines to double
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Trailing whitespace
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        return text.strip()

    def _apply_abbreviations(self, text: str) -> str:
        """Apply common phrase abbreviations."""
        for pattern, replacement in self.ABBREVIATIONS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    def _truncate_examples(self, text: str, max_example_length: int = 500) -> str:
        """Truncate long examples in the prompt."""
        # Find example blocks (```...```)
        def truncate_block(match):
            content = match.group(0)
            if len(content) > max_example_length:
                return content[:max_example_length] + "\n... [truncated] ...\n```"
            return content

        text = re.sub(r"```[\s\S]*?```", truncate_block, text)
        return text


# =============================================================================
# Unified Cost Optimizer
# =============================================================================

class LLMCostOptimizer:
    """
    Unified LLM cost optimization combining all techniques.

    Usage:
        optimizer = get_cost_optimizer()

        # Route and check cache
        result = await optimizer.route_request(prompt, task_type="generation")
        if result.cached_response:
            return result.cached_response

        # Make LLM call
        response = await call_llm(result.model, result.prompt)

        # Cache response
        await optimizer.cache_response(prompt, response, result.model)
    """

    def __init__(
        self,
        enable_cache: bool = True,
        enable_routing: bool = True,
        enable_compression: bool = True,
    ):
        self.enable_cache = enable_cache
        self.enable_routing = enable_routing
        self.enable_compression = enable_compression

        self._cache = SemanticLLMCache() if enable_cache else None
        self._router = ModelRouter() if enable_routing else None
        self._compressor = PromptCompressor() if enable_compression else None

        self._total_requests = 0
        self._cache_hits = 0
        self._estimated_savings = 0.0

    async def route_request(
        self,
        prompt: str,
        task_type: Optional[str] = None,
        force_model: Optional[str] = None,
        skip_cache: bool = False,
        min_quality: Optional[float] = None,
    ) -> RouteResult:
        """
        Route request through all optimization layers.

        Args:
            prompt: The prompt to process
            task_type: Task type hint for routing
            force_model: Force a specific model
            skip_cache: Skip cache lookup
            min_quality: Minimum quality requirement

        Returns:
            RouteResult with routing decision and any cached response
        """
        self._total_requests += 1

        # 1. Check cache first
        cached_response = None
        cache_hit_type = None
        similarity_score = None

        if self.enable_cache and self._cache and not skip_cache:
            cached_response, cache_hit_type, similarity_score = await self._cache.get(
                prompt,
                model=force_model or ""
            )
            if cached_response:
                self._cache_hits += 1

        # 2. Route to appropriate model
        if self.enable_routing and self._router:
            model, complexity, routing_reason = self._router.route(
                prompt, task_type, force_model, min_quality
            )
        else:
            model = force_model or DEFAULT_MODELS["fast"]
            complexity = TaskComplexity.MODERATE
            routing_reason = "routing disabled"

        # 3. Compress prompt if needed
        compressed_prompt = prompt
        compression_applied = False
        original_tokens = 0
        compressed_tokens = 0

        if self.enable_compression and self._compressor and not cached_response:
            (
                compressed_prompt,
                compression_applied,
                original_tokens,
                compressed_tokens,
            ) = self._compressor.compress(prompt)

        result = RouteResult(
            model=model,
            prompt=compressed_prompt,
            complexity=complexity,
            cached_response=cached_response,
            cache_hit_type=cache_hit_type,
            similarity_score=similarity_score,
            compression_applied=compression_applied,
            original_token_count=original_tokens,
            compressed_token_count=compressed_tokens,
            routing_reason=routing_reason,
        )

        self._estimated_savings += result.cost_savings_estimate

        return result

    async def cache_response(
        self,
        prompt: str,
        response: str,
        model: str = "",
        token_count: int = 0,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Cache successful LLM response."""
        if self.enable_cache and self._cache:
            await self._cache.set(
                prompt=prompt,
                response=response,
                model=model,
                token_count=token_count,
                ttl=ttl,
                metadata=metadata,
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        stats = {
            "total_requests": self._total_requests,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": (
                f"{self._cache_hits / self._total_requests:.1%}"
                if self._total_requests > 0 else "0%"
            ),
            "estimated_savings": f"{self._estimated_savings / max(self._total_requests, 1):.1%}",
        }

        if self._cache:
            stats["cache"] = self._cache.get_stats()
        if self._router:
            stats["router"] = self._router.get_stats()

        return stats

    async def clear_cache(self) -> None:
        """Clear the cache."""
        if self._cache:
            await self._cache.clear()


# =============================================================================
# Singleton
# =============================================================================

_cost_optimizer: Optional[LLMCostOptimizer] = None


def get_cost_optimizer(
    enable_cache: bool = True,
    enable_routing: bool = True,
    enable_compression: bool = True,
) -> LLMCostOptimizer:
    """Get the singleton LLM cost optimizer."""
    global _cost_optimizer
    if _cost_optimizer is None:
        _cost_optimizer = LLMCostOptimizer(
            enable_cache=enable_cache,
            enable_routing=enable_routing,
            enable_compression=enable_compression,
        )
    return _cost_optimizer


def reset_cost_optimizer() -> None:
    """Reset the cost optimizer (for testing)."""
    global _cost_optimizer
    _cost_optimizer = None
