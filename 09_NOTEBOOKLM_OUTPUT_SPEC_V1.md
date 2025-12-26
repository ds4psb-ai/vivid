# NotebookLM Output Spec v1

**작성**: 2025-12-24  
**목표**: 거장 데이터 요약/라벨/패턴 후보를 구조화해 Sheets Bus에 기록

---

Source Pack/Guide 프로토콜:
- `33_NOTEBOOKLM_SOURCE_PACK_AND_PROMPT_PROTOCOL_CODEX.md`

---

## Output rules

- output must be a **single JSON object**
- **no markdown**, **no prose outside JSON**
- arrays must be **flat and compact**
- use empty string/array when unknown
- Mega-Notebook outputs are **ops-only** and must include `labels: ["ops_only", "mega_notebook"]`.

---

## Required fields

- `source_id`
- `summary`
- `output_type`
- `output_language`
- `prompt_version`
- `model_version`
- `generated_at`
- `source_pack_id`

If the output is from a curated Notebook Library, include `notebook_id`.
If the output is from a Mega-Notebook, include `labels` with `ops_only`, `mega_notebook`.

## Output type values

- `video_overview`
- `audio_overview`
- `mind_map`
- `report`
- `data_table`

---

## Optional fields

- `guide_type` (summary / homage / variation / template_fit / persona / synapse / story / beat_sheet / storyboard / study_guide / briefing_doc / table)
- `temporal_phase` (HOOK / BUILD / PAYOFF / CTA / SETUP / TURN / ESCALATION / CLIMAX / RESOLUTION)
- `homage_guide`
- `variation_guide`
- `template_recommendations[]`
- `user_fit_notes`
- `cluster_id`
- `cluster_label`
- `persona_profile`
- `synapse_logic`
- `origin_notebook_id`
- `filter_notebook_id`
- `style_logic`
- `mise_en_scene`
- `director_intent`
- `labels[]`
- `signature_motifs[]`
- `camera_motion` (object)
- `color_palette` (object)
- `pacing` (object)
- `sound_design`
- `editing_rhythm`
- `story_beats[]`
- `storyboard_cards[]`
- `key_patterns[]`
- `cluster_label`
- `cluster_confidence`
- `confidence`
- `studio_output_id`
- `evidence_refs[]`
- `claims[]`
- `notebook_ref`
- `notebook_id`

---

## Evidence refs format

- Derived outputs must use: `sheet:{SheetName}:{RowId}` or `db:{table}:{id}`
- Allowed `db` tables: `raw_assets`, `video_segments`, `evidence_records`, `patterns`, `pattern_trace`, `notebook_library`
- `source:` and other prefixes are reserved for **video_structured** evidence only and will be filtered at capsule boundary

---

## JSON schema (example)

```json
{
  "source_id": "uuid",
  "summary": "short summary of the auteur logic and scene pattern",
  "guide_type": "variation",
  "persona_profile": "director profile with trauma/era/philosophy summary",
  "synapse_logic": "A+B passed through D becomes C with heightened color + pop cues",
  "origin_notebook_id": "nlb-origin-001",
  "filter_notebook_id": "nlb-filter-777",
  "homage_guide": "keep symmetry, avoid handheld, preserve cool palette",
  "variation_guide": "shift pacing to fast while maintaining symmetry",
  "template_recommendations": ["tmpl-auteur-bong", "tmpl-auteur-park"],
  "user_fit_notes": "prefers tense pacing and cool palettes",
  "cluster_id": "cluster-auteur-bong",
  "cluster_label": "tension-driven symmetry",
  "output_type": "video_overview",
  "output_language": "ko",
  "style_logic": "cause-effect structure or narrative logic",
  "mise_en_scene": "staging, blocking, framing notes",
  "director_intent": "interpretation of intent or theme",
  "labels": ["tension", "symmetry", "social class"],
  "signature_motifs": ["stairs", "mirror symmetry", "rain reflections"],
  "camera_motion": {
    "mode": "controlled",
    "notes": "slow push-ins with tension"
  },
  "color_palette": {
    "bias": "cool",
    "swatches": ["#102A43", "#243B53", "#334E68"],
    "notes": "muted blues with low saturation"
  },
  "pacing": {
    "tempo": "medium",
    "notes": "3-5s average cuts"
  },
  "sound_design": "diegetic ambience + sparse music",
  "editing_rhythm": "holds long shots, then rapid cut",
  "story_beats": [
    { "beat_id": "b1", "summary": "daily routine reveals class tension", "tension": "low" },
    { "beat_id": "b2", "summary": "intrusion escalates stakes", "tension": "medium" }
  ],
  "storyboard_cards": [
    { "card_id": "c1", "shot": "static wide", "palette": "cool", "note": "stairwell symmetry" }
  ],
  "key_patterns": [
    {
      "pattern_name": "vertical_blocking",
      "pattern_type": "scene",
      "description": "stacked framing to show hierarchy",
      "weight": 0.8
    }
  ],
  "cluster_label": "tension-driven symmetry",
  "cluster_confidence": 0.62,
  "confidence": 0.74,
  "prompt_version": "nlm-auteur-v1",
  "model_version": "notebooklm-2025-12",
  "source_pack_id": "sp_cluster-auteur-bong_HOOK_20251224",
  "generated_at": "2025-12-24T09:00:00Z",
  "evidence_refs": ["sheet:VIVID_RAW_ASSETS:42", "db:video_segments:seg-auteur-bong-1999-barking-dogs-01"],
  "notebook_id": "nlb-001",
  "notebook_ref": "notebooklm://notebook/abc123",
  "studio_output_id": "studio-output-001"
}
```

---

## Mapping to Sheets

- `VIVID_DERIVED_INSIGHTS.summary` = `summary`
- `VIVID_DERIVED_INSIGHTS.guide_type` = `guide_type`
- `VIVID_DERIVED_INSIGHTS.homage_guide` = `homage_guide`
- `VIVID_DERIVED_INSIGHTS.variation_guide` = `variation_guide`
- `VIVID_DERIVED_INSIGHTS.template_recommendations` = `template_recommendations[]`
- `VIVID_DERIVED_INSIGHTS.user_fit_notes` = `user_fit_notes`
- `VIVID_DERIVED_INSIGHTS.cluster_id` = `cluster_id`
- `VIVID_DERIVED_INSIGHTS.cluster_label` = `cluster_label`
- `VIVID_DERIVED_INSIGHTS.persona_profile` = `persona_profile`
- `VIVID_DERIVED_INSIGHTS.synapse_logic` = `synapse_logic`
- `VIVID_DERIVED_INSIGHTS.origin_notebook_id` = `origin_notebook_id`
- `VIVID_DERIVED_INSIGHTS.filter_notebook_id` = `filter_notebook_id`
- `VIVID_DERIVED_INSIGHTS.style_logic` = `style_logic`
- `VIVID_DERIVED_INSIGHTS.mise_en_scene` = `mise_en_scene`
- `VIVID_DERIVED_INSIGHTS.director_intent` = `director_intent`
- `VIVID_DERIVED_INSIGHTS.notebook_id` = `notebook_id`
- `VIVID_DERIVED_INSIGHTS.story_beats` = `story_beats[]`
- `VIVID_DERIVED_INSIGHTS.storyboard_cards` = `storyboard_cards[]`
- `VIVID_PATTERN_CANDIDATES` rows derived from `key_patterns[]`
- Opal 출력도 동일 포맷 사용 (adapter=opal, output_type=report 권장)
