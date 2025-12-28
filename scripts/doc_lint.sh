#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[doc-lint] canonical anchor scan"

if command -v rg >/dev/null 2>&1; then
  rg -n "Non-Negotiable|Crebit DNA|Evidence Loop|User Flow|Creator Flow|Admin Flow" *.md || true
  rg -n "NotebookLM은|Opal|DB SoR|Sheets Bus|Video Structuring|Gemini 구조화" *.md || true
else
  grep -nE "Non-Negotiable|Crebit DNA|Evidence Loop|User Flow|Creator Flow|Admin Flow" *.md || true
  grep -nE "NotebookLM은|Opal|DB SoR|Sheets Bus|Video Structuring|Gemini 구조화" *.md || true
fi

echo "[doc-lint] done"
