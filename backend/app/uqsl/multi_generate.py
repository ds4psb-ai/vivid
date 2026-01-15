"""
Multi-Generate Engine - N-candidate parallel generation

2026 Best Practice (arXiv:2502.11027, arXiv:2510.01171):
- Diversified Sampling: Diverse prompts for broader solution space
- Verbalized Sampling: Explicit probability distribution requests
- asyncio.Semaphore for concurrency control
- Temperature + seed variation for diversity
- Compute-Optimal Inference: Adaptive strategy per prompt difficulty
"""

from __future__ import annotations

import asyncio
import hashlib
import time
import random
from typing import Optional, Literal

from app.uqsl.models import CandidateResult
from app.config import settings


# =============================================================================
# Diversity Strategies (2026 Research-Backed)
# =============================================================================

DIVERSITY_STRATEGIES = {
    "standard": {
        "description": "Standard temperature variation",
        "temp_range": (0.7, 1.0),
        "prompt_variations": False,
    },
    "verbalized": {
        "description": "Verbalized Sampling (arXiv:2510.01171) - 1.6-2.1x diversity",
        "temp_range": (0.8, 1.2),
        "prompt_variations": True,
    },
    "diversified": {
        "description": "Diversified Sampling (arXiv:2502.11027) - Multi-cluster coverage",
        "temp_range": (0.5, 1.5),
        "prompt_variations": True,
    },
    "compute_optimal": {
        "description": "Compute-Optimal (ICLR 2025) - Adaptive per difficulty",
        "temp_range": (0.6, 1.3),
        "prompt_variations": True,
    },
}

# Verbalized Sampling 프롬프트 템플릿 (한국어/영어)
VERBALIZED_TEMPLATES = {
    "ko": [
        "창의적인 관점에서 다음을 재해석해주세요: {prompt}",
        "예상치 못한 방향으로 접근해보세요: {prompt}",
        "전문가의 시선으로 분석해주세요: {prompt}",
        "새로운 시각으로 표현해주세요: {prompt}",
        "독특한 스타일로 변환해주세요: {prompt}",
    ],
    "en": [
        "Reinterpret from a creative perspective: {prompt}",
        "Approach this from an unexpected angle: {prompt}",
        "Analyze with expert precision: {prompt}",
        "Express with a fresh viewpoint: {prompt}",
        "Transform into a unique style: {prompt}",
    ],
}

# Diversified Prompting 전략 (Multi-cluster coverage)
DIVERSIFIED_PERSPECTIVES = [
    "technical",  # 기술적 관점
    "artistic",   # 예술적 관점
    "emotional",  # 감성적 관점
    "analytical", # 분석적 관점
    "narrative",  # 서사적 관점
]


