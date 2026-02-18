"""Tests for PatternPruningService."""
from app.features.original_ip_foundry.pattern_pruning_service import PatternPruningService


def test_prune_without_qdrant():
    svc = PatternPruningService(qdrant_pattern_store=None)
    result = svc.prune(dry_run=True)
    assert result["would_delete_count"] == 0
    assert result["error"] == "no_qdrant_store"


def test_prune_returns_filters_applied():
    svc = PatternPruningService()
    result = svc.prune(confidence_threshold=0.2, max_age_days=30, dry_run=True)
    assert result["filters_applied"]["confidence_threshold"] == 0.2
    assert result["filters_applied"]["max_age_days"] == 30


def test_prune_with_project_filter():
    svc = PatternPruningService()
    result = svc.prune(project_id="test-project", dry_run=True)
    assert result["filters_applied"]["project_id"] == "test-project"


def test_default_thresholds():
    assert PatternPruningService.DEFAULT_CONFIDENCE_THRESHOLD == 0.3
    assert PatternPruningService.DEFAULT_MAX_AGE_DAYS == 90


def test_prune_dry_run_flag():
    svc = PatternPruningService()
    result = svc.prune(dry_run=True)
    assert result["dry_run"] is True
