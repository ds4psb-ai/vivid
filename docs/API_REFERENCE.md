# Vivid API Reference

> **Version**: 1.0
> **Base URL**: `http://localhost:8100` (development)
> **Authentication**: Google OAuth session cookie, or `X-User-Id` header (dev only)

---

## Table of Contents

1. [Agent API](#1-agent-api)
2. [Dimension API](#2-dimension-api)
3. [Credits API](#3-credits-api)
4. [Workflow API](#4-workflow-api)
5. [Error Handling](#5-error-handling)

---

## 1. Agent API

Base path: `/api/v1/agent`

### 1.1 Chat (SSE Streaming)

**Endpoint**: `POST /api/v1/agent/chat`

Initiate a chat conversation with the AI agent. Responses are streamed via Server-Sent Events (SSE).

#### Request

```bash
curl -X POST http://localhost:8100/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -H "Accept: text/event-stream" \
  -d '{
    "message": "시네마틱한 도시 야경 영상을 만들어줘",
    "session_id": null,
    "model": "gemini-3-flash-preview",
    "attachments": [],
    "page_context": "/dimension/prompt-alchemy"
  }'
```

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | ✅ | User message (min 1 char) |
| `session_id` | string | ❌ | Existing session ID (null for new) |
| `model` | string | ❌ | LLM model (default: `gemini-3-flash-preview`) |
| `attachments` | array | ❌ | File attachments `[{name, mime_type, file_uri}]` |
| `page_context` | string | ❌ | Current page path for context |
| `metadata` | object | ❌ | Custom metadata |

#### SSE Event Types

| Event | Payload | Description |
|-------|---------|-------------|
| `agent.delta` | `{"delta": "..."}` | Text token streaming |
| `agent.tool_calls` | `{"tool_calls": [...]}` | Tool invocation |
| `agent.tool_result` | `{"name": "...", "status": "...", "output": {...}}` | Tool result |
| `agent.message` | `{"content": "..."}` | Final message |
| `agent.workflow_start` | `{"workflow_id": "...", "dimensions": [...]}` | Workflow started |
| `agent.workflow_complete` | `{"total_credits": N}` | Workflow finished |

#### Example SSE Stream

```
event: agent.delta
data: {"delta": "알겠습니다! "}

event: agent.delta
data: {"delta": "시네마틱한 "}

event: agent.tool_calls
data: {"tool_calls": [{"id": "call_1", "name": "generate_veo_prompt", "arguments": {...}}]}

event: agent.tool_result
data: {"name": "generate_veo_prompt", "status": "complete", "output": {"prompt": "..."}}

event: agent.message
data: {"content": "프롬프트가 생성되었습니다!"}
```

---

### 1.2 Get Session

**Endpoint**: `GET /api/v1/agent/sessions/{session_id}`

Retrieve a specific agent session with messages and artifacts.

#### Request

```bash
curl http://localhost:8100/api/v1/agent/sessions/abc123 \
  -H "X-User-Id: user123"
```

#### Response

```json
{
  "session_id": "abc123",
  "status": "active",
  "title": "도시 야경 영상 제작",
  "agent_model": "gemini-3-flash-preview",
  "metadata": {},
  "created_at": "2026-01-08T10:00:00Z",
  "updated_at": "2026-01-08T10:15:00Z",
  "messages": [...],
  "artifacts": [...]
}
```

---

### 1.3 Upload File

**Endpoint**: `POST /api/v1/agent/upload`

Upload a file for use in agent conversations (images, videos).

#### Request

```bash
curl -X POST http://localhost:8100/api/v1/agent/upload \
  -H "X-User-Id: user123" \
  -F "file=@reference.jpg"
```

#### Response

```json
{
  "file_uri": "gs://bucket/uploads/user123/abc123.jpg",
  "mime_type": "image/jpeg",
  "name": "reference.jpg"
}
```

---

## 2. Dimension API

Base path: `/api/dimension`

All dimension endpoints require authentication and consume credits based on the model used.

### 2.1 Prompt Generation (1D Origin)

**Endpoint**: `POST /api/dimension/1d/generate`

Generate Veo 3.1 video prompts from a topic.

#### Request

```bash
curl -X POST http://localhost:8100/api/dimension/1d/generate \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{
    "topic": "감성적인 도시 야경",
    "style": "cinematic",
    "mood": "dramatic",
    "duration": "15 seconds",
    "language": "en",
    "model": "gemini-3-flash-preview"
  }'
```

#### Request Body

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `topic` | string | ✅ | - | Video topic (max 500 chars) |
| `style` | string | ❌ | `"cinematic"` | Visual style |
| `mood` | string | ❌ | `"neutral"` | Emotional tone |
| `duration` | string | ❌ | `"15 seconds"` | Video duration hint |
| `language` | string | ❌ | `"ko"` | Output language (ko/en) |
| `model` | string | ❌ | `"gemini-3-flash-preview"` | AI model |

#### Response

```json
{
  "success": true,
  "output": {
    "prompt": "Cinematic aerial shot of a glowing cityscape...",
    "negative_prompt": "blurry, low quality, distorted...",
    "style": {
      "cinematography": "Aerial tracking shot",
      "lighting": "Golden hour with neon accents",
      "color_grade": "Teal and orange"
    },
    "technical": {
      "aspect_ratio": "16:9",
      "duration": "15 seconds",
      "fps": "24"
    }
  },
  "credit_cost": 5,
  "metrics": {
    "latency_ms": 1234
  }
}
```

---

### 2.2 Storyboard Creation (2D Blueprint)

**Endpoint**: `POST /api/dimension/2d/create`

Generate a visual storyboard with scene breakdowns.

#### Request

```bash
curl -X POST http://localhost:8100/api/dimension/2d/create \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{
    "concept": "도시 야경을 배경으로 한 감성 브이로그",
    "scene_count": 5,
    "language": "ko",
    "model": "gemini-3-flash-preview"
  }'
```

#### Response

```json
{
  "success": true,
  "output": {
    "scenes": [
      {
        "scene_number": 1,
        "description": "도시 스카이라인의 와이드 샷",
        "duration": "3s",
        "camera": "Fixed wide angle",
        "mood": "Establishing"
      },
      ...
    ],
    "total_duration": "15s"
  },
  "credit_cost": 8
}
```

---

### 2.3 Image Prompt (3D Ambience)

**Endpoint**: `POST /api/dimension/3d/generate`

Generate detailed image prompts for Midjourney/DALL-E.

---

### 2.4 Reference Analysis (4D Moment)

**Endpoint**: `POST /api/dimension/4d/analyze`

Analyze uploaded reference images/videos for style extraction.

---

### 2.5 Quality Check (QC)

**Endpoint**: `POST /api/dimension/qc/check`

Evaluate content quality across 6 criteria.

---

### 2.6 Veo Video Generation (VEO)

**Endpoint**: `POST /api/dimension/veo/generate/stream`

Generate actual videos using Veo 3.1 (SSE streaming for progress).

---

## 3. Credits API

Base path: `/api/v1/credits`

### 3.1 Get Balance

**Endpoint**: `GET /api/v1/credits/balance`

```bash
curl http://localhost:8100/api/v1/credits/balance \
  -H "X-User-Id: user123"
```

#### Response

```json
{
  "user_id": "user123",
  "balance": 500,
  "subscription_credits": 300,
  "topup_credits": 200,
  "promo_credits": 0,
  "promo_expires_at": null
}
```

---

### 3.2 Get Transactions

**Endpoint**: `GET /api/v1/credits/transactions`

```bash
curl "http://localhost:8100/api/v1/credits/transactions?limit=10&offset=0" \
  -H "X-User-Id: user123"
```

#### Response

```json
{
  "transactions": [
    {
      "id": "tx_123",
      "event_type": "usage",
      "amount": -5,
      "balance_snapshot": 495,
      "description": "1D Prompt Generation",
      "created_at": "2026-01-08T10:00:00Z"
    }
  ],
  "total": 42
}
```

---

### 3.3 Top Up Credits

**Endpoint**: `POST /api/v1/credits/topup`

```bash
curl -X POST http://localhost:8100/api/v1/credits/topup \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{"amount": 100, "pack_id": "starter"}'
```

---

## 4. Workflow API

Base path: `/api/v1/workflow`

### 4.1 Get Templates

**Endpoint**: `GET /api/v1/workflow/templates`

Get available workflow templates from the Singularity gallery.

---

### 4.2 Plan Workflow

**Endpoint**: `POST /api/v1/workflow/plan`

Create a workflow plan based on user intent.

---

## 5. Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Error message here",
  "error_code": "INSUFFICIENT_CREDITS"
}
```

### Common HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| `400` | Bad Request | Invalid input, validation failed |
| `401` | Unauthorized | Missing or invalid auth |
| `402` | Payment Required | Insufficient credits |
| `404` | Not Found | Session/resource not found |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Server Error | Internal error, retry later |

### Credit-Related Errors

```json
{
  "detail": "크레딧이 부족합니다. 현재: 3, 필요: 5",
  "error_code": "INSUFFICIENT_CREDITS",
  "required": 5,
  "available": 3
}
```

---

## Appendix: Credit Costs

| Dimension | Flash Model | Pro Model |
|-----------|-------------|-----------|
| 1D (Prompt) | 5 credits | 10 credits |
| 2D (Storyboard) | 8 credits | 15 credits |
| 3D (Image) | 5 credits | 10 credits |
| 4D (Reference) | 8 credits | 15 credits |
| QC (Quality) | 3 credits | 8 credits |
| AD (Aesthetic) | 5 credits | 12 credits |
| VEO (Video) | 20 credits | 40 credits |
