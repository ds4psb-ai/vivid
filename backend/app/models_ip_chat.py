"""IP Chat Models for Phase 10.

This module defines models for IP character real-time chat:
- IPChatSession: Chat session with an IP character
- IPChatMessage: Individual chat messages
- IPChatScenario: Branching scenario paths for characters
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class IPChatSession(Base):
    """IP Chat Session - Conversation session with an IP character.

    Each session tracks conversation state, model preference, and usage.
    """
    __tablename__ = "ip_chat_sessions"
    __table_args__ = (
        Index("ix_chat_session_user", "user_id", "last_message_at"),
        Index("ix_chat_session_ip", "ip_id"),
        Index("ix_chat_session_tenant", "tenant_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    ip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ip_catalog.id", ondelete="CASCADE"), nullable=False)
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)

    # Session metadata
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    character_state: Mapped[dict] = mapped_column(JSONB, default=dict)  # Character memory/emotional state
    scenario_branch: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # Current scenario path

    # Model configuration
    model_preference: Mapped[str] = mapped_column(String(32), default="flash")  # flash, pro, opus
    persona_mode: Mapped[str] = mapped_column(String(32), default="default")  # default, custom, roleplay

    # Usage stats
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    total_credits_spent: Mapped[int] = mapped_column(Integer, default=0)

    # UI state
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    messages: Mapped[List["IPChatMessage"]] = relationship("IPChatMessage", back_populates="session", cascade="all, delete-orphan")


class IPChatMessage(Base):
    """IP Chat Message - Individual message in a chat session.

    Supports text, media attachments, and conversation branching.
    """
    __tablename__ = "ip_chat_messages"
    __table_args__ = (
        Index("ix_chat_message_session", "session_id", "created_at"),
        Index("ix_chat_message_parent", "parent_message_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ip_chat_sessions.id", ondelete="CASCADE"), nullable=False)

    # Message content
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_urls: Mapped[list] = mapped_column(JSONB, default=list)  # Images, audio, video attachments

    # Model info
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    credits_charged: Mapped[int] = mapped_column(Integer, default=0)
    model_used: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    message_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)  # Scenario choices, emotions, etc.

    # Branching support
    is_regenerated: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_message_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    session: Mapped["IPChatSession"] = relationship("IPChatSession", back_populates="messages")


class IPChatScenario(Base):
    """IP Chat Scenario - Branching paths for character interactions.

    Defines starting scenarios and branch options for rich storytelling.
    """
    __tablename__ = "ip_chat_scenarios"
    __table_args__ = (
        Index("ix_chat_scenario_ip", "ip_id"),
        UniqueConstraint("ip_id", "scenario_key", name="uq_chat_scenario_ip_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ip_catalog.id", ondelete="CASCADE"), nullable=False)
    scenario_key: Mapped[str] = mapped_column(String(64), nullable=False)

    # Display info
    name_ko: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    description_ko: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Opening message
    opening_message_ko: Mapped[str] = mapped_column(Text, nullable=False)
    opening_message_en: Mapped[str] = mapped_column(Text, nullable=False)

    # Character setup
    character_mood: Mapped[str] = mapped_column(String(32), default="neutral")  # neutral, happy, sad, angry, etc.
    context_injection: Mapped[dict] = mapped_column(JSONB, default=dict)  # Additional RAG context

    # Branching
    branch_options: Mapped[list] = mapped_column(JSONB, default=list)  # [{key, label_ko, label_en}]

    # Metadata
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
