"""Tests for Foundry observability — Langfuse integration."""
from __future__ import annotations

import json
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from app.features.original_ip_foundry.foundry_observability import trace_foundry_event


class TestTraceFoundryEvent:
    """Verify trace_foundry_event emits Langfuse spans + stdout JSON."""

    @patch("app.features.original_ip_foundry.foundry_observability.get_langfuse")
    def test_trace_foundry_emits_langfuse_span(self, mock_get_langfuse):
        mock_client = MagicMock()
        mock_get_langfuse.return_value = mock_client

        trace_foundry_event(
            name="/api/v1/foundry/health",
            latency_ms=42.0,
            status_code=200,
            tags=["foundry", "get"],
            metadata={"user": "ted@example.com", "model": "unknown", "input_type": "unknown"},
        )

        mock_client.trace.assert_called_once()
        call_kwargs = mock_client.trace.call_args[1]
        assert call_kwargs["name"] == "foundry./api/v1/foundry/health"
        assert call_kwargs["tags"] == ["foundry", "get"]
        assert call_kwargs["metadata"]["latency_ms"] == 42.0
        assert call_kwargs["metadata"]["status_code"] == 200
        assert call_kwargs["metadata"]["user"] == "ted@example.com"

    @patch("app.features.original_ip_foundry.foundry_observability.get_langfuse")
    def test_trace_foundry_noop_when_disabled(self, mock_get_langfuse):
        mock_get_langfuse.return_value = None

        # Should not raise
        trace_foundry_event(
            name="/api/v1/foundry/health",
            latency_ms=10.0,
            status_code=200,
        )

    @patch("app.features.original_ip_foundry.foundry_observability.get_langfuse")
    def test_trace_foundry_stdout_output(self, mock_get_langfuse, capsys):
        mock_get_langfuse.return_value = None

        trace_foundry_event(
            name="test_path",
            latency_ms=55.5,
            status_code=201,
            metadata={"user": "alice"},
        )

        captured = capsys.readouterr()
        line = json.loads(captured.out.strip())
        assert line["event"] == "foundry.test_path"
        assert line["latency_ms"] == 55.5
        assert line["status_code"] == 201
        assert line["user"] == "alice"

    @patch("app.features.original_ip_foundry.foundry_observability.get_langfuse")
    def test_trace_foundry_default_tags_and_metadata(self, mock_get_langfuse, capsys):
        """When tags/metadata are None, defaults are used without error."""
        mock_get_langfuse.return_value = None

        trace_foundry_event(
            name="minimal",
            latency_ms=1.0,
            status_code=200,
        )

        captured = capsys.readouterr()
        line = json.loads(captured.out.strip())
        assert line["event"] == "foundry.minimal"
        assert "latency_ms" in line
