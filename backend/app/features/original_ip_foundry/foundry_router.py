"""Original-IP Foundry router with guardrails + continuity-first services."""
from __future__ import annotations

import json
import logging
from time import perf_counter
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.features.original_ip_foundry.c2pa_export_service import FoundryC2PAExportService
from app.features.original_ip_foundry.contracts import (
    FoundryC2PAExportRequest,
    FoundryC2PAExportResponse,
    FoundryExperimentAssignRequest,
    FoundryExperimentAssignResponse,
    FoundryExperimentFeedbackRequest,
    FoundryMemoryNormalizeRequest,
    FoundryPatternExtractionRequest,
    FoundryPatternExtractionResponse,
    FoundryRecommendationRequest,
    FoundryRecommendationResponse,
    FoundryRetrievalRequest,
    FoundryWorkerDispatchRequest,
    FoundryWorkerDispatchResponse,
    FoundryWorkerStatusResponse,
    FoundryRightsEvaluationRequest,
    FoundryRightsEvaluationResponse,
)
from app.features.original_ip_foundry.experiment_service import FoundryExperimentService
from app.features.original_ip_foundry.foundry_auth import (
    foundry_write_guard,
    require_foundry_access,
)
from app.features.original_ip_foundry.memory_adapter import OpenClawMemoryAdapter
from app.features.original_ip_foundry.qdrant_memory_store import QdrantDirectorMemoryStore
from app.features.original_ip_foundry.pattern_extraction_service import PatternExtractionService
from app.features.original_ip_foundry.recommendation_service import FoundryRecommendationService
from app.features.original_ip_foundry.retrieval_service import FoundryRetrievalService
from app.features.original_ip_foundry.rights_service import FoundryRightsService
from app.features.original_ip_foundry.worker_runtime import (
    FoundryWorkerRuntime,
    JobScopeMismatchError,
)


logger = logging.getLogger("foundry.audit")


def _extract_input_context(body: bytes) -> tuple[str, str]:
    if not body:
        return "unknown", "unknown"
    try:
        payload = json.loads(body)
    except Exception:
        return "unknown", "unknown"
    if not isinstance(payload, dict):
        return "unknown", "unknown"
    model = str(payload.get("model") or payload.get("engine") or "unknown")
    input_type = str(payload.get("input_type") or payload.get("source_channel") or "unknown")
    return model, input_type


class FoundryAuditRoute(APIRoute):
    """APIRoute wrapper that emits Foundry observability schema."""

    def get_route_handler(self):
        original_handler = super().get_route_handler()

        async def custom_handler(request: Request):
            started = perf_counter()
            model = "unknown"
            input_type = "unknown"
            failure_code: str | None = None
            block_reason: str | None = None
            status_code = 500

            try:
                if request.method in {"POST", "PUT", "PATCH"}:
                    body = await request.body()
                    model, input_type = _extract_input_context(body)
                response = await original_handler(request)
                status_code = response.status_code
                if status_code >= 400:
                    failure_code = f"HTTP_{status_code}"
                return response
            except HTTPException as exc:
                status_code = exc.status_code
                failure_code = f"HTTP_{exc.status_code}"
                block_reason = str(exc.detail)
                raise
            except Exception as exc:
                failure_code = "UNHANDLED_EXCEPTION"
                block_reason = type(exc).__name__
                raise
            finally:
                latency_ms = int((perf_counter() - started) * 1000)
                user = (
                    getattr(request.state, "foundry_email", None)
                    or request.headers.get("X-User-Id")
                    or "anonymous"
                )
                logger.info(
                    "foundry_request",
                    extra={
                        "extra": {
                            "type": "foundry_request",
                            "path": request.url.path,
                            "method": request.method,
                            "user": user,
                            "model": model,
                            "input_type": input_type,
                            "latency_ms": latency_ms,
                            "status_code": status_code,
                            "failure_code": failure_code,
                            "block_reason": block_reason,
                        }
                    },
                )

        return custom_handler


_memory_adapter = OpenClawMemoryAdapter()
_memory_store = QdrantDirectorMemoryStore()
_pattern_service = PatternExtractionService()
_rights_service = FoundryRightsService()
_recommendation_service = FoundryRecommendationService(_rights_service)
_experiment_service = FoundryExperimentService()
_retrieval_service = FoundryRetrievalService(_memory_store, _pattern_service)
_c2pa_export_service = FoundryC2PAExportService()
_worker_runtime = FoundryWorkerRuntime()


router = APIRouter(
    route_class=FoundryAuditRoute,
    dependencies=[
        Depends(require_foundry_access),
        Depends(foundry_write_guard),
    ],
)


@router.get("/health")
async def foundry_health() -> dict[str, Any]:
    return {
        "status": "ok",
        "foundry_enabled": settings.AD_FOUNDRY_ENABLED,
        "write_enabled": settings.AD_FOUNDRY_WRITE_ENABLED,
        "access_scope": settings.AD_FOUNDRY_ACCESS_SCOPE,
    }


@router.get("/status")
async def foundry_status() -> dict[str, Any]:
    return {
        "enabled": settings.AD_FOUNDRY_ENABLED,
        "write_enabled": settings.AD_FOUNDRY_WRITE_ENABLED,
        "access_scope": settings.AD_FOUNDRY_ACCESS_SCOPE,
        "worker_provider": settings.AD_FOUNDRY_WORKER_PROVIDER,
        "allowlist_count": len(settings.AD_FOUNDRY_ALLOWLIST_SET),
        "readonly_safe_path_count": len(settings.AD_FOUNDRY_READONLY_SAFE_PATHS_SET),
    }


