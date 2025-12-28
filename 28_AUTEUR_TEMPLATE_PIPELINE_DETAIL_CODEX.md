# Auteur Data -> Template -> Creator Usage Pipeline (Detailed, CODEX v28)

**Date**: 2025-12-24  
**Status**: CODEX (SoR detail extension)  
**Purpose**: 거장/명장면 데이터화부터 템플릿화, 사용자 실행, 학습까지 **실제 운영 가능한 단계별 파이프라인**을 상세하게 정의한다.

---

## 0) Scope & Invariants

**Scope**
- 이 문서는 `27_AUTEUR_PIPELINE_E2E_CODEX.md`의 **실행 상세판**이다.
- 운영자가 실제로 진행 가능한 수준으로 **입력/출력/검증/오너/엔드포인트**를 구체화한다.

**Invariants (절대 원칙)**
- **DB SoR**가 증명/학습의 기준이며, NotebookLM/Opal은 **가이드/가속 레이어**다.
- 원본 영상/내부 JSON은 NotebookLM에 직접 넣지 않는다.
- 캡슐 노드는 **Sealed**: 입력/출력/노출 파라미터만 공개한다.
- 재현성은 `capsule_id@version + patternVersion`으로 고정한다.
- evidence는 `sheet:`/`db:`로 추적 가능해야 한다.

References:  
`20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`, `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`,  
`27_AUTEUR_PIPELINE_E2E_CODEX.md`, `10_PIPELINES_AND_USER_FLOWS.md`,  
`33_NOTEBOOKLM_SOURCE_PACK_AND_PROMPT_PROTOCOL_CODEX.md`

---

## 1) Roles & Ownership

| Role | Responsibility | Output |
| --- | --- | --- |
| Admin/Curator | 원본 수집/권리 확인/노트북 큐레이션 | RawAsset, NotebookLibrary/Assets |
| Data Engineer | 전처리/구조화/승격 파이프라인 운영 | VideoSegment, EvidenceRecord |
| Reviewer | 패턴 승격/리스크 검수 | Pattern, PatternVersion |
| Product/Studio | 템플릿 공개/버전 관리 | Template, TemplateVersion |
| Creator/PD/Writer | 템플릿 기반 실행/피드백 | CapsuleRun, GenerationRun |

---

## 2) Artifact Map (SoR vs Derived)

| Artifact | Source of Truth | Storage | Visibility |
| --- | --- | --- | --- |
| RawAsset | SoR | DB | Admin only |
| VideoSegment | SoR | DB | Admin only |
| NotebookLibrary | SoR | DB | Admin only |
| NotebookAsset | SoR | DB | Admin only |
| Derived Insight | Derived | Sheets Bus | Admin + Ops |
| EvidenceRecord | SoR | DB | Admin + Ops |
| Pattern/Trace/Version | SoR | DB | Admin + Ops |
| CapsuleSpec | SoR | DB | Limited (sealed) |
| Template/TemplateVersion | SoR | DB | Creator (public) |
| CapsuleRun | SoR | DB | Creator + Ops |
| GenerationRun | SoR | DB | Creator + Ops |

---

## 2.1 Canonical Hierarchy & IDs (Film -> Scene -> Shot)

**Purpose**: 영상 해석 결과가 템플릿/패턴/학습으로 이어질 수 있도록 ID 체계를 고정한다.

**Hierarchy**
- **work_id**: 작품 단위 (Film/Episode/Ad)
- **sequence_id**: 큰 흐름 (Act/Sequence)
- **scene_id**: 장면 단위 (story beat)
- **shot_id**: 촬영 단위 (camera cut)
- **segment_id**: 구조화 출력 단위 (shot split or micro-shot)

**Required fields (minimum)**
- `work_id`, `scene_id`, `shot_id`, `segment_id`
- `time_start`, `time_end`, `source_id`
- `visual_schema`, `audio_schema`, `motifs[]`
- `prompt_version`, `model_version`

**Rules**
- `segment_id`는 `shot_id`에 종속된다.
- `scene_id`는 반드시 `work_id`에 종속된다.
- 템플릿/패턴 승격은 **scene_id 이상** 단위에서만 가능.

---

## 3) End-to-End Pipeline (Detailed Stages)

