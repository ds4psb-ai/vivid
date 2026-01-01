# Crebit Migration Plan (CODEX v30)

**Date**: 2025-12-24  
**Status**: CODEX reference (migration sequencing)  
**Purpose**: 문서 기준(SoR)과 현재 코드베이스를 **무중단/무파괴 방식**으로 정렬하고, 운영 가능한 아키텍처로 단계적 마이그레이션을 수행한다.

---

## 0) Scope / Constraints

정본 원칙/흐름은 아래 문서를 따른다:

- `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
- `10_PIPELINES_AND_USER_FLOWS.md`
- `05_CAPSULE_NODE_SPEC.md`
- `08_SHEETS_SCHEMA_V1.md`
- `11_DB_PROMOTION_RULES_V1.md`
- `22_DOCUMENTATION_STRUCTURE_CODEX.md`

---

## 1) Canonical References

- Architecture baseline: `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
- User flows: `10_PIPELINES_AND_USER_FLOWS.md`
- Capsule contract: `05_CAPSULE_NODE_SPEC.md`
- Template system: `23_TEMPLATE_SYSTEM_SPEC_CODEX.md`
- E2E pipeline: `27_AUTEUR_PIPELINE_E2E_CODEX.md`, `28_AUTEUR_TEMPLATE_PIPELINE_DETAIL_CODEX.md`
- Production pipeline: `29_AI_PRODUCTION_PIPELINE_CODEX.md`
- Execution sequencing: `19_CREBIT_EXECUTION_PLAN_V1.md`
- UI system: `13_UI_DESIGN_GUIDE_2025-12.md`

---

## 2) Current State Snapshot (as-is)

**Ready / Implemented**
- Capsule run pipeline with WS/SSE streaming + cancel/retry (MVP).
- Template catalog + narrative seeds + production contract metadata.
- Production spec output: shot contracts + prompt contracts + export (JSON/CSV).
- Evidence refs + pattern version wiring.
- Credits/affiliate scaffolding + ops endpoints.
- UI localization + error normalization.

**Partial / Needs hardening**
- Input contract validation in capsule run (strict enforcement).
- Evidence refs enforcement + output contracts validation (warning/deny).
- Full GA/RL learning loop (reward + promotion policy wiring).
- NotebookLM/Opal real adapters (not stub).
- Admin/role gating & audit policies.

---

## 3) Migration Phases (No breaking changes)

### Phase 0 — Contract Freeze (Doc → Code) ✅
**Goal**: 문서(SoR)의 계약을 확정하고, 코드/데이터 변경 기준점을 고정한다.

**Tasks**
- Freeze: `00/01/05/08/09/10/13/20/23/27/28/29`.
- Confirm canonical ports + env template (no secret copy).
- Lock template naming + capsule_id@version policy.

**Exit Criteria**
- SoR 문서 간 용어/필드 충돌 없음.
- 템플릿/캡슐 naming 고정.

**Status**: Completed 2025-12-26

---

### Phase 1 — Schema & Data Canonicalization ✅
**Goal**: DB SoR, Notebook Library, Pattern Trace 구조를 일관되게 정리하고 seed를 최신화한다.

**Tasks**
- DB init/migrate (`init_db`) → missing columns 보강.
- Seed 최신 캡슐/템플릿(프로덕션 캡슐 포함).
- Notebook Library + Assets ingest (manual → scripted).
- Derived Insights → DB promotion (Sheets Bus).
- Pattern promotion + version bump → capsule/template sync.

**Exit Criteria**
- NotebookLibrary/Assets, PatternTrace, PatternVersion counts 정상.
- 템플릿에 narrative_seeds + production_contract 포함.

**Status**: Completed 2025-12-26
- RawAsset: 4, VideoSegment: 4, NotebookLibrary: 3
- EvidenceRecord: 7, Pattern: 3, Template: 8

---

### Phase 2 — Capsule Execution Hardening
**Goal**: 캡슐 계약/증거/출력 규칙을 엄격히 지키는 실행 레이어로 전환한다.

