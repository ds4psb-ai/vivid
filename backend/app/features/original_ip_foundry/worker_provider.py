"""Worker provider ports for Foundry batch orchestration."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class WorkerProvider(Protocol):
    def dispatch_job(self, job_type: str, payload: dict, *, tenant_id: str, project_id: str) -> dict: ...
    def get_job_status(self, job_id: str) -> dict: ...
    def cancel_job(self, job_id: str) -> dict: ...


def _build_fingerprint(provider: str, job_type: str, tenant_id: str, project_id: str) -> str:
    return hashlib.sha256(
        f"{provider}:{tenant_id}:{project_id}:{job_type}:{datetime.utcnow().isoformat()}".encode("utf-8")
    ).hexdigest()[:16]


@dataclass
class TaskiqWorkerProvider:
    """Taskiq-friendly provider (works as adapter even before full migration)."""

    broker_path: str

    def dispatch_job(self, job_type: str, payload: dict, *, tenant_id: str, project_id: str) -> dict:
        fingerprint = _build_fingerprint("taskiq", job_type, tenant_id, project_id)
        return {
            "provider": "taskiq",
            "status": "queued",
            "job_id": f"taskiq-{fingerprint}",
            "job_type": job_type,
            "tenant_id": tenant_id,
            "project_id": project_id,
            "payload": payload,
            "broker": self.broker_path,
        }

    def get_job_status(self, job_id: str) -> dict:
        return {
            "provider": "taskiq",
            "job_id": job_id,
            "status": "unknown",
            "message": "Taskiq provider is configured as adapter; integrate broker backend for live status.",
        }

    def cancel_job(self, job_id: str) -> dict:
        return {
            "provider": "taskiq",
            "job_id": job_id,
            "status": "cancel_requested",
        }


@dataclass
class Agent0WorkerProvider:
    """Agent0 provider adapter."""

    control_plane: str = "agent0-control-plane"

    def dispatch_job(self, job_type: str, payload: dict, *, tenant_id: str, project_id: str) -> dict:
        fingerprint = _build_fingerprint("agent0", job_type, tenant_id, project_id)
        return {
            "provider": "agent0",
            "status": "queued",
            "job_id": f"agent0-{fingerprint}",
            "job_type": job_type,
            "tenant_id": tenant_id,
            "project_id": project_id,
            "payload": payload,
            "control_plane": self.control_plane,
        }

    def get_job_status(self, job_id: str) -> dict:
        return {
            "provider": "agent0",
            "job_id": job_id,
            "status": "unknown",
            "message": "Agent0 adapter mode: attach real control-plane API for live status.",
        }

    def cancel_job(self, job_id: str) -> dict:
        return {
            "provider": "agent0",
            "job_id": job_id,
            "status": "cancel_requested",
        }


@dataclass
class TemporalWorkerProvider:
    """Temporal provider adapter."""

    namespace: str = "default"

    def dispatch_job(self, job_type: str, payload: dict, *, tenant_id: str, project_id: str) -> dict:
        fingerprint = _build_fingerprint("temporal", job_type, tenant_id, project_id)
        return {
            "provider": "temporal",
            "status": "queued",
            "job_id": f"temporal-{fingerprint}",
            "job_type": job_type,
            "tenant_id": tenant_id,
            "project_id": project_id,
            "payload": payload,
            "namespace": self.namespace,
        }

    def get_job_status(self, job_id: str) -> dict:
        return {
            "provider": "temporal",
            "job_id": job_id,
            "status": "unknown",
            "message": "Temporal adapter mode: wire workflow handle for live status.",
        }

    def cancel_job(self, job_id: str) -> dict:
        return {
            "provider": "temporal",
            "job_id": job_id,
            "status": "cancel_requested",
        }
