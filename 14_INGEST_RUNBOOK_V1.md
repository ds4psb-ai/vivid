# Manual Ingest Runbook (v1)

**작성**: 2025-12-24  
**대상**: Admin / Ops / Data Curation  
**목표**: Gemini 구조화 → NotebookLM/Opal → Sheets Bus → DB SoR 파이프라인을 안정적으로 운영

---

## 0) 전제

- Sheets 스키마는 `08_SHEETS_SCHEMA_V1.md` 기준
- NotebookLM 출력 규격은 `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md` 기준
- DB 승격 규칙은 `11_DB_PROMOTION_RULES_V1.md` 기준
- Pattern 승격 기준은 `12_PATTERN_PROMOTION_CRITERIA_V1.md` 기준
- Ingest API는 **Admin 권한**이 필요 (Notebook/Raw/Video/Derived 모두)

---

## 1) 준비 사항 (필수)

### 1.1 Sheets 탭 확인
- `VIVID_NOTEBOOK_LIBRARY`
- `VIVID_RAW_ASSETS`
- `VIVID_VIDEO_STRUCTURED`
- `VIVID_DERIVED_INSIGHTS`
- `VIVID_PATTERN_CANDIDATES`
- `VIVID_PATTERN_TRACE` (옵션)

### 1.2 ID 규칙 (권장)
- `source_id`: `auteur-{director}-{year}-{slug}`
  - 예: `auteur-bong-1999-barking-dogs`
- `segment_id`: `seg-{source_id}-{shot_index}`
- `work_id`: `work-{director}-{year}-{slug}`
- `scene_id`: `scene-{seq}-{index}` (예: `scene-03`)
- `shot_id`: `shot-{scene}-{index}` (예: `shot-03-01`)
- `output_type`: `video` | `scene` | `image` | `script`
- `output_language`: `ko` | `en` (ISO-639-1)
- `notebook_id`: `nlb-{auteur}-{yy}-{slug}`

### 1.3 권리 상태
- `rights_status`: `ok` | `restricted`
- `restricted`는 DB 승격 대상에서 제외됨

---

## 2) 단계별 운영 루틴

### Step 1: Raw 입력 (관리자 수집)
`VIVID_RAW_ASSETS`에 원본 링크와 메타를 입력합니다.

필수 컬럼: `source_id`, `source_url`, `source_type`, `created_at`  
권장 컬럼: `title`, `director`, `year`, `duration_sec`, `language`, `tags`, `scene_ranges`, `notes`, `rights_status`

예시:
```
source_id,source_url,source_type,title,director,year,duration_sec,language,tags,scene_ranges,rights_status,created_by,created_at
auteur-bong-1999-barking-dogs,https://example.com/video.mp4,video,Barking Dogs,Bong Joon-ho,1999,6360,ko,"class,apartment","00:03:10-00:04:20",ok,admin,2025-12-24T10:00:00Z
```

---

### Step 1.1: JSON 직접 업로드 (옵션)
Raw Asset JSON이 준비되어 있으면 로컬 스크립트로 바로 DB에 업로드할 수 있습니다.

```
cd backend
python scripts/ingest_raw_assets.py --input /absolute/path/raw_assets.json
```

검증만 수행하려면:
```
python scripts/ingest_raw_assets.py --input /path/raw_assets.json --dry-run
```

---

### Step 1.2: Video Structuring (Gemini 3 Pro)
영상 소스는 **ASR + 키프레임/샷 분할** 후 Gemini 구조화 출력으로 변환합니다.

- `responseMimeType=application/json`
- `responseJsonSchema` 적용
- 결과는 `VIVID_VIDEO_STRUCTURED`에 기록
- 문서: `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`
- `time_start/time_end` 형식: `HH:MM:SS.mmm`
- `prompt_version`은 `VIDEO_SCHEMA_VERSIONS` allowlist를 따름 (backend/.env)
- `visual_schema_json` 허용 키: composition, lighting, color_palette, camera_motion, blocking, pacing
- `audio_schema_json` 허용 키: sound_design, music_mood
- `keyframes`, `motifs`, `evidence_refs`는 **비어 있지 않은 문자열 리스트**여야 함 (없으면 생략)
- `keyframes`는 `VIDEO_KEYFRAME_PATTERN`를 따름 (backend/.env)
- `evidence_refs`는 `VIDEO_EVIDENCE_REF_PATTERN`를 따름 (backend/.env, 예: `source:00:00:10.000-00:00:12.500`)

필수 컬럼: `segment_id`, `source_id`, `work_id`, `scene_id`, `shot_id`, `time_start`, `time_end`, `prompt_version`, `model_version`, `generated_at`
권장 컬럼: `sequence_id`

