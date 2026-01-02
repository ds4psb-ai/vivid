# Agent Studio Artifact Spec (V1)

**작성**: 2026-01-01  
**버전**: v1.0  
**대상**: Backend / Frontend / Product  
**목표**: Agent Studio에서 사용되는 표준 아티팩트 타입과 스키마를 고정한다.

---

## 1) 핵심 원칙

- **artifact_type 필수**: 모든 아티팩트는 `artifact_type`이 있어야 한다.
- **JSON-safe**: SSE/DB 저장을 위해 payload는 JSON 직렬화 가능해야 한다.
- **증거 추적**: `evidence_refs` 또는 `source_refs`를 통해 provenance를 유지한다.
- **도구 일관성**: tool 결과에서 생성되는 아티팩트는 표준 스키마로 변환된다.

---

## 2) 공통 필드

모든 아티팩트는 아래 공통 필드를 포함한다.

```json
{
  "artifact_type": "storyboard|shot_list|data_table|scene_card|video_summary|audio_overview",
  "artifact_id": "uuid",
  "title": "string",
  "created_at": "2026-01-01T00:00:00Z"
}
```

추가 메타:
- `version` (옵션): DB 저장 시 버전
- `capsule_id` (옵션): 생성에 사용된 캡슐 식별자

---

## 3) SSE Event Envelope

Agent Chat은 SSE로 아티팩트를 전달한다.

```json
{
  "event_id": "session_id:seq",
  "session_id": "uuid",
  "type": "agent.artifact_update",
  "seq": 42,
  "ts": "2026-01-01T00:00:00Z",
  "payload": {
    "artifact_id": "uuid",
    "artifact_type": "storyboard",
    "payload": { "artifact_type": "storyboard", "...": "..." },
    "version": 1,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z"
  }
}
```

`payload.artifact_type`는 반드시 포함한다.

---

## 4) Artifact Types

### 4.1 Storyboard

```json
{
  "artifact_type": "storyboard",
  "artifact_id": "uuid",
  "title": "Storyboard",
  "created_at": "2026-01-01T00:00:00Z",
  "capsule_id": "auteur.bong-joon-ho",
  "capsule_version": "v1",
  "cards": [
    {
      "shot_id": "shot-01",
      "shot_type": "medium",
      "description": "Opening shot",
      "composition": "Wide hallway",
      "duration_sec": 4,
      "dominant_color": "#333333",
      "accent_color": "#555555",
      "note": "Hold for tension",
      "evidence_refs": ["db:pattern_trace:123"],
      "dialogue": "..."
    }
  ],
  "total_duration_sec": 12
}
```

### 4.2 Shot List

```json
{
  "artifact_type": "shot_list",
  "artifact_id": "uuid",
  "title": "Storyboard - Shot List",
  "created_at": "2026-01-01T00:00:00Z",
  "project_id": "storyboard_artifact_id",
  "shots": [
    {
      "shot_id": "shot-01",
      "sequence": "SEQ-01",
      "scene": "SC-01",
      "shot_size": "MS",
      "action": "Opening shot",
      "dialogue": "Optional",
      "duration": "4s",
      "notes": "..."
    }
  ],
  "total_shots": 1
}
```

### 4.3 Data Table (NotebookLM Claims)

```json
{
  "artifact_type": "data_table",
  "artifact_id": "uuid",
  "title": "Claim Evidence Table",
  "created_at": "2026-01-01T00:00:00Z",
  "columns": [
    { "id": "claim_id", "name": "Claim ID", "type": "string" },
    { "id": "claim_type", "name": "Claim Type", "type": "string" },
    { "id": "statement", "name": "Statement", "type": "string" },
    { "id": "evidence_count", "name": "Evidence Count", "type": "number" },
    { "id": "evidence_refs", "name": "Evidence Refs", "type": "string" }
  ],
  "rows": [
    {
      "claim_id": "c_cluster_logic",
      "claim_type": "pattern",
      "statement": "Logic summary...",
      "evidence_count": 2,
      "evidence_refs": "db:patterns:1, sheet:CREBIT:42"
    }
  ],
  "source_refs": ["db:patterns:1"]
}
```

### 4.4 Scene Card

```json
{
  "artifact_type": "scene_card",
  "artifact_id": "uuid",
  "scene_number": 1,
  "title": "Scene 1",
  "description": "Short scene summary",
  "mood": "tense",
  "color_palette": ["#102A43", "#243B53"],
  "duration_sec": 5,
  "evidence_refs": ["db:pattern_trace:123"]
}
```

### 4.5 Video Summary

```json
{
  "artifact_type": "video_summary",
  "artifact_id": "uuid",
  "title": "Project Summary",
  "created_at": "2026-01-01T00:00:00Z",
  "synopsis": "Short overview...",
  "key_themes": ["tension", "symmetry"],
  "scene_count": 12,
  "visual_style": "muted, cool",
  "capsule_id": "auteur.bong-joon-ho"
}
```

### 4.6 Audio Overview

```json
{
  "artifact_type": "audio_overview",
  "artifact_id": "uuid",
  "title": "Audio Overview",
  "created_at": "2026-01-01T00:00:00Z",
  "status": "READY",
  "focus": "Key beats summary",
  "language_code": "ko",
  "notebook_id": "nb_123",
  "audio_overview_id": "audio_456"
}
```

---

## 5) Tool → Artifact Mapping

- `run_capsule` → `storyboard` + `shot_list`
- `analyze_sources` → `data_table` (NotebookLM claims)
- `generate_storyboard` → `storyboard` (preview)
- `generate_audio_overview` → `audio_overview`

---

## 6) Frontend Render Rules

- Compact view: preview cards/tables (3~5 rows/shots)
- Expanded view: full table + CSV export
- Simple mode: 결과 중심(artifact만 강조)
- Expert mode: tool/metadata 카드 노출

---

## 7) Evidence 규칙

- `evidence_refs`/`source_refs`는 `sheet:` 또는 `db:` 포맷만 허용
- 허용 테이블: `raw_assets`, `video_segments`, `evidence_records`, `patterns`, `pattern_trace`, `notebook_library`

---

## 8) Change Log

- v1.0 (2026-01-01): Agent Studio artifact types + SSE envelope 정의
