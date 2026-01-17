# Vivid Testing Guide

> **Version**: 2.0
> **Last Updated**: 2026-01-17

---

## Table of Contents

1. [Overview](#1-overview)
2. [Backend Testing (Python/pytest)](#2-backend-testing)
3. [Frontend Testing (TypeScript/Vitest)](#3-frontend-testing)
4. [Integration Testing](#4-integration-testing)
5. [Running Tests](#5-running-tests)
6. [Writing New Tests](#6-writing-new-tests)

---

## 1. Overview

### Test Framework Summary

| Layer | Framework | Config File | Coverage |
|-------|-----------|-------------|----------|
| Backend | pytest | `pytest.ini` | ~75% |
| Frontend | Vitest | `vitest.config.ts` | ~60% |
| E2E | Playwright | `playwright.config.ts` | Active |

### Current Test Coverage (2026-01-17)

| 영역 | 테스트 수 | 상태 |
|------|----------|------|
| Dimension Apps Security | 653+ | ✅ |
| VEO Video Maker | 85 | ✅ |
| Abyss Mirror | 67 | ✅ |
| Character Consistency | 40+ | ✅ |
| RAG System | 100+ | ✅ |
| UQSL | 124 | ✅ |

### Key Testing Principles

1. **Unit tests first**: Test individual functions in isolation
2. **Mock external services**: Gemini API, Veo, database
3. **Test edge cases**: Error handling, timeouts, rate limits
4. **Regression tests**: Add test for every bug fix

---

## 2. Backend Testing

### 2.1 Directory Structure

```
backend/tests/
├── agents/              # Agent and tool tests
│   ├── test_dimension_tools.py
│   ├── test_intent_router.py
│   └── test_evidence_loop.py
├── routers/             # API endpoint tests
│   ├── test_agent.py
│   ├── test_dimension.py
│   └── test_credits.py
├── services/            # Business logic tests
│   ├── test_credit_service.py
│   └── test_veo_service.py
├── conftest.py          # Shared fixtures
└── __init__.py
```

### 2.2 Key Fixtures (`conftest.py`)

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.main import app

@pytest.fixture
async def db_session():
    """Async database session for tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with AsyncSession(engine) as session:
        yield session

@pytest.fixture
def client():
    """FastAPI TestClient."""
    from fastapi.testclient import TestClient
    return TestClient(app)

@pytest.fixture
def mock_gemini(mocker):
    """Mock Gemini API responses."""
    return mocker.patch("app.gemini_client.GeminiClient.generate")
```

### 2.3 Example Test: Intent Router

```python
# tests/agents/test_intent_router.py
import pytest
from app.agents.intent_router import IntentRouter, Intent

class TestIntentRouter:
    def test_classify_prompt_generation(self):
        """Test Korean prompt generation intent."""
        router = IntentRouter()
        result = router.classify("Veo 프롬프트 만들어줘")
        assert result.intent == Intent.GENERATE_PROMPT
        assert result.confidence >= 0.8

    def test_classify_workflow_request(self):
        """Test workflow/autonomous mode triggers."""
        router = IntentRouter()
        result = router.classify("알아서 영상 만들어줘")
        assert result.intent == Intent.WORKFLOW_REQUEST

    def test_classify_english_trend(self):
        """Test English trend analysis (hardening fix)."""
        router = IntentRouter()
        result = router.classify("Analyze current viral trends on TikTok")
        assert result.intent in [Intent.ANALYZE_REFERENCE, Intent.GENERATE_PROMPT]
```

### 2.4 Example Test: Evidence Loop

```python
# tests/agents/test_evidence_loop.py
import pytest
from app.agents.evidence_loop import (
    EvidenceCollector,
    EvidenceConfig,
    record_tool_start,
    record_tool_success,
)

class TestEvidenceCollector:
    def test_thread_safety(self):
        """Test concurrent access doesn't cause race conditions."""
        import concurrent.futures
        collector = EvidenceCollector()

        def record():
            eid = collector.record_tool_start("session-1", "test_tool")
            collector.record_tool_success(eid, "session-1", "test_tool")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(record) for _ in range(100)]
            concurrent.futures.wait(futures)

        stats = collector.get_stats()
        assert stats["total_events"] <= 200  # Bounded buffer

    def test_rate_limiting(self):
        """Test rate limiting prevents event flooding."""
        config = EvidenceConfig(rate_limit_per_minute=5)
        collector = EvidenceCollector(config)

        for i in range(10):
            collector.record_tool_start("session-1", f"tool_{i}")

        stats = collector.get_stats()
        assert stats["total_events"] <= 5
        assert stats["dropped_count"] >= 5
```

---

## 3. Frontend Testing

### 3.1 Directory Structure

```
frontend/src/
├── lib/
│   ├── agent-event-handlers.test.ts
│   ├── sse-utils.test.ts
│   └── ...
├── hooks/
│   ├── useAsyncOperation.test.ts
│   └── ...
└── components/
    └── dimension/
        └── PromptGeneratorPanel.test.tsx (planned)
```

### 3.2 Vitest Configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      reporter: ['text', 'html'],
    },
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
});
```

### 3.3 Example Test: Event Handlers

```typescript
// src/lib/agent-event-handlers.test.ts
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { createEventHandlers, type AgentEventContext } from './agent-event-handlers';

describe('createEventHandlers', () => {
  let mockContext: AgentEventContext;

  beforeEach(() => {
    mockContext = {
      setMessages: vi.fn(),
      assistantMessageId: 'msg-1',
      accumulatedContentRef: { current: '' },
      router: { push: vi.fn() } as any,
    };
  });

  describe('agent.delta', () => {
    test('accumulates text content', () => {
      const handlers = createEventHandlers(mockContext);
      handlers["agent.delta"]({ delta: "Hello" });
      handlers["agent.delta"]({ delta: " World" });
      expect(mockContext.accumulatedContentRef.current).toBe("Hello World");
    });
  });

  describe('agent.teaching_*', () => {
    test('maps to handleWorkflowStep', () => {
      const onWorkflowStep = vi.fn();
      mockContext.onWorkflowStep = onWorkflowStep;
      const handlers = createEventHandlers(mockContext);

      handlers["agent.teaching_start"]({ tool_name: "generate_veo_prompt" });

      expect(onWorkflowStep).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'start', dimension: 'Teaching' })
      );
    });
  });
});
```

---

## 4. Integration Testing

### 4.1 Agent Chat Flow

```python
# tests/integration/test_agent_chat_flow.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

class TestAgentChatIntegration:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_full_chat_flow(self, client, mock_gemini):
        """Test complete chat flow: message -> tool call -> response."""
        mock_gemini.return_value = MockLLMResponse(
            content="I'll generate a prompt for you!",
            tool_calls=[{"name": "generate_veo_prompt", "arguments": {...}}]
        )

        response = client.post(
            "/api/v1/agent/chat",
            json={"message": "시네마틱 도시 야경 프롬프트 만들어줘"},
            headers={"X-User-Id": "test-user"},
        )

        assert response.status_code == 200
        # SSE stream contains expected events
        events = parse_sse_stream(response.text)
        assert any(e["type"] == "agent.tool_calls" for e in events)
```

### 4.2 Credit Deduction Flow

```python
# tests/integration/test_credit_flow.py
class TestCreditIntegration:
    async def test_dimension_deducts_credits(self, db_session, client):
        """Test that dimension API deducts credits correctly."""
        # Setup: Give user credits
        await create_user_credits(db_session, "user-1", balance=100)

        # Execute
        response = client.post(
            "/api/dimension/1d/generate",
            json={"topic": "Test topic"},
            headers={"X-User-Id": "user-1"},
        )

        # Verify
        assert response.status_code == 200
        user_credits = await get_user_credits(db_session, "user-1")
        assert user_credits.balance == 95  # 100 - 5 (flash model cost)
```

---

## 5. Running Tests

### 5.1 Backend Tests

```bash
# Run all backend tests
cd backend && pytest -v

# Run specific test file
pytest tests/agents/test_intent_router.py -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run only marked tests
pytest -m "not slow" -v
```

### 5.2 Frontend Tests

```bash
# Run all frontend tests
cd frontend && bun test

# Run specific test file
bun test src/lib/agent-event-handlers.test.ts

# Run with coverage
bun test --coverage

# Watch mode (development)
bun test --watch
```

### 5.3 CI Integration

```yaml
# .github/workflows/test.yml (example)
name: Tests
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest -v

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v1
      - run: cd frontend && bun install
      - run: cd frontend && bun test
```

---

## 6. Writing New Tests

### 6.1 Backend Test Template

```python
import pytest
from unittest.mock import MagicMock, patch

class TestYourFeature:
    """Tests for [feature name]."""

    @pytest.fixture
    def setup_data(self):
        """Setup test data."""
        return {"key": "value"}

    def test_happy_path(self, setup_data):
        """Test normal operation."""
        result = your_function(setup_data)
        assert result.success is True

    def test_error_handling(self):
        """Test error cases."""
        with pytest.raises(ValueError):
            your_function(invalid_data)

    @patch("app.external_service.call")
    def test_with_mock(self, mock_call):
        """Test with mocked external service."""
        mock_call.return_value = {"status": "ok"}
        result = your_function()
        mock_call.assert_called_once()
```

### 6.2 Frontend Test Template

```typescript
import { describe, test, expect, vi, beforeEach } from 'vitest';

describe('YourComponent/Function', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('should handle normal case', () => {
    const result = yourFunction({ input: 'test' });
    expect(result).toBe('expected');
  });

  test('should handle error case', () => {
    expect(() => yourFunction(null)).toThrow();
  });

  test('should work with mocks', () => {
    const mockFn = vi.fn().mockReturnValue('mocked');
    const result = yourFunction({ callback: mockFn });
    expect(mockFn).toHaveBeenCalledTimes(1);
  });
});
```

---

## Appendix: Test Coverage Summary (2026-01-17)

### Backend Test Counts

| 영역 | 테스트 수 | 핵심 파일 |
|------|----------|----------|
| Dimension Apps Security | 653+ | `tests/security/` |
| VEO Video Maker | 85 | `tests/routers/test_veo.py` |
| Abyss Mirror | 67 | `tests/routers/test_abyss_mirror.py` |
| Character Consistency | 40+ | `tests/routers/test_character_consistency.py` |
| RAG System | 100+ | `tests/rag/` |
| UQSL | 124 | `tests/uqsl/` |
| Agent Core | 50+ | `tests/agents/` |
| Credit Service | 30+ | `tests/services/test_credit_service.py` |

### Coverage Goals

| Area | Current | Target |
|------|---------|--------|
| Agent Core | 75% | 85% |
| Intent Router | 85% | 90% |
| Dimension Tools | 70% | 80% |
| RAG System | 80% | 90% |
| Credit Service | 75% | 85% |
| VEO/Video | 90% | 95% |

### E2E Test Files

| 영역 | 파일 | 상태 |
|------|------|------|
| Dimension | `e2e/dimension.spec.ts` | ✅ |
| Credits | `e2e/credits.spec.ts` | ✅ |
| Agent Chat | `e2e/agent-chat.spec.ts` | ✅ |
| Flow | `e2e/flow.spec.ts` | ✅ |
