"""Generation A/B Testing Service.

Wraps ABTestingService to apply variant payloads to capsule generation inputs/params.

Phase 7 (HITL Enhancement) - Task 3
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.experiments.ab_testing import ABTestingService, ExperimentAssignment


@dataclass
class GenerationABResult:
    experiment_key: str
    variant_name: str
    is_control: bool
    payload: Dict[str, Any]
    params: Dict[str, Any]
    inputs: Dict[str, Any]
    already_assigned: bool = False


class GenerationABService:
    """Generation output A/B testing wrapper."""

    def __init__(self, ab_service: ABTestingService):
        self.ab_service = ab_service

    async def get_variant_config(
        self,
        experiment_key: str,
        user_id: str,
        db: AsyncSession,
        base_params: Dict[str, Any],
        base_inputs: Dict[str, Any],
        context: Optional[dict] = None,
    ) -> Optional[GenerationABResult]:
        """Assign a variant and apply payload overrides.

        The variant payload can be either:
        - {"params": {...}, "inputs": {...}, "metadata": {...}}
        - or a flat dict treated as param overrides.
        """
        assignment = await self.ab_service.assign_variant(
            experiment_key=experiment_key,
            user_id=user_id,
            db=db,
            context=context or {},
        )
        if not assignment:
            return None

        payload = assignment.payload or {}
        merged_inputs, merged_params = apply_variant_payload(
            base_inputs=base_inputs,
            base_params=base_params,
            payload=payload,
        )

        return GenerationABResult(
            experiment_key=experiment_key,
            variant_name=assignment.variant_name,
            is_control=assignment.is_control,
            payload=payload,
            params=merged_params,
            inputs=merged_inputs,
            already_assigned=assignment.already_assigned,
        )


def apply_variant_payload(
    base_inputs: Dict[str, Any],
    base_params: Dict[str, Any],
    payload: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Merge variant payload into inputs/params."""
    merged_inputs = dict(base_inputs)
    merged_params = dict(base_params)

    if isinstance(payload, dict):
        payload_inputs = payload.get("inputs")
        payload_params = payload.get("params")

        if isinstance(payload_inputs, dict):
            merged_inputs.update(payload_inputs)

        if isinstance(payload_params, dict):
            merged_params.update(payload_params)
        else:
            for key, value in payload.items():
                if key in {"inputs", "params", "metadata"}:
                    continue
                merged_params[key] = value

    return merged_inputs, merged_params
