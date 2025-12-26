import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.routers import capsules


def test_output_contract_enforced() -> None:
    summary = {"shot_contracts": []}
    output_contracts = {"types": ["shot_contracts", "prompt_contracts"]}
    missing = capsules._apply_output_contracts(summary, output_contracts)
    assert missing == ["missing_outputs:prompt_contracts"]
    with pytest.raises(HTTPException):
        capsules._enforce_output_contracts(summary, output_contracts)


def test_evidence_refs_enforced() -> None:
    with pytest.raises(HTTPException):
        capsules._enforce_evidence_refs(["evidence_ref_filtered:disallowed_prefix:opal"])


def test_validate_inputs_rejects_unknown_keys() -> None:
    spec_inputs = {"scene_summary": {"type": "string", "required": True}}
    input_contracts = {"required": ["scene_summary"]}
    with pytest.raises(HTTPException):
        capsules._validate_inputs(
            spec_inputs,
            {"scene_summary": "ok", "extra": 1},
            False,
            input_contracts,
        )


def test_validate_inputs_contracts_require_inputs() -> None:
    spec_inputs = {"scene_summary": {"type": "string", "required": True}}
    input_contracts = {"required": ["scene_summary", "duration_sec"]}
    with pytest.raises(HTTPException):
        capsules._validate_inputs(
            spec_inputs,
            {"scene_summary": "ok"},
            False,
            input_contracts,
        )


def test_production_capsule_outputs_present() -> None:
    from app.capsule_adapter import execute_capsule

    spec = {
        "outputContracts": {
            "types": [
                "shot_contracts",
                "prompt_contracts",
                "prompt_contract_version",
                "storyboard_refs",
            ]
        }
    }
    summary, _ = execute_capsule(
        capsule_id="production.stage-rehearsal",
        capsule_version="1.0.0",
        inputs={"scene_summary": "test"},
        params={},
        capsule_spec=spec,
    )
    for key in spec["outputContracts"]["types"]:
        assert key in summary
