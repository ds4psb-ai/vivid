"""Tests for 4-pass retrieval service."""
from app.features.original_ip_foundry.memory_adapter import InMemoryDirectorMemoryStore, OpenClawMemoryAdapter
from app.features.original_ip_foundry.pattern_extraction_service import PatternExtractionService
from app.features.original_ip_foundry.retrieval_service import FoundryRetrievalService


def _make_service():
    mem = InMemoryDirectorMemoryStore()
    adapter = OpenClawMemoryAdapter()
    entry = adapter.normalize(
        tenant_id="t1", project_id="p1", scene_id="s1",
        source_channel="web", note="low angle tracking shot with @hero in dark alley",
    )
    mem.put(entry)
    pattern = PatternExtractionService()
    pattern.extract(
        project_id="p1", scene_id="s1",
        shots=[{"shot_id": "sh1", "camera_angle": "low_angle", "camera_movement": "tracking",
                "shot_size": "medium", "emotion_tone": "tension", "transition_to_next": "dissolve"}],
    )
    return FoundryRetrievalService(mem, pattern)


def test_director_context_pass():
    svc = _make_service()
    result = svc.query(tenant_id="t1", project_id="p1", query_type="director_context",
                       query="low angle", limit=5)
    assert result["source"] == "openclaw_memory"
    assert len(result["items"]) >= 1


def test_shot_reference_pass():
    svc = _make_service()
    result = svc.query(tenant_id="t1", project_id="p1", query_type="shot_reference",
                       query="tracking", limit=5)
    assert result["source"] == "foundry_shot_corpus"


def test_payload_filter_pass():
    svc = _make_service()
    result = svc.query(tenant_id="t1", project_id="p1", query_type="payload_filter",
                       query="low angle", limit=5, filters={"camera_angle": "low_angle"})
    assert result["source"] == "foundry_payload_filter"
    assert "filters_applied" in result


def test_transition_rerank_pass():
    svc = _make_service()
    result = svc.query(tenant_id="t1", project_id="p1", query_type="transition_rerank",
                       query="tension", limit=5)
    assert result["source"] == "foundry_transition_rerank"
