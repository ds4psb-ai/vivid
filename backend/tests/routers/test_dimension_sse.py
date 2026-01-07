"""Tests for Dimension SSE utilities and streaming endpoints.

Tests cover:
- SSE event formatters
- Progress emitter
- SSE headers
- Generic streaming wrapper
"""
import asyncio
import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.utils.sse_utils import (
    SSEProgress,
    SSEComplete,
    SSEError,
    sse_event,
    sse_progress,
    sse_complete,
    sse_error,
    sse_heartbeat,
    get_sse_headers,
    ProgressEmitter,
    create_dimension_stream,
)


class TestSSEEventFormatters:
    """Test SSE event formatting functions."""

    def test_sse_event_with_dataclass(self):
        """sse_event should handle SSEProgress dataclass."""
        progress = SSEProgress(percent=50, message="처리 중...", stage="processing")
        result = sse_event("progress", progress)

        assert result.startswith("data: ")
        assert result.endswith("\n\n")

        # Parse the JSON
        data = json.loads(result[6:-2])  # Remove "data: " and "\n\n"
        assert data["type"] == "progress"
        assert data["percent"] == 50
        assert data["message"] == "처리 중..."
        assert data["stage"] == "processing"

    def test_sse_event_with_dict(self):
        """sse_event should handle plain dict."""
        result = sse_event("custom", {"key": "value", "count": 42})

        data = json.loads(result[6:-2])
        assert data["type"] == "custom"
        assert data["key"] == "value"
        assert data["count"] == 42

    def test_sse_event_with_scalar(self):
        """sse_event should handle scalar values."""
        result = sse_event("message", "Hello World")

        data = json.loads(result[6:-2])
        assert data["type"] == "message"
        assert data["data"] == "Hello World"

    def test_sse_progress_helper(self):
        """sse_progress should create proper progress event."""
        result = sse_progress(75, "거의 완료", "finalizing")

        data = json.loads(result[6:-2])
        assert data["type"] == "progress"
        assert data["percent"] == 75
        assert data["message"] == "거의 완료"
        assert data["stage"] == "finalizing"

    def test_sse_complete_helper(self):
        """sse_complete should create proper completion event."""
        result = sse_complete(
            {"output": "result data"},
            {"latency_ms": 1234}
        )

        data = json.loads(result[6:-2])
        assert data["type"] == "complete"
        assert data["success"] is True
        assert data["data"] == {"output": "result data"}
        assert data["metrics"] == {"latency_ms": 1234}

    def test_sse_error_helper(self):
        """sse_error should create proper error event."""
        result = sse_error("크레딧 부족", "INSUFFICIENT_CREDITS", "10 크레딧 필요")

        data = json.loads(result[6:-2])
        assert data["type"] == "error"
        assert data["error"] == "크레딧 부족"
        assert data["code"] == "INSUFFICIENT_CREDITS"
        assert data["detail"] == "10 크레딧 필요"

    def test_sse_heartbeat_helper(self):
        """sse_heartbeat should create heartbeat event with timestamp."""
        result = sse_heartbeat()

        data = json.loads(result[6:-2])
        assert data["type"] == "heartbeat"
        assert "timestamp" in data
        assert isinstance(data["timestamp"], int)

    def test_korean_characters_preserved(self):
        """Korean characters should be preserved (not escaped)."""
        result = sse_progress(50, "한글 메시지 테스트")

        # Should contain actual Korean, not unicode escapes
        assert "한글" in result
        assert "\\u" not in result


class TestSSEHeaders:
    """Test SSE response headers."""

    def test_get_sse_headers(self):
        """get_sse_headers should return proper headers."""
        headers = get_sse_headers()

        assert headers["Cache-Control"] == "no-cache"
        assert headers["Connection"] == "keep-alive"
        assert headers["X-Accel-Buffering"] == "no"

    def test_get_sse_headers_returns_copy(self):
        """get_sse_headers should return a new dict each time."""
        headers1 = get_sse_headers()
        headers2 = get_sse_headers()

        headers1["Custom"] = "value"
        assert "Custom" not in headers2


