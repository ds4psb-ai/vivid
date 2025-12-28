"""WebSocket endpoints for run streaming."""
import asyncio
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import CapsuleRun, CapsuleSpec
from app.run_events import run_event_hub
from app.routers.capsules import (
    _apply_policy,
    _apply_pattern_version,
    _apply_source_id,
    _filter_evidence_refs,
    _merge_summary_warnings,
)

router = APIRouter()


async def _cancel_run(run_id: str, reason: str) -> None:
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(CapsuleRun).where(CapsuleRun.id == run_uuid))
        run = result.scalars().first()
        if not run or run.status in {"done", "failed", "cancelled"}:
            return
        run_event_hub.cancel(run_id)
        run.status = "cancelled"
        run.summary = {"message": reason}
        run.evidence_refs = []
        await session.commit()
        await run_event_hub.publish(
            run_id,
            "run.cancelled",
            {"status": "cancelled", "message": reason},
        )


@router.websocket("/runs/{run_id}")
async def run_stream(websocket: WebSocket, run_id: str) -> None:
    await websocket.accept()
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        await websocket.send_json(
            {
                "event_id": f"{run_id}:error",
                "run_id": run_id,
                "type": "run.failed",
                "seq": 0,
                "ts": "",
                "payload": {"status": "failed", "error": "Invalid run id"},
            }
        )
        await websocket.close()
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(CapsuleRun).where(CapsuleRun.id == run_uuid))
        run = result.scalars().first()
        if not run:
            await websocket.send_json(
                {
                    "event_id": f"{run_id}:error",
                    "run_id": run_id,
                    "type": "run.failed",
                    "seq": 0,
                    "ts": "",
                    "payload": {"status": "failed", "error": "Run not found"},
                }
            )
            await websocket.close()
            return

        if run.status in {"done", "failed", "cancelled"}:
            spec_result = await session.execute(
                select(CapsuleSpec).where(
                    CapsuleSpec.capsule_key == run.capsule_key,
                    CapsuleSpec.version == run.capsule_version,
                )
            )
            spec = spec_result.scalars().first()
            spec_payload = (spec.spec or {}) if spec else {}
            policy = spec_payload.get("policy", {})
            output_contracts = (
                spec_payload.get("outputContracts") or spec_payload.get("output_contracts") or {}
            )
            pattern_version = spec_payload.get("patternVersion") or spec_payload.get(
                "pattern_version"
            )
            filtered_refs, evidence_warnings = await _filter_evidence_refs(
                list(run.evidence_refs or []),
                session,
            )
            summary = _apply_pattern_version(run.summary, pattern_version)
            summary = _apply_source_id(summary, run.inputs or {})
            summary = _merge_summary_warnings(
                summary,
                evidence_warnings=evidence_warnings,
                output_contracts=output_contracts,
            )
            summary, evidence_refs = _apply_policy(summary, filtered_refs, policy, False)
            if run.status == "done":
                event_type = "run.completed"
            elif run.status == "failed":
                event_type = "run.failed"
            else:
                event_type = "run.cancelled"
            payload = {
                "status": run.status,
                "summary": summary,
                "evidence_refs": evidence_refs,
                "version": run.capsule_version,
                "token_usage": run.token_usage,
                "latency_ms": run.latency_ms,
                "cost_usd_est": run.cost_usd_est,
            }
            await websocket.send_json(
                {
                    "event_id": f"{run_id}:final",
                    "run_id": str(run.id),
                    "type": event_type,
                    "seq": 0,
                    "ts": "",
                    "payload": payload,
                }
            )
            await websocket.close()
            return

    queue = run_event_hub.subscribe(run_id, replay_last=True)
    try:
        queue_task = asyncio.create_task(queue.get())
        recv_task = asyncio.create_task(websocket.receive_json())
        while True:
            done, pending = await asyncio.wait(
                {queue_task, recv_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            if queue_task in done:
                event = queue_task.result()
                await websocket.send_json(
                    {
                        "event_id": event.event_id,
                        "run_id": event.run_id,
                        "type": event.type,
                        "seq": event.seq,
                        "ts": event.ts,
                        "payload": event.payload,
                    }
                )
                if event.type in {"run.completed", "run.failed", "run.cancelled"}:
                    break
                queue_task = asyncio.create_task(queue.get())

            if recv_task in done:
                message = recv_task.result()
                msg_type = message.get("type") if isinstance(message, dict) else None
                if msg_type == "cancel":
                    await _cancel_run(run_id, "Cancelled by client")
                recv_task = asyncio.create_task(websocket.receive_json())
    except WebSocketDisconnect:
        pass
    finally:
        for task in ("queue_task", "recv_task"):
            if task in locals() and not locals()[task].done():
                locals()[task].cancel()
        run_event_hub.unsubscribe(run_id, queue)
        await websocket.close()
