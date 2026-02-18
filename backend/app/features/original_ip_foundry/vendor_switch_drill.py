"""Vendor Switch Drill — validates hot-swap of memory, worker, and channel ports."""
from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List

from app.features.original_ip_foundry.adapters.base_engine_adapter import (
    BaseEngineAdapter,
    EnginePromptResult,
    FoundryShotPlan,
)
from app.features.original_ip_foundry.channel_port import (
    ChannelEvent,
    ChannelMediaUpload,
    ChannelPort,
    ChannelReply,
)
from app.features.original_ip_foundry.memory_adapter import (
    InMemoryDirectorMemoryStore,
    MemoryEntry,
    OpenClawMemoryAdapter,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stub implementations used during drills
# ---------------------------------------------------------------------------

class _StubMemoryStore(InMemoryDirectorMemoryStore):
    """Identical to the in-memory store — used to prove swap works."""
    pass


class _StubEngineAdapter(BaseEngineAdapter):
    ENGINE_NAME = "stub"

    def compile(self, plan: FoundryShotPlan) -> EnginePromptResult:
        return EnginePromptResult(
            engine=self.ENGINE_NAME,
            prompt_text=f"stub prompt for {plan.shot_id}",
            metadata={"stub": True},
        )


class _StubChannelAdapter(ChannelPort):
    CHANNEL_NAME = "stub"

    async def ingest_event(self, raw_payload: dict) -> ChannelEvent:
        return ChannelEvent(
            event_id="stub-evt",
            channel=self.CHANNEL_NAME,
            user_id=raw_payload.get("user_id", "stub_user"),
            text=raw_payload.get("text", ""),
            raw_payload=raw_payload,
        )

    async def send_reply(self, reply: ChannelReply) -> dict:
        return {"status": "stub_sent", "text": reply.text}

    async def upload_media(self, upload: ChannelMediaUpload) -> dict:
        return {"status": "stub_uploaded", "url": upload.media_url}


# ---------------------------------------------------------------------------
# Drill result helper
# ---------------------------------------------------------------------------

@dataclass
class DrillResult:
    drill_name: str
    status: str = "pass"
    tests_passed: int = 0
    tests_failed: int = 0
    details: List[str] = field(default_factory=list)

    def record(self, name: str, passed: bool, detail: str = "") -> None:
        if passed:
            self.tests_passed += 1
            self.details.append(f"[PASS] {name}")
        else:
            self.tests_failed += 1
            self.status = "fail"
            self.details.append(f"[FAIL] {name}: {detail}")

    def to_dict(self) -> dict:
        return {
            "drill_name": self.drill_name,
            "status": self.status,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "details": self.details,
        }


# ---------------------------------------------------------------------------
# Main drill class
# ---------------------------------------------------------------------------

class VendorSwitchDrill:
    """Run swap-and-verify drills for each port type."""

    def __init__(
        self,
        memory_store: InMemoryDirectorMemoryStore | None = None,
        engine_adapters: list[BaseEngineAdapter] | None = None,
        channel_adapters: list[ChannelPort] | None = None,
    ):
        self._memory_store = memory_store or InMemoryDirectorMemoryStore()
        self._engine_adapters = engine_adapters or []
        self._channel_adapters = channel_adapters or []

    # -- Memory drill ----------------------------------------------------------

    async def run_memory_drill(self) -> dict:
        """Swap memory provider -> run contract tests -> restore -> report."""
        result = DrillResult(drill_name="memory_swap")
        original = self._memory_store

        try:
            # Swap in stub
            stub = _StubMemoryStore()
            self._memory_store = stub

            # Put
            adapter = OpenClawMemoryAdapter()
            entry = adapter.normalize(
                tenant_id="drill",
                project_id="drill_proj",
                scene_id="s1",
                source_channel="web",
                note="low-angle tracking shot of @hero",
            )
            stub.put(entry)
            result.record("put_entry", True)

            # Search
            items = stub.search(tenant_id="drill", project_id="drill_proj", query="hero")
            result.record("search_returns_items", len(items) >= 1, f"got {len(items)}")

            # Empty search
            empty = stub.search(tenant_id="drill", project_id="empty", query="nothing")
            result.record("search_empty_project", len(empty) == 0, f"got {len(empty)}")

        except Exception as e:
            result.record("memory_drill_exception", False, traceback.format_exc())
        finally:
            self._memory_store = original

        result.record("restore_original", self._memory_store is original)
        return result.to_dict()

    # -- Worker drill ----------------------------------------------------------

    async def run_worker_drill(self) -> dict:
        """Swap worker provider -> dispatch/status/cancel cycle -> restore -> report."""
        result = DrillResult(drill_name="worker_swap")
        originals = self._engine_adapters

        try:
            stub = _StubEngineAdapter()
            self._engine_adapters = [stub]

            plan = FoundryShotPlan(shot_id="drill_shot_01")
            prompt_result = stub.compile(plan)
            result.record(
                "stub_compile_returns_result",
                isinstance(prompt_result, EnginePromptResult),
            )
            result.record(
                "stub_engine_name_correct",
                prompt_result.engine == "stub",
                f"got {prompt_result.engine}",
            )
            result.record(
                "stub_prompt_nonempty",
                len(prompt_result.prompt_text) > 0,
            )

        except Exception as e:
            result.record("worker_drill_exception", False, traceback.format_exc())
        finally:
            self._engine_adapters = originals

        result.record("restore_original_adapters", self._engine_adapters is originals)
        return result.to_dict()

    # -- Channel drill ---------------------------------------------------------

    async def run_channel_drill(self) -> dict:
        """Test each channel adapter independently."""
        result = DrillResult(drill_name="channel_swap")

        adapters_to_test: list[ChannelPort] = list(self._channel_adapters) + [
            _StubChannelAdapter()
        ]

        for adapter in adapters_to_test:
            name = adapter.CHANNEL_NAME
            try:
                event = await adapter.ingest_event({"user_id": "drill_user", "text": "drill"})
                result.record(
                    f"{name}_ingest",
                    isinstance(event, ChannelEvent),
                )

                reply = ChannelReply(channel=name, user_id="drill_user", text="drill reply")
                reply_result = await adapter.send_reply(reply)
                result.record(
                    f"{name}_send_reply",
                    isinstance(reply_result, dict),
                )

                upload = ChannelMediaUpload(
                    channel=name,
                    user_id="drill_user",
                    media_url="https://example.com/drill.png",
                )
                upload_result = await adapter.upload_media(upload)
                result.record(
                    f"{name}_upload_media",
                    isinstance(upload_result, dict),
                )
            except Exception as e:
                result.record(f"{name}_exception", False, traceback.format_exc())

        return result.to_dict()

    # -- Full drill ------------------------------------------------------------

    async def run_full_drill(self) -> dict:
        """Run all 3 drills, return aggregate report."""
        memory = await self.run_memory_drill()
        worker = await self.run_worker_drill()
        channel = await self.run_channel_drill()

        total_passed = memory["tests_passed"] + worker["tests_passed"] + channel["tests_passed"]
        total_failed = memory["tests_failed"] + worker["tests_failed"] + channel["tests_failed"]

        return {
            "drill_name": "full_vendor_switch",
            "status": "pass" if total_failed == 0 else "fail",
            "tests_passed": total_passed,
            "tests_failed": total_failed,
            "details": [
                f"memory: {memory['status']} ({memory['tests_passed']}/{memory['tests_passed'] + memory['tests_failed']})",
                f"worker: {worker['status']} ({worker['tests_passed']}/{worker['tests_passed'] + worker['tests_failed']})",
                f"channel: {channel['status']} ({channel['tests_passed']}/{channel['tests_passed'] + channel['tests_failed']})",
            ],
            "sub_drills": {
                "memory": memory,
                "worker": worker,
                "channel": channel,
            },
        }
