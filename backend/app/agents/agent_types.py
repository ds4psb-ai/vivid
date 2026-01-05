"""Shared agent types and tool registry primitives."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol

from pydantic import BaseModel, Field


# =============================================================================
# Handle Pattern Types
# =============================================================================

# HandleRef is a string reference to large data: "handle:{storage}:{key}"
HandleRef = str


class AgentRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolTaskState(str, Enum):
    WORKING = "working"
    INPUT_REQUIRED = "input_required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    tool_call_id: str
    name: str
    status: ToolTaskState = ToolTaskState.COMPLETED
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    task_id: Optional[str] = None

    def to_message_content(self) -> str:
        payload = {
            "name": self.name,
            "status": self.status.value,
            "output": self.output or {},
            "error": self.error,
            "task_id": self.task_id,
        }
        return json.dumps(payload, ensure_ascii=True)


class AgentMessage(BaseModel):
    role: AgentRole
    content: str = ""
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    attachments: List[Dict[str, Any]] = Field(default_factory=list)


class ToolSpec(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None


# =============================================================================
# TieredContext: Multi-level context for workflow execution
# =============================================================================

# Hardening constants
MAX_HISTORY_LENGTH = 100  # Maximum step summaries to keep
MAX_HANDLES_COUNT = 50    # Maximum handle references
MAX_SESSION_KEYS = 50     # Maximum session key-value pairs


@dataclass
class StepSummary:
    """Summary of a completed workflow step."""
    step_index: int
    dimension: str  # "1D", "2D", "3D", "4D"
    tool_name: str
    success: bool
    output_preview: str
    credit_cost: int = 0
    completed_at: Optional[str] = None  # ISO timestamp

    @classmethod
    def from_dict_safe(cls, data: Dict[str, Any]) -> Optional["StepSummary"]:
        """Safely create StepSummary from dict with validation.

        Returns None if required fields are missing or invalid.
        """
        required_fields = ["step_index", "dimension", "tool_name", "success", "output_preview"]

        # Check required fields exist
        for field in required_fields:
            if field not in data:
                return None

        # Validate types
        try:
            step_index = int(data["step_index"])
            dimension = str(data["dimension"])
            tool_name = str(data["tool_name"])
            success = bool(data["success"])
            output_preview = str(data["output_preview"])
            credit_cost = int(data.get("credit_cost", 0))
            completed_at = data.get("completed_at")
            if completed_at is not None:
                completed_at = str(completed_at)

            return cls(
                step_index=step_index,
                dimension=dimension,
                tool_name=tool_name,
                success=success,
                output_preview=output_preview,
                credit_cost=credit_cost,
                completed_at=completed_at,
            )
        except (ValueError, TypeError):
            return None


@dataclass
class TieredContext:
    """Multi-level context for workflow execution.

    Provides isolation between steps while maintaining session-wide state.

    Levels:
    - session: Series-wide globals (character, style, user preferences)
    - step: Current step state (inputs, intermediate results)
    - history: Summaries of previous steps for context continuity
    - handles: References to large artifacts stored externally
    """
    session: Dict[str, Any] = field(default_factory=dict)
    step: Dict[str, Any] = field(default_factory=dict)
    history: List[StepSummary] = field(default_factory=list)
    handles: Dict[str, HandleRef] = field(default_factory=dict)
    current_step_index: int = 0
    current_dimension: Optional[str] = None

    def advance_step(self, dimension: str) -> None:
        """Advance to next step, archiving current step to history."""
        if self.step and self.current_dimension:
            summary = StepSummary(
                step_index=self.current_step_index,
                dimension=self.current_dimension,
                tool_name=self.step.get("tool_name", "unknown"),
                success=self.step.get("success", False),
                output_preview=self._create_output_preview(self.step.get("output", {})),
                credit_cost=self.step.get("credit_cost", 0),
                completed_at=datetime.utcnow().isoformat() + "Z",
            )
            self.history.append(summary)

            # Enforce history size limit (FIFO eviction)
            if len(self.history) > MAX_HISTORY_LENGTH:
                self.history = self.history[-MAX_HISTORY_LENGTH:]

        self.step = {}
        self.current_step_index += 1
        self.current_dimension = dimension

    def _create_output_preview(self, output: Dict[str, Any], max_len: int = 200) -> str:
        """Create truncated preview of step output."""
        if not output:
            return "(empty)"

        for key in ["prompt", "description", "analysis"]:
            if key in output and isinstance(output[key], str):
                text = output[key]
                return text[:max_len] + "..." if len(text) > max_len else text

        if "scenes" in output and isinstance(output["scenes"], list):
            return f"{len(output['scenes'])} scenes generated"

        return f"{len(output)} fields"

    def get_session_value(self, key: str, default: Any = None) -> Any:
        """Get session-level value."""
        return self.session.get(key, default)

    def set_session_value(self, key: str, value: Any) -> None:
        """Set session-level value (persists across steps).

        Raises ValueError if session key limit exceeded.
        """
        if key not in self.session and len(self.session) >= MAX_SESSION_KEYS:
            raise ValueError(f"Session key limit ({MAX_SESSION_KEYS}) exceeded")
        self.session[key] = value

    def register_handle(self, key: str, handle_ref: HandleRef) -> None:
        """Register a handle reference for large data.

        Raises ValueError if handle limit exceeded.
        """
        if key not in self.handles and len(self.handles) >= MAX_HANDLES_COUNT:
            raise ValueError(f"Handle limit ({MAX_HANDLES_COUNT}) exceeded")
        self.handles[key] = handle_ref

    def get_last_output(self) -> Dict[str, Any]:
        """Get the last step's full output from step context."""
        return self.step.get("output", {})

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage/transmission."""
        return {
            "session": self.session,
            "step": self.step,
            "history": [asdict(s) for s in self.history],
            "handles": self.handles,
            "current_step_index": self.current_step_index,
            "current_dimension": self.current_dimension,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TieredContext":
        """Deserialize from storage with validation.

        Invalid history entries are skipped with warning.
        Size limits are enforced on load.
        """
        # Parse history with validation
        history: List[StepSummary] = []
        raw_history = data.get("history", [])
        if isinstance(raw_history, list):
            for i, item in enumerate(raw_history):
                if isinstance(item, dict):
                    summary = StepSummary.from_dict_safe(item)
                    if summary is not None:
                        history.append(summary)
                    # Skip invalid entries silently (already logged in from_dict_safe)

        # Enforce history limit on load
        if len(history) > MAX_HISTORY_LENGTH:
            history = history[-MAX_HISTORY_LENGTH:]

        # Parse session with limit
        session = data.get("session", {})
        if isinstance(session, dict) and len(session) > MAX_SESSION_KEYS:
            # Keep most recent keys (arbitrary order in dict)
            session = dict(list(session.items())[:MAX_SESSION_KEYS])

        # Parse handles with limit
        handles = data.get("handles", {})
        if isinstance(handles, dict) and len(handles) > MAX_HANDLES_COUNT:
            handles = dict(list(handles.items())[:MAX_HANDLES_COUNT])

        return cls(
            session=session if isinstance(session, dict) else {},
            step=data.get("step", {}) if isinstance(data.get("step"), dict) else {},
            history=history,
            handles=handles if isinstance(handles, dict) else {},
            current_step_index=int(data.get("current_step_index", 0)),
            current_dimension=data.get("current_dimension"),
        )


@dataclass
class AgentState:
    session_id: str
    messages: List[AgentMessage] = field(default_factory=list)
    summary: Optional[str] = None
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tiered_context: Optional[TieredContext] = None

    def get_or_create_tiered_context(self) -> TieredContext:
        """Get existing tiered context or create new one."""
        if self.tiered_context is None:
            self.tiered_context = TieredContext()
        return self.tiered_context


@dataclass
class ToolContext:
    state: AgentState
    emit_event: Optional[Callable[[str, Dict[str, Any]], None]] = None

    @property
    def session_id(self) -> str:
        return self.state.session_id

    @property
    def tiered(self) -> Optional[TieredContext]:
        """Get tiered context if available."""
        return self.state.tiered_context

    def require_tiered(self) -> TieredContext:
        """Get or create tiered context."""
        return self.state.get_or_create_tiered_context()

    def get_session_value(self, key: str, default: Any = None) -> Any:
        """Get value from session tier."""
        if self.tiered:
            return self.tiered.get_session_value(key, default)
        return self.state.metadata.get(key, default)

    def set_session_value(self, key: str, value: Any) -> None:
        """Set value in session tier."""
        tiered = self.require_tiered()
        tiered.set_session_value(key, value)


@dataclass
class AgentTurnOutcome:
    assistant_message: AgentMessage
    tool_results: List[ToolResult]


class ToolHandler(Protocol):
    async def __call__(self, context: ToolContext, call: ToolCall) -> ToolResult:
        ...


@dataclass
class ToolRegistry:
    _tools: Dict[str, ToolSpec] = field(default_factory=dict)
    _handlers: Dict[str, ToolHandler] = field(default_factory=dict)

    def register(self, spec: ToolSpec, handler: ToolHandler) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Tool '{spec.name}' already registered")
        self._tools[spec.name] = spec
        self._handlers[spec.name] = handler

    def specs(self) -> List[ToolSpec]:
        return list(self._tools.values())

    async def execute(self, context: ToolContext, call: ToolCall) -> ToolResult:
        handler = self._handlers.get(call.name)
        if handler is None:
            return ToolResult(
                tool_call_id=call.id,
                name=call.name,
                status=ToolTaskState.FAILED,
                error=f"Unknown tool: {call.name}",
            )
        try:
            result = await handler(context, call)
            if not isinstance(result, ToolResult):
                return ToolResult(
                    tool_call_id=call.id,
                    name=call.name,
                    output={"result": result},
                )
            return result
        except Exception as exc:
            return ToolResult(
                tool_call_id=call.id,
                name=call.name,
                status=ToolTaskState.FAILED,
                error=str(exc),
            )
