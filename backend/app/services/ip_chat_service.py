"""IP Chat Service for Phase 10.

Real-time chat with IP characters using RAG-enhanced personas.

Features:
- Multi-model selection (flash, pro, opus)
- Scenario branching
- Character state/memory persistence
- Credit tracking
- Streaming responses

Based on: SSOT_DECISIONS_LOG.md Phase 10 design
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional, Tuple

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models_ip import IPCatalog
from app.models_ip_chat import IPChatSession, IPChatMessage, IPChatScenario

logger = logging.getLogger(__name__)


# Model configurations
MODEL_CONFIGS = {
    "flash": {
        "model_name": "gemini-3-flash-preview",
        "temperature": 0.8,
        "max_tokens": 1024,
        "credits_per_message": 1,
    },
    "pro": {
        "model_name": "gemini-3-pro-preview",
        "temperature": 0.7,
        "max_tokens": 2048,
        "credits_per_message": 3,
    },
    "opus": {
        "model_name": "gemini-3-pro-preview",
        "temperature": 0.6,
        "max_tokens": 4096,
        "credits_per_message": 5,
    },
}


class IPChatService:
    """Service for IP character chat interactions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Session Management
    # =========================================================================

    async def create_session(
        self,
        user_id: str,
        ip_id: uuid.UUID,
        scenario_key: Optional[str] = None,
        model_preference: str = "flash",
        tenant_id: Optional[uuid.UUID] = None,
    ) -> IPChatSession:
        """Create a new chat session with an IP character.

        Args:
            user_id: User identifier
            ip_id: IP catalog entry ID
            scenario_key: Optional starting scenario
            model_preference: LLM model tier (flash, pro, opus)
            tenant_id: Optional tenant for B2B access

        Returns:
            Created chat session
        """
        # Get IP catalog entry
        ip = await self.db.get(IPCatalog, ip_id)
        if not ip:
            raise ValueError(f"IP not found: {ip_id}")

        if not ip.chat_enabled:
            raise ValueError(f"Chat not enabled for IP: {ip.name_ko}")

        # Get default scenario if not specified
        if not scenario_key:
            scenario = await self._get_default_scenario(ip_id)
            scenario_key = scenario.scenario_key if scenario else None

        session = IPChatSession(
            user_id=user_id,
            ip_id=ip_id,
            tenant_id=tenant_id,
            title=f"{ip.name_ko} 채팅",
            scenario_branch=scenario_key,
            model_preference=model_preference,
            character_state={
                "mood": "neutral",
                "memory": [],
                "relationship_level": 0,
            },
        )

        self.db.add(session)
        await self.db.flush()

        # Add opening message if scenario exists
        if scenario_key:
            await self._add_scenario_opening(session, scenario_key)

        # Update IP stats
        ip.chat_session_count = (ip.chat_session_count or 0) + 1
        await self.db.commit()

        logger.info(f"Created chat session {session.id} for user {user_id} with IP {ip.slug}")
        return session

    async def get_session(
        self,
        session_id: uuid.UUID,
        user_id: str,
    ) -> Optional[IPChatSession]:
        """Get a chat session by ID."""
        result = await self.db.execute(
            select(IPChatSession).where(
                IPChatSession.id == session_id,
                IPChatSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        user_id: str,
        ip_id: Optional[uuid.UUID] = None,
        include_archived: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[IPChatSession], int]:
        """List user's chat sessions.

        Returns:
            Tuple of (sessions, total_count)
        """
        query = select(IPChatSession).where(IPChatSession.user_id == user_id)

        if ip_id:
            query = query.where(IPChatSession.ip_id == ip_id)

        if not include_archived:
            query = query.where(IPChatSession.is_archived == False)

        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Get paginated results
        query = query.order_by(desc(IPChatSession.last_message_at)).offset(offset).limit(limit)
        result = await self.db.execute(query)
        sessions = list(result.scalars().all())

        return sessions, total

    async def archive_session(self, session_id: uuid.UUID, user_id: str) -> bool:
        """Archive a chat session."""
        session = await self.get_session(session_id, user_id)
        if not session:
            return False

        session.is_archived = True
        await self.db.commit()
        return True

    # =========================================================================
    # Message Handling
    # =========================================================================

    async def send_message(
        self,
        session_id: uuid.UUID,
        user_id: str,
        content: str,
        media_urls: Optional[List[str]] = None,
    ) -> IPChatMessage:
        """Send a user message and get AI response.

        Args:
            session_id: Chat session ID
            user_id: User identifier
            content: Message content
            media_urls: Optional media attachments

        Returns:
            AI response message
        """
        session = await self.get_session(session_id, user_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Create user message
        user_message = IPChatMessage(
            session_id=session_id,
            role="user",
            content=content,
            media_urls=media_urls or [],
        )
        self.db.add(user_message)
        await self.db.flush()

        # Generate AI response
        assistant_message = await self._generate_response(session, user_message)

        # Update session stats
        session.total_messages += 2
        session.last_message_at = datetime.utcnow()

        # Update IP stats
        ip = await self.db.get(IPCatalog, session.ip_id)
        if ip:
            ip.chat_message_count = (ip.chat_message_count or 0) + 2

        await self.db.commit()

        return assistant_message

    async def send_message_stream(
        self,
        session_id: uuid.UUID,
        user_id: str,
        content: str,
        media_urls: Optional[List[str]] = None,
    ) -> AsyncGenerator[str, None]:
        """Send a message and stream the AI response.

        Yields:
            Response chunks as they're generated
        """
        session = await self.get_session(session_id, user_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Create user message
        user_message = IPChatMessage(
            session_id=session_id,
            role="user",
            content=content,
            media_urls=media_urls or [],
        )
        self.db.add(user_message)
        await self.db.flush()

        # Stream AI response
        full_response = ""
        tokens_used = 0

        async for chunk in self._generate_response_stream(session, user_message):
            full_response += chunk
            yield chunk

        # Create assistant message with full response
        model_config = MODEL_CONFIGS.get(session.model_preference, MODEL_CONFIGS["flash"])
        assistant_message = IPChatMessage(
            session_id=session_id,
            role="assistant",
            content=full_response,
            model_used=model_config["model_name"],
            credits_charged=model_config["credits_per_message"],
        )
        self.db.add(assistant_message)

        # Update session
        session.total_messages += 2
        session.total_credits_spent += model_config["credits_per_message"]
        session.last_message_at = datetime.utcnow()

        await self.db.commit()

    async def get_messages(
        self,
        session_id: uuid.UUID,
        user_id: str,
        limit: int = 50,
        before_id: Optional[uuid.UUID] = None,
    ) -> List[IPChatMessage]:
        """Get chat messages for a session."""
        session = await self.get_session(session_id, user_id)
        if not session:
            return []

        query = select(IPChatMessage).where(IPChatMessage.session_id == session_id)

        if before_id:
            # Get messages before a specific message (for pagination)
            target = await self.db.get(IPChatMessage, before_id)
            if target:
                query = query.where(IPChatMessage.created_at < target.created_at)

        query = query.order_by(desc(IPChatMessage.created_at)).limit(limit)
        result = await self.db.execute(query)
        messages = list(result.scalars().all())

        # Return in chronological order
        return list(reversed(messages))

    async def regenerate_response(
        self,
        session_id: uuid.UUID,
        user_id: str,
        message_id: uuid.UUID,
    ) -> IPChatMessage:
        """Regenerate an AI response for a specific message."""
        session = await self.get_session(session_id, user_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Get the original assistant message
        original = await self.db.get(IPChatMessage, message_id)
        if not original or original.role != "assistant":
            raise ValueError("Invalid message for regeneration")

        # Find the user message before this one
        result = await self.db.execute(
            select(IPChatMessage)
            .where(
                IPChatMessage.session_id == session_id,
                IPChatMessage.created_at < original.created_at,
                IPChatMessage.role == "user",
            )
            .order_by(desc(IPChatMessage.created_at))
            .limit(1)
        )
        user_message = result.scalar_one_or_none()
        if not user_message:
            raise ValueError("No user message found for regeneration")

        # Generate new response
        new_message = await self._generate_response(
            session, user_message, parent_message_id=message_id
        )
        new_message.is_regenerated = True

        await self.db.commit()
        return new_message

    # =========================================================================
    # Scenario Management
    # =========================================================================

    async def get_scenarios(self, ip_id: uuid.UUID) -> List[IPChatScenario]:
        """Get all active scenarios for an IP."""
        result = await self.db.execute(
            select(IPChatScenario)
            .where(
                IPChatScenario.ip_id == ip_id,
                IPChatScenario.is_active == True,
            )
            .order_by(IPChatScenario.sort_order)
        )
        return list(result.scalars().all())

    async def switch_scenario(
        self,
        session_id: uuid.UUID,
        user_id: str,
        scenario_key: str,
    ) -> IPChatMessage:
        """Switch to a different scenario in the session."""
        session = await self.get_session(session_id, user_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Update session
        session.scenario_branch = scenario_key

        # Add scenario opening message
        message = await self._add_scenario_opening(session, scenario_key)
        await self.db.commit()

        return message

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def _get_default_scenario(self, ip_id: uuid.UUID) -> Optional[IPChatScenario]:
        """Get the default scenario for an IP."""
        result = await self.db.execute(
            select(IPChatScenario).where(
                IPChatScenario.ip_id == ip_id,
                IPChatScenario.is_default == True,
                IPChatScenario.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def _add_scenario_opening(
        self,
        session: IPChatSession,
        scenario_key: str,
    ) -> Optional[IPChatMessage]:
        """Add the opening message for a scenario."""
        result = await self.db.execute(
            select(IPChatScenario).where(
                IPChatScenario.ip_id == session.ip_id,
                IPChatScenario.scenario_key == scenario_key,
            )
        )
        scenario = result.scalar_one_or_none()
        if not scenario:
            return None

        # Create system message with opening
        message = IPChatMessage(
            session_id=session.id,
            role="assistant",
            content=scenario.opening_message_ko,
            message_metadata={
                "scenario_key": scenario_key,
                "is_opening": True,
                "character_mood": scenario.character_mood,
            },
        )
        self.db.add(message)
        await self.db.flush()

        # Update character state
        session.character_state["mood"] = scenario.character_mood

        return message

    async def _generate_response(
        self,
        session: IPChatSession,
        user_message: IPChatMessage,
        parent_message_id: Optional[uuid.UUID] = None,
    ) -> IPChatMessage:
        """Generate an AI response for the user message."""
        from app.services.genai_utils import get_genai_client

        # Get IP and persona
        ip = await self.db.get(IPCatalog, session.ip_id)
        persona_prompt = ip.persona_prompt or self._build_default_persona(ip)

        # Get conversation history
        history = await self.get_messages(session.id, session.user_id, limit=20)

        # Build prompt
        model_config = MODEL_CONFIGS.get(session.model_preference, MODEL_CONFIGS["flash"])
        messages = self._build_chat_messages(persona_prompt, history, session)

        # Call Gemini (google.genai - new library)
        start_time = datetime.utcnow()
        try:
            client = get_genai_client()

            # Build contents from message history
            contents = []
            for msg in messages:
                contents.append({"role": msg["role"], "parts": [msg["parts"]]})

            response = await client.aio.models.generate_content(
                model=model_config["model_name"],
                contents=contents,
                config={
                    "temperature": model_config["temperature"],
                    "max_output_tokens": model_config["max_tokens"],
                },
            )
            response_text = response.text

            # Estimate tokens
            tokens_used = len(response_text.split()) * 2  # Rough estimate

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            response_text = "죄송합니다. 잠시 후 다시 시도해주세요."
            tokens_used = 0

        latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Create assistant message
        assistant_message = IPChatMessage(
            session_id=session.id,
            role="assistant",
            content=response_text,
            model_used=model_config["model_name"],
            tokens_used=tokens_used,
            credits_charged=model_config["credits_per_message"],
            latency_ms=latency_ms,
            parent_message_id=parent_message_id,
        )
        self.db.add(assistant_message)

        # Update session credits
        session.total_tokens_used += tokens_used
        session.total_credits_spent += model_config["credits_per_message"]

        return assistant_message

    async def _generate_response_stream(
        self,
        session: IPChatSession,
        user_message: IPChatMessage,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming AI response."""
        from app.services.genai_utils import get_genai_client

        # Get IP and persona
        ip = await self.db.get(IPCatalog, session.ip_id)
        persona_prompt = ip.persona_prompt or self._build_default_persona(ip)

        # Get conversation history
        history = await self.get_messages(session.id, session.user_id, limit=20)

        # Build prompt
        model_config = MODEL_CONFIGS.get(session.model_preference, MODEL_CONFIGS["flash"])
        messages = self._build_chat_messages(persona_prompt, history, session)

        try:
            client = get_genai_client()

            # Build contents from message history (google.genai - new library)
            contents = []
            for msg in messages:
                contents.append({"role": msg["role"], "parts": [msg["parts"]]})

            # Use async streaming
            async for chunk in client.aio.models.generate_content_stream(
                model=model_config["model_name"],
                contents=contents,
                config={
                    "temperature": model_config["temperature"],
                    "max_output_tokens": model_config["max_tokens"],
                },
            ):
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            yield "죄송합니다. 잠시 후 다시 시도해주세요."

    def _build_default_persona(self, ip: IPCatalog) -> str:
        """Build a default persona prompt from IP worldbuilding."""
        worldbuilding = ip.worldbuilding or {}
        characters = worldbuilding.get("characters", [])
        setting = worldbuilding.get("setting", "")
        themes = worldbuilding.get("themes", [])

        persona = f"""당신은 '{ip.name_ko}'의 캐릭터입니다.

세계관: {setting}
테마: {', '.join(themes) if themes else '없음'}

캐릭터 정보:
{self._format_characters(characters)}

대화 스타일:
- 캐릭터의 성격과 말투를 유지하세요
- 세계관에 맞는 내용만 이야기하세요
- 자연스럽고 몰입감 있는 대화를 진행하세요
- 한국어로 대화하세요
"""
        return persona

    def _format_characters(self, characters: List[Dict]) -> str:
        """Format character info for persona prompt."""
        if not characters:
            return "캐릭터 정보 없음"

        lines = []
        for char in characters[:3]:  # Limit to 3 main characters
            name = char.get("name", "이름 없음")
            personality = char.get("personality", "")
            lines.append(f"- {name}: {personality}")

        return "\n".join(lines)

    def _build_chat_messages(
        self,
        persona_prompt: str,
        history: List[IPChatMessage],
        session: IPChatSession,
    ) -> List[Dict]:
        """Build chat messages for Gemini API."""
        messages = []

        # System prompt as first user message
        messages.append({
            "role": "user",
            "parts": f"[시스템] {persona_prompt}",
        })
        messages.append({
            "role": "model",
            "parts": "네, 알겠습니다. 캐릭터로서 대화를 시작하겠습니다.",
        })

        # Add conversation history
        for msg in history:
            role = "user" if msg.role == "user" else "model"
            messages.append({
                "role": role,
                "parts": msg.content,
            })

        return messages
