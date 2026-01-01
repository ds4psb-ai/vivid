"""Helpers for deriving standardized artifacts from tool payloads."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List

from app.schemas.artifact_schemas import (
    create_data_table_from_claims,
    create_shot_list_from_storyboard,
    create_storyboard_from_capsule_output,
    create_storyboard_from_preview,
)


def _with_artifact_id(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not payload.get("artifact_id"):
        payload["artifact_id"] = str(uuid.uuid4())
    return payload


def derive_artifacts_from_tool_payload(
    tool_name: str,
    payload: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Create standardized artifact payloads from a tool result payload."""
    output = payload.get("output")
    output = output if isinstance(output, dict) else {}
    artifacts: List[Dict[str, Any]] = []

    if tool_name == "run_capsule":
        summary = output.get("summary")
        if isinstance(summary, dict):
            storyboard = create_storyboard_from_capsule_output(
                summary,
                artifact_id=str(uuid.uuid4()),
                title="Storyboard",
            )
            artifacts.append(storyboard.model_dump(mode="json"))
            shot_list = create_shot_list_from_storyboard(
                storyboard,
                artifact_id=str(uuid.uuid4()),
            )
            artifacts.append(shot_list.model_dump(mode="json"))

    if tool_name == "analyze_sources":
        summary = output.get("summary")
        if isinstance(summary, dict):
            if isinstance(output.get("evidence_refs"), list) and "evidence_refs" not in summary:
                summary = {**summary, "evidence_refs": output.get("evidence_refs")}
            data_table = create_data_table_from_claims(
                summary,
                artifact_id=str(uuid.uuid4()),
                title="Claim Evidence Table",
            )
            if data_table:
                artifacts.append(data_table.model_dump(mode="json"))

    if tool_name == "generate_storyboard":
        preview = output.get("storyboard")
        if isinstance(preview, list):
            storyboard = create_storyboard_from_preview(
                preview,
                artifact_id=str(uuid.uuid4()),
                title="Storyboard Preview",
            )
            if storyboard:
                artifacts.append(storyboard.model_dump(mode="json"))

    return [_with_artifact_id(payload) for payload in artifacts]
