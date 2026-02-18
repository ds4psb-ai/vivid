"""Tests for QdrantPatternAtomStore."""
from unittest.mock import MagicMock, patch

from app.features.original_ip_foundry.qdrant_pattern_store import QdrantPatternAtomStore


def _make_store_with_mocks():
    store = QdrantPatternAtomStore()
    mock_client = MagicMock()
    store._client = mock_client
    mock_embedder = MagicMock()
    mock_embedder.embed.return_value = [0.1] * 384
    mock_embedder.embed_batch.return_value = [[0.1] * 384, [0.2] * 384]
    store._embedder = mock_embedder
    return store, mock_client, mock_embedder


def test_upsert_batch_stores_atoms():
    store, mock_client, mock_embedder = _make_store_with_mocks()

    atoms = [
        {"atom_id": "low_angle::tracking::close_up::anxiety::cut", "camera_angle": "low_angle",
         "camera_movement": "tracking", "shot_size": "close_up", "emotion_tone": "anxiety",
         "transition": "cut", "frequency": 2, "confidence": 0.75},
        {"atom_id": "eye_level::static::medium::neutral::cut", "camera_angle": "eye_level",
         "camera_movement": "static", "shot_size": "medium", "emotion_tone": "neutral",
         "transition": "cut", "frequency": 1, "confidence": 0.55},
    ]

    result = store.upsert_batch(project_id="p1", scene_id="s1", atoms=atoms)

    assert len(result) == 2
    assert mock_client.upsert.call_count == 1
    assert mock_embedder.embed_batch.call_count == 1


def test_upsert_batch_empty_atoms_returns_empty():
    store, mock_client, _ = _make_store_with_mocks()

    result = store.upsert_batch(project_id="p1", scene_id="s1", atoms=[])

    assert result == []
    assert mock_client.upsert.call_count == 0


def test_search_atoms_returns_payloads():
    store, mock_client, mock_embedder = _make_store_with_mocks()

    mock_hit = MagicMock()
    mock_hit.payload = {"atom_id": "test", "camera_angle": "low_angle", "confidence": 0.8}
    mock_client.search.return_value = [mock_hit]

    results = store.search_atoms(project_id="p1", query="low angle tracking")

    assert len(results) == 1
    assert results[0]["atom_id"] == "test"
    assert mock_embedder.embed.call_count == 1


def test_unavailable_qdrant_returns_empty():
    store = QdrantPatternAtomStore()
    store._available = False

    assert store.upsert_batch(project_id="p1", scene_id="s1", atoms=[{"atom_id": "x"}]) == []
    assert store.search_atoms(project_id="p1", query="test") == []


def test_upsert_is_idempotent():
    store, mock_client, _ = _make_store_with_mocks()

    atoms = [{"atom_id": "a::b::c::d::e", "camera_angle": "a", "camera_movement": "b",
              "shot_size": "c", "emotion_tone": "d", "transition": "e", "frequency": 1, "confidence": 0.5}]

    ids_first = store.upsert_batch(project_id="p1", scene_id="s1", atoms=atoms)
    ids_second = store.upsert_batch(project_id="p1", scene_id="s1", atoms=atoms)

    assert ids_first == ids_second
