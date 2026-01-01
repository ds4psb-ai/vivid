#!/usr/bin/env python3
"""Simple SSE smoke test for /api/v1/agent/chat."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, Iterable, List, Optional

import httpx


def _parse_event_block(block: str) -> Optional[Dict[str, object]]:
    lines = block.splitlines()
    data_lines = []
    for line in lines:
        if line.startswith("data:"):
            data_lines.append(line[5:].strip())
    if not data_lines:
        return None
    payload = "\n".join(data_lines)
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def _iter_sse_events(chunks: Iterable[str]) -> Iterable[Dict[str, object]]:
    buffer = ""
    for chunk in chunks:
        buffer += chunk
        while "\n\n" in buffer:
            block, buffer = buffer.split("\n\n", 1)
            event = _parse_event_block(block)
            if event:
                yield event
    tail = buffer.strip()
    if tail:
        event = _parse_event_block(tail)
        if event:
            yield event


def _wait_for_health(
    base_url: str,
    health_path: str,
    retries: int,
    delay: float,
) -> bool:
    url = f"{base_url.rstrip('/')}{health_path}"
    for attempt in range(1, retries + 1):
        try:
            response = httpx.get(url, timeout=5.0)
            if response.status_code < 400:
                return True
        except httpx.HTTPError:
            pass
        print(f"Health check attempt {attempt}/{retries} failed, retrying...")
        if attempt < retries:
            try:
                import time

                time.sleep(delay)
            except KeyboardInterrupt:
                break
    return False


def run(
    base_url: str,
    message: str,
    session_id: Optional[str],
    model: Optional[str],
    user_id: Optional[str],
    admin_mode: Optional[str],
    max_events: int,
    require_tool: bool,
    require_artifact: bool,
    health_path: str,
    health_retries: int,
    health_delay: float,
    skip_health: bool,
) -> int:
    url = f"{base_url.rstrip('/')}/api/v1/agent/chat"
    payload: Dict[str, object] = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    if model:
        payload["model"] = model

    headers = {}
    if user_id:
        headers["X-User-Id"] = user_id
    if admin_mode:
        headers["X-Admin-Mode"] = admin_mode

    event_types: List[str] = []
    if not skip_health:
        ok = _wait_for_health(base_url, health_path, health_retries, health_delay)
        if not ok:
            print("Health check failed. Is the API server running?")
            return 1

    with httpx.Client(timeout=60.0, headers=headers) as client:
        with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            for event in _iter_sse_events(response.iter_text()):
                event_type = str(event.get("type"))
                event_types.append(event_type)
                if len(event_types) >= max_events:
                    break

    if not event_types:
        print("No SSE events received.")
        return 1

    print("Events:", event_types)
    if "agent.message" not in event_types:
        print("Missing agent.message event.")
        return 1
    if require_tool and "agent.tool_result" not in event_types:
        print("Missing agent.tool_result event.")
        return 1
    if require_artifact and "agent.artifact_update" not in event_types:
        print("Missing agent.artifact_update event.")
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="SSE smoke test for agent chat")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument(
        "--message",
        default="봉준호 스타일로 30초짜리 불안한 분위기의 드라마 만들어줘",
        help="Prompt to send",
    )
    parser.add_argument("--session-id", default=None, help="Existing session id")
    parser.add_argument("--model", default=None, help="Override model name")
    parser.add_argument("--user-id", default=None, help="Send X-User-Id header")
    parser.add_argument("--admin-mode", default=None, help="Send X-Admin-Mode header")
    parser.add_argument("--max-events", type=int, default=200, help="Stop after N events")
    parser.add_argument("--require-tool", action="store_true", help="Require tool_result event")
    parser.add_argument("--require-artifact", action="store_true", help="Require artifact_update event")
    parser.add_argument(
        "--health-path",
        default="/health/ready",
        help="Health endpoint path (default: /health/ready)",
    )
    parser.add_argument("--health-retries", type=int, default=15, help="Health check retries")
    parser.add_argument("--health-delay", type=float, default=1.0, help="Delay between health retries (sec)")
    parser.add_argument("--skip-health", action="store_true", help="Skip health check")
    args = parser.parse_args()

    code = run(
        base_url=args.base_url,
        message=args.message,
        session_id=args.session_id,
        model=args.model,
        user_id=args.user_id,
        admin_mode=args.admin_mode,
        max_events=args.max_events,
        require_tool=args.require_tool,
        require_artifact=args.require_artifact,
        health_path=args.health_path,
        health_retries=args.health_retries,
        health_delay=args.health_delay,
        skip_health=args.skip_health,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
