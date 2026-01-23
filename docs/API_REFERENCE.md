# Vivid API Reference

> **Version**: 1.1
> **Last Updated**: 2026-01-24
> **Base URL**: `http://localhost:8100` (development)
> **Authentication**: Google OAuth session cookie, or `X-User-Id` header (dev only)

> [!NOTE]
> **2026-01-24 변경사항**: Director API 4개 함수 제거됨 (`getVibePresets`, `interpretVibe`, `checkDnaCompliance`, `analyzeForeshadow`). 대신 Dimension API 사용 권장.

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
    "page_context": "/dimension/prompt"
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
    "duration": 6,
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
| `duration` | integer | ❌ | `6` | Video duration in seconds (4-8) |
| `language` | string | ❌ | `"ko"` | Output language (ko/en) |
| `model` | string | ❌ | `"gemini-3-flash-preview"` | AI model |

#### Response

```json
{
  "success": true,
  "capsule_id": "teaching.prompt.generate",
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
      "duration": "6 seconds",
      "fps": "24"
    }
  },
  "metrics": {
    "latency_ms": 1234,
    "tokens": 842,
    "model": "gemini-3-flash-preview"
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
    "prompt": "핸드헬드 감성, 야간 네온, 인물 클로즈업 강조",
    "scene_count": 5,
    "language": "ko",
    "model": "gemini-3-flash-preview"
  }'
```

#### Response

```json
{
  "success": true,
  "capsule_id": "teaching.storyboard.create",
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
  "metrics": {
    "latency_ms": 1460,
    "tokens": 1034,
    "model": "gemini-3-flash-preview"
  }
}
```

---

### 2.3 Image Prompt (3D Ambience)

**Endpoint**: `POST /api/dimension/3d/generate`

Generate detailed image prompts for Midjourney/DALL-E.

#### Request

```bash
curl -X POST http://localhost:8100/api/dimension/3d/generate \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{
    "description": "비 오는 밤, 네온 간판이 반사되는 좁은 골목",
    "style": "photorealistic",
    "aspect_ratio": "16:9",
    "model": "gemini-3-flash-preview"
  }'
```

#### Response

```json
{
  "success": true,
  "capsule_id": "teaching.image.generate",
  "output": {
    "prompt": "Photorealistic rainy night alley with neon reflections, wet pavement, cinematic depth of field...",
    "negative_prompt": "overexposed, noisy, low detail",
    "style_notes": "moody, glossy surfaces, high contrast",
    "aspect_ratio": "16:9"
  },
  "metrics": {
    "latency_ms": 1180,
    "tokens": 760,
    "model": "gemini-3-flash-preview"
  }
}
```

---

### 2.4 Reference Analysis (4D Moment)

**Endpoint**: `POST /api/dimension/4d/analyze`

Analyze uploaded reference images/videos for style extraction.

#### Request

```bash
curl -X POST http://localhost:8100/api/dimension/4d/analyze \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{
    "video_description": "느릿한 롱테이크로 인물의 고독을 보여주는 흑백 단편",
    "focus_areas": ["cinematography", "editing", "color"],
    "analysis_depth": "standard",
    "output_format": "structured",
    "model": "gemini-3-flash-preview"
  }'
```

#### Response

```json
{
  "success": true,
  "capsule_id": "teaching.reference.analyze",
  "output": {
    "cinematography": "Static wide frames, long holds to emphasize isolation.",
    "editing": "Minimal cuts, dissolve used only for time shifts.",
    "color": "Monochrome with high contrast, crushed blacks."
  },
  "metrics": {
    "latency_ms": 1735,
    "tokens": 1290,
    "model": "gemini-3-flash-preview"
  }
}
```

---

### 2.5 Aesthetic Director (AD)

**Endpoint**: `POST /api/dimension/aesthetic/direct`

Generate visual style guidelines with auteur matching (6 directors: Bong, Park, Shinkai, etc.).

#### Request

