from app.features.original_ip_foundry.worker_provider import TaskiqWorkerProvider


def test_taskiq_provider_returns_dispatch_receipt():
    provider = TaskiqWorkerProvider(broker_path="redis://localhost:6379")
    receipt = provider.dispatch_job(
        "pattern_reindex",
        {"project_id": "p1"},
        tenant_id="tenant-a",
        project_id="p1",
    )

    assert receipt["provider"] == "taskiq"
    assert receipt["status"] == "queued"
    assert receipt["job_type"] == "pattern_reindex"
    assert receipt["tenant_id"] == "tenant-a"

