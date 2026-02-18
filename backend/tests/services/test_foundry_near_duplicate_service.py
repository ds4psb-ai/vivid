"""Tests for NearDuplicateService."""
from app.features.original_ip_foundry.near_duplicate_service import NearDuplicateService


def _shots():
    return [
        {"camera_angle": "low_angle", "camera_movement": "dolly",
         "shot_size": "close_up", "emotion_tone": "anxiety", "transition_to_next": "cut"},
    ]


def test_compute_content_hash_deterministic():
    svc = NearDuplicateService()
    h1 = svc.compute_content_hash(_shots())
    h2 = svc.compute_content_hash(_shots())
    assert h1 == h2


def test_first_submission_allowed():
    svc = NearDuplicateService()
    result = svc.check_duplicate(project_id="p1", scene_id="s1", shots=_shots())
    assert result["decision"] == "allow"


def test_duplicate_submission_blocked():
    svc = NearDuplicateService()
    svc.check_duplicate(project_id="p1", scene_id="s1", shots=_shots())
    result = svc.check_duplicate(project_id="p1", scene_id="s2", shots=_shots())
    assert result["decision"] == "block"
    assert "EXACT_HASH_MATCH" in result["reason_codes"]


def test_different_shots_allowed():
    svc = NearDuplicateService()
    svc.check_duplicate(project_id="p1", scene_id="s1", shots=_shots())
    different = [{"camera_angle": "high_angle", "camera_movement": "static",
                  "shot_size": "wide", "emotion_tone": "calm", "transition_to_next": "fade"}]
    result = svc.check_duplicate(project_id="p1", scene_id="s2", shots=different)
    assert result["decision"] == "allow"


def test_content_hash_in_result():
    svc = NearDuplicateService()
    result = svc.check_duplicate(project_id="p1", scene_id="s1", shots=_shots())
    assert "content_hash" in result
    assert len(result["content_hash"]) > 0


def test_thresholds():
    assert NearDuplicateService.COSINE_BLOCK_THRESHOLD == 0.92
    assert NearDuplicateService.COSINE_REVIEW_THRESHOLD == 0.85


def test_no_qdrant_still_works():
    svc = NearDuplicateService(qdrant_pattern_store=None)
    result = svc.check_duplicate(project_id="p1", scene_id="s1", shots=_shots())
    assert result["decision"] == "allow"
    assert result["similarity"] is None
