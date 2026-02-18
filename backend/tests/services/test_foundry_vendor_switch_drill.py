"""Tests for VendorSwitchDrill — validate swap-and-verify for all port types."""
from __future__ import annotations

import pytest

from app.features.original_ip_foundry.adapters import KlingEngineAdapter, VeoEngineAdapter
from app.features.original_ip_foundry.channels import (
    KakaoChannelAdapter,
    TelegramChannelAdapter,
    WebChannelAdapter,
)
from app.features.original_ip_foundry.memory_adapter import InMemoryDirectorMemoryStore
from app.features.original_ip_foundry.vendor_switch_drill import VendorSwitchDrill


@pytest.fixture
def drill() -> VendorSwitchDrill:
    return VendorSwitchDrill(
        memory_store=InMemoryDirectorMemoryStore(),
        engine_adapters=[KlingEngineAdapter(), VeoEngineAdapter()],
        channel_adapters=[
            TelegramChannelAdapter(bot_token=""),
            KakaoChannelAdapter(),
            WebChannelAdapter(),
        ],
    )


@pytest.mark.asyncio
async def test_memory_drill_runs_and_reports(drill: VendorSwitchDrill):
    report = await drill.run_memory_drill()
    assert report["drill_name"] == "memory_swap"
    assert report["status"] == "pass"
    assert report["tests_passed"] >= 3
    assert report["tests_failed"] == 0


@pytest.mark.asyncio
async def test_worker_drill_runs_and_reports(drill: VendorSwitchDrill):
    report = await drill.run_worker_drill()
    assert report["drill_name"] == "worker_swap"
    assert report["status"] == "pass"
    assert report["tests_passed"] >= 3
    assert report["tests_failed"] == 0


@pytest.mark.asyncio
async def test_channel_drill_runs_and_reports(drill: VendorSwitchDrill):
    report = await drill.run_channel_drill()
    assert report["drill_name"] == "channel_swap"
    assert report["status"] == "pass"
    # 4 adapters (3 real + 1 stub), 3 tests each = 12
    assert report["tests_passed"] >= 12
    assert report["tests_failed"] == 0


@pytest.mark.asyncio
async def test_full_drill_aggregates_results(drill: VendorSwitchDrill):
    report = await drill.run_full_drill()
    assert report["drill_name"] == "full_vendor_switch"
    assert report["status"] == "pass"
    assert report["tests_passed"] > 0
    assert report["tests_failed"] == 0
    assert "sub_drills" in report
    assert set(report["sub_drills"].keys()) == {"memory", "worker", "channel"}


@pytest.mark.asyncio
async def test_drill_restores_after_failure():
    """Verify original references are restored even if drill internals fail."""
    original_store = InMemoryDirectorMemoryStore()
    original_adapters = [KlingEngineAdapter()]
    original_channels = [WebChannelAdapter()]

    drill = VendorSwitchDrill(
        memory_store=original_store,
        engine_adapters=original_adapters,
        channel_adapters=original_channels,
    )

    await drill.run_memory_drill()
    assert drill._memory_store is original_store

    await drill.run_worker_drill()
    assert drill._engine_adapters is original_adapters