```bash
curl -X POST http://localhost:8100/api/dimension/aesthetic/direct \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{
    "concept": "추격 씬이 있는 도시 느와르 스릴러",
    "reference_style": "bong",
    "mood": "tense",
    "lighting_style": "low-key",
    "color_mood": "cool",
    "target_medium": "video",
    "use_rag": true,
    "model": "gemini-3-pro-preview"
  }'
```

#### Response

```json
{
  "success": true,
  "capsule_id": "dimension.aesthetic.direct",
  "output": {
    "visual_guidelines": {
      "composition": "Deep focus with foreground/background tension",
      "lighting": "High contrast chiaroscuro with neon accents",
      "camera": "Wide masters, sudden tight close-ups",
      "pacing": "Slow build to explosive action"
    },
    "color_palette": ["#1a1a2e", "#16213e", "#e94560", "#f1f1f1"],
    "style_keywords": ["noir", "urban", "tense", "symmetric framing"],
    "avoid_elements": ["handheld shaky cam", "oversaturated colors"],
    "auteur_influence": {
      "name": "봉준호",
      "key_techniques": ["Genre blending", "Class hierarchy symbolism"],
      "reference_works": ["기생충", "살인의 추억"]
    }
  },
  "metrics": {
    "latency_ms": 1682,
    "tokens": 1210,
    "model": "gemini-3-pro-preview"
  }
}
```

---

### 2.6 Persona Analysis (Abyss Mirror / 심연의 거울)

Multi-turn creative persona analysis using MBTI, blood type, and Saju (사주).

> **Flow**: `/mirror/init` → `/mirror/chat` (15+ turns) → `/mirror/export`

#### 2.6.1 Initialize Session

**Endpoint**: `POST /api/dimension/mirror/init`

Start a new persona analysis session with birth info.

```bash
curl -X POST http://localhost:8100/api/dimension/mirror/init \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{
    "mbti": "INTJ",
    "blood_type": "A",
    "birth_year": 1994,
    "birth_month": 3,
    "birth_day": 21,
    "birth_hour": 9,
    "gender": "M",
    "model": "gemini-3-flash-preview"
  }'
```

**Response**:
```json
{
  "success": true,
  "session_id": "abc-123-uuid",
  "saju": {
    "year_pillar": "甲戌",
    "month_pillar": "丁卯",
    "day_pillar": "庚午",
    "hour_pillar": "辛巳",
    "dominant_element": "금"
  },
  "initial_message": "🪞 **심연의 거울에 오신 것을 환영합니다.**\n...",
  "persona_data": {...},
  "completion_rate": 25.0
}
```

#### 2.6.2 Chat (Multi-turn)

**Endpoint**: `POST /api/dimension/mirror/chat`

Continue persona analysis conversation (minimum 15 turns for completion).

```bash
curl -X POST http://localhost:8100/api/dimension/mirror/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{
    "session_id": "abc-123-uuid",
    "user_message": "어린 시절 레고 조립에 몰입했어요",
    "persona_data": {...},
    "chat_history": [...],
    "current_stage": "intro",
    "model": "gemini-3-flash-preview"
  }'
```

**Response**:
```json
{
  "success": true,
  "ai_response": "레고 조립이군요! 구조적 사고와 창작의 결합...",
  "persona_data": {
    "psychology": {"maslow_level": {...}, "core_values": ["structure", "creation"]},
    "creativity": {"visual_style_affinity": ["architectural", "geometric"]}
  },
  "completion_rate": 35.0,
  "current_stage": "maslow",
  "is_complete": false,
  "trace_id": "trace-uuid",
  "evidence_refs": [],
  "confidence": 0.0,
  "is_crisis": false
}
```

#### 2.6.3 Export Preset

**Endpoint**: `POST /api/dimension/mirror/export`

Export completed persona as JSON preset.

```bash
curl -X POST http://localhost:8100/api/dimension/mirror/export \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{
    "persona_data": {...}
  }'
```

