"""IP Character Chat Router (Phase 10).

REST + WebSocket endpoints for real-time IP character chat.

Endpoints:
- POST /chat/sessions - Create chat session
- GET /chat/sessions - List user's sessions
- GET /chat/sessions/{id} - Get session details
- DELETE /chat/sessions/{id} - Archive session
- POST /chat/sessions/{id}/messages - Send message (REST)
- GET /chat/sessions/{id}/messages - Get message history
- GET /chat/sessions/{id}/stream - SSE message streaming
- WS /chat/sessions/{id}/ws - WebSocket for real-time chat
- GET /chat/ips/{id}/scenarios - Get IP scenarios
- POST /chat/sessions/{id}/scenario - Switch scenario
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_tokens import decode_token
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models_ip import IPCatalog
from app.models_ip_chat import IPChatSession, IPChatMessage, IPChatScenario
from app.services.ip_chat_service import IPChatService
from app.utils.sse_utils import sse_event, sse_heartbeat, SSE_HEADERS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["ip-chat"])


# =============================================================================
# Pydantic Models
# =============================================================================

class CreateSessionRequest(BaseModel):
    """Request to create a new chat session."""
    ip_id: UUID
    scenario_key: Optional[str] = None
    model_preference: str = Field(default="flash", pattern="^(flash|pro|opus)$")


class SessionResponse(BaseModel):
    """Chat session response."""
    id: UUID
    ip_id: UUID
    ip_name: str
    ip_thumbnail: Optional[str] = None
    title: Optional[str] = None
    scenario_branch: Optional[str] = None
    model_preference: str
    total_messages: int
    total_credits_spent: int
    is_pinned: bool
    is_archived: bool
    created_at: datetime
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Paginated session list response."""
    sessions: List[SessionResponse]
    total: int
    page: int
    page_size: int


class SendMessageRequest(BaseModel):
    """Request to send a chat message."""
    content: str = Field(min_length=1, max_length=4000)
    media_urls: Optional[List[str]] = None


