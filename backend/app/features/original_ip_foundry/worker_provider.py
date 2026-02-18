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


@dataclass
class TaskiqWorkerProvider:
    """Taskiq-friendly provider (works as adapter even before full migration)."""

    broker_path: str

    def dispatch_job(self, job_type: str, payload: dict, *, tenant_id: str, project_id: str) -> dict:
        fingerprint = hashlib.sha256(
            f"{tenant_id}:{project_id}:{job_type}:{datetime.utcnow().isoformat()}".encode("utf-8")
        ).hexdigest()[:16]
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