예시:
```
segment_id,source_id,work_id,scene_id,shot_id,time_start,time_end,shot_index,keyframes,transcript,visual_schema_json,audio_schema_json,motifs,confidence,prompt_version,model_version,generated_at
seg-auteur-bong-1999-barking-dogs-01,auteur-bong-1999-barking-dogs,work-bong-1999-barking-dogs,scene-03,shot-03-01,00:03:10.120,00:03:24.880,1,"kf_001,kf_002","...","{""composition"":""blocked_symmetry"",""lighting"":""low_key""}","{""sound_design"":""room_tone""}","stairwell,mirror",0.78,gemini-video-v1,gemini-3-pro-2025-12,2025-12-24T10:30:00Z
```

---

### Step 1.2.1: JSON 직접 업로드 (옵션)
Gemini 구조화 JSON이 준비되어 있으면 로컬 스크립트로 바로 DB에 업로드할 수 있습니다.

```
cd backend
python scripts/ingest_video_structured.py \
  --input /absolute/path/segments.json \
  --default-prompt-version gemini-video-v1 \
  --default-model-version gemini-3-pro-2025-12
```

입력 JSON 형식:
- 배열(list) 또는 단일 객체
- 필드: `segment_id`, `source_id`, `work_id`, `scene_id`, `shot_id`, `time_start`, `time_end`, `prompt_version`, `model_version`
- 옵션: `sequence_id` (act/sequence 단위)
- `visual_schema`/`audio_schema`도 허용 (script가 `*_schema_json`으로 매핑)

검증만 수행하려면:
```
python scripts/ingest_video_structured.py --input /path/segments.json --dry-run
```

---

### Step 1.5: Notebook Library 등록 (권장)
`VIVID_NOTEBOOK_LIBRARY`에 NotebookLM 노트북 메타를 기록합니다.

필수 컬럼: `notebook_id`, `title`, `notebook_ref`, `created_at`
권장 컬럼: `cluster_id`, `cluster_label`, `cluster_tags`, `guide_scope`, `curator_notes`

예시:
```
notebook_id,title,notebook_ref,cluster_id,cluster_label,guide_scope,source_ids,source_count,created_at
nlb-bong-99,Bong Joon-ho Notebook,https://notebooklm.google.com/notebook/abc123,cluster-auteur-bong,"tension-driven symmetry",auteur,"auteur-bong-1999-barking-dogs",1,2025-12-24T10:20:00Z
```

---

### Step 1.5.1: Phase-locked Source Pack (Capsule eligible)
Capsule 승격에 사용하는 **phase-locked pack**은 `build_source_pack.py`로 생성합니다.

- 기본 제한: **source 50개** (NotebookLM phase-locked pack)
- Mega-Notebook은 별도(아래 Step 1.5.2)

예시:
```
cd backend
python scripts/build_source_pack.py \
  --cluster-id cluster-auteur-bong \
  --temporal-phase HOOK \
  --max-sources 50 \
  --output /absolute/path/source_pack.json
```

---

### Step 1.5.2: Mega-Notebook 운영 (옵션, Ops/Discovery 전용)
Mega-Notebook은 **발굴/집계/운영 인사이트 전용**이며, **캡슐 승격에 직접 사용하지 않습니다.**

운영 규칙:
- Mega-Notebook 결과는 **후보 발굴/드리프트 감지/운영 요약**에만 사용
- 캡슐 승격은 반드시 `{cluster_id, temporal_phase}` **phase-locked pack**에서만 수행

메가팩 생성 스크립트 (JSON 출력):
```
cd backend
python scripts/build_mega_source_pack.py \
  --cluster-id cluster-auteur-bong \
  --cluster-id cluster-auteur-park \
  --max-sources 600 \
  --max-segments 500 \
  --notes "ops discovery" \
  --output /absolute/path/mega_pack.json
```

권장 표시:
- Mega-Notebook의 Derived 출력은 `labels`에 `ops_only`를 포함
- `curator_notes`에 `mega_notebook` 문구를 명시

---

### Step 1.5.3: Notebook Library JSON 업로드 (옵션)
Notebook Library JSON이 준비되어 있으면 로컬 스크립트로 바로 DB에 업로드할 수 있습니다.

```
cd backend
python scripts/ingest_notebook_library.py --input /absolute/path/notebooks.json
```

검증만 수행하려면:
```
python scripts/ingest_notebook_library.py --input /path/notebooks.json --dry-run
```

---

