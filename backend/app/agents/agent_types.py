"""Shared agent types and tool registry primitives."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol

from pydantic import BaseModel, Field


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


class ToolSpec(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None


@dataclass
class AgentState:
    session_id: str
    messages: List[AgentMessage] = field(default_factory=list)
    summary: Optional[str] = None
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolContext:
    state: AgentState
    emit_event: Optional[Callable[[str, Dict[str, Any]], None]] = None

    @property
    def session_id(self) -> str:
        return self.state.session_id


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
