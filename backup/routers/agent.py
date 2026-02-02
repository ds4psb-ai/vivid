"""Agent chat API endpoints."""
from __future__ import annotations

import asyncio
import json
import threading
import uuid
from datetime import datetime
from typing import AsyncGenerator, List, Optional

from cachetools import TTLCache
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from fastapi.responses import StreamingResponse

from app.middleware.rate_limit import limiter, RATE_LIMIT_LLM_GENERATE, RATE_LIMIT_UPLOAD
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
import os
import shutil

from app.agents.agent_types import AgentMessage as CoreAgentMessage
from app.agents.agent_types import AgentRole, AgentState, ToolCall, ToolContext
from app.agents.model_clients import GeminiModelClient, StubModelClient
from app.agents.artifact_backfill import derive_artifacts_from_tool_payload
from app.agents.vivid_agent import VividAgent
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.utils.error_sanitize import safe_error_detail
from app.logging_config import get_logger
from app.models import AgentArtifact, AgentMessage as AgentMessageRecord, AgentSession

router = APIRouter(prefix="/agent", tags=["agent"])
logger = get_logger("agent_router")


def _build_agent(model_name: Optional[str] = None, use_cache: bool = True) -> VividAgent:
    """Build VividAgent with optional context caching.
    
    Args:
        model_name: Gemini model name
        use_cache: Enable explicit context caching for cost optimization
    """
    selected_model = model_name or settings.GEMINI_AGENT_MODEL
    # H1.3: SecretStr - use .get_secret_value() for actual API key
    if settings.GEMINI_ENABLED and settings.GEMINI_API_KEY.get_secret_value():
        try:
            return VividAgent(
                model_client=GeminiModelClient(
                    model_name=selected_model,
                    temperature=settings.GEMINI_AGENT_TEMPERATURE,
                    max_output_tokens=settings.GEMINI_AGENT_MAX_TOKENS,
                    use_cache=use_cache,  # Enable context caching
                )
            )
        except Exception as exc:
            logger.warning(
                "Gemini model init failed, using stub",
                extra={"error": str(exc)},
            )
    return VividAgent(model_client=StubModelClient())


# P0-3: TTLCache로 메모리 누수 방지 (최대 5개 모델, 1시간 TTL)
_AGENT_CACHE: TTLCache = TTLCache(maxsize=5, ttl=3600)
_AGENT_CACHE_LOCK = threading.Lock()

# P0-1: Session-based StreamController cache to prevent duplicate streams
_STREAM_CONTROLLERS: TTLCache = TTLCache(maxsize=100, ttl=600)  # 10분 TTL
_STREAM_CONTROLLERS_LOCK = threading.Lock()


def _get_stream_controller(session_id: str) -> "StreamController":
    """Get or create a StreamController for a session.

    Thread-safe cache lookup with lazy initialization.
    Prevents duplicate stream threads for the same session.
    """
    with _STREAM_CONTROLLERS_LOCK:
        if session_id not in _STREAM_CONTROLLERS:
            _STREAM_CONTROLLERS[session_id] = StreamController()
            logger.debug(f"Created StreamController for session {session_id}")
        return _STREAM_CONTROLLERS[session_id]


def _get_agent(model_name: str) -> VividAgent:
    """Get or create agent with thread-safe TTL caching."""
    with _AGENT_CACHE_LOCK:
        if model_name in _AGENT_CACHE:
            return _AGENT_CACHE[model_name]
        agent = _build_agent(model_name)
        _AGENT_CACHE[model_name] = agent
        logger.debug(f"Agent cached for model: {model_name}, cache size: {len(_AGENT_CACHE)}")
        return agent


class AgentChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1)
    metadata: Optional[dict] = None
    model: Optional[str] = None
    attachments: List[dict] = Field(default_factory=list)
    page_context: Optional[str] = None  # Current page path for context-aware responses


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
    attachments: List[dict] = Field(default_factory=list)
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
    attachments = record.payload.get("attachments", []) if record.payload else []

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
        attachments=attachments,
    )


def _ensure_genai():
    """Get google.genai client via genai_utils factory."""
    try:
        from app.services.genai_utils import get_genai_client
        # genai_utils handles H1.3: SecretStr internally
        return get_genai_client()
    except ImportError:
        raise HTTPException(status_code=500, detail="google-genai not installed")
    except ValueError:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")


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
    """Result holder for streaming thread."""
    def __init__(self) -> None:
        self.message: Optional[CoreAgentMessage] = None
        self.error: Optional[Exception] = None


