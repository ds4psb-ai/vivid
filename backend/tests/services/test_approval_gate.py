"""Tests for Approval Gate Service (Phase 7 HITL Enhancement).

Tests for confidence-based auto/manual approval routing.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

# Skip all tests if dependencies unavailable
try:
    from app.services.approval_gate import ApprovalGateService
    from app.schemas.approval_gate_schemas import (
        ApprovalDecision,
        ApprovalGateConfig,
        CheckpointAction,
    )
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    ApprovalGateService = None
    ApprovalDecision = None
    ApprovalGateConfig = None
    CheckpointAction = None


pytestmark = pytest.mark.skipif(
    not DEPS_AVAILABLE,
    reason=f"Dependencies not available: {IMPORT_ERROR if not DEPS_AVAILABLE else ''}"
)


class TestApprovalGateConfig:
    """Tests for ApprovalGateConfig defaults."""

    def test_default_thresholds(self):
        """Default thresholds should match spec."""
        config = ApprovalGateConfig()
        assert config.auto_approve_threshold == 0.85
        assert config.escalate_threshold == 0.50
        assert config.timeout_seconds == 3600

    def test_custom_thresholds(self):
        """Should accept custom threshold values."""
        config = ApprovalGateConfig(
            auto_approve_threshold=0.90,
            escalate_threshold=0.40,
            timeout_seconds=7200,
        )
        assert config.auto_approve_threshold == 0.90
        assert config.escalate_threshold == 0.40
        assert config.timeout_seconds == 7200


class TestApprovalDecision:
    """Tests for ApprovalDecision enum values."""

    def test_auto_approved_value(self):
        """AUTO_APPROVED should have correct string value."""
        assert ApprovalDecision.AUTO_APPROVED == "auto_approved"

    def test_pending_review_value(self):
        """PENDING_REVIEW should have correct string value."""
        assert ApprovalDecision.PENDING_REVIEW == "pending_review"

    def test_escalated_value(self):
        """ESCALATED should have correct string value."""
        assert ApprovalDecision.ESCALATED == "escalated"


class TestApprovalGateService:
    """Tests for ApprovalGateService."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create an ApprovalGateService instance."""
        return ApprovalGateService(mock_db)

    @pytest.mark.asyncio
    async def test_evaluate_auto_approve_high_confidence(self, service, mock_db):
        """High confidence (>= 0.85) should auto-approve."""
        execution_id = uuid4()
        node_id = "test_node"
        output = {"result": "test output"}
        confidence = 0.90

        result = await service.evaluate_for_approval(
            execution_id=execution_id,
            node_id=node_id,
            output=output,
            confidence=confidence,
        )

        assert result.decision == ApprovalDecision.AUTO_APPROVED
        assert result.confidence == confidence

    @pytest.mark.asyncio
    async def test_evaluate_escalate_low_confidence(self, service, mock_db):
        """Low confidence (< 0.50) should escalate."""
        execution_id = uuid4()
        node_id = "test_node"
        output = {"result": "test output"}
        confidence = 0.30

        result = await service.evaluate_for_approval(
            execution_id=execution_id,
            node_id=node_id,
            output=output,
            confidence=confidence,
        )

        assert result.decision == ApprovalDecision.ESCALATED
        assert result.confidence == confidence

    @pytest.mark.asyncio
    async def test_evaluate_pending_review_mid_confidence(self, service, mock_db):
        """Medium confidence (0.50 - 0.85) should require review."""
        execution_id = uuid4()
        node_id = "test_node"
        output = {"result": "test output"}
        confidence = 0.65

        result = await service.evaluate_for_approval(
            execution_id=execution_id,
            node_id=node_id,
            output=output,
            confidence=confidence,
        )

        assert result.decision == ApprovalDecision.PENDING_REVIEW
        assert result.confidence == confidence

    @pytest.mark.asyncio
    async def test_dimension_config_override(self, service, mock_db):
        """Dimension-specific config should override defaults."""
        execution_id = uuid4()
        node_id = "test_node"
        output = {"result": "test output"}
        # With default config this would be PENDING_REVIEW
        confidence = 0.80

        # Override dimension config to auto-approve at 0.75
        service.dimension_configs["test_dimension"] = ApprovalGateConfig(
            auto_approve_threshold=0.75
        )

        result = await service.evaluate_for_approval(
            execution_id=execution_id,
            node_id=node_id,
            output=output,
            confidence=confidence,
            dimension="test_dimension",
        )

        assert result.decision == ApprovalDecision.AUTO_APPROVED

    @pytest.mark.asyncio
    async def test_get_pending_approvals_empty(self, service, mock_db):
        """Should return empty list when no pending approvals."""
        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )

        items, total = await service.get_pending_approvals(limit=10)

        assert items == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_boundary_threshold_auto_approve(self, service, mock_db):
        """Confidence exactly at auto_approve_threshold should auto-approve."""
        execution_id = uuid4()
        confidence = 0.85  # Exactly at threshold

        result = await service.evaluate_for_approval(
            execution_id=execution_id,
            node_id="node",
            output={},
            confidence=confidence,
        )

        assert result.decision == ApprovalDecision.AUTO_APPROVED

    @pytest.mark.asyncio
    async def test_boundary_threshold_escalate(self, service, mock_db):
        """Confidence exactly at escalate_threshold should be PENDING_REVIEW."""
        execution_id = uuid4()
        confidence = 0.50  # Exactly at threshold

        result = await service.evaluate_for_approval(
            execution_id=execution_id,
            node_id="node",
            output={},
            confidence=confidence,
        )

        assert result.decision == ApprovalDecision.PENDING_REVIEW

    @pytest.mark.asyncio
    async def test_just_below_escalate_threshold(self, service, mock_db):
        """Confidence just below escalate_threshold should escalate."""
        execution_id = uuid4()
        confidence = 0.49

        result = await service.evaluate_for_approval(
            execution_id=execution_id,
            node_id="node",
            output={},
            confidence=confidence,
        )

        assert result.decision == ApprovalDecision.ESCALATED


class TestCheckpointAction:
    """Tests for CheckpointAction enum."""

    def test_approve_continue_value(self):
        """APPROVE_CONTINUE should have correct string value."""
        assert CheckpointAction.APPROVE_CONTINUE == "approve_continue"

    def test_reject_value(self):
        """REJECT should have correct string value."""
        assert CheckpointAction.REJECT == "reject"

    def test_request_revision_value(self):
        """REQUEST_REVISION should have correct string value."""
        assert CheckpointAction.REQUEST_REVISION == "request_revision"
