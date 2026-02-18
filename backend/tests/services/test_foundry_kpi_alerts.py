"""Tests for KPI alert rules in FoundryKPIService."""
from __future__ import annotations

import pytest

from app.features.original_ip_foundry.kpi_service import FoundryKPIService


class TestKPIAlerts:
    """Verify alert rule evaluation against latency window."""

    def test_p95_breach_fires_alert(self):
        svc = FoundryKPIService(window_size=200)
        for _ in range(100):
            svc.record_latency(3000.0)

        alerts = svc.check_alerts()
        assert len(alerts) == 1
        assert alerts[0]["rule"] == "p95_latency_breach"
        assert alerts[0]["actual_ms"] > 2500
        assert alerts[0]["severity"] == "warning"
        assert alerts[0]["threshold_ms"] == 2500

    def test_below_threshold_no_alerts(self):
        svc = FoundryKPIService(window_size=200)
        for _ in range(100):
            svc.record_latency(500.0)

        alerts = svc.check_alerts()
        assert alerts == []

    def test_empty_window_no_alerts(self):
        svc = FoundryKPIService()
        alerts = svc.check_alerts()
        assert alerts == []

    def test_mixed_latencies_near_threshold(self):
        svc = FoundryKPIService(window_size=200)
        # 90 fast + 10 slow: p95 should land in the slow region
        for _ in range(90):
            svc.record_latency(100.0)
        for _ in range(10):
            svc.record_latency(3000.0)

        alerts = svc.check_alerts()
        # p95 should be 3000 (at 95th percentile, 10 of 100 are 3000)
        assert len(alerts) == 1
        assert alerts[0]["actual_ms"] > 2500

    def test_all_at_threshold_no_alert(self):
        """Exactly at threshold should not fire (> not >=)."""
        svc = FoundryKPIService(window_size=200)
        for _ in range(100):
            svc.record_latency(2500.0)

        alerts = svc.check_alerts()
        assert alerts == []

    def test_just_above_threshold_fires(self):
        svc = FoundryKPIService(window_size=200)
        for _ in range(100):
            svc.record_latency(2501.0)

        alerts = svc.check_alerts()
        assert len(alerts) == 1