**Response**:
```json
{
  "success": true,
  "preset_json": "{\"meta\": {...}, \"psychology\": {...}, \"creativity\": {...}, \"persona\": {...}}",
  "download_filename": "abyss_mirror_creator_20260115_123456.json"
}
```

#### 2.6.4 Chat Stream (SSE)

**Endpoint**: `POST /api/dimension/mirror/chat/stream`

Real-time streaming version of chat (requires Run-Token).

> **Note**: Requires `X-Run-Token` header from Run-Token API.

---

### 2.7 Story Architect (STORY)

**Endpoint**: `POST /api/dimension/story/architect`

Generate structured scenarios with 3-act/hero/circular structures.

#### Request

```bash
curl -X POST http://localhost:8100/api/dimension/story/architect \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{
    "concept": "외로운 로봇이 감정을 배우는 이야기",
    "persona_data": "창작 DNA: melancholic, introspective",
    "reference_analysis": "레퍼런스: 네온 누아르, 롱테이크",
    "genre": "drama",
    "duration": 60,
    "structure": "3-act",
    "language": "ko",
    "model": "gemini-3-pro-preview"
  }'
```

#### Response

```json
{
  "success": true,
  "capsule_id": "dimension.story.architect",
  "output": {
    "title": "기계의 눈물",
    "logline": "폐공장의 로봇이 버려진 강아지를 만나 처음으로 슬픔을 경험한다.",
    "synopsis": "먼지 쌓인 공장에서 혼자 작동하는 로봇 유닛-7. 어느 날 비 내리는 밤, 상자 속 떨고 있는 강아지를 발견한다...",
    "structure": [
      {"act": 1, "description": "일상 속 고독", "duration": "15s", "emotion": "lonely"},
      {"act": 2, "description": "만남과 변화", "duration": "30s", "emotion": "curious"},
      {"act": 3, "description": "이별과 깨달음", "duration": "15s", "emotion": "bittersweet"}
    ],
    "characters": [
      {"name": "유닛-7", "role": "protagonist", "arc": "flat→growth", "traits": ["curious", "innocent"]}
    ],
    "themes": ["고독", "감정의 발견", "인간성"],
    "visual_motifs": ["비", "녹슨 금속", "따뜻한 빛"],
    "next_dimension": "storyboard-sketch"
  },
  "metrics": {
    "latency_ms": 2100,
    "tokens": 1620,
    "model": "gemini-3-pro-preview"
  }
}
```

---

### 2.8 Sound Crafter (SOUND)

**Endpoint**: `POST /api/dimension/sound/craft`

Generate music/sound prompts with platform-optimized guidance.

#### Request

```bash
curl -X POST http://localhost:8100/api/dimension/sound/craft \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{
    "concept": "로봇의 슬픔을 표현하는 감성 피아노 음악",
    "storyboard": "장면 1: 비 오는 폐공장, 장면 2: 로봇의 멈칫",
    "sound_type": "bgm",
    "mood": "cinematic",
    "genre": "drama",
    "tempo": "slow",
    "duration": 60,
    "target_platform": "youtube",
    "language": "ko",
    "model": "gemini-3-flash-preview"
  }'
```

#### Response

```json
{
  "success": true,
  "capsule_id": "dimension.sound.craft",
  "output": {
    "music_prompt": "Melancholic solo piano with soft strings, building emotional tension, cinematic atmosphere, gentle arpeggios fading into silence",
    "style_tags": ["cinematic", "emotional", "piano", "ambient", "sad"],
    "bpm_range": "60-80 BPM",
    "key_signature": "D minor",
    "instrumentation": ["piano", "strings", "ambient pads"],
    "dynamics": "Starts pianissimo, builds to mezzo-forte climax, fades to silence"
  },
  "metrics": {
    "latency_ms": 1320,
    "tokens": 910,
    "model": "gemini-3-flash-preview"
  }
}
```

---

### 2.9 Quality Check (QC)

**Endpoint**: `POST /api/dimension/quality/check`

Evaluate content quality across 6 criteria: clarity, specificity, creativity, coherence, grammar, and impact.

#### Request

