# App/Dimension Color Generation (AppRegistry SSoT)

**Date**: 2026-01-18  
**Purpose**: Keep Dimension/App colors in sync with `config/apps/content/dimensions/*.yaml`.

---

## Generator

- Script: `scripts/generate_app_colors.py`
- Input: `config/apps/content/dimensions/*.yaml`
- Output: `tokens/app_colors.json`

## Run

```bash
python scripts/generate_app_colors.py \
  --input config/apps/content/dimensions \
  --output tokens/app_colors.json
```

## Strategy (v1)

- **Hue**: stable hash of `metadata.name` (0–359)
- **Chroma**: fixed 0.18
- **Lightness**: light 0.52 / dark 0.64

> This produces deterministic colors aligned to the **AppRegistry**.
> Future revisions may replace the hash strategy with curated hues.
