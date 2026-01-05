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
        """Set session-level value (persists across steps)."""
        self.session[key] = value

    def register_handle(self, key: str, handle_ref: HandleRef) -> None:
        """Register a handle reference for large data."""
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
        """Deserialize from storage."""
        history = [StepSummary(**s) for s in data.get("history", [])]
        return cls(
            session=data.get("session", {}),
            step=data.get("step", {}),
            history=history,
            handles=data.get("handles", {}),
            current_step_index=data.get("current_step_index", 0),
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
