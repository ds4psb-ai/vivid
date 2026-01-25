# CLAUDE.md

> Claude Code 설정 파일 - Crebit Studio (Vivid)

---

## Quick Rules

### 검증 명령어 (필수)
```bash
cd backend && source venv/bin/activate && pytest --tb=short -q  # Backend
cd frontend && npm run build  # Frontend
```

### 핵심 원칙
1. **확인 후 코딩**: `Grep`/`Read`로 파일 존재 확인 → 코드 작성
2. **테스트 동반**: 새 기능 추가 시 테스트도 함께 작성
3. **에러 처리 포함**: try-except, rollback 패턴 적용
4. **타입 명시**: Python type hints, TypeScript strict

### 환각 금지
- 존재하지 않는 파일/함수 참조 금지
- 추측으로 import 작성 금지
- 불확실하면 Grep으로 먼저 검색

---

## P0: 앱/DB 작업 전 필수 참조 문서

**앱 또는 DB 관련 작업 요청 시 반드시 아래 문서를 먼저 읽고 진행:**

### 1. 앱 개발 프로토콜
| 문서 | 경로 | 용도 |
|------|------|------|
| 앱 개발 가이드 | `docs/DIMENSION_APP_DEVELOPER_GUIDE.md` | 앱 생성 표준 절차 |
| 앱 YAML 스키마 | `config/apps/content/dimensions/*.yaml` | SSoT 설정 |
| 앱 라우터 패턴 | `backend/app/routers/dimension/_base.py` | 공통 유틸 |

### 2. 앱별 리서치 문서 (2026 Best Practices)
| 앱 | 리서치 문서 |
|----|-------------|
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

### 3. DB/백엔드 프로토콜
| 문서 | 경로 | 용도 |
|------|------|------|
| 크레딧 시스템 | `docs/13_CREDITS_AND_BILLING_SPEC_V1.md` | Run-Token 흐름 |
| 아키텍처 코덱스 | `docs/15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md` | 설계 철학 |
| Backend CLAUDE.md | `backend/CLAUDE.md` | DB/API 패턴 |
| **Railway 배포** | `docs/RAILWAY_DEPLOYMENT_GUIDE.md` | Railway 배포 가이드 |

### 5. Railway 배포 핵심 (P0)

```bash
# Dockerfile - shell form 필수 ($PORT 확장)
CMD sh -c "uvicorn app.main:app --port ${PORT:-8080}"

# DATABASE_URL - asyncpg 드라이버 명시
DATABASE_URL=postgresql+asyncpg://...@postgres.railway.internal:5432/...

# Private networking 사용 (egress 무료)
REDIS_URL=redis://...@redis.railway.internal:6379
```

**주의사항:**
- `railway.json` startCommand와 Dockerfile CMD 중 **하나만** 사용
- 변수 참조 안 되면 하드코딩 (`${{Service.VAR}}` → 실제값)
- 상세: `docs/RAILWAY_DEPLOYMENT_GUIDE.md`

### 4. 큐레이션 체크리스트 (앱 완성도 평가)
```
□ YAML Config 존재 (config/apps/content/dimensions/{app}.yaml)
□ Router 구현 (backend/app/routers/dimension/{app}.py)
□ Adapter Handler 등록 (backend/app/dimension_adapter.py)
□ Tests 작성 (backend/tests/routers/test_{app}.py) - 최소 30개
□ Frontend Page 존재 (frontend/src/app/dimension/{app}/page.tsx)
□ Frontend Panel 구현 (frontend/src/components/dimension/{App}Panel.tsx)
□ dimension-data.ts 등록 (DIMENSION_ITEMS, ROUTE_KEYS)
□ 2026 Best Practices 적용 (React 19, Pydantic v2, SSE streaming)
```

---

## Auto Research Mode

사용자 입력이 다음 조건을 충족하면 **2026년 기준 MCP 리서치 및 웹서칭** 수행:
- 새로운 기능 구현 요청
- 아키텍처/설계 관련 질문
- 라이브러리/프레임워크 관련 질문

예외 (리서치 없이 바로 수행):
- 단순 질문 (무엇인가요?, 어떻게?)
- 간단 패치/수정 요청
- 파일 읽기/탐색 요청
- git 명령어

---

## Project Overview

**Crebit Studio** - 크리에이티브 AI 콘텐츠 생성 풀스택 플랫폼

### 4-Layer 생태계 아키텍처

| Layer | Component | Description |
|:-----:|-----------|-------------|
| **4** | Trust & Governance | Tool Tier (Experimental→Verified→Certified), Sandbox, Audit |
| **3** | RAG (Knowledge) | NotebookLM Workbench + Qdrant Production |
| **2** | Human Cloud | 의뢰→크리에이터 매칭→납품 (75/25) |
| **1** | Tool Workshop | Dimension Apps, Fork 수익분배 (60/30/10) |

### UI Layer

| Component | Description |
|-----------|-------------|
| Dimension Miniapps | 13개 앱 (1D~4D, AD, AI, QC, VEO 등) |
| Agent Chat | Vivid Agent (초끼) |
| Train Workflow | Train-based step execution |
| Singularity | Template gallery |
| Human Cloud | 의뢰-제작 플로우 |

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

