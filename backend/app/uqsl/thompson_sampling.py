"""
Thompson Sampling Router - Dynamic Multi-Armed Bandit

2026 Best Practice:
- Beta 분포 기반 Bayesian 업데이트
- UCB-Thompson Hybrid: Exploration bonus for uncertainty
- Sliding Window: Recent feedback emphasis (non-stationary)
- Contextual Bandit: User/session-specific preferences
- Time-decay: Adaptive to changing environments

References:
- Thompson Sampling Guide 2025
- NeurIPS 2024: Contextual Bandits for LLM Selection
- arXiv:2502.11027: Adaptive MAB for Inference
"""

from __future__ import annotations

import math
import random
import time
from collections import deque
from typing import Optional, TYPE_CHECKING, Literal

from scipy.stats import beta as beta_dist
import numpy as np

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# =============================================================================
# Selection Strategies
# =============================================================================

SelectionStrategy = Literal["thompson", "ucb", "hybrid", "epsilon_greedy"]


class ThompsonSamplingRouter:
    """
    Dynamic Thompson Sampling 기반 자동 진화 라우터 (2026 Enhanced)

    각 arm은 Beta(alpha, beta) 분포를 따르며,
    사용자 피드백으로 분포를 업데이트합니다.

    Features:
    - UCB-Thompson Hybrid: Balances exploration with uncertainty bonus
    - Sliding Window: Tracks recent history for non-stationary environments
    - Contextual Bandit: User/context-specific arm preferences
    - Time-decay: Gradual forgetting of old feedback

    Arms types:
    - backend:qdrant_hybrid
    - backend:notebooklm
    - reranker:local_cross_encoder
    - generation:temperature_high
    - strategy:verbalized
    - strategy:diversified
    """

    def __init__(
        self,
        min_exploration_rate: float = 0.05,
        decay_factor: float = 0.99,
        sliding_window_size: int = 100,
        ucb_c: float = 2.0,
        default_strategy: SelectionStrategy = "hybrid",
    ):
        # In-memory arm state (synced with DB)
        self.arms: dict[str, dict] = {}
        self.min_exploration_rate = min_exploration_rate
        self.decay_factor = decay_factor
        self.sliding_window_size = sliding_window_size
        self.ucb_c = ucb_c  # UCB exploration coefficient
        self.default_strategy = default_strategy

        # Sliding window for recent feedback (per arm)
        self.recent_rewards: dict[str, deque] = {}

        # Contextual arm preferences (user_id -> arm_id -> bonus)
        self.context_preferences: dict[str, dict[str, float]] = {}

        # Global step counter for UCB
        self.total_steps = 0

    async def load_from_db(self, db: "AsyncSession") -> None:
        """DB에서 arm 상태 로드"""
        try:
            from sqlalchemy import select
            from app.models_uqsl import BanditArm

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

    def select_arm(
        self,
        arm_type: str,
        strategy: Optional[SelectionStrategy] = None,
        context_id: Optional[str] = None,
    ) -> str:
        """
        Multi-strategy arm selection (2026 Dynamic MAB)

        Args:
            arm_type: Arm type prefix (e.g., "backend", "reranker")
            strategy: Selection strategy (thompson/ucb/hybrid/epsilon_greedy)
            context_id: Optional context for personalized selection

        Returns:
            Selected arm_id
        """
        strategy = strategy or self.default_strategy
        self.total_steps += 1

        # Filter arms by type
        candidates = {
            k: v for k, v in self.arms.items()
            if k.startswith(f"{arm_type}:")
        }

        if not candidates:
            raise ValueError(f"No arms found for type: {arm_type}")

        # Forced exploration with minimum rate
        if random.random() < self.min_exploration_rate:
            return random.choice(list(candidates.keys()))

        # Strategy-based selection
        if strategy == "thompson":
            return self._select_thompson(candidates, context_id)
        elif strategy == "ucb":
            return self._select_ucb(candidates, context_id)
        elif strategy == "hybrid":
            return self._select_hybrid(candidates, context_id)
        elif strategy == "epsilon_greedy":
            return self._select_epsilon_greedy(candidates, context_id)
        else:
            return self._select_thompson(candidates, context_id)

    def _select_thompson(
        self,
        candidates: dict[str, dict],
        context_id: Optional[str] = None,
    ) -> str:
        """Pure Thompson Sampling with contextual bonus."""
        samples = {}
        for arm, params in candidates.items():
            # Base Thompson sample
            sample = beta_dist.rvs(params["alpha"], params["beta"])

            # Add contextual bonus if available
            if context_id and context_id in self.context_preferences:
                bonus = self.context_preferences[context_id].get(arm, 0.0)
                sample += bonus * 0.1  # Small contextual influence

            samples[arm] = sample

        return max(samples, key=samples.get)

    def _select_ucb(
        self,
        candidates: dict[str, dict],
        context_id: Optional[str] = None,
    ) -> str:
        """Upper Confidence Bound selection."""
        ucb_scores = {}
        for arm, params in candidates.items():
            n_trials = params["total"] + 1  # Avoid division by zero
            mean = params["alpha"] / (params["alpha"] + params["beta"])

            # UCB formula: mean + c * sqrt(2 * ln(t) / n)
            exploration_bonus = self.ucb_c * math.sqrt(
                2 * math.log(self.total_steps + 1) / n_trials
            )

            score = mean + exploration_bonus

            # Contextual bonus
            if context_id and context_id in self.context_preferences:
                score += self.context_preferences[context_id].get(arm, 0.0) * 0.1

            ucb_scores[arm] = score

        return max(ucb_scores, key=ucb_scores.get)

    def _select_hybrid(
        self,
        candidates: dict[str, dict],
        context_id: Optional[str] = None,
    ) -> str:
        """
        UCB-Thompson Hybrid: Best of both worlds.

        Uses Thompson for exploitation, UCB bonus for exploration.
        """
        hybrid_scores = {}
        for arm, params in candidates.items():
            # Thompson sample for exploitation
            thompson_sample = beta_dist.rvs(params["alpha"], params["beta"])

            # UCB bonus for exploration
            n_trials = params["total"] + 1
            ucb_bonus = 0.5 * math.sqrt(
                math.log(self.total_steps + 1) / n_trials
            )

            # Recent performance from sliding window
            recent_bonus = self._get_recent_performance(arm)

            # Combined score
            score = thompson_sample + ucb_bonus * 0.3 + recent_bonus * 0.2

            # Contextual adjustment
            if context_id and context_id in self.context_preferences:
                score += self.context_preferences[context_id].get(arm, 0.0) * 0.1

            hybrid_scores[arm] = score

        return max(hybrid_scores, key=hybrid_scores.get)

    def _select_epsilon_greedy(
        self,
        candidates: dict[str, dict],
        context_id: Optional[str] = None,
        epsilon: float = 0.1,
    ) -> str:
        """Epsilon-greedy selection."""
        if random.random() < epsilon:
            return random.choice(list(candidates.keys()))

        # Greedy: select best mean
        best_arm = max(
            candidates.keys(),
            key=lambda a: candidates[a]["alpha"] / (candidates[a]["alpha"] + candidates[a]["beta"])
        )
        return best_arm

    def _get_recent_performance(self, arm_id: str) -> float:
        """Get recent performance from sliding window."""
        if arm_id not in self.recent_rewards:
            return 0.0

        recent = self.recent_rewards[arm_id]
        if len(recent) == 0:
            return 0.0

        return sum(recent) / len(recent)

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
        context_id: Optional[str] = None,
        reward_value: Optional[float] = None,
    ) -> None:
        """
        사용자 피드백으로 분포 업데이트 (2026 Enhanced)

        Args:
            db: Database session (optional - can update in-memory only)
            arm_id: Arm identifier
            reward: True for positive, False for negative
            context_id: Optional context for personalized learning
            reward_value: Optional continuous reward (0-1), overrides bool reward
        """
        # Initialize if not exists
        if arm_id not in self.arms:
            self.arms[arm_id] = {"alpha": 1, "beta": 1, "total": 0}

        # Initialize sliding window if not exists
        if arm_id not in self.recent_rewards:
            self.recent_rewards[arm_id] = deque(maxlen=self.sliding_window_size)

        # Determine reward value
        r = reward_value if reward_value is not None else (1.0 if reward else 0.0)

        # Update Beta distribution
        if r >= 0.5:
            self.arms[arm_id]["alpha"] += 1
        else:
            self.arms[arm_id]["beta"] += 1
        self.arms[arm_id]["total"] += 1

        # Update sliding window
        self.recent_rewards[arm_id].append(r)

        # Update context preferences
        if context_id:
            if context_id not in self.context_preferences:
                self.context_preferences[context_id] = {}

            current = self.context_preferences[context_id].get(arm_id, 0.0)
            # Exponential moving average for context preference
            self.context_preferences[context_id][arm_id] = 0.9 * current + 0.1 * r

        # DB sync (if session provided)
        if db is not None:
            try:
                from sqlalchemy import update as sql_update
                from sqlalchemy.sql import func
                from app.models_uqsl import BanditArm

                await db.execute(
                    sql_update(BanditArm)
                    .where(BanditArm.arm_id == arm_id)
                    .values(
                        alpha=self.arms[arm_id]["alpha"],
                        beta=self.arms[arm_id]["beta"],
                        total_trials=self.arms[arm_id]["total"],
                        last_reward=r,
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


def get_thompson_sampling_router(
    strategy: SelectionStrategy = "hybrid",
) -> ThompsonSamplingRouter:
    """Get or create Thompson Sampling router singleton"""
    global _router
    if _router is None:
        _router = ThompsonSamplingRouter(default_strategy=strategy)

        # Initialize backend arms
        _router.initialize_arm("backend:qdrant_hybrid")
        _router.initialize_arm("backend:notebooklm")

        # Initialize reranker arms
        _router.initialize_arm("reranker:cross_encoder")
        _router.initialize_arm("reranker:semantic")

        # Initialize generation temperature arms
        _router.initialize_arm("generation:temperature_0.7")
        _router.initialize_arm("generation:temperature_1.0")
        _router.initialize_arm("generation:temperature_1.3")

        # Initialize diversity strategy arms (2026)
        _router.initialize_arm("strategy:standard")
        _router.initialize_arm("strategy:verbalized")
        _router.initialize_arm("strategy:diversified")
        _router.initialize_arm("strategy:compute_optimal")

    return _router


async def get_initialized_router(db: "AsyncSession") -> ThompsonSamplingRouter:
    """Get router with DB state loaded"""
    router = get_thompson_sampling_router()
    await router.load_from_db(db)
    return router
