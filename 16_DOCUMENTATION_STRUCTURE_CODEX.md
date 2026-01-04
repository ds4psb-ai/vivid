# Documentation Structure (CODEX v22)

**Date**: 2025-12-24  
**Updated**: 2026-01-01  
**Status**: CODEX baseline (structure + governance)  
**Purpose**: 문서 체계를 강화하고, 최신 아키텍처/운영 철학을 일관되게 유지하기 위한 표준 구조를 정의한다.

---

## 0) Principles

- **Legacy 문서는 삭제하지 않는다.** 변경은 업데이트 또는 CODEX 확장 문서로만 수행.
- **SoR(정본) vs Reference(참고) 구분**을 명시한다.
- NotebookLM/Opal은 **지식/가이드 레이어(가속)**, DB는 **학습/증명(SoR)**.
- 캡슐 노드는 **Sealed**: 입력/출력/노출 파라미터만 공개.

---

## 1) Document Taxonomy (범주별 구조)

문서 목록/상태는 `00_DOCS_INDEX.md`를 정본으로 삼는다. 아래는 **범주 정의 + 대표 문서**만 유지한다.

### A. Vision & Architecture (SoR)
- `00_EXECUTIVE_SUMMARY_NODE_CANVAS.md`
- `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
- `01_NODE_CANVAS_TECHNICAL_SPECIFICATION.md`
- `04_CAPSULE_NODE_SPEC.md`
- `20_DOC_LINT_RULES_CODEX.md`

### B. Data & Evidence (SoR)
- `06_SHEETS_SCHEMA_V1.md`
- `07_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
- `08_PIPELINES_AND_USER_FLOWS.md`
- `09_DB_PROMOTION_RULES_V1.md`
- `12_PATTERN_TAXONOMY_V1.md`
- `19_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`
- `24_CLAIM_EVIDENCE_TRACE_SPEC_V1.md`
- `25_NOTEBOOKLM_SOURCE_PACK_PROTOCOL_CODEX.md`
- `29_AUTEUR_DATA_COLLECTION_PROTOCOL_CODEX.md`
- `31_AGENT_STUDIO_ARTIFACT_SPEC_V1.md`

### C. Execution & Roadmap (Reference)
- See `00_DOCS_INDEX.md`

### D. UI/UX & Product (SoR)
- `10_UI_DESIGN_GUIDE_2025-12.md`
- `05_TEMPLATE_CATALOG.md`
- `17_TEMPLATE_SYSTEM_SPEC_CODEX.md`
- `18_PDR_NODE_CANVAS.md`

### E. Business & Growth (Reference)
- See `00_DOCS_INDEX.md`

### F. Research & Reverse Engineering (Reference)
- See `00_DOCS_INDEX.md`

### G. Audit & Quality (Reference)
- See `00_DOCS_INDEX.md`

---

## 2) Dependency Map (핵심 의존관계)

