#!/usr/bin/env bash
# Vivid CI Check Script
# Runs backend tests, frontend lint/build, and doc-lint in sequence.
# Exit on first failure.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Vivid CI Check ==="
echo "Root: $ROOT_DIR"
echo ""

# Phase 1: Backend Tests
echo "[1/4] Backend Tests"
cd "$ROOT_DIR/backend"
if [ -f "venv/bin/python" ]; then
    venv/bin/python -m pytest -q
else
    python -m pytest -q
fi
echo "✓ Backend tests passed"
echo ""

# Phase 2: Frontend Lint
echo "[2/4] Frontend Lint"
cd "$ROOT_DIR/frontend"
npm run lint
echo "✓ Frontend lint passed"
echo ""

# Phase 3: Frontend Build
echo "[3/4] Frontend Build"
npm run build
echo "✓ Frontend build passed"
echo ""

# Phase 4: Doc Lint
echo "[4/4] Documentation Lint"
cd "$ROOT_DIR"
if [ -f "scripts/doc_lint.sh" ]; then
    ./scripts/doc_lint.sh
    echo "✓ Doc lint passed"
else
    echo "⚠ scripts/doc_lint.sh not found, skipping"
fi
echo ""

echo "=== All CI checks passed! ==="
