#!/bin/bash
# H3.2: Coverage and Mutation Testing Script
# Usage: ./scripts/coverage.sh [mode]
#   mode: full | quick | mutation | report
#   default: full

set -e

MODE="${1:-full}"
MIN_COVERAGE=60

echo "========================================"
echo "Vivid Backend Coverage Script"
echo "Mode: $MODE"
echo "========================================"

# Ensure we're in the backend directory
cd "$(dirname "$0")/.."

# Activate virtualenv if exists
if [ -d "venv/bin" ]; then
    source venv/bin/activate
elif [ -d ".venv/bin" ]; then
    source .venv/bin/activate
fi

case $MODE in
    quick)
        echo ""
        echo "=== Running Quick Tests (no coverage) ==="
        pytest --tb=short -q
        ;;

    full)
        echo ""
        echo "=== Running Tests with Full Coverage ==="
        pytest \
            --cov=app \
            --cov-branch \
            --cov-report=term-missing \
            --cov-report=html \
            --cov-report=xml \
            --cov-fail-under=$MIN_COVERAGE

        echo ""
        echo "=== Coverage Summary ==="
        coverage report --fail-under=$MIN_COVERAGE

        echo ""
        echo "HTML Report: htmlcov/index.html"
        echo "XML Report: coverage.xml"
        ;;

    mutation)
        echo ""
        echo "=== Running Mutation Tests (Critical Services) ==="
        echo "This may take a while..."

        # Run mutation tests on critical services only
        mutmut run \
            --paths-to-mutate=app/services/credit_service.py \
            --tests-dir=tests/services/ \
            --runner="pytest -x -q --tb=no"

        echo ""
        echo "=== Mutation Results ==="
        mutmut results
        ;;

    report)
        echo ""
        echo "=== Generating Coverage Report ==="
        coverage html
        coverage xml
        coverage report

        echo ""
        echo "HTML Report: htmlcov/index.html"
        ;;

    ci)
        echo ""
        echo "=== CI Mode: Running Tests with Coverage ==="
        pytest \
            --cov=app \
            --cov-branch \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-fail-under=$MIN_COVERAGE \
            --junitxml=test-results.xml

        echo ""
        echo "Coverage XML: coverage.xml"
        echo "Test Results: test-results.xml"
        ;;

    *)
        echo "Unknown mode: $MODE"
        echo "Usage: ./scripts/coverage.sh [mode]"
        echo "  mode: full | quick | mutation | report | ci"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "Done!"
echo "========================================"
