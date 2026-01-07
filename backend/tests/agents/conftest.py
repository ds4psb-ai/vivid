"""Test fixtures for agent integration tests."""
import asyncio
import uuid
from datetime import datetime
from typing import AsyncGenerator, List
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.agents.agent_types import (
    AgentMessage,
    AgentRole,
    AgentState,
    ToolCall,
    ToolContext,
    ToolResult,
    ToolSpec,
    ToolTaskState,
    ToolRegistry,
)
from app.agents.model_clients import GeminiModelClient
from app.models import AgentSession, WorkflowState
from app.database import Base


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """In-memory SQLite for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_agent_session(test_db: AsyncSession) -> AgentSession:
    """Create a test agent session."""
    session = AgentSession(
        id=uuid.uuid4(),
        status="active",
        title="Test Session",
        owner_id="test-user",
        meta={},
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)
    return session


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_gemini_client() -> MagicMock:
    """Mock Gemini API client for testing without API calls."""
    client = MagicMock(spec=GeminiModelClient)
    
    # Default complete response
    async def mock_complete(messages, tools=None):
        return AgentMessage(
            role=AgentRole.ASSISTANT,
            content="Mock response from Gemini",
            tool_calls=[],
        )
    
    client.complete = AsyncMock(side_effect=mock_complete)
    return client


@pytest.fixture
def mock_gemini_with_tool_calls() -> MagicMock:
    """Mock Gemini client that returns tool calls."""
    client = MagicMock(spec=GeminiModelClient)
    
    async def mock_complete(messages, tools=None):
        return AgentMessage(
            role=AgentRole.ASSISTANT,
            content="",
            tool_calls=[
                ToolCall(
                    id="call-1",
                    name="test_tool",
                    arguments={"param": "value"},
                )
            ],
        )
    
    client.complete = AsyncMock(side_effect=mock_complete)
    return client


# =============================================================================
# Tool Fixtures
# =============================================================================

@pytest.fixture
def instant_tool():
    """Tool that executes instantly for overhead testing."""
    async def handler(ctx: ToolContext, call: ToolCall) -> ToolResult:
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.COMPLETED,
            output={"result": "instant"},
        )
    
    return ToolSpec(
        name="instant_tool",
        description="Instant test tool",
        input_schema={"type": "object", "properties": {}},
    ), handler


@pytest.fixture
def slow_tool():
    """Tool that takes 150 seconds - triggers timeout."""
    async def handler(ctx: ToolContext, call: ToolCall) -> ToolResult:
        await asyncio.sleep(150)  # Will be cancelled by timeout
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.COMPLETED,
            output={"result": "slow"},
        )
    
    return ToolSpec(
        name="slow_tool",
        description="Slow tool for timeout testing",
        input_schema={"type": "object", "properties": {}},
    ), handler


@pytest.fixture
def flaky_tool():
    """Tool that fails N times then succeeds - for retry testing."""
    call_count = {"value": 0}
    
    async def handler(ctx: ToolContext, call: ToolCall) -> ToolResult:
        call_count["value"] += 1
        
        if call_count["value"] < 3:
            return ToolResult(
                tool_call_id=call.id,
                name=call.name,
                status=ToolTaskState.FAILED,
                error="temporary_failure",
            )
        
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.COMPLETED,
            output={"result": "success", "attempts": call_count["value"]},
        )
    
    return ToolSpec(
        name="flaky_tool",
        description="Flaky tool for retry testing",
        input_schema={"type": "object", "properties": {}},
    ), handler, call_count


# =============================================================================
# State Fixtures
# =============================================================================

@pytest.fixture
def sample_messages() -> List[AgentMessage]:
    """Sample conversation messages."""
    return [
        AgentMessage(role=AgentRole.USER, content="안녕하세요"),
        AgentMessage(role=AgentRole.ASSISTANT, content="안녕하세요! 무엇을 도와드릴까요?"),
        AgentMessage(role=AgentRole.USER, content="프롬프트 만들어주세요"),
    ]


@pytest.fixture
def long_conversation() -> List[AgentMessage]:
    """Long conversation for context window testing (100 messages)."""
    messages = []
    for i in range(100):
        role = AgentRole.USER if i % 2 == 0 else AgentRole.ASSISTANT
        content = f"테스트 메시지 #{i}. " + ("내용 " * 50)  # ~200 chars each
        messages.append(AgentMessage(role=role, content=content))
    return messages


@pytest.fixture
def agent_state(sample_messages: List[AgentMessage]) -> AgentState:
    """Sample agent state."""
    return AgentState(
        session_id="test-session-id",
        messages=sample_messages,
        summary="",
    )


# =============================================================================
# Registry Fixtures
# =============================================================================

@pytest.fixture
def tool_registry_with_instant(instant_tool) -> ToolRegistry:
    """ToolRegistry with instant tool registered."""
    spec, handler = instant_tool
    registry = ToolRegistry()
    registry.register(spec, handler)
    return registry


@pytest.fixture
def tool_registry_with_slow(slow_tool) -> ToolRegistry:
    """ToolRegistry with slow tool registered."""
    spec, handler = slow_tool
    registry = ToolRegistry()
    registry.register(spec, handler)
    return registry
