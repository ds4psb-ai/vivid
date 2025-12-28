"""NICE Payments (나이스페이) integration endpoints."""
import base64
from datetime import datetime
from typing import Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import CrebitApplication


router = APIRouter(prefix="/payment", tags=["payment"])


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────────────────────────────────────────

class PaymentConfirmRequest(BaseModel):
    tid: str
    amount: int
    application_id: UUID


class PaymentConfirmResponse(BaseModel):
    success: bool
    tid: str
    status: str
    paid_at: Optional[datetime] = None
    result_code: str
    result_msg: str


class PaymentCallbackData(BaseModel):
    authResultCode: str
    authResultMsg: str
    tid: str
    clientId: str
    orderId: str
    amount: str
    authToken: Optional[str] = None
    signature: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def get_nice_credentials() -> str:
    """Generate Base64 encoded credentials for NICE API."""
    credentials = f"{settings.NICEPAY_CLIENT_ID}:{settings.NICEPAY_SECRET_KEY}"
    return base64.b64encode(credentials.encode()).decode()


async def call_nice_approval_api(tid: str, amount: int) -> dict:
    """Call NICE Payments approval API."""
    credentials = get_nice_credentials()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.NICEPAY_API_URL}/v1/payments/{tid}",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json",
            },
            json={"amount": amount},
        )
        
        if response.status_code != 200:
            return {
                "resultCode": "9999",
                "resultMsg": f"HTTP Error: {response.status_code}",
            }
        
        return response.json()


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/confirm", response_model=PaymentConfirmResponse)
async def confirm_payment(
    data: PaymentConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm NICE payment after user authentication.
    
    This endpoint is called after the user completes card authentication
    in the NICE payment window. It calls the NICE approval API and updates
    the application status.
    """
    # 1. Find the application
    result = await db.execute(
        select(CrebitApplication).where(CrebitApplication.id == data.application_id)
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application.status == "paid":
        return PaymentConfirmResponse(
            success=True,
            tid=application.payment_id or data.tid,
            status="already_paid",
            paid_at=application.paid_at,
            result_code="0000",
            result_msg="Already paid",
        )
    
    # 2. Call NICE approval API
    nice_result = await call_nice_approval_api(data.tid, data.amount)
    
    result_code = nice_result.get("resultCode", "9999")
    result_msg = nice_result.get("resultMsg", "Unknown error")
    
    # 3. Process result
    if result_code == "0000":
        # Success - update application
        application.status = "paid"
        application.payment_id = data.tid
        application.paid_amount = data.amount
        application.paid_at = datetime.utcnow()
        await db.commit()
        await db.refresh(application)
        
        return PaymentConfirmResponse(
            success=True,
            tid=data.tid,
            status="paid",
            paid_at=application.paid_at,
            result_code=result_code,
            result_msg=result_msg,
        )
    else:
        # Failed
        return PaymentConfirmResponse(
            success=False,
            tid=data.tid,
            status="failed",
            paid_at=None,
            result_code=result_code,
            result_msg=result_msg,
        )


@router.get("/config")
async def get_payment_config():
    """
    Get payment configuration for frontend.
    
    Returns the client ID and mode for JS SDK initialization.
    """
    return {
        "client_id": settings.NICEPAY_CLIENT_ID,
        "mode": settings.NICEPAY_MODE,
        "js_sdk_url": (
            "https://pay.nicepay.co.kr/v1/js/"
            if settings.NICEPAY_MODE == "production"
            else "https://pay.nicepay.co.kr/v1/js/"  # Same URL for both
        ),
    }