### Stage 0. Source Intake (RawAsset)
**Goal**: 명장면/거장 레퍼런스의 출처/권리 상태를 안정적으로 등록한다.  
**Input**: URL, title, director, year, notes, rights_status  
**Process**: 출처 확인 → rights_status 지정 → RawAsset upsert  
**Output**: `raw_assets`  
**Owner**: Admin/Curator  
**API**: `POST /api/v1/ingest/raw`  
**Gate**: `rights_status=restricted`는 이후 승격 금지  
**Failure**: missing source_id/source_url → quarantine

---

### Stage 1. Preprocess (ASR/Shot/Keyframe)
**Goal**: 영상의 구조적 단위를 만든다.  
**Input**: RawAsset video  
**Process**: ASR, shot boundary, keyframe extraction  
**Output**: preprocess JSON (timecode + keyframe ids)  
**Owner**: Data Engineer  
**Tooling**: external pipeline (FFmpeg/whisper/shot-detect 등)  
**Gate**: 타임코드 누락/키프레임 과다 방지

---

### Stage 2. Gemini Structured Output (VideoSegment)
**Goal**: 장면/샷을 구조화해 DB SoR에 적재한다.  
**Input**: preprocess JSON  
**Process**: Gemini 3 Pro/Flash structured output  
**Output**: `video_segments` rows  
**Owner**: Data Engineer  
**API**: `POST /api/v1/ingest/video-structured`  
**Gate**: JSON Schema 검증, evidence refs 패턴 검증  
**Failure**: invalid evidence refs → quarantine

**Required fields (MVP)**
- `work_id`, `scene_id`, `shot_id`, `segment_id`
- `time_start`, `time_end`, `source_id`
- `visual_schema` (composition/lighting/color/camera/blocking/pacing)
- `audio_schema` (sound_design/music_mood)
- `motifs[]` (optional)

---

### Stage 3. Notebook Library & Assets (Private)
**Goal**: 거장/장르 클러스터 지식의 책장을 구축한다.  
**Input**: notebook meta + asset refs  
**Process**: NotebookLibrary + NotebookAsset 등록  
**Output**: `notebook_library`, `notebook_assets`  
**Owner**: Admin/Curator  
**API**:  
- `POST /api/v1/ingest/notebook`  
- `POST /api/v1/ingest/notebook-assets`  
**Gate**: 노트북은 관리자 전용, 사용자에게 직접 노출 금지

---

### Stage 4. NotebookLM/Opal Derived Outputs (Guide Layer)
**Goal**: 요약/오마주/변주/템플릿 적합도 가이드를 생성한다.  
**Input**: DB SoR + **Source Pack**  
**Process**: NotebookLM/Opal 실행 → JSON 출력  
**Output**: `CREBIT_DERIVED_INSIGHTS` (Sheets Bus)  
**Owner**: Admin/Curator  
**Contract**: `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`  
**Gate**: guide_type / output_type allowlist 준수  
**Protocol**: `33_NOTEBOOKLM_SOURCE_PACK_AND_PROMPT_PROTOCOL_CODEX.md`

**Guide types (MVP)**
- `summary`: 작품/장면 요약
- `homage`: 거장 스타일 오마주 가이드
- `variation`: 변주/리믹스 가이드
- `persona`: 작가/거장 해석/철학 요약
- `synapse`: A+B→C 변환 규칙 요약
- `story`/`beat_sheet`/`storyboard`: 서사 seed

---

### Stage 5. Sheets Bus → DB Promotion (Evidence)
**Goal**: Derived 결과를 검증 가능한 SoR로 승격한다.  
**Input**: Sheets CSV  
**Process**: `promote_from_sheets.py` 실행  
**Output**: `evidence_records`, `pattern_candidates`  
**Owner**: Data Engineer  
**Script**: `backend/scripts/promote_from_sheets.py`  
**Gate**: invalid schema rows → quarantine

---

### Stage 6. Pattern Promotion + Versioning
**Goal**: 증명된 패턴만 캡슐에 반영한다.  
**Input**: `pattern_candidates`  
**Process**: Review → approve → Pattern/Trace update → PatternVersion increment  
**Output**: `patterns`, `pattern_trace`, `pattern_versions`  
**Owner**: Reviewer  
**Policy**: `12_PATTERN_PROMOTION_CRITERIA_V1.md`
**Script**: `backend/scripts/promote_patterns.py`

---

### Stage 7. Capsule Spec Update
**Goal**: 최신 패턴 스냅샷을 캡슐 스펙에 고정한다.  
**Input**: latest PatternVersion  
**Process**: CapsuleSpec `patternVersion` 갱신  
**Output**: `capsule_specs`  
**Owner**: Product/Studio  
**Gate**: `capsule_id@version + patternVersion` 재현성 보장
**Script**: `backend/scripts/update_capsule_pattern_version.py`

