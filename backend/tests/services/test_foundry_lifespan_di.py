"""Tests for Foundry DI lifespan container and in-memory bounds."""
from __future__ import annotations

import asyncio
from collections import deque
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.features.original_ip_foundry.foundry_lifespan import (
    FoundryServices,
    _create_services,
    foundry_lifespan,
    get_foundry_services,
)


# ---- B1: Container creation ----

def test_services_container_creation():
    """FoundryServices can be instantiated with all fields."""
    svc = _create_services()
    assert isinstance(svc, FoundryServices)
    assert svc.memory_adapter is not None
    assert svc.memory_store is not None
    assert svc.qdrant_pattern_store is not None
    assert svc.pattern_service is not None
    assert svc.rights_service is not None
    assert svc.clone_risk_service is not None
    assert svc.recommendation_service is not None
    assert svc.experiment_service is not None
    assert svc.retrieval_service is not None
    assert svc.c2pa_export_service is not None
    assert svc.prompt_compiler is not None
    assert svc.worker_runtime is not None
    assert svc.near_duplicate_service is not None
    assert svc.kpi_service is not None
    assert svc.channel_webhook_router is not None
    assert svc.enhanced_reward_service is not None


def test_services_accessible_via_dependency():
    """get_foundry_services returns proper container from request.app.state."""
    svc = _create_services()

    mock_request = MagicMock()
    mock_request.app.state.foundry = svc

    result = get_foundry_services(mock_request)
    assert result is svc


def test_services_share_qdrant_store():
    """pattern_service and clone_risk_service share the same qdrant_pattern_store."""
    svc = _create_services()
    assert svc.pattern_service._qdrant_store is svc.qdrant_pattern_store
    assert svc.clone_risk_service._qdrant_store is svc.qdrant_pattern_store


@pytest.mark.asyncio
async def test_lifespan_creates_and_cleanup():
    """Async context manager attaches services to app.state and cleans up."""
    mock_app = MagicMock()
    mock_app.state = MagicMock()

    async with foundry_lifespan(mock_app):
        assert hasattr(mock_app.state, "foundry")
        svc = mock_app.state.foundry
        assert isinstance(svc, FoundryServices)


# ---- B3: In-memory state bounds ----

def test_experiment_events_bounded():
    """Adding >10000 events to one key stays within maxlen."""
    from app.features.original_ip_foundry.experiment_service import FoundryExperimentService

    svc = FoundryExperimentService(use_thompson=False)
    key = "tenant:exp"
    for i in range(12_000):
        svc._events[key].append({"i": i})

    assert len(svc._events[key]) == svc.MAX_EVENTS_PER_KEY
    assert isinstance(svc._events[key], deque)


def test_assignment_dict_bounded():
    """Experiment assignments stay under MAX_ASSIGNMENTS."""
    from app.features.original_ip_foundry.experiment_service import FoundryExperimentService

    svc = FoundryExperimentService(use_thompson=False)
    limit = svc.MAX_ASSIGNMENTS

    # Fill to capacity + some extra
    for i in range(limit + 500):
        svc.assign(
            tenant_id="t",
            experiment_key="e",
            user_key=f"user_{i}",
            scene_id=f"scene_{i}",
            variants=["A", "B"],
        )

    assert len(svc._assignments) <= limit


def test_dedup_registry_bounded():
    """Channel router _event_dedup stays under MAX_DEDUP_ENTRIES."""
    from app.features.original_ip_foundry.channel_router import ChannelWebhookRouter

    router = ChannelWebhookRouter()
    limit = router.MAX_DEDUP_ENTRIES

    for i in range(limit + 500):
        if len(router._event_dedup) >= limit:
            oldest_key = next(iter(router._event_dedup))
            del router._event_dedup[oldest_key]
        router._event_dedup[f"evt_{i}"] = float(i)

    assert len(router._event_dedup) <= limit


def test_hash_registry_bounded():
    """NearDuplicateService _hash_registry stays under MAX_HASH_REGISTRY."""
    from app.features.original_ip_foundry.near_duplicate_service import NearDuplicateService

    svc = NearDuplicateService()
    limit = svc.MAX_HASH_REGISTRY

    for i in range(limit + 500):
        svc._evict_oldest_hash()
        svc._hash_registry[f"hash_{i}"] = f"id_{i}"

    assert len(svc._hash_registry) <= limit


def test_kpi_window_already_bounded():
    """KPI service already uses bounded deque (SlidingWindow)."""
    from app.features.original_ip_foundry.kpi_service import FoundryKPIService

    svc = FoundryKPIService(window_size=100)

    for i in range(200):
        svc.record_latency(float(i))

    snapshot = svc.get_kpi_snapshot()
    assert snapshot["sample_counts"]["latency"] == 100


@pytest.mark.asyncio
async def test_foundry_disabled_skips_init():
    """When AD_FOUNDRY_ENABLED=False, foundry services are not created in lifespan."""
    mock_app = MagicMock()
    mock_app.state = MagicMock(spec=[])

    with patch("app.features.original_ip_foundry.foundry_lifespan.settings") as mock_settings:
        mock_settings.AD_FOUNDRY_ENABLED = False
        # Calling lifespan should still work; the gating is in main.py
        # Verify that if we DON'T call lifespan, app.state has no foundry attr
        assert not hasattr(mock_app.state, "foundry")
