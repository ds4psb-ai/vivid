from unittest.mock import MagicMock

from app.features.original_ip_foundry.qdrant_safe_writer import FoundryQdrantSafeWriter


def test_upsert_with_revision_conflict_returns_conflict():
    mock_client = MagicMock()
    existing = MagicMock()
    existing.payload = {"revision": 3}
    mock_client.retrieve.return_value = [existing]

    writer = FoundryQdrantSafeWriter(client=mock_client)
    result = writer.upsert_point(
        collection_name="foundry_pattern_atoms",
        point_id="point-1",
        vector=[0.1, 0.2],
        payload={"atom_id": "a1"},
        expected_revision=2,
    )

    assert result["status"] == "conflict"
    assert result["current_revision"] == 3


def test_upsert_with_matching_revision_uses_strong_ordering():
    mock_client = MagicMock()
    existing = MagicMock()
    existing.payload = {"revision": 2}
    mock_client.retrieve.return_value = [existing]

    writer = FoundryQdrantSafeWriter(client=mock_client)
    result = writer.upsert_point(
        collection_name="foundry_pattern_atoms",
        point_id="point-2",
        vector=[0.3, 0.4],
        payload={"atom_id": "a2"},
        expected_revision=2,
    )

    assert result["status"] == "ok"
    assert result["revision"] == 3
    mock_client.upsert.assert_called_once()

