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

    def check_publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Gate C: Verify content is safe for public distribution."""
        reason_codes = []

        # Check near-duplicate result
        near_dup = payload.get("near_duplicate_result") or {}
        if near_dup.get("decision") == "block":
            reason_codes.append("NEAR_DUPLICATE_BLOCKED")

        # Check clone risk
        clone_risk = float(payload.get("clone_risk", 0.0))
        publish_threshold = float(payload.get("publish_threshold", 0.5))
        if clone_risk >= publish_threshold:
            reason_codes.append("CLONE_RISK_PUBLISH_HIGH")

        # Check ingredient licenses
        ingredients = payload.get("ingredients") or []
        for ingredient in ingredients:
            license_val = str(ingredient.get("source_license") or "").strip()
            if not license_val or license_val.upper() == "UNKNOWN":
                reason_codes.append("INCOMPLETE_LICENSE_FOR_PUBLISH")
                break  # one is enough

        decision = "block" if reason_codes else "allow"
        return {
            "decision": decision,
            "reason_codes": reason_codes,
            "evidence_refs": payload.get("evidence_refs", []),
        }
