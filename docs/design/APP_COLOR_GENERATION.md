# App/Dimension Color Generation (AppRegistry SSoT)

**Date**: 2026-01-18  
**Purpose**: Keep Dimension/App colors in sync with `config/apps/content/dimensions/*.yaml`.

---

## Generator

- Script: `scripts/generate_app_colors.py`
- Input: `config/apps/content/dimensions/*.yaml`
- Output (required): `tokens/app_colors.json`
- Output (optional): `frontend/src/app/app-colors.css`
- Output (optional): `frontend/src/lib/generated/app_colors.json`

## Run

```bash
python scripts/generate_app_colors.py \
  --input config/apps/content/dimensions \
  --output tokens/app_colors.json \
  --css-output frontend/src/app/app-colors.css \
  --frontend-output frontend/src/lib/generated/app_colors.json
```

## Strategy (v1)

- **Hue**: stable hash of `metadata.name` (0–359)
- **Chroma**: fixed 0.18
- **Lightness**: light 0.52 / dark 0.64

> This produces deterministic colors aligned to the **AppRegistry**.
> Future revisions may replace the hash strategy with curated hues.

## CSS Output

The CSS output generates theme-safe variables:

- `--app-color-{slug}`: light value on `:root`, dark value on `.dark`
- `--app-color-{slug}-light` / `--app-color-{slug}-dark`: explicit values

Use `--app-color-*` to map `--color-dimension-*` in `globals.css` without hardcoding.
