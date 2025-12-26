import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import main


def test_health_check_payload() -> None:
    result = asyncio.run(main.health_check())
    assert result["status"] == "ok"
    assert "environment" in result


def test_routes_registered() -> None:
    paths = {route.path for route in main.app.router.routes}
    assert "/" in paths
    assert "/health" in paths
    assert "/api/v1/canvases/" in paths
    assert "/api/v1/ingest/video-structured" in paths
    assert "/api/v1/ingest/video-structured/{segment_id}" in paths
    assert "/api/v1/ingest/raw/{source_id}/video-structured" in paths
