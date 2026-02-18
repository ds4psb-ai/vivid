"""Port contract tests for Foundry worker providers."""
import time

import pytest

from app.features.original_ip_foundry.worker_provider import (
    Agent0WorkerProvider,
    TaskiqWorkerProvider,
    TemporalWorkerProvider,
)

PROVIDERS = [
    pytest.param(TaskiqWorkerProvider(broker_path="test"), id="taskiq"),
    pytest.param(Agent0WorkerProvider(), id="agent0"),
    pytest.param(TemporalWorkerProvider(), id="temporal"),
]

REQUIRED_DISPATCH_KEYS = {"provider", "status", "job_id", "job_type", "tenant_id", "project_id"}


# --- dispatch_job returns required fields ---


@pytest.mark.parametrize("provider", PROVIDERS)
def test_dispatch_returns_required_fields(provider):
    result = provider.dispatch_job(
        "pattern_reindex", {"data": "x"}, tenant_id="t1", project_id="p1"
    )
    assert REQUIRED_DISPATCH_KEYS.issubset(result.keys())


@pytest.mark.parametrize("provider", PROVIDERS)
def test_dispatch_status_is_queued(provider):
    result = provider.dispatch_job(
        "render", {}, tenant_id="t1", project_id="p1"
    )
    assert result["status"] == "queued"


@pytest.mark.parametrize("provider", PROVIDERS)
def test_dispatch_preserves_job_type(provider):
    result = provider.dispatch_job(
        "style_transfer", {}, tenant_id="t1", project_id="p1"
    )
    assert result["job_type"] == "style_transfer"


@pytest.mark.parametrize("provider", PROVIDERS)
def test_dispatch_preserves_tenant_and_project(provider):
    result = provider.dispatch_job(
        "render", {}, tenant_id="tenant-x", project_id="proj-y"
    )
    assert result["tenant_id"] == "tenant-x"
    assert result["project_id"] == "proj-y"


# --- dispatch produces unique job_ids ---


@pytest.mark.parametrize("provider", PROVIDERS)
def test_dispatch_produces_unique_ids(provider):
    r1 = provider.dispatch_job("job_a", {}, tenant_id="t1", project_id="p1")
    time.sleep(0.01)  # fingerprint uses datetime
    r2 = provider.dispatch_job("job_b", {}, tenant_id="t1", project_id="p1")
    assert r1["job_id"] != r2["job_id"]


# --- get_job_status returns provider and status ---


@pytest.mark.parametrize("provider", PROVIDERS)
def test_get_job_status_fields(provider):
    status = provider.get_job_status("fake-id-123")
    assert "provider" in status
    assert "status" in status
    assert "job_id" in status


@pytest.mark.parametrize("provider", PROVIDERS)
def test_get_job_status_returns_unknown(provider):
    status = provider.get_job_status("nonexistent-job")
    assert status["status"] == "unknown"


# --- cancel_job returns status ---


@pytest.mark.parametrize("provider", PROVIDERS)
def test_cancel_returns_status(provider):
    result = provider.cancel_job("fake-cancel-id")
    assert "status" in result
    assert result["status"] == "cancel_requested"


@pytest.mark.parametrize("provider", PROVIDERS)
def test_cancel_returns_provider(provider):
    result = provider.cancel_job("fake-cancel-id")
    assert "provider" in result


# --- Job ID prefix matches provider name ---


@pytest.mark.parametrize(
    "provider,expected_prefix",
    [
        (TaskiqWorkerProvider(broker_path="test"), "taskiq-"),
        (Agent0WorkerProvider(), "agent0-"),
        (TemporalWorkerProvider(), "temporal-"),
    ],
    ids=["taskiq", "agent0", "temporal"],
)
def test_job_id_prefix_matches_provider(provider, expected_prefix):
    result = provider.dispatch_job("render", {}, tenant_id="t1", project_id="p1")
    assert result["job_id"].startswith(expected_prefix)


def test_taskiq_includes_broker_path():
    provider = TaskiqWorkerProvider(broker_path="redis://localhost:6379")
    result = provider.dispatch_job("render", {}, tenant_id="t1", project_id="p1")
    assert result["broker"] == "redis://localhost:6379"
