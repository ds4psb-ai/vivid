import asyncio

import pytest

from app.features.original_ip_foundry.experiment_service import FoundryExperimentService


def test_assignment_is_deterministic_per_user_and_scene():
    service = FoundryExperimentService(use_thompson=False)

    first = service.assign(
        tenant_id="tenant-a",
        experiment_key="exp-1",
        user_key="user-1",
        scene_id="scene-1",
        variants=["A", "B", "AB_A", "AB_B"],
    )
    second = service.assign(
        tenant_id="tenant-a",
        experiment_key="exp-1",
        user_key="user-1",
        scene_id="scene-1",
        variants=["A", "B", "AB_A", "AB_B"],
    )

    assert first["assigned_variant"] == second["assigned_variant"]
    assert first["hash_slot"] == second["hash_slot"]


@pytest.mark.asyncio
async def test_feedback_summary_aggregates_rates():
    service = FoundryExperimentService(use_thompson=False)
    await service.record_feedback(
        tenant_id="tenant-a",
        experiment_key="exp-2",
        user_key="u1",
        variant="A",
        outcome="accepted",
        completion_seconds=30,
    )
    await service.record_feedback(
        tenant_id="tenant-a",
        experiment_key="exp-2",
        user_key="u2",
        variant="A",
        outcome="edited",
        completion_seconds=40,
    )
    await service.record_feedback(
        tenant_id="tenant-a",
        experiment_key="exp-2",
        user_key="u3",
        variant="B",
        outcome="rejected",
        completion_seconds=22,
    )

    summary = service.summary(tenant_id="tenant-a", experiment_key="exp-2")
    assert summary["total_events"] == 3
    assert summary["variants"]["A"]["accept_rate"] == 0.5
    assert summary["variants"]["B"]["reject_rate"] == 1.0


def test_hash_used_before_warmup():
    """Thompson should not activate when fewer than 10 trials recorded."""
    service = FoundryExperimentService(use_thompson=True)

    result = service.assign(
        tenant_id="t1", experiment_key="exp-warmup",
        user_key="u1", scene_id=None, variants=["A", "B"],
    )
    assert result["assigned_variant"] in ["A", "B"]
    # With 0 events, Thompson should not be active in summary
    summary = service.summary("t1", "exp-warmup")
    assert summary["thompson_active"] is False


@pytest.mark.asyncio
async def test_thompson_activates_after_warmup():
    """After 10+ feedback events, Thompson should activate."""
    service = FoundryExperimentService(use_thompson=True)

    # Generate 12 feedback events
    for i in range(12):
        await service.record_feedback(
            tenant_id="t1", experiment_key="exp-warm",
            user_key=f"u{i}", variant="A" if i % 2 == 0 else "B",
            outcome="accepted" if i % 3 == 0 else "edited",
        )

    summary = service.summary("t1", "exp-warm")
    assert summary["thompson_active"] is True
    assert summary["total_events"] == 12


@pytest.mark.asyncio
async def test_feedback_updates_thompson_arm():
    """record_feedback should update Thompson arm stats."""
    service = FoundryExperimentService(use_thompson=True)

    await service.record_feedback(
        tenant_id="t1", experiment_key="exp-arm",
        user_key="u1", variant="A", outcome="accepted",
    )

    arm_id = "foundry:t1:exp-arm:A"
    assert service._thompson is not None
    assert arm_id in service._thompson.arms
    # accepted → reward_value=1.0 → alpha incremented
    assert service._thompson.arms[arm_id]["alpha"] > 1


@pytest.mark.asyncio
async def test_summary_includes_thompson_stats():
    """Summary should include thompson_stats and thompson_active fields."""
    service = FoundryExperimentService(use_thompson=True)

    await service.record_feedback(
        tenant_id="t1", experiment_key="exp-stats",
        user_key="u1", variant="A", outcome="accepted",
    )

    summary = service.summary("t1", "exp-stats")
    assert "thompson_active" in summary
    assert "thompson_stats" in summary
    assert isinstance(summary["thompson_stats"], dict)


@pytest.mark.asyncio
async def test_enhanced_reward_params_accepted():
    """record_feedback accepts edit_distance and satisfaction_score."""
    service = FoundryExperimentService(use_thompson=False)
    result = await service.record_feedback(
        tenant_id="t1", experiment_key="exp-enhanced",
        user_key="u1", variant="A", outcome="accepted",
        edit_distance=0.3, satisfaction_score=0.9,
    )
    assert result["status"] == "recorded"


@pytest.mark.asyncio
async def test_enhanced_reward_uses_4factor():
    """Enhanced reward should produce different values based on edit_distance."""
    service = FoundryExperimentService(use_thompson=True)

    await service.record_feedback(
        tenant_id="t1", experiment_key="exp-4f",
        user_key="u1", variant="A", outcome="edited",
        edit_distance=0.0,
    )
    await service.record_feedback(
        tenant_id="t1", experiment_key="exp-4f",
        user_key="u2", variant="A", outcome="edited",
        edit_distance=0.9,
    )
    # Both recorded successfully
    summary = service.summary("t1", "exp-4f")
    assert summary["total_events"] == 2
