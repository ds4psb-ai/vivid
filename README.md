# Crebit Studio (Dimension Tools + Train Workflow + Agent Chat)

This repo builds the chat-first agent, dimension miniapps, and train-style workflow UI described in the Crebit docs. The focus is a fast, minimal base for:

- Chokki Agent (chat-first): tool-aware chat + artifact previews (SSE streaming)
- Dimension tools (miniapps) for prompt/storyboard/image/reference
- Train workflow UI (Flow) for chaining tools with 3-option connectors
- Legacy canvas assets remain under `frontend/src/app/_deprecated`

## Scope distilled from Crebit docs (current code)

- Train workflow: tool chain planning + connector choices + sequential execution
- Dimension tools: teaching capsules backed by Gemini models (BYOK supported)
- Agent chat: SSE streaming + artifact previews
- Legacy canvas model: nodes + edges + versioning (kept for back-compat only)
- NotebookLM/Opal outputs flow through **Sheets Bus → DB SoR** (Derived only)
- NotebookLM은 **지식/가이드 레이어** (클러스터 노트북, 오마주/변주 가이드, 템플릿 적합도 제안)
- Video 이해는 Gemini 구조화 출력으로 **DB SoR**에 적재 후 NotebookLM 소스로 사용
- Pattern Library/Trace records the repeatable auteur rules
- NotebookLM/Opal Ultra 구독 전제 (다중 출력/다국어 활용)
- 흐름/역할 정본: `08_PIPELINES_AND_USER_FLOWS.md`, 원칙 정본: `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`

## Story-First Features (NEW: 2025-12-30, legacy UI)

바이럴 콘텐츠 제작을 위한 서사 중심 제어 시스템 (현재 UI는 `_deprecated`에 위치):

- **CanvasNarrativePanel**: 부조화 설계, 감정 곡선, 훅 스타일 3-Tab 구조
- **HookVariantSelector**: 8종 훅 스타일 (충격/호기심/감정/역설 등) + A/B 테스트
- **DNAComplianceViewer**: 브랜드 DNA 가이드라인 준수 리포트
- **MetricsDashboard**: 바이럴 성과 분석 + 인사이트 대시보드

**핵심 타입**: `frontend/src/types/storyFirst.ts` (HookVariant, NarrativeArc, Sequence 등)

## Agent Chat (Chokki)

- Global chat accordion is available in `AppShell` (all pages).
- Streaming SSE events update assistant messages, tool results, and artifacts.
- Audio Overview artifacts are wired; Storyboard/Shot List/Data Table are legacy capsule artifacts.
- Train workflow integration is in progress (Flow UI currently uses mock options).

## Tech baseline

- Frontend: Next.js + train workflow UI (+ legacy ReactFlow in `_deprecated`)
- Backend: FastAPI + async SQLAlchemy
- Storage: Postgres JSONB for sessions/telemetry (canvas graphs are legacy)
- Data Bus (MVP): Google Sheets (staging) → DB (source of record)

## Docs index (핵심)

- 문서 맵: `00_DOCS_INDEX.md`

Canonical anchors:
- `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
- `08_PIPELINES_AND_USER_FLOWS.md`
- `04_CAPSULE_NODE_SPEC.md`
- `19_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`
- `06_SHEETS_SCHEMA_V1.md`
- `07_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
- `09_DB_PROMOTION_RULES_V1.md`
- `24_CLAIM_EVIDENCE_TRACE_SPEC_V1.md`

## Local setup

### 1) Infra (Postgres only)

```bash
docker-compose up -d
```