---

### Stage 8. Template Seeding (Narrative + Pattern)
**Goal**: NotebookLM 가이드로 **Script/Storyboard seed**가 포함된 템플릿 생성.  
**Input**: EvidenceRecord (story_beats, storyboard_cards, key_patterns)  
**Process**: Template graph 생성 → TemplateVersion 저장  
**Output**: `templates`, `template_versions`  
**Owner**: Product/Studio  
**API/Script**:  
- `POST /api/v1/templates/seed/from-evidence`  
- `backend/scripts/seed_template_from_evidence.py`  
**Seed Graph**: `Input → Capsule → Script/Beat → Storyboard → Output`

**Seeding rules (detail)**
- `guide_type=homage/variation` → 캡슐 기본 파라미터 `style_intensity`, `pacing`, `color_bias` 기본값 생성
- `key_patterns[]` → 템플릿 tags + `patternVersion` 연결
- `story_beats[]` → Script/Beat 노드 seed
- `storyboard_cards[]` → Storyboard 노드 seed
- `persona/synapse` → Capsule params override (tone, rhythm, motif weight)

---

### Stage 9. Template Publish
**Goal**: Creator에게 노출할 템플릿 확정.  
**Input**: Template + Version  
**Process**: is_public + tags + description 확정  
**Output**: 템플릿 카드 갤러리 노출  
**Owner**: Product/Studio  
**Gate**: evidence_refs 포함 여부 확인

---

### Stage 10. Creator Canvas Execution (Preview)
**Goal**: 창작자가 템플릿 기반으로 캔버스를 실행한다.  
**Input**: Template → Canvas graph  
**Process**: CapsuleRun + Preview panel  
**Output**: `capsule_runs`, preview payload  
**Owner**: Creator  
**API**:  
- `POST /api/v1/capsules/run`  
- `GET /api/v1/capsules/run/{run_id}/stream` (SSE)  
- `WS /ws/runs/{run_id}` (WS)

---

### Stage 11. Generation Run (Final)
**Goal**: 프리뷰 이후 고품질 결과 생성.  
**Input**: Preview spec  
**Process**: GenerationRun 실행  
**Output**: `generation_runs` + artifacts  
**Owner**: Creator  
**API**: `POST /api/v1/runs`

---

### Stage 12. Feedback → Learning
**Goal**: 결과 성과를 학습으로 연결한다.  
**Input**: Evidence metrics  
**Process**: GA 탐색 → RL 보정 → Template 승격  
**Output**: TemplateVersion update  
**Owner**: Reviewer + Product  
**Gate**: evidence thresholds 충족 시만 승격

---

## 4) Narrative Data (Story/Beat/Storyboard)

**Source**: NotebookLM/Opal derived output  
**Fields**:
- `story_beats[]`: beat sheet summary list  
- `storyboard_cards[]`: shot/scene card list  
**Usage**:
- Stage 8 Template Seeding에서 Script/Storyboard 노드에 seed로 삽입  
- Stage 10 Preview에서 생성 시 seed가 그대로 표시됨  
**Contract**: `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`

---

## 5) Failure Modes & Controls

- **권리 문제**: `rights_status=restricted`는 승격 금지  
- **Schema 실패**: quarantine 기록 후 재실행  
- **NotebookLM 편향**: DB SoR 승격 규칙으로 완충  
- **비용 폭증**: Preview/Final 분리, credit_cost 상한  
- **재현성 붕괴**: capsule_id@version + patternVersion 고정

---

## 6) Implementation Anchors (현재 코드 기준)

**Ingest API**
- `/api/v1/ingest/raw`
- `/api/v1/ingest/video-structured`
- `/api/v1/ingest/notebook`
- `/api/v1/ingest/notebook-assets`

**Promotion**
- `backend/scripts/promote_from_sheets.py`

**Template Seeding**
- `POST /api/v1/templates/seed/from-evidence`
- `backend/scripts/seed_template_from_evidence.py`

**Execution**
- `/api/v1/capsules/run`
- `/api/v1/capsules/run/{run_id}/stream`
- `/ws/runs/{run_id}`
- `/api/v1/runs`

