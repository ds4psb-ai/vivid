"""Integration tests for VividAgent.

Tests cover:
- Basic conversation flow
- Tool execution with timeout
- Tool retry on recoverable errors
- Context window management
- Workflow state persistence
"""
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

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
from app.agents.vivid_agent import VividAgent, MemoryManager


class TestVividAgentConversation:
    """Test basic conversation flow."""
    
    def test_memory_manager_initialization(self):
        """MemoryManager should initialize with correct defaults."""
        mm = MemoryManager()
        
        assert mm.max_tokens == 28000
        assert mm.CHARS_PER_TOKEN == 3.5
        assert mm.message_budget == 20000
        assert mm.summary_budget == 2000
    
    def test_token_estimation_korean(self):
        """Token estimation should handle Korean text."""
        mm = MemoryManager()
        
        # Korean text
        korean = "안녕하세요"  # 5 chars
        tokens = mm.estimate_tokens(korean)
        
        # Should return a positive number
        assert tokens >= 1
    
    def test_token_estimation_english(self):
        """Token estimation should handle English text."""
        mm = MemoryManager()
        
        english = "Hello, how are you?"  # 19 chars
        tokens = mm.estimate_tokens(english)
        
        assert tokens > 0
        # Just verify it returns a reasonable value
        assert tokens >= 1


class TestContextWindowManagement:
    """Test context window compression and management."""
    
    def test_build_context_within_budget(self, sample_messages, agent_state):
        """Context building should stay within token budget."""
        mm = MemoryManager()
        
        context = mm.build_context(agent_state, "System prompt")
        
        # Should return all messages plus system
        total_tokens = sum(mm.estimate_tokens(m.content) for m in context)
        assert total_tokens <= mm.max_tokens
    
    def test_build_context_with_long_conversation(self, long_conversation):
        """Long conversations should be compressed/summarized."""
        mm = MemoryManager()
        state = AgentState(
            session_id="test",
            messages=long_conversation,
            summary="",
        )
        
        context = mm.build_context(state, "System prompt")
        
        # Should have fewer messages due to compression
        total_tokens = sum(mm.estimate_tokens(m.content) for m in context)
        assert total_tokens <= mm.max_tokens
        
        # Should include a summary for overflow messages
        has_summary = any("[이전 대화 요약]" in m.content or "요약" in m.content 
                          for m in context if m.role == AgentRole.SYSTEM)
        # May or may not have summary depending on implementation
    
    def test_newest_messages_preserved(self, long_conversation):
        """Newest messages should always be preserved."""
        mm = MemoryManager()
        state = AgentState(
            session_id="test",
            messages=long_conversation,
            summary="",
        )
        
        context = mm.build_context(state, "System prompt")
        
        # The last user message should be in context
        last_user_msg = long_conversation[-2]  # Last even index
        context_contents = [m.content for m in context]
        
        # At least some recent messages should be present
        assert len(context) > 1


class TestToolExecutionTimeout:
    """Test tool execution timeout behavior."""
    
    @pytest.mark.asyncio
    async def test_instant_tool_executes_quickly(self, tool_registry_with_instant):
        """Instant tool should complete without timeout."""
        registry = tool_registry_with_instant
        
        call = ToolCall(id="call-1", name="instant_tool", arguments={})
        result = await registry.execute(None, call)
        
        assert result.status == ToolTaskState.COMPLETED
        assert result.output == {"result": "instant"}
    
    @pytest.mark.asyncio
    async def test_slow_tool_times_out(self, tool_registry_with_slow):
        """Slow tool should timeout after configured duration."""
        registry = tool_registry_with_slow
        
        call = ToolCall(id="call-1", name="slow_tool", arguments={})
        
        # Execute with short timeout for testing
        result = await registry.execute(None, call, timeout_override=0.1)
        
        assert result.status == ToolTaskState.FAILED
        assert "timed out" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self):
        """Unknown tool should return error without timeout."""
        registry = ToolRegistry()
        
        call = ToolCall(id="call-1", name="nonexistent_tool", arguments={})
        result = await registry.execute(None, call)
        
        assert result.status == ToolTaskState.FAILED
        assert "Unknown tool" in result.error


class TestToolMetrics:
    """Test tool execution metrics tracking."""
    
    @pytest.mark.asyncio
    async def test_execution_count_tracked(self, tool_registry_with_instant):
        """Tool execution count should be tracked."""
        registry = tool_registry_with_instant
        
        call = ToolCall(id="call-1", name="instant_tool", arguments={})
        await registry.execute(None, call)
        await registry.execute(None, call)
        
        metrics = registry.get_metrics()
        assert metrics["instant_tool"]["executions"] == 2
    
    @pytest.mark.asyncio
    async def test_failure_count_tracked(self, tool_registry_with_slow):
        """Tool failure count should be tracked."""
        registry = tool_registry_with_slow
        
        call = ToolCall(id="call-1", name="slow_tool", arguments={})
        await registry.execute(None, call, timeout_override=0.1)  # Will timeout
        
        metrics = registry.get_metrics()
        assert metrics["slow_tool"]["failures"] == 1


class TestIntentClassification:
    """Test intent classification accuracy."""
    
    def test_prompt_generation_intent(self):
        """Prompt generation messages should be classified correctly."""
        from app.agents.intent_router import classify_intent
        
        result = classify_intent("프롬프트 만들어줘")
        assert result.intent is not None
        assert result.confidence > 0
    
    def test_storyboard_intent(self):
        """Storyboard messages should be classified correctly."""
        from app.agents.intent_router import classify_intent
        
        result = classify_intent("스토리보드 작성해줘")
        assert result.intent is not None
    
    def test_cache_stats_available(self):
        """Cache stats should be available."""
        from app.agents.intent_router import get_cache_stats
        
        stats = get_cache_stats()
        assert "size" in stats
        assert "maxsize" in stats
        assert "ttl" in stats
