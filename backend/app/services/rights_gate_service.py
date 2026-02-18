"""Policy checks for rights-safe generation flows."""

from __future__ import annotations

from typing import Any, Dict


class RightsGateService:
    """Evaluate pre/post generation rights constraints."""

    REMIX_ACTIONS = {"remix", "derive", "commercial_remix"}

    def check_pre_generation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action")
        rights_asset = payload.get("rights_asset") or {}
        allowed_actions = rights_asset.get("allowed_actions") or []
        derivative_allowed = rights_asset.get("derivative_allowed", True)

        reason_codes = []

        if action in self.REMIX_ACTIONS and not derivative_allowed:
            reason_codes.append("DERIVATIVE_NOT_ALLOWED")

        if allowed_actions and action and action not in allowed_actions:
            reason_codes.append("ACTION_NOT_LICENSED")

        decision = "block" if reason_codes else "allow"

        return {
            "decision": decision,
            "reason_codes": reason_codes,
            "evidence_refs": payload.get("evidence_refs", []),
        }

    def check_post_generation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        clone_risk = float(payload.get("clone_risk", 0.0))
        threshold = float(payload.get("threshold", 0.6))

        reason_codes = []
        if clone_risk >= threshold:
            reason_codes.append("CLONE_RISK_HIGH")

        decision = "block" if reason_codes else "allow"
        return {
            "decision": decision,
            "reason_codes": reason_codes,
            "evidence_refs": payload.get("evidence_refs", []),
        }
