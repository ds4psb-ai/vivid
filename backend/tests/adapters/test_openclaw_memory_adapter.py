from app.features.original_ip_foundry.memory_adapter import (
    InMemoryDirectorMemoryStore,
    OpenClawMemoryAdapter,
)


def test_normalize_memory_extracts_characters_and_tags():
    adapter = OpenClawMemoryAdapter()

    item = adapter.normalize(
        tenant_id="tenant-1",
        project_id="proj-1",
        scene_id="scene-3",
        source_channel="telegram",
        note="@Hero enters with low-angle shot, handheld panic beat #intent:power",
        attachments=["https://example.com/img.png"],
    )

    assert item.tenant_id == "tenant-1"
    assert item.project_id == "proj-1"
    assert "hero" in item.characters
    assert "power" in item.intent_tags
    assert "low_angle" in item.mise_en_scene_tags
    assert "handheld" in item.mise_en_scene_tags


def test_memory_store_is_isolated_by_tenant():
    adapter = OpenClawMemoryAdapter()
    store = InMemoryDirectorMemoryStore()

    item_a = adapter.normalize(
        tenant_id="tenant-a",
        project_id="proj-1",
        scene_id="scene-1",
        source_channel="web",
        note="@hero low-angle pressure beat",
    )
    item_b = adapter.normalize(
        tenant_id="tenant-b",
        project_id="proj-1",
        scene_id="scene-1",
        source_channel="web",
        note="@hero high-angle release beat",
    )
    store.put(item_a)
    store.put(item_b)

    results_a = store.search("tenant-a", "proj-1", "pressure", limit=5)
    results_b = store.search("tenant-b", "proj-1", "pressure", limit=5)

    assert len(results_a) == 1
    assert results_a[0]["tenant_id"] == "tenant-a"
    assert len(results_b) == 1
    assert results_b[0]["tenant_id"] == "tenant-b"
    assert "high-angle" in results_b[0]["note"]
