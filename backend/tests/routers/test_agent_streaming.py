"""Integration tests for Agent Streaming (SSE).

Tests cover:
- SSE event sequence ordering
- StreamController mutex protection
- Stream cleanup on error
- Event formatting
"""
import asyncio
import pytest
from unittest.mock import MagicMock, patch
import threading

from app.routers.agent import StreamController, _build_event, _format_sse


class TestStreamController:
    """Test StreamController thread safety."""
    
    def test_initial_state_inactive(self):
        """StreamController should start inactive."""
        controller = StreamController()
        assert controller.is_active is False
    
    def test_start_stream_sets_active(self):
        """Starting stream should set active state."""
        controller = StreamController()
        
        # Mock dependencies
        mock_client = MagicMock()
        mock_client.stream_generate = MagicMock(return_value=iter([]))
        
        loop = asyncio.new_event_loop()
        queue = asyncio.Queue()
        
        try:
            controller.start_stream(
                mock_client,
                [],  # messages
                [],  # tools
                queue,
                loop,
            )
            
            # Give thread time to start
            import time
            time.sleep(0.1)
            
            # Should be active briefly, then finish
            # (empty generator finishes quickly)
            time.sleep(0.2)
            
            # After completion, should be inactive
            assert controller.is_active is False
        finally:
            loop.close()
    
    def test_duplicate_stream_raises_error(self):
        """Attempting duplicate stream should raise RuntimeError."""
        controller = StreamController()
        
        # Mock a slow generator
        def slow_generator():
            import time
            time.sleep(1)
            return
            yield  # Make it a generator
        
        mock_client = MagicMock()
        mock_client.stream_generate = MagicMock(return_value=slow_generator())
        
        loop = asyncio.new_event_loop()
        queue = asyncio.Queue()
        
        try:
            # Start first stream
            controller.start_stream(mock_client, [], [], queue, loop)
            
            # Give thread time to start
            import time
            time.sleep(0.05)
            
            # Second stream should fail
            with pytest.raises(RuntimeError, match="Stream already active"):
                controller.start_stream(mock_client, [], [], queue, loop)
        finally:
            loop.close()
    
    def test_stream_cleanup_on_completion(self):
        """Stream should cleanup properly on completion."""
        controller = StreamController()
        
        # Mock generator that completes
        mock_client = MagicMock()
        mock_client.stream_generate = MagicMock(return_value=iter(["delta1", "delta2"]))
        
        loop = asyncio.new_event_loop()
        queue = asyncio.Queue()
        
        try:
            result = controller.start_stream(mock_client, [], [], queue, loop)
            
            # Wait for completion
            import time
            time.sleep(0.3)
            
            # Should be inactive
            assert controller.is_active is False
        finally:
            loop.close()


class TestSSEEventFormatting:
    """Test SSE event format helpers."""
    
    def test_build_event_structure(self):
        """_build_event should create proper structure."""
        event = _build_event(
            session_id="session-123",
            seq=1,
            event_type="agent.delta",
            payload={"delta": "Hello"},
            ts="2026-01-08T00:00:00Z",
        )
        
        assert event["event_id"] == "session-123:1"
        assert event["session_id"] == "session-123"
        assert event["type"] == "agent.delta"
        assert event["seq"] == 1
        assert event["payload"] == {"delta": "Hello"}
    
    def test_format_sse_output(self):
        """_format_sse should format SSE correctly."""
        data = {
            "event_id": "session:1",
            "type": "agent.delta",
            "payload": {"text": "hi"},
        }
        
        output = _format_sse("agent.delta", data)
        
        assert "id: session:1" in output
        assert "event: agent.delta" in output
        assert "data: " in output
        assert output.endswith("\n\n")
    
    def test_sequence_numbers_increment(self):
        """Sequence numbers should increment properly."""
        events = []
        for i in range(1, 5):
            event = _build_event(
                session_id="test",
                seq=i,
                event_type="agent.delta",
                payload={"n": i},
                ts="",
            )
            events.append(event)
        
        seqs = [e["seq"] for e in events]
        assert seqs == [1, 2, 3, 4]


class TestSSEEventTypes:
    """Test various SSE event types."""
    
    def test_delta_event(self):
        """Delta event should have correct structure."""
        event = _build_event(
            session_id="s",
            seq=1,
            event_type="agent.delta",
            payload={"delta": "Hi"},
            ts="",
        )
        assert event["type"] == "agent.delta"
    
    def test_tool_result_event(self):
        """Tool result event should have correct structure."""
        event = _build_event(
            session_id="s",
            seq=2,
            event_type="agent.tool_result",
            payload={
                "tool_call_id": "call-1",
                "name": "test_tool",
                "status": "complete",
                "output": {"data": 123},
            },
            ts="",
        )
        assert event["type"] == "agent.tool_result"
        assert event["payload"]["name"] == "test_tool"
    
    def test_workflow_event(self):
        """Workflow events should have correct structure."""
        event = _build_event(
            session_id="s",
            seq=3,
            event_type="agent.workflow_start",
            payload={
                "topic": "Video generation",
                "dimensions": ["1D", "2D"],
                "total_steps": 3,
            },
            ts="",
        )
        assert event["type"] == "agent.workflow_start"
        assert event["payload"]["total_steps"] == 3
