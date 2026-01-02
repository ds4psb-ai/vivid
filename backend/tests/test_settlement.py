"""Settlement System Tests.

Comprehensive test suite for production-level revenue settlement:
- Settlement creation
- Processing (success/failure)
- Batch processing
- Rollback
- Disputes
- Edge cases
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models_settlement import (
    SettlementTransaction,
    SettlementPayout,
    SettlementDispute,
    SettlementStatus,
    PayoutStatus,
    ShareType,
    DisputeStatus,
)
from app.models_telemetry import ToolManifest, ToolRunEvent, ForkEvent, ToolTier
from app.services import fork_revenue_service


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_db():
    """Create mock async database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def original_tool():
    """Create a mock original tool (no parent)."""
    tool = MagicMock(spec=ToolManifest)
    tool.id = uuid4()
    tool.tool_key = "original_tool"
    tool.display_name = "Original Tool"
    tool.created_by = "creator_123"
    tool.parent_tool_id = None
    return tool


@pytest.fixture
def forked_tool(original_tool):
    """Create a mock forked tool."""
    tool = MagicMock(spec=ToolManifest)
    tool.id = uuid4()
    tool.tool_key = "forked_tool"
    tool.display_name = "Forked Tool"
    tool.created_by = "forker_456"
    tool.parent_tool_id = original_tool.id
    return tool


@pytest.fixture
def fork_event(original_tool, forked_tool):
    """Create a mock fork event."""
    fork = MagicMock(spec=ForkEvent)
    fork.id = uuid4()
    fork.parent_tool_id = original_tool.id
    fork.child_tool_id = forked_tool.id
    fork.attribution_score = 60.0  # Mid-range score
    fork.revenue_generated = 0
    fork.revenue_shared = 0
    return fork


# =============================================================================
# Unit Tests: Share Rate Calculation
# =============================================================================

class TestShareRateCalculation:
    """Tests for calculate_owner_share_rate function."""
    
    def test_original_tool_gets_100_percent(self):
        """Original tools (no attribution) get 100%."""
        rate = fork_revenue_service.calculate_owner_share_rate(None)
        assert rate == Decimal("1.0")
    
    def test_high_attribution_gets_75_percent(self):
        """High attribution (75+) gets 75%."""
        rate = fork_revenue_service.calculate_owner_share_rate(80.0)
        assert rate == Decimal("0.75")
    
    def test_medium_high_attribution_gets_50_percent(self):
        """Medium-high attribution (50-74) gets 50%."""
        rate = fork_revenue_service.calculate_owner_share_rate(60.0)
        assert rate == Decimal("0.50")
    
    def test_medium_low_attribution_gets_25_percent(self):
        """Medium-low attribution (25-49) gets 25%."""
        rate = fork_revenue_service.calculate_owner_share_rate(35.0)
        assert rate == Decimal("0.25")
    
    def test_low_attribution_gets_10_percent(self):
        """Low attribution (< 25) gets 10%."""
        rate = fork_revenue_service.calculate_owner_share_rate(15.0)
        assert rate == Decimal("0.10")
    
    def test_boundary_at_75(self):
        """Exactly 75 gets 75%."""
        rate = fork_revenue_service.calculate_owner_share_rate(75.0)
        assert rate == Decimal("0.75")
    
    def test_boundary_at_50(self):
        """Exactly 50 gets 50%."""
        rate = fork_revenue_service.calculate_owner_share_rate(50.0)
        assert rate == Decimal("0.50")
    
    def test_boundary_at_25(self):
        """Exactly 25 gets 25%."""
        rate = fork_revenue_service.calculate_owner_share_rate(25.0)
        assert rate == Decimal("0.25")


# =============================================================================
# Unit Tests: Payout Calculation
# =============================================================================