### 2) Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8100
```

Optional: seed the 6 auteur templates and capsule specs
```bash
python scripts/seed_auteur_data.py
```

Or set in `.env`:
```bash
SEED_AUTEUR_DATA=true
```

Optional: enable external adapters (NotebookLM/Opal)
```bash
ENABLE_EXTERNAL_ADAPTERS=true
NOTEBOOKLM_API_URL=https://example.com/notebooklm
NOTEBOOKLM_API_KEY=your_key_here
OPAL_API_URL=https://example.com/opal
OPAL_API_KEY=your_key_here
EXTERNAL_ADAPTER_TIMEOUT=15
EXTERNAL_ADAPTER_RETRIES=1
```

Optional: promote Sheets Bus → DB SoR
```bash
# set SHEETS_MODE and URLs in backend/.env
python scripts/promote_from_sheets.py
```
Note: if you use Notebook Library, set `CREBIT_NOTEBOOK_LIBRARY_CSV_URL` (and optional `CREBIT_NOTEBOOK_ASSETS_CSV_URL`) or ranges too.

Demo: promote mock sheets data (CSV files in `backend/mock_sheets`)
```bash
backend/venv/bin/python backend/scripts/promote_demo.py
```

Demo (clean tables first):
```bash
backend/venv/bin/python backend/scripts/promote_demo.py --drop-all
```

Demo (custom mock dir):
```bash
backend/venv/bin/python backend/scripts/promote_demo.py --mock-dir /path/to/mock_sheets
```

### 3) Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Optional (private templates/canvases):
```bash
# in .env.local
NEXT_PUBLIC_USER_ID=demo-user
```

Optional (admin-only data visibility):
```bash
# in .env.local
NEXT_PUBLIC_ADMIN_MODE=true
```

## Ports (non-conflicting with komission)

- Frontend: http://localhost:3100
- Backend: http://localhost:8100
- Postgres: localhost:5433 (db: crebit_canvas)

Reserved if you add services later:
- Redis: 6379
- Neo4j: 7475 / 7688

## API (current routers)

- POST /api/teaching/prompt/generate
- POST /api/teaching/storyboard/create
- POST /api/teaching/image/generate
- POST /api/teaching/reference/analyze
- POST /api/v1/agent/chat
- POST /api/v1/agent/upload
- GET /api/v1/agent/sessions/{id}
- POST /api/v1/agent/sessions/{id}/approve
- POST /api/v1/agent/sessions/{id}/reject
- GET /api/v1/tools
- GET /api/v1/tools/for-agent
- GET /api/v1/tools/dimension/{1D|2D|3D|4D|5D}
- GET /api/v1/workflow/templates
- POST /api/v1/workflow/plan
- GET /api/v1/workflow/tools
- GET /api/v1/workflow/session/{id}
- POST /api/v1/workflow/session/{id}/advance
- GET /api/v1/credits/balance
- GET /api/v1/credits/transactions
- POST /api/v1/credits/topup
- POST /api/v1/credits/deduct (internal)
- GET /api/v1/auth/session
- POST /api/v1/auth/logout
- POST /api/v1/run-token/issue
- POST /api/v1/run-token/validate
- POST /api/v1/run-token/deduct
- POST /api/v1/run-token/refund
- GET /api/v1/run-token/status/{run_id}
- POST /api/v1/internal/credit-reserve (mTLS)
- POST /api/v1/internal/credit-commit (mTLS)
- POST /api/v1/internal/credit-rollback (mTLS)

Auth: Google OAuth + session cookie (X-User-Id header is dev fallback).

## Graph data shape (legacy canvas)

```json
{
  "nodes": [
    {
      "id": "node-id",
      "type": "input",
      "position": { "x": 0, "y": 0 },
      "data": { "label": "Character Input", "subtitle": "..." }
    },
    {
      "id": "capsule-1",
      "type": "capsule",
      "position": { "x": 360, "y": 220 },
      "data": {
        "label": "Auteur Capsule",
        "subtitle": "auteur.bong-joon-ho",
        "capsuleId": "auteur.bong-joon-ho",
        "capsuleVersion": "1.0.0",
        "params": {
          "style_intensity": 0.7,
          "pacing": "medium"
        },
        "locked": true
      }
    }
  ],
  "edges": [
    {
      "id": "edge-id",
      "source": "node-a",
      "target": "node-b"
    }
  ]
}
```
