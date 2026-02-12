# CLAUDE.md

> Claude Code configuration file - Crebit Studio (Vivid)

---

## Quick Rules

### Verification Commands (Required)
```bash
cd backend && source venv/bin/activate && pytest --tb=short -q  # Backend
cd frontend && npm run build  # Frontend
```

### Core Principles
1. **Verify before coding**: Use `Grep`/`Read` to confirm file existence → then write code
2. **Include tests**: Write tests alongside new features
3. **Include error handling**: Apply try-except, rollback patterns
4. **Explicit types**: Python type hints, TypeScript strict

### No Hallucinations
- Do not reference non-existent files/functions
- Do not write speculative imports
- If unsure, search with Grep first

---

## P0: Required Reference Documents Before App/DB Work

**When working on app or DB-related tasks, you MUST read the following documents first:**

### 1. App Development Protocol
| Document | Path | Purpose |
|----------|------|---------|
| App Development Guide | `docs/DIMENSION_APP_DEVELOPER_GUIDE.md` | Standard app creation procedure |
| App YAML Schema | `config/apps/content/dimensions/*.yaml` | SSoT configuration |
| App Router Pattern | `backend/app/routers/dimension/_base.py` | Common utilities |

### 2. Per-App Research Documents (2026 Best Practices)
| App | Research Document |
|-----|-------------------|
| Abyss Mirror | `docs/research/01_ABYSS_MIRROR_RESEARCH.md` |
| Reference Decoder | `docs/research/02_REFERENCE_DECODER_RESEARCH.md` |
| Scenario Generator | `docs/research/03_SCENARIO_GENERATOR_RESEARCH.md` |
| Sound Crafter | `docs/research/04_SOUND_CRAFTER_RESEARCH.md` |
| Storyboard Sketcher | `docs/research/05_STORYBOARD_SKETCHER_RESEARCH.md` |
| Prompt Alchemy | `docs/research/06_PROMPT_ALCHEMY_RESEARCH.md` |
| Visual Realizer | `docs/research/07_VISUAL_REALIZER_RESEARCH.md` |
| Video Maker | `docs/research/08_VIDEO_MAKER_RESEARCH.md` |
| Quality Director | `docs/research/09_QUALITY_DIRECTOR_RESEARCH.md` |
| Aesthetic Director | `docs/research/10_AESTHETIC_DIRECTOR_RESEARCH.md` |

### 3. DB/Backend Protocol
| Document | Path | Purpose |
|----------|------|---------|
| Credit System | `docs/13_CREDITS_AND_BILLING_SPEC_V1.md` | Run-Token flow |
| Architecture Codex | `docs/15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md` | Design philosophy |
| Backend CLAUDE.md | `backend/CLAUDE.md` | DB/API patterns |
| **Railway Deployment** | `docs/RAILWAY_DEPLOYMENT_GUIDE.md` | Backend deployment (Railway) |
| **Vercel Deployment** | `docs/VERCEL_DEPLOYMENT_GUIDE.md` | Frontend deployment (Vercel) |

### 5. Railway Deployment Essentials (P0) - Backend

```bash
# Dockerfile - must use shell form ($PORT expansion)
CMD sh -c "uvicorn app.main:app --port ${PORT:-8080}"

# DATABASE_URL - specify asyncpg driver
DATABASE_URL=postgresql+asyncpg://...@postgres.railway.internal:5432/...

# Use private networking (egress free)
REDIS_URL=redis://...@redis.railway.internal:6379
```

**Important Notes:**
- Use only **one** of `railway.json` startCommand or Dockerfile CMD
- If variable references fail, hardcode them (`${{Service.VAR}}` → actual value)
- Details: `docs/RAILWAY_DEPLOYMENT_GUIDE.md`

### 6. Vercel Deployment Essentials (P0) - Frontend

```bash
# API-based deployment (recommended) - more stable than CLI
VERCEL_TOKEN=$(cat "/Users/ted/Library/Application Support/com.vercel.cli/auth.json" | jq -r '.token')
curl -s -X POST "https://api.vercel.com/v13/deployments?skipAutoDetectionConfirmation=1" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "crebit",
    "project": "crebit",
    "gitSource": {"type": "github", "org": "ds4psb-ai", "repo": "vivid", "ref": "main"},
    "target": "production"
  }'
```

**Important Notes:**
- CLI (`vercel deploy`) may fail due to VPN interference or Git author checks
- **Use the API method** (bypasses Git author check, more stable)
- Details: `docs/VERCEL_DEPLOYMENT_GUIDE.md`

### 4. Curation Checklist (App Completeness Evaluation)
```
[] YAML Config exists (config/apps/content/dimensions/{app}.yaml)
[] Router implemented (backend/app/routers/dimension/{app}.py)
[] Adapter Handler registered (backend/app/dimension_adapter.py)
[] Tests written (backend/tests/routers/test_{app}.py) - minimum 30
[] Frontend Page exists (frontend/src/app/dimension/{app}/page.tsx)
[] Frontend Panel implemented (frontend/src/components/dimension/{App}Panel.tsx)
[] dimension-data.ts registered (DIMENSION_ITEMS, ROUTE_KEYS)
[] 2026 Best Practices applied (React 19, Pydantic v2, SSE streaming)
```

---

## Auto Research Mode

Perform **2026-standard MCP research and web search** when user input meets these conditions:
- New feature implementation requests
- Architecture/design questions
- Library/framework questions

Exceptions (execute directly without research):
- Simple questions (What is?, How to?)
- Simple patch/fix requests
- File reading/exploration requests
- Git commands

---

## Project Overview

**Crebit Studio** - Creative AI content generation full-stack platform

