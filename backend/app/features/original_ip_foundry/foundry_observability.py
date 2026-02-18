"""Foundry observability — Langfuse only, NO OTEL."""
from __future__ import annotations

import json
import sys
from typing import Optional

from app.rag.observability import get_langfuse


def trace_foundry_event(
    *,
    name: str,
    latency_ms: float,
    status_code: int,
    tags: list[str] | None = None,
    metadata: dict | None = None,
) -> None:
    """Emit a Foundry trace to Langfuse + structured stdout JSON."""
    langfuse = get_langfuse()
    if langfuse:
        langfuse.trace(
            name=f"foundry.{name}",
            tags=tags or [],
            metadata={
                "latency_ms": latency_ms,
                "status_code": status_code,
                **(metadata or {}),
            },
        )
    # Always emit structured JSON to stdout for Railway log aggregation
    print(
        json.dumps(
            {
                "event": f"foundry.{name}",
                "latency_ms": latency_ms,
                "status_code": status_code,
                **(metadata or {}),
            }
        ),
        flush=True,
    )
