# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## ⚡ Quick Rules (반드시 지킬 것)

### 검증 명령어
```bash
# Backend 변경 후 (필수)
cd backend && source venv/bin/activate && pytest --tb=short -q

# Frontend 변경 후 (필수)
cd frontend && npm run build
```

### 핵심 원칙
1. **확인 후 코딩**: `Grep`/`Read`로 파일 존재 확인 → 코드 작성
2. **테스트 동반**: 새 기능 추가 시 테스트도 함께 작성
3. **에러 처리 포함**: try-except, rollback 패턴 적용
4. **타입 명시**: Python type hints, TypeScript strict

### 환각 금지
```
❌ 존재하지 않는 파일/함수 참조 금지
❌ 추측으로 import 작성 금지
✅ 불확실하면 Grep으로 먼저 검색
```

---

## Project Overview

**Crebit Studio** - A full-stack platform for creative AI content generation.

| Layer | Component | Description |
|-------|-----------|-------------|
| **1** | Dimension Miniapps | 1D Origin, 2D Blueprint, 3D Ambience, 4D Moment |
| **2** | Agent Chat | Vivid Agent (Chokki) - chat-first orchestration |
| **3** | Workflow (Flow UI) | Train-based step execution |
| **∞** | Singularity | Template gallery for dimension combinations |