### 4-Layer Ecosystem Architecture

| Layer | Component | Description |
|:-----:|-----------|-------------|
| **4** | Trust & Governance | Tool Tier (Experimental→Verified→Certified), Sandbox, Audit |
| **3** | RAG (Knowledge) | NotebookLM Workbench + Qdrant Production |
| **2** | Human Cloud | Request→Creator matching→Delivery (75/25) |
| **1** | Tool Workshop | Dimension Apps, Fork revenue sharing (60/30/10) |

### UI Layer

| Component | Description |
|-----------|-------------|
| Dimension Miniapps | 13 apps (1D~4D, AD, AI, QC, VEO, etc.) |
| Agent Chat | Vivid Agent (Chokki) |
| Train Workflow | Train-based step execution |
| Singularity | Template gallery |
| Human Cloud | Request-production flow |

### Tech Stack
- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind
- **Backend**: FastAPI, Python 3.11, SQLAlchemy 2.0 async
- **Database**: PostgreSQL 16, Qdrant, Redis
- **AI**: Google Gemini API

### Ports
| Service | Port |
|---------|------|
| Frontend | 3100 |
| Backend | 8100 |
| Postgres | 5433 |
| Redis | 6380 |
| Qdrant | 6333 |

---

## Vivid Core Rules (P0)

### 1. evidence_refs Type
```python
# Correct - List[str]
evidence_refs = ["db:capsule_runs:uuid", "db:rag_docs:4D:video_ref:doc_id"]

# Wrong - array of dicts
evidence_refs = [{"source": "...", "ref_id": "..."}]
```

### 2. Run-Token Flow
```
issue() → capsule execution → deduct()/refund()
```
- Do NOT call `reserve_credits()`/`commit_credits()` directly

### 3. Sealed Capsule Principle
- Do NOT call Gemini directly from frontend
- All LLM calls must be inside server capsules

---

## Slash Commands

| Command | Description |
|---------|-------------|
| `/spec-interview` | Create SPEC document via deep interview |
| `/spec-execute` | Implement based on SPEC |
| `/spec-verify` | Verify against SPEC |
| `/review` | Code review |
| `/test` | Run tests |
| `/catchup` | Analyze branch changes |
| `/deploy` | Deployment checklist |
| `/server` | Dev server management |
| `/app-create` | Create Dimension app |
| `/rag-quality` | RAG quality evaluation |
| `/evidence` | Verify evidence_refs |

---

## Detailed Guides (Sub CLAUDE.md files)

| Path | Content |
|------|---------|
| `backend/CLAUDE.md` | FastAPI, Python, DB guide |
| `frontend/CLAUDE.md` | Next.js, React, TypeScript guide |
| `CLAUDE.local.md` | Personal settings (gitignored) |

---

## Key Files

| File | Role |
|------|------|
| `backend/app/generation_client.py` | Shot/Prompt Contract |
| `backend/app/agents/dimension_tools.py` | Dimension Tools |
| `backend/app/routers/run_token.py` | Run Token |
| `backend/app/services/capsule_executor.py` | Capsule Executor |
| `frontend/src/lib/api.ts` | Typed API Client |

---

## SSoT Documents

| Document | Content |
|----------|---------|
| `00_DOCS_INDEX.md` | Document map |
| `13_CREDITS_AND_BILLING_SPEC_V1.md` | Credit system |
| `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md` | Architecture philosophy |
| `docs/DIMENSION_APP_DEVELOPER_GUIDE.md` | App development guide |

---

## RAG System

### Tier Structure
| Tier | System | Purpose |
|------|--------|---------|
| Tier0 | NotebookLM (CDP) | Master knowledge base |
| Tier1 | Qdrant + BM25 | Hybrid search |

### Usage
```python
from app.rag.hybrid_rag import hybrid_query

result = await hybrid_query(
    query="Bong Joon-ho style",
    dimension="AD",
    auteur_key="bong",
)
# result.notebooklm_sources, result.vertex_sources
```

### Key Files
| File | Role |
|------|------|
| `app/rag/hybrid_rag.py` | Hybrid RAG |
| `app/rag/rag_presets.py` | Auteur style hints |
| `app/rag/rag_suggestion_service.py` | evidence_refs generation |

---

## Intent System

### IntentFactory Presets
```python
from app.agents.intent_factory import IntentFactory

intent = IntentFactory.teaching_reference_analyze(
    topic="film analysis",
    auteur_key="kubrick",
)
# intent.app, intent.action, intent.dimension, intent.rag_hint
```

### Key Presets (14)
| Preset | Dimension | RAG |
|--------|-----------|-----|
| `teaching_reference_analyze` | 4D | Yes |
| `teaching_image_generate` | 3D | Yes |
| `teaching_story_write` | Story | Yes |
| `veo_generate` | VEO | Yes |

---

## TieredContext

### Hierarchy
```
SessionContext (global)
  └── StepContext (per-step)
       └── InputContext (input)
```

### Usage
```python
from app.workflow.tiered_context import TieredContext

ctx = TieredContext(session_id="...")
ctx.set_session("auteur_key", "bong")
ctx.set_step("step_1", "topic", "film scene")
resolved = ctx.resolve("step_1", "auteur_key")  # "bong"
```

---

## Sub-Agents (.claude/agents/)

| Agent | Purpose |
|-------|---------|
| `code-reviewer` | PR review |
| `test-runner` | Test execution/analysis |
| `vivid-expert` | Vivid domain expert |
| `db-migrator` | DB migration |
| `rag-expert` | RAG system (Tier0/Tier1) |
| `evidence-checker` | evidence_refs verification |
| `app-creator` | Dimension app creation |
