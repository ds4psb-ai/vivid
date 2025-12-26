# Vivid Node Canvas (MVP scaffold)

This repo bootstraps the Node Canvas MVP described in the Vivid docs. The focus is a fast, minimal base for:

- Visual node canvas (drag, connect, inspect)
- Persisted canvases (save/load) using JSON graphs
- Future hooks for GA/RL optimization and template marketplace

## Scope distilled from Vivid docs

- Canvas model: nodes + connections + metadata + versioning
- Node types grouped into input, style, customization, processing, output, capsule
- Processing includes auto-calc, GA suggestions, and RL feedback loops
- Templates are first-class objects (public share + marketplace later)
- MVP path: build canvas UI + persistence first, add GA/RL after
- NotebookLM/Opal outputs flow through **Sheets Bus → DB SoR** (Derived only)
- NotebookLM은 **지식/가이드 레이어** (클러스터 노트북, 오마주/변주 가이드, 템플릿 적합도 제안)
- Video 이해는 Gemini 구조화 출력으로 **DB SoR**에 적재 후 NotebookLM 소스로 사용
- Pattern Library/Trace records the repeatable auteur rules
- NotebookLM/Opal Ultra 구독 전제 (다중 출력/다국어 활용)
- 흐름/역할 정본: `10_PIPELINES_AND_USER_FLOWS.md`, 원칙 정본: `20_VIVID_ARCHITECTURE_EVOLUTION_CODEX.md`

## Tech baseline

- Frontend: Next.js + ReactFlow
- Backend: FastAPI + async SQLAlchemy
- Storage: Postgres JSONB for canvas graphs
- Data Bus (MVP): Google Sheets (staging) → DB (source of record)

## Docs index (핵심)

- 문서 맵: `00_DOCS_INDEX.md`

Canonical anchors:
- `20_VIVID_ARCHITECTURE_EVOLUTION_CODEX.md`
- `10_PIPELINES_AND_USER_FLOWS.md`
- `05_CAPSULE_NODE_SPEC.md`
- `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`
- `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`

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
Note: if you use Notebook Library, set `VIVID_NOTEBOOK_LIBRARY_CSV_URL` (and optional `VIVID_NOTEBOOK_ASSETS_CSV_URL`) or ranges too.

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
- Postgres: localhost:5433 (db: vivid_canvas)

Reserved if you add services later:
- Redis: 6380
- Neo4j: 7475 / 7688

## API

- GET /api/v1/canvases/
- POST /api/v1/canvases/
- POST /api/v1/canvases/from-template
- GET /api/v1/canvases/{id}
- PATCH /api/v1/canvases/{id}
- GET /api/v1/templates/
- GET /api/v1/templates/{id}
- PATCH /api/v1/templates/{id}
- GET /api/v1/templates/{id}/versions
- GET /api/v1/capsules/
- GET /api/v1/capsules/{capsule_key}
- GET /api/v1/capsules/{capsule_key}/runs
- POST /api/v1/capsules/run
- GET /api/v1/capsules/run/{run_id}
- GET /api/v1/capsules/run/{run_id}/stream
- POST /api/v1/capsules/run/{run_id}/cancel
- WS /ws/runs/{run_id}
- GET /api/v1/capsules/{capsule_key}/runs/{run_id}/preview
- POST /api/v1/ingest/raw
- GET /api/v1/ingest/raw/{source_id}
- GET /api/v1/ingest/video-structured
- GET /api/v1/ingest/video-structured/{segment_id}
- GET /api/v1/ingest/raw/{source_id}/video-structured
- POST /api/v1/ingest/video-structured
- POST /api/v1/ingest/notebook
- GET /api/v1/ingest/notebook
- POST /api/v1/ingest/derive
- GET /api/v1/ingest/derive
- POST /api/v1/ingest/pattern-candidate
- POST /api/v1/runs/
- GET /api/v1/runs/{id}

Auth (MVP): send `X-User-Id` header for private resources.

## Graph data shape

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
