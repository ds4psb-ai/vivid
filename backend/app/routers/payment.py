"""NICE Payments (나이스페이) integration endpoints.

Security Notes:
- /confirm endpoint requires auth or confirm token and validates application ownership
- Rate limiting should be applied at nginx/middleware level
- NICEPAY auth signature is verified on callback
"""
import base64
import hmac
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user_optional
from app.models import CrebitApplication
from app.services.crebit_payment_security import (
    compute_nicepay_auth_signature,
    normalize_amount_str,
    verify_confirm_token,
)

router = APIRouter(prefix="/payment", tags=["payment"])
logger = logging.getLogger("payment")


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────────────────────────────────────────

class PaymentConfirmRequest(BaseModel):
    tid: str
    amount: int
    application_id: UUID
    amount_raw: Optional[str] = None
    auth_token: Optional[str] = None
    signature: Optional[str] = None
    client_id: Optional[str] = None
    confirm_token: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


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
    # H1.3: SecretStr - use .get_secret_value() for actual secret key
    credentials = f"{settings.NICEPAY_CLIENT_ID}:{settings.NICEPAY_SECRET_KEY.get_secret_value()}"
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
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Confirm NICE payment after authentication or confirm token validation.

    This endpoint is called after the user completes card authentication
    in the NICE payment window. It calls the NICE approval API and updates
    the application status.

    Security:
    - Requires authenticated user or confirm token (prevents anonymous abuse)
    - NICEPAY auth signature verification
    - NICE API validates tid/amount match
    - Rate limiting at nginx level
    """
    # Audit logging for security monitoring
    client_ip = request.client.host if request.client else "unknown"
    user_id = user.get("user_id") if user else None
    logger.info(
        f"[PAYMENT CONFIRM] app_id={data.application_id} tid={data.tid} "
        f"amount={data.amount} user={user_id or 'anonymous'} ip={client_ip}"
    )

    # 1. Find the application
    result = await db.execute(
        select(CrebitApplication).where(CrebitApplication.id == data.application_id)
    )
    application = result.scalar_one_or_none()

    if not application:
        logger.warning(f"[PAYMENT CONFIRM FAIL] app_id={data.application_id} not found ip={client_ip}")
        raise HTTPException(status_code=404, detail="Application not found")

    # 2. Verify NICEPAY auth signature
    if not data.auth_token or not data.signature or not data.client_id:
        raise HTTPException(status_code=400, detail="Missing NICEPAY signature parameters")

    if data.client_id != settings.NICEPAY_CLIENT_ID:
        raise HTTPException(status_code=400, detail="Invalid NICEPAY client ID")

    if data.amount_raw:
        try:
            raw_amount_int = int(data.amount_raw)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid amount format") from exc
        if raw_amount_int != data.amount:
            raise HTTPException(status_code=400, detail="Amount mismatch")

    amount_str = normalize_amount_str(data.amount_raw, data.amount)
    # H1.3: SecretStr - use .get_secret_value() for actual secret key
    expected_signature = compute_nicepay_auth_signature(
        data.auth_token,
        data.client_id,
        amount_str,
        settings.NICEPAY_SECRET_KEY.get_secret_value(),
    )
    if not hmac.compare_digest(expected_signature, data.signature):
        raise HTTPException(status_code=400, detail="Invalid NICEPAY signature")

    # 3. Verify ownership or confirm token
    if application.owner_id:
        if not user_id or application.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized for this application")
    else:
        if user_id:
            application.owner_id = user_id
        else:
            if not data.confirm_token:
                raise HTTPException(status_code=401, detail="Confirm token required")
            if application.confirm_token_expires_at and application.confirm_token_expires_at < datetime.utcnow():
                raise HTTPException(status_code=401, detail="Confirm token expired")
            if not verify_confirm_token(data.confirm_token, application.confirm_token_hash):
                raise HTTPException(status_code=403, detail="Invalid confirm token")

    if application.status == "paid":
        return PaymentConfirmResponse(
            success=True,
            tid=application.payment_id or data.tid,
            status="already_paid",
            paid_at=application.paid_at,
            result_code="0000",
            result_msg="Already paid",
        )

    # 4. Prevent duplicate tid reuse
    dup_result = await db.execute(
        select(CrebitApplication)
        .where(CrebitApplication.payment_id == data.tid)
        .where(CrebitApplication.id != data.application_id)
    )
    if dup_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Payment ID already used")

    # 5. Call NICE approval API
    nice_result = await call_nice_approval_api(data.tid, data.amount)

    result_code = nice_result.get("resultCode", "9999")
    result_msg = nice_result.get("resultMsg", "Unknown error")

    # 6. Process result
    if result_code == "0000":
        # Success - update application
        application.status = "paid"
        application.payment_id = data.tid
        application.paid_amount = data.amount
        application.paid_at = datetime.utcnow()
        application.confirm_token_hash = None
        application.confirm_token_expires_at = None
        await db.commit()
        await db.refresh(application)

        logger.info(
            f"[PAYMENT SUCCESS] app_id={data.application_id} tid={data.tid} "
            f"amount={data.amount} ip={client_ip}"
        )
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
        logger.warning(
            f"[PAYMENT FAIL] app_id={data.application_id} tid={data.tid} "
            f"code={result_code} msg={result_msg} ip={client_ip}"
        )
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
