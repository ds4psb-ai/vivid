# Auteur Data -> Template -> Creator Usage Pipeline (CODEX v27)

**Date**: 2025-12-24  
**Status**: SoR (End-to-End execution blueprint)  
**Goal**: 거장/명장면 데이터화부터 템플릿화, 사용자 실행, 학습/승격까지의 전 과정을 완전한 실행 파이프라인으로 정의한다.

---

## 0) Invariants (절대 원칙)

- **DB SoR**가 증명/학습의 기준이다. NotebookLM/Opal은 **가이드/가속 레이어**다.
- 원본 영상/내부 JSON은 **NotebookLM에 직접 노출하지 않는다**.
- 캡슐 노드는 **Sealed**: 입력/출력/파라미터만 공개, 내부 체인은 서버 전용.
- 재현성은 **capsule_id@version + patternVersion**으로 고정한다.
- 증거는 **evidence_refs**로 추적 가능해야 하며 `sheet:`/`db:`만 허용한다.

참조 문서:  
`10_PIPELINES_AND_USER_FLOWS.md`, `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`,  
`05_CAPSULE_NODE_SPEC.md`, `11_DB_PROMOTION_RULES_V1.md`,  
`33_NOTEBOOKLM_SOURCE_PACK_AND_PROMPT_PROTOCOL_CODEX.md`

---

## 1) Core Entities (DB SoR 기준)

- **RawAsset**: 원본 레퍼런스 링크/메타
- **VideoSegment**: Gemini 구조화(샷/씬) 결과
- **NotebookLibrary**: 노트북 메타(클러스터/가이드 범위)
- **NotebookAsset**: 노트북이 참조하는 자산 링크
- **EvidenceRecord**: NotebookLM/Opal 요약/가이드 출력
- **PatternCandidate**: LLM 제안 패턴 후보
- **Pattern / PatternTrace / PatternVersion**: 검증된 패턴과 적용 기록
- **CapsuleSpec**: 실행 규약(입력/출력/노출 파라미터)
- **Template / TemplateVersion**: 재사용 가능한 파이프라인 블루프린트
- **Canvas / CapsuleRun / GenerationRun**: 사용자 실행 및 결과

---

## 2) E2E Pipeline (Admin -> User -> Learning)

### Stage 0. Source Intake (Admin Ingest)
**Goal**: 거장/명장면 원본을 안정적으로 등록한다.  
**Input**: Raw URLs / Asset metadata  
**Process**: 권리 상태/출처 확인 → RawAsset 등록  
**Output**: `raw_assets` (SoR), 권리 메모  
**Check**: rights_status=restricted 는 승격 금지

---

### Stage 1. Preprocess (ASR / Shot / Keyframe)
**Goal**: 영상의 구조적 단위를 만든다.  
**Process**: ASR + shot boundary + keyframe extraction  
**Output**: 전처리 산출물 (JSON/text)  
**Check**: 타임코드 누락/키프레임 과다 방지

---

### Stage 2. Gemini Structured Output (Video Schema)
**Goal**: 장면/샷을 구조화해 DB SoR에 적재한다.  
**Input**: 전처리 산출물  
**Process**: Gemini 3 Pro/Flash structured output  
**Output**: `video_segments` rows  
**Check**: schema validation + evidence refs 규칙  

---

### Stage 3. Notebook Library + Assets (Private)
**Goal**: 거장/장르 클러스터 지식의 "책장"을 구축한다.  
**Input**: 노트북 메타 + 참조 자산  
**Process**: NotebookLibrary + NotebookAssets 등록  
**Output**: `notebook_library`, `notebook_assets`  
**Check**: 노트북은 관리자 전용, 사용자에게 직접 노출 금지

---

