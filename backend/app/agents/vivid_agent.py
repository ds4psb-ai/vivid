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
        
        # Inject page context hint for context-aware responses
        if state.metadata and state.metadata.get("page_context"):
            page_context = state.metadata["page_context"]
            page_hint = self._get_page_hint(page_context)
            if page_hint:
                context.append(
                    AgentMessage(
                        role=AgentRole.SYSTEM,
                        content=f"[Page Context] 사용자가 현재 {page_hint}에 있습니다. 해당 페이지의 기능과 관련된 도움을 제공하세요.",
                    )
                )
        
        if state.metadata:
            # Filter out page_context from metadata string (already handled above)
            filtered_metadata = {k: v for k, v in state.metadata.items() if k != "page_context"}
            if filtered_metadata:
                try:
                    metadata_str = json.dumps(filtered_metadata, ensure_ascii=True)
                except TypeError:
                    metadata_str = str(filtered_metadata)
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
    
    def _get_page_hint(self, page_context: str) -> str:
        """Get human-readable page hint for context injection."""
        PAGE_HINTS = {
            "/dimension": "차원문(미니앱) 갤러리 - AI 도구들 (프롬프트 생성, 스토리보드, 이미지 등)",
            "/flow": "차원 흐름 디자이너 - 워크플로우 설계",
            "/singularity": "싱귤래리티 템플릿 갤러리 - 워크플로우 템플릿 탐색/적용",
            "/tools": "도구 대시보드 - 사용자 도구 관리/생성/Fork",
            "/tools/create": "새 도구 생성 페이지",
            "/humancloud": "휴먼클라우드 마켓플레이스 - 크리에이티브 요청/크리에이터 매칭",
            "/humancloud/requests": "요청 목록 페이지",
            "/settings": "설정 페이지 - API 키, 알림, 프로필",
            "/credits": "크레딧 관리 페이지 - 충전, 사용 내역, BYOK",
            "/crebit": "Crebit 구독/결제 페이지",
            "/admin": "관리자 대시보드",
            # Original Dimension Capsules
            "/dimension/prompt": "1D 프롬프트 생성기 - Veo 영상 프롬프트 생성",
            "/dimension/storyboard": "2D 스토리보드 아키텍트 - 씬 구조화",
            "/dimension/image-tool": "3D 비주얼 스튜디오 - 이미지 프롬프트 생성",
            "/dimension/shot-catch": "4D 프레임 캐쳐 - 레퍼런스 분석",
            # Extended Dimension Capsules
            "/dimension/quality-check": "QC 퀄리티 검수기 - 콘텐츠 품질 평가 (6가지 기준)",
            "/dimension/aesthetic": "AD 미학디렉터 - 거장 감독 스타일 가이드 생성",
            "/dimension/abyss": "AI 심연해석기 - 페르소나/심층 분석",
            "/dimension/veo-video": "VEO 비디오 생성 - Veo 3.1 AI 영상 생성",
        }
        # Exact match first
        if page_context in PAGE_HINTS:
            return PAGE_HINTS[page_context]
        # Partial match
        for path, hint in PAGE_HINTS.items():
            if page_context.startswith(path):
                return hint
        return ""

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