class TestPayoutCalculation:
    """Tests for calculate_payouts function."""
    
    def test_empty_lineage_returns_empty(self):
        """Empty lineage returns no payouts."""
        payouts = fork_revenue_service.calculate_payouts(1000, [])
        assert payouts == []
    
    def test_original_tool_gets_all(self, original_tool):
        """Original tool owner gets 100% of creator pool."""
        lineage = [(original_tool, None)]
        payouts = fork_revenue_service.calculate_payouts(1000, lineage)
        
        assert len(payouts) == 1
        assert payouts[0]["recipient_id"] == "creator_123"
        assert payouts[0]["amount"] == 1000
        assert payouts[0]["share_type"] == ShareType.OWNER.value
        assert payouts[0]["share_rate"] == 1.0
    
    def test_forked_tool_splits_revenue(self, original_tool, forked_tool, fork_event):
        """Forked tool splits between owner and ancestor."""
        lineage = [
            (original_tool, None),
            (forked_tool, fork_event),
        ]
        payouts = fork_revenue_service.calculate_payouts(1000, lineage)
        
        # Attribution score 60 = 50% to owner
        assert len(payouts) == 2
        
        owner_payout = next(p for p in payouts if p["share_type"] == ShareType.OWNER.value)
        ancestor_payout = next(p for p in payouts if p["share_type"] == ShareType.ANCESTOR.value)
        
        assert owner_payout["recipient_id"] == "forker_456"
        assert owner_payout["amount"] == 500  # 50% of 1000
        
        assert ancestor_payout["recipient_id"] == "creator_123"
        assert ancestor_payout["amount"] == 500  # Remainder
    
    def test_minimum_payout_threshold(self, original_tool):
        """Payouts below minimum are excluded."""
        # Create tool that would get 0 after split
        lineage = [(original_tool, None)]
        payouts = fork_revenue_service.calculate_payouts(0, lineage)
        
        # 0 credits = no payouts
        assert len(payouts) == 0
    
    def test_deep_fork_chain(self, original_tool):
        """Revenue splits correctly across deep fork chain."""
        # Create 3-level fork chain
        level1_tool = MagicMock(spec=ToolManifest)
        level1_tool.id = uuid4()
        level1_tool.tool_key = "level1"
        level1_tool.created_by = "level1_user"
        level1_tool.parent_tool_id = original_tool.id
        
        level1_fork = MagicMock(spec=ForkEvent)
        level1_fork.attribution_score = 50.0
        
        level2_tool = MagicMock(spec=ToolManifest)
        level2_tool.id = uuid4()
        level2_tool.tool_key = "level2"
        level2_tool.created_by = "level2_user"
        level2_tool.parent_tool_id = level1_tool.id
        
        level2_fork = MagicMock(spec=ForkEvent)
        level2_fork.attribution_score = 30.0  # 25% share
        
        lineage = [
            (original_tool, None),
            (level1_tool, level1_fork),
            (level2_tool, level2_fork),
        ]
        
        payouts = fork_revenue_service.calculate_payouts(1000, lineage)
        
        # Owner (level2_user) gets 25% = 250
        # Ancestors split 750 = 375 each
        assert len(payouts) == 3
        
        owner = next(p for p in payouts if p["share_type"] == ShareType.OWNER.value)
        assert owner["amount"] == 250
        
        total = sum(p["amount"] for p in payouts)
        assert total == 1000  # All credits distributed


# =============================================================================
# Integration Tests: Settlement Creation
# =============================================================================

class TestSettlementCreation:
    """Tests for create_settlement function."""
    
    @pytest.mark.asyncio
    async def test_creates_pending_settlement(self, mock_db, original_tool):
        """Settlement is created with PENDING status."""
        # Setup mocks
        mock_db.get = AsyncMock(return_value=original_tool)
        mock_db.execute = AsyncMock(return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
        ))
        
        with patch.object(fork_revenue_service, 'get_tool_lineage', return_value=[(original_tool, None)]):
            settlement = await fork_revenue_service.create_settlement(
                db=mock_db,
                tool_run_id=uuid4(),
                tool_id=original_tool.id,
                tool_key=original_tool.tool_key,
                total_credits=100,
                payer_user_id="payer_123",
            )
        
        assert settlement.status == SettlementStatus.PENDING.value
        assert settlement.total_credits == 100
        assert settlement.platform_fee == 30  # 30%
        assert settlement.creator_pool == 70
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_creates_payout_records(self, mock_db, original_tool):
        """Settlement creates corresponding payout records."""
        mock_db.get = AsyncMock(return_value=original_tool)
        
        added_items = []
        mock_db.add = lambda x: added_items.append(x)
        
        with patch.object(fork_revenue_service, 'get_tool_lineage', return_value=[(original_tool, None)]):
            settlement = await fork_revenue_service.create_settlement(
                db=mock_db,
                tool_run_id=uuid4(),
                tool_id=original_tool.id,
                tool_key=original_tool.tool_key,
                total_credits=100,
                payer_user_id="payer_123",
            )
        
        # Should add settlement + 1 payout
        payouts = [x for x in added_items if isinstance(x, SettlementPayout)]
        assert len(payouts) == 1
        assert payouts[0].amount == 70
        assert payouts[0].status == PayoutStatus.PENDING.value


