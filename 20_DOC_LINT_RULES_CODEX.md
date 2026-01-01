# Doc Lint Rules (CODEX v26)

**작성**: 2025-12-24  
**대상**: Product / Design / Engineering  
**목표**: 문서 중복을 줄이고, 핵심 원칙/흐름/역할을 단일 기준으로 유지

---

## 0) Canonical Anchors (Single Source of Truth)

- **원칙/철학**: `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
- **흐름/역할**: `10_PIPELINES_AND_USER_FLOWS.md`
- **캡슐 계약**: `05_CAPSULE_NODE_SPEC.md`
- **영상 구조화**: `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`
- **Sheets/DB 계약**: `08_SHEETS_SCHEMA_V1.md`, `11_DB_PROMOTION_RULES_V1.md`
- **NotebookLM 출력 규격**: `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
- **Claim/Evidence/Trace**: `32_CLAIM_EVIDENCE_TRACE_SPEC_V1.md`

---

## 1) Duplication Rules

- 원칙/철학/역할/흐름을 **다른 문서에서 재정의하지 않는다**.
- 필요한 경우 **1줄 요약 + 정본 링크**만 허용한다.
- 동일한 플로우/역할 설명이 2개 문서 이상에 존재하면 **정본으로 합치고 링크로 대체**한다.

---

## 2) Update Discipline

- 새 결정(원칙/흐름/역할 변화)은 `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`에 먼저 반영.
- 흐름/역할 변경은 `10_PIPELINES_AND_USER_FLOWS.md`에 먼저 반영.
- 파이프라인/스키마 변경은 관련 계약 문서(08/09/11/25)에 우선 반영.
- 문서 구조 변경 시 `22_DOCUMENTATION_STRUCTURE_CODEX.md`에 링크 갱신.

---

## 3) Minimal Duplication Pattern (예시)

**허용 예시**
- "상세 흐름은 `10_PIPELINES_AND_USER_FLOWS.md` 참조."
- "영상 구조화는 `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md` 참조."

**금지 예시**
- 다른 문서에 동일한 단계/역할 목록 재작성
- NotebookLM/Opal/DB SoR 역할을 별도 문서에서 재정의

---

## 4) Quick Lint Checks (Manual)

아래 키워드는 중복 가능성이 높으므로 변경 후 확인:

```
rg -n "Non-Negotiable|Crebit DNA|Evidence Loop|User Flow|Creator Flow|Admin Flow" *.md
rg -n "NotebookLM은|Opal|DB SoR|Sheets Bus|Video Structuring|Gemini 구조화" *.md
```

스크립트:
```
./scripts/doc_lint.sh
```

중복 발견 시: 정본 문서로 이동하고 다른 문서는 링크로 대체한다.

---

## 5) Scope Guardrails

- Reference 문서는 정본을 **요약/인용**만 한다.
- SoR 문서 간에도 중복은 최소화하고 **서로 역할을 분리**한다.
- 새로운 대형 문서 추가 시, 0~1 문장으로 canonical anchors를 명시한다.
