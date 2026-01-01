"""Agent chat API endpoints."""
from __future__ import annotations

import asyncio
import json
import threading
import uuid
from datetime import datetime
from typing import AsyncGenerator, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.agent_types import AgentMessage as CoreAgentMessage
from app.agents.agent_types import AgentRole, AgentState, ToolCall, ToolContext
from app.agents.model_clients import GeminiModelClient, StubModelClient
from app.agents.artifact_backfill import derive_artifacts_from_tool_payload
from app.agents.vivid_agent import VividAgent
from app.config import settings
from app.database import get_db
from app.logging_config import get_logger
from app.models import AgentArtifact, AgentMessage as AgentMessageRecord, AgentSession

router = APIRouter(prefix="/agent", tags=["agent"])
logger = get_logger("agent_router")


def _build_agent(model_name: Optional[str] = None) -> VividAgent:
    selected_model = model_name or settings.GEMINI_AGENT_MODEL
    if settings.GEMINI_ENABLED and settings.GEMINI_API_KEY:
        try:
            return VividAgent(
                model_client=GeminiModelClient(
                    model_name=selected_model,
                    temperature=settings.GEMINI_AGENT_TEMPERATURE,
                    max_output_tokens=settings.GEMINI_AGENT_MAX_TOKENS,
                )
            )
        except Exception as exc:
            logger.warning(
                "Gemini model init failed, using stub",
                extra={"error": str(exc)},
            )
    return VividAgent(model_client=StubModelClient())


_AGENT_CACHE: dict[str, VividAgent] = {}


def _get_agent(model_name: str) -> VividAgent:
    cached = _AGENT_CACHE.get(model_name)
    if cached is not None:
        return cached
    agent = _build_agent(model_name)
    _AGENT_CACHE[model_name] = agent
    return agent


class AgentChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1)
    metadata: Optional[dict] = None
    model: Optional[str] = None


class AgentDecisionRequest(BaseModel):
    note: Optional[str] = None
    metadata: Optional[dict] = None


class AgentMessageResponse(BaseModel):
    message_id: str
    role: str
    content: str
    tool_calls: List[dict] = Field(default_factory=list)
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    created_at: datetime


class AgentArtifactResponse(BaseModel):
    artifact_id: str
    artifact_type: str
    payload: dict
    version: int
    created_at: datetime
    updated_at: datetime


class AgentSessionResponse(BaseModel):
    session_id: str
    status: str
    title: Optional[str] = None
    agent_model: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    messages: List[AgentMessageResponse] = Field(default_factory=list)
    artifacts: List[AgentArtifactResponse] = Field(default_factory=list)


class AgentSessionStatusResponse(BaseModel):
    session_id: str
    status: str
    metadata: dict = Field(default_factory=dict)
    updated_at: datetime


def _merge_metadata(base: Optional[dict], patch: Optional[dict]) -> dict:
    merged = dict(base or {})
    if patch:
        merged.update(patch)
    return merged


def _resolve_agent_model(session: AgentSession, request: AgentChatRequest) -> str:
    if request.model:
        return _validate_agent_model(request.model)
    stored = (session.meta or {}).get("agent_model")
    if stored:
        return _coerce_agent_model(stored)
    return settings.GEMINI_AGENT_MODEL


def _allowed_agent_models() -> set[str]:
    models = set(settings.ALLOWED_GEMINI_AGENT_MODELS or [])
    if settings.GEMINI_AGENT_MODEL:
        models.add(settings.GEMINI_AGENT_MODEL)
    return models


def _validate_agent_model(model_name: str) -> str:
    allowed = _allowed_agent_models()
    if model_name not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model. Allowed: {sorted(allowed)}",
        )
    return model_name


def _coerce_agent_model(model_name: str) -> str:
    allowed = _allowed_agent_models()
    if model_name in allowed:
        return model_name
    logger.warning(
        "Agent model not allowed, using default",
        extra={"requested": model_name, "default": settings.GEMINI_AGENT_MODEL},
    )
    return settings.GEMINI_AGENT_MODEL


def _format_sse(event_type: str, data: dict) -> str:
    return (
        f"id: {data['event_id']}\n"
        f"event: {event_type}\n"
        f"data: {json.dumps(data, ensure_ascii=True)}\n\n"
    )


def _build_event(
    session_id: str,
    seq: int,
    event_type: str,
    payload: dict,
    ts: str,
) -> dict:
    return {
        "event_id": f"{session_id}:{seq}",
        "session_id": session_id,
        "type": event_type,
        "seq": seq,
        "ts": ts,
        "payload": payload,
    }


def _chunk_text(text: str, size: int = 48) -> List[str]:
    return [text[i : i + size] for i in range(0, len(text), size)]


