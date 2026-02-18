"""Rights gate composition for Foundry-scoped decisions."""
from __future__ import annotations

from typing import List

from app.services.rights_gate_service import RightsGateService


class FoundryRightsService:
    """Evaluate asset-level rights and aggregate allow/review/block decisions."""

    def __init__(self):
        self._base = RightsGateService()

    def evaluate_assets(
        self,
        *,
        action: str,
        assets: List[dict],
        requested_elements: List[str] | None = None,
        evidence_refs: List[str] | None = None,
    ) -> dict:
        requested = {item.lower() for item in (requested_elements or []) if item}
        per_asset: list[dict] = []

        has_block = False
        has_review = False
        aggregate_reason_codes: list[str] = []

        for asset in assets:
            asset_id = str(asset.get("asset_id") or "unknown_asset")
            source_license = str(asset.get("source_license") or "").strip()
            allowed_actions = asset.get("allowed_actions") or []
            blocked_elements = [str(item).lower() for item in (asset.get("blocked_elements") or [])]

            base = self._base.check_pre_generation(
                {
                    "action": action,
                    "rights_asset": {
                        "derivative_allowed": bool(asset.get("derivative_allowed", True)),
                        "allowed_actions": allowed_actions,
                    },
                }
            )
            decision = "allow"
            reason_codes = list(base.get("reason_codes") or [])

            if source_license == "":
                decision = "review"
                reason_codes.append("MISSING_LICENSE")

            blocked_hit = sorted(requested.intersection(set(blocked_elements)))
            if blocked_hit:
                decision = "block"
                reason_codes.append("BLOCKED_ELEMENT_MATCH")

            if base.get("decision") == "block":
                decision = "block"

            # normalize reason order + dedupe
            reason_codes = list(dict.fromkeys(reason_codes))
            per_asset.append(
                {
                    "asset_id": asset_id,
                    "decision": decision,
                    "reason_codes": reason_codes,
                }
            )

            if decision == "block":
                has_block = True
            elif decision == "review":
                has_review = True
            aggregate_reason_codes.extend(reason_codes)

        if has_block:
            final_decision = "block"
        elif has_review:
            final_decision = "review"
        else:
            final_decision = "allow"

        return {
            "decision": final_decision,
            "reason_codes": list(dict.fromkeys(aggregate_reason_codes)),
            "per_asset": per_asset,
            "evidence_refs": list(evidence_refs or []),
        }

