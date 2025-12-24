# Sheets Schema v1 (NotebookLM/Opal Bus)

**작성**: 2025-12-24  
**목표**: NotebookLM/Opal 결과를 빠르게 운영하되, DB SoR로 승격 가능한 최소 스키마

---

## Global rules

- **snake_case** column names
- **append-only** (no destructive updates)
- **id is required** for every row
- use **ISO8601** timestamps

---

## 1) VIVID_RAW_ASSETS (source inventory)

Purpose: raw references (video/image/doc) captured by the admin.

| column | type | required | notes |
| --- | --- | --- | --- |
| source_id | string (uuid) | yes | stable id for the asset |
| source_url | string | yes | original link |
| source_type | enum | yes | video / image / doc |
| title | string | no | free text |
| director | string | no | auteur name or source |
| year | number | no | release year |
| duration_sec | number | no | video length |
| language | string | no | en/ko/ja/etc |
| tags | string | no | comma-separated |
| scene_ranges | string | no | "00:10-00:35;01:05-01:20" |
| notes | string | no | admin memo |
| rights_status | enum | no | unknown / cleared / restricted |
| created_at | datetime | yes | ISO8601 |
| created_by | string | no | admin id |

---

## 2) VIVID_DERIVED_INSIGHTS (NotebookLM outputs)

Purpose: structured outputs from NotebookLM or Opal.

| column | type | required | notes |
| --- | --- | --- | --- |
| derived_id | string (uuid) | yes | row id |
| source_id | string (uuid) | yes | link to raw asset |
| summary | string | yes | short summary |
| style_logic | string | no | logic/structure note |
| mise_en_scene | string | no | visual staging summary |
| director_intent | string | no | personal interpretation |
| labels | string | no | comma-separated |
| signature_motifs | string | no | comma-separated |
| camera_motion | string | no | static/controlled/dynamic + note |
| color_palette | string | no | swatches or bias |
| pacing | string | no | slow/medium/fast + note |
| sound_design | string | no | short note |
| editing_rhythm | string | no | short note |
| key_patterns | string | no | comma-separated pattern names |
| output_type | enum | yes | video_overview / audio_overview / mind_map / report |
| output_language | string | yes | en/ko/ja/etc |
| studio_output_id | string | no | NotebookLM studio output id |
| adapter | enum | no | notebooklm / opal |
| opal_workflow_id | string | no | Opal workflow id |
| confidence | number | no | 0.0~1.0 |
| prompt_version | string | yes | template version |
| model_version | string | yes | model/version tag |
| notebook_ref | string | no | notebook id or url |
| evidence_refs | string | no | comma-separated refs |
| generated_at | datetime | yes | ISO8601 |

---

## 3) VIVID_PATTERN_CANDIDATES (proposed patterns)

Purpose: LLM-proposed patterns before validation.

| column | type | required | notes |
| --- | --- | --- | --- |
| candidate_id | string (uuid) | yes | row id |
| source_id | string (uuid) | yes | link to raw asset |
| pattern_name | string | yes | short label |
| pattern_type | enum | yes | hook / scene / subtitle / audio / pacing |
| description | string | no | short explanation |
| weight | number | no | 0.0~1.0 |
| evidence_ref | string | no | ref or timestamp |
| confidence | number | no | 0.0~1.0 |
| status | enum | yes | proposed / validated / promoted |
| created_at | datetime | yes | ISO8601 |

---

## 4) VIVID_PATTERN_TRACE (validated usage)

Purpose: validated pattern usage per source/variant.

| column | type | required | notes |
| --- | --- | --- | --- |
| trace_id | string (uuid) | yes | row id |
| source_id | string (uuid) | yes | link to raw asset |
| pattern_id | string (uuid) | yes | stable pattern id |
| weight | number | no | 0.0~1.0 |
| evidence_ref | string | no | ref or timestamp |
| created_at | datetime | yes | ISO8601 |

---

## Notes

- Derived rows must reference a **source_id** from VIVID_RAW_ASSETS.
- Pattern Candidates are **not** SoR; only validated patterns are promoted to DB.
- `output_type`/`output_language` reflects NotebookLM Studio multi-output (Ultra 기준).
