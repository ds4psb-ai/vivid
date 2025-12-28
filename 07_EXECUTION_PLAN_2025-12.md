# Execution Plan (2025-12 최신 기준)

**작성**: 2025-12-24  
**대상**: Product / Engineering / Ops  
**목표**: NotebookLM/Opal + Sheets Bus 기반으로 빠르게 돌리되, DB/이벤트 기반 아키텍처로 무리 없이 확장

---

## 0) 기본 원칙 (정본 참조)

- 철학/원칙: `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
- 흐름/역할: `10_PIPELINES_AND_USER_FLOWS.md`
- 계약/정책: `05_CAPSULE_NODE_SPEC.md`, `08_SHEETS_SCHEMA_V1.md`, `11_DB_PROMOTION_RULES_V1.md`

---

## Phase 1: Dataization MVP (0~6주)

### 1.1 Sheets 스키마 확정 (주 1)
- Notebook Library 시트: `notebook_id`, `title`, `notebook_ref`, `source_ids`, `source_count`
- Raw 시트: `source_url`, `title`, `duration`, `scene_notes`, `created_at`, `annotator`
- Video Structured 시트: `segment_id`, `source_id`, `time_start`, `time_end`, `visual_schema_json`, `audio_schema_json`
- Derived 시트: `source_id`, `summary`, `labels`, `output_type`, `output_language`, `prompt_version`, `model_version`, `confidence`, `notebook_id`
- Pattern 후보: `pattern_id`, `pattern_type`, `description`, `source_id`
- Pattern Trace: `variant_id`, `pattern_id`, `weight`, `evidence_ref`
- 문서: `08_SHEETS_SCHEMA_V1.md`
- 패턴 시드: `15_PATTERN_TAXONOMY_V1.md`

### 1.2 Gemini 구조화 출력 (주 1)
- ASR + 샷/키프레임 분할 후 Gemini 3 Pro/Flash로 구조화 JSON 생성
- `CREBIT_VIDEO_STRUCTURED`에 기록 후 DB SoR 승격
- 문서: `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`

### 1.3 Notebook Library 등록 (주 1)
- NotebookLM 노트북 메타를 `CREBIT_NOTEBOOK_LIBRARY`에 등록
- 노트북은 비공개 지식 베이스로 유지 (UI 노출 금지)
- 클러스터 메타(`cluster_id`, `cluster_label`, `guide_scope`)로 거장/장르 묶음 관리
- (옵션) Mega-Notebook은 **발굴/집계/운영 전용**으로만 사용하고, 캡슐 승격은 **phase-locked pack**에서만 수행

### 1.4 NotebookLM 출력 규격 (주 1)
- 출력 JSON 포맷 고정
- `summary`, `output_type`, `output_language`, `prompt_version`, `model_version` 필수화
- `notebook_id` 포함 (Library 연동)
- `guide_type`, `homage_guide`, `variation_guide`, `template_recommendations`로 가이드 레이어 강화
- `persona_profile`, `synapse_logic`, `origin_notebook_id`, `filter_notebook_id` 추가 (통 데이터셋)
- 동일 입력 재실행 시 버전 증가 규칙 정의
- 문서: `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`

### 1.5 수동 인제스트 운영 루틴 (주 2)
- 관리자 수집 링크 → Raw 시트 입력
- Gemini 구조화 → Video Structured 시트 기록
- NotebookLM 실행 → Derived 시트 기록
- 일일/주간 검수 → Pattern 후보 승인
- (옵션) API 입력: `/api/v1/ingest/raw`, `/api/v1/ingest/derive`
- 문서: `14_INGEST_RUNBOOK_V1.md`

### 1.6 DB 승격 파이프라인 (주 3~4)
- Notebook Library + Sheets → DB 일괄 업서트 (idempotent)
- Pattern Library/Trace 테이블 생성
- 승격 상태: `proposed → validated → promoted`
- 문서: `11_DB_PROMOTION_RULES_V1.md`
- 스크립트: `backend/scripts/promote_from_sheets.py`

### 1.6.1 Pattern 승격 기준 확정
- 검수 기준/리프트 기준 확정
- 문서: `12_PATTERN_PROMOTION_CRITERIA_V1.md`

### 1.7 캡슐 반영 (주 5~6)
- CapsuleSpec에 DB 기반 패턴/파라미터 주입
- evidence_refs에 sheet_row 또는 db_ref 연결
- 캡슐 버전 고정 정책 적용

### 1.8 관찰성 최소 기준 (주 6)
- capsule_run trace_id + prompt/model version 로그
- evidence_refs와 결과 요약 저장

---

## Phase 2: Optimization + Evidence Loop (6~12주)

### 2.1 Pattern Lift 계산
- `Lift = (variant - parent) / parent` 기본 수식 적용
- Pattern Lift 집계 테이블 구축

### 2.2 GA/RL 연결
- Pattern Lift 기반 피트니스/보상 설계
- 온라인 로그 + 주간 오프라인 학습 루프

### 2.3 관찰성/평가 지표
- Run trace, 비용/지연, 품질 지표 대시보드
- Evidence Coverage, Pattern Lift 평균 모니터링

### 2.4 LLMOps 평가 하니스 (옵션)
- 프롬프트/체인 버전 관리 + 오프라인 평가셋
- groundedness/relevancy/completeness 지표 기록
- 휴먼 피드백 수집 → 템플릿/캡슐 개선 루프

---

## Phase 3: Event-driven 확장 (3~6개월)

### 3.1 이벤트 기반 작업 분리
- Ingestion / Summarize / Promote / Generate 큐 분리
- 재시도/보상 처리 정책 정의

### 3.2 비용/지연 최적화
- 프리뷰 저비용 모델, 최종 고품질 모델 분리
- 캐시 정책 + 스냅샷 버전 관리

### 3.3 Dev/QA/Prod 분리 (운영 기준)
- 캡슐/템플릿 승격은 QA 검증 후 PROD 반영
- 배포 전후 품질/비용 리그레션 체크

---

## 산출물 체크리스트

- [x] Sheets 스키마 v1
- [x] Notebook Library 시트/DB
- [x] NotebookLM 출력 규격 v1
- [x] DB 승격 스크립트
- [x] Pattern Library/Trace 테이블
- [x] CapsuleSpec 버전 고정 정책
- [x] Pattern Lift 산출 리포트

> [!NOTE]
> **2025-12-28 업데이트**: Phase 1 Dataization MVP 100% 완료. 상세 진행은 `21_DOCUMENTATION_AUDIT_REPORT_V1.md` 참조.