class MessageResponse(BaseModel):
    """Chat message response."""
    id: UUID
    role: str
    content: str
    media_urls: List[str] = []
    tokens_used: int = 0
    credits_charged: int = 0
    model_used: Optional[str] = None
    latency_ms: int = 0
    is_regenerated: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Message history response."""
    messages: List[MessageResponse]
    has_more: bool


class ScenarioResponse(BaseModel):
    """Chat scenario response."""
    scenario_key: str
    name_ko: str
    name_en: str
    description_ko: Optional[str] = None
    description_en: Optional[str] = None
    character_mood: str
    is_default: bool

    class Config:
        from_attributes = True


class SwitchScenarioRequest(BaseModel):
    """Request to switch scenario."""
    scenario_key: str


class ChatIPResponse(BaseModel):
    """IP info for chat."""
    id: UUID
    slug: str
    name_ko: str
    name_en: str
    thumbnail_url: Optional[str] = None
    chat_enabled: bool
    chat_model_default: str
    chat_session_count: int
    chat_message_count: int

    class Config:
        from_attributes = True


# =============================================================================
# Session Endpoints
# =============================================================================

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat session with an IP character."""
    service = IPChatService(db)

    try:
        session = await service.create_session(
            user_id=user["id"],
            ip_id=request.ip_id,
            scenario_key=request.scenario_key,
            model_preference=request.model_preference,
        )

        # Get IP info for response
        ip = await db.get(IPCatalog, session.ip_id)

        return SessionResponse(
            id=session.id,
            ip_id=session.ip_id,
            ip_name=ip.name_ko if ip else "Unknown",
            ip_thumbnail=ip.thumbnail_url if ip else None,
            title=session.title,
            scenario_branch=session.scenario_branch,
            model_preference=session.model_preference,
            total_messages=session.total_messages,
            total_credits_spent=session.total_credits_spent,
            is_pinned=session.is_pinned,
            is_archived=session.is_archived,
            created_at=session.created_at,
            last_message_at=session.last_message_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    ip_id: Optional[UUID] = None,
    include_archived: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's chat sessions."""
    service = IPChatService(db)

    offset = (page - 1) * page_size
    sessions, total = await service.list_sessions(
        user_id=user["id"],
        ip_id=ip_id,
        include_archived=include_archived,
        limit=page_size,
        offset=offset,
    )

    # Enrich with IP info
    session_responses = []
    for session in sessions:
        ip = await db.get(IPCatalog, session.ip_id)
        session_responses.append(
            SessionResponse(
                id=session.id,
                ip_id=session.ip_id,
                ip_name=ip.name_ko if ip else "Unknown",
                ip_thumbnail=ip.thumbnail_url if ip else None,
                title=session.title,
                scenario_branch=session.scenario_branch,
                model_preference=session.model_preference,
                total_messages=session.total_messages,
                total_credits_spent=session.total_credits_spent,
                is_pinned=session.is_pinned,
                is_archived=session.is_archived,
                created_at=session.created_at,
                last_message_at=session.last_message_at,
            )
        )

    return SessionListResponse(
        sessions=session_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get chat session details."""
    service = IPChatService(db)

    session = await service.get_session(session_id, user["id"])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    ip = await db.get(IPCatalog, session.ip_id)

    return SessionResponse(
        id=session.id,
        ip_id=session.ip_id,
        ip_name=ip.name_ko if ip else "Unknown",
        ip_thumbnail=ip.thumbnail_url if ip else None,
        title=session.title,
        scenario_branch=session.scenario_branch,
        model_preference=session.model_preference,
        total_messages=session.total_messages,
        total_credits_spent=session.total_credits_spent,
        is_pinned=session.is_pinned,
        is_archived=session.is_archived,
        created_at=session.created_at,
        last_message_at=session.last_message_at,
    )


@router.delete("/sessions/{session_id}")
async def archive_session(
    session_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Archive a chat session."""
    service = IPChatService(db)

    success = await service.archive_session(session_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"success": True, "message": "Session archived"}


# =============================================================================
# Message Endpoints
# =============================================================================

@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: UUID,
    request: SendMessageRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message and get AI response (non-streaming)."""
    service = IPChatService(db)

    try:
        message = await service.send_message(
            session_id=session_id,
            user_id=user["id"],
            content=request.content,
            media_urls=request.media_urls,
        )

        return MessageResponse(
            id=message.id,
            role=message.role,
            content=message.content,
            media_urls=message.media_urls or [],
            tokens_used=message.tokens_used,
            credits_charged=message.credits_charged,
            model_used=message.model_used,
            latency_ms=message.latency_ms,
            is_regenerated=message.is_regenerated,
            created_at=message.created_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
async def get_messages(
    session_id: UUID,
    before_id: Optional[UUID] = None,
    limit: int = Query(default=50, ge=1, le=100),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get message history for a session."""
    service = IPChatService(db)

    messages = await service.get_messages(
        session_id=session_id,
        user_id=user["id"],
        limit=limit + 1,  # Get one extra to check has_more
        before_id=before_id,
    )

    has_more = len(messages) > limit
    if has_more:
        messages = messages[:-1]

    return MessageListResponse(
        messages=[
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                media_urls=msg.media_urls or [],
                tokens_used=msg.tokens_used,
                credits_charged=msg.credits_charged,
                model_used=msg.model_used,
                latency_ms=msg.latency_ms,
                is_regenerated=msg.is_regenerated,
                created_at=msg.created_at,
            )
            for msg in messages
        ],
        has_more=has_more,
    )


@router.post("/sessions/{session_id}/messages/{message_id}/regenerate", response_model=MessageResponse)
async def regenerate_message(
    session_id: UUID,
    message_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Regenerate an AI response."""
    service = IPChatService(db)

    try:
        message = await service.regenerate_response(
            session_id=session_id,
            user_id=user["id"],
            message_id=message_id,
        )

        return MessageResponse(
            id=message.id,
            role=message.role,
            content=message.content,
            media_urls=message.media_urls or [],
            tokens_used=message.tokens_used,
            credits_charged=message.credits_charged,
            model_used=message.model_used,
            latency_ms=message.latency_ms,
            is_regenerated=message.is_regenerated,
            created_at=message.created_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Streaming Endpoints
# =============================================================================

@router.get("/sessions/{session_id}/stream")
async def stream_message(
    session_id: UUID,
    content: str = Query(..., min_length=1, max_length=4000),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message and stream the AI response via SSE."""
    service = IPChatService(db)

    # Verify session exists
    session = await service.get_session(session_id, user["id"])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    async def generate() -> AsyncGenerator[str, None]:
        try:
            yield sse_event("message.started", {"session_id": str(session_id)})

            full_content = ""
            async for chunk in service.send_message_stream(
                session_id=session_id,
                user_id=user["id"],
                content=content,
            ):
                full_content += chunk
                yield sse_event("message.chunk", {"chunk": chunk})

            yield sse_event("message.completed", {"full_content": full_content})

        except Exception as e:
            logger.exception(f"Stream error for session {session_id}")
            yield sse_event("error", {"message": str(e)})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


# =============================================================================
# WebSocket Endpoint
# =============================================================================

class ConnectionManager:
    """Manages WebSocket connections for chat sessions."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def send_to_session(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for ws in self.active_connections[session_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


async def authenticate_websocket(websocket: WebSocket) -> Optional[str]:
    """Authenticate WebSocket connection using JWT token.

    Security Hardening (H1.2): Validates JWT token BEFORE accepting connection.
    Token can be passed via:
    1. Query parameter: ?token=xxx
    2. Subprotocol header (for browsers that support it)

    Args:
        websocket: The WebSocket connection (not yet accepted)

    Returns:
        User ID if authenticated, None otherwise
    """
    # Try query parameter first (most common for WebSocket)
    token = websocket.query_params.get("token")

    # Fallback: Check Sec-WebSocket-Protocol header for token
    if not token:
        protocols = websocket.headers.get("sec-websocket-protocol", "")
        for protocol in protocols.split(","):
            protocol = protocol.strip()
            if protocol.startswith("auth-"):
                token = protocol[5:]  # Remove 'auth-' prefix
                break

    if not token:
        return None

    # Validate token using existing auth system
    try:
        payload = decode_token(token, settings.SESSION_SECRET)
        if payload and isinstance(payload.get("user_id"), str):
            return payload["user_id"]
    except Exception as e:
        logger.warning(f"WebSocket auth failed: {e}")

    return None


@router.websocket("/sessions/{session_id}/ws")
async def websocket_chat(
    websocket: WebSocket,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """WebSocket endpoint for real-time chat.

    Security: JWT authentication required BEFORE connection acceptance.
    Pass token via query param: ws://host/sessions/{id}/ws?token=your_jwt_token

    Message types:
    - Client -> Server: {"type": "message", "content": "...", "media_urls": [...]}
    - Server -> Client: {"type": "chunk", "chunk": "..."}
    - Server -> Client: {"type": "complete", "message": {...}}
    - Server -> Client: {"type": "error", "message": "..."}
    """
    # H1.2: Authenticate BEFORE accepting WebSocket connection
    user_id = await authenticate_websocket(websocket)

    # In development, allow anonymous access for testing
    if not user_id:
        if settings.ENVIRONMENT.lower() in {"development", "dev", "local"}:
            # Development fallback - check query param
            user_id = websocket.query_params.get("user_id")
            if not user_id:
                user_id = "dev-user-001"
                logger.warning(f"WebSocket using dev user for session {session_id}")
        else:
            # Production: Reject unauthenticated connections
            await websocket.close(code=4001, reason="Unauthorized: Valid token required")
            return

    service = IPChatService(db)

    # Verify session exists
    session = await service.get_session(session_id, user_id)
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return

    await manager.connect(str(session_id), websocket)

    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "session_id": str(session_id),
            "model_preference": session.model_preference,
        })

        while True:
            # Receive message from client
            data = await websocket.receive_json()

            if data.get("type") == "message":
                content = data.get("content", "")
                media_urls = data.get("media_urls", [])

                if not content:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Empty message content",
                    })
                    continue

                # Stream response
                try:
                    await websocket.send_json({"type": "typing"})

                    full_response = ""
                    async for chunk in service.send_message_stream(
                        session_id=session_id,
                        user_id=user_id,
                        content=content,
                        media_urls=media_urls,
                    ):
                        full_response += chunk
                        await websocket.send_json({
                            "type": "chunk",
                            "chunk": chunk,
                        })

                    await websocket.send_json({
                        "type": "complete",
                        "content": full_response,
                    })

                except Exception as e:
                    logger.error(f"WebSocket message error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                    })

            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(str(session_id), websocket)


# =============================================================================
# Scenario Endpoints
# =============================================================================

@router.get("/ips/{ip_id}/scenarios", response_model=List[ScenarioResponse])
async def get_scenarios(
    ip_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get available scenarios for an IP character."""
    service = IPChatService(db)

    scenarios = await service.get_scenarios(ip_id)

    return [
        ScenarioResponse(
            scenario_key=s.scenario_key,
            name_ko=s.name_ko,
            name_en=s.name_en,
            description_ko=s.description_ko,
            description_en=s.description_en,
            character_mood=s.character_mood,
            is_default=s.is_default,
        )
        for s in scenarios
    ]


@router.post("/sessions/{session_id}/scenario", response_model=MessageResponse)
async def switch_scenario(
    session_id: UUID,
    request: SwitchScenarioRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Switch to a different scenario in the session."""
    service = IPChatService(db)

    try:
        message = await service.switch_scenario(
            session_id=session_id,
            user_id=user["id"],
            scenario_key=request.scenario_key,
        )

        if not message:
            raise HTTPException(status_code=400, detail="Scenario not found")

        return MessageResponse(
            id=message.id,
            role=message.role,
            content=message.content,
            media_urls=message.media_urls or [],
            tokens_used=message.tokens_used,
            credits_charged=message.credits_charged,
            model_used=message.model_used,
            latency_ms=message.latency_ms,
            is_regenerated=message.is_regenerated,
            created_at=message.created_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# IP Discovery Endpoints
# =============================================================================

@router.get("/ips", response_model=List[ChatIPResponse])
async def list_chat_enabled_ips(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List IPs that have chat enabled."""
    from sqlalchemy import select, desc

    result = await db.execute(
        select(IPCatalog)
        .where(
            IPCatalog.chat_enabled == True,
            IPCatalog.is_active == True,
        )
        .order_by(desc(IPCatalog.chat_session_count))
        .offset(offset)
        .limit(limit)
    )
    ips = result.scalars().all()

    return [
        ChatIPResponse(
            id=ip.id,
            slug=ip.slug,
            name_ko=ip.name_ko,
            name_en=ip.name_en,
            thumbnail_url=ip.thumbnail_url,
            chat_enabled=ip.chat_enabled,
            chat_model_default=ip.chat_model_default or "flash",
            chat_session_count=ip.chat_session_count or 0,
            chat_message_count=ip.chat_message_count or 0,
        )
        for ip in ips
    ]


@router.get("/ips/{ip_id}", response_model=ChatIPResponse)
async def get_chat_ip(
    ip_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get IP details for chat."""
    ip = await db.get(IPCatalog, ip_id)
    if not ip:
        raise HTTPException(status_code=404, detail="IP not found")

    if not ip.chat_enabled:
        raise HTTPException(status_code=400, detail="Chat not enabled for this IP")

    return ChatIPResponse(
        id=ip.id,
        slug=ip.slug,
        name_ko=ip.name_ko,
        name_en=ip.name_en,
        thumbnail_url=ip.thumbnail_url,
        chat_enabled=ip.chat_enabled,
        chat_model_default=ip.chat_model_default or "flash",
        chat_session_count=ip.chat_session_count or 0,
        chat_message_count=ip.chat_message_count or 0,
    )
