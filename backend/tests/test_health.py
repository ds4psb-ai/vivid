"""Health check and route registration tests."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import main


def test_routes_registered() -> None:
    """Test that core routes are registered."""
    paths = {route.path for route in main.app.router.routes}

    # Core routes
    assert "/" in paths

    # Dimension API routes
    assert "/api/dimension/1d/generate" in paths
    assert "/api/dimension/2d/create" in paths
    assert "/api/dimension/3d/generate" in paths
    assert "/api/dimension/4d/analyze" in paths

    # [PIVOTED] Agent routes - disabled for prompty pivot
    # assert "/api/v1/agent/chat" in paths

    # MiniApps routes
    assert "/api/v1/miniapps/submit" in paths
    assert "/api/v1/miniapps/submissions" in paths

    # Prompty routes (new)
    assert "/api/projects" in paths
    assert "/api/templates" in paths
    assert "/api/critique" in paths
