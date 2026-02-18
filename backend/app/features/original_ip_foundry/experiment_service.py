"""A/B and variant experimentation service for Foundry."""
from __future__ import annotations

import hashlib
import logging
from collections import defaultdict, deque
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from app.features.original_ip_foundry.enhanced_reward_service import EnhancedRewardService

if TYPE_CHECKING:
    from app.uqsl.thompson_sampling import ThompsonSamplingRouter

logger = logging.getLogger(__name__)

REWARD_MAP = {"accepted": 1.0, "edited": 0.5, "rejected": 0.0}


class FoundryExperimentService:
    """Deterministic assignment + Thompson Sampling adaptive routing."""

    MAX_EVENTS_PER_KEY = 10_000
    MAX_ASSIGNMENTS = 10_000

    def __init__(self, use_thompson: bool = True):
        self._assignments: Dict[Tuple[str, str, str], str] = {}
        self._events: Dict[str, deque[dict]] = defaultdict(lambda: deque(maxlen=self.MAX_EVENTS_PER_KEY))
        self._use_thompson = use_thompson
        self._thompson: Optional["ThompsonSamplingRouter"] = None
        self._enhanced_reward = EnhancedRewardService()

        if use_thompson:
            try:
                from app.uqsl.thompson_sampling import ThompsonSamplingRouter
                self._thompson = ThompsonSamplingRouter(
                    default_strategy="hybrid", sliding_window_size=50,
                )
            except Exception as e:
                logger.warning(f"[Experiment] Thompson init failed, using hash-only: {e}")
                self._thompson = None

    def _evict_oldest_assignment(self) -> None:
        """Evict oldest assignment if at capacity."""
        if len(self._assignments) >= self.MAX_ASSIGNMENTS:
            oldest_key = next(iter(self._assignments))
            del self._assignments[oldest_key]

    def _total_trials(self, tenant_id: str, experiment_key: str) -> int:
        scoped_key = f"{tenant_id}:{experiment_key}"
        return len(self._events.get(scoped_key, []))

    def assign(
        self,
        *,
        tenant_id: str,
        experiment_key: str,
        user_key: str,
        scene_id: str | None,
        variants: List[str],
    ) -> dict:
        normalized_variants = [variant for variant in variants if variant]
        if not normalized_variants:
            normalized_variants = ["A", "B"]

        assignment_key = (f"{tenant_id}:{experiment_key}", user_key, scene_id or "__global__")
        if assignment_key in self._assignments:
            assigned = self._assignments[assignment_key]
            hash_slot = normalized_variants.index(assigned) if assigned in normalized_variants else 0
            return {
                "tenant_id": tenant_id,
                "experiment_key": experiment_key,
                "assigned_variant": assigned,
                "hash_slot": hash_slot,
            }

        # Use Thompson if enabled and enough trials collected
        if self._thompson and self._total_trials(tenant_id, experiment_key) >= 10:
            arm_prefix = f"foundry:{tenant_id}:{experiment_key}"
            for variant in normalized_variants:
                self._thompson.initialize_arm(f"{arm_prefix}:{variant}")

            try:
                selected_arm = self._thompson.select_arm(arm_type=arm_prefix)
                assigned = selected_arm.split(":")[-1]
                if assigned not in normalized_variants:
                    assigned = normalized_variants[0]
                hash_slot = normalized_variants.index(assigned)
                self._evict_oldest_assignment()
                self._assignments[assignment_key] = assigned
                return {
                    "tenant_id": tenant_id,
                    "experiment_key": experiment_key,
                    "assigned_variant": assigned,
                    "hash_slot": hash_slot,
                }
            except Exception as e:
                logger.warning(f"[Experiment] Thompson selection failed, falling back to hash: {e}")

        # Deterministic hash fallback
        digest = hashlib.sha256(
            f"{tenant_id}:{experiment_key}:{user_key}:{scene_id or ''}".encode("utf-8")
        ).hexdigest()
        hash_int = int(digest[:8], 16)
        hash_slot = hash_int % len(normalized_variants)
        assigned = normalized_variants[hash_slot]
        self._evict_oldest_assignment()
        self._assignments[assignment_key] = assigned
        return {
            "tenant_id": tenant_id,
            "experiment_key": experiment_key,
            "assigned_variant": assigned,
            "hash_slot": hash_slot,
        }

    async def record_feedback(
        self,
        *,
        tenant_id: str,
        experiment_key: str,
        user_key: str,
        variant: str,
        outcome: str,
        completion_seconds: int | None = None,
        edit_distance: float = 0.0,
        satisfaction_score: float | None = None,
    ) -> dict:
        scoped_key = f"{tenant_id}:{experiment_key}"
        event = {
            "tenant_id": tenant_id,
            "experiment_key": experiment_key,
            "user_key": user_key,
            "variant": variant,
            "outcome": outcome,
            "completion_seconds": completion_seconds,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._events[scoped_key].append(event)

        # Update Thompson arms with reward signal
        if self._thompson:
            arm_id = f"foundry:{tenant_id}:{experiment_key}:{variant}"
            reward_result = self._enhanced_reward.compute_reward(
                outcome=outcome,
                completion_seconds=completion_seconds,
                edit_distance=edit_distance,
                satisfaction_score=satisfaction_score,
            )
            reward_value = reward_result["reward"]
            try:
                await self._thompson.update(
                    db=None,
                    arm_id=arm_id,
                    reward=(outcome == "accepted"),
                    reward_value=reward_value,
                )
            except Exception as e:
                logger.warning(f"[Experiment] Thompson update failed (non-fatal): {e}")

        return {"status": "recorded", "event": event}

    def summary(self, tenant_id: str, experiment_key: str) -> dict:
        scoped_key = f"{tenant_id}:{experiment_key}"
        events = self._events.get(scoped_key, [])
        by_variant: Dict[str, dict] = {}
        for event in events:
            bucket = by_variant.setdefault(
                event["variant"],
                {"total": 0, "accepted": 0, "edited": 0, "rejected": 0, "avg_completion_seconds": 0.0},
            )
            bucket["total"] += 1
            if event["outcome"] in {"accepted", "edited", "rejected"}:
                bucket[event["outcome"]] += 1

        for variant, stats in by_variant.items():
            variant_events = [e for e in events if e["variant"] == variant and e.get("completion_seconds") is not None]
            if variant_events:
                stats["avg_completion_seconds"] = round(
                    sum(e["completion_seconds"] for e in variant_events) / len(variant_events),
                    2,
                )
            total = max(stats["total"], 1)
            stats["accept_rate"] = round(stats["accepted"] / total, 4)
            stats["edit_rate"] = round(stats["edited"] / total, 4)
            stats["reject_rate"] = round(stats["rejected"] / total, 4)

        # Thompson stats
        thompson_active = self._thompson is not None and self._total_trials(tenant_id, experiment_key) >= 10
        thompson_stats: Dict[str, dict] = {}
        if self._thompson:
            arm_prefix = f"foundry:{tenant_id}:{experiment_key}"
            thompson_stats = self._thompson.get_all_stats(arm_type=arm_prefix)

        return {
            "tenant_id": tenant_id,
            "experiment_key": experiment_key,
            "total_events": len(events),
            "variants": by_variant,
            "thompson_active": thompson_active,
            "thompson_stats": thompson_stats,
        }
