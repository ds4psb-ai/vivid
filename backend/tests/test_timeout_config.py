"""Timeout configuration regression tests."""

from app.core.timeouts import TimeoutConfig


def test_scene_detect_routes_use_extended_timeout():
    """Scene-detect uploads should not use the 30s default API timeout."""
    timeout = TimeoutConfig.get_for_route("/api/v1/scene-detect/")
    assert timeout == 600.0
