"""
Thompson Sampling Router - Beta 분포 기반 Multi-Armed Bandit

2026 Best Practice:
- Beta 분포 기반 Bayesian 업데이트
- 최소 탐색률 보장 (min_exploration_rate)
- 비동기 DB 동기화 (Redis 캐시 + PostgreSQL 영속)

References:
- https://www.shadecoder.com/topics/thompson-sampling-for-bandits-a-comprehensive-guide-for-2025
"""

from __future__ import annotations

import random
from typing import Optional, TYPE_CHECKING

from scipy.stats import beta as beta_dist

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ThompsonSamplingRouter:
    """
    Thompson Sampling 기반 자동 진화 라우터

    각 arm은 Beta(alpha, beta) 분포를 따르며,
    사용자 피드백으로 분포를 업데이트합니다.

    Arms types:
    - backend:qdrant_hybrid
    - backend:notebooklm
    - reranker:local_cross_encoder
    - generation:temperature_high
    """

    def __init__(
        self,
        min_exploration_rate: float = 0.05,
        decay_factor: float = 0.99,
    ):
        # In-memory arm state (synced with DB)
        self.arms: dict[str, dict[str, int]] = {}
        self.min_exploration_rate = min_exploration_rate
        self.decay_factor = decay_factor

    async def load_from_db(self, db: "AsyncSession") -> None:
        """DB에서 arm 상태 로드"""
        try:
            from sqlalchemy import select
            from app.models_feedback import BanditArm

            result = await db.execute(
                select(BanditArm).where(BanditArm.enabled == True)
            )
            for arm in result.scalars():
                self.arms[arm.arm_id] = {
                    "alpha": arm.alpha,
                    "beta": arm.beta,
                    "total": arm.total_trials,
                }
        except Exception:
            # Table might not exist yet - use defaults
            pass

    def initialize_arm(self, arm_id: str, alpha: int = 1, beta: int = 1) -> None:
        """Initialize a new arm with prior"""
        if arm_id not in self.arms:
            self.arms[arm_id] = {
                "alpha": alpha,
                "beta": beta,
                "total": 0,
            }

    def select_arm(self, arm_type: str) -> str:
        """
        Thompson Sampling으로 최적 arm 선택

        Args:
            arm_type: Arm type prefix (e.g., "backend", "reranker")

        Returns:
            Selected arm_id
        """
        # Filter arms by type
        candidates = {
            k: v for k, v in self.arms.items()
            if k.startswith(f"{arm_type}:")
        }

        if not candidates:
            # No arms registered for this type
            raise ValueError(f"No arms found for type: {arm_type}")

        # Forced exploration with minimum rate
        if random.random() < self.min_exploration_rate:
            return random.choice(list(candidates.keys()))

        # Thompson Sampling: sample from each arm's Beta distribution
        samples = {
            arm: beta_dist.rvs(params["alpha"], params["beta"])
            for arm, params in candidates.items()
        }

        # Return arm with highest sample
        return max(samples, key=samples.get)

    def select_multiple_arms(self, arm_type: str, n: int = 2) -> list[str]:
        """Select top N arms for parallel execution"""
        candidates = {
            k: v for k, v in self.arms.items()
            if k.startswith(f"{arm_type}:")
        }

        if not candidates:
            raise ValueError(f"No arms found for type: {arm_type}")

        # Sample from each arm
        samples = {
            arm: beta_dist.rvs(params["alpha"], params["beta"])
            for arm, params in candidates.items()
        }

        # Return top N by sample value
        sorted_arms = sorted(samples.keys(), key=lambda a: samples[a], reverse=True)
        return sorted_arms[:n]

    async def update(
        self,
        db: Optional["AsyncSession"],
        arm_id: str,
        reward: bool,
    ) -> None:
        """
        사용자 피드백으로 분포 업데이트

        Args:
            db: Database session (optional - can update in-memory only)
            arm_id: Arm identifier
            reward: True for positive, False for negative
        """
        # Initialize if not exists
        if arm_id not in self.arms:
            self.arms[arm_id] = {"alpha": 1, "beta": 1, "total": 0}

        # Update Beta distribution
        if reward:
            self.arms[arm_id]["alpha"] += 1
        else:
            self.arms[arm_id]["beta"] += 1
        self.arms[arm_id]["total"] += 1

        # DB sync (if session provided)
        if db is not None:
            try:
                from sqlalchemy import update as sql_update
                from sqlalchemy.sql import func
                from app.models_feedback import BanditArm

                await db.execute(
                    sql_update(BanditArm)
                    .where(BanditArm.arm_id == arm_id)
                    .values(
                        alpha=self.arms[arm_id]["alpha"],
                        beta=self.arms[arm_id]["beta"],
                        total_trials=self.arms[arm_id]["total"],
                        last_reward=1.0 if reward else 0.0,
                        updated_at=func.now(),
                    )
                )
                await db.commit()
            except Exception:
                # Log but don't fail - in-memory update succeeded
                pass

    def get_arm_stats(self, arm_id: str) -> dict:
        """
        Arm 통계 조회

        Returns:
            Dictionary with success_rate, confidence, total_trials
        """
        if arm_id not in self.arms:
            return {"success_rate": 0.5, "confidence": 0.0, "total_trials": 0}

        arm = self.arms[arm_id]
        success_rate = arm["alpha"] / (arm["alpha"] + arm["beta"])
        confidence = 1 - (1 / (arm["total"] + 1))  # More trials = more confidence

        return {
            "success_rate": success_rate,
            "confidence": confidence,
            "total_trials": arm["total"],
            "alpha": arm["alpha"],
            "beta": arm["beta"],
        }

    def get_all_stats(self, arm_type: Optional[str] = None) -> dict[str, dict]:
        """Get stats for all arms (optionally filtered by type)"""
        if arm_type:
            arms = [k for k in self.arms if k.startswith(f"{arm_type}:")]
        else:
            arms = list(self.arms.keys())

        return {arm: self.get_arm_stats(arm) for arm in arms}

    def apply_decay(self) -> None:
        """Apply decay to all arms (for non-stationary environments)"""
        for arm_id in self.arms:
            self.arms[arm_id]["alpha"] = max(
                1, int(self.arms[arm_id]["alpha"] * self.decay_factor)
            )
            self.arms[arm_id]["beta"] = max(
                1, int(self.arms[arm_id]["beta"] * self.decay_factor)
            )


# Singleton instance
_router: Optional[ThompsonSamplingRouter] = None


def get_thompson_sampling_router() -> ThompsonSamplingRouter:
    """Get or create Thompson Sampling router singleton"""
    global _router
    if _router is None:
        _router = ThompsonSamplingRouter()
        # Initialize default arms
        _router.initialize_arm("backend:qdrant_hybrid")
        _router.initialize_arm("backend:notebooklm")
        _router.initialize_arm("reranker:cross_encoder")
        _router.initialize_arm("generation:temperature_0.7")
        _router.initialize_arm("generation:temperature_1.0")
    return _router


async def get_initialized_router(db: "AsyncSession") -> ThompsonSamplingRouter:
    """Get router with DB state loaded"""
    router = get_thompson_sampling_router()
    await router.load_from_db(db)
    return router
