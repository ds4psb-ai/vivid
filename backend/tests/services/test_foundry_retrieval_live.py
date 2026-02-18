"""4-Pass Retrieval Pipeline Validation tests.

Tests each of the 4 retrieval passes using in-memory services
seeded with real corpus data.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pytest

from app.features.original_ip_foundry.memory_adapter import (
    InMemoryDirectorMemoryStore,
    OpenClawMemoryAdapter,
)
from app.features.original_ip_foundry.pattern_extraction_service import PatternExtractionService
from app.features.original_ip_foundry.retrieval_service import FoundryRetrievalService

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "foundry" / "seed_shot_corpus.json"


@pytest.fixture(scope="module")
def corpus_shots() -> list[dict]:
    with open(DATA_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def seeded_pattern_service(corpus_shots) -> PatternExtractionService:
    """Extract patterns for all directors into an in-memory service."""
    service = PatternExtractionService(qdrant_store=None)
    by_director: dict[str, list[dict]] = defaultdict(list)
    for shot in corpus_shots:
        by_director[shot["director"]].append(shot)

    for director, shots in by_director.items():
        service.extract(
            project_id=f"seed_{director}",
            scene_id=f"corpus_{director}",
            shots=shots,
        )
    return service


@pytest.fixture(scope="module")
def seeded_memory_store() -> InMemoryDirectorMemoryStore:
    """Seed director memory with example notes."""
    store = InMemoryDirectorMemoryStore()
    adapter = OpenClawMemoryAdapter()

    notes = [
        {
            "tenant_id": "default",
            "project_id": "seed_kubrick",
            "scene_id": "s01",
            "source_channel": "web",
            "note": "Symmetrical wide shot with @jack walking through the hotel corridor, low-angle dolly movement creating tension. #intent:anxiety",
        },
        {
            "tenant_id": "default",
            "project_id": "seed_kubrick",
            "scene_id": "s02",
            "source_channel": "web",
            "note": "Steadicam tracking @danny through the maze, isolation and fear atmosphere.",
        },
        {
            "tenant_id": "default",
            "project_id": "seed_bong",
            "scene_id": "s01",
            "source_channel": "telegram",
            "note": "High-angle crane shot showing class contrast between @ki_woo and @mr_park, #intent:power dynamics in the mansion garden.",
        },
        {
            "tenant_id": "default",
            "project_id": "seed_bong",
            "scene_id": "s02",
            "source_channel": "web",
            "note": "Close-up handheld @chung_sook in the kitchen, tension building with tracking movement.",
        },
        {
            "tenant_id": "default",
            "project_id": "seed_tarantino",
            "scene_id": "s01",
            "source_channel": "web",
            "note": "Extreme close-up of @jules with low-angle, power and rage, whip-pan transition.",
        },
    ]

    for n in notes:
        entry = adapter.normalize(**n)
        store.put(entry)

    return store


@pytest.fixture(scope="module")
def retrieval_service(
    seeded_memory_store: InMemoryDirectorMemoryStore,
    seeded_pattern_service: PatternExtractionService,
) -> FoundryRetrievalService:
    return FoundryRetrievalService(
        memory_store=seeded_memory_store,
        pattern_service=seeded_pattern_service,
    )


# ── Pass 1: Director Context Query ────────────────────────────────────


class TestDirectorContextQuery:
    """Pass 1: query director memory for contextual notes."""

    def test_returns_matching_entries(self, retrieval_service):
        result = retrieval_service.query(
            tenant_id="default",
            project_id="seed_kubrick",
            query_type="director_context",
            query="hotel corridor tension dolly",
            limit=5,
        )
        assert result["source"] == "openclaw_memory"
        assert result["query_type"] == "director_context"
        assert len(result["items"]) > 0

    def test_kubrick_anxiety_intent(self, retrieval_service):
        result = retrieval_service.query(
            tenant_id="default",
            project_id="seed_kubrick",
            query_type="director_context",
            query="anxiety fear",
            limit=5,
        )
        items = result["items"]
        assert len(items) > 0
        # At least one should have anxiety intent
        all_intents = []
        for item in items:
            all_intents.extend(item.get("intent_tags", []))
        assert "anxiety" in all_intents

    def test_bong_power_intent(self, retrieval_service):
        result = retrieval_service.query(
            tenant_id="default",
            project_id="seed_bong",
            query_type="director_context",
            query="power class contrast",
            limit=5,
        )
        assert len(result["items"]) > 0

    def test_empty_project_returns_empty(self, retrieval_service):
        result = retrieval_service.query(
            tenant_id="default",
            project_id="nonexistent_project",
            query_type="director_context",
            query="anything",
            limit=5,
        )
        assert len(result["items"]) == 0


# ── Pass 2: Shot Reference Query ──────────────────────────────────────


class TestShotReferenceQuery:
    """Pass 2: pattern-based shot reference search."""

    def test_returns_pattern_atoms(self, retrieval_service):
        result = retrieval_service.query(
            tenant_id="default",
            project_id="seed_kubrick",
            query_type="shot_reference",
            query="dolly wide tension",
            limit=5,
        )
        assert result["source"] == "foundry_shot_corpus"
        assert result["query_type"] == "shot_reference"
        assert len(result["items"]) > 0

    def test_atoms_have_required_fields(self, retrieval_service):
        result = retrieval_service.query(
            tenant_id="default",
            project_id="seed_kubrick",
            query_type="shot_reference",
            query="steadicam isolation",
            limit=3,
        )
        for item in result["items"]:
            assert "atom_id" in item
            assert "camera_angle" in item
            assert "camera_movement" in item
            assert "confidence" in item

    def test_kubrick_has_steadicam_atoms(self, retrieval_service):
        result = retrieval_service.query(
            tenant_id="default",
            project_id="seed_kubrick",
            query_type="shot_reference",
            query="steadicam",
            limit=10,
        )
        movements = [item.get("camera_movement") for item in result["items"]]
        assert "steadicam" in movements

    def test_tarantino_has_whip_pan_atoms(self, retrieval_service):
        result = retrieval_service.query(
            tenant_id="default",
            project_id="seed_tarantino",
            query_type="shot_reference",
            query="whip_pan close_up",
            limit=10,
        )
        movements = [item.get("camera_movement") for item in result["items"]]
        assert "whip_pan" in movements


# ── Pass 3: Payload Filter Query ──────────────────────────────────────


class TestPayloadFilterQuery:
    """Pass 3: Qdrant payload-filtered search."""

    def test_filter_by_camera_movement(self, retrieval_service):
        result = retrieval_service.query(
            tenant_id="default",
            project_id="seed_kubrick",
            query_type="payload_filter",
            query="dolly tension",
            limit=10,
            filters={"camera_movement": "dolly"},
        )
        assert result["query_type"] == "payload_filter"
        for item in result["items"]:
            assert item["camera_movement"] == "dolly"

    def test_filter_by_emotion(self, retrieval_service):
        result = retrieval_service.query(
            tenant_id="default",
            project_id="seed_bong",
            query_type="payload_filter",
            query="tension fear",
            limit=10,
            filters={"emotion_tone": "tension"},
        )
        for item in result["items"]:
            assert item["emotion_tone"] == "tension"

    def test_filter_with_list_values(self, retrieval_service):
        result = retrieval_service.query(
            tenant_id="default",
            project_id="seed_kubrick",
            query_type="payload_filter",
            query="wide shot",
            limit=10,
            filters={"shot_size": ["wide", "extreme_wide"]},
        )
        for item in result["items"]:
            assert item["shot_size"] in ["wide", "extreme_wide"]

    def test_no_filter_returns_all(self, retrieval_service):
        result = retrieval_service.query(
            tenant_id="default",
            project_id="seed_nolan",
            query_type="payload_filter",
            query="awe crane",
            limit=5,
        )
        # Without filters, should return items from pattern search
        assert len(result["items"]) > 0

    def test_filters_applied_in_response(self, retrieval_service):
        result = retrieval_service.query(
            tenant_id="default",
            project_id="seed_kubrick",
            query_type="payload_filter",
            query="dolly",
            limit=5,
            filters={"camera_movement": "dolly"},
        )
        assert result.get("filters_applied") == {"camera_movement": "dolly"}


# ── Pass 4: Transition Rerank Query ───────────────────────────────────


class TestTransitionRerankQuery:
    """Pass 4: Pattern search + transition rule affinity reranking."""

    def test_returns_reranked_results(self, retrieval_service):
        result = retrieval_service.query(
            tenant_id="default",
            project_id="seed_kubrick",
            query_type="transition_rerank",
            query="wide dolly tension",
            limit=5,
        )
        assert result["source"] == "foundry_transition_rerank"
        assert result["query_type"] == "transition_rerank"
        assert len(result["items"]) > 0

    def test_dissolve_ranked_above_cut_given_equal_confidence(self, retrieval_service):
        """Items with dissolve transition should get bonus over plain cut."""
        result = retrieval_service.query(
            tenant_id="default",
            project_id="seed_kubrick",
            query_type="transition_rerank",
            query="tension",
            limit=20,
        )
        items = result["items"]
        if len(items) < 2:
            pytest.skip("Not enough items to test reranking")

        # Find first dissolve and first cut in ranked list
        dissolve_rank = None
        cut_rank = None
        for i, item in enumerate(items):
            if item.get("transition") == "dissolve" and dissolve_rank is None:
                dissolve_rank = i
            if item.get("transition") == "cut" and cut_rank is None:
                cut_rank = i
            if dissolve_rank is not None and cut_rank is not None:
                break

        # If both exist and have similar base confidence, dissolve should rank higher
        if dissolve_rank is not None and cut_rank is not None:
            dissolve_conf = items[dissolve_rank].get("confidence", 0)
            cut_conf = items[cut_rank].get("confidence", 0)
            # Only assert if base confidences are close (within 0.15)
            if abs(dissolve_conf - cut_conf) < 0.15:
                assert dissolve_rank < cut_rank, (
                    f"Dissolve (rank {dissolve_rank}, conf {dissolve_conf}) "
                    f"should rank above cut (rank {cut_rank}, conf {cut_conf})"
                )

    def test_limit_respected(self, retrieval_service):
        for limit in [1, 3, 5]:
            result = retrieval_service.query(
                tenant_id="default",
                project_id="seed_kubrick",
                query_type="transition_rerank",
                query="tension wide",
                limit=limit,
            )
            assert len(result["items"]) <= limit