### Step 1.6: Notebook Assets 등록 (옵션)
`VIVID_NOTEBOOK_ASSETS`에 노트북이 참조하는 자산(영화/씬/스크립트/스틸)을 등록합니다.

필수 컬럼: `notebook_id`, `asset_id`, `asset_type`
권장 컬럼: `asset_ref`, `title`, `tags`, `notes`

예시:
```
notebook_id,asset_id,asset_type,asset_ref,title,tags,notes
nlb-bong-99,asset-barking-dogs,video,https://example.com/barking_dogs,1999 Barking Dogs,film,class_drift
```

---

### Step 1.6.1: Notebook Assets JSON 업로드 (옵션)
Notebook Assets JSON이 준비되어 있으면 로컬 스크립트로 바로 DB에 업로드할 수 있습니다.

```
cd backend
python scripts/ingest_notebook_assets.py --input /absolute/path/notebook_assets.json
```

검증만 수행하려면:
```
python scripts/ingest_notebook_assets.py --input /path/notebook_assets.json --dry-run
```

---

### Step 2: NotebookLM/Opal 요약 → Derived 입력
`VIVID_DERIVED_INSIGHTS`에 NotebookLM/Opal 출력(JSON)을 규격대로 입력합니다.

핵심 필드 (필수):
- `summary`, `output_type`, `output_language`, `prompt_version`, `model_version`, `source_pack_id`
- Mega-Notebook Derived는 `labels`에 `ops_only`, `mega_notebook`를 포함

권장 필드:
- `style_logic`, `mise_en_scene`, `director_intent`, `labels`, `signature_motifs`
- `camera_motion`, `color_palette`, `pacing`, `key_patterns`
- `story_beats`, `storyboard_cards` (JSON array)
- `guide_type`, `homage_guide`, `variation_guide`, `template_recommendations`, `user_fit_notes`
- `persona_profile`, `synapse_logic`, `origin_notebook_id`, `filter_notebook_id`
- `adapter`, `opal_workflow_id`, `studio_output_id`, `notebook_ref`
- `notebook_id`

작성 규칙:
- 리스트는 콤마 또는 JSON 배열
- 객체 필드는 JSON 형식 권장
- `source_pack_id`는 `source_packs.pack_id`에 존재해야 함 (미존재 시 quarantine)
- `evidence_refs`는 `sheet:{Sheet}:{RowId}` 또는 `db:{table}:{id}`만 허용
- `key_patterns`는 `pattern_name`(snake_case) + `pattern_type`(taxonomy) 규칙을 따라야 함

예시:
```
derived_id,source_id,summary,output_type,output_language,prompt_version,model_version,labels,signature_motifs,camera_motion,color_palette,pacing,key_patterns,adapter,opal_workflow_id,studio_output_id,notebook_id,notebook_ref,generated_at
drv-001,auteur-bong-1999-barking-dogs,"일상적 공간에서 계급 긴장이 축적된다",video_overview,ko,2025-12-24.v1,notebooklm-2025-12,"class_tension,deadpan","stairwell,static_frame","{""mode"":""static"",""moves"":[""slow_pan""]}","{""primary"":[""#102A43"",""#334E68""]}","{""tempo"":""slow""}","[{""pattern_name"":""blocked_symmetry"",""pattern_type"":""scene""}]","notebooklm","opal-vid-001","studio-out-991","nlb-bong-99","https://notebooklm.google.com/notebook/abc123",2025-12-24T10:45:00Z
```

---

### Step 2.1: Derived JSON 업로드 (옵션)
NotebookLM/Opal 출력 JSON을 로컬 스크립트로 DB에 직접 업로드할 수 있습니다.

```
cd backend
python scripts/ingest_derived_insights.py \
  --input /absolute/path/derived_insights.json \
  --default-output-language ko \
  --default-prompt-version 2025-12-24.v1 \
  --default-model-version notebooklm-2025-12
```

검증만 수행하려면:
```
python scripts/ingest_derived_insights.py --input /path/derived_insights.json --dry-run
```

---

### Step 3: Pattern 후보 입력
`VIVID_PATTERN_CANDIDATES`에 패턴 후보를 기록합니다.

필수 컬럼: `source_id`, `pattern_name`, `pattern_type`  
권장 컬럼: `description`, `weight`, `evidence_ref`, `confidence`, `status`

예시:
```
candidate_id,source_id,pattern_name,pattern_type,description,weight,evidence_ref,confidence,status
cand-001,auteur-bong-1999-barking-dogs,blocked_symmetry,scene,"대칭 구도 + 인물 분리",0.72,source:00:03:10-00:04:20,0.68,proposed
```

---

