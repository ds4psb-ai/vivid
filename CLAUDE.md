# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

## Notes

- Legacy canvas code: `frontend/src/app/_deprecated/`
- Agent memory: 24-message cap + auto-summary
- Dev auth: `X-User-Id: dev-user-001` header
- Architecture philosophy: [15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md](file:///Users/ted/vivid/15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md)
