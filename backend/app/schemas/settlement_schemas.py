"""Settlement Pydantic Schemas.

Request/response models for settlement API endpoints.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Payout Schemas
# =============================================================================

class PayoutBase(BaseModel):
    """Base payout schema for responses."""
    id: UUID
    settlement_id: UUID
    recipient_id: str
    recipient_tool_key: Optional[str] = None
    amount: int
    share_type: str
    share_rate: float
    lineage_position: int
    status: str
    credited_at: Optional[datetime] = None


class PayoutResponse(PayoutBase):
    """Full payout response."""
    created_at: datetime
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Settlement Schemas
# =============================================================================

class SettlementBase(BaseModel):
    """Base settlement schema."""
    id: UUID
    tool_run_id: UUID
    tool_id: Optional[UUID] = None
    tool_key: str
    status: str
    total_credits: int
    platform_fee: int
    creator_pool: int


class SettlementResponse(SettlementBase):
    """Full settlement response."""
    lineage_depth: int
    attribution_score: Optional[float] = None
    payer_user_id: str
    created_at: datetime
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SettlementDetailResponse(SettlementResponse):
    """Settlement with payouts and disputes."""
    payouts: List[PayoutResponse] = []
    disputes: List["DisputeResponse"] = []


class SettlementPreview(BaseModel):
    """Preview of settlement before creation."""
    tool_id: UUID
    tool_key: str
    total_credits: int
    platform_fee: int
    creator_pool: int
    lineage_depth: int
    attribution_score: Optional[float] = None
    payouts: List[dict]


# =============================================================================
# Dispute Schemas
# =============================================================================

class DisputeCreate(BaseModel):
    """Create dispute request."""
    reason: str = Field(..., min_length=10, max_length=2000)
    expected_amount: Optional[int] = Field(None, ge=0)
    evidence: Optional[dict] = None


class DisputeResolve(BaseModel):
    """Resolve dispute request."""
    resolution: str = Field(..., min_length=10, max_length=2000)
    status: str = Field(..., pattern="^(resolved|rejected)$")
    adjustment_amount: Optional[int] = Field(None, ge=0)


class DisputeResponse(BaseModel):
    """Full dispute response."""
    id: UUID
    settlement_id: UUID
    complainant_id: str
    reason: str
    expected_amount: Optional[int] = None
    status: str
    resolution: Optional[str] = None
    adjustment_amount: Optional[int] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Summary Schemas
# =============================================================================

class UserSettlementSummary(BaseModel):
    """User's settlement summary."""
    period_days: int
    total_payouts: int
    total_earned: int
    avg_per_payout: float
    pending_amount: int


class AdminSettlementStats(BaseModel):
    """Admin settlement statistics."""
    pending_count: int
    processing_count: int
    completed_today: int
    total_settled_today: int
    open_disputes: int


# =============================================================================
# Batch Schemas
# =============================================================================

class BatchProcessRequest(BaseModel):
    """Batch settlement processing request."""
    limit: int = Field(100, ge=1, le=1000)


class BatchProcessResponse(BaseModel):
    """Batch processing result."""
    processed: int
    succeeded: int
    failed: int
    errors: List[dict] = []


# Update forward refs
SettlementDetailResponse.model_rebuild()
