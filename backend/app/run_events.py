"""In-memory run event hub for SSE/WS streaming."""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class RunEvent:
    event_id: str
    run_id: str
    type: str
    seq: int
    ts: str
    payload: Dict[str, Any]


class RunEventHub:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[asyncio.Queue[RunEvent]]] = {}
        self._seq: Dict[str, int] = {}
        self._lock = asyncio.Lock()
        self._cancelled: set[str] = set()

    async def publish(self, run_id: str, event_type: str, payload: Dict[str, Any]) -> RunEvent:
        async with self._lock:
            seq = self._seq.get(run_id, 0) + 1
            self._seq[run_id] = seq
            event = RunEvent(
                event_id=f"{run_id}:{seq}",
                run_id=run_id,
                type=event_type,
                seq=seq,
                ts=f"{datetime.utcnow().isoformat()}Z",
                payload=payload,
            )
            queues = list(self._subscribers.get(run_id, []))

        for queue in queues:
            await queue.put(event)
        return event

    def subscribe(self, run_id: str) -> asyncio.Queue[RunEvent]:
        queue: asyncio.Queue[RunEvent] = asyncio.Queue()
        self._subscribers.setdefault(run_id, []).append(queue)
        return queue

    def unsubscribe(self, run_id: str, queue: asyncio.Queue[RunEvent]) -> None:
        queues = self._subscribers.get(run_id)
        if not queues:
            return
        if queue in queues:
            queues.remove(queue)
        if not queues:
            self._subscribers.pop(run_id, None)
            self._seq.pop(run_id, None)

    def cancel(self, run_id: str) -> None:
        self._cancelled.add(run_id)

    def is_cancelled(self, run_id: str) -> bool:
        return run_id in self._cancelled

    def clear_cancelled(self, run_id: str) -> None:
        self._cancelled.discard(run_id)


run_event_hub = RunEventHub()
