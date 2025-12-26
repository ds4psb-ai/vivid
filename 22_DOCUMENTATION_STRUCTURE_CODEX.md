# Documentation Structure (CODEX v22)

**Date**: 2025-12-24  
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
- `20_VIVID_ARCHITECTURE_EVOLUTION_CODEX.md`
- `01_NODE_CANVAS_TECHNICAL_SPECIFICATION.md`
- `05_CAPSULE_NODE_SPEC.md`
- `26_DOC_LINT_RULES_CODEX.md`

### B. Data & Evidence (SoR)
- `08_SHEETS_SCHEMA_V1.md`
- `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
- `10_PIPELINES_AND_USER_FLOWS.md`
- `11_DB_PROMOTION_RULES_V1.md`
- `12_PATTERN_PROMOTION_CRITERIA_V1.md`
- `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`
- `31_NOTEBOOKLM_PATTERN_ENGINE_AND_CAPSULE_NODE_CODEX.md`
- `32_CLAIM_EVIDENCE_TRACE_SPEC_V1.md`
- `33_NOTEBOOKLM_SOURCE_PACK_AND_PROMPT_PROTOCOL_CODEX.md`

### C. Execution & Roadmap (Reference)
- See `00_DOCS_INDEX.md`

### D. UI/UX & Product (SoR)
- `13_UI_DESIGN_GUIDE_2025-12.md`
- `06_TEMPLATE_CATALOG.md`
- `23_TEMPLATE_SYSTEM_SPEC_CODEX.md`
- `24_PDR_NODE_CANVAS.md`

### E. Business & Growth (Reference)
- See `00_DOCS_INDEX.md`

### F. Research & Reverse Engineering (Reference)
- See `00_DOCS_INDEX.md`

### G. Audit & Quality (Reference)
- See `00_DOCS_INDEX.md`

---

## 2) Dependency Map (핵심 의존관계)

- `00` → `01`, `05`, `10`, `20` (철학/아키텍처 원칙)
- `01` → `05`, `08`, `09`, `10` (기술 계약/파이프라인)
- `05` → `08`, `09`, `11`, `12` (캡슐 실행/증거 규칙)
- `08` ↔ `09` (Sheets Bus ↔ NotebookLM 출력 규격)
- `10` → `14`, `11`, `12`, `25` (운영/승격/검수/영상 구조화)
- `27` → `10`, `14`, `11`, `12`, `23`, `25` (E2E 파이프라인 상세)
- `28` → `27`, `10`, `14`, `11`, `12`, `23`, `25` (실행 단계/운영 상세)
- `13` → `05` (캡슐 노드 상태/정책 반영)
- `23` → `05`, `10`, `20` (템플릿 구조/캡슐/파이프라인)
- `24` → `00`, `01`, `20`, `23` (제품 요구사항 정렬)
- `31` → `09`, `10`, `11`, `12`, `25`, `05` (NotebookLM -> Capsule pipeline)
- `32` → `09`, `11`, `12`, `25` (Claim/Evidence/Trace)

---

## 3) Definition of Truth (SoR vs Derived vs Reference)

- **SoR**: 핵심 계약/정책 문서 (운영의 기준)
- **Derived**: NotebookLM/Opal 출력 및 Sheets Bus 결과 (승격 전)
- **Reference**: 리서치/벤치마크/로드맵 문서

SoR 변경 시 반드시 관련 문서 링크 업데이트 필요.

**Canonical anchors**
- 원칙/철학: `20_VIVID_ARCHITECTURE_EVOLUTION_CODEX.md`
- 흐름/역할: `10_PIPELINES_AND_USER_FLOWS.md`

---

## 4) NotebookLM/Opal Role (정본 표현)

정본 역할 정의는 `10_PIPELINES_AND_USER_FLOWS.md`를 따른다.

---

## 5) Versioning Rules

- 기존 문서는 유지, 변경 내역은 상단에 **Updated** 기록.
- 구조 변경이나 철학 변경은 `*_CODEX.md`로 확장.
- 새로운 문서 추가 시 2자리 번호를 순차 사용 (예: 22, 23...).

---

## 6) Update Procedure

1. SoR 문서 변경 시: `00/01/05/08/09/10/13/20` 동기화.
2. 변경 영향이 있으면 `07` 또는 `19` 실행 계획에 반영.
3. 신규 결정사항은 `20`의 Decision Summary에 반영.
