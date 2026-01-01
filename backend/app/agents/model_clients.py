"""Model clients for agent development."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Iterator, List, Optional
from uuid import uuid4

from app.agents.agent_types import AgentMessage, AgentRole, ToolCall, ToolSpec
from app.config import settings

logger = logging.getLogger(__name__)


class GeminiModelClient:
    """Gemini client that returns JSON responses with optional tool calls."""

    def __init__(
        self,
        *,
        model_name: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.4,
        max_output_tokens: int = 2048,
    ) -> None:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set")
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise ImportError("google-generativeai not installed") from exc

        self._genai = genai
        self._genai.configure(api_key=settings.GEMINI_API_KEY)
        self._system_prompt = system_prompt or (
            "You are Vivid Studio's chat-first agent. Use tools to build workflows and artifacts. "
            "Call compile_workflow when the user asks for workflows, nodes, or a video plan. "
            "Call run_capsule to execute a capsule or generate production outputs. "
            "Call analyze_sources when the user provides sources or asks for analysis. "
            "Call generate_storyboard when asked for storyboard previews. "
            "If session metadata includes a canvas_snapshot, use it to align responses with the current canvas. "
            "Respond ONLY with JSON: {\"content\": \"...\", \"tool_calls\": "
            "[{\"id\": \"optional\", \"name\": \"tool_name\", \"arguments\": {}}]}. "
            "Always put the 'content' field first. Use empty tool_calls when none."
        )
        self._model_name = model_name
        self._generation_config = {
            "temperature": temperature,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": max_output_tokens,
            "response_mime_type": "application/json",
        }
        self._model = self._build_model()

    async def complete(
        self,
        messages: List[AgentMessage],
        tools: List[ToolSpec],
    ) -> AgentMessage:
        prompt = self._build_prompt(messages, tools)
        response = self._model.generate_content(prompt)
        text = (response.text or "").strip()
        return self._build_message(text, tools)

    def stream_generate(
        self,
        messages: List[AgentMessage],
        tools: List[ToolSpec],
    ) -> Iterator[str]:
        prompt = self._build_prompt(messages, tools)
        model = self._build_model()
        stream = model.generate_content(prompt, stream=True)
        parser = JSONContentStreamParser()
        raw_text = ""
        for chunk in stream:
            chunk_text = (chunk.text or "")
            if not chunk_text:
                continue
            raw_text += chunk_text
            delta = parser.feed(chunk_text)
            if delta:
                yield delta

        return self._build_message(raw_text, tools, parser.content)

    def _build_model(self):
        return self._genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=self._system_prompt,
            generation_config=self._generation_config,
        )

    def _build_prompt(self, messages: List[AgentMessage], tools: List[ToolSpec]) -> str:
        tool_lines = []
        for tool in tools:
            tool_lines.append(
                f"- {tool.name}: {tool.description}\n  input_schema: "
                f"{json.dumps(tool.input_schema, ensure_ascii=True)}"
            )
        tools_section = "\n".join(tool_lines) if tool_lines else "- none"

        convo_lines = []
        for message in messages:
            role = message.role.value.upper()
            if message.role == AgentRole.TOOL:
                name = message.name or "tool"
                convo_lines.append(f"{role}({name}): {message.content}")
            else:
                convo_lines.append(f"{role}: {message.content}")
        conversation = "\n".join(convo_lines)

        return (
            "Available tools:\n"
            f"{tools_section}\n\n"
            "Conversation:\n"
            f"{conversation}\n\n"
            "Return JSON only."
        )

    def _parse_json(self, text: str) -> Dict[str, Any]:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`").strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(cleaned[start : end + 1])
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

        logger.warning("Gemini response is not JSON", extra={"response": text[:200]})
        return {"content": text, "tool_calls": []}

    def _parse_tool_calls(
        self,
        parsed: Dict[str, Any],
        tools: List[ToolSpec],
    ) -> List[ToolCall]:
        if not isinstance(parsed, dict):
            return []
        raw_calls = parsed.get("tool_calls") or parsed.get("toolCalls") or []
        if not isinstance(raw_calls, list):
            return []
        tool_names = {tool.name for tool in tools}
        calls: List[ToolCall] = []
        for raw in raw_calls:
            if not isinstance(raw, dict):
                continue
            name = raw.get("name")
            if not name or name not in tool_names:
                continue
            arguments = raw.get("arguments")
            if not isinstance(arguments, dict):
                arguments = {}
            call_id = raw.get("id") or f"call_{uuid4().hex[:8]}"
            calls.append(ToolCall(id=call_id, name=name, arguments=arguments))
        return calls

    def _build_message(
        self,
        raw_text: str,
        tools: List[ToolSpec],
        fallback_content: Optional[str] = None,
    ) -> AgentMessage:
        parsed = self._parse_json(raw_text)
        tool_calls = self._parse_tool_calls(parsed, tools)
        content = parsed.get("content") if isinstance(parsed, dict) else None
        if not content:
            content = fallback_content or ""
        if not isinstance(content, str):
            content = str(content)
        return AgentMessage(
            role=AgentRole.ASSISTANT,
            content=content,
            tool_calls=tool_calls,
        )


class JSONContentStreamParser:
    def __init__(self) -> None:
        self.buffer = ""
        self.cursor = 0
        self.content_started = False
        self.content_ended = False
        self.escape = False
        self.unicode_escape: Optional[str] = None
        self.content = ""

    def feed(self, text: str) -> str:
        if self.content_ended:
            return ""
        self.buffer += text

        if not self.content_started:
            key_index = self.buffer.find("\"content\"")
            if key_index == -1:
                return ""
            colon_index = self.buffer.find(":", key_index)
            if colon_index == -1:
                return ""
            quote_index = self.buffer.find("\"", colon_index)
            if quote_index == -1:
                return ""
            self.content_started = True
            self.cursor = quote_index + 1

        emitted = []
        while self.cursor < len(self.buffer):
            ch = self.buffer[self.cursor]
            self.cursor += 1

            if self.unicode_escape is not None:
                if ch.lower() in "0123456789abcdef":
                    self.unicode_escape += ch
                    if len(self.unicode_escape) == 4:
                        try:
                            emitted.append(chr(int(self.unicode_escape, 16)))
                        except ValueError:
                            emitted.append("")
                        self.unicode_escape = None
                else:
                    self.unicode_escape = None
                continue

            if self.escape:
                self.escape = False
                if ch == "u":
                    self.unicode_escape = ""
                    continue
                mapping = {
                    "\"": "\"",
                    "\\": "\\",
                    "/": "/",
                    "n": "\n",
                    "r": "\r",
                    "t": "\t",
                    "b": "\b",
                    "f": "\f",
                }
                emitted.append(mapping.get(ch, ch))
                continue

            if ch == "\\":
                self.escape = True
                continue
            if ch == "\"":
                self.content_ended = True
                break
            emitted.append(ch)

        delta = "".join(emitted)
        if delta:
            self.content += delta
        return delta


class StubModelClient:
    """Deterministic model stub for wiring agent flows without an LLM."""

    async def complete(
        self,
        messages: List[AgentMessage],
        tools: List[ToolSpec],
    ) -> AgentMessage:
        user_text = ""
        for message in reversed(messages):
            if message.role == AgentRole.USER:
                user_text = (message.content or "").strip()
                break

        if not user_text:
            return AgentMessage(
                role=AgentRole.ASSISTANT,
                content="Tell me what you want to build.",
            )

        if messages and messages[-1].role == AgentRole.TOOL:
            return AgentMessage(
                role=AgentRole.ASSISTANT,
                content="Tool results received. Review the draft and let me know changes.",
            )

        tool_names = {tool.name for tool in tools}
        lowered = user_text.lower()
        if "create_scene" in tool_names and "scene" in lowered:
            call = ToolCall(
                id=f"call_{uuid4().hex[:8]}",
                name="create_scene",
                arguments={
                    "title": "Scene Draft",
                    "summary": user_text,
                },
            )
            return AgentMessage(
                role=AgentRole.ASSISTANT,
                content="Drafting a scene from your request.",
                tool_calls=[call],
            )

        return AgentMessage(
            role=AgentRole.ASSISTANT,
            content=f"Noted: {user_text}",
        )
