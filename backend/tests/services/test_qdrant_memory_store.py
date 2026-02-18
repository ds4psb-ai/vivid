"""Tests for QdrantDirectorMemoryStore."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.features.original_ip_foundry.memory_adapter import MemoryEntry


def make_entry(tenant_id: str = "t1", project_id: str = "p1", scene_id: str | None = None) -> MemoryEntry:
    return MemoryEntry(
        tenant_id=tenant_id,
        project_id=project_id,
        scene_id=scene_id,
        source_channel="web",
        note="low-angle shot #intent:power",
        intent_tags=["power"],
        mise_en_scene_tags=["low_angle"],
        characters=["@hero"],
        attachments=[],
        created_at=datetime(2026, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def mock_qdrant_client():
    client = MagicMock()
    # search returns list of hits with payload
    hit = MagicMock()
    hit.payload = {
        "note": "low-angle shot",
        "tenant_id": "t1",
        "project_id": "p1",
        "scene_id": None,
        "intent_tags": ["power"],
    }
    client.search.return_value = [hit]
    client.upsert.return_value = None
    return client


@pytest.fixture
def mock_embedder():
    embedder = MagicMock()
    embedder.embed.return_value = [0.1] * 384
    return embedder


@pytest.fixture
def store(mock_qdrant_client, mock_embedder):
    from app.features.original_ip_foundry.qdrant_memory_store import QdrantDirectorMemoryStore
    s = QdrantDirectorMemoryStore()
    s._embedder = mock_embedder
    s._client = mock_qdrant_client
    s._available = True
    return s


def test_put_and_search_memory(store, mock_qdrant_client, mock_embedder):
    """put returns point_id, search returns results."""
    entry = make_entry()
    point_id = store.put(entry)

    # put should return a non-empty string (UUID)
    assert isinstance(point_id, str)
    assert len(point_id) > 0

    # upsert was called
    mock_qdrant_client.upsert.assert_called_once()

    # search works
    results = store.search("t1", "p1", "power shot", limit=5)
    assert isinstance(results, list)
    mock_embedder.embed.assert_called()


def test_memory_tenant_isolation(store, mock_qdrant_client):
    """search filters by tenant_id."""
    store.search("tenant_A", "proj_1", "test query", limit=5)

    call_args = mock_qdrant_client.search.call_args
    # Retrieve query_filter from kwargs or positional args
    query_filter = None
    if call_args.kwargs:
        query_filter = call_args.kwargs.get("query_filter")
    if query_filter is None and call_args.args:
        # Check positional args
        for arg in call_args.args:
            if hasattr(arg, "must"):
                query_filter = arg
                break

    # query_filter should be set (not None)
    assert query_filter is not None, "search must include a tenant_id filter"


def test_memory_scene_filter(store, mock_qdrant_client):
    """entry with scene_id is stored with scene_id in payload."""
    entry = make_entry(scene_id="scene_01")
    store.put(entry)

    call_args = mock_qdrant_client.upsert.call_args
    # Get the points list
    points = None
    if call_args.kwargs:
        points = call_args.kwargs.get("points")
    if points is None and call_args.args:
        points = call_args.args[1] if len(call_args.args) > 1 else None

    assert points is not None
    assert any(p.payload.get("scene_id") == "scene_01" for p in points), \
        "scene_id must be included in Qdrant payload"
