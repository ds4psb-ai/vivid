# Repository Guidelines

## Project Structure & Module Organization
- `backend/app/` API code; `backend/tests/` pytest.
- `frontend/src/` UI; `frontend/e2e/` Playwright; `frontend/public/` assets.
- `docs/` + root numbered `*.md` canonical specs (`00_DOCS_INDEX.md`).
- `config/apps/` AppRegistry SSoT (`config/apps/content/dimensions/*.yaml`).
- `scripts/` + `backend/scripts/`; `data/` datasets.

## Canonical Docs & Architecture (SSoT)
- `00_DOCS_INDEX.md`: doc map.
- `00_EXECUTIVE_SUMMARY_NODE_CANVAS.md` + `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`.
- `08_PIPELINES_AND_USER_FLOWS.md` + `10_UI_DESIGN_GUIDE_2025-12.md`.
- `13_CREDITS_AND_BILLING_SPEC_V1.md` + `27_MCP_INTEGRATION_SPEC_V1.md`.
- `30_UNIFIED_EXECUTION_ROADMAP.md` + `docs/DIMENSION_APP_DEVELOPER_GUIDE.md`.

## SSoT Change Impact Checklist
- AppRegistry/YAML: check `backend/app/core/app_registry.py`, `backend/app/routers/dimension/_base.py`, `backend/app/agents/dimension_tools.py`, `backend/app/rag/app_registry.py`, `backend/app/rag/rag_presets.py`.
- Credits/tool cost: align `13_CREDITS_AND_BILLING_SPEC_V1.md`.
- Flow/Agent/Dimension: sync `08_PIPELINES_AND_USER_FLOWS.md`, `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`, `frontend/src/app/`; update `00_DOCS_INDEX.md` if canon changes.

## SSoT Test Matrix (Quick)
| Change area | Backend smoke | Frontend smoke |
| --- | --- | --- |
| Dimension/AppRegistry | `pytest -v tests/routers/test_dimension_sse.py` | `npm run test:e2e -- e2e/dimension.spec.ts` |
| Credits/Run-token | `pytest -v tests/test_kelly_credit_service.py` | `npm run test:e2e -- e2e/credits.spec.ts` |
| Agent/Flow | `pytest -v tests/agents/test_vivid_agent_integration.py tests/routers/test_agent_streaming.py` | `npm run test:e2e -- e2e/agent-chat.spec.ts e2e/flow.spec.ts` |

## Build, Test, and Development Commands
- `docker-compose up -d`
- Backend: `cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8100`
- Frontend dev: `cd frontend && npm install && npm run dev` (`http://localhost:3100`)
- Frontend lint/build/start: `cd frontend && npm run lint|build|start`
- E2E: `cd frontend && npm run test:e2e`

## Auto Research Mode (2026)
사용자 입력이 다음 조건을 충족하면 **2026년 기준 MCP 리서치 및 웹서칭** 수행:
- 새로운 기능 구현 요청
- 아키텍처/설계 관련 질문
- 라이브러리/프레임워크 관련 질문

예외 (리서치 없이 바로 수행):
- 단순 질문 (무엇인가요?, 어떻게?)
- 간단 패치/수정 요청
- 파일 읽기/탐색 요청
- git 명령어

## Context Engineering Playbook (Prompting Standards)
- 비자명한 작업 시작 전, 최소 컨텍스트 패킷을 명시한다:
  - 목표/완료 조건(Definition of Done)
  - 역할 스탠스(구현자/리뷰어/비판자)
  - 제약/비목표
  - 근거 아티팩트(관련 파일/로그/이슈/커밋/링크)
  - 스타일 민감 작업이면 good 예시 1개 + avoid 예시 1개
- **Reverse prompting 기본 적용**: 결정 품질에 필요한 정보가 비어 있으면 먼저 짧고 구체적으로 질문한다.
- **Humanity test**: 같은 지시를 동료에게 주었을 때 수행이 불가능하면, 컨텍스트를 보강한 뒤 실행한다.
- **비판적 사고 기본값**: 과도한 동의보다 반례/리스크/가정을 먼저 점검한다.
- **추론 보고 원칙**: 내부 chain-of-thought 전문 대신 가정/판단기준/검증 체크리스트를 요약 보고한다.

## Coding Style & Naming Conventions
- Python: 4-space indentation, snake_case, type hints.
- TypeScript/TSX: 2-space indentation, `PascalCase` components, `useX` hooks, `camelCase` utilities.
- ESLint rules live in `frontend/eslint.config.mjs`.

## Testing Guidelines
- Backend: pytest in `backend/tests/` (`test_*.py`).
- Frontend: Playwright E2E in `frontend/e2e/*.spec.ts`.

## Commit & Pull Request Guidelines
- Conventional Commits, e.g. `feat(dimension): ...`.
- PRs: summary, tests run, screenshots/GIFs for UI changes.

## Security & Permissions
- Capsules are sealed: no raw prompts/inner chains; expose inputs/params/outputs + evidence refs only.
- NotebookLM content is private; expose derived summaries only.
- Admin/Ops are role-gated; `X-User-Id` is dev fallback only.
- Execution requires run-tokens (`/api/v1/run-token/*`) with credit reserve/commit/rollback; insufficient credits should return 402 per `13_CREDITS_AND_BILLING_SPEC_V1.md`.
- Run-token error response examples:
```json
{"success": false, "error": "Run ID mismatch"}
{"success": false, "error": "App not found"}
```
- Internal endpoints use mTLS when `MTLS_ENABLED=true`; never allow direct client writes to DB SoR.

## Configuration & Secrets
- Copy `backend/.env.example` → `backend/.env` and `frontend/.env.example` → `frontend/.env.local`.
- Never commit API keys; use env vars for external adapters.