**Ops**
- `backend/scripts/pipeline_report.py`
- `GET /api/v1/ops/pipeline`
  - `CREBIT_QUARANTINE_CSV_PATH`가 설정되어 있으면 쿼런틴 요약 포함
  - 최근 patternVersion 히스토리(최근 5개) 포함
  - Quarantine 샘플 row(최대 20개) 포함
  - patternVersion note 표시

---

## 7) Operator Runbook (Commands)

> 운영자 기준 "필수 실행 순서"만 정리한다. 각 단계는 `--dry-run`로 먼저 검증한다.
> 샘플 페이로드는 `data/README.md` 및 `data/*.json`을 참고한다.

### 7.1 RawAsset (Stage 0)
```bash
python backend/scripts/ingest_raw_assets.py --input data/raw_assets.json
```

### 7.2 Preprocess (Stage 1)
외부 파이프라인에서 ASR/shot/keyframe 추출 후 `data/preprocess/*.json`에 저장.  
이 결과는 Stage 2 입력으로만 사용 (DB write 없음).

### 7.3 VideoSegment (Stage 2)
```bash
python backend/scripts/ingest_video_structured.py \
  --input data/video_segments.json \
  --source-id SRC_001 \
  --prompt-version v1 \
  --model-version gemini-3-pro
```

### 7.4 Notebook Library & Assets (Stage 3)
```bash
python backend/scripts/ingest_notebook_library.py --input data/notebooks.json
python backend/scripts/ingest_notebook_assets.py --input data/notebook_assets.json
```

### 7.5 Derived Insights (Stage 4)
**Preferred**: Sheets Bus → Stage 5 승격  
**Local QA (직접 적재)**:
```bash
python backend/scripts/ingest_derived_insights.py \
  --input data/derived_insights.json \
  --default-output-language ko \
  --default-prompt-version v1 \
  --default-model-version opal-1
```

### 7.6 Sheets Promotion (Stage 5)
```bash
export CREBIT_DERIVED_INSIGHTS_CSV_URL="https://..."
python backend/scripts/promote_from_sheets.py
```

### 7.7 Pattern Promotion (Stage 6)
```bash
python backend/scripts/promote_patterns.py --derive-from-evidence --note "pattern v2"
```

### 7.8 Capsule Spec Update (Stage 7)
```bash
python backend/scripts/update_capsule_pattern_version.py
```

### 7.9 Template Seeding (Stage 8)
```bash
python backend/scripts/seed_template_from_evidence.py \
  --notebook-id NB_001 \
  --slug auteur-bong-v1 \
  --title "Bong Joon-ho v1" \
  --capsule-key auteur.bong-joon-ho \
  --capsule-version 1.0.1 \
  --tags "auteur,thriller"
```

### 7.10 Creator Runs (Stage 9-11)
- UI에서 템플릿 선택 → Canvas 실행 → Preview → Generate
- API: `/api/v1/capsules/run` → `/ws/runs/{run_id}` → `/api/v1/runs`

### 7.11 Pipeline Health Check
```bash
python backend/scripts/pipeline_report.py
```

---

## 8) Acceptance Criteria (Operator Checklist)

1. RawAsset 등록 + rights_status 확인  
2. VideoSegment 구조화 업로드 성공  
3. NotebookLibrary + NotebookAssets 등록  
4. NotebookLM derived output 생성 (Sheets Bus)  
5. Promote 실행 후 EvidenceRecord 생성  
6. Pattern 승격 + PatternVersion 증가  
7. Template seeded (Script/Storyboard 포함)  
8. Creator preview 실행 성공 (capsule run)  
9. Final generation 실행 성공 (generation run)

---

## 9) Creator Flow (User Step-by-Step)

1. Template 카드 선택 (Auteur/Creator/Synapse)
2. Canvas 생성 후 입력 자료 연결 (script/scene/video)
3. Capsule 파라미터 조정 (style_intensity, pacing 등)
4. Preview 실행 (WS/SSE 스트리밍)
5. Preview 결과 확인 (summary + storyboard cards)
6. Generate 실행 (최종 산출물)
7. Export + Feedback 입력 (Evidence Loop로 연결)

---

## 10) Related Docs

- `27_AUTEUR_PIPELINE_E2E_CODEX.md`
- `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`
- `10_PIPELINES_AND_USER_FLOWS.md`
- `08_SHEETS_SCHEMA_V1.md`
- `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
- `11_DB_PROMOTION_RULES_V1.md`
- `12_PATTERN_PROMOTION_CRITERIA_V1.md`
- `23_TEMPLATE_SYSTEM_SPEC_CODEX.md`
