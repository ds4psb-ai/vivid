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
from app.features.original_ip_foundry.contracts import (
    FoundryC2PAExportRequest,
    FoundryC2PAExportResponse,
    FoundryCompiledShot,
    FoundryEnginePromptResult,
    FoundryExperimentAssignRequest,
    FoundryExperimentAssignResponse,
    FoundryExperimentFeedbackRequest,
    FoundryMemoryNormalizeRequest,
    FoundryPatternExtractionRequest,
    FoundryPatternExtractionResponse,
    FoundryPromptCompileRequest,
    FoundryPromptCompileResponse,
    FoundryRecommendationRequest,
    FoundryRecommendationResponse,
    FoundryRetrievalRequest,
    FoundryWorkerDispatchRequest,
    FoundryWorkerDispatchResponse,
    FoundryWorkerStatusResponse,
    FoundryRightsEvaluationRequest,
    FoundryRightsEvaluationResponse,
)
from app.features.original_ip_foundry.foundry_auth import (
    foundry_write_guard,
    require_foundry_access,
)
from app.features.original_ip_foundry.foundry_lifespan import FoundryServices, get_foundry_services
from app.features.original_ip_foundry.webhook_signature import WebhookSignatureError
from app.features.original_ip_foundry.channel_router import WebhookRateLimitError
from app.features.original_ip_foundry.worker_runtime import JobScopeMismatchError


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


router = APIRouter(
    route_class=FoundryAuditRoute,
    dependencies=[
        Depends(require_foundry_access),
        Depends(foundry_write_guard),
    ],
)


# ---------------------------------------------------------------------------
# Channel sub-routes (webhook, reply, upload, monitoring)
# These are defined inline because the ChannelWebhookRouter instance comes
# from the DI container (FoundryServices) via app.state, not from a module
# global.  We create lightweight route functions that pull the services at
# request time.
# ---------------------------------------------------------------------------

@router.post("/channels/{channel}/webhook")
async def channel_webhook(
    channel: str,
    payload: dict,
    request: Request,
    svc: FoundryServices = Depends(get_foundry_services),
) -> dict[str, Any]:
    headers = {k.lower(): v for k, v in request.headers.items()}
    try:
        return await svc.channel_webhook_router.handle_webhook(channel, payload, headers=headers)
    except WebhookSignatureError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except WebhookRateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/channels/monitoring")
async def channel_monitoring(
    svc: FoundryServices = Depends(get_foundry_services),
) -> dict[str, Any]:
    return svc.channel_webhook_router.get_monitoring()


@router.post("/channels/{channel}/reply")
async def channel_reply(
    channel: str,
    payload: dict,
    svc: FoundryServices = Depends(get_foundry_services),
) -> dict[str, Any]:
    user_id = payload.get("user_id") or ""
    text = payload.get("text") or ""
    attachments = payload.get("attachments") or []
    if not user_id or not text:
        raise HTTPException(status_code=400, detail="user_id and text required")
    try:
        return await svc.channel_webhook_router.handle_reply(channel, user_id, text, attachments)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/channels/{channel}/upload")
async def channel_upload(
    channel: str,
    payload: dict,
    svc: FoundryServices = Depends(get_foundry_services),
) -> dict[str, Any]:
    user_id = payload.get("user_id") or ""
    media_url = payload.get("media_url") or ""
    if not user_id or not media_url:
        raise HTTPException(status_code=400, detail="user_id and media_url required")
    try:
        return await svc.channel_webhook_router.handle_upload(
            channel, user_id, media_url,
            media_type=payload.get("media_type") or "image",
            caption=payload.get("caption") or "",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Core Foundry endpoints
# ---------------------------------------------------------------------------

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
    svc: FoundryServices = Depends(get_foundry_services),
) -> FoundryRightsEvaluationResponse:
    result = await svc.rights_service.evaluate_assets(
        action=payload.action,
        assets=[asset.model_dump() for asset in payload.assets],
        requested_elements=payload.requested_elements,
        evidence_refs=payload.evidence_refs,
        db=db,
        project_id="unknown",
    )
    return FoundryRightsEvaluationResponse(**result)


