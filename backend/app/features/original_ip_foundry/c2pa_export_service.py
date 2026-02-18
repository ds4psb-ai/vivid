"""C2PA-compatible manifest export for Foundry provenance traces."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List


class FoundryC2PAExportService:
    """Build detached C2PA-compatible manifests from provenance data."""

    SPEC_VERSION = "2.2"

    def export_manifest(
        self,
        *,
        project_id: str,
        scene_id: str,
        asset_id: str,
        title: str,
        generator_model: str,
        source_license: str | None,
        actions: List[Dict[str, Any]],
        provenance_trace: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        instance_id = f"urn:uuid:{uuid.uuid4()}"

        normalized_actions = actions or [{"action": "c2pa.created", "parameters": {"generator": generator_model}}]
        normalized_ingredients = []
        for item in provenance_trace:
            normalized_ingredients.append(
                {
                    "relationship": item.get("relationship", "componentOf"),
                    "title": item.get("title") or item.get("asset_id"),
                    "instance_id": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, str(item.get('asset_id', 'unknown')))}",
                    "asset_id": item.get("asset_id", "unknown"),
                    "metadata": {
                        "source_license": item.get("source_license") or source_license or "",
                    },
                }
            )

        manifest = {
            "manifest_label": f"vivid.foundry.{project_id}.{scene_id}",
            "title": title,
            "format": "application/json",
            "instance_id": instance_id,
            "claim_generator": "VIVID Original-IP Foundry",
            "created": now,
            "assertions": [
                {
                    "label": "c2pa.actions",
                    "data": {
                        "actions": normalized_actions,
                    },
                },
                {
                    "label": "c2pa.ingredient",
                    "data": {
                        "ingredients": normalized_ingredients,
                    },
                },
                {
                    "label": "com.vivid.provenance",
                    "data": {
                        "project_id": project_id,
                        "scene_id": scene_id,
                        "asset_id": asset_id,
                        "generator_model": generator_model,
                        "source_license": source_license or "",
                        "provenance_trace": provenance_trace,
                    },
                },
            ],
        }

        warnings = [
            "Detached manifest only: cryptographic signing and hard-binding assertion are not included in this export.",
        ]
        if not normalized_ingredients:
            warnings.append("No provenance ingredients were provided; legal review may still be required.")

        return {
            "spec_version": self.SPEC_VERSION,
            "manifest": manifest,
            "compliance": {
                "eu_ai_act_article_50_ready": True,
                "machine_readable_marking": True,
                "human_disclosure_required": True,
            },
            "warnings": warnings,
        }

