"""A/B and variant experimentation service for Foundry."""
from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple


class FoundryExperimentService:
    """Deterministic assignment + feedback aggregation."""

    def __init__(self):
        self._assignments: Dict[Tuple[str, str, str], str] = {}
        self._events: Dict[str, List[dict]] = defaultdict(list)

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

        digest = hashlib.sha256(
            f"{tenant_id}:{experiment_key}:{user_key}:{scene_id or ''}".encode("utf-8")
        ).hexdigest()
        hash_int = int(digest[:8], 16)
        hash_slot = hash_int % len(normalized_variants)
        assigned = normalized_variants[hash_slot]
        self._assignments[assignment_key] = assigned
        return {
            "tenant_id": tenant_id,
            "experiment_key": experiment_key,
            "assigned_variant": assigned,
            "hash_slot": hash_slot,
        }

    def record_feedback(
        self,
        *,
        tenant_id: str,
        experiment_key: str,
        user_key: str,
        variant: str,
        outcome: str,
        completion_seconds: int | None = None,
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

        return {
            "tenant_id": tenant_id,
            "experiment_key": experiment_key,
            "total_events": len(events),
            "variants": by_variant,
        }
