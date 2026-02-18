"""Foundry DI container and lifespan management."""
from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI, Request

from app.config import settings


@dataclass
class FoundryServices:
    """Container for all Foundry service singletons."""

    memory_adapter: "OpenClawMemoryAdapter"
    memory_store: "QdrantDirectorMemoryStore"
    qdrant_pattern_store: "QdrantPatternAtomStore"
    pattern_service: "PatternExtractionService"
    rights_service: "FoundryRightsService"
    clone_risk_service: "CloneRiskService"
    recommendation_service: "FoundryRecommendationService"
    experiment_service: "FoundryExperimentService"
    retrieval_service: "FoundryRetrievalService"
    c2pa_export_service: "FoundryC2PAExportService"
    prompt_compiler: "FoundryPromptCompiler"
    worker_runtime: "FoundryWorkerRuntime"
    near_duplicate_service: "NearDuplicateService"
    kpi_service: "FoundryKPIService"
    channel_webhook_router: "ChannelWebhookRouter"
    enhanced_reward_service: "EnhancedRewardService"


def _create_services() -> FoundryServices:
    """Instantiate all Foundry services with the same wiring as the old singletons."""
    from app.features.original_ip_foundry.c2pa_export_service import FoundryC2PAExportService
    from app.features.original_ip_foundry.channel_router import ChannelWebhookRouter
    from app.features.original_ip_foundry.clone_risk_service import CloneRiskService
    from app.features.original_ip_foundry.enhanced_reward_service import EnhancedRewardService
    from app.features.original_ip_foundry.experiment_service import FoundryExperimentService
    from app.features.original_ip_foundry.kpi_service import FoundryKPIService
    from app.features.original_ip_foundry.memory_adapter import OpenClawMemoryAdapter
    from app.features.original_ip_foundry.near_duplicate_service import NearDuplicateService
    from app.features.original_ip_foundry.pattern_extraction_service import PatternExtractionService
    from app.features.original_ip_foundry.prompt_compiler import FoundryPromptCompiler
    from app.features.original_ip_foundry.qdrant_memory_store import QdrantDirectorMemoryStore
    from app.features.original_ip_foundry.qdrant_pattern_store import QdrantPatternAtomStore
    from app.features.original_ip_foundry.recommendation_service import FoundryRecommendationService
    from app.features.original_ip_foundry.retrieval_service import FoundryRetrievalService
    from app.features.original_ip_foundry.rights_service import FoundryRightsService
    from app.features.original_ip_foundry.worker_runtime import FoundryWorkerRuntime

    memory_adapter = OpenClawMemoryAdapter()
    memory_store = QdrantDirectorMemoryStore()
    qdrant_pattern_store = QdrantPatternAtomStore()
    pattern_service = PatternExtractionService(qdrant_store=qdrant_pattern_store)
    rights_service = FoundryRightsService()
    clone_risk_service = CloneRiskService(qdrant_pattern_store=qdrant_pattern_store)
    recommendation_service = FoundryRecommendationService(
        rights_service, clone_risk_service=clone_risk_service,
    )
    experiment_service = FoundryExperimentService()
    retrieval_service = FoundryRetrievalService(memory_store, pattern_service)
    c2pa_export_service = FoundryC2PAExportService()
    prompt_compiler = FoundryPromptCompiler()
    worker_runtime = FoundryWorkerRuntime()
    near_duplicate_service = NearDuplicateService(qdrant_pattern_store=qdrant_pattern_store)
    kpi_service = FoundryKPIService()
    enhanced_reward_service = EnhancedRewardService()

    channel_webhook_router = ChannelWebhookRouter(
        memory_adapter=memory_adapter,
        memory_store=memory_store,
        rate_limit=settings.AD_FOUNDRY_WEBHOOK_RATE_LIMIT,
    )

    return FoundryServices(
        memory_adapter=memory_adapter,
        memory_store=memory_store,
        qdrant_pattern_store=qdrant_pattern_store,
        pattern_service=pattern_service,
        rights_service=rights_service,
        clone_risk_service=clone_risk_service,
        recommendation_service=recommendation_service,
        experiment_service=experiment_service,
        retrieval_service=retrieval_service,
        c2pa_export_service=c2pa_export_service,
        prompt_compiler=prompt_compiler,
        worker_runtime=worker_runtime,
        near_duplicate_service=near_duplicate_service,
        kpi_service=kpi_service,
        channel_webhook_router=channel_webhook_router,
        enhanced_reward_service=enhanced_reward_service,
    )


@asynccontextmanager
async def foundry_lifespan(app: FastAPI):
    """Initialize Foundry services and attach to app.state for DI."""
    services = _create_services()
    app.state.foundry = services
    yield
    # No explicit teardown needed; services are stateless or self-managing.


def get_foundry_services(request: Request) -> FoundryServices:
    """FastAPI dependency that retrieves the Foundry service container."""
    return request.app.state.foundry
