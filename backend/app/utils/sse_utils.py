"""SSE (Server-Sent Events) utilities for streaming responses.

This module provides reusable helpers for SSE streaming:
- Event formatting
- Progress tracking
- Error handling
- Generic streaming wrapper for dimension tools

Usage:
    from app.utils.sse_utils import (
        sse_event,
        create_dimension_stream,
        SSEProgress,
    )
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from typing import Any, AsyncGenerator, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================================
# SSE Event Types
# ============================================================================

@dataclass
class SSEProgress:
    """Progress event data structure."""
    percent: int  # 0-100
    message: str  # e.g., "처리 중..."
    stage: str = "processing"  # starting, processing, finalizing


@dataclass
class SSEComplete:
    """Completion event data structure."""
    success: bool
    data: Dict[str, Any]
    metrics: Optional[Dict[str, Any]] = None


@dataclass
class SSEError:
    """Error event data structure."""
    error: str
    code: Optional[str] = None
    detail: Optional[str] = None


# ============================================================================
# SSE Event Formatters
# ============================================================================

def sse_event(event_type: str, data: Any) -> str:
    """Format data as an SSE event string.

    Args:
        event_type: Type of event (progress, complete, error, heartbeat)
        data: Event payload (will be JSON serialized)

    Returns:
        Formatted SSE event string
    """
    if isinstance(data, (SSEProgress, SSEComplete, SSEError)):
        payload = {"type": event_type, **asdict(data)}
    elif isinstance(data, dict):
        payload = {"type": event_type, **data}
    else:
        payload = {"type": event_type, "data": data}

    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def sse_progress(percent: int, message: str, stage: str = "processing") -> str:
    """Create a progress SSE event."""
    return sse_event("progress", SSEProgress(percent, message, stage))


def sse_complete(data: Dict[str, Any], metrics: Optional[Dict[str, Any]] = None) -> str:
    """Create a completion SSE event."""
    return sse_event("complete", SSEComplete(True, data, metrics))


def sse_error(error: str, code: Optional[str] = None, detail: Optional[str] = None) -> str:
    """Create an error SSE event."""
    return sse_event("error", SSEError(error, code, detail))


def sse_heartbeat() -> str:
    """Create a heartbeat SSE event to keep connection alive."""
    return sse_event("heartbeat", {"timestamp": int(time.time())})


# ============================================================================
# Progress Callback Factory
# ============================================================================

class ProgressEmitter:
    """Manages progress emission for long-running operations.

    Usage:
        async def my_operation():
            emitter = ProgressEmitter()

            emitter.update(10, "분석 중...")
            # ... do work ...
            emitter.update(50, "생성 중...")
            # ... more work ...
            emitter.update(90, "완료 중...")

            return result
    """

    def __init__(self, queue: asyncio.Queue):
        self._queue = queue
        self._last_percent = 0

    def update(self, percent: int, message: str, stage: str = "processing"):
        """Update progress. Skips if percent hasn't increased."""
        if percent > self._last_percent:
            self._last_percent = percent
            try:
                self._queue.put_nowait(SSEProgress(percent, message, stage))
            except asyncio.QueueFull:
                pass  # Skip if queue is full


# ============================================================================
# Generic Streaming Wrapper
# ============================================================================

