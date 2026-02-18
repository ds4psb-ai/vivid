"""Automatic clone risk scoring for Foundry candidates."""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CloneRiskService:
    """Compute clone risk score from pattern similarity, license risk, and tag density."""

    LICENSE_RISK: dict[str, float] = {
        "CC0": 0.0,
        "PUBLIC_DOMAIN": 0.0,
        "CC_BY": 0.1,
        "CC_BY_SA": 0.15,
        "CC_BY_NC": 0.2,
        "CC_BY_ND": 0.3,
        "FAIR_USE": 0.4,
        "EDITORIAL": 0.5,
        "PROPRIETARY": 0.8,
        "UNKNOWN": 0.6,
    }

    def __init__(self, qdrant_pattern_store=None):
        self._qdrant_store = qdrant_pattern_store

    def compute(
        self,
        *,
        candidate_tags: list[str],
        project_id: str,
        reference_licenses: list[str] | None = None,
    ) -> float:
        pattern_sim = self._compute_pattern_similarity(candidate_tags, project_id)
        license_risk = self._compute_license_risk(reference_licenses or [])
        tag_density = self._compute_tag_density(candidate_tags)

        score = 0.5 * pattern_sim + 0.3 * license_risk + 0.2 * tag_density
        return max(0.0, min(round(score, 4), 1.0))

    def _compute_pattern_similarity(self, tags: list[str], project_id: str) -> float:
        if not self._qdrant_store or not tags:
            return 0.5  # neutral default when no Qdrant available
        try:
            query = " ".join(tags[:10])  # limit query size
            results = self._qdrant_store.search_atoms(
                project_id=project_id, query=query, limit=3
            )
            if not results:
                return 0.3
            # Average confidence of top matches as similarity proxy
            confidences = [r.get("confidence", 0.5) for r in results]
            return min(sum(confidences) / len(confidences), 1.0)
        except Exception as e:
            logger.warning(f"[CloneRisk] Pattern similarity failed: {e}")
            return 0.5

    def _compute_license_risk(self, licenses: list[str]) -> float:
        if not licenses:
            return 0.0
        risks = [self.LICENSE_RISK.get(lic.upper().replace("-", "_"), 0.6) for lic in licenses]
        return max(risks)  # worst-case license

    def _compute_tag_density(self, tags: list[str]) -> float:
        # More unique tags = more original, less clone risk
        if not tags:
            return 0.5
        unique = len(set(t.lower() for t in tags))
        # 10+ unique tags -> low density risk, 1-2 -> high density risk
        return max(0.0, min(1.0 - (unique / 15.0), 1.0))

    def decide(
        self,
        *,
        candidate_tags: list[str],
        project_id: str,
        reference_licenses: list[str] | None = None,
    ) -> dict:
        """Compute clone risk and return a structured decision."""
        score = self.compute(
            candidate_tags=candidate_tags,
            project_id=project_id,
            reference_licenses=reference_licenses,
        )
        from app.config import settings

        block_threshold = getattr(settings, "AD_FOUNDRY_CLONE_BLOCK_THRESHOLD", 0.7)
        review_threshold = getattr(settings, "AD_FOUNDRY_CLONE_REVIEW_THRESHOLD", 0.4)
        if score >= block_threshold:
            decision = "block"
        elif score >= review_threshold:
            decision = "review"
        else:
            decision = "allow"
        return {
            "score": score,
            "decision": decision,
            "thresholds": {"block": block_threshold, "review": review_threshold},
        }

    def compute_batch(self, items: list[dict]) -> list[float]:
        """Bulk clone risk scoring for multiple candidates."""
        results = []
        for item in items:
            score = self.compute(
                candidate_tags=item.get("candidate_tags", []),
                project_id=item.get("project_id", "unknown"),
                reference_licenses=item.get("reference_licenses"),
            )
            results.append(score)
        return results
