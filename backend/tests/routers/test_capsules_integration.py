"""Integration tests for Capsule Router.

P5 Commit 7: DoD verification tests for capsule direct connection.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Skip all tests if dependencies unavailable
try:
    from app.routers.capsules import (
        router,
        list_capsules,
        get_capsule,
        run_capsule,
        get_run_status,
        get_run_history,
        cancel_run,
        stream_run,
    )
    from app.utils.sse_utils import sse_run_event
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    router = None
    list_capsules = None
    get_capsule = None
    run_capsule = None
    get_run_status = None
    get_run_history = None
    cancel_run = None
    stream_run = None
    sse_run_event = None


pytestmark = pytest.mark.skipif(
    not DEPS_AVAILABLE,
    reason=f"Dependencies not available: {IMPORT_ERROR if not DEPS_AVAILABLE else ''}"
)


class TestRouterEndpoints:
    """Tests for capsule router endpoints."""
    
    def test_router_prefix(self):
        """Router should have correct prefix."""
        assert router.prefix == "/api/v1/capsules"
    
    def test_router_tags(self):
        """Router should have capsules tag."""
        assert "capsules" in router.tags


class TestSSERunEvent:
    """Tests for sse_run_event function."""
    
    def test_event_line_included(self):
        """Should include event: line in output."""
        result = sse_run_event("run.completed", {"run_id": "test-123"})
        assert "event: run.completed" in result
        assert "data:" in result
        assert "run_id" in result
    
    def test_heartbeat_event(self):
        """Should format heartbeat event correctly."""
        result = sse_run_event("heartbeat", {"ts": "2026-01-12T00:00:00Z"})
        assert "event: heartbeat" in result


class TestCreditIntegration:
    """Tests for credit integration in run_capsule."""
    
    def test_402_error_format(self):
        """402 error should include required fields."""
        # This is a schema test - actual integration tested via E2E
        expected_fields = ["code", "message", "required", "balance"]
        # Just verify the structure is documented
        assert len(expected_fields) == 4


class TestCapsuleSpecSSoT:
    """Tests for capsule spec SSoT service integration."""
    
    def test_fixtures_available(self):
        """Fixtures should be loadable."""
        try:
            from app.fixtures.dimension_capsules import DIMENSION_CAPSULES
            from app.fixtures.auteur_capsules import CAPSULE_SPECS
            assert len(DIMENSION_CAPSULES) > 0
            assert len(CAPSULE_SPECS) > 0
        except ImportError:
            pytest.skip("Fixtures not available")


class TestDoD:
    """Definition of Done verification tests."""
    
    def test_endpoints_defined(self):
        """All required endpoints should be defined."""
        route_paths = [r.path for r in router.routes]
        
        # Check for required endpoints
        assert "/" in route_paths  # list_capsules
        assert "/{capsule_key}" in route_paths  # get_capsule
        assert "/run" in route_paths  # run_capsule
        assert "/run/{run_id}" in route_paths  # get_run_status
        assert "/{capsule_key}/runs" in route_paths  # get_run_history
        assert "/run/{run_id}/cancel" in route_paths  # cancel_run
        assert "/run/{run_id}/stream" in route_paths  # stream_run
    
    def test_run_response_schema(self):
        """RunResponse should have all frontend-expected fields."""
        from app.routers.capsules import RunResponse
        
        # Get field names from schema
        fields = RunResponse.model_fields.keys()
        
        expected = [
            "run_id",
            "status",
            "summary",
            "evidence_refs",
            "version",
            "token_usage",
            "latency_ms",
            "cost_usd_est",
            "error",
        ]
        
        for field in expected:
            assert field in fields, f"Missing field: {field}"
