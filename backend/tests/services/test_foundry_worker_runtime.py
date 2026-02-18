from app.features.original_ip_foundry.worker_runtime import FoundryWorkerRuntime


def test_runtime_uses_configured_provider_by_default():
    runtime = FoundryWorkerRuntime()

    result = runtime.dispatch_job(
        tenant_id="tenant-a",
        project_id="project-a",
        job_type="index_rebuild",
        payload={"scope": "all"},
        provider="taskiq",
    )

    assert result["provider"] == "taskiq"
    assert result["status"] == "queued"
    assert result["tenant_id"] == "tenant-a"


def test_runtime_tracks_status_and_cancel():
    runtime = FoundryWorkerRuntime()
    dispatch = runtime.dispatch_job(
        tenant_id="tenant-b",
        project_id="project-b",
        job_type="eval_rollup",
        payload={"window": "7d"},
        provider="agent0",
    )
    job_id = dispatch["job_id"]

    status = runtime.get_job_status(job_id)
    assert status["provider"] == "agent0"
    assert status["job_id"] == job_id

    cancelled = runtime.cancel_job(job_id)
    assert cancelled["status"] == "cancel_requested"
    assert cancelled["job_id"] == job_id

