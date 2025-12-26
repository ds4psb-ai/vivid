Sample Dataset (Pipeline Validation)

These files provide a minimal, synthetic dataset to validate the pipeline in
`27_AUTEUR_PIPELINE_E2E_CODEX.md` and `28_AUTEUR_TEMPLATE_PIPELINE_DETAIL_CODEX.md`.
They contain no real media and are safe for local testing.

Recommended run order (run each with --dry-run first):

One-click helper:

python backend/scripts/run_sample_pipeline.py

Use --execute to apply DB writes:

python backend/scripts/run_sample_pipeline.py --execute

---

1) Raw assets
   python backend/scripts/ingest_raw_assets.py --input data/raw_assets.json

2) Video segments (Gemini structured outputs)
   python backend/scripts/ingest_video_structured.py \
     --input data/video_segments.json \
     --default-prompt-version gemini-video-v1 \
     --default-model-version gemini-3-pro-2025-12

3) Notebook library + assets
   python backend/scripts/ingest_notebook_library.py --input data/notebooks.json
   python backend/scripts/ingest_notebook_assets.py --input data/notebook_assets.json

4) Derived insights (NotebookLM/Opal outputs)
   python backend/scripts/ingest_derived_insights.py \
     --input data/derived_insights.json \
     --default-output-language en \
     --default-prompt-version nlm-guide-v1 \
     --default-model-version notebooklm-2025-12

5) Pattern candidates (validated)
   python backend/scripts/ingest_pattern_candidates.py --input data/pattern_candidates.json

6) Pattern promotion
   python backend/scripts/promote_patterns.py --note "sample promotion"

7) Update capsule patternVersion
   python backend/scripts/update_capsule_pattern_version.py

8) Seed a template from evidence
   python backend/scripts/seed_template_from_evidence.py \
     --notebook-id nlb-sample-auteur \
     --slug sample-auteur-template \
     --title "Sample Auteur Template" \
     --capsule-key auteur.bong-joon-ho \
     --capsule-version 1.0.1 \
     --tags "sample,auteur"

9) Pipeline report
   python backend/scripts/pipeline_report.py
