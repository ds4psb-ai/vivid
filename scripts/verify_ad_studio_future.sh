#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WITH_TESTS=0

if [[ "${1:-}" == "--with-tests" ]]; then
  WITH_TESTS=1
fi

echo "[verify] root: $ROOT"
echo "[verify] mode: $([[ "$WITH_TESTS" -eq 1 ]] && echo "with-tests" || echo "static-only")"

required_files=(
  "backend/app/routers/dimension/ad_studio.py"
  "backend/app/services/ad_brain.py"
  "backend/app/services/ad_prompt_engine.py"
  "frontend/src/components/dimension/ADStudioPanel.tsx"
  "frontend/src/components/dimension/ad-studio/SequenceTimeline.tsx"
  "backend/tests/routers/test_ad_studio.py"
  "frontend/src/components/dimension/ad-studio/SequenceTimeline.test.tsx"
)

for rel in "${required_files[@]}"; do
  if [[ ! -f "$ROOT/$rel" ]]; then
    echo "[fail] missing file: $rel"
    exit 1
  fi
  echo "[ok] file exists: $rel"
done

checks=(
  "backend/app/routers/dimension/ad_studio.py|ALLOWED_ENGINES"
  "backend/app/routers/dimension/ad_studio.py|/analyze-video"
  "backend/app/routers/dimension/ad_studio.py|continuity_score"
  "backend/app/services/ad_brain.py|decomposition:5-domain"
  "backend/app/services/ad_brain.py|_calculate_continuity_score"
  "frontend/src/components/dimension/ADStudioPanel.tsx|/api/dimension/ad-studio/analyze"
  "frontend/src/components/dimension/ADStudioPanel.tsx|MAX_SCENARIO_LENGTH"
  "frontend/src/components/dimension/ad-studio/SequenceTimeline.tsx|연속성 점수"
  "frontend/src/components/dimension/ad-studio/SequenceTimeline.tsx|text-emerald-500"
  "backend/tests/routers/test_ad_studio.py|test_router_has_four_routes"
  "backend/tests/routers/test_ad_studio.py|test_build_sequence_analysis_continuity_score"
  "frontend/src/components/dimension/ad-studio/SequenceTimeline.test.tsx|shows continuity score badge when provided"
)

for item in "${checks[@]}"; do
  file="${item%%|*}"
  pattern="${item#*|}"
  if rg -n --fixed-strings "$pattern" "$ROOT/$file" >/dev/null; then
    echo "[ok] pattern found: $file :: $pattern"
  else
    echo "[fail] pattern missing: $file :: $pattern"
    exit 1
  fi
done

if [[ "$WITH_TESTS" -eq 1 ]]; then
  echo "[run] pytest backend/tests/routers/test_ad_studio.py"
  (
    cd "$ROOT/backend"
    if [[ -x "venv/bin/pytest" ]]; then
      ./venv/bin/pytest -q tests/routers/test_ad_studio.py
    else
      pytest -q tests/routers/test_ad_studio.py
    fi
  )
fi

echo "[done] AD Studio future verification passed."