class MultiGenerateEngine:
    """
    N개 후보 병렬 생성 (2026 Diversified Sampling)

    2026 Best Practice:
    - Verbalized Sampling: 1.6-2.1x diversity (arXiv:2510.01171)
    - Diversified Prompting: Multi-cluster coverage (arXiv:2502.11027)
    - Compute-Optimal: Adaptive strategy per difficulty (ICLR 2025)
    """

    def __init__(
        self,
        max_concurrency: int = 5,
        timeout_per_candidate_ms: int = 30000,
        default_strategy: str = "diversified",
    ):
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.timeout_per_candidate = timeout_per_candidate_ms / 1000.0
        self.default_strategy = default_strategy

    async def generate_candidates(
        self,
        prompt: str,
        app_key: str,
        n_candidates: int = 3,
        diversity_seeds: Optional[list[int]] = None,
        diversity_factor: float = 0.3,
        diversity_strategy: Optional[str] = None,
        language: str = "ko",
    ) -> list[CandidateResult]:
        """
        N개 후보 병렬 생성 (2026 Diversified Sampling)

        Args:
            prompt: Input prompt
            app_key: Application key for capsule lookup
            n_candidates: Number of candidates to generate
            diversity_seeds: Optional seeds for reproducibility
            diversity_factor: Temperature variation factor (0-1)
            diversity_strategy: Sampling strategy (standard/verbalized/diversified/compute_optimal)
            language: Language for verbalized templates (ko/en)

        Returns:
            List of CandidateResult with generated content
        """
        # Select strategy
        strategy = diversity_strategy or self.default_strategy
        if strategy not in DIVERSITY_STRATEGIES:
            strategy = "diversified"

        strategy_config = DIVERSITY_STRATEGIES[strategy]
        seeds = diversity_seeds or self._generate_diversity_seeds(prompt, n_candidates)

        # Prepare prompts based on strategy
        prompts = self._prepare_diverse_prompts(
            prompt=prompt,
            n=n_candidates,
            strategy=strategy,
            language=language,
        )

        async def _generate_single(idx: int, seed: int, varied_prompt: str) -> CandidateResult:
            async with self.semaphore:
                start = time.perf_counter()
                try:
                    # Temperature from strategy range
                    temp_min, temp_max = strategy_config["temp_range"]
                    temperature = temp_min + (idx * (temp_max - temp_min) / max(n_candidates - 1, 1))

                    result = await self._execute_generation(
                        prompt=varied_prompt,
                        app_key=app_key,
                        seed=seed,
                        temperature=min(temperature, 1.5),  # Cap at 1.5
                        timeout=self.timeout_per_candidate,
                    )

                    latency = int((time.perf_counter() - start) * 1000)

                    return CandidateResult(
                        idx=idx,
                        content=result.get("output", ""),
                        metadata={
                            "seed": seed,
                            "temperature": round(temperature, 2),
                            "run_id": result.get("run_id", ""),
                            "strategy": strategy,
                            "prompt_varied": varied_prompt != prompt,
                        },
                        latency_ms=latency,
                        backend_used=result.get("backend_used", "default"),
                    )

                except asyncio.TimeoutError:
                    latency = int((time.perf_counter() - start) * 1000)
                    return CandidateResult(
                        idx=idx,
                        content=f"[Generation timeout after {latency}ms]",
                        metadata={"seed": seed, "error": "timeout", "strategy": strategy},
                        latency_ms=latency,
                        backend_used="timeout",
                    )
                except Exception as e:
                    latency = int((time.perf_counter() - start) * 1000)
                    return CandidateResult(
                        idx=idx,
                        content=f"[Generation error: {str(e)[:100]}]",
                        metadata={"seed": seed, "error": str(e), "strategy": strategy},
                        latency_ms=latency,
                        backend_used="error",
                    )

        # Parallel execution with varied prompts
        tasks = [_generate_single(i, seeds[i], prompts[i]) for i in range(n_candidates)]
        return await asyncio.gather(*tasks)

    def _prepare_diverse_prompts(
        self,
        prompt: str,
        n: int,
        strategy: str,
        language: str = "ko",
    ) -> list[str]:
        """
        Prepare diverse prompts based on sampling strategy.

        - standard: Same prompt for all candidates
        - verbalized: Explicit probability/diversity requests (arXiv:2510.01171)
        - diversified: Multi-perspective prompts (arXiv:2502.11027)
        - compute_optimal: Adaptive based on prompt complexity
        """
        if strategy == "standard":
            return [prompt] * n

        if strategy == "verbalized":
            # Verbalized Sampling: 1.6-2.1x diversity
            templates = VERBALIZED_TEMPLATES.get(language, VERBALIZED_TEMPLATES["en"])
            prompts = [prompt]  # First one is original
            for i in range(1, n):
                template = templates[i % len(templates)]
                prompts.append(template.format(prompt=prompt))
            return prompts

        if strategy == "diversified":
            # Diversified Sampling: Multi-cluster coverage
            perspectives = DIVERSIFIED_PERSPECTIVES[:n]
            prompts = [prompt]  # First one is original
            for i in range(1, n):
                perspective = perspectives[i % len(perspectives)]
                prompts.append(self._apply_perspective(prompt, perspective, language))
            return prompts

        if strategy == "compute_optimal":
            # Compute-Optimal: Adaptive based on prompt complexity
            complexity = self._estimate_prompt_complexity(prompt)
            if complexity < 0.3:
                # Simple prompt: use standard
                return [prompt] * n
            elif complexity < 0.7:
                # Medium complexity: use verbalized
                return self._prepare_diverse_prompts(prompt, n, "verbalized", language)
            else:
                # Complex prompt: use diversified
                return self._prepare_diverse_prompts(prompt, n, "diversified", language)

        return [prompt] * n

    def _apply_perspective(self, prompt: str, perspective: str, language: str) -> str:
        """Apply a specific perspective to the prompt for diversified sampling."""
        perspective_prefixes = {
            "ko": {
                "technical": "기술적 정확성에 초점을 맞춰서",
                "artistic": "예술적 감성과 미학을 강조하며",
                "emotional": "감성적 깊이와 정서적 공감을 담아",
                "analytical": "논리적으로 분석하고 구조화하여",
                "narrative": "스토리텔링 관점에서 서사적으로",
            },
            "en": {
                "technical": "With focus on technical precision,",
                "artistic": "Emphasizing artistic sensibility and aesthetics,",
                "emotional": "With emotional depth and empathy,",
                "analytical": "Analyzing logically and structurally,",
                "narrative": "From a storytelling perspective,",
            },
        }

        prefixes = perspective_prefixes.get(language, perspective_prefixes["en"])
        prefix = prefixes.get(perspective, "")

        if prefix:
            return f"{prefix} {prompt}"
        return prompt

    def _estimate_prompt_complexity(self, prompt: str) -> float:
        """
        Estimate prompt complexity for compute-optimal strategy.

        Returns: 0.0 (simple) to 1.0 (complex)
        """
        score = 0.0

        # Length factor
        length = len(prompt)
        if length > 500:
            score += 0.3
        elif length > 200:
            score += 0.2
        elif length > 100:
            score += 0.1

        # Sentence count
        sentence_count = prompt.count('.') + prompt.count('?') + prompt.count('!')
        if sentence_count > 5:
            score += 0.2
        elif sentence_count > 2:
            score += 0.1

        # Technical terms (simple heuristic)
        technical_keywords = ['분석', '비교', '구조', 'analyze', 'compare', 'structure',
                            'technical', 'specific', 'detailed', '상세', '기술적']
        for keyword in technical_keywords:
            if keyword in prompt.lower():
                score += 0.05

        # Question complexity
        if '?' in prompt:
            score += 0.1

        return min(score, 1.0)

    async def _execute_generation(
        self,
        prompt: str,
        app_key: str,
        seed: int,
        temperature: float,
        timeout: float,
    ) -> dict:
        """
        Execute single generation with capsule executor

        This method integrates with Vivid's existing capsule system.
        """
        try:
            # Import here to avoid circular dependency
            from app.services.capsule_executor import execute_capsule
            from app.rag.manifest_loader import get_manifest

            # Get manifest for app
            manifest = await get_manifest(app_key)
            capsule_key = manifest.get("capsule_key", "dimension.1d.generate")

            # Execute capsule with timeout
            result = await asyncio.wait_for(
                execute_capsule(
                    capsule_key=capsule_key,
                    inputs={"prompt": prompt},
                    params={
                        "seed": seed,
                        "temperature": temperature,
                    },
                ),
                timeout=timeout,
            )

            return {
                "output": result.summary.get("output", ""),
                "run_id": str(result.run_id),
                "backend_used": manifest.get("backend", "default"),
            }

        except ImportError:
            # Fallback for testing without full capsule system
            return await self._mock_generation(prompt, seed, temperature)

    async def _mock_generation(
        self,
        prompt: str,
        seed: int,
        temperature: float,
    ) -> dict:
        """Mock generation for testing"""
        import random
        random.seed(seed)

        # Simulate latency
        await asyncio.sleep(random.uniform(0.5, 2.0))

        # Generate mock content with variation
        variations = [
            f"[Seed {seed}] A cinematic interpretation: {prompt[:50]}...",
            f"[Seed {seed}] From a creative perspective: {prompt[:50]}...",
            f"[Seed {seed}] Artistically rendered: {prompt[:50]}...",
        ]

        return {
            "output": random.choice(variations),
            "run_id": f"mock-{seed}-{int(time.time())}",
            "backend_used": "mock",
        }

    def _generate_diversity_seeds(self, prompt: str, n: int) -> list[int]:
        """Generate deterministic but diverse seeds based on prompt hash"""
        base_hash = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
        return [base_hash + i * 1000 for i in range(n)]


# Singleton instance
_engine: Optional[MultiGenerateEngine] = None


def get_multi_generate_engine() -> MultiGenerateEngine:
    """Get or create the multi-generate engine singleton"""
    global _engine
    if _engine is None:
        _engine = MultiGenerateEngine(
            max_concurrency=settings.UQSL_MAX_CONCURRENCY if hasattr(settings, "UQSL_MAX_CONCURRENCY") else 5,
            timeout_per_candidate_ms=settings.UQSL_TIMEOUT_MS if hasattr(settings, "UQSL_TIMEOUT_MS") else 30000,
        )
    return _engine
