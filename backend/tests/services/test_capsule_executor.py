"""Tests for Capsule Executor Pipeline.

P5 Commit 2: Tests for adapter selection, input validation, output normalization
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Skip all tests if dependencies unavailable
try:
    from app.services.capsule_executor import (
        CapsuleExecutionResult,
        _validate_inputs,
        _get_adapter_type,
        _normalize_output,
        execute_capsule,
    )
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    CapsuleExecutionResult = None
    _validate_inputs = None
    _get_adapter_type = None
    _normalize_output = None
    execute_capsule = None


pytestmark = pytest.mark.skipif(
    not DEPS_AVAILABLE,
    reason=f"Dependencies not available: {IMPORT_ERROR if not DEPS_AVAILABLE else ''}"
)


class TestGetAdapterType:
    """Tests for _get_adapter_type function."""
    
    def test_teaching_capsule(self):
        """teaching.* -> dimension adapter."""
        assert _get_adapter_type("teaching.prompt.generate") == "dimension"
    
    def test_dimension_capsule(self):
        """dimension.* -> dimension adapter."""
        assert _get_adapter_type("dimension.aesthetic.direct") == "dimension"
    
    def test_veo_capsule(self):
        """veo.* -> dimension adapter."""
        assert _get_adapter_type("veo.video.generate") == "dimension"
    
    def test_auteur_capsule(self):
        """auteur.* -> notebooklm adapter."""
        assert _get_adapter_type("auteur.bong-joon-ho") == "notebooklm"
    
    def test_production_capsule(self):
        """production.* -> notebooklm adapter."""
        assert _get_adapter_type("production.stage-rehearsal") == "notebooklm"
    
    def test_unknown_capsule(self):
        """Unknown prefix -> dimension adapter (default)."""
        assert _get_adapter_type("unknown.capsule") == "dimension"


class TestValidateInputs:
    """Tests for _validate_inputs function."""
    
    def test_required_input_present(self):
        """Should pass when required input is present."""
        spec = {"inputs": {"topic": {"required": True}}}
        inputs = {"topic": "test topic"}
        
        result = _validate_inputs(inputs, spec)
        assert result["topic"] == "test topic"
    
    def test_required_input_missing(self):
        """Should raise when required input is missing."""
        spec = {"inputs": {"topic": {"required": True}}}
        inputs = {}
        
        with pytest.raises(ValueError, match="Missing required input: topic"):
            _validate_inputs(inputs, spec)
    
    def test_default_applied(self):
        """Should apply default when input not provided."""
        spec = {"inputs": {"language": {"required": False, "default": "ko"}}}
        inputs = {}
        
        result = _validate_inputs(inputs, spec)
        assert result["language"] == "ko"
    
    def test_user_input_overrides_default(self):
        """User input should override default."""
        spec = {"inputs": {"language": {"required": False, "default": "ko"}}}
        inputs = {"language": "en"}
        
        result = _validate_inputs(inputs, spec)
        assert result["language"] == "en"
    
    def test_empty_spec(self):
        """Should pass through inputs when spec is empty."""
        spec = {}
        inputs = {"key": "value"}
        
        result = _validate_inputs(inputs, spec)
        assert result["key"] == "value"


class TestNormalizeOutput:
    """Tests for _normalize_output function."""
    
    def test_extracts_common_summary_fields(self):
        """Should extract known summary fields."""
        raw = {
            "output": {
                "prompt": "generated prompt",
                "internal_field": "hidden",
            },
            "metrics": {"tokens": 100},
        }
        
        result = _normalize_output(raw, "teaching.prompt.generate")
        
        assert result["summary"]["prompt"] == "generated prompt"
        assert "internal_field" not in result["summary"] or result["summary"] == raw["output"]
    
    def test_extracts_token_usage(self):
        """Should extract token usage from metrics."""
        raw = {
            "output": {},
            "metrics": {"input_tokens": 50, "output_tokens": 100, "tokens": 150},
        }
        
        result = _normalize_output(raw, "test")
        
        assert result["token_usage"]["input"] == 50
        assert result["token_usage"]["output"] == 100
        assert result["token_usage"]["total"] == 150
    
    def test_extracts_evidence_refs(self):
        """Should extract sources as evidence_refs."""
        raw = {
            "output": {
                "sources": ["source1", "source2"],
            },
        }
        
        result = _normalize_output(raw, "test")
        
        assert len(result["evidence_refs"]) == 2


class TestCapsuleExecutionResult:
    """Tests for CapsuleExecutionResult dataclass."""
    
    def test_to_dict(self):
        """Should convert to dict correctly."""
        result = CapsuleExecutionResult(
            run_id="test-run-123",
            status="done",
            summary={"answer": "test"},
            version="1.0.0",
            latency_ms=500,
        )
        
        d = result.to_dict()
        
        assert d["run_id"] == "test-run-123"
        assert d["status"] == "done"
        assert d["version"] == "1.0.0"
        assert d["latency_ms"] == 500


@pytest.mark.asyncio
class TestExecuteCapsule:
    """Integration tests for execute_capsule function."""
    
    async def test_unknown_capsule_returns_error(self):
        """Should return error for unknown capsule."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        user = {"id": "test-user"}

        # Patch get_spec in capsule_specs module (where it's imported from)
        with patch("app.services.capsule_specs.get_spec", new_callable=AsyncMock, return_value=None):
            result = await execute_capsule(
                capsule_id="nonexistent.capsule",
                inputs={},
                params={},
                user=user,
                db=mock_db,
            )

        assert result.status == "failed"
        assert "not found" in result.error.lower()