> **Canonical Docs**: See [00_DOCS_INDEX.md](file:///Users/ted/vivid/00_DOCS_INDEX.md) for the full documentation map.

---

## Quick Start

### Infrastructure
```bash
docker-compose up -d  # postgres:5433, redis:6380, qdrant:6333
```

### Backend
```bash
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8100

# DB
alembic upgrade head
python scripts/seed_auteur_data.py
```

### Frontend
```bash
cd frontend && npm run dev  # localhost:3100
```

### Ports
| Service | Port |
|---------|------|
| Frontend | 3100 |
| Backend | 8100 |
| Postgres | 5433 |
| Redis | 6380 |
| Qdrant | 6333 |

---

## Architecture

### Tech Stack
- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind, @xyflow/react
- **Backend**: FastAPI, Python 3.11, SQLAlchemy 2.0 async, Pydantic v2
- **Database**: PostgreSQL 16, Qdrant, Redis
- **AI**: Google Gemini API
- **Auth**: Google OAuth 2.0 (dev fallback: `X-User-Id` header)

### NotebookLM Integration (Playwright Automation)

All NotebookLM interactions (Create, Add Source, Query, Delete) are handled by `notebooklm_playwright.py` using **Chrome DevTools Protocol (CDP)**.
This bypasses the lack of an official API by executing internal RPC calls directly within an authenticated browser session.

#### Prerequisites
1. Chrome running: `--remote-debugging-port=9222`
2. User logged into NotebookLM in that Chrome session
3. `playwright` package installed

#### RPC Reference (verified 2026-01)
| RPC ID | Method | Parameters |
|--------|--------|------------|
| `CCqFvf` | CreateNotebook | `[title]` |
| `izAoDd` | AddSource | `[[[text, title, null, 1]], notebook_id, ...]` |
| `WWINqb` | DeleteNotebook | `[[notebook_id], [2]]` |
| `wXbhsf` | ListNotebooks | `[null, 1, null, [2]]` |
| `GenerateFreeFormStreamed` | Query | `[sources_array, query, null, [2,null,[1]], conv_id]` |

#### Key API
```python
async with PlaywrightNotebookLMClient(cdp_port=9222) as client:
    nb_id = await client.create_notebook("Title")
    source_id = await client.add_text_source(nb_id, "Doc", "Content...")
    result = await client.query(nb_id, "Question?", source_ids=[source_id])
    await client.delete_notebook(nb_id)
```

#### Troubleshooting
| Error | Cause | Fix |
|-------|-------|-----|
| 401/403 | Cookie fingerprint mismatch | Use CDP, not direct HTTP |
| 400 | Wrong source ID format | Use `[[sid]]` per source (2 brackets) |
| Login required | Session expired | Re-login in Chrome |


### API Endpoints (Primary)

| Endpoint | Handler | Description |
|----------|---------|-------------|
| `POST /api/dimension/1d/generate` | `dimension_adapter.py` | Veo Prompt (Origin) |
| `POST /api/dimension/2d/create` | `dimension_adapter.py` | Storyboard (Blueprint) |
| `POST /api/dimension/3d/generate` | `dimension_adapter.py` | Image Prompt (Ambience) |
| `POST /api/dimension/4d/analyze` | `dimension_adapter.py` | Reference Analysis (Moment) |
| `POST /api/v1/agent/chat` | `vivid_agent.py` | SSE Agent Chat |
| `POST /api/v1/workflow/plan` | `workflow_planner.py` | Workflow Planning |

---

## Key Files

### Backend
| File | Role |
|------|------|
| `main.py` | App bootstrap, 40+ routers |
| `config.py` | Pydantic settings |
| `dimension_adapter.py` | Capsule execution + credit deduction |
| `fixtures/dimension_capsules.py` | **SSoT for capsule specs & credit costs** |
| `vivid_agent.py` | Agent loop + memory |
| `credit_service.py` | Credit deduction/refund logic |

### Frontend
| File | Role |
|------|------|
| `lib/api.ts` | Typed API client |
| `components/AppShell.tsx` | Global layout |
| `contexts/DimensionSettingsContext.tsx` | Tool state |

---

## Legacy vs New

> [!WARNING]
> The codebase has migrated from "Teaching" to "Dimension" naming.

| Component | Legacy (v1) | Current (v2) |
|-----------|-------------|--------------|
| Router | `routers/teaching.py` | `routers/dimension.py` |
| Adapter | `teaching_adapter.py` | `dimension_adapter.py` |
| Fixtures | ❌ (deleted) | `fixtures/dimension_capsules.py` |
| Endpoints | `/api/teaching/*` | `/api/dimension/*` |

**The legacy `teaching.py` router has been deleted.** All functionality now lives in `dimension.py`.

---

## Adding New Features

### New Dimension Tool
1. Add request/response models → `routers/dimension.py`
2. Implement handler → `dimension_adapter.py`
3. Register tool → `agents/dimension_tools.py`
4. Add credit cost → `fixtures/dimension_capsules.py` (`DIMENSION_CAPSULES` list)

### New Agent Tool
1. Create handler in `agents/` directory
2. Register with `ToolRegistry` in `vivid_agent.py`
3. Define `ToolSpec` with `input_schema`

### New API Route
1. Create `routers/my_feature.py`
2. Include in `main.py` with prefix
3. Use `Depends(get_current_user)` for auth

---

## Environment Variables

### Backend `.env`
```bash
GEMINI_API_KEY=...
POSTGRES_USER=... POSTGRES_PASSWORD=... POSTGRES_DB=... POSTGRES_HOST=... POSTGRES_PORT=...
REDIS_URL=redis://localhost:6380
GOOGLE_CLIENT_ID=... GOOGLE_CLIENT_SECRET=...
SESSION_SECRET=...
```

### Frontend `.env.local`
```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8100
NEXT_PUBLIC_USER_ID=demo-user   # Dev override
```

---

## Credits System

- **SSoT**: [13_CREDITS_AND_BILLING_SPEC_V1.md](file:///Users/ted/vivid/13_CREDITS_AND_BILLING_SPEC_V1.md)
- **Consumption Order**: Promo → Subscription → Topup
- **BYOK**: Pass `X-Gemini-API-Key` header to bypass billing
- **Refund**: Automatic on failed generation

---

## RAG Integration (P1-P4 2026-01)

### evidence_refs SoR (Source of Record)

```
evidence_refs: List[str] = ["db:capsule_runs:{run_id}"]
```

| 형식 | 설명 |
|------|------|
| `db:capsule_runs:{uuid}` | CapsuleRun 기반 증거 |
| `db:rag_docs:4D:video_ref:{doc_id}` | 비디오 레퍼런스 |
| `db:rag_docs:3D:image_grid:{doc_id}` | 이미지 그리드 |

### Dataset Routing

| 앱 | Dimension | Datasets |
|----|-----------|----------|
| `teaching.reference.analyze` | 4D | `video_ref`, `film_analysis` |
| `teaching.image.generate` | 3D | `image_grid`, `visual_style` |

### Ingestion Scripts

```bash
# Video Reference 인제스션
python scripts/ingest_video_reference.py --input ../data/source_packs/video_refs.json

# Image Grid 인제스션
python scripts/ingest_image_grid.py --input ../data/source_packs/grids.json

# RAG 품질 리포트
python scripts/run_rag_quality_report.py --no-llm
```

### Key Files

| File | Role |
|------|------|
| `app/rag/app_manifest.py` | Dataset routing rules |
| `app/rag/tier1_dimension_rag.py` | Qdrant indexing |
| `app/rag/rag_suggestion_service.py` | evidence_refs 생성 |
| `scripts/ingest_video_reference.py` | 비디오 인제스션 |
| `scripts/ingest_image_grid.py` | 그리드 인제스션 |
| `scripts/run_rag_quality_report.py` | 품질 평가 CLI |

### Documentation

- [RAG_QUALITY.md](file:///Users/ted/vivid/docs/RAG_QUALITY.md) - 품질 평가 가이드

---

## Notes

- Legacy canvas code: `frontend/src/app/_deprecated/`
- Agent memory: 24-message cap + auto-summary
- Dev auth: `X-User-Id: dev-user-001` header
- Architecture philosophy: [15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md](file:///Users/ted/vivid/15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md)
