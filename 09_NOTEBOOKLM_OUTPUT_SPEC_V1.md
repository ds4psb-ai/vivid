# NotebookLM Output Spec v1

**작성**: 2025-12-24  
**목표**: 거장 데이터 요약/라벨/패턴 후보를 구조화해 Sheets Bus에 기록

---

## Output rules

- output must be a **single JSON object**
- **no markdown**, **no prose outside JSON**
- arrays must be **flat and compact**
- use empty string/array when unknown

---

## Required fields

- `source_id`
- `summary`
- `output_type`
- `output_language`
- `prompt_version`
- `model_version`
- `generated_at`

## Output type values

- `video_overview`
- `audio_overview`
- `mind_map`
- `report`

---

## Optional fields

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
- `key_patterns[]`
- `cluster_label`
- `cluster_confidence`
- `confidence`
- `studio_output_id`
- `evidence_refs[]`
- `notebook_ref`

---

## JSON schema (example)

```json
{
  "source_id": "uuid",
  "summary": "short summary of the auteur logic and scene pattern",
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
  "generated_at": "2025-12-24T09:00:00Z",
  "evidence_refs": ["source:00:10-00:35", "sheet:VIVID_RAW_ASSETS:42"],
  "notebook_ref": "notebooklm://notebook/abc123",
  "studio_output_id": "studio-output-001"
}
```

---

## Mapping to Sheets

- `VIVID_DERIVED_INSIGHTS.summary` = `summary`
- `VIVID_DERIVED_INSIGHTS.style_logic` = `style_logic`
- `VIVID_DERIVED_INSIGHTS.mise_en_scene` = `mise_en_scene`
- `VIVID_DERIVED_INSIGHTS.director_intent` = `director_intent`
- `VIVID_PATTERN_CANDIDATES` rows derived from `key_patterns[]`
- Opal 출력도 동일 포맷 사용 (adapter=opal, output_type=report 권장)