@router.post("/rights/evaluate-assets", response_model=FoundryRightsEvaluationResponse)
async def evaluate_rights(
    payload: FoundryRightsEvaluationRequest,
    db: AsyncSession = Depends(get_db),
) -> FoundryRightsEvaluationResponse:
    result = await _rights_service.evaluate_assets(
        action=payload.action,
        assets=[asset.model_dump() for asset in payload.assets],
        requested_elements=payload.requested_elements,
        evidence_refs=payload.evidence_refs,
        db=db,
        project_id="unknown",
    )
    return FoundryRightsEvaluationResponse(**result)


@router.post("/patterns/extract", response_model=FoundryPatternExtractionResponse)
async def extract_patterns(payload: FoundryPatternExtractionRequest) -> FoundryPatternExtractionResponse:
    result = _pattern_service.extract(
        project_id=payload.project_id,
        scene_id=payload.scene_id,
        shots=[shot.model_dump() for shot in payload.shots],
    )
    return FoundryPatternExtractionResponse(**result)


@router.post("/recommendations/next-scene", response_model=FoundryRecommendationResponse)
async def recommend_next_scene(payload: FoundryRecommendationRequest) -> FoundryRecommendationResponse:
    result = await _recommendation_service.recommend(
        scene_context=payload.scene_context.model_dump(),
        candidates=[candidate.model_dump() for candidate in payload.candidates],
        rights_action=payload.rights_action,
        continuity_floor=payload.continuity_floor,
    )
    return FoundryRecommendationResponse(**result)


@router.post("/experiments/assign", response_model=FoundryExperimentAssignResponse)
async def assign_experiment(payload: FoundryExperimentAssignRequest) -> FoundryExperimentAssignResponse:
    result = _experiment_service.assign(
        tenant_id=payload.tenant_id,
        experiment_key=payload.experiment_key,
        user_key=payload.user_key,
        scene_id=payload.scene_id,
        variants=payload.variants,
    )
    return FoundryExperimentAssignResponse(**result)


@router.post("/experiments/feedback")
async def record_experiment_feedback(payload: FoundryExperimentFeedbackRequest) -> dict[str, Any]:
    return _experiment_service.record_feedback(
        tenant_id=payload.tenant_id,
        experiment_key=payload.experiment_key,
        user_key=payload.user_key,
        variant=payload.variant,
        outcome=payload.outcome,
        completion_seconds=payload.completion_seconds,
    )


@router.get("/experiments/{experiment_key}/summary")
async def experiment_summary(experiment_key: str, tenant_id: str = "default") -> dict[str, Any]:
    return _experiment_service.summary(tenant_id=tenant_id, experiment_key=experiment_key)


@router.post("/memory/normalize")
async def normalize_memory(payload: FoundryMemoryNormalizeRequest) -> dict[str, Any]:
    normalized = _memory_adapter.normalize(
        tenant_id=payload.tenant_id,
        project_id=payload.project_id,
        scene_id=payload.scene_id,
        source_channel=payload.source_channel,
        note=payload.note,
        attachments=payload.attachments,
    )
    _memory_store.put(normalized)
    return {"normalized": normalized.to_dict()}


@router.post("/retrieval/query")
async def retrieval_query(payload: FoundryRetrievalRequest) -> dict[str, Any]:
    if payload.query_type not in {"director_context", "shot_reference"}:
        raise HTTPException(status_code=400, detail="Unsupported query_type")
    return _retrieval_service.query(
        tenant_id=payload.tenant_id,
        project_id=payload.project_id,
        query_type=payload.query_type,
        query=payload.query,
        limit=payload.limit,
    )


@router.post("/provenance/export-c2pa", response_model=FoundryC2PAExportResponse)
async def export_c2pa_manifest(payload: FoundryC2PAExportRequest) -> FoundryC2PAExportResponse:
    result = _c2pa_export_service.export_manifest(
        project_id=payload.project_id,
        scene_id=payload.scene_id,
        asset_id=payload.asset_id,
        title=payload.title,
        generator_model=payload.generator_model,
        source_license=payload.source_license,
        actions=[item.model_dump() for item in payload.actions],
        provenance_trace=[item.model_dump() for item in payload.provenance_trace],
    )
    return FoundryC2PAExportResponse(**result)


@router.get("/workers/providers")
async def get_worker_providers() -> dict[str, Any]:
    return {
        "active_provider": _worker_runtime.resolve_provider(None),
        "providers": _worker_runtime.list_providers(),
    }


@router.post("/workers/dispatch", response_model=FoundryWorkerDispatchResponse)
async def dispatch_worker_job(payload: FoundryWorkerDispatchRequest) -> FoundryWorkerDispatchResponse:
    result = _worker_runtime.dispatch_job(
        tenant_id=payload.tenant_id,
        project_id=payload.project_id,
        job_type=payload.job_type,
        payload=payload.payload,
        provider=payload.provider,
    )
    return FoundryWorkerDispatchResponse(**result)


@router.get("/workers/jobs/{job_id}", response_model=FoundryWorkerStatusResponse)
async def get_worker_job_status(
    job_id: str,
    tenant_id: str,
    project_id: str,
) -> FoundryWorkerStatusResponse:
    try:
        status = _worker_runtime.get_job_status(
            job_id,
            tenant_id=tenant_id,
            project_id=project_id,
        )
    except JobScopeMismatchError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return FoundryWorkerStatusResponse(**status)


@router.post("/workers/jobs/{job_id}/cancel", response_model=FoundryWorkerStatusResponse)
async def cancel_worker_job(
    job_id: str,
    tenant_id: str,
    project_id: str,
) -> FoundryWorkerStatusResponse:
    try:
        status = _worker_runtime.cancel_job(
            job_id,
            tenant_id=tenant_id,
            project_id=project_id,
        )
    except JobScopeMismatchError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return FoundryWorkerStatusResponse(**status)