### Step 3.1: Pattern 후보 JSON 업로드 (옵션)
패턴 후보 JSON이 준비되어 있으면 로컬 스크립트로 바로 DB에 업로드할 수 있습니다.

```
cd backend
python scripts/ingest_pattern_candidates.py --input /absolute/path/pattern_candidates.json
```

검증만 수행하려면:
```
python scripts/ingest_pattern_candidates.py --input /path/pattern_candidates.json --dry-run
```

---

### Step 4: DB 승격 (Sheets → DB)
Sheets Bus를 DB SoR로 승격합니다.

#### 4.1 CSV 링크 모드 (권장 초기)
`backend/.env`에 CSV Export URL을 넣고 실행:
```
SHEETS_MODE=csv
VIVID_RAW_ASSETS_CSV_URL=...
VIVID_VIDEO_STRUCTURED_CSV_URL=...
VIVID_DERIVED_INSIGHTS_CSV_URL=...
VIVID_PATTERN_CANDIDATES_CSV_URL=...
VIVID_PATTERN_TRACE_CSV_URL=...
```

CSV Export URL 형식:
```
https://docs.google.com/spreadsheets/d/<spreadsheet_id>/export?format=csv&gid=<sheet_gid>
```

로컬 파일 테스트 (옵션):
```
VIVID_RAW_ASSETS_CSV_URL=file:///absolute/path/raw_assets.csv
```

#### 4.2 Quarantine 출력 (옵션)
필수 컬럼 누락/권한 제한 등으로 스킵된 행을 로컬 CSV로 기록합니다.

```
VIVID_QUARANTINE_CSV_PATH=/absolute/path/vivid_quarantine.csv
```

출력 컬럼:
- `sheet`: 원본 시트명
- `reason`: 스킵 사유 코드
- `row`: 원본 행(JSON, ASCII)
- `created_at`: quarantine 기록 시각 (ISO8601)

API Key 모드에서는 `VIVID_QUARANTINE_RANGE` 시트에 append 됩니다.

```
cd backend
python scripts/promote_from_sheets.py
```

Ops UI에서도 실행 가능:
- `Pipeline` 페이지의 **Sheets 동기화** 버튼 (Admin 전용)
- `POST /api/v1/ops/sheets/sync`

Notebook Library 승격 (권장):
- `VIVID_NOTEBOOK_LIBRARY_CSV_URL` 또는 Sheets range를 설정하면 `promote_from_sheets.py`가 함께 승격한다.

#### 4.2 API 키 모드 (확장)
```
SHEETS_MODE=api_key
SHEETS_SPREADSHEET_ID=...
SHEETS_API_KEY=...
```

---

### Step 4.3: 조회 API (옵션)
구조화 결과를 확인할 때는 아래 엔드포인트를 사용합니다.

- `GET /api/v1/ingest/video-structured/{segment_id}`
- `GET /api/v1/ingest/raw/{source_id}/video-structured`
- `GET /api/v1/ingest/raw/{source_id}`

---

### Step 5: 검수 및 승격 상태 업데이트
- Pattern 후보 `status`를 `validated` 또는 `promoted`로 변경
- 변경 후 스크립트 재실행 → DB Pattern 승격

---

### Step 5.1: Pattern 승격 실행 (DB 기준)
검수 완료된 후보를 Pattern Library로 승격하고 patternVersion을 증가시킵니다.

```
cd backend
python scripts/promote_patterns.py
```

옵션:
- `--min-confidence 0.6` (validated 최소 신뢰도)
- `--min-sources 2` (최소 소스 개수)
- `--allow-empty-evidence` (evidence_ref 없음 허용)
- `--allow-missing-raw` (RawAsset 미존재 허용)
- `--dry-run` (검증만)

Derived key_patterns에서 후보 생성까지 함께 하려면:
```
python scripts/promote_patterns.py --derive-from-evidence
```

---

### Step 6: 파이프라인 상태 리포트 (옵션)
운영 상태를 한 번에 점검할 수 있는 요약 리포트를 출력합니다.

```
cd backend
python scripts/pipeline_report.py
```

---

## 3) 캡슐 반영 (요약)
- CapsuleSpec의 `patternVersion`에 승격된 패턴 버전 연결
- `evidence_refs`에는 Sheet row 또는 DB ref만 유지
- 내부 프롬프트/체인은 절대 클라이언트에 노출 금지

---

## 4) 운영 가드레일

- 원문/프롬프트/워크플로는 Sheets에 저장하지 않기
- 저작권 민감 자료는 `rights_status=restricted`
- Derived는 “요약 + 근거 refs”만 남기기 (증거 원문 제외)