**Tasks**
- InputContracts validation (required/optional/maxUpstream/allowedTypes).
- Evidence refs allowlist 필터링 강화 (sheet/db만).
- OutputContracts mismatch warning or fail 정책 확정.
- Upstream context snapshot 강화 (contextMode 적용).

**Exit Criteria**
- 캡슐 실행 로그에 upstream_context/evidence_refs/token/latency 포함.
- invalid evidence/output → 경고/차단 정책 작동.

---

### Phase 3 — Production Pipeline Enablement
**Goal**: 샷/프롬프트 계약을 실제 제작 파이프라인에 투입할 수 있게 한다.

**Tasks**
- Production capsule 파라미터가 spec에 반영되도록 강화.
- GenerationRun outputs에 production_contract 고정 포함.
- 내보내기(패키지/CSV) UX 완료.
- Production template 피드백 루프 준비(shot-level metadata).

**Exit Criteria**
- 템플릿 → 캔버스 → 생성 실행 → shot/prompt 계약 export 완주.
- 프로덕션 템플릿이 필터/배지로 구분됨.

---

### Phase 4 — Template Learning (GA/RL)
**Goal**: Evidence Loop 기반 템플릿 학습 루프를 안정화한다.

**Tasks**
- Evidence reward 정의 + GA/RL 적용.
- Pattern Lift 기반 승격 규칙을 실행 코드와 연결.
- TemplateVersion 승격 자동화 (조건 통과 시).

**Exit Criteria**
- GA/RL 결과가 TemplateVersion으로 승격되고 재현 가능.

---

### Phase 5 — Commerce & Observability
**Goal**: 비용/성과 투명성과 성장 기능을 운영 수준으로 강화한다.

**Tasks**
- Credit ledger 우선순위 정책 확정 및 UI 반영.
- Affiliate reward gating (verified + first run).
- Run-level token/latency/cost UI 표시.

**Exit Criteria**
- 모든 run에 비용/성능 기록 노출.
- Growth/credits/usage 정책이 일관되게 적용.

---

## 4) Migration Runbook (Operational Order)

1. **Backup**: DB snapshot / file backup  
2. **Init DB**: `init_db` 실행  
3. **Seed**: 캡슐/템플릿 최신화  
4. **Ingest**: Notebook Library/Assets → Derived Insights  
5. **Promote**: Sheets Bus → DB SoR  
6. **Pattern Promote**: Pattern/Trace/Version  
7. **Verify**: Ops endpoints / template list / capsule runs  

> 모든 단계는 **quarantine 체크 → 승인 → 진행** 순서를 유지한다.

---

## 5) Validation Checklist

- Templates: `meta.narrative_seeds` + `production_contract` 확인  
- Capsules: `inputContracts` + `patternVersion` + `adapter` 확인  
- Runs: `evidence_refs` + `token_usage` + `latency_ms` 기록  
- UI: 템플릿 카드 배지/필터, 프리뷰/생성 패널 정상 동작  
- Exports: shot/prompt 계약 JSON/CSV 정상 출력  

---

## 6) Rollback Strategy

- **DB rollback**: 마지막 스냅샷 복원  
- **Seed rollback**: seed 실행 전 상태의 Template/TemplateVersion 유지  
- **Feature rollback**: 특정 모듈 비활성화 (adapter type fallback)

---

## 7) Decision Gates (Need approval)

1. Production 캡슐 기본 파라미터 세트 확정  
2. Evidence 기준(승격/차단) 수치 확정  
3. Template learning 자동 승격 여부  
4. Credit cost matrix (preview vs final)

---

## 8) Owner Mapping

- **Admin/Curator**: Notebook Library, rights, seed  
- **Data Engineer**: ingest + promotion  
- **Product/Studio**: templates + capsule versioning  
- **Creator/PD/Writer**: canvas execution + feedback  

---

## 9) Completion Definition

V1 migration is complete when:
- **1 auteur + 1 production template**가 end-to-end로 실행 가능하고,
- **evidence refs + patternVersion**이 모든 run에 포함되며,
- **shot/prompt 계약 export**가 제작 파이프라인에 즉시 투입 가능한 상태가 된다.
