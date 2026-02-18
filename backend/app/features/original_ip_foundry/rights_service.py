"""Rights gate composition for Foundry-scoped decisions."""
from __future__ import annotations

import logging
from typing import List, Optional

from app.services.rights_gate_service import RightsGateService

logger = logging.getLogger(__name__)


class FoundryRightsService:
    """Evaluate asset-level rights and aggregate allow/review/block decisions."""

    def __init__(self):
        self._base = RightsGateService()

    async def evaluate_assets(
        self,
        *,
        action: str,
        assets: List[dict],
        requested_elements: List[str] | None = None,
        evidence_refs: List[str] | None = None,
        db=None,  # Optional[AsyncSession]
        project_id: str = "unknown",
    ) -> dict:
        from sqlalchemy import select
        from app.models_rights_graph import RightsAsset, ProvenanceEvent

        requested = {item.lower() for item in (requested_elements or []) if item}
        per_asset: list[dict] = []

        has_block = False
        has_review = False
        aggregate_reason_codes: list[str] = []
        db_asset_map: dict[str, RightsAsset] = {}

        # DB lookup: enrich asset data from rights_assets table
        if db is not None:
            asset_ids = [str(a.get("asset_id") or "") for a in assets if a.get("asset_id")]
            if asset_ids:
                try:
                    result = await db.execute(
                        select(RightsAsset).where(RightsAsset.asset_id.in_(asset_ids))
                    )
                    for db_asset in result.scalars().all():
                        db_asset_map[db_asset.asset_id] = db_asset
                except Exception as e:
                    logger.warning(f"[Rights] DB lookup failed: {e}")

        events_to_insert: list[ProvenanceEvent] = []

        for asset in assets:
            asset_id = str(asset.get("asset_id") or "unknown_asset")
            db_asset = db_asset_map.get(asset_id)

            # Use DB values if available, else fallback to request payload
            if db_asset:
                source_license = db_asset.source_license
                allowed_actions = db_asset.allowed_actions or []
                blocked_elements = [str(e).lower() for e in (db_asset.blocked_elements or [])]
                derivative_allowed = db_asset.derivative_allowed
            else:
                source_license = str(asset.get("source_license") or "").strip()
                allowed_actions = asset.get("allowed_actions") or []
                blocked_elements = [str(item).lower() for item in (asset.get("blocked_elements") or [])]
                derivative_allowed = bool(asset.get("derivative_allowed", True))

            base = self._base.check_pre_generation(
                {
                    "action": action,
                    "rights_asset": {
                        "derivative_allowed": derivative_allowed,
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

            # Record provenance event for non-allow decisions on known DB assets
            if db is not None and db_asset is not None and decision != "allow":
                events_to_insert.append(ProvenanceEvent(
                    rights_asset_id=db_asset.id,
                    project_id=project_id,
                    scene_id=None,
                    event_type=f"rights_{decision}",
                    event_payload={"action": action, "reason_codes": reason_codes},
                    evidence_refs=list(evidence_refs or []),
                ))

        # Insert provenance events (commit handled by get_db dependency)
        if db is not None and events_to_insert:
            try:
                for event in events_to_insert:
                    db.add(event)
                await db.flush()
                logger.info(f"[Rights] Flushed {len(events_to_insert)} provenance events")
            except Exception as e:
                logger.warning(f"[Rights] ProvenanceEvent insert failed: {e}")

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