class StreamController:
    """P0-1: Thread-safe streaming controller to prevent duplicate streams.
    
    Ensures only one streaming thread runs at a time per controller instance.
    """
    
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active = False
        self._thread: Optional[threading.Thread] = None
    
    def start_stream(
        self,
        model_client: GeminiModelClient,
        messages: List[CoreAgentMessage],
        tools: List,
        queue: asyncio.Queue,
        loop: asyncio.AbstractEventLoop,
    ) -> _StreamResult:
        """Start a streaming thread with mutex protection.
        
        Raises:
            RuntimeError: If a stream is already active
        """
        with self._lock:
            if self._active:
                logger.warning("Attempted to start duplicate stream, blocking")
                raise RuntimeError("Stream already active for this controller")
            self._active = True
        
        result = _StreamResult()
        
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
                logger.error(f"Stream thread error: {type(exc).__name__}: {exc}")
            finally:
                with self._lock:
                    self._active = False
                loop.call_soon_threadsafe(queue.put_nowait, None)
        
        self._thread = threading.Thread(target=_runner, daemon=True)
        self._thread.start()
        return result
    
    @property
    def is_active(self) -> bool:
        """Check if a stream is currently active."""
        with self._lock:
            return self._active


def _start_stream_thread(
    model_client: GeminiModelClient,
    messages: List[CoreAgentMessage],
    tools: List,
    queue: asyncio.Queue,
    result: _StreamResult,
    loop: asyncio.AbstractEventLoop,
) -> None:
    """Legacy wrapper for backward compatibility.
    
    Note: New code should use StreamController directly for better safety.
    """
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
            logger.error(f"Stream thread error: {type(exc).__name__}: {exc}")
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)
        thread = threading.Thread(target=_runner, daemon=True)
    thread.start()


@router.post("/upload")
@limiter.limit(RATE_LIMIT_UPLOAD)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),  # P0: Auth required - prevent API abuse
):
    """Upload a file to Gemini File API."""
    client = _ensure_genai()

    # Save to temp file first
    temp_filename = f"temp_{uuid.uuid4().hex}_{file.filename}"
    try:
        async with aiofiles.open(temp_filename, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        # Upload to Gemini (google.genai - new library)
        # Note: upload handles MIME type detection, but we can hint it or verify
        uploaded_file = client.files.upload(file=temp_filename, config={"display_name": file.filename})

        # Return info needed for the chat request
        return {
            "file_uri": uploaded_file.uri,
            "name": uploaded_file.name,
            "mime_type": uploaded_file.mime_type,
            "display_name": file.filename,
        }
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=safe_error_detail(e, "File upload"))
    finally:
        # Cleanup temp file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


