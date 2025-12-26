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

## 0) VIVID_NOTEBOOK_LIBRARY (curated notebooks)

Purpose: curated NotebookLM notebook index (private library).

| column | type | required | notes |
| --- | --- | --- | --- |
| notebook_id | string (uuid) | yes | stable id |
| title | string | yes | notebook title |
| notebook_ref | string | yes | notebooklm id/url |
| owner_id | string | no | creator/owner id (self-style) |
| cluster_id | string | no | auteur/genre cluster id |
| cluster_label | string | no | cluster label |
| cluster_tags | string | no | comma-separated tags |
| guide_scope | enum | no | auteur / genre / format / creator / mixed |
| source_ids | string | no | comma-separated source_id list |
| source_count | number | no | number of sources |
| curator_notes | string | no | librarian memo |
| created_at | datetime | yes | ISO8601 |
| updated_at | datetime | no | ISO8601 |

---

## 1) VIVID_NOTEBOOK_ASSETS (library asset links)

Purpose: assets referenced by a NotebookLM notebook (films, scenes, scripts, stills).

| column | type | required | notes |
| --- | --- | --- | --- |
| notebook_id | string (uuid) | yes | link to Notebook Library |
| asset_id | string | yes | stable id for asset |
| asset_type | enum | yes | video / image / doc / script / still / scene / segment / link |
| asset_ref | string | no | url/id reference |
| title | string | no | asset title |
| tags | string | no | comma-separated |
| notes | string | no | librarian notes |
| created_at | datetime | no | ISO8601 |
| updated_at | datetime | no | ISO8601 |

---

## 2) VIVID_RAW_ASSETS (source inventory)

Purpose: raw references (video/image/doc) captured by the admin.

| column | type | required | notes |
| --- | --- | --- | --- |
| source_id | string (uuid) | yes | stable id for the asset |
| source_url | string | yes | original link |
| source_type | enum | yes | video / image / doc |
| title | string | no | free text |
| director | string | no | auteur name or source |
| creator_id | string | no | self-style owner id |
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

## 3) VIVID_VIDEO_STRUCTURED (Gemini video outputs)

Purpose: structured scene/shot outputs from Gemini 3 Pro/Flash.

| column | type | required | notes |
| --- | --- | --- | --- |
| segment_id | string (uuid) | yes | stable id for segment |
| source_id | string (uuid) | yes | link to raw asset |
| work_id | string | yes | film/work identifier |
| sequence_id | string | no | act/sequence identifier |
| scene_id | string | yes | scene identifier |
| shot_id | string | yes | shot identifier |
| time_start | string | yes | HH:MM:SS.mmm |
| time_end | string | yes | HH:MM:SS.mmm |
| shot_index | number | no | optional ordering |
| keyframes | string | no | comma-separated ids |
| transcript | string | no | ASR text |
| visual_schema_json | string | no | JSON string |
| audio_schema_json | string | no | JSON string |
| motifs | string | no | comma-separated |
| confidence | number | no | 0.0~1.0 |
| prompt_version | string | yes | schema version |
| model_version | string | yes | gemini-3-pro-2025-12 |
| evidence_refs | string | no | timecodes/keyframes |
| generated_at | datetime | yes | ISO8601 |

---

## 4) VIVID_DERIVED_INSIGHTS (NotebookLM outputs)

Purpose: structured outputs from NotebookLM or Opal.

| column | type | required | notes |
| --- | --- | --- | --- |
| derived_id | string (uuid) | yes | row id |
| source_id | string (uuid) | yes | link to raw asset |
| notebook_id | string (uuid) | no | link to notebook library |
| source_pack_id | string | yes | phase-locked pack id (or mega pack id) |
| summary | string | yes | short summary |
| guide_type | enum | no | summary / homage / variation / template_fit / persona / synapse / story / beat_sheet / storyboard / study_guide / briefing_doc / table |
| persona_profile | string | no | persona summary (B/D) |
| synapse_logic | string | no | A+B+D→C transform rule |
| origin_notebook_id | string | no | origin notebook (A/B) |
| filter_notebook_id | string | no | filter notebook (D) |
| homage_guide | string | no | homage checklist |
| variation_guide | string | no | remix/variation guide |
| template_recommendations | string | no | comma-separated template ids |
| user_fit_notes | string | no | persona/taste notes |
| style_logic | string | no | logic/structure note |
| mise_en_scene | string | no | visual staging summary |
| director_intent | string | no | personal interpretation |
| labels | string | no | comma-separated; mega outputs include `ops_only,mega_notebook` |
| signature_motifs | string | no | comma-separated |
| camera_motion | string | no | static/controlled/dynamic + note |
| color_palette | string | no | swatches or bias |
| pacing | string | no | slow/medium/fast + note |
| sound_design | string | no | short note |
| editing_rhythm | string | no | short note |
| story_beats | string | no | JSON array (story/beat structure) |
| storyboard_cards | string | no | JSON array (scene cards) |
| key_patterns | string | no | JSON array of objects or comma-separated `pattern_name:pattern_type` |
| cluster_label | string | no | cluster name (optional) |
| cluster_id | string | no | cluster id (optional) |
| output_type | enum | yes | video_overview / audio_overview / mind_map / report / data_table |
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

## 5) VIVID_PATTERN_CANDIDATES (proposed patterns)

Purpose: LLM-proposed patterns before validation.

| column | type | required | notes |
| --- | --- | --- | --- |
| candidate_id | string (uuid) | yes | row id |
| source_id | string (uuid) | yes | link to raw asset |
| pattern_name | string | yes | short label |
| pattern_type | enum | yes | hook / scene / subtitle / audio / pacing |
| description | string | no | short explanation |
| weight | number | no | 0.0~1.0 |
| evidence_ref | string | no | ref or timestamp (VIDEO_EVIDENCE_REF_PATTERN) |
| confidence | number | no | 0.0~1.0 |
| status | enum | yes | proposed / validated / promoted |
| created_at | datetime | yes | ISO8601 |

---

## 6) VIVID_PATTERN_TRACE (validated usage)

Purpose: validated pattern usage per source/variant.

| column | type | required | notes |
| --- | --- | --- | --- |
| trace_id | string (uuid) | yes | row id |
| source_id | string (uuid) | yes | link to raw asset |
| pattern_id | string (uuid or name:type) | yes | uuid 또는 `pattern_name:pattern_type` (normalized, 예: `blocked_symmetry:scene`) |
| weight | number | no | 0.0~1.0 |
| evidence_ref | string | no | ref or timestamp |
| created_at | datetime | yes | ISO8601 |

---

## 7) VIVID_QUARANTINE (optional)

Purpose: ingestion errors or skipped rows for manual review.

| column | type | required | notes |
| --- | --- | --- | --- |
| sheet | string | yes | source sheet name |
| reason | string | yes | skip reason code |
| row | string (json) | yes | raw row as JSON (ASCII) |
| created_at | datetime | no | quarantine timestamp (UTC) |

---

## Notes

- Derived rows must reference a **source_id** from VIVID_RAW_ASSETS and should include **notebook_id** when available.
- Video Structured rows are the canonical scene/shot schema and are used as NotebookLM sources.
- Notebook library rows are private metadata and are not exposed to end users.
- Pattern Candidates are **not** SoR; only validated patterns are promoted to DB.
- `guide_type=persona/synapse`는 통 데이터셋의 **B/D(페르소나)** 및 **Synapse Rule**을 의미.
- `output_type`/`output_language` reflects NotebookLM Studio multi-output (Ultra 기준).
