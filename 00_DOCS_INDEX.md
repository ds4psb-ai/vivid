# Docs Index (정본)

**Updated**: 2026-01-04  
**총 문서**: 33개 (00 두 개 포함)

---

## 핵심 정본 (SoR)

| # | 문서 | 역할 | 상태 |
|---|------|------|------|
| 00 | DOCS_INDEX | 이 문서 | ✅ |
| 00 | EXECUTIVE_SUMMARY_NODE_CANVAS | 프로젝트 개요 | ✅ |
| 01 | NODE_CANVAS_TECHNICAL_SPECIFICATION | 기술 명세 | ⚠️ 레거시 (Canvas/Studio deprecated) |
| 04 | CAPSULE_NODE_SPEC | 캡슐 계약 | ✅ |
| 08 | PIPELINES_AND_USER_FLOWS | 파이프라인/역할 | ✅ |
| 09 | DB_PROMOTION_RULES_V1 | 승격 규칙 | ✅ |
| 10 | UI_DESIGN_GUIDE_2025-12 | UI/UX | ✅ |
| 15 | CREBIT_ARCHITECTURE_EVOLUTION_CODEX | 철학/원칙 | ✅ |
| 30 | UNIFIED_EXECUTION_ROADMAP | 실행 로드맵 | ✅ |

---

## 2026 H1 신규 스택

| 항목 | 위치 | 설명 |
|------|------|------|
| **AG-UI 이벤트 매퍼** | `frontend/src/lib/agui/` | SSE → AG-UI 표준 이벤트 매핑 |
| **A2UI 검증기** | `frontend/src/lib/a2ui/validator.ts` | 화이트리스트 위젯 검증 |
| **Teaching Tools** | `backend/app/agents/teaching_tools.py` | 4개 도구 (generate_veo_prompt 등) |

---

## Deprecated 경로

| 경로 | 사유 |
|------|------|
| `frontend/src/app/_deprecated/studio/` | Canvas/Studio UI → Dimension/Flow 전환 |
| `frontend/src/app/_deprecated/canvas/` | Canvas UI deprecated |
| `backend/app/agents/_deprecated/` | workflow_tools 등 레거시 도구 |
| `backend/app/routers/_deprecated/` | 레거시 API 라우터 |

---

## 보조 문서

| # | 문서 | 역할 |
|---|------|------|
| 02 | GA_AND_RL_DEEP_DIVE | 최적화 |
| 03 | RESEARCH_SOURCES_2025-12 | 리서치 |
| 05 | TEMPLATE_CATALOG | 템플릿 |
| 06 | SHEETS_SCHEMA_V1 | Sheets 스키마 |
| 07 | NOTEBOOKLM_OUTPUT_SPEC_V1 | NotebookLM 출력 |
| 11 | INGEST_RUNBOOK_V1 | 인제스트 |
| 12 | PATTERN_TAXONOMY_V1 | 패턴 분류 |
| 13 | CREDITS_AND_BILLING_SPEC_V1 | 크레딧 |
| 14 | REVERSE_ENGINEERING_REPORT | 역설계 |
| 16 | DOCUMENTATION_STRUCTURE_CODEX | 문서 구조 |
| 17 | TEMPLATE_SYSTEM_SPEC_CODEX | 템플릿 시스템 |
| 18 | PDR_NODE_CANVAS | PRD |
| 19 | VIDEO_UNDERSTANDING_PIPELINE_CODEX | 영상 구조화 |
| 20 | DOC_LINT_RULES_CODEX | 문서 린트 |
| 21 | AUTEUR_PIPELINE_E2E_CODEX | E2E 파이프라인 |
| 22 | AI_PRODUCTION_PIPELINE_CODEX | AI 프로덕션 |
| 23 | MIGRATION_PLAN_CODEX | 마이그레이션 |
| 24 | CLAIM_EVIDENCE_TRACE_SPEC_V1 | 증거 추적 |
| 25 | NOTEBOOKLM_SOURCE_PACK_PROTOCOL_CODEX | NotebookLM 프로토콜 |
| 26 | AFFILIATE_PROGRAM_SPEC_V1 | 어필리에이트 |
| 27 | MCP_INTEGRATION_SPEC_V1 | MCP 통합 |
| 28 | EVENT_DRIVEN_ARCHITECTURE_SPEC_V1 | 이벤트 아키텍처 |
| 29 | AUTEUR_DATA_COLLECTION_PROTOCOL_CODEX | 데이터 수집 |
| 31 | AGENT_STUDIO_ARTIFACT_SPEC_V1 | 아티팩트 스펙 |

---

## 기타

- `README.md` - 프로젝트 소개
- `PRIVACY_POLICY.md` / `TERMS_OF_SERVICE.md` - 법률
- `task.md` / `walkthrough.md` - 개발 로그

---

## Archived (docs/archive/)

통합/폐기된 역사적 문서들