### Stage 4. NotebookLM/Opal Guide Outputs (Derived)
**Goal**: 요약/오마주/변주/템플릿 적합도 가이드를 만든다.  
**Input**: DB SoR + **Source Pack** (원본 영상 금지)  
**Process**: NotebookLM/Opal 실행 → JSON 출력  
**Output**: `VIVID_DERIVED_INSIGHTS` (Sheets Bus)  
**Check**: `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md` 규격 준수  
**Protocol**: `33_NOTEBOOKLM_SOURCE_PACK_AND_PROMPT_PROTOCOL_CODEX.md`

---

### Stage 5. Sheets Bus -> DB Promotion (Evidence)
**Goal**: Derived 결과를 검증 가능한 데이터로 승격한다.  
**Process**: Sheets Bus 수집 → quarantine → DB upsert  
**Output**: `evidence_records`, `pattern_candidates`  
**Check**: idempotent upsert + 규칙 위반 row는 quarantine

---

### Stage 6. Pattern Promotion + Versioning
**Goal**: 검증된 패턴만 캡슐에 반영한다.  
**Process**: 후보 필터링 → Pattern/Trace 승격 → PatternVersion 증가  
**Output**: `patterns`, `pattern_trace`, `pattern_versions`  
**Check**: 승격 기준은 `12_PATTERN_PROMOTION_CRITERIA_V1.md`

---

### Stage 7. Capsule Spec Update
**Goal**: 최신 패턴 스냅샷을 캡슐 스펙에 고정한다.  
**Process**: CapsuleSpec `patternVersion` 갱신  
**Output**: `capsule_specs`  
**Check**: `capsule_id@version + patternVersion` 재현성 보장

---

### Stage 8. Template Seeding (Auteur / Creator / Synapse)
**Goal**: 사용자가 즉시 시작할 템플릿을 만든다.  
**Input**: NotebookLM/Opal Derived + PatternVersion  
**Process**: 템플릿 그래프 생성 → TemplateVersion 기록  
**Output**: `templates`, `template_versions`  
**Check**: Public Graph만 저장, 내부 체인은 저장 금지

**Seeding Rules (MVP)**
- `guide_type=homage/variation` → **Capsule Params** 기본값 생성
- `story_beats[]` → **Script/Beat Node** seed (요약 텍스트)
- `storyboard_cards[]` → **Storyboard Node** seed (컷/카드 요약)
- `key_patterns[]` → 템플릿 **tag + PatternVersion** 연결
- 템플릿 그래프 기본형: `Input → Capsule → Script → Storyboard → Output`

---

### Stage 9. Creator Canvas Execution
**Goal**: 템플릿 기반 캔버스 실행/미리보기 제공.  
**Process**: Canvas 생성 → Capsule Run (WS/SSE) → Preview  
**Output**: `capsule_runs`, preview payload  
**Check**: evidence_refs 필터링, 비용/토큰/지연 기록

---

### Stage 10. Generate (Script/Storyboard/Scene)
**Goal**: 프리뷰 이후 고품질 결과 생성.  
**Process**: GenerationRun 실행 → 결과 저장  
**Output**: `generation_runs` + output artifacts  
**Check**: 프리뷰/최종 분리, 비용 상한 적용

---

### Stage 11. Feedback -> Learning (GA/RL)
**Goal**: 성과 데이터를 학습으로 연결한다.  
**Process**: Evidence Loop 점수 → GA 탐색 → RL 보정  
**Output**: 개선된 params + 템플릿 버전 승격  
**Check**: evidence 기반만 승격, 자동 승격은 제한

---