class TestProgressEmitter:
    """Test ProgressEmitter for real-time progress updates."""

    @pytest.mark.asyncio
    async def test_emitter_updates_queue(self):
        """ProgressEmitter should put progress in queue."""
        queue = asyncio.Queue()
        emitter = ProgressEmitter(queue)

        emitter.update(10, "시작")
        emitter.update(50, "진행 중")
        emitter.update(90, "완료 중")

        # Should have 3 items
        assert queue.qsize() == 3

        progress1 = await queue.get()
        assert progress1.percent == 10
        assert progress1.message == "시작"

    @pytest.mark.asyncio
    async def test_emitter_skips_non_increasing_percent(self):
        """ProgressEmitter should skip updates with same/lower percent."""
        queue = asyncio.Queue()
        emitter = ProgressEmitter(queue)

        emitter.update(50, "첫번째")
        emitter.update(50, "두번째")  # Same - should skip
        emitter.update(40, "세번째")  # Lower - should skip
        emitter.update(60, "네번째")  # Higher - should emit

        assert queue.qsize() == 2

    @pytest.mark.asyncio
    async def test_emitter_handles_full_queue(self):
        """ProgressEmitter should not block on full queue."""
        queue = asyncio.Queue(maxsize=2)
        emitter = ProgressEmitter(queue)

        emitter.update(10, "1")
        emitter.update(20, "2")
        emitter.update(30, "3")  # Queue full - should not raise

        assert queue.qsize() == 2


class TestCreateDimensionStream:
    """Test generic streaming wrapper."""

    @pytest.mark.asyncio
    async def test_successful_stream(self):
        """Stream should emit progress and complete on success."""
        async def mock_execute():
            return {
                "success": True,
                "output": {"result": "data"},
                "metrics": {"tokens": 100},
            }

        events = []
        async for event in create_dimension_stream(mock_execute, "테스트"):
            events.append(event)

        # Should have: starting, processing, finalizing, complete
        assert len(events) >= 3

        # Check first event is starting
        first = json.loads(events[0][6:-2])
        assert first["type"] == "progress"
        assert first["stage"] == "starting"

        # Check last event is complete
        last = json.loads(events[-1][6:-2])
        assert last["type"] == "complete"
        assert last["success"] is True

    @pytest.mark.asyncio
    async def test_error_stream(self):
        """Stream should emit error on failure."""
        async def mock_execute():
            return {
                "success": False,
                "error": "Something went wrong",
            }

        events = []
        async for event in create_dimension_stream(mock_execute, "테스트"):
            events.append(event)

        # Check last event is error
        last = json.loads(events[-1][6:-2])
        assert last["type"] == "error"
        assert "Something went wrong" in last["error"]

    @pytest.mark.asyncio
    async def test_exception_stream(self):
        """Stream should handle exceptions gracefully."""
        async def mock_execute():
            raise ValueError("Unexpected error")

        events = []
        async for event in create_dimension_stream(mock_execute, "테스트"):
            events.append(event)

        # Check last event is error
        last = json.loads(events[-1][6:-2])
        assert last["type"] == "error"
        assert last["code"] == "INTERNAL_ERROR"

    @pytest.mark.asyncio
    async def test_timeout_stream(self):
        """Stream should handle timeout."""
        async def mock_execute():
            await asyncio.sleep(10)  # Very long
            return {"success": True}

        events = []
        async for event in create_dimension_stream(
            mock_execute,
            "테스트",
            timeout_seconds=0.1,  # Very short timeout
        ):
            events.append(event)

        # Check last event is timeout error
        last = json.loads(events[-1][6:-2])
        assert last["type"] == "error"
        assert last["code"] == "TIMEOUT"


class TestSSEDataclasses:
    """Test SSE dataclass structures."""

    def test_sse_progress_defaults(self):
        """SSEProgress should have default stage."""
        progress = SSEProgress(percent=50, message="Test")
        assert progress.stage == "processing"

    def test_sse_complete_defaults(self):
        """SSEComplete should have optional metrics."""
        complete = SSEComplete(success=True, data={"key": "value"})
        assert complete.metrics is None

    def test_sse_error_defaults(self):
        """SSEError should have optional code and detail."""
        error = SSEError(error="Something failed")
        assert error.code is None
        assert error.detail is None
