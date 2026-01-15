# Docs Index (정본)

**Updated**: 2026-01-15  
**총 문서**: 12개 (핵심), 35개 (archive)

---

## 핵심 문서 (Root)

| # | 문서 | 역할 | 상태 |
|---|------|------|------|
| 00 | DOCS_INDEX.md | 문서 맵 | ✅ |
| 00 | EXECUTIVE_SUMMARY_NODE_CANVAS.md | 프로젝트 개요 | ✅ |
| 08 | PIPELINES_AND_USER_FLOWS.md | 파이프라인/역할 | ✅ |
| 10 | UI_DESIGN_GUIDE_2025-12.md | UI/UX 가이드 | ✅ |
| 13 | CREDITS_AND_BILLING_SPEC_V1.md | 크레딧 시스템 | ✅ |
| 15 | CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md | 아키텍처 철학 | ✅ |
| 27 | MCP_INTEGRATION_SPEC_V1.md | MCP 통합 | ✅ |
| 30 | UNIFIED_EXECUTION_ROADMAP.md | 실행 로드맵 | ✅ |
| **31** | **[DIMENSION_APP_DEVELOPER_GUIDE.md](docs/DIMENSION_APP_DEVELOPER_GUIDE.md)** | **앱 개발자 가이드 (SSoT)** | ✅ |
| - | README.md | 프로젝트 소개 | ✅ |
| - | PRIVACY_POLICY.md / TERMS_OF_SERVICE.md | 법률 문서 | ✅ |

---

## 2026 H1 스택

| 항목 | 위치 | 설명 |
|------|------|------|
| **AppRegistry SSoT** | `config/apps/README.md` | YAML 기반 앱 설정 통합 (크레딧 비용 SSoT) |
| **AG-UI 이벤트 매퍼** | `frontend/src/lib/agui/` | SSE → AG-UI 표준 이벤트 매핑 |
| **A2UI 검증기** | `frontend/src/lib/a2ui/validator.ts` | 화이트리스트 위젯 검증 |
| **Dimension Tools** | `backend/app/agents/dimension_tools.py` | 15개 도구 (core + expert/alias 포함) |
| **Singularity (특이점)** | `frontend/src/app/singularity/` | 차원 조합 템플릿 갤러리 |
| **앱 개발자 가이드** | `docs/DIMENSION_APP_DEVELOPER_GUIDE.md` | 앱 개발자 공통 가이드 (SSoT) |
| **RAG Reliability** | [`docs/RAG_RELIABILITY.md`](docs/RAG_RELIABILITY.md) | Circuit Breaker, CRAG, 캐시 |
| **NotebookLM Playwright** | [`docs/NOTEBOOKLM_PLAYWRIGHT.md`](docs/NOTEBOOKLM_PLAYWRIGHT.md) | RPC/UI 폴백 자동화 |
| **Grafana Dashboard** | `config/grafana/rag_overview.json` | RAG 모니터링 15패널 |
| **Chrome CDP Workflow** | `.agent/workflows/chrome-debug.md` | 9223 포트 사용 가이드 |

---

## 2026-01-13 신규 (RAG P1-P5)

| 항목 | 위치 | 설명 |
|------|------|------|
| **RAG Quality Guide** | [`docs/RAG_QUALITY.md`](docs/RAG_QUALITY.md) | 품질 평가 + OKR 기준 (**NEW**) |
| **EvidenceDisplay UX** | [`docs/EVIDENCE_DISPLAY_UX.md`](docs/EVIDENCE_DISPLAY_UX.md) | 패널별 적용 규칙 (**NEW**) |
| **Video Ref 인제스션** | `backend/scripts/ingest_video_reference.py` | video_ref → Qdrant |
| **Image Grid 인제스션** | `backend/scripts/ingest_image_grid.py` | image_grid → Qdrant |
| **RAG Quality CLI** | `backend/scripts/run_rag_quality_report.py` | 품질 리포트 생성 |
| **EvidenceDisplay 공유** | `frontend/src/components/dimension/EvidenceDisplay.tsx` | AI 근거 표시 표준 컴포넌트 |

---

## 2026-01-14 RAG Ops (P6)

| 항목 | 위치 | 설명 |
|------|------|------|
| **Router Decision Report** | `backend/scripts/router_decision_report.py` | 라우터 전략/캐시 히트 분석 |
| **Cache Tuning Report** | `backend/scripts/rag_cache_report.py` | stale/avg_hit 리포트 |
| **Retention Cleanup** | `backend/scripts/cleanup_router_logs.py` | RouterDecisionLog 보존 정책 |
| **Qdrant Reindex Note** | `docs/RAG_RELIABILITY.md` | 384 dim 정합성 & 재인덱싱 |

---

## Security and Policy (docs/)

| Document | Location | Description |
| --- | --- | --- |
| Security Overview | `docs/SECURITY_OVERVIEW.md` | Top-level security posture and scope |
| Security Controls Baseline | `docs/SECURITY_CONTROLS_BASELINE.md` | Minimum control requirements and mapping template |
| Data Governance Policy | `docs/DATA_GOVERNANCE_POLICY.md` | Classification, handling, retention, deletion |
| AI and RAG Security Policy | `docs/AI_RAG_SECURITY_POLICY.md` | RAG threat model and guardrails |
| Secure SDLC Policy | `docs/SECURE_SDLC_POLICY.md` | SSDF-aligned development requirements |
| Incident Response and BCP | `docs/INCIDENT_RESPONSE_AND_BCP.md` | Incident handling and continuity plan |
| Access Control Policy | `docs/ACCESS_CONTROL_POLICY.md` | Authentication and authorization rules |
| Logging and Monitoring Policy | `docs/LOGGING_MONITORING_POLICY.md` | Logging, monitoring, and alerting requirements |
| Vendor Risk Policy | `docs/VENDOR_RISK_POLICY.md` | Third-party risk management |

---

## 전략 문서 (docs/strategic/)

| 문서 | 역할 |
|------|------|
| crebit_teaching_apps_spec.md | 3-Layer 생태계 스펙 |
| unified_4layer_strategy.md | 4레이어 전략 |
| teaching_capsule_agent_integration_spec.md | 에이전트 통합 스펙 |

---

## Archive (docs/archive/)

정리 완료된 역사적 문서들 (35개) - 필요시 참조

---

## 기타

- `task.md` / `walkthrough.md` - 개발 로그
- 문서 언어 토글은 `<details>` 기반이며 기본 열림은 한국어
