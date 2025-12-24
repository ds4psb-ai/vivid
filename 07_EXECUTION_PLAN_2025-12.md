# Execution Plan (2025-12 최신 기준)

**작성**: 2025-12-24  
**대상**: Product / Engineering / Ops  
**목표**: NotebookLM/Opal + Sheets Bus 기반으로 빠르게 돌리되, DB/이벤트 기반 아키텍처로 무리 없이 확장

---

## 0) 기본 원칙

- NotebookLM/Opal은 **가속 레이어**, DB는 **SoR**
- Sheets Bus는 **초기 운영 버스**, DB로 승격 가능해야 함
- Raw/Derived 분리 + 버전 고정 + append-only 로그 유지
- 캡슐 노드는 요약/근거만 노출 (IP 보호)
- 파이프라인/사용자 흐름 기준 문서: `10_PIPELINES_AND_USER_FLOWS.md`

---

## Phase 1: Dataization MVP (0~6주)

### 1.1 Sheets 스키마 확정 (주 1)
- Raw 시트: `source_url`, `title`, `duration`, `scene_notes`, `created_at`, `annotator`
- Derived 시트: `source_id`, `summary`, `labels`, `output_type`, `output_language`, `prompt_version`, `model_version`, `confidence`
- Pattern 후보: `pattern_id`, `pattern_type`, `description`, `source_id`
- Pattern Trace: `variant_id`, `pattern_id`, `weight`, `evidence_ref`
- 문서: `08_SHEETS_SCHEMA_V1.md`

### 1.2 NotebookLM 출력 규격 (주 1)
- 출력 JSON 포맷 고정
- `summary`, `output_type`, `output_language`, `prompt_version`, `model_version` 필수화
- 동일 입력 재실행 시 버전 증가 규칙 정의
- 문서: `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`

### 1.3 수동 인제스트 운영 루틴 (주 2)
- 관리자 수집 링크 → Raw 시트 입력
- NotebookLM 실행 → Derived 시트 기록
- 일일/주간 검수 → Pattern 후보 승인

### 1.4 DB 승격 파이프라인 (주 3~4)
- Sheets → DB 일괄 업서트 (idempotent)
- Pattern Library/Trace 테이블 생성
- 승격 상태: `proposed → validated → promoted`
- 문서: `11_DB_PROMOTION_RULES_V1.md`
- 스크립트: `backend/scripts/promote_from_sheets.py`

### 1.4.1 Pattern 승격 기준 확정
- 검수 기준/리프트 기준 확정
- 문서: `12_PATTERN_PROMOTION_CRITERIA_V1.md`

### 1.5 캡슐 반영 (주 5~6)
- CapsuleSpec에 DB 기반 패턴/파라미터 주입
- evidence_refs에 sheet_row 또는 db_ref 연결
- 캡슐 버전 고정 정책 적용

### 1.6 관찰성 최소 기준 (주 6)
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

---

## Phase 3: Event-driven 확장 (3~6개월)

### 3.1 이벤트 기반 작업 분리
- Ingestion / Summarize / Promote / Generate 큐 분리
- 재시도/보상 처리 정책 정의

### 3.2 비용/지연 최적화
- 프리뷰 저비용 모델, 최종 고품질 모델 분리
- 캐시 정책 + 스냅샷 버전 관리

---

## 산출물 체크리스트

- [ ] Sheets 스키마 v1
- [ ] NotebookLM 출력 규격 v1
- [ ] DB 승격 스크립트
- [ ] Pattern Library/Trace 테이블
- [ ] CapsuleSpec 버전 고정 정책
- [ ] Pattern Lift 산출 리포트
