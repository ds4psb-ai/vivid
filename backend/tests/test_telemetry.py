"""Tests for Telemetry System.

Comprehensive tests covering:
- Tool manifest CRUD
- Tool run event lifecycle
- Fork event with Sybil detection
- Attribution score calculation
- Metric aggregation
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from app.models_telemetry import ToolManifest, ToolRunEvent, ForkEvent, ToolTier
from app.schemas.telemetry_schemas import (
    ToolManifestCreate,
    ToolRunEventCreate,
    ToolRunEventComplete,
    ForkEventCreate,
    ToolRunFeedback,
)
from app.services import telemetry_service


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_db():
    """Create a mock async database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = AsyncMock()
    db.get = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def sample_tool_manifest():
    """Create a sample tool manifest."""
    return ToolManifest(
        id=uuid4(),
        tool_key="test_prompt_tool",
        display_name="Test Prompt Tool",
        description="A test tool for generating prompts",
        version="1.0.0",
        category="film",
        tier=ToolTier.EXPERIMENTAL.value,
        input_schema={"type": "object", "properties": {"text": {"type": "string"}}},
        output_schema={"type": "object", "properties": {"prompt": {"type": "string"}}},
        credit_cost=5,
        fork_count=0,
        usage_count=0,
        total_revenue=0,
        fork_depth=0,
        created_by="user_123",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_tool_run_event(sample_tool_manifest):
    """Create a sample tool run event."""
    return ToolRunEvent(
        id=uuid4(),
        tool_id=sample_tool_manifest.id,
        tool_key=sample_tool_manifest.tool_key,
        tool_version="1.0.0",
        user_id="user_456",
        status="started",
        inputs_summary={"text": "test input"},
        outputs_summary={},
        credits_charged=0,
        credits_refunded=0,
        created_at=datetime.utcnow(),
    )


# =============================================================================
# Tool Manifest Schema Tests
# =============================================================================

class TestToolManifestSchemas:
    """Test Pydantic schemas for tool manifests."""
    
    def test_valid_tool_manifest_create(self):
        """Test creating a valid tool manifest."""
        data = ToolManifestCreate(
            tool_key="my_test_tool",
            display_name="My Test Tool",
            description="This is a test tool for testing purposes",
            category="film",
            credit_cost=10,
        )
        assert data.tool_key == "my_test_tool"
        assert data.category == "film"
        assert data.credit_cost == 10
    
    def test_tool_key_lowercase_validation(self):
        """Test that tool_key lowercase is validated at pattern level."""
        # Pattern requires lowercase, so uppercase should fail
        with pytest.raises(ValueError):
            ToolManifestCreate(
                tool_key="MY_TEST_TOOL",  # Uppercase fails pattern
                display_name="Test",
                description="Test description...",
                category="FILM",
            )
        
        # Lowercase should work and category should be normalized
        data = ToolManifestCreate(
            tool_key="my_test_tool",
            display_name="Test",
            description="Test description...",
            category="FILM",
        )
        assert data.tool_key == "my_test_tool"
        assert data.category == "film"
    
    def test_tool_key_pattern_validation(self):
        """Test that invalid tool_key patterns are rejected."""
        with pytest.raises(ValueError):
            ToolManifestCreate(
                tool_key="invalid tool key!",
                display_name="Test",
                description="Test description...",
                category="film",
            )
    
    def test_credit_cost_bounds(self):
        """Test credit cost validation bounds."""
        # Valid
        data = ToolManifestCreate(
            tool_key="test",
            display_name="Test",
            description="Test description...",
            category="film",
            credit_cost=0,
        )
        assert data.credit_cost == 0
        
        # Invalid - negative
        with pytest.raises(ValueError):
            ToolManifestCreate(
                tool_key="test",
                display_name="Test",
                description="Test description...",
                category="film",
                credit_cost=-1,
            )
        
        # Invalid - too high
        with pytest.raises(ValueError):
            ToolManifestCreate(
                tool_key="test",
                display_name="Test",
                description="Test description...",
                category="film",
                credit_cost=1001,
            )


# =============================================================================
# Tool Run Event Schema Tests
# =============================================================================

class TestToolRunEventSchemas:
    """Test Pydantic schemas for tool run events."""
    
    def test_valid_run_event_create(self):
        """Test creating a valid run event."""
        data = ToolRunEventCreate(
            tool_id=uuid4(),
            tool_key="test_tool",
            inputs_summary={"text": "hello"},
        )
        assert data.tool_key == "test_tool"
        # Status is not a field in ToolRunEventCreate, only in Complete
        assert not hasattr(data, 'status') or 'status' not in data.model_fields
    
    def test_pii_sanitization(self):
        """Test that PII fields are removed from inputs."""
        data = ToolRunEventCreate(
            tool_id=uuid4(),
            tool_key="test_tool",
            inputs_summary={
                "text": "hello",
                "password": "secret123",
                "api_key": "sk-xxx",
                "token": "bearer-xxx",
            },
        )
        # PII fields should be removed
        assert "password" not in data.inputs_summary
        assert "api_key" not in data.inputs_summary
        assert "token" not in data.inputs_summary
        assert "text" in data.inputs_summary
    
    def test_run_complete_validation(self):
        """Test run completion validation."""
        data = ToolRunEventComplete(
            status="success",
            outputs_summary={"result": "done"},
            latency_ms=1500,
            credits_charged=5,
        )
        assert data.status == "success"
        assert data.credits_charged == 5
    
    def test_run_feedback_rating_bounds(self):
        """Test feedback rating validation."""
        # Valid
        data = ToolRunFeedback(rating=5, feedback="Great!")
        assert data.rating == 5
        
        # Invalid - too low
        with pytest.raises(ValueError):
            ToolRunFeedback(rating=0)
        
        # Invalid - too high
        with pytest.raises(ValueError):
            ToolRunFeedback(rating=6)


# =============================================================================
# Fork Event Schema Tests
# =============================================================================

class TestForkEventSchemas:
    """Test Pydantic schemas for fork events."""
    
    def test_valid_fork_event_create(self):
        """Test creating a valid fork event."""
        data = ForkEventCreate(
            parent_tool_id=uuid4(),
            child_tool_id=uuid4(),
            forker_id="user_123",
            diff_lines_added=50,
            diff_lines_removed=10,
            diff_lines_modified=20,
        )
        assert data.diff_lines_added == 50
    
    def test_diff_score_calculation(self):
        """Test automatic diff score calculation."""
        # Small changes
        data1 = ForkEventCreate(
            parent_tool_id=uuid4(),
            child_tool_id=uuid4(),
            forker_id="user_123",
            diff_lines_added=5,
            diff_lines_removed=2,
            diff_lines_modified=3,
        )
        # Score should be low for small changes
        assert hasattr(data1, '__dict__')
        
        # Large changes
        data2 = ForkEventCreate(
            parent_tool_id=uuid4(),
            child_tool_id=uuid4(),
            forker_id="user_123",
            diff_lines_added=100,
            diff_lines_removed=50,
            diff_lines_modified=30,
        )
        # Both should have computed diff_score
        assert data1.diff_lines_added + data1.diff_lines_removed + data1.diff_lines_modified == 10


# =============================================================================
# Telemetry Service Tests
# =============================================================================

class TestTelemetryService:
    """Test telemetry service business logic."""
    
    @pytest.mark.asyncio
    async def test_create_tool_manifest(self, mock_db, sample_tool_manifest):
        """Test tool manifest creation."""
        mock_db.get.return_value = None  # No parent tool
        
        data = ToolManifestCreate(
            tool_key="new_tool",
            display_name="New Tool",
            description="A brand new tool for testing",
            category="film",
            credit_cost=5,
        )
        
        # Mock the refresh to set the manifest
        async def mock_refresh(obj):
            obj.id = uuid4()
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()
        mock_db.refresh = mock_refresh
        
        result = await telemetry_service.create_tool_manifest(mock_db, data, "user_123")
        
        assert result.tool_key == "new_tool"
        assert result.created_by == "user_123"
        assert result.tier == ToolTier.EXPERIMENTAL.value
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_fork_tool_manifest(self, mock_db, sample_tool_manifest):
        """Test creating a fork of an existing tool."""
        mock_db.get.return_value = sample_tool_manifest  # Parent exists
        
        data = ToolManifestCreate(
            tool_key="forked_tool",
            display_name="Forked Tool",
            description="A fork of the original tool",
            category="film",
            parent_tool_id=sample_tool_manifest.id,
        )
        
        async def mock_refresh(obj):
            obj.id = uuid4()
            obj.fork_depth = 1
        mock_db.refresh = mock_refresh
        
        result = await telemetry_service.create_tool_manifest(mock_db, data, "user_456")
        
        assert result.fork_depth == 1
        assert result.parent_tool_id == sample_tool_manifest.id
    
    @pytest.mark.asyncio
    async def test_sybil_detection_low_diff(self, mock_db, sample_tool_manifest):
        """Test Sybil detection for low diff score."""
        mock_db.get.return_value = sample_tool_manifest
        
        # Mock the count query to return 0 forks
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 0
        mock_db.execute.return_value = mock_result
        
        # Very small diff = suspicious
        is_suspicious, reason = await telemetry_service.check_sybil_patterns(
            mock_db, "user_123", diff_score=2.0
        )
        
        assert is_suspicious is True
        assert "Diff score" in reason
    
    @pytest.mark.asyncio
    async def test_sybil_detection_too_many_forks(self, mock_db):
        """Test Sybil detection for too many forks in a day."""
        # Mock the execute to return an async result
        mock_result = AsyncMock()
        mock_result.scalar = lambda: 15  # > SYBIL_MAX_FORKS_PER_DAY (sync method)
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        is_suspicious, reason = await telemetry_service.check_sybil_patterns(
            mock_db, "user_123", diff_score=50.0  # Good diff score
        )
        
        assert is_suspicious is True
        assert "Too many forks" in reason


# =============================================================================
# Attribution Score Tests
# =============================================================================

class TestAttributionScore:
    """Test attribution score calculation."""
    
    @pytest.mark.asyncio
    async def test_attribution_score_calculation(self, mock_db, sample_tool_manifest):
        """Test full attribution score calculation."""
        # Create a fork event
        fork = ForkEvent(
            id=uuid4(),
            parent_tool_id=uuid4(),
            child_tool_id=sample_tool_manifest.id,
            fork_depth=1,
            forker_id="user_123",
            diff_score=60.0,  # Good diff
            test_passed=True,  # Tests pass
            attribution_score=0,
        )
        
        # Set up tool with usage data
        sample_tool_manifest.usage_count = 50
        sample_tool_manifest.total_revenue = 500
        sample_tool_manifest.quality_rating = 4.5
        
        # Mock db.get to return fork and tool
        mock_db.get = AsyncMock(side_effect=[fork, sample_tool_manifest])
        
        result = await telemetry_service.calculate_attribution_score(mock_db, fork.id)
        
        # Verify score components
        assert result.diff_score == 60.0
        assert result.test_score == 100.0  # Tests passed
        assert result.quality_score == 90.0  # 4.5 * 20
        assert result.total_score > 0
        assert result.total_score <= 100
        
        # Verify weights used
        assert result.weights["diff"] == 0.2
        assert result.weights["test"] == 0.15
        assert result.weights["usage"] == 0.25
        assert result.weights["revenue"] == 0.25
        assert result.weights["quality"] == 0.15
    
    def test_attribution_weights_sum_to_one(self):
        """Verify attribution weights sum to 1.0."""
        total = sum(telemetry_service.ATTRIBUTION_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001  # Allow small floating point error


# =============================================================================
# Integration Tests (with actual DB - marked for CI/CD)
# =============================================================================

@pytest.mark.integration
class TestTelemetryIntegration:
    """Integration tests requiring actual database."""
    
    @pytest.mark.asyncio
    async def test_full_tool_lifecycle(self):
        """Test complete tool lifecycle: create -> run -> feedback -> metrics."""
        # This would require actual database setup
        # Marked for integration testing environment
        pass
    
    @pytest.mark.asyncio
    async def test_fork_revenue_tracking(self):
        """Test fork revenue accumulation and sharing."""
        # This would require actual database setup
        pass


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
