"""Tests for EnhancedRewardService."""
from app.features.original_ip_foundry.enhanced_reward_service import EnhancedRewardService


def test_accepted_full_reward():
    svc = EnhancedRewardService()
    result = svc.compute_reward(outcome="accepted")
    # adoption=1.0*0.4 + edit_factor=1.0*0.2 + speed=0.5*0.2 + satisfaction=1.0*0.2 = 0.9
    assert result["reward"] == 0.9


def test_rejected_minimal_reward():
    svc = EnhancedRewardService()
    result = svc.compute_reward(outcome="rejected")
    # adoption=0.0*0.4 + edit=1.0*0.2 + speed=0.5*0.2 + satisfaction=0.0*0.2 = 0.3
    assert result["reward"] == 0.3


def test_edited_mid_reward():
    svc = EnhancedRewardService()
    result = svc.compute_reward(outcome="edited")
    assert 0.3 < result["reward"] < 0.9


def test_speed_excellent():
    svc = EnhancedRewardService()
    result = svc.compute_reward(outcome="accepted", completion_seconds=5)
    assert result["factors"]["decision_speed"] == 1.0


def test_speed_poor():
    svc = EnhancedRewardService()
    result = svc.compute_reward(outcome="accepted", completion_seconds=400)
    assert result["factors"]["decision_speed"] == 0.0


def test_edit_distance_reduces_reward():
    svc = EnhancedRewardService()
    r1 = svc.compute_reward(outcome="accepted", edit_distance=0.0)
    r2 = svc.compute_reward(outcome="accepted", edit_distance=0.8)
    assert r1["reward"] > r2["reward"]


def test_satisfaction_override():
    svc = EnhancedRewardService()
    result = svc.compute_reward(outcome="rejected", satisfaction_score=1.0)
    assert result["factors"]["satisfaction"] == 1.0


def test_weights_sum_to_one():
    svc = EnhancedRewardService()
    assert abs(sum(svc.WEIGHTS.values()) - 1.0) < 1e-9


def test_result_contains_all_fields():
    svc = EnhancedRewardService()
    result = svc.compute_reward(outcome="accepted")
    assert "reward" in result
    assert "factors" in result
    assert "weights" in result
    assert set(result["factors"].keys()) == {"adoption", "edit_distance", "decision_speed", "satisfaction"}
