"""WebSocket endpoints for run streaming."""
import asyncio
import uuid
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import CapsuleRun, CapsuleSpec
from app.run_events import run_event_hub
from app.routers.capsules import _filter_evidence_refs

router = APIRouter()


def _apply_policy(
    summary: Dict[str, Any],
    evidence_refs: List[str],
    policy: Dict[str, Any],
    is_admin: bool,
) -> Tuple[Dict[str, Any], List[str]]:
    if not policy:
        return summary, evidence_refs

    filtered = dict(summary or {})
    allow_raw_logs = bool(policy.get("allowRawLogs", False))
    if not is_admin or not allow_raw_logs:
        for key in ("raw_logs", "debug", "trace"):
            filtered.pop(key, None)

    evidence_policy = policy.get("evidence", "summary_only")
    if evidence_policy == "references_only":
        filtered = {
            "message": "references_only",
            "capsule_id": summary.get("capsule_id") if isinstance(summary, dict) else None,
            "version": summary.get("version") if isinstance(summary, dict) else None,
        }

    return filtered, evidence_refs


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
            policy = (spec.spec or {}).get("policy", {}) if spec else {}
            filtered_refs, _ = await _filter_evidence_refs(list(run.evidence_refs or []), session)
            summary, evidence_refs = _apply_policy(run.summary, filtered_refs, policy, False)
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

    queue = run_event_hub.subscribe(run_id)
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