# =============================================================================
# Integration Tests: Settlement Processing
# =============================================================================

class TestSettlementProcessing:
    """Tests for process_settlement function."""
    
    @pytest.mark.asyncio
    async def test_successful_processing(self, mock_db, original_tool):
        """Successful processing credits users and updates status."""
        settlement = SettlementTransaction(
            id=uuid4(),
            tool_run_id=uuid4(),
            tool_id=original_tool.id,
            tool_key="test_tool",
            status=SettlementStatus.PENDING.value,
            total_credits=100,
            platform_fee=30,
            creator_pool=70,
            payer_user_id="payer",
            created_at=datetime.utcnow(),
        )
        
        payout = SettlementPayout(
            id=uuid4(),
            settlement_id=settlement.id,
            recipient_id="creator",
            amount=70,
            share_type=ShareType.OWNER.value,
            share_rate=1.0,
            lineage_position=0,
            status=PayoutStatus.PENDING.value,
            created_at=datetime.utcnow(),
        )
        settlement.payouts = [payout]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = settlement
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        mock_user_credits = MagicMock()
        mock_user_credits.topup_credits = 0
        mock_user_credits.balance = 0
        
        with patch('app.services.fork_revenue_service.get_or_create_user_credits', 
                   AsyncMock(return_value=mock_user_credits)):
            with patch('app.services.fork_revenue_service.record_transaction',
                      AsyncMock(return_value=MagicMock(id=uuid4()))):
                success, error = await fork_revenue_service.process_settlement(
                    mock_db, settlement.id
                )
        
        assert success is True
        assert error is None
        assert settlement.status == SettlementStatus.COMPLETED.value
        assert payout.status == PayoutStatus.CREDITED.value


# =============================================================================
# Integration Tests: Rollback
# =============================================================================

class TestSettlementRollback:
    """Tests for rollback_settlement function."""
    
    @pytest.mark.asyncio
    async def test_rollback_reverses_payouts(self, mock_db):
        """Rollback reverses all credited payouts."""
        settlement = SettlementTransaction(
            id=uuid4(),
            tool_run_id=uuid4(),
            tool_id=uuid4(),
            tool_key="test_tool",
            status=SettlementStatus.COMPLETED.value,
            total_credits=100,
            platform_fee=30,
            creator_pool=70,
            payer_user_id="payer",
            created_at=datetime.utcnow(),
            meta={},
        )
        
        payout = SettlementPayout(
            id=uuid4(),
            settlement_id=settlement.id,
            recipient_id="creator",
            amount=70,
            share_type=ShareType.OWNER.value,
            share_rate=1.0,
            lineage_position=0,
            status=PayoutStatus.CREDITED.value,
            created_at=datetime.utcnow(),
        )
        settlement.payouts = [payout]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = settlement
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        mock_user_credits = MagicMock()
        mock_user_credits.topup_credits = 70
        mock_user_credits.balance = 70
        
        with patch('app.services.fork_revenue_service.get_or_create_user_credits',
                   AsyncMock(return_value=mock_user_credits)):
            with patch('app.services.fork_revenue_service.record_transaction',
                      AsyncMock(return_value=MagicMock())):
                success, error = await fork_revenue_service.rollback_settlement(
                    mock_db, settlement.id, "Test reason", "admin_123"
                )
        
        assert success is True
        assert settlement.status == SettlementStatus.REVERSED.value
        assert payout.status == PayoutStatus.REVERSED.value


# =============================================================================
# Integration Tests: Disputes
# =============================================================================