def _to_core_message(record: AgentMessageRecord) -> CoreAgentMessage:
    tool_calls = []
    for raw in record.tool_calls or []:
        if not isinstance(raw, dict):
            continue
        call_id = raw.get("id")
        name = raw.get("name")
        if not call_id or not name:
            continue
        tool_calls.append(
            ToolCall(
                id=call_id,
                name=name,
                arguments=raw.get("arguments") or {},
            )
        )
    try:
        role = AgentRole(record.role)
    except ValueError:
        role = AgentRole.ASSISTANT
    return CoreAgentMessage(
        role=role,
        content=record.content or "",
        tool_calls=tool_calls,
        tool_call_id=record.tool_call_id,
        name=record.name,
    )


def _tool_result_payload(result) -> dict:
    payload = {
        "tool_call_id": result.tool_call_id,
        "status": result.status.value,
        "output": result.output or {},
    }
    if result.error:
        payload["error"] = result.error
    if result.task_id:
        payload["task_id"] = result.task_id
    return payload


def _should_store_artifact(payload: dict) -> bool:
    return bool(payload.get("output")) or payload.get("error") or payload.get("task_id")


def _build_artifacts_from_result(result) -> List[dict]:
    tool_payload = _tool_result_payload(result)
    return derive_artifacts_from_tool_payload(result.name, tool_payload)


def _payload_fingerprint(payload: dict) -> str:
    try:
        return json.dumps(payload, sort_keys=True, default=str)
    except TypeError:
        return str(payload)


def _derive_missing_artifacts(artifacts: List[AgentArtifact]) -> List[AgentArtifactResponse]:
    derived: List[AgentArtifactResponse] = []
    existing_payloads = set()
    for artifact in artifacts:
        if isinstance(artifact.payload, dict):
            existing_payloads.add(_payload_fingerprint(artifact.payload))

    for artifact in artifacts:
        if not isinstance(artifact.payload, dict):
            continue
        if "artifact_type" in artifact.payload:
            continue
        for payload in derive_artifacts_from_tool_payload(artifact.artifact_type, artifact.payload):
            fingerprint = _payload_fingerprint(payload)
            if fingerprint in existing_payloads:
                continue
            existing_payloads.add(fingerprint)
            artifact_id = str(payload.get("artifact_id") or uuid.uuid4())
            payload["artifact_id"] = artifact_id
            derived.append(
                AgentArtifactResponse(
                    artifact_id=artifact_id,
                    artifact_type=payload.get("artifact_type", "artifact"),
                    payload=payload,
                    version=1,
                    created_at=artifact.created_at,
                    updated_at=artifact.updated_at,
                )
            )
    return derived


class _StreamResult:
    def __init__(self) -> None:
        self.message: Optional[CoreAgentMessage] = None
        self.error: Optional[Exception] = None


def _start_stream_thread(
    model_client: GeminiModelClient,
    messages: List[CoreAgentMessage],
    tools: List,
    queue: asyncio.Queue,
    result: _StreamResult,
    loop: asyncio.AbstractEventLoop,
) -> None:
    def _runner() -> None:
        try:
            generator = model_client.stream_generate(messages, tools)
            while True:
                try:
                    delta = next(generator)
                except StopIteration as stop:
                    result.message = stop.value
                    break
                if delta:
                    loop.call_soon_threadsafe(queue.put_nowait, delta)
        except Exception as exc:
            result.error = exc
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()


