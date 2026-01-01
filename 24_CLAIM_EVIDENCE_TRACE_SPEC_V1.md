# Claim / Evidence / Trace Spec (V1)

**작성**: 2025-12-26  
**대상**: Product / Design / Engineering  
**목표**: NotebookLM 산출물이 DB SoR로 승격되기 위한 Claim-Evidence-Trace 계약을 고정

---

## 0) Canonical Anchors

- 흐름/역할: `10_PIPELINES_AND_USER_FLOWS.md`
- NotebookLM 출력 규격: `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
- 승격 규칙: `11_DB_PROMOTION_RULES_V1.md`
- 승격 기준: `12_PATTERN_PROMOTION_CRITERIA_V1.md`
- 영상 구조화: `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`

---

## 1) Core Entities

### 1.1 EvidenceRef
DB SoR의 구조화 세그먼트를 가리키는 최소 근거 단위.

필수 필드:
- `evidence_id` (uuid)
- `kind` (shot | segment | beat)
- `source_id` (raw source id)
- `segment_id` or `shot_id`
- `time_start_ms`, `time_end_ms`
- `source_hash` (structured snapshot hash)

권장 필드:
- `tags[]`
- `notes`

### 1.2 Claim
NotebookLM 산출물의 “검증 가능한 주장” 단위.

필수 필드:
- `claim_id` (uuid)
- `claim_type` (pattern | persona | constraint)
- `statement` (짧고 명확한 규칙/주장)
- `evidence_refs[]` (최소 2개)

### 1.3 ClaimEvidenceMap
Claim과 EvidenceRef의 연결 테이블/레코드.

필수 필드:
- `claim_id`
- `evidence_id`
- `weight` (0.0~1.0)
- `created_at`

### 1.4 Trace
승격/실행의 관찰성 기록.

필수 필드:
- `trace_id`
- `bundle_hash`
- `model_version`
- `prompt_version`
- `eval_scores` (groundedness/relevancy/completeness)
- `token_usage`, `latency_ms`, `cost_usd_est`
- `created_at`

권장 필드:
- `eval_scores.ragas` (faithfulness/answer_relevancy/context_precision/context_recall)

---

## 2) Evidence Reference 규칙

1. evidenceRef는 반드시 DB SoR의 구조화 레코드를 가리켜야 한다.
2. `time_start_ms` ~ `time_end_ms`는 segment 범위 내여야 한다.
3. `source_hash`는 구조화 스냅샷의 해시로 고정한다.
4. evidenceRefs는 `db:` 또는 `sheet:` prefix만 허용한다.
5. Claim은 최소 2개의 evidenceRefs를 가진다.

---

## 3) Validation Rules (Ingest Gate)

### 3.1 구조 검증
- Claim, EvidenceRef, Trace 필드 누락 시 Reject
- evidenceRefs 길이 < 2 → Reject

### 3.2 존재성 검증
- evidenceRefs가 DB SoR에 존재하지 않으면 Reject
- `source_hash`가 현재 스냅샷과 다르면 Warning or Reject

### 3.3 정합성 검증
- claim_type이 패턴/페르소나 규칙과 불일치 시 Reject
- temporal_phase 불일치 시 Reject

### 3.4 품질 점수 검증 (RAGAS-style)
- `eval_scores`는 최소 2개 이상 기록 (예: groundedness/relevancy)
- RAGAS 계열 지표는 `eval_scores.ragas.*`로 확장 가능
- 기준 미달 시 `candidate` 유지 또는 `quarantine`

---

## 4) Promotion Gate 연결

이 스펙은 승격 규칙의 “전제 조건”이다.

- 구조/존재성 검증 통과 → `candidate`
- coverage/quant/utility/trace 기준 통과 → `promoted`

상세 기준은 아래 문서에 따른다:
- `11_DB_PROMOTION_RULES_V1.md`
- `12_PATTERN_PROMOTION_CRITERIA_V1.md`

---

## 5) Minimal JSON Examples

### 5.1 EvidenceRef
```json
{
  "evidence_id": "evr_001",
  "kind": "shot",
  "source_id": "src_010",
  "shot_id": "shot_55",
  "time_start_ms": 12000,
  "time_end_ms": 18000,
  "source_hash": "sha256:abcd..."
}
```

### 5.2 Claim
```json
{
  "claim_id": "clm_001",
  "claim_type": "pattern",
  "statement": "phase 내 샷 길이가 점진적으로 단축된다",
  "evidence_refs": ["evr_001", "evr_002"]
}
```

### 5.3 Trace
```json
{
  "trace_id": "trc_001",
  "bundle_hash": "sha256:bundle...",
  "model_version": "gemini-3-pro",
  "prompt_version": "v1",
  "eval_scores": {
    "groundedness": 0.82,
    "relevancy": 0.79,
    "completeness": 0.74
  },
  "token_usage": { "input": 1200, "output": 420 },
  "latency_ms": 1260,
  "cost_usd_est": 0.12
}
```

---

## 6) Acceptance Checklist

- Claim은 반드시 2개 이상의 EvidenceRef를 가진다.
- EvidenceRef는 DB SoR에 존재하며 time range가 유효하다.
- Trace에는 eval_scores + cost/latency/token 기록이 존재한다.
- Promotion Gate에서 이 스펙을 필수 전제 조건으로 사용한다.