@router.post("/chat")
@limiter.limit(RATE_LIMIT_LLM_GENERATE)
async def chat_agent(
    request: Request,
    chat_request: AgentChatRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = None
    if chat_request.session_id:
        try:
            session_uuid = uuid.UUID(chat_request.session_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid session id") from exc
        result = await db.execute(select(AgentSession).where(AgentSession.id == session_uuid))
        session = result.scalars().first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        # P0 BOLA: Verify session ownership to prevent message injection
        user_id = user.get("id") or user.get("sub")
        if session.owner_id and session.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        title = (chat_request.message or "").strip()
        if len(title) > 80:
            title = f"{title[:77]}..."
        user_id = user.get("id") or user.get("sub")
        session = AgentSession(
            status="active",
            title=title or None,
            meta=chat_request.metadata or {},
            owner_id=user_id,  # P0 BOLA: Store owner for access control
        )
        db.add(session)
        await db.flush()

    logger.info(
        "Agent chat request",
        extra={
            "session_id": str(session.id),
            "existing_session": bool(chat_request.session_id),
        },
    )

    if chat_request.metadata:
        session.meta = _merge_metadata(session.meta, chat_request.metadata)
    model_name = _resolve_agent_model(session, chat_request)
    session.meta = _merge_metadata(session.meta, {"agent_model": model_name})

    # Store page context for context-aware agent responses
    if chat_request.page_context:
        session.meta = _merge_metadata(session.meta, {"page_context": chat_request.page_context})

    agent = _get_agent(model_name)

    existing_messages_result = await db.execute(
        select(AgentMessageRecord)
        .where(AgentMessageRecord.session_id == session.id)
        .order_by(AgentMessageRecord.created_at.asc())
    )
    existing_messages = existing_messages_result.scalars().all()
    state_messages = [_to_core_message(message) for message in existing_messages]
    state = AgentState(session_id=str(session.id), messages=state_messages, metadata=session.meta or {})

    user_content = chat_request.message.strip()
    state.messages.append(CoreAgentMessage(role=AgentRole.USER, content=user_content))
    user_record = AgentMessageRecord(
        session_id=session.id,
        role="user",
        content=user_content,
        tool_calls=[],
        payload={"attachments": chat_request.attachments} if chat_request.attachments else None,
    )
    db.add(user_record)
    await db.commit()
    await db.refresh(session)

    # Auto-execution context injection for AUTONOMOUS mode
    from app.agents.intent_router import classify_intent, Intent
    from app.agents.attachment_analyzer import AttachmentAnalyzer

    routing = classify_intent(user_content)

    # Inject auto-execution context if AUTONOMOUS mode detected
    if routing.should_auto_execute and routing.intent == Intent.WORKFLOW_REQUEST:
        # Analyze attachments for workflow inference
        attachment_suggestion = AttachmentAnalyzer.analyze(request.attachments)

        auto_context = {
            "auto_execute": True,
            "intent": routing.intent.value,
            "confidence": routing.confidence,
            "suggested_dimensions": attachment_suggestion.dimensions,
            "start_dimension": attachment_suggestion.start_dimension,
            "full_workflow": routing.full_workflow,
            "topic_hint": user_content[:100],
            "attachment_reason": attachment_suggestion.reason,
        }

        session.meta = _merge_metadata(session.meta, {"auto_context": auto_context})
        state.metadata = _merge_metadata(state.metadata or {}, {"auto_context": auto_context})

        logger.info(
            "Auto-execution context injected",
            extra={
                "session_id": str(session.id),
                "intent": routing.intent.value,
                "auto_execute": True,
                "full_workflow": routing.full_workflow,
                "dimensions": attachment_suggestion.dimensions,
            },
        )
    elif routing.intent != Intent.GENERAL_CHAT:
        # Inject routing hint even for non-auto-execute cases
        routing_hint = {
            "intent": routing.intent.value,
            "confidence": routing.confidence,
            "suggested_tool": routing.suggested_tool,
            "workflow_suggestion": routing.workflow_suggestion,
        }
        session.meta = _merge_metadata(session.meta, {"routing_hint": routing_hint})
        state.metadata = _merge_metadata(state.metadata or {}, {"routing_hint": routing_hint})

    async def _event_stream() -> AsyncGenerator[str, None]:
        seq = 0
        session_id = str(session.id)

        def _next_event(event_type: str, payload: dict) -> str:
            nonlocal seq
            seq += 1
            return _format_sse(
                event_type,
                _build_event(
                    session_id,
                    seq,
                    event_type,
                    payload,
                    f"{datetime.utcnow().isoformat()}Z",
                ),
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
                loop = asyncio.get_running_loop()

                # P0-1: Use session-based StreamController to prevent duplicate streams
                stream_controller = _get_stream_controller(session_id)
                try:
                    result = stream_controller.start_stream(
                        model_client,
                        context,
                        tool_registry.specs(),
                        queue,
                        loop,
                    )
                except RuntimeError as e:
                    # Stream already active for this session - reject duplicate request
                    logger.warning(
                        "Duplicate stream request blocked",
                        extra={"session_id": session_id, "error": str(e)},
                    )
                    yield _next_event(
                        "agent.error",
                        {
                            "code": "STREAM_ALREADY_ACTIVE",
                            "message": "이미 처리 중인 요청이 있습니다. 완료될 때까지 기다려주세요.",
                        },
                    )
                    return

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
                    {
                        **tool_payload,
                        "name": result.name,
                        "arguments": call.arguments,  # 🆕 Include inputs for frontend display
                    },
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
    message_limit: int = Query(default=200, ge=1, le=500, description="Max messages to return"),
    artifact_limit: int = Query(default=100, ge=1, le=200, description="Max artifacts to return"),
    user: dict = Depends(get_current_user),  # P0 BOLA: Auth required
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
    
    # P0 BOLA: Owner verification
    user_id = user.get("id") or user.get("sub")
    if session.owner_id and session.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Performance optimization: parallel queries with limits
    async def _fetch_messages():
        r = await db.execute(
            select(AgentMessageRecord)
            .where(AgentMessageRecord.session_id == session_uuid)
            .order_by(AgentMessageRecord.created_at.asc())
            .limit(message_limit)
        )
        return r.scalars().all()

    async def _fetch_artifacts():
        r = await db.execute(
            select(AgentArtifact)
            .where(AgentArtifact.session_id == session_uuid)
            .order_by(AgentArtifact.created_at.asc())
            .limit(artifact_limit)
        )
        return r.scalars().all()

    messages, artifacts = await asyncio.gather(_fetch_messages(), _fetch_artifacts())

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
                attachments=message.payload.get("attachments", []) if message.payload else [],
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
    user: dict = Depends(get_current_user),  # P0 BOLA: Auth required
    db: AsyncSession = Depends(get_db),
) -> AgentSessionStatusResponse:
    session = await _load_session(session_id, db, user)
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
    user: dict = Depends(get_current_user),  # P0 BOLA: Auth required
    db: AsyncSession = Depends(get_db),
) -> AgentSessionStatusResponse:
    session = await _load_session(session_id, db, user)
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


async def _load_session(session_id: str, db: AsyncSession, user: dict) -> AgentSession:
    """Load session with ownership verification."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid session id") from exc
    result = await db.execute(select(AgentSession).where(AgentSession.id == session_uuid))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # P0 BOLA: Owner verification
    user_id = user.get("id") or user.get("sub")
    if session.owner_id and session.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return session
