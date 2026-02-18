"""Worker runtime selector for Foundry providers."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

from app.config import settings
from app.features.original_ip_foundry.worker_provider import (
    Agent0WorkerProvider,
    TaskiqWorkerProvider,
    TemporalWorkerProvider,
    WorkerProvider,
)


class JobScopeMismatchError(ValueError):
    """Raised when caller scope does not match job registry scope."""


@dataclass
class FoundryWorkerRuntime:
    """Dispatch and track jobs across provider adapters."""

    _providers: Dict[str, WorkerProvider] = field(default_factory=dict)
    _job_registry: Dict[str, dict] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self._providers:
            self._providers = {
                "agent0": Agent0WorkerProvider(),
                "taskiq": TaskiqWorkerProvider(broker_path=settings.AD_FOUNDRY_TASKIQ_BROKER),
                "temporal": TemporalWorkerProvider(),
            }

    def resolve_provider(self, preferred: Optional[str] = None) -> str:
        target = (preferred or settings.AD_FOUNDRY_WORKER_PROVIDER or "agent0").strip().lower()
        if target not in self._providers:
            target = "agent0"
        return target

    def list_providers(self) -> list[dict]:
        active = self.resolve_provider(None)
        return [
            {"provider": name, "active": name == active}
            for name in sorted(self._providers.keys())
        ]

    def dispatch_job(
        self,
        *,
        tenant_id: str,
        project_id: str,
        job_type: str,
        payload: dict,
        provider: Optional[str] = None,
    ) -> dict:
        provider_name = self.resolve_provider(provider)
        adapter = self._providers[provider_name]
        result = adapter.dispatch_job(
            job_type=job_type,
            payload=payload,
            tenant_id=tenant_id,
            project_id=project_id,
        )
        now = datetime.now(timezone.utc).isoformat()
        entry = {
            **result,
            "updated_at": now,
        }
        self._job_registry[result["job_id"]] = entry
        return entry

    def get_job_status(
        self,
        job_id: str,
        *,
        tenant_id: str | None = None,
        project_id: str | None = None,
    ) -> dict:
        if job_id in self._job_registry:
            entry = dict(self._job_registry[job_id])
            if tenant_id and entry.get("tenant_id") != tenant_id:
                raise JobScopeMismatchError("tenant scope mismatch")
            if project_id and entry.get("project_id") != project_id:
                raise JobScopeMismatchError("project scope mismatch")
            provider = str(entry.get("provider", "agent0"))
            adapter = self._providers.get(provider)
            if adapter is not None:
                probe = adapter.get_job_status(job_id)
                entry.update(
                    {
                        "status": probe.get("status", entry.get("status", "unknown")),
                        "message": probe.get("message"),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                self._job_registry[job_id] = entry
            return entry

        inferred_provider = "agent0"
        if job_id.startswith("taskiq-"):
            inferred_provider = "taskiq"
        elif job_id.startswith("temporal-"):
            inferred_provider = "temporal"

        adapter = self._providers[inferred_provider]
        probe = adapter.get_job_status(job_id)
        return {
            "provider": inferred_provider,
            "job_id": job_id,
            "status": probe.get("status", "unknown"),
            "tenant_id": tenant_id,
            "project_id": project_id,
            "message": probe.get("message", "Job not found in runtime registry."),
        }

    def cancel_job(
        self,
        job_id: str,
        *,
        tenant_id: str | None = None,
        project_id: str | None = None,
    ) -> dict:
        if job_id in self._job_registry:
            entry = self._job_registry[job_id]
            if tenant_id and entry.get("tenant_id") != tenant_id:
                raise JobScopeMismatchError("tenant scope mismatch")
            if project_id and entry.get("project_id") != project_id:
                raise JobScopeMismatchError("project scope mismatch")
            provider = str(entry.get("provider", "agent0"))
            adapter = self._providers[provider]
            result = adapter.cancel_job(job_id)
            entry.update(
                {
                    "status": result.get("status", "cancel_requested"),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            self._job_registry[job_id] = entry
            return entry

        status = self.get_job_status(
            job_id,
            tenant_id=tenant_id,
            project_id=project_id,
        )
        return {
            **status,
            "status": "cancel_requested",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
