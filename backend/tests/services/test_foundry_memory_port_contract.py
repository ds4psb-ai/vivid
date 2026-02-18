"""Port contract tests for Foundry memory adapter and store."""
import pytest

from app.features.original_ip_foundry.memory_adapter import (
    InMemoryDirectorMemoryStore,
    MemoryEntry,
    OpenClawMemoryAdapter,
)


@pytest.fixture
def adapter():
    return OpenClawMemoryAdapter()


@pytest.fixture
def store():
    return InMemoryDirectorMemoryStore()


# --- normalize() returns MemoryEntry with correct fields ---


@pytest.mark.parametrize("channel", ["telegram", "web", "notion", "other"])
def test_normalize_returns_memory_entry_per_channel(adapter, channel):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id="s1",
        source_channel=channel,
        note="hello world",
    )
    assert isinstance(entry, MemoryEntry)
    assert entry.tenant_id == "t1"
    assert entry.project_id == "p1"
    assert entry.scene_id == "s1"
    assert entry.source_channel == channel


def test_normalize_preserves_attachments(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="with files",
        attachments=["img.png", "doc.pdf"],
    )
    assert entry.attachments == ["img.png", "doc.pdf"]


def test_normalize_none_attachments_becomes_empty_list(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="no attachments",
        attachments=None,
    )
    assert entry.attachments == []


# --- Character extraction from @mentions ---


def test_character_extraction_single_mention(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="Focus on @Hero in this scene",
    )
    assert "hero" in entry.characters


def test_character_extraction_multiple_mentions(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="@Alice confronts @Bob while @Charlie watches",
    )
    assert entry.characters == ["alice", "bob", "charlie"]


def test_character_extraction_deduplication(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="@Hero fights then @Hero retreats",
    )
    assert entry.characters == ["hero"]


# --- Intent tag inference ---


def test_intent_fear_maps_to_anxiety(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="a scene of fear and panic",
    )
    assert "anxiety" in entry.intent_tags


def test_intent_power_keyword(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="display of raw power",
    )
    assert "power" in entry.intent_tags


def test_intent_intimate_maps_to_intimacy(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="an intimate conversation",
    )
    assert "intimacy" in entry.intent_tags


def test_intent_lonely_maps_to_isolation(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="a lonely character",
    )
    assert "isolation" in entry.intent_tags


def test_explicit_intent_tag_overrides_inference(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="fear and power #intent:custom_tag",
    )
    # When explicit intent tags are present, inference is skipped
    assert entry.intent_tags == ["custom_tag"]


# --- Mise-en-scene tag extraction ---


def test_mise_low_angle(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="use a low-angle shot here",
    )
    assert "low_angle" in entry.mise_en_scene_tags


def test_mise_close_up(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="close-up on the face",
    )
    assert "close_up" in entry.mise_en_scene_tags


def test_mise_multiple_tags(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="tracking dolly shot with backlight",
    )
    assert "tracking" in entry.mise_en_scene_tags
    assert "dolly" in entry.mise_en_scene_tags
    assert "backlight" in entry.mise_en_scene_tags


# --- to_dict() ---


def test_to_dict_returns_all_fields(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id="s1",
        source_channel="telegram",
        note="@Hero in fear with close-up",
    )
    d = entry.to_dict()
    assert d["tenant_id"] == "t1"
    assert d["project_id"] == "p1"
    assert d["scene_id"] == "s1"
    assert d["source_channel"] == "telegram"
    assert "created_at" in d
    assert isinstance(d["characters"], list)
    assert isinstance(d["intent_tags"], list)
    assert isinstance(d["mise_en_scene_tags"], list)


# --- put/search roundtrip ---


def test_put_search_roundtrip(adapter, store):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id="s1",
        source_channel="web",
        note="tracking shot with @Hero showing power",
    )
    store.put(entry)
    results = store.search("t1", "p1", "tracking")
    assert len(results) >= 1
    assert results[0]["note"] == "tracking shot with @Hero showing power"


def test_search_empty_store(store):
    results = store.search("t1", "p1", "anything")
    assert results == []


def test_search_no_match_returns_recent_fallback(adapter, store):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="completely unrelated note about weather",
    )
    store.put(entry)
    # Query terms that don't match anything should fall back to recent items
    results = store.search("t1", "p1", "zzzznonexistent")
    assert len(results) == 1
    assert results[0]["note"] == "completely unrelated note about weather"


# --- Empty note handling ---


def test_empty_note_handling(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="",
    )
    assert entry.note == ""
    assert entry.characters == []
    assert entry.intent_tags == []
    assert entry.mise_en_scene_tags == []


# --- Korean unicode text ---


def test_korean_unicode_text(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="미장센 분석: 로우앵글 트래킹 숏",
    )
    assert isinstance(entry, MemoryEntry)
    assert entry.note == "미장센 분석: 로우앵글 트래킹 숏"


def test_korean_intent_keywords(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="공포와 불안의 장면",
    )
    assert "anxiety" in entry.intent_tags


def test_korean_power_keyword(adapter):
    entry = adapter.normalize(
        tenant_id="t1",
        project_id="p1",
        scene_id=None,
        source_channel="web",
        note="권력 구조를 보여주는 씬",
    )
    assert "power" in entry.intent_tags