## Vivid 핵심 규칙 (P0)

### 1. evidence_refs 타입
```python
# ✅ 올바름 - List[str]
evidence_refs = ["db:capsule_runs:uuid", "db:rag_docs:4D:video_ref:doc_id"]

# ❌ 틀림 - dict 배열
evidence_refs = [{"source": "...", "ref_id": "..."}]
```

### 2. Run-Token 흐름
```
issue() → 캡슐 실행 → deduct()/refund()
```
- `reserve_credits()`/`commit_credits()` 직접 호출 금지

### 3. Sealed Capsule 원칙
- 프론트엔드에서 Gemini 직접 호출 금지
- 모든 LLM 호출은 서버 캡슐 내부에서

---

## Slash Commands

| Command | 설명 |
|---------|------|
| `/spec-interview` | 심층 인터뷰로 SPEC 문서 작성 |
| `/spec-execute` | SPEC 기반 구현 |
| `/spec-verify` | SPEC 대비 검증 |
| `/review` | 코드 리뷰 |
| `/test` | 테스트 실행 |
| `/catchup` | 브랜치 변경사항 분석 |
| `/deploy` | 배포 체크리스트 |
| `/server` | 개발 서버 관리 |
| `/app-create` | Dimension 앱 생성 |
| `/rag-quality` | RAG 품질 평가 |
| `/evidence` | evidence_refs 검증 |

---

## 상세 가이드 (하위 CLAUDE.md)

| 경로 | 내용 |
|------|------|
| `backend/CLAUDE.md` | FastAPI, Python, DB 가이드 |
| `frontend/CLAUDE.md` | Next.js, React, TypeScript 가이드 |
| `CLAUDE.local.md` | 개인 설정 (gitignore) |

---

## Key Files

| 파일 | 역할 |
|------|------|
| `backend/app/generation_client.py` | Shot/Prompt Contract |
| `backend/app/agents/dimension_tools.py` | Dimension Tools |
| `backend/app/routers/run_token.py` | Run Token |
| `backend/app/services/capsule_executor.py` | Capsule Executor |
| `frontend/src/lib/api.ts` | Typed API Client |

---

## SSoT Documents

| 문서 | 내용 |
|------|------|
| `00_DOCS_INDEX.md` | 문서 맵 |
| `13_CREDITS_AND_BILLING_SPEC_V1.md` | 크레딧 시스템 |
| `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md` | 아키텍처 철학 |
| `docs/DIMENSION_APP_DEVELOPER_GUIDE.md` | 앱 개발 가이드 |

---

## RAG 시스템

### Tier 구조
| Tier | 시스템 | 용도 |
|------|--------|------|
| Tier0 | NotebookLM (CDP) | 거장 지식베이스 |
| Tier1 | Qdrant + BM25 | 하이브리드 검색 |

### 사용법
```python
from app.rag.hybrid_rag import hybrid_query

result = await hybrid_query(
    query="봉준호 스타일",
    dimension="AD",
    auteur_key="bong",
)
# result.notebooklm_sources, result.vertex_sources
```

### 핵심 파일
| 파일 | 역할 |
|------|------|
| `app/rag/hybrid_rag.py` | 하이브리드 RAG |
| `app/rag/rag_presets.py` | 거장 스타일 힌트 |
| `app/rag/rag_suggestion_service.py` | evidence_refs 생성 |

---

## Intent 시스템

### IntentFactory Presets
```python
from app.agents.intent_factory import IntentFactory

intent = IntentFactory.teaching_reference_analyze(
    topic="영화 분석",
    auteur_key="kubrick",
)
# intent.app, intent.action, intent.dimension, intent.rag_hint
```

### 주요 프리셋 (14개)
| 프리셋 | Dimension | RAG |
|--------|-----------|-----|
| `teaching_reference_analyze` | 4D | ✅ |
| `teaching_image_generate` | 3D | ✅ |
| `teaching_story_write` | Story | ✅ |
| `veo_generate` | VEO | ✅ |

---

## TieredContext

### 계층 구조
```
SessionContext (전역)
  └── StepContext (단계별)
       └── InputContext (입력)
```

### 사용법
```python
from app.workflow.tiered_context import TieredContext

ctx = TieredContext(session_id="...")
ctx.set_session("auteur_key", "bong")
ctx.set_step("step_1", "topic", "영화 장면")
resolved = ctx.resolve("step_1", "auteur_key")  # "bong"
```

---

## 서브에이전트 (.claude/agents/)

| Agent | 용도 |
|-------|------|
| `code-reviewer` | PR 리뷰 |
| `test-runner` | 테스트 실행/분석 |
| `vivid-expert` | Vivid 도메인 전문가 |
| `db-migrator` | DB 마이그레이션 |
| `rag-expert` | RAG 시스템 (Tier0/Tier1) |
| `evidence-checker` | evidence_refs 검증 |
| `app-creator` | Dimension 앱 생성 |