@router.post("/patterns/extract", response_model=FoundryPatternExtractionResponse)
async def extract_patterns(
    payload: FoundryPatternExtractionRequest,
    svc: FoundryServices = Depends(get_foundry_services),
) -> FoundryPatternExtractionResponse:
    result = svc.pattern_service.extract(
        project_id=payload.project_id,
        scene_id=payload.scene_id,
        shots=[shot.model_dump() for shot in payload.shots],
    )
    return FoundryPatternExtractionResponse(**result)


@router.post("/recommendations/next-scene", response_model=FoundryRecommendationResponse)
async def recommend_next_scene(
    payload: FoundryRecommendationRequest,
    svc: FoundryServices = Depends(get_foundry_services),
) -> FoundryRecommendationResponse:
    result = await svc.recommendation_service.recommend(
        scene_context=payload.scene_context.model_dump(),
        candidates=[candidate.model_dump() for candidate in payload.candidates],
        rights_action=payload.rights_action,
        continuity_floor=payload.continuity_floor,
    )
    return FoundryRecommendationResponse(**result)


@router.post("/experiments/assign", response_model=FoundryExperimentAssignResponse)
async def assign_experiment(
    payload: FoundryExperimentAssignRequest,
    svc: FoundryServices = Depends(get_foundry_services),
) -> FoundryExperimentAssignResponse:
    result = svc.experiment_service.assign(
        tenant_id=payload.tenant_id,
        experiment_key=payload.experiment_key,
        user_key=payload.user_key,
        scene_id=payload.scene_id,
        variants=payload.variants,
    )
    return FoundryExperimentAssignResponse(**result)


@router.post("/experiments/feedback")
async def record_experiment_feedback(
    payload: FoundryExperimentFeedbackRequest,
    svc: FoundryServices = Depends(get_foundry_services),
) -> dict[str, Any]:
    return await svc.experiment_service.record_feedback(
        tenant_id=payload.tenant_id,
        experiment_key=payload.experiment_key,
        user_key=payload.user_key,
        variant=payload.variant,
        outcome=payload.outcome,
        completion_seconds=payload.completion_seconds,
        edit_distance=payload.edit_distance or 0.0,
        satisfaction_score=payload.satisfaction_score,
    )


@router.get("/experiments/{experiment_key}/summary")
async def experiment_summary(
    experiment_key: str,
    tenant_id: str = "default",
    svc: FoundryServices = Depends(get_foundry_services),
) -> dict[str, Any]:
    return svc.experiment_service.summary(tenant_id=tenant_id, experiment_key=experiment_key)


@router.post("/memory/normalize")
async def normalize_memory(
    payload: FoundryMemoryNormalizeRequest,
    svc: FoundryServices = Depends(get_foundry_services),
) -> dict[str, Any]:
    normalized = svc.memory_adapter.normalize(
        tenant_id=payload.tenant_id,
        project_id=payload.project_id,
        scene_id=payload.scene_id,
        source_channel=payload.source_channel,
        note=payload.note,
        attachments=payload.attachments,
    )
    svc.memory_store.put(normalized)
    return {"normalized": normalized.to_dict()}


@router.post("/retrieval/query")
async def retrieval_query(
    payload: FoundryRetrievalRequest,
    svc: FoundryServices = Depends(get_foundry_services),
) -> dict[str, Any]:
    supported = {"director_context", "shot_reference", "payload_filter", "transition_rerank"}
    if payload.query_type not in supported:
        raise HTTPException(status_code=400, detail="Unsupported query_type")
    return svc.retrieval_service.query(
        tenant_id=payload.tenant_id,
        project_id=payload.project_id,
        query_type=payload.query_type,
        query=payload.query,
        limit=payload.limit,
        filters=payload.filters,
    )