```bash
curl -X POST http://localhost:8100/api/dimension/quality/check \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{
    "content": "A cinematic shot of a lonely robot...",
    "content_type": "prompt",
    "inspection_mode": "comprehensive",
    "criteria": ["clarity", "creativity", "coherence"],
    "threshold": 0.7,
    "model": "gemini-3-flash-preview"
  }'
```

#### Response

```json
{
  "success": true,
  "capsule_id": "dimension.quality.check",
  "output": {
    "overall_score": 82,
    "criteria_scores": {
      "clarity": 85,
      "creativity": 80,
      "coherence": 81
    },
    "issues": [
      {"severity": "minor", "description": "Lighting direction could be more specific"}
    ],
    "suggestions": [
      "Add specific time of day for lighting consistency",
      "Consider adding camera movement descriptor"
    ]
  },
  "metrics": {
    "latency_ms": 980,
    "tokens": 640,
    "model": "gemini-3-flash-preview"
  }
}
```

---

### 2.10 Creative Editor (CE)

**Endpoint**: `POST /api/dimension/quality/editor`

Generate editorial critique and revision suggestions with 4 persona modes.

#### Request

```bash
curl -X POST http://localhost:8100/api/dimension/quality/editor \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{
    "content": "폐공장에서 로봇이 강아지를 만나 슬퍼한다.",
    "context": "SF 감성 드라마, 60초 쇼트폼",
    "persona": "Senior Editor",
    "use_rag": true,
    "model": "gemini-3-flash-preview"
  }'
```

#### Response

```json
{
  "success": true,
  "capsule_id": "dimension.quality.editor",
  "output": {
    "critique": {
      "narrative_score": 75,
      "visual_score": 60,
      "pacing_score": 70,
      "issues": [
        "시각적 디테일 부족",
        "감정 전개가 급함"
      ]
    },
    "original_content": "폐공장에서 로봇이 강아지를 만나 슬퍼한다.",
    "improved_content": "녹슨 기어가 굴러다니는 폐공장. 유닛-7의 광학 센서가 비에 젖은 상자를 감지한다. 안에서 미약한 체온 신호. 강아지다. 로봇의 서보 모터가 처음으로 멈칫한다.",
    "changes_made": [
      "배경 디테일 추가",
      "로봇 시점 서술 강화",
      "감정 암시적 표현"
    ]
  },
  "metrics": {
    "latency_ms": 1120,
    "tokens": 720,
    "model": "gemini-3-flash-preview"
  }
}
```

---

### 2.11 Veo Video Generation (VEO)

**Endpoint**: `POST /api/dimension/veo/generate`  
**Endpoint (SSE)**: `POST /api/dimension/veo/generate/stream`

Generate actual videos using Veo 3.1 (SSE streaming for progress).

#### Request

```bash
curl -X POST http://localhost:8100/api/dimension/veo/generate \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{
    "prompt": "A slow dolly-in on a neon-lit alley, rain reflections, cinematic mood",
    "negative_prompt": "blurry, low quality",
    "aspect_ratio": "16:9",
    "duration": 6,
    "style": "cinematic",
    "seed": 42,
    "model": "veo-3.1-generate-preview"
  }'
```

#### Response (Non-Streaming)

```json
{
  "success": true,
  "capsule_id": "veo.video.generate",
  "output": {
    "video_uri": "gs://bucket/videos/user123/veo_abc123.mp4",
    "duration_ms": 6000,
    "metadata": {
      "aspect_ratio": "16:9",
      "fps": 24
    }
  },
  "metrics": {
    "latency_ms": 6000,
    "tokens": 0,
    "model": "veo-3.1-generate-preview"
  }
}
```

#### SSE Stream Example

```
data: {"type":"progress","progress":0.1,"message":"요청 접수"}
data: {"type":"progress","progress":0.6,"message":"렌더링 중"}
data: {"type":"result","output":{"video_uri":"gs://bucket/videos/user123/veo_abc123.mp4","duration_ms":6000}}
```

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
