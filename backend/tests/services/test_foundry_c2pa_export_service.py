from app.features.original_ip_foundry.c2pa_export_service import FoundryC2PAExportService


def test_c2pa_export_contains_actions_and_ingredients():
    service = FoundryC2PAExportService()

    result = service.export_manifest(
        project_id="proj-1",
        scene_id="scene-9",
        asset_id="asset-1",
        title="Scene 9 Candidate",
        generator_model="gemini-3-pro",
        source_license="cc-by-4.0",
        actions=[
            {"action": "c2pa.created", "parameters": {"prompt": "low-angle confrontation"}},
            {"action": "c2pa.edited", "parameters": {"tool": "kling-3.0"}},
        ],
        provenance_trace=[
            {"asset_id": "src-1", "relationship": "componentOf", "title": "Reference clip"},
            {"asset_id": "src-2", "relationship": "componentOf", "title": "Mood image"},
        ],
    )

    assert result["spec_version"] == "2.2"
    manifest = result["manifest"]
    assert manifest["claim_generator"] == "VIVID Original-IP Foundry"
    assertion_labels = [item["label"] for item in manifest["assertions"]]
    assert "c2pa.actions" in assertion_labels
    assert "c2pa.ingredient" in assertion_labels
    assert result["compliance"]["eu_ai_act_article_50_ready"] is True

