from app.features.original_ip_foundry.memory_adapter import OpenClawMemoryAdapter


def test_normalize_memory_extracts_characters_and_tags():
    adapter = OpenClawMemoryAdapter()

    item = adapter.normalize(
        project_id="proj-1",
        scene_id="scene-3",
        source_channel="telegram",
        note="@Hero enters with low-angle shot, handheld panic beat #intent:power",
        attachments=["https://example.com/img.png"],
    )

    assert item.project_id == "proj-1"
    assert "hero" in item.characters
    assert "power" in item.intent_tags
    assert "low_angle" in item.mise_en_scene_tags
    assert "handheld" in item.mise_en_scene_tags

