# DB Promotion Rules v1 (Sheets → DB SoR)

**작성**: 2025-12-24  
**대상**: Engineering / Ops  
**목표**: NotebookLM/Opal 결과를 Sheets Bus에서 DB SoR로 안정적으로 승격

---

## 0) 기본 원칙

- **idempotent upsert** (동일 입력 반복 실행 가능)
- **append-only in Sheets**, 정합성은 DB에서 확보
- Raw/Derived/Pattern은 **분리 테이블로 저장**
- 승격 기준은 `12_PATTERN_PROMOTION_CRITERIA_V1.md`를 따른다

---

## 1) 입력 시트 → DB 매핑

| Sheets | 목적 | DB 대상(개념) |
| --- | --- | --- |
| VIVID_NOTEBOOK_LIBRARY | 노트북 메타 | notebook_library |
| VIVID_NOTEBOOK_ASSETS | 노트북 자산 링크 | notebook_assets |
| VIVID_RAW_ASSETS | 원본 링크/메타 | raw_assets |
| VIVID_VIDEO_STRUCTURED | 영상 구조화(샷/씬) | video_segments |
| VIVID_DERIVED_INSIGHTS | NotebookLM/Opal 요약 | evidence_records |
| VIVID_PATTERN_CANDIDATES | 패턴 후보 | pattern_candidates (staging) |
| VIVID_PATTERN_TRACE | 검증된 패턴 적용 | pattern_trace |

DB SoR에 **승격되는 것은 validated/promoted 패턴**만.
`guide_type=persona/synapse`는 evidence_records에 태그로 보존된다.

---

## 2) Upsert 키 규칙 (MVP 기준)

### 2.1 raw_assets
- **key**: `source_id`
- duplicate URL은 허용하되 `source_id` 기준이 우선

### 2.2 video_segments
- **key**: `segment_id`
- `segment_id`가 없으면 `(source_id, time_start, time_end, prompt_version, model_version)`로 대체

### 2.3 evidence_records
- **key**: `(source_id, prompt_version, model_version, output_type, output_language)`
- 동일 키는 **최신 generated_at**으로 덮어쓰기

### 2.4 patterns
- **key**: `(pattern_name_normalized, pattern_type)`
- `pattern_id`가 있으면 그것을 우선 키로 사용 (uuid 또는 `pattern_name:pattern_type` 허용)

### 2.5 pattern_trace
- **key**: `(source_id, pattern_id, evidence_ref)`
- `pattern_id`는 uuid 또는 `pattern_name:pattern_type` (normalized)로 입력 가능
- 동일 키는 **weight 업데이트만 허용**

---

## 3) 승격 흐름

1. **Sheets 수집**: Raw/Derived/Candidate/Trace 추출
2. **유효성 검사**: 필수 컬럼/타입/참조 무결성 확인
3. **Pattern 후보 필터**: status=validated/promoted만 DB 승격
4. **Upsert 실행**: key 규칙대로 DB 반영
5. **patternVersion 증가**: 변경 내용이 있으면 스냅샷 버전 +1

---

## 4) 데이터 품질 검사

- **source_id 존재 여부** (Derived/Candidate/Trace 모두 필수)
- **video_structured 타임코드 누락**은 Reject
- **prompt_version/model_version/output_type** 누락 시 Reject
- **rights_status=restricted**인 Raw는 자동 승격 금지
- **confidence < threshold**인 Candidate는 승격 보류
- **video_structured evidence_refs**는 `VIDEO_EVIDENCE_REF_PATTERN`을 만족해야 승격
- **derived evidence_refs**는 `sheet:`/`db:` 포맷만 허용 (불일치 시 quarantine)
- **pattern_trace evidence_ref**는 `VIDEO_EVIDENCE_REF_PATTERN`을 만족해야 승격
- **key_patterns**는 `pattern_name:pattern_type` 규칙 및 taxonomy를 만족해야 승격
- **eval_scores** 누락 시 quarantine (RAGAS 계열 점수는 optional)

---

## 5) 오류 처리 (MVP)

- 실패 행은 **quarantine 시트**로 이동 (수동 재검토)
- 오류 이유를 `error_reason` 컬럼에 기록
- 재실행 시 동일 키는 안전하게 덮어쓰기
- CSV 모드에서는 `VIVID_QUARANTINE_CSV_PATH`로 로컬 quarantine 파일을 기록
- API Key 모드에서는 `VIVID_QUARANTINE_RANGE`로 append 기록

---

## 6) 최소 운영 루틴

- **주 1회 배치 업서트** (초기)
- 패턴 승격 완료 후 **capsule spec 버전 증가**
- 모든 승격 로그는 `trace_id`로 연결
- 실행 스크립트: `backend/scripts/promote_from_sheets.py`

---

## 7) Sheets API 운영 기준 (리서치 반영)

- 요청은 **batchGet/batchUpdate**로 묶어 호출 수 최소화
- **2MB 이하 payload** 권장 (응답/요청 모두)
- **per-minute quota**에 맞춰 배치 주기/크기 조절
- 실패 시 **exponential backoff**로 재시도
- Sheets 업데이트는 **atomic**하므로 부분 실패 대비 필요