- `00_EXECUTIVE_SUMMARY_NODE_CANVAS.md` → `01_NODE_CANVAS_TECHNICAL_SPECIFICATION.md`, `08_PIPELINES_AND_USER_FLOWS.md`, `10_UI_DESIGN_GUIDE_2025-12.md`, `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
- `01_NODE_CANVAS_TECHNICAL_SPECIFICATION.md` → `04_CAPSULE_NODE_SPEC.md`, `06_SHEETS_SCHEMA_V1.md`, `07_NOTEBOOKLM_OUTPUT_SPEC_V1.md`, `08_PIPELINES_AND_USER_FLOWS.md`
- `04_CAPSULE_NODE_SPEC.md` → `06_SHEETS_SCHEMA_V1.md`, `07_NOTEBOOKLM_OUTPUT_SPEC_V1.md`, `09_DB_PROMOTION_RULES_V1.md`, `12_PATTERN_TAXONOMY_V1.md`
- `06_SHEETS_SCHEMA_V1.md` ↔ `07_NOTEBOOKLM_OUTPUT_SPEC_V1.md` (Sheets Bus ↔ NotebookLM 출력 규격)
- `08_PIPELINES_AND_USER_FLOWS.md` → `11_INGEST_RUNBOOK_V1.md`, `09_DB_PROMOTION_RULES_V1.md`, `19_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`, `25_NOTEBOOKLM_SOURCE_PACK_PROTOCOL_CODEX.md`
- `17_TEMPLATE_SYSTEM_SPEC_CODEX.md` → `05_TEMPLATE_CATALOG.md`, `04_CAPSULE_NODE_SPEC.md`, `08_PIPELINES_AND_USER_FLOWS.md`
- `21_AUTEUR_PIPELINE_E2E_CODEX.md` → `11_INGEST_RUNBOOK_V1.md`, `19_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`, `25_NOTEBOOKLM_SOURCE_PACK_PROTOCOL_CODEX.md`, `29_AUTEUR_DATA_COLLECTION_PROTOCOL_CODEX.md`
- `22_AI_PRODUCTION_PIPELINE_CODEX.md` → `08_PIPELINES_AND_USER_FLOWS.md`, `19_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`, `25_NOTEBOOKLM_SOURCE_PACK_PROTOCOL_CODEX.md`
- `24_CLAIM_EVIDENCE_TRACE_SPEC_V1.md` → `07_NOTEBOOKLM_OUTPUT_SPEC_V1.md`, `06_SHEETS_SCHEMA_V1.md`, `09_DB_PROMOTION_RULES_V1.md`, `25_NOTEBOOKLM_SOURCE_PACK_PROTOCOL_CODEX.md`
- `31_AGENT_STUDIO_ARTIFACT_SPEC_V1.md` → `07_NOTEBOOKLM_OUTPUT_SPEC_V1.md`, `06_SHEETS_SCHEMA_V1.md`, `08_PIPELINES_AND_USER_FLOWS.md`

---

## 3) Definition of Truth (SoR vs Derived vs Reference)

- **SoR**: 핵심 계약/정책 문서 (운영의 기준)
- **Derived**: NotebookLM/Opal 출력 및 Sheets Bus 결과 (승격 전)
- **Reference**: 리서치/벤치마크/로드맵 문서

SoR 변경 시 반드시 관련 문서 링크 업데이트 필요.

**Canonical anchors**
- 원칙/철학: `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
- 흐름/역할: `08_PIPELINES_AND_USER_FLOWS.md`

---

## 4) NotebookLM/Opal Role (정본 표현)

정본 역할 정의는 `08_PIPELINES_AND_USER_FLOWS.md`를 따른다.

---

## 5) Versioning Rules

- 기존 문서는 유지, 변경 내역은 상단에 **Updated** 기록.
- 구조 변경이나 철학 변경은 `*_CODEX.md`로 확장.
- 새로운 문서 추가 시 2자리 번호를 순차 사용 (예: 22, 23...).

---

## 6) Update Procedure

1. SoR 문서 변경 시: `00_EXECUTIVE_SUMMARY_NODE_CANVAS.md`, `01_NODE_CANVAS_TECHNICAL_SPECIFICATION.md`, `04_CAPSULE_NODE_SPEC.md`, `06_SHEETS_SCHEMA_V1.md`, `07_NOTEBOOKLM_OUTPUT_SPEC_V1.md`, `08_PIPELINES_AND_USER_FLOWS.md`, `09_DB_PROMOTION_RULES_V1.md`, `10_UI_DESIGN_GUIDE_2025-12.md`, `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`, `30_UNIFIED_EXECUTION_ROADMAP.md` 동기화.
2. 파이프라인/스키마 변경 영향이 있으면 `11_INGEST_RUNBOOK_V1.md`, `19_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`, `25_NOTEBOOKLM_SOURCE_PACK_PROTOCOL_CODEX.md`에 반영.
3. 신규 결정사항은 `20_DOC_LINT_RULES_CODEX.md`의 Decision Summary에 반영.
