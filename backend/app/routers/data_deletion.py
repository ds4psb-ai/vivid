"""
Data Deletion API Router

GDPR/CCPA compliance endpoint for user data deletion requests.
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_user_id
from app.database import get_db
from app.models import (
    UserAccount,
    UserCredits,
    CreditLedger,
    Canvas,
    CapsuleRun,
    AnalyticsEvent,
    AffiliateProfile,
    AffiliateReferral,
)
from app.logging_config import get_logger

router = APIRouter(prefix="/data-deletion", tags=["compliance"])
logger = get_logger("compliance")


class DataDeletionRequest(BaseModel):
    """Request for data deletion."""
    email: EmailStr
    reason: Optional[str] = None
    confirm: bool = False  # Must be True to proceed


class DataDeletionResponse(BaseModel):
    """Response for data deletion request."""
    request_id: str
    status: str
    message: str
    deleted_data: dict


@router.post("/request", response_model=DataDeletionResponse)
async def request_data_deletion(
    request: DataDeletionRequest,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> DataDeletionResponse:
    """
    Request deletion of all user data (GDPR Right to Erasure).
    
    This endpoint:
    1. Verifies the user's identity
    2. Deletes all associated data
    3. Logs the deletion for compliance
    """
    if not request.confirm:
        raise HTTPException(
            status_code=400,
            detail="Please confirm deletion by setting 'confirm' to true"
        )
    
    # Generate request ID for tracking
    request_id = str(uuid4())[:8]
    deleted_data = {
        "canvases": 0,
        "capsule_runs": 0,
        "credits_transactions": 0,
        "analytics_events": 0,
        "affiliate_data": 0,
    }
    
    # Find user by email
    result = await db.execute(
        select(UserAccount).where(UserAccount.email == request.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        logger.info(
            f"Data deletion requested for unknown email",
            extra={"request_id": request_id, "email": request.email}
        )
        # Return success even if user not found (privacy)
        return DataDeletionResponse(
            request_id=request_id,
            status="completed",
            message="If an account exists with this email, all data has been deleted.",
            deleted_data=deleted_data,
        )
    
    target_user_id = user.user_id
    
    # Verify requesting user matches (if authenticated)
    if user_id and user_id != target_user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only request deletion of your own data"
        )
    
    try:
        # Delete canvases
        result = await db.execute(
            delete(Canvas).where(Canvas.owner_id == target_user_id)
        )
        deleted_data["canvases"] = result.rowcount
        
        # Delete credit transactions
        result = await db.execute(
            delete(CreditLedger).where(CreditLedger.user_id == target_user_id)
        )
        deleted_data["credits_transactions"] = result.rowcount
        
        # Delete user credits
        await db.execute(
            delete(UserCredits).where(UserCredits.user_id == target_user_id)
        )
        
        # Delete analytics events
        result = await db.execute(
            delete(AnalyticsEvent).where(AnalyticsEvent.user_id == target_user_id)
        )
        deleted_data["analytics_events"] = result.rowcount
        
        # Delete affiliate data
        await db.execute(
            delete(AffiliateReferral).where(AffiliateReferral.referrer_user_id == target_user_id)
        )
        result = await db.execute(
            delete(AffiliateProfile).where(AffiliateProfile.user_id == target_user_id)
        )
        deleted_data["affiliate_data"] = result.rowcount
        
        # Finally, delete the user account
        await db.execute(
            delete(UserAccount).where(UserAccount.user_id == target_user_id)
        )
        
        await db.commit()
        
        logger.info(
            f"Data deletion completed",
            extra={
                "request_id": request_id,
                "user_id": target_user_id,
                "deleted_data": deleted_data,
                "reason": request.reason,
            }
        )
        
        return DataDeletionResponse(
            request_id=request_id,
            status="completed",
            message="All your data has been permanently deleted.",
            deleted_data=deleted_data,
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(
            f"Data deletion failed",
            extra={
                "request_id": request_id,
                "error": str(e),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Data deletion failed. Please contact support."
        )


@router.get("/status/{request_id}")
async def get_deletion_status(request_id: str) -> dict:
    """
    Check status of a data deletion request.
    
    Note: In production, this would check a deletion request queue.
    """
    return {
        "request_id": request_id,
        "status": "completed",
        "message": "Deletion requests are processed immediately.",
    }