### Stage Contracts (Minimum Fields)
- **Stage 0** RawAsset: `source_id`, `source_url`, `source_type`, `rights_status`
- **Stage 2** VideoSegment: `segment_id`, `source_id`, `work_id`, `scene_id`, `shot_id`, `sequence_id?`, `time_start`, `time_end`, `visual_schema`, `prompt_version`, `model_version`
- **Stage 3** NotebookLibrary: `notebook_id`, `title`, `notebook_ref`, `guide_scope`, `cluster_id`
- **Stage 4** Derived: `summary`, `output_type`, `output_language`, `guide_type`, `story_beats[]?`, `storyboard_cards[]?`, `key_patterns[]?`
- **Stage 6** PatternTrace: `pattern_id`, `source_id`, `evidence_ref`, `weight`, `pattern_version`
- **Stage 8** Template: `graph.nodes`, `capsule_id@version`, `patternVersion`, `guide_sources`, `narrative_seeds`
- **Stage 9** CapsuleRun: `upstream_context`, `evidence_refs`, `credit_cost`, `token_usage`, `latency_ms`
- **Stage 10** GenerationRun: `spec`, `outputs`, `artifact_refs`
- **Stage 10 Outputs (MVP)**: `script_text`, `storyboard_cards`, `previewUrl`

---

## 3) Narrative/Story Schema (Derived Layer)

- **Story/Beat/Storyboard**는 `guide_type=story/beat_sheet/storyboard`로 구분한다.  
- 구조화된 서사는 `story_beats[]`와 `storyboard_cards[]`에 저장한다.  
- **Persona/Synapse**는 `guide_type=persona/synapse`로 구분한다.  
- 템플릿에는 **요약/가이드만** 사용하고 원문은 노출 금지한다.

---

## 4) Acceptance Criteria (MVP 기준)

1. **거장 1명 + 작품 3개**의 구조화/가이드/패턴이 끝까지 승격됨  
2. 해당 데이터를 기반으로 **템플릿 1개**가 생성되고 캔버스에서 실행됨  
3. 실행 결과에 **patternVersion + evidence_refs**가 포함됨  
4. 프리뷰와 최종 생성이 **분리**되어 비용 제어가 가능함  

---

## 5) Known Risks & Controls

- **권리/출처 문제**: RawAsset rights_status로 차단  
- **NotebookLM 편향**: DB SoR 승격 규칙으로 완충  
- **패턴 과적합**: 승격 기준/표본 수 최소치 유지  
- **비용 폭증**: 프리뷰/최종 분리 + credit cost 정책  

---

## 6) Implementation Pointers

- Ingest 운영: `14_INGEST_RUNBOOK_V1.md`  
- DB 승격: `11_DB_PROMOTION_RULES_V1.md`  
- 템플릿 정책: `23_TEMPLATE_SYSTEM_SPEC_CODEX.md`  
- 템플릿 시드: `backend/scripts/seed_template_from_evidence.py` 또는 `POST /api/v1/templates/seed/from-evidence`  
- 캡슐 계약: `05_CAPSULE_NODE_SPEC.md`  
- 실행 계획: `19_VIVID_EXECUTION_PLAN_V1.md`

---

## 7) End-to-End Checklist (Operator View)

1. **RawAsset 등록**: `source_id`, `source_url`, `rights_status` 확인  
2. **Preprocess**: ASR/shot/keyframe 산출 → 파일 경로/메타 저장  
3. **Gemini 구조화**: `video_segments` 업서트 + evidence refs 검증  
4. **Notebook Library 생성**: 클러스터 노트북 등록  
5. **Notebook Assets 연결**: 노트북과 참조 자산 링크 기록  
6. **NotebookLM/Opal 실행**: `guide_type`별 요약/가이드 생성  
7. **Sheets Bus 기록**: Derived JSON 업로드 (`VIVID_DERIVED_INSIGHTS`)  
8. **Promotion 배치**: `promote_from_sheets.py` 실행 → quarantine 확인  
9. **Pattern 검수**: `pattern_candidates` 승인/보류  
10. **Pattern Trace 등록**: 적용 근거/evidence ref 기록  
11. **patternVersion 증가 확인**: 캡슐/템플릿 버전 반영  
12. **템플릿 시드 생성**: Script/Storyboard 노드 포함 그래프 작성  
13. **캔버스 실행 검증**: Preview 생성 + evidence_refs 확인  
14. **초기 학습 루프**: GA/RL 추천 결과 점검 → 승격 여부 판단
