"""Workflow Typed Exceptions (Phase 2 Hardening).

Typed exceptions for workflow orchestration with clear error categories.
Each exception includes error code for frontend handling.

Error Code Ranges:
    - WF001-099: Validation errors (input, config, state)
    - WF100-199: Execution errors (tool, capsule, timeout)
    - WF200-299: Resource errors (credits, quota, rate limit)
    - WF300-399: State errors (session, node, transition)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class WorkflowError(Exception):
    """Base workflow exception with structured error info."""

    error_code: str = "WF000"

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        if error_code:
            self.error_code = error_code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API response."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


class WorkflowValidationError(WorkflowError):
    """Input or configuration validation failed."""

    error_code = "WF001"

    def __init__(
        self,
        message: str,
        field_errors: Optional[List[Dict[str, Any]]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.field_errors = field_errors or []
        super().__init__(message, details=details)

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base["field_errors"] = self.field_errors
        return base


class InvalidToolIdError(WorkflowError):
    """Unknown or unsupported tool ID."""

    error_code = "WF002"

    def __init__(self, tool_id: str):
        self.tool_id = tool_id
        super().__init__(
            message=f"Unknown tool_id: {tool_id}",
            details={"tool_id": tool_id},
        )


class MissingRequiredFieldError(WorkflowError):
    """Required input field is missing."""

    error_code = "WF003"

    def __init__(self, field_name: str, tool_id: str):
        self.field_name = field_name
        self.tool_id = tool_id
        super().__init__(
            message=f"Missing required field '{field_name}' for tool '{tool_id}'",
            details={"field": field_name, "tool_id": tool_id},
        )


class InvalidFieldTypeError(WorkflowError):
    """Field has incorrect type."""

    error_code = "WF004"

    def __init__(self, field_name: str, expected_type: str, actual_type: str):
        self.field_name = field_name
        self.expected_type = expected_type
        self.actual_type = actual_type
        super().__init__(
            message=f"Field '{field_name}' expected {expected_type}, got {actual_type}",
            details={
                "field": field_name,
                "expected": expected_type,
                "actual": actual_type,
            },
        )


class ToolExecutionError(WorkflowError):
    """Tool/capsule execution failed."""

    error_code = "WF100"

    def __init__(self, tool_id: str, capsule_error: Optional[str] = None):
        self.tool_id = tool_id
        self.capsule_error = capsule_error
        super().__init__(
            message=f"Tool execution failed: {tool_id}",
            details={"tool_id": tool_id, "capsule_error": capsule_error},
        )


class ToolTimeoutError(WorkflowError):
    """Tool execution timed out."""

    error_code = "WF101"

    def __init__(self, tool_id: str, timeout_seconds: int):
        self.tool_id = tool_id
        self.timeout_seconds = timeout_seconds
        super().__init__(
            message=f"Tool '{tool_id}' timed out after {timeout_seconds}s",
            details={"tool_id": tool_id, "timeout": timeout_seconds},
        )


class CapsuleNotFoundError(WorkflowError):
    """Capsule not found for tool."""

    error_code = "WF102"

    def __init__(self, tool_id: str, capsule_id: str):
        self.tool_id = tool_id
        self.capsule_id = capsule_id
        super().__init__(
            message=f"Capsule '{capsule_id}' not found for tool '{tool_id}'",
            details={"tool_id": tool_id, "capsule_id": capsule_id},
        )


class InsufficientCreditsError(WorkflowError):
    """User doesn't have enough credits."""

    error_code = "WF200"

    def __init__(
        self,
        required_credits: int,
        available_credits: int,
        tool_id: str = "",
    ):
        self.required_credits = required_credits
        self.available_credits = available_credits
        self.tool_id = tool_id
        super().__init__(
            message=f"크레딧 부족: 필요 {required_credits}, 보유 {available_credits}",
            details={
                "required": required_credits,
                "available": available_credits,
                "tool_id": tool_id,
            },
        )


class QuotaExceededError(WorkflowError):
    """User exceeded daily/monthly quota."""

    error_code = "WF201"

    def __init__(self, quota_type: str, limit: int, used: int):
        self.quota_type = quota_type
        self.limit = limit
        self.used = used
        super().__init__(
            message=f"{quota_type.capitalize()} quota exceeded: {used}/{limit}",
            details={"quota_type": quota_type, "limit": limit, "used": used},
        )


class RateLimitExceededError(WorkflowError):
    """Too many requests in short time."""

    error_code = "WF202"

    def __init__(self, retry_after_seconds: int = 60):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            message=f"Rate limit exceeded. Retry after {retry_after_seconds}s",
            details={"retry_after": retry_after_seconds},
        )


class SessionNotFoundError(WorkflowError):
    """Workflow session not found."""

    error_code = "WF300"

    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(
            message=f"Workflow session not found: {session_id}",
            details={"session_id": session_id},
        )


class SessionExpiredError(WorkflowError):
    """Workflow session has expired (TTL exceeded)."""

    error_code = "WF301"

    def __init__(self, session_id: str, expired_at: Optional[str] = None):
        self.session_id = session_id
        self.expired_at = expired_at
        super().__init__(
            message=f"Workflow session expired: {session_id}",
            details={"session_id": session_id, "expired_at": expired_at},
        )


class InvalidSessionStateError(WorkflowError):
    """Session is in invalid state for requested action."""

    error_code = "WF302"

    def __init__(self, session_id: str, current_state: str, required_state: str):
        self.session_id = session_id
        self.current_state = current_state
        self.required_state = required_state
        super().__init__(
            message=f"Session '{session_id}' is '{current_state}', expected '{required_state}'",
            details={
                "session_id": session_id,
                "current": current_state,
                "required": required_state,
            },
        )


class NodeAlreadyExecutedError(WorkflowError):
    """Node has already been executed (idempotency guard)."""

    error_code = "WF303"

    def __init__(self, node_id: str, session_id: str):
        self.node_id = node_id
        self.session_id = session_id
        super().__init__(
            message=f"Node '{node_id}' already executed",
            details={"node_id": node_id, "session_id": session_id},
        )


class NodeExecutingError(WorkflowError):
    """Node is currently being executed (concurrent call)."""

    error_code = "WF304"

    def __init__(self, node_id: str, session_id: str):
        self.node_id = node_id
        self.session_id = session_id
        super().__init__(
            message=f"Node '{node_id}' is already executing (duplicate call?)",
            details={"node_id": node_id, "session_id": session_id},
        )


class NoMoreStepsError(WorkflowError):
    """No more steps to execute in workflow."""

    error_code = "WF305"

    def __init__(self, session_id: str, current_step: int, total_steps: int):
        self.session_id = session_id
        self.current_step = current_step
        self.total_steps = total_steps
        super().__init__(
            message=f"No more steps to execute ({current_step}/{total_steps})",
            details={
                "session_id": session_id,
                "current_step": current_step,
                "total_steps": total_steps,
            },
        )
