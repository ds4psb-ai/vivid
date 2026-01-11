"""
P3 Commit 4: QC Multi-Mode Tests

Tests for multi-mode quality checker functionality:
- Single mode backward compat
- Multi-mode with modes/overall
- Invalid mode handling
- Threshold normalization
- Partial failure handling
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# Test helpers
from app.dimension_adapter import (
    _normalize_modes,
    _normalize_threshold_qc,
    _get_mode_config,
    _dedupe_list,
    _aggregate_metrics,
    VALID_INSPECTION_MODES,
    DEFAULT_CRITERIA,
    MODE_CONFIGS,
    CapsuleMetrics,
)


class TestModeNormalization:
    """Test _normalize_modes helper."""
    
    def test_single_mode_valid(self):
        """Valid single mode returns list."""
        result = _normalize_modes({"inspection_mode": "cinematic"})
        assert result == ["cinematic"]
    
    def test_single_mode_invalid(self):
        """Invalid single mode returns empty (triggers engine error)."""
        result = _normalize_modes({"inspection_mode": "invalid_mode"})
        assert result == []
    
    def test_multi_mode_mixed(self):
        """Multi-mode filters invalid, keeps valid."""
        result = _normalize_modes({"inspection_modes": ["cinematic", "invalid", "quick"]})
        assert result == ["cinematic", "quick"]
    
    def test_multi_mode_all_invalid(self):
        """All invalid modes returns empty."""
        result = _normalize_modes({"inspection_modes": ["bad1", "bad2"]})
        assert result == []
    
    def test_multi_mode_dedupe(self):
        """Duplicate modes are removed."""
        result = _normalize_modes({"inspection_modes": ["cinematic", "cinematic", "quick"]})
        assert result == ["cinematic", "quick"]
    
    def test_fallback_to_inspection_mode(self):
        """If inspection_modes is None, use inspection_mode field."""
        result = _normalize_modes({"inspection_mode": "comprehensive"})
        assert result == ["comprehensive"]
    
    def test_default_comprehensive(self):
        """Empty input defaults to ['comprehensive'] via inspection_mode default."""
        result = _normalize_modes({})
        # inspection_mode defaults to "comprehensive" in router
        assert result == ["comprehensive"]


class TestThresholdNormalization:
    """Test _normalize_threshold_qc helper."""
    
    def test_float_0_1_scale(self):
        """0.7 → 70."""
        result = _normalize_threshold_qc({"threshold": 0.7})
        assert result == 70
    
    def test_int_0_100_scale(self):
        """70 stays 70."""
        result = _normalize_threshold_qc({"threshold": 70})
        assert result == 70
    
    def test_float_boundary(self):
        """1.0 → 100."""
        result = _normalize_threshold_qc({"threshold": 1.0})
        assert result == 100
    
    def test_invalid_returns_default(self):
        """Invalid value returns 70."""
        result = _normalize_threshold_qc({"threshold": "invalid"})
        assert result == 70
    
    def test_clamp_high(self):
        """Values > 100 clamped to 100."""
        result = _normalize_threshold_qc({"threshold": 150})
        assert result == 100
    
    def test_clamp_low(self):
        """Values < 0 clamped to 0."""
        result = _normalize_threshold_qc({"threshold": -10})
        assert result == 0


class TestModeConfig:
    """Test _get_mode_config helper."""
    
    def test_comprehensive_uses_base_criteria(self):
        """Comprehensive mode uses passed base_criteria."""
        criteria, instruction = _get_mode_config("comprehensive", ["a", "b", "c"])
        assert criteria == ["a", "b", "c"]
        assert instruction == ""
    
    def test_cinematic_overrides_criteria(self):
        """Cinematic mode has fixed criteria."""
        criteria, instruction = _get_mode_config("cinematic", ["a", "b"])
        assert criteria == ["aesthetic", "narrative", "technical"]
        assert "cinematic" in instruction.lower()
    
    def test_quick_limits_criteria(self):
        """Quick mode takes first 2 of base_criteria."""
        criteria, instruction = _get_mode_config("quick", ["a", "b", "c", "d"])
        assert criteria == ["a", "b"]
    
    def test_consistency_overrides_criteria(self):
        """Consistency mode has fixed criteria."""
        criteria, instruction = _get_mode_config("consistency", ["a", "b"])
        assert criteria == ["consistency", "technical"]


class TestDedupeList:
    """Test _dedupe_list helper."""
    
    def test_removes_duplicates(self):
        """Duplicates removed, order preserved."""
        result = _dedupe_list(["a", "b", "a", "c", "b"])
        assert result == ["a", "b", "c"]
    
    def test_empty_list(self):
        """Empty list returns empty."""
        result = _dedupe_list([])
        assert result == []


class TestAggregateMetrics:
    """Test _aggregate_metrics helper."""
    
    def test_sum_tokens_and_latency(self):
        """Aggregates tokens and latency correctly."""
        m1 = CapsuleMetrics(latency_ms=100, input_tokens=50, output_tokens=50, model="gemini-3")
        m2 = CapsuleMetrics(latency_ms=200, input_tokens=60, output_tokens=40, model="gemini-3")
        
        result = _aggregate_metrics({"mode1": m1, "mode2": m2})
        
        assert result["latency_ms"] == 300  # Sum (sequential)
        assert result["tokens"] == 200  # 100 + 100
        assert result["model"] == "gemini-3"
    
    def test_handles_none_metrics(self):
        """None metrics are skipped."""
        m1 = CapsuleMetrics(latency_ms=100, input_tokens=50, output_tokens=50, model="gemini-3")
        
        result = _aggregate_metrics({"mode1": m1, "mode2": None})
        
        assert result["latency_ms"] == 100
        assert result["tokens"] == 100


class TestConstants:
    """Test P3 constants."""
    
    def test_valid_modes(self):
        """All 4 modes are defined."""
        assert VALID_INSPECTION_MODES == {"comprehensive", "quick", "cinematic", "consistency"}
    
    def test_default_criteria_matches_engine(self):
        """DEFAULT_CRITERIA matches engine expectation."""
        assert DEFAULT_CRITERIA == ["aesthetic", "consistency", "safety"]
    
    def test_mode_configs_complete(self):
        """All valid modes have configs."""
        for mode in VALID_INSPECTION_MODES:
            assert mode in MODE_CONFIGS
