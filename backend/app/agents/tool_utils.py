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
# Evidence Refs Filtering
# =============================================================================

# Allowed evidence ref prefixes (per 32_CLAIM_EVIDENCE_TRACE_SPEC.md)
ALLOWED_EVIDENCE_PREFIXES = frozenset({
    "db:",        # Database references (db:table:id)
    "sheet:",     # Sheet references (sheet:SheetName:RowId)
    "source:",    # Source timestamps (source:00:00:10-00:00:15)
    "segment:",   # Segment IDs (segment:abc123)
    "claim:",     # Claim references (claim:xyz)
    "pattern:",   # Pattern references (pattern:abc)
    "comment_",   # Comment references (comment_123)
    "ref-",       # Legacy generic refs (ref-1, ref-abc)
    "ref:",       # Legacy generic refs (ref:abc)
})

# Maximum evidence refs to prevent response bloat
MAX_EVIDENCE_REFS = 50


def filter_evidence_refs(
    refs: list,
    max_refs: int = MAX_EVIDENCE_REFS,
    deduplicate: bool = True,
) -> tuple[list[str], list[str]]:
    """Filter and validate evidence refs.

    Args:
        refs: Raw list of evidence refs
        max_refs: Maximum number of refs to return
        deduplicate: Remove duplicate refs

    Returns:
        Tuple of (filtered_refs, warnings)

    Filtering rules:
    1. Remove non-strings
    2. Strip whitespace
    3. Remove empty strings
    4. Deduplicate (if enabled)
    5. Validate prefix (must be in ALLOWED_EVIDENCE_PREFIXES)
    6. Limit to max_refs
    """
    if not refs:
        return [], []

    filtered: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()

    for ref in refs:
        # Skip non-strings
        if not isinstance(ref, str):
            warnings.append("evidence_ref_filtered:invalid_type")
            continue

        # Strip and skip empty
        cleaned = ref.strip()
        if not cleaned:
            continue

        # Deduplicate
        if deduplicate:
            if cleaned in seen:
                continue
            seen.add(cleaned)

        # Validate prefix
        has_valid_prefix = any(
            cleaned.startswith(prefix) for prefix in ALLOWED_EVIDENCE_PREFIXES
        )
        if not has_valid_prefix:
            prefix = cleaned.split(":", 1)[0] if ":" in cleaned else cleaned[:10]
            warnings.append(f"evidence_ref_filtered:invalid_prefix:{prefix}")
            continue

        # Validate format for known prefixes
        if cleaned.startswith("db:"):
            parts = cleaned.split(":", 2)
            if len(parts) != 3 or not parts[1] or not parts[2]:
                warnings.append("evidence_ref_filtered:invalid_db_format")
                continue
        elif cleaned.startswith("sheet:"):
            parts = cleaned.split(":", 2)
            if len(parts) != 3 or not parts[1] or not parts[2]:
                warnings.append("evidence_ref_filtered:invalid_sheet_format")
                continue
        elif cleaned.startswith("source:"):
            # source:00:00:10-00:00:15 format
            if len(cleaned) < 10:  # Minimum length check
                warnings.append("evidence_ref_filtered:invalid_source_format")
                continue

        filtered.append(cleaned)

        # Limit refs
        if len(filtered) >= max_refs:
            remaining = len(refs) - len(filtered)
            if remaining > 0:
                warnings.append(f"evidence_ref_truncated:limit_{max_refs}:dropped_{remaining}")
            break

    return filtered, warnings


def extract_evidence_refs(
    claims: list,
    filter_refs: bool = True,
    max_refs: int = MAX_EVIDENCE_REFS,
) -> list[str]:
    """Extract evidence_refs from a list of claims.

    Args:
        claims: List of claim dicts with evidence_refs field
        filter_refs: Apply filtering/validation (default: True)
        max_refs: Maximum refs when filtering

    Returns:
        List of evidence refs (filtered if enabled)
    """
    raw_refs = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_refs = claim.get("evidence_refs", [])
        if isinstance(claim_refs, str):
            raw_refs.append(claim_refs)
        elif isinstance(claim_refs, list):
            raw_refs.extend(claim_refs)

    if filter_refs:
        filtered, warnings = filter_evidence_refs(raw_refs, max_refs=max_refs)
        if warnings:
            logger.debug(f"Evidence ref filtering: {len(warnings)} warnings")
        return filtered

    return raw_refs


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
