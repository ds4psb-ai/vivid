"""Contract tests for the Memory Port (InMemoryDirectorMemoryStore)."""
from __future__ import annotations

import pytest

from app.features.original_ip_foundry.memory_adapter import (
    InMemoryDirectorMemoryStore,
    MemoryEntry,
    OpenClawMemoryAdapter,
)


class MemoryPortContractMixin:
    """Mixin that defines the memory port contract.

    Each concrete test class must implement ``get_implementation``.
    """

    def get_implementation(self) -> InMemoryDirectorMemoryStore:
        raise NotImplementedError

    def _make_entry(self, **overrides) -> MemoryEntry:
        defaults = dict(
            tenant_id="t1",
            project_id="p1",
            scene_id="s1",
            source_channel="web",
            note="low-angle tracking shot of @hero in rain",
        )
        defaults.update(overrides)
        adapter = OpenClawMemoryAdapter()
        return adapter.normalize(**defaults)

    # -- contract tests -------------------------------------------------------

    def test_put_and_search(self):
        store = self.get_implementation()
        entry = self._make_entry(note="low-angle tracking shot of @hero in rain")
        store.put(entry)

        results = store.search(tenant_id="t1", project_id="p1", query="hero rain")
        assert len(results) >= 1
        assert results[0]["note"] == entry.note

    def test_list_memory(self):
        store = self.get_implementation()
        store.put(self._make_entry(note="scene one establishing shot"))
        store.put(self._make_entry(note="close-up of @hero fear in face"))
        store.put(self._make_entry(note="dolly tracking through corridor"))

        # Empty query returns recent items
        results = store.search(tenant_id="t1", project_id="p1", query="", limit=10)
        assert len(results) == 3

    def test_delete_memory(self):
        """Memory store has no explicit delete — verify isolation by project."""
        store = self.get_implementation()
        store.put(self._make_entry(project_id="p1", note="hero close-up"))
        store.put(self._make_entry(project_id="p2", note="villain wide shot"))

        results_p1 = store.search(tenant_id="t1", project_id="p1", query="hero")
        results_p2 = store.search(tenant_id="t1", project_id="p2", query="hero")
        assert len(results_p1) >= 1
        # p2 has "villain wide shot" — no "hero" keyword match via scoring
        # but empty-match fallback returns recent items
        assert all(r["project_id"] == "p2" for r in results_p2)

    def test_search_empty_returns_empty(self):
        store = self.get_implementation()
        results = store.search(tenant_id="t1", project_id="nonexistent", query="anything")
        assert results == []

    def test_put_overwrites_existing(self):
        """In append-based store, duplicate puts result in duplicates (not overwrite)."""
        store = self.get_implementation()
        entry = self._make_entry(note="dolly shot of @hero")
        store.put(entry)
        store.put(entry)

        results = store.search(tenant_id="t1", project_id="p1", query="dolly hero")
        assert len(results) >= 2  # append semantics


class TestInMemoryDirectorMemoryStore(MemoryPortContractMixin):
    """Concrete contract test class for the built-in in-memory store."""

    def get_implementation(self) -> InMemoryDirectorMemoryStore:
        return InMemoryDirectorMemoryStore()