@router.post("/chat")
async def chat_agent(
    request: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
):
    session = None
    if request.session_id:
        try:
            session_uuid = uuid.UUID(request.session_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid session id") from exc
        result = await db.execute(select(AgentSession).where(AgentSession.id == session_uuid))
        session = result.scalars().first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        title = (request.message or "").strip()
        if len(title) > 80:
            title = f"{title[:77]}..."
        session = AgentSession(
            status="active",
            title=title or None,
            meta=request.metadata or {},
        )
        db.add(session)
        await db.flush()

    logger.info(
        "Agent chat request",
        extra={
            "session_id": str(session.id),
            "existing_session": bool(request.session_id),
        },
    )

    if request.metadata:
        session.meta = _merge_metadata(session.meta, request.metadata)
    model_name = _resolve_agent_model(session, request)
    session.meta = _merge_metadata(session.meta, {"agent_model": model_name})
    agent = _get_agent(model_name)

    existing_messages_result = await db.execute(
        select(AgentMessageRecord)
        .where(AgentMessageRecord.session_id == session.id)
        .order_by(AgentMessageRecord.created_at.asc())
    )
    existing_messages = existing_messages_result.scalars().all()
    state_messages = [_to_core_message(message) for message in existing_messages]
    state = AgentState(session_id=str(session.id), messages=state_messages, metadata=session.meta or {})

    user_content = request.message.strip()
    state.messages.append(CoreAgentMessage(role=AgentRole.USER, content=user_content))
    user_record = AgentMessageRecord(
        session_id=session.id,
        role="user",
        content=user_content,
        tool_calls=[],
    )
    db.add(user_record)
    await db.commit()
    await db.refresh(session)

    async def _event_stream() -> AsyncGenerator[str, None]:
        seq = 0
        now = f"{datetime.utcnow().isoformat()}Z"
        session_id = str(session.id)

        def _next_event(event_type: str, payload: dict) -> str:
            nonlocal seq
            seq += 1
            return _format_sse(
                event_type,
                _build_event(session_id, seq, event_type, payload, now),
            )

        yield _next_event(
            "agent.session",
            {
                "status": session.status,
                "title": session.title,
                "agent_model": model_name,
            },
        )

        tool_registry = agent.tool_registry
        memory = agent.memory_manager
        model_client = agent.model_client
        max_rounds = agent.max_tool_rounds

        for round_idx in range(max_rounds + 1):
            context = memory.build_context(state, agent.system_prompt)
            assistant_record = AgentMessageRecord(
                session_id=session.id,
                role="assistant",
                content="",
                tool_calls=[],
            )
            db.add(assistant_record)
            await db.commit()
            await db.refresh(assistant_record)
            assistant_message_id = str(assistant_record.id)

            yield _next_event(
                "agent.thinking",
                {"message_id": assistant_message_id},
            )

            assistant_message: Optional[CoreAgentMessage] = None
            assistant_tool_calls: List[dict] = []

            if isinstance(model_client, GeminiModelClient) and hasattr(model_client, "stream_generate"):
                queue: asyncio.Queue = asyncio.Queue()
                result = _StreamResult()
                loop = asyncio.get_running_loop()
                _start_stream_thread(
                    model_client,
                    context,
                    tool_registry.specs(),
                    queue,
                    result,
                    loop,
                )
                while True:
                    delta = await queue.get()
                    if delta is None:
                        break
                    yield _next_event(
                        "agent.delta",
                        {
                            "message_id": assistant_message_id,
                            "delta": delta,
                        },
                    )
                if result.error:
                    logger.warning(
                        "Gemini streaming failed",
                        extra={"error": str(result.error)},
                    )
                assistant_message = result.message
            else:
                assistant_message = await model_client.complete(context, tool_registry.specs())
                for chunk in _chunk_text(assistant_message.content or ""):
                    yield _next_event(
                        "agent.delta",
                        {
                            "message_id": assistant_message_id,
                            "delta": chunk,
                        },
                    )
                    await asyncio.sleep(0)

            if assistant_message is None:
                assistant_message = CoreAgentMessage(
                    role=AgentRole.ASSISTANT,
                    content="Model error: unable to generate a response.",
                )

            if assistant_message.tool_calls:
                assistant_tool_calls = [call.model_dump() for call in assistant_message.tool_calls]

            assistant_record.content = assistant_message.content or ""
            assistant_record.tool_calls = assistant_tool_calls
            await db.commit()

            if assistant_tool_calls:
                yield _next_event(
                    "agent.tool_calls",
                    {
                        "message_id": assistant_message_id,
                        "tool_calls": assistant_tool_calls,
                    },
                )

            yield _next_event(
                "agent.message",
                {
                    "message_id": assistant_message_id,
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": assistant_tool_calls,
                },
            )

            state.messages.append(assistant_message)
            if not assistant_message.tool_calls:
                break

            for call in assistant_message.tool_calls:
                tool_events: asyncio.Queue = asyncio.Queue()
                loop = asyncio.get_running_loop()

                def emit_event(event_type: str, payload: dict) -> None:
                    loop.call_soon_threadsafe(tool_events.put_nowait, (event_type, payload))

                tool_context = ToolContext(state=state, emit_event=emit_event)
                tool_task = asyncio.create_task(tool_registry.execute(tool_context, call))
                while True:
                    if tool_task.done():
                        break
                    try:
                        event_type, payload = await asyncio.wait_for(tool_events.get(), timeout=0.25)
                    except asyncio.TimeoutError:
                        continue
                    yield _next_event(event_type, payload)

                result = await tool_task
                await asyncio.sleep(0)
                while not tool_events.empty():
                    event_type, payload = tool_events.get_nowait()
                    yield _next_event(event_type, payload)
                tool_message_content = result.to_message_content()
                tool_record = AgentMessageRecord(
                    session_id=session.id,
                    role="tool",
                    content=tool_message_content,
                    tool_calls=[],
                    tool_call_id=call.id,
                    name=call.name,
                )
                db.add(tool_record)
                tool_payload = _tool_result_payload(result)
                if _should_store_artifact(tool_payload):
                    db.add(
                        AgentArtifact(
                            session_id=session.id,
                            artifact_type=result.name,
                            payload=tool_payload,
                            version=1,
                        )
                    )

                generated_artifacts: List[AgentArtifact] = []
                for artifact_payload in _build_artifacts_from_result(result):
                    artifact_type = artifact_payload.get("artifact_type", "artifact")
                    artifact = AgentArtifact(
                        session_id=session.id,
                        artifact_type=artifact_type,
                        payload=artifact_payload,
                        version=1,
                    )
                    db.add(artifact)
                    generated_artifacts.append(artifact)
                await db.commit()

                yield _next_event(
                    "agent.tool_result",
                    {**tool_payload, "name": result.name},
                )

                for artifact in generated_artifacts:
                    yield _next_event(
                        "agent.artifact_update",
                        {
                            "artifact_id": str(artifact.id),
                            "artifact_type": artifact.artifact_type,
                            "payload": artifact.payload or {},
                            "version": artifact.version,
                            "created_at": artifact.created_at.isoformat() + "Z",
                            "updated_at": artifact.updated_at.isoformat() + "Z",
                        },
                    )

                state.messages.append(
                    CoreAgentMessage(
                        role=AgentRole.TOOL,
                        content=tool_message_content,
                        tool_call_id=call.id,
                        name=call.name,
                    )
                )

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/sessions/{session_id}", response_model=AgentSessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> AgentSessionResponse:
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid session id") from exc

    result = await db.execute(select(AgentSession).where(AgentSession.id == session_uuid))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages_result = await db.execute(
        select(AgentMessageRecord)
        .where(AgentMessageRecord.session_id == session_uuid)
        .order_by(AgentMessageRecord.created_at.asc())
    )
    messages = messages_result.scalars().all()

    artifacts_result = await db.execute(
        select(AgentArtifact)
        .where(AgentArtifact.session_id == session_uuid)
        .order_by(AgentArtifact.created_at.asc())
    )
    artifacts = artifacts_result.scalars().all()

    artifact_responses = [
        AgentArtifactResponse(
            artifact_id=str(artifact.id),
            artifact_type=artifact.artifact_type,
            payload=artifact.payload or {},
            version=artifact.version,
            created_at=artifact.created_at,
            updated_at=artifact.updated_at,
        )
        for artifact in artifacts
    ]
    artifact_responses.extend(_derive_missing_artifacts(artifacts))
    artifact_responses.sort(key=lambda item: item.created_at)

    return AgentSessionResponse(
        session_id=str(session.id),
        status=session.status,
        title=session.title,
        agent_model=_coerce_agent_model(
            (session.meta or {}).get("agent_model") or settings.GEMINI_AGENT_MODEL
        ),
        metadata=session.meta or {},
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[
            AgentMessageResponse(
                message_id=str(message.id),
                role=message.role,
                content=message.content or "",
                tool_calls=message.tool_calls or [],
                tool_call_id=message.tool_call_id,
                name=message.name,
                created_at=message.created_at,
            )
            for message in messages
        ],
        artifacts=artifact_responses,
    )


@router.post("/sessions/{session_id}/approve", response_model=AgentSessionStatusResponse)
async def approve_session(
    session_id: str,
    request: AgentDecisionRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentSessionStatusResponse:
    session = await _load_session(session_id, db)
    session.status = "approved"
    session.meta = _merge_metadata(session.meta, request.metadata)
    if request.note:
        session.meta["decision_note"] = request.note
    await db.commit()
    await db.refresh(session)
    logger.info(
        "Agent session approved",
        extra={"session_id": str(session.id)},
    )
    return AgentSessionStatusResponse(
        session_id=str(session.id),
        status=session.status,
        metadata=session.meta or {},
        updated_at=session.updated_at,
    )


@router.post("/sessions/{session_id}/reject", response_model=AgentSessionStatusResponse)
async def reject_session(
    session_id: str,
    request: AgentDecisionRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentSessionStatusResponse:
    session = await _load_session(session_id, db)
    session.status = "rejected"
    session.meta = _merge_metadata(session.meta, request.metadata)
    if request.note:
        session.meta["decision_note"] = request.note
    await db.commit()
    await db.refresh(session)
    logger.info(
        "Agent session rejected",
        extra={"session_id": str(session.id)},
    )
    return AgentSessionStatusResponse(
        session_id=str(session.id),
        status=session.status,
        metadata=session.meta or {},
        updated_at=session.updated_at,
    )


async def _load_session(session_id: str, db: AsyncSession) -> AgentSession:
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid session id") from exc
    result = await db.execute(select(AgentSession).where(AgentSession.id == session_uuid))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
