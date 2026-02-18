"""Tests for FoundryKPIService."""
from app.features.original_ip_foundry.kpi_service import FoundryKPIService, SlidingWindow


def test_sliding_window_push_and_mean():
    w = SlidingWindow(max_size=10)
    w.push(10.0)
    w.push(20.0)
    assert w.mean() == 15.0


def test_sliding_window_percentile():
    w = SlidingWindow(max_size=100)
    for i in range(1, 101):
        w.push(float(i))
    p95 = w.percentile(95)
    assert p95 is not None
    assert 94 <= p95 <= 96


def test_empty_window_returns_none():
    w = SlidingWindow(max_size=10)
    assert w.mean() is None
    assert w.percentile(50) is None


def test_kpi_record_latency():
    svc = FoundryKPIService(window_size=100)
    for i in range(50):
        svc.record_latency(float(i * 10))
    snap = svc.get_kpi_snapshot()
    assert snap["p95_latency_ms"] is not None
    assert snap["p50_latency_ms"] is not None


def test_kpi_pattern_reuse_rate():
    svc = FoundryKPIService()
    svc.record_pattern_reuse(True)
    svc.record_pattern_reuse(True)
    svc.record_pattern_reuse(False)
    snap = svc.get_kpi_snapshot()
    assert abs(snap["pattern_reuse_rate"] - 0.6667) < 0.01


def test_kpi_continuity_uplift():
    svc = FoundryKPIService()
    svc.record_continuity_score(0.8)
    svc.record_continuity_score(0.7)
    snap = svc.get_kpi_snapshot()
    # mean = 0.75, uplift = 0.75 - 0.5 = 0.25
    assert snap["continuity_uplift"] == 0.25


def test_kpi_empty_snapshot():
    svc = FoundryKPIService()
    snap = svc.get_kpi_snapshot()
    assert snap["p95_latency_ms"] is None
    assert snap["pattern_reuse_rate"] is None
    assert snap["continuity_uplift"] is None
