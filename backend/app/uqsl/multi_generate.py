"""
Multi-Generate Engine - N-candidate parallel generation

2026 Best Practice:
- asyncio.Semaphore for concurrency control
- Diversity via temperature variation and seed control
- Timeout handling per candidate
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from typing import Optional

from app.uqsl.models import CandidateResult
from app.config import settings


class MultiGenerateEngine:
    """동일 프롬프트로 N개 후보 병렬 생성 (2026 FastAPI async pattern)"""

    def __init__(
        self,
        max_concurrency: int = 5,
        timeout_per_candidate_ms: int = 30000,
    ):
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.timeout_per_candidate = timeout_per_candidate_ms / 1000.0

    async def generate_candidates(
        self,
        prompt: str,
        app_key: str,
        n_candidates: int = 3,
        diversity_seeds: Optional[list[int]] = None,
        diversity_factor: float = 0.3,
    ) -> list[CandidateResult]:
        """
        N개 후보 병렬 생성

        Args:
            prompt: Input prompt
            app_key: Application key for capsule lookup
            n_candidates: Number of candidates to generate
            diversity_seeds: Optional seeds for reproducibility
            diversity_factor: Temperature variation factor (0-1)

        Returns:
            List of CandidateResult with generated content
        """
        seeds = diversity_seeds or self._generate_diversity_seeds(prompt, n_candidates)

        async def _generate_single(idx: int, seed: int) -> CandidateResult:
            async with self.semaphore:
                start = time.perf_counter()
                try:
                    # Temperature variation for diversity
                    temperature = 0.7 + (idx * diversity_factor / n_candidates)

                    result = await self._execute_generation(
                        prompt=prompt,
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
                            "temperature": temperature,
                            "run_id": result.get("run_id", ""),
                        },
                        latency_ms=latency,
                        backend_used=result.get("backend_used", "default"),
                    )

                except asyncio.TimeoutError:
                    latency = int((time.perf_counter() - start) * 1000)
                    return CandidateResult(
                        idx=idx,
                        content=f"[Generation timeout after {latency}ms]",
                        metadata={"seed": seed, "error": "timeout"},
                        latency_ms=latency,
                        backend_used="timeout",
                    )
                except Exception as e:
                    latency = int((time.perf_counter() - start) * 1000)
                    return CandidateResult(
                        idx=idx,
                        content=f"[Generation error: {str(e)[:100]}]",
                        metadata={"seed": seed, "error": str(e)},
                        latency_ms=latency,
                        backend_used="error",
                    )

        # Parallel execution
        tasks = [_generate_single(i, seeds[i]) for i in range(n_candidates)]
        return await asyncio.gather(*tasks)

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
