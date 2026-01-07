"""Chat-first agent core for 3-Layer Ecosystem."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import List, Optional, Protocol, Set

from app.agents.agent_types import (
    AgentMessage,
    AgentRole,
    AgentState,
    AgentTurnOutcome,
    ToolContext,
    ToolRegistry,
    ToolResult,
    ToolSpec,
    ToolTaskState,
)
from app.agents.notebooklm_tools import register_notebooklm_tools
from app.agents.dimension_tools import register_dimension_tools
from app.agents.workflow_tools import register_workflow_tools
from app.agents.navigation_tools import register_navigation_tools
from app.agents.singularity_tools import register_singularity_tools
from app.agents.humancloud_tools import register_humancloud_tools
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
    """P1-3: Enhanced memory manager with token-aware context building.
    
    Features:
    - Approximate token counting for Gemini models
    - Dynamic message compression based on token budget
    - Priority-based context allocation
    - Intelligent summarization of old messages
    """
    
    # Token budget configuration
    max_tokens: int = 28000         # Safe limit for Gemini (32K context - 4K buffer)
    system_prompt_budget: int = 4000  # Reserved for system prompts
    message_budget: int = 20000       # For conversation history
    summary_budget: int = 2000        # For compression/summary
    
    # Backwards-compatible settings
    max_messages: int = 24
    max_summary_chars: int = 1200
    max_item_chars: int = 200
    
    # Token estimation constants (Gemini-optimized)
    CHARS_PER_TOKEN: float = 3.5  # Korean/English mix average
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.
        
        Uses character-based approximation optimized for Korean/English mix.
        More accurate than len(text)//4 for mixed content.
        """
        if not text:
            return 0
        return int(len(text) / self.CHARS_PER_TOKEN)
    
    def estimate_message_tokens(self, message: AgentMessage) -> int:
        """Estimate tokens for a single message including overhead."""
        base_tokens = self.estimate_tokens(message.content)
        # Add overhead for role, tool calls, etc.
        overhead = 10  # tokens for role/formatting
        if message.tool_calls:
            overhead += len(message.tool_calls) * 50  # tool call overhead
        return base_tokens + overhead

    def build_context(
        self,
        state: AgentState,
        system_prompt: Optional[str] = None,
    ) -> List[AgentMessage]:
        """Build token-optimized context for LLM.
        
        P1-3: Prioritizes recent messages while respecting token budget.
        Compresses/summarizes older messages when needed.
        """
        context: List[AgentMessage] = []
        used_tokens = 0
        
        # 1. System prompt (highest priority)
        if system_prompt:
            system_tokens = self.estimate_tokens(system_prompt)
            context.append(AgentMessage(role=AgentRole.SYSTEM, content=system_prompt))
            used_tokens += system_tokens
        
        # 2. Build system context messages
        system_context_messages = self._build_system_context(state)
        for msg in system_context_messages:
            msg_tokens = self.estimate_message_tokens(msg)
            if used_tokens + msg_tokens <= self.system_prompt_budget:
                context.append(msg)
                used_tokens += msg_tokens
        
        # 3. Calculate remaining budget for conversation
        remaining_budget = self.max_tokens - used_tokens
        
        # 4. Select messages with token budget
        selected_messages, overflow = self._select_messages_by_budget(
            state.messages, 
            remaining_budget
        )
        
        # 5. If overflow, create/update summary
        if overflow:
            state.summary = self._summarize_smart(overflow, state.summary)
            
        # 6. Add summary if exists
        if state.summary:
            summary_msg = AgentMessage(
                role=AgentRole.SYSTEM,
                content=f"[Conversation Summary] {state.summary}",
            )
            summary_tokens = self.estimate_message_tokens(summary_msg)
            if summary_tokens <= self.summary_budget:
                context.append(summary_msg)
        
        # 7. Add selected messages
        context.extend(selected_messages)
        
        # Debug logging
        total_tokens = sum(self.estimate_message_tokens(m) for m in context)
        logger.debug(
            f"Context built: {len(context)} messages, ~{total_tokens} tokens "
            f"(budget: {self.max_tokens})"
        )
        
        return context
    
    def _build_system_context(self, state: AgentState) -> List[AgentMessage]:
        """Build system context messages from state metadata."""
        messages: List[AgentMessage] = []
        
        # Page context
        if state.metadata and state.metadata.get("page_context"):
            page_context = state.metadata["page_context"]
            page_hint = self._get_page_hint(page_context)
            if page_hint:
                messages.append(AgentMessage(
                    role=AgentRole.SYSTEM,
                    content=f"[Page Context] 사용자가 현재 {page_hint}에 있습니다.",
                ))
        
        # Template context
        if state.metadata and state.metadata.get("template"):
            template = state.metadata["template"]
            template_hint = self._build_template_hint(template)
            if template_hint:
                messages.append(AgentMessage(
                    role=AgentRole.SYSTEM,
                    content=template_hint,
                ))
        
        # Routing hint (concise)
        if state.metadata and state.metadata.get("routing_hint"):
            hint = state.metadata["routing_hint"]
            intent = hint.get("intent", "unknown")
            tool = hint.get("suggested_tool", "")
            if tool:
                messages.append(AgentMessage(
                    role=AgentRole.SYSTEM,
                    content=f"[Routing] User intent is '{intent}'. You MUST use the tool '{tool}' immediately. Do not ask for confirmation or mention buttons.",
                ))
        
        # Other metadata (compressed)
        if state.metadata:
            skip_keys = {"page_context", "template", "routing_hint", "auto_context"}
            filtered = {k: v for k, v in state.metadata.items() if k not in skip_keys}
            if filtered:
                try:
                    meta_str = json.dumps(filtered, ensure_ascii=False)[:500]
                    messages.append(AgentMessage(
                        role=AgentRole.SYSTEM,
                        content=f"[Session] {meta_str}",
                    ))
                except (TypeError, ValueError):
                    pass
        
        return messages
    
    def _select_messages_by_budget(
        self, 
        messages: List[AgentMessage], 
        budget: int
    ) -> tuple[List[AgentMessage], List[AgentMessage]]:
        """Select messages that fit within token budget.
        
        Prioritizes recent messages. Returns (selected, overflow).
        """
        if not messages:
            return [], []
        
        selected: List[AgentMessage] = []
        overflow: List[AgentMessage] = []
        used_tokens = 0
        
        # Process from newest to oldest
        for msg in reversed(messages):
            msg_tokens = self.estimate_message_tokens(msg)
            if used_tokens + msg_tokens <= budget:
                selected.insert(0, msg)  # Maintain order
                used_tokens += msg_tokens
            else:
                overflow.insert(0, msg)  # Maintain order
        
        return selected, overflow
    
    def _summarize_smart(
        self, 
        messages: List[AgentMessage], 
        previous_summary: Optional[str]
    ) -> str:
        """Create intelligent summary of overflow messages.
        
        Groups by role, extracts key information, respects size limits.
        """
        if not messages:
            return previous_summary or ""
        
        parts: List[str] = []
        
        # Keep previous summary
        if previous_summary:
            # Truncate old summary if too long
            if len(previous_summary) > self.max_summary_chars // 2:
                previous_summary = previous_summary[-(self.max_summary_chars // 2):]
            parts.append(previous_summary)
        
        # Summarize new messages by role
        user_msgs = [m for m in messages if m.role == AgentRole.USER]
        assistant_msgs = [m for m in messages if m.role == AgentRole.ASSISTANT]
        tool_msgs = [m for m in messages if m.role == AgentRole.TOOL]
        
        # User message summary
        if user_msgs:
            user_snippets = []
            for msg in user_msgs[-3:]:  # Last 3 user messages
                snippet = msg.content.replace("\n", " ").strip()[:100]
                if snippet:
                    user_snippets.append(snippet)
            if user_snippets:
                parts.append(f"User: {' → '.join(user_snippets)}")
        
        # Tool execution summary
        if tool_msgs:
            tool_names = []
            for msg in tool_msgs[-5:]:  # Last 5 tool results
                if msg.name:
                    tool_names.append(msg.name)
            if tool_names:
                parts.append(f"Tools used: {', '.join(set(tool_names))}")
        
        # Assistant summary (very brief)
        if assistant_msgs:
            last_response = assistant_msgs[-1].content.replace("\n", " ").strip()
            if last_response:
                parts.append(f"Last response: {last_response[:150]}...")
        
        summary = " | ".join(parts)
        
        # Enforce max length
        if len(summary) > self.max_summary_chars:
            summary = summary[-self.max_summary_chars:]
        
        return summary
    
    def _build_template_hint(self, template: dict) -> str:
        """Build template context hint for Singularity templates."""
        try:
            if not isinstance(template, dict):
                return ""

            title = template.get("title")
            if not title or not isinstance(title, str):
                return ""
            title = title.strip()[:100]
            if not title:
                return ""

            hint_parts = [f"[Template] '{title}'"]

            description = template.get("description")
            if description and isinstance(description, str):
                safe_desc = description.strip()[:200]
                if safe_desc:
                    hint_parts.append(f"설명: {safe_desc}")

            tool_sequence = template.get("tool_sequence")
            if tool_sequence and isinstance(tool_sequence, list):
                safe_sequence = [str(item)[:20] for item in tool_sequence[:8] if item]
                if safe_sequence:
                    hint_parts.append(f"순서: {' → '.join(safe_sequence)}")

            return " | ".join(hint_parts)

        except Exception as e:
            logger.warning(f"Failed to build template hint: {e}")
            return ""

    def _get_page_hint(self, page_context: str) -> str:
        """Get human-readable page hint for context injection."""
        PAGE_HINTS = {
            "/dimension": "차원문(미니앱) 갤러리",
            "/flow": "차원 흐름 디자이너",
            "/singularity": "싱귤래리티 템플릿 갤러리",
            "/tools": "도구 대시보드",
            "/humancloud": "휴먼클라우드",
            "/settings": "설정",
            "/credits": "크레딧 관리",
            "/crebit": "Crebit 구독",
            "/admin": "관리자 대시보드",
            "/dimension/prompt": "1D 프롬프트 생성기",
            "/dimension/storyboard": "2D 스토리보드",
            "/dimension/image-tool": "3D 비주얼 스튜디오",
            "/dimension/shot-catch": "4D 프레임 캐쳐",
            "/dimension/quality-check": "QC 퀄리티 검수기",
            "/dimension/aesthetic": "AD 미학디렉터",
            "/dimension/abyss": "AI 심연해석기",
            "/dimension/veo-video": "VEO 비디오 생성",
        }
        if page_context in PAGE_HINTS:
            return PAGE_HINTS[page_context]
        for path, hint in PAGE_HINTS.items():
            if page_context.startswith(path):
                return hint
        return ""

    def _summarize(self, messages: List[AgentMessage], previous: Optional[str]) -> str:
        """Legacy summarize method for backwards compatibility."""
        return self._summarize_smart(messages, previous)


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
            # Full Ecosystem: Teaching + NotebookLM + Workflow + Navigation + Singularity + HumanCloud
            register_dimension_tools(self._tools)
            register_notebooklm_tools(self._tools)
            register_workflow_tools(self._tools)
            register_navigation_tools(self._tools)
            register_singularity_tools(self._tools)
            register_humancloud_tools(self._tools)
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

    # P0-2: Recoverable error types for retry logic
    RECOVERABLE_ERRORS: Set[str] = {
        "timeout", "rate_limit", "temporary_failure", 
        "connection_error", "service_unavailable"
    }

    def _classify_error(self, error: Optional[str]) -> str:
        """Classify error type for retry decision."""
        if not error:
            return "unknown"
        error_lower = error.lower()
        if "timeout" in error_lower:
            return "timeout"
        if "rate" in error_lower and "limit" in error_lower:
            return "rate_limit"
        if "temporary" in error_lower or "transient" in error_lower:
            return "temporary_failure"
        if "connection" in error_lower:
            return "connection_error"
        if "unavailable" in error_lower or "503" in error_lower:
            return "service_unavailable"
        return "permanent_failure"

    async def _execute_tool_with_retry(
        self,
        tool_context: ToolContext,
        call,
        timeout_seconds: float = 120.0,
        max_retries: int = 2,
    ) -> ToolResult:
        """Execute tool with timeout and retry logic.
        
        P0-2: Adds resilience to tool execution with:
        - Configurable timeout (default 120s)
        - Retry for recoverable errors (max 2 retries)
        - Exponential backoff between retries
        """
        for attempt in range(max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    self._tools.execute(tool_context, call),
                    timeout=timeout_seconds,
                )
                
                # Check if tool itself reported a failure that's recoverable
                if result.status == ToolTaskState.FAILED and result.error:
                    error_type = self._classify_error(result.error)
                    if error_type in self.RECOVERABLE_ERRORS and attempt < max_retries:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logger.warning(
                            f"Tool {call.name} failed with recoverable error (attempt {attempt + 1}/{max_retries + 1}), "
                            f"retrying in {wait_time}s: {result.error}"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                
                return result
                
            except asyncio.TimeoutError:
                logger.error(
                    f"Tool {call.name} execution timed out after {timeout_seconds}s (attempt {attempt + 1})"
                )
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying tool {call.name} in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                    
                return ToolResult(
                    tool_call_id=call.id,
                    name=call.name,
                    status=ToolTaskState.FAILED,
                    error=f"Tool execution timed out after {timeout_seconds}s",
                )
                
            except Exception as exc:
                logger.exception(f"Tool {call.name} execution error: {exc}")
                error_type = self._classify_error(str(exc))
                
                if error_type in self.RECOVERABLE_ERRORS and attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"Retrying tool {call.name} in {wait_time}s due to: {exc}")
                    await asyncio.sleep(wait_time)
                    continue
                
                return ToolResult(
                    tool_call_id=call.id,
                    name=call.name,
                    status=ToolTaskState.FAILED,
                    error=f"Tool execution error: {type(exc).__name__}: {str(exc)}",
                )
        
        # Should not reach here, but safety fallback
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.FAILED,
            error="Tool execution failed after all retries",
        )

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
                result = await self._execute_tool_with_retry(
                    tool_context, call, timeout_seconds=120.0, max_retries=2
                )
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
