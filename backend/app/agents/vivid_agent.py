"""Chat-first agent core for 3-Layer Ecosystem."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Optional, Protocol

from app.agents.agent_types import (
    AgentMessage,
    AgentRole,
    AgentState,
    AgentTurnOutcome,
    ToolContext,
    ToolRegistry,
    ToolSpec,
)
from app.agents.notebooklm_tools import register_notebooklm_tools
from app.agents.teaching_tools import register_teaching_tools
from app.agents.workflow_tools import register_workflow_tools
from app.agents.intent_router import classify_intent, get_intent_router
from app.logging_config import get_logger

logger = get_logger("vivid_agent")


class ModelClientProtocol(Protocol):
    async def complete(
        self,
        messages: List[AgentMessage],
        tools: List[ToolSpec],
    ) -> AgentMessage:
        ...


@dataclass
class MemoryManager:
    max_messages: int = 24
    max_summary_chars: int = 1200
    max_item_chars: int = 200

    def build_context(
        self,
        state: AgentState,
        system_prompt: Optional[str] = None,
    ) -> List[AgentMessage]:
        if len(state.messages) > self.max_messages:
            overflow = state.messages[:-self.max_messages]
            state.messages = state.messages[-self.max_messages :]
            state.summary = self._summarize(overflow, state.summary)

        context: List[AgentMessage] = []
        if system_prompt:
            context.append(AgentMessage(role=AgentRole.SYSTEM, content=system_prompt))
        if state.summary:
            context.append(
                AgentMessage(
                    role=AgentRole.SYSTEM,
                    content=f"Conversation summary: {state.summary}",
                )
            )
        if state.metadata:
            try:
                metadata_str = json.dumps(state.metadata, ensure_ascii=True)
            except TypeError:
                metadata_str = str(state.metadata)
            if len(metadata_str) > self.max_summary_chars:
                metadata_str = f"{metadata_str[: self.max_summary_chars]}..."
            context.append(
                AgentMessage(
                    role=AgentRole.SYSTEM,
                    content=f"Session metadata: {metadata_str}",
                )
            )
        context.extend(state.messages)
        return context

    def _summarize(self, messages: List[AgentMessage], previous: Optional[str]) -> str:
        lines: List[str] = []
        if previous:
            lines.append(previous)
        for msg in messages:
            snippet = msg.content.replace("\n", " ").strip()
            if len(snippet) > self.max_item_chars:
                snippet = f"{snippet[: self.max_item_chars]}..."
            lines.append(f"{msg.role.value}: {snippet}")
        summary = " | ".join(lines)
        if len(summary) > self.max_summary_chars:
            summary = summary[-self.max_summary_chars :]
        return summary


class VividAgent:
    """Core chat-first agent with Teaching Tools and NotebookLM RAG."""

    def __init__(
        self,
        model_client: ModelClientProtocol,
        *,
        tool_registry: Optional[ToolRegistry] = None,
        memory_manager: Optional[MemoryManager] = None,
        system_prompt: Optional[str] = None,
        max_tool_rounds: int = 3,
    ) -> None:
        self._model = model_client
        self._tools = tool_registry or ToolRegistry()
        if tool_registry is None:
            # 3-Layer Ecosystem: Teaching + NotebookLM + Workflow
            register_teaching_tools(self._tools)
            register_notebooklm_tools(self._tools)
            register_workflow_tools(self._tools)
        self._memory = memory_manager or MemoryManager()
        self._system_prompt = system_prompt
        self._max_tool_rounds = max_tool_rounds

    @property
    def model_client(self) -> ModelClientProtocol:
        return self._model

    @property
    def tool_registry(self) -> ToolRegistry:
        return self._tools

    @property
    def memory_manager(self) -> MemoryManager:
        return self._memory

    @property
    def system_prompt(self) -> Optional[str]:
        return self._system_prompt

    @property
    def max_tool_rounds(self) -> int:
        return self._max_tool_rounds

    async def handle_user_message(
        self,
        state: AgentState,
        content: str,
    ) -> AgentTurnOutcome:
        """Handle user message with intent routing."""
        # Intent 분류 및 라우팅 컨텍스트 생성
        routing_result = classify_intent(content)
        
        if routing_result.is_confident:
            # 높은 신뢰도: 라우팅 힌트를 메타데이터에 추가
            if state.metadata is None:
                state.metadata = {}
            state.metadata["routing_hint"] = {
                "intent": routing_result.intent.value,
                "confidence": routing_result.confidence,
                "suggested_tool": routing_result.suggested_tool,
                "dimension": routing_result.dimension.value if routing_result.dimension else None,
            }
            if routing_result.workflow_suggestion:
                state.metadata["routing_hint"]["workflow"] = routing_result.workflow_suggestion
            
            logger.info(
                "Intent routing applied",
                extra={
                    "session_id": state.session_id,
                    "intent": routing_result.intent.value,
                    "confidence": routing_result.confidence,
                    "tool": routing_result.suggested_tool,
                },
            )
        
        state.messages.append(AgentMessage(role=AgentRole.USER, content=content))
        return await self._run_turn(state)

    async def _run_turn(self, state: AgentState) -> AgentTurnOutcome:
        tool_results = []
        assistant_message = None
        for round_idx in range(self._max_tool_rounds + 1):
            context = self._memory.build_context(state, self._system_prompt)
            try:
                assistant_message = await self._model.complete(
                    context,
                    self._tools.specs(),
                )
            except Exception as exc:
                logger.exception("Model call failed", extra={"error": str(exc)})
                assistant_message = AgentMessage(
                    role=AgentRole.ASSISTANT,
                    content="Model error: unable to generate a response.",
                )
                state.messages.append(assistant_message)
                return AgentTurnOutcome(
                    assistant_message=assistant_message,
                    tool_results=tool_results,
                )

            state.messages.append(assistant_message)
            if not assistant_message.tool_calls:
                break

            tool_context = ToolContext(state=state)
            for call in assistant_message.tool_calls:
                result = await self._tools.execute(tool_context, call)
                tool_results.append(result)
                state.messages.append(
                    AgentMessage(
                        role=AgentRole.TOOL,
                        content=result.to_message_content(),
                        tool_call_id=call.id,
                        name=call.name,
                    )
                )
            if round_idx >= self._max_tool_rounds:
                logger.warning(
                    "Max tool rounds reached",
                    extra={"session_id": state.session_id},
                )
                break

        if assistant_message is None:
            assistant_message = AgentMessage(
                role=AgentRole.ASSISTANT,
                content="",
            )
        return AgentTurnOutcome(
            assistant_message=assistant_message,
            tool_results=tool_results,
        )