async def create_dimension_stream(
    execute_fn: Callable[[], Any],
    operation_name: str = "처리",
    timeout_seconds: float = 120.0,
) -> AsyncGenerator[str, None]:
    """Create an SSE stream for a dimension tool execution.

    This wrapper provides progress feedback for any async operation:
    1. Sends initial "starting" progress
    2. Executes the operation with timeout
    3. Sends "complete" or "error" based on result

    Args:
        execute_fn: Async function to execute (should return dict with 'success', 'output', etc.)
        operation_name: Name for progress messages (e.g., "프롬프트 생성")
        timeout_seconds: Maximum execution time

    Yields:
        SSE event strings

    Example:
        async def my_handler():
            async def do_work():
                return await execute_dimension_capsule(...)

            return StreamingResponse(
                create_dimension_stream(do_work, "스토리보드 생성"),
                media_type="text/event-stream",
            )
    """
    start_time = time.time()

    # Initial progress
    yield sse_progress(1, f"{operation_name} 시작...", "starting")

    try:
        # Show processing state
        yield sse_progress(10, f"{operation_name} 준비 중...", "processing")

        # Execute with timeout
        result = await asyncio.wait_for(
            execute_fn(),
            timeout=timeout_seconds,
        )

        # Show finalizing
        yield sse_progress(90, f"{operation_name} 완료 중...", "finalizing")

        latency_ms = int((time.time() - start_time) * 1000)

        if result and result.get("success"):
            metrics = result.get("metrics", {})
            metrics["latency_ms"] = latency_ms
            yield sse_complete(result.get("output", {}), metrics)
        else:
            error_msg = result.get("error", "Unknown error") if result else "No result"
            yield sse_error(error_msg, code="EXECUTION_FAILED")

    except asyncio.TimeoutError:
        yield sse_error(
            f"{operation_name} 시간 초과 ({timeout_seconds}초)",
            code="TIMEOUT",
        )
    except Exception as e:
        logger.exception(f"SSE stream error during {operation_name}")
        yield sse_error(str(e), code="INTERNAL_ERROR")


async def create_dimension_stream_with_progress(
    execute_fn: Callable[[ProgressEmitter], Any],
    operation_name: str = "처리",
    timeout_seconds: float = 120.0,
    heartbeat_interval: float = 10.0,
) -> AsyncGenerator[str, None]:
    """Create an SSE stream with real-time progress updates.

    Unlike create_dimension_stream, this version passes a ProgressEmitter
    to the execute function, allowing fine-grained progress updates.

    Args:
        execute_fn: Async function that accepts a ProgressEmitter
        operation_name: Name for progress messages
        timeout_seconds: Maximum execution time
        heartbeat_interval: Seconds between heartbeats

    Yields:
        SSE event strings

    Example:
        async def my_handler():
            async def do_work(emitter: ProgressEmitter):
                emitter.update(20, "데이터 로드 중...")
                data = await load_data()
                emitter.update(60, "AI 생성 중...")
                result = await generate(data)
                emitter.update(90, "검증 중...")
                return validate(result)

            return StreamingResponse(
                create_dimension_stream_with_progress(do_work, "스토리 생성"),
                media_type="text/event-stream",
            )
    """
    start_time = time.time()
    progress_queue: asyncio.Queue[SSEProgress] = asyncio.Queue(maxsize=100)
    emitter = ProgressEmitter(progress_queue)

    # Initial progress
    yield sse_progress(1, f"{operation_name} 시작...", "starting")

    # Start execution in background
    async def run_with_emitter():
        return await execute_fn(emitter)

    task = asyncio.create_task(run_with_emitter())

    try:
        # Stream progress updates until task completes
        while not task.done():
            try:
                progress = await asyncio.wait_for(
                    progress_queue.get(),
                    timeout=heartbeat_interval,
                )
                yield sse_progress(progress.percent, progress.message, progress.stage)
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                yield sse_heartbeat()

                # Check overall timeout
                if time.time() - start_time > timeout_seconds:
                    task.cancel()
                    yield sse_error(
                        f"{operation_name} 시간 초과 ({timeout_seconds}초)",
                        code="TIMEOUT",
                    )
                    return

        # Get result
        result = await task
        latency_ms = int((time.time() - start_time) * 1000)

        if result and result.get("success"):
            metrics = result.get("metrics", {})
            metrics["latency_ms"] = latency_ms
            yield sse_complete(result.get("output", {}), metrics)
        else:
            error_msg = result.get("error", "Unknown error") if result else "No result"
            yield sse_error(error_msg, code="EXECUTION_FAILED")

    except asyncio.CancelledError:
        yield sse_error("작업이 취소되었습니다", code="CANCELLED")
    except Exception as e:
        logger.exception(f"SSE stream error during {operation_name}")
        yield sse_error(str(e), code="INTERNAL_ERROR")


# ============================================================================
# Streaming Response Helpers
# ============================================================================

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # Disable nginx buffering
}


def get_sse_headers() -> Dict[str, str]:
    """Get standard SSE response headers."""
    return SSE_HEADERS.copy()