@router.post("/provenance/export-c2pa", response_model=FoundryC2PAExportResponse)
async def export_c2pa_manifest(
    payload: FoundryC2PAExportRequest,
    svc: FoundryServices = Depends(get_foundry_services),
) -> FoundryC2PAExportResponse:
    result = svc.c2pa_export_service.export_manifest(
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
async def get_worker_providers(
    svc: FoundryServices = Depends(get_foundry_services),
) -> dict[str, Any]:
    return {
        "active_provider": svc.worker_runtime.resolve_provider(None),
        "providers": svc.worker_runtime.list_providers(),
    }


@router.post("/workers/dispatch", response_model=FoundryWorkerDispatchResponse)
async def dispatch_worker_job(
    payload: FoundryWorkerDispatchRequest,
    svc: FoundryServices = Depends(get_foundry_services),
) -> FoundryWorkerDispatchResponse:
    result = svc.worker_runtime.dispatch_job(
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
    svc: FoundryServices = Depends(get_foundry_services),
) -> FoundryWorkerStatusResponse:
    try:
        status = svc.worker_runtime.get_job_status(
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
    svc: FoundryServices = Depends(get_foundry_services),
) -> FoundryWorkerStatusResponse:
    try:
        status = svc.worker_runtime.cancel_job(
            job_id,
            tenant_id=tenant_id,
            project_id=project_id,
        )
    except JobScopeMismatchError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return FoundryWorkerStatusResponse(**status)


@router.post("/prompts/compile", response_model=FoundryPromptCompileResponse)
async def compile_prompts(
    payload: FoundryPromptCompileRequest,
    svc: FoundryServices = Depends(get_foundry_services),
) -> FoundryPromptCompileResponse:
    started = perf_counter()
    try:
        compiled = svc.prompt_compiler.compile_scene(
            [shot.model_dump() for shot in payload.shots],
            engines=payload.engines,
        )
        compiled_shots = []
        for shot_input, engine_results in zip(payload.shots, compiled):
            engines_out = {
                engine: FoundryEnginePromptResult(
                    engine=result.engine,
                    prompt_text=result.prompt_text,
                    negative_prompt=result.negative_prompt,
                    metadata=result.metadata,
                )
                for engine, result in engine_results.items()
            }
            compiled_shots.append(FoundryCompiledShot(shot_id=shot_input.shot_id, engines=engines_out))
        return FoundryPromptCompileResponse(
            project_id=payload.project_id,
            scene_id=payload.scene_id,
            compiled_shots=compiled_shots,
        )
    finally:
        latency_ms = (perf_counter() - started) * 1000
        svc.kpi_service.record_latency(latency_ms)


@router.post("/rights/evaluate-publish")
async def evaluate_publish_readiness(
    payload: dict,
    svc: FoundryServices = Depends(get_foundry_services),
) -> dict[str, Any]:
    return await svc.rights_service.evaluate_publish_readiness(
        project_id=payload.get("project_id", "unknown"),
        scene_id=payload.get("scene_id"),
        shots=payload.get("shots"),
        clone_risk=payload.get("clone_risk"),
        ingredients=payload.get("ingredients"),
        near_duplicate_service=svc.near_duplicate_service,
        clone_risk_service=svc.clone_risk_service,
    )


@router.get("/kpi/snapshot")
async def get_kpi_snapshot(
    svc: FoundryServices = Depends(get_foundry_services),
) -> dict[str, Any]:
    return svc.kpi_service.get_kpi_snapshot()


@router.post("/ops/vendor-switch-drill")
async def run_vendor_switch_drill(
    svc: FoundryServices = Depends(get_foundry_services),
) -> dict[str, Any]:
    from app.features.original_ip_foundry.vendor_switch_drill import VendorSwitchDrill

    drill = VendorSwitchDrill(services=svc)
    return await drill.run_full_drill()