class TestDisputes:
    """Tests for dispute management."""
    
    @pytest.mark.asyncio
    async def test_create_dispute(self, mock_db):
        """Creating dispute updates settlement status."""
        settlement = MagicMock(spec=SettlementTransaction)
        settlement.id = uuid4()
        settlement.status = SettlementStatus.COMPLETED.value
        
        mock_db.get = AsyncMock(return_value=settlement)
        
        dispute = await fork_revenue_service.create_dispute(
            db=mock_db,
            settlement_id=settlement.id,
            complainant_id="user_123",
            reason="I should have received more credits",
            expected_amount=100,
        )
        
        assert dispute is not None
        assert dispute.status == DisputeStatus.OPEN.value
        assert settlement.status == SettlementStatus.DISPUTED.value
        mock_db.add.assert_called()
    
    @pytest.mark.asyncio
    async def test_dispute_not_found_raises(self, mock_db):
        """Creating dispute for non-existent settlement raises."""
        mock_db.get = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="Settlement not found"):
            await fork_revenue_service.create_dispute(
                db=mock_db,
                settlement_id=uuid4(),
                complainant_id="user_123",
                reason="Test reason",
            )
    
    @pytest.mark.asyncio
    async def test_resolve_dispute(self, mock_db):
        """Resolving dispute updates status."""
        dispute = MagicMock(spec=SettlementDispute)
        dispute.id = uuid4()
        dispute.settlement_id = uuid4()
        dispute.status = DisputeStatus.OPEN.value
        
        settlement = MagicMock(spec=SettlementTransaction)
        settlement.status = SettlementStatus.DISPUTED.value
        
        mock_db.get = AsyncMock(side_effect=[dispute, settlement])
        mock_db.execute = AsyncMock(return_value=MagicMock(
            scalar=MagicMock(return_value=0)  # No other open disputes
        ))
        
        resolved = await fork_revenue_service.resolve_dispute(
            db=mock_db,
            dispute_id=dispute.id,
            resolution="Investigation complete, amount is correct",
            status=DisputeStatus.REJECTED,
            adjustment_amount=None,
            resolved_by="admin_123",
        )
        
        assert resolved.status == DisputeStatus.REJECTED.value
        assert resolved.resolved_by == "admin_123"


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_platform_fee_rounding(self):
        """Platform fee rounds correctly for odd amounts."""
        # 30% of 33 = 9.9, should round to 10
        from decimal import Decimal, ROUND_HALF_UP
        
        total = Decimal(33)
        fee = (total * fork_revenue_service.PLATFORM_FEE_RATE).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        assert fee == Decimal("10")
    
    def test_zero_credits_settlement(self, original_tool):
        """Zero credit settlement returns no payouts."""
        lineage = [(original_tool, None)]
        payouts = fork_revenue_service.calculate_payouts(0, lineage)
        assert payouts == []
    
    @pytest.mark.asyncio
    async def test_invalid_status_for_processing(self, mock_db):
        """Cannot process non-pending settlement."""
        settlement = MagicMock(spec=SettlementTransaction)
        settlement.status = SettlementStatus.COMPLETED.value
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = settlement
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        success, error = await fork_revenue_service.process_settlement(
            mock_db, uuid4()
        )
        
        assert success is False
        assert "Invalid status" in error
    
    @pytest.mark.asyncio
    async def test_settlement_not_found(self, mock_db):
        """Processing non-existent settlement fails gracefully."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        success, error = await fork_revenue_service.process_settlement(
            mock_db, uuid4()
        )
        
        assert success is False
        assert "not found" in error


# =============================================================================
# Batch Processing
# =============================================================================

class TestBatchProcessing:
    """Tests for batch settlement processing."""
    
    @pytest.mark.asyncio
    async def test_batch_processes_pending(self, mock_db):
        """Batch processing handles multiple settlements."""
        settlement1 = MagicMock(spec=SettlementTransaction)
        settlement1.id = uuid4()
        settlement1.status = SettlementStatus.PENDING.value
        settlement1.retry_count = 0
        
        settlement2 = MagicMock(spec=SettlementTransaction)
        settlement2.id = uuid4()
        settlement2.status = SettlementStatus.PENDING.value
        settlement2.retry_count = 0
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [settlement1, settlement2]
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        with patch.object(fork_revenue_service, 'process_settlement', 
                         AsyncMock(return_value=(True, None))):
            result = await fork_revenue_service.process_batch_settlements(
                mock_db, limit=10
            )
        
        assert result["processed"] == 2
        assert result["succeeded"] == 2
        assert result["failed"] == 0
