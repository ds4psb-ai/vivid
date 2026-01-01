"""Shared utilities for agent tool handlers.

Provides common patterns for tool result building, error handling,
event emission, and Enterprise client instantiation.
"""
from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from app.agents.agent_types import (
    ToolCall,
    ToolContext,
    ToolResult,
    ToolTaskState,
)
from app.logging_config import get_logger

logger = get_logger("tool_utils")

T = TypeVar("T")


# =============================================================================
# Tool Result Builders
# =============================================================================

def success_result(
    call: ToolCall,
    output: Dict[str, Any],
) -> ToolResult:
    """Build a successful ToolResult."""
    return ToolResult(
        tool_call_id=call.id,
        name=call.name,
        status=ToolTaskState.COMPLETED,
        output=output,
    )


def error_result(
    call: ToolCall,
    error: str,
) -> ToolResult:
    """Build a failed ToolResult."""
    return ToolResult(
        tool_call_id=call.id,
        name=call.name,
        status=ToolTaskState.FAILED,
        error=error,
    )


def validation_error(
    call: ToolCall,
    field: str,
    message: Optional[str] = None,
) -> ToolResult:
    """Build a validation error ToolResult."""
    error_msg = message or f"{field} is required"
    return error_result(call, error_msg)


# =============================================================================
# Event Emitter Factory
# =============================================================================

class EventEmitter:
    """Context-aware event emitter for tool handlers."""
    
    def __init__(self, context: ToolContext, call: ToolCall):
        self._emit_fn = context.emit_event
        self._call = call
    
    def emit(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Emit an event with tool_call_id automatically included."""
        if self._emit_fn:
            payload = {"tool_call_id": self._call.id}
            if data:
                payload.update(data)
            self._emit_fn(event_type, payload)
    
    def progress(
        self,
        step: int,
        name: str,
        progress: int,
        total_steps: int = 5,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit a progress event with standard structure."""
        data = {
            "step": step,
            "name": name,
            "progress": progress,
            "total_steps": total_steps,
        }
        if extra:
            data.update(extra)
        self.emit("agent.analysis_progress", data)


def create_emitter(context: ToolContext, call: ToolCall) -> EventEmitter:
    """Create an EventEmitter for the given context and call."""
    return EventEmitter(context, call)


# =============================================================================
# Enterprise Client Factory
# =============================================================================

_enterprise_client_cache: Dict[str, Any] = {}


def get_enterprise_client(
    project_number: Optional[str] = None,
    credentials_path: Optional[str] = None,
    *,
    use_cache: bool = True,
) -> Any:
    """
    Get a NotebookLM Enterprise client instance.
    
    Caches client instances to avoid repeated credential refresh.
    """
    from app.notebooklm_enterprise_client import NotebookLMEnterpriseClient
    from app.config import settings
    
    project = project_number or getattr(settings, "GCP_PROJECT_NUMBER", "239259013228")
    creds = credentials_path or getattr(settings, "GCP_CREDENTIALS_PATH", None)
    
    cache_key = f"{project}:{creds or 'default'}"
    
    if use_cache and cache_key in _enterprise_client_cache:
        return _enterprise_client_cache[cache_key]
    
    client = NotebookLMEnterpriseClient(
        project_number=project,
        credentials_path=creds,
    )
    
    if use_cache:
        _enterprise_client_cache[cache_key] = client
    
    return client


def clear_client_cache() -> None:
    """Clear the enterprise client cache."""
    _enterprise_client_cache.clear()


# =============================================================================
# Token Usage Accumulator
# =============================================================================

class TokenUsageTracker:
    """Accumulates token usage across multiple operations."""
    
    def __init__(self):
        self._input = 0
        self._output = 0
        self._total = 0
    
    def add(self, usage: Dict[str, int]) -> None:
        """Add usage from a single operation."""
        self._input += usage.get("input", 0)
        self._output += usage.get("output", 0)
        self._total += usage.get("total", 0)
    
    def to_dict(self) -> Dict[str, int]:
        """Return accumulated usage as a dict."""
        return {
            "input": self._input,
            "output": self._output,
            "total": self._total,
        }
    
    @property
    def input(self) -> int:
        return self._input
    
    @property
    def output(self) -> int:
        return self._output
    
    @property
    def total(self) -> int:
        return self._total


# =============================================================================
# Evidence Refs Extractor
# =============================================================================

def extract_evidence_refs(claims: list) -> list:
    """
    Extract evidence_refs from a list of claims.
    
    Handles both string and list evidence_refs.
    """
    refs = []
    for claim in claims:
        claim_refs = claim.get("evidence_refs", [])
        if isinstance(claim_refs, str):
            refs.append(claim_refs)
        elif isinstance(claim_refs, list):
            refs.extend(claim_refs)
    return refs


# =============================================================================
# Source ID Extractor
# =============================================================================

def extract_first_source_id(source_pack: Dict[str, Any]) -> Optional[str]:
    """Extract the first valid source_id from a source_pack."""
    source_ids = source_pack.get("source_ids")
    if not isinstance(source_ids, list):
        return None
    
    for item in source_ids:
        if isinstance(item, str) and item.strip():
            return item.strip()
    
    return None
