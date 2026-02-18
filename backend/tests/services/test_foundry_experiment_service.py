from app.features.original_ip_foundry.experiment_service import FoundryExperimentService


def test_assignment_is_deterministic_per_user_and_scene():
    service = FoundryExperimentService()

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


def test_feedback_summary_aggregates_rates():
    service = FoundryExperimentService()
    service.record_feedback(
        tenant_id="tenant-a",
        experiment_key="exp-2",
        user_key="u1",
        variant="A",
        outcome="accepted",
        completion_seconds=30,
    )
    service.record_feedback(
        tenant_id="tenant-a",
        experiment_key="exp-2",
        user_key="u2",
        variant="A",
        outcome="edited",
        completion_seconds=40,
    )
    service.record_feedback(
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
