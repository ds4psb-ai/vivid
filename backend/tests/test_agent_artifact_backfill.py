from app.agents.artifact_backfill import derive_artifacts_from_tool_payload


def test_derive_run_capsule_storyboard_and_shot_list():
    payload = {
        "output": {
            "summary": {
                "title": "Test Storyboard",
                "storyboard_cards": [
                    {
                        "description": "Opening shot",
                        "composition": "Wide shot",
                    }
                ],
            }
        }
    }
    artifacts = derive_artifacts_from_tool_payload("run_capsule", payload)
    types = {artifact.get("artifact_type") for artifact in artifacts}
    assert "storyboard" in types
    assert "shot_list" in types


def test_derive_analyze_sources_data_table():
    payload = {
        "output": {
            "summary": {
                "claims": [
                    {
                        "claim_id": "c1",
                        "statement": "Claim statement",
                        "evidence_refs": ["ref-1"],
                    }
                ],
                "token_usage": {"input": 1, "output": 2, "total": 3},
            },
            "evidence_refs": ["ref-1"],
        }
    }
    artifacts = derive_artifacts_from_tool_payload("analyze_sources", payload)
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.get("artifact_type") == "data_table"
    assert artifact.get("rows")
    assert artifact["rows"][0]["statement"] == "Claim statement"


def test_derive_generate_storyboard_preview():
    payload = {
        "output": {
            "storyboard": [
                {
                    "description": "Scene preview",
                    "duration_hint": "4s",
                }
            ]
        }
    }
    artifacts = derive_artifacts_from_tool_payload("generate_storyboard", payload)
    assert len(artifacts) == 1
    assert artifacts[0].get("artifact_type") == "storyboard"
