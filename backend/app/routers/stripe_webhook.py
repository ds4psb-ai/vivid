"""
Stripe Webhook Router - H2.3 Core Feature Hardening

Handles Stripe webhook events with:
1. Mandatory signature verification
2. Idempotent event processing
3. Comprehensive audit logging
4. PCI DSS 4.0 compliance

Security Note:
- ALWAYS verify webhook signatures before processing
- NEVER trust unverified webhook data
- Log all webhook events for audit trail
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stripe", tags=["stripe-webhook"])


# =============================================================================
# Schemas
# =============================================================================

class WebhookResponse(BaseModel):
    """Response for webhook processing."""
    received: bool
    event_id: Optional[str] = None
    event_type: Optional[str] = None


class CheckoutSessionRequest(BaseModel):
    """Request to create checkout session."""
    credits: int
    price_cents: int
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutSessionResponse(BaseModel):
    """Response with checkout session details."""
    session_id: str
    checkout_url: str


class PaymentConfigResponse(BaseModel):
    """Payment configuration for frontend."""
    publishable_key: str
    credit_packages: list


# =============================================================================
# Webhook Endpoint
# =============================================================================

def _get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Check for forwarded headers (in order of preference)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (original client)
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct connection IP
    if request.client:
        return request.client.host
    return ""


def _verify_stripe_ip(client_ip: str) -> bool:
    """P1: Verify client IP is in Stripe's webhook IP whitelist."""
    whitelist = settings.STRIPE_WEBHOOK_IP_WHITELIST
    if not whitelist:
        # No whitelist configured - skip IP check (rely on signature only)
        return True

    allowed_ips = {ip.strip() for ip in whitelist.split(",") if ip.strip()}
    if not allowed_ips:
        return True

    return client_ip in allowed_ips


@router.post("/webhook", response_model=WebhookResponse)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
):
    """
    Handle Stripe webhook events (H2.3 Enhanced + P1 IP Whitelist).

    CRITICAL: All webhooks MUST have valid signatures.
    This endpoint processes payment-related events from Stripe.

    Events Handled:
    - checkout.session.completed: Credit purchase completed
    - payment_intent.payment_failed: Payment failed
    - charge.refunded: Refund processed
    - checkout.session.expired: Session expired

    Security:
    - P1: Optional IP whitelist check (defense-in-depth)
    - Signature verification is MANDATORY
    - All events are logged for audit
    - Duplicate events are handled idempotently
    """
    # P1: IP whitelist check (defense-in-depth, before signature verification)
    client_ip = _get_client_ip(request)
    if not _verify_stripe_ip(client_ip):
        logger.warning(f"Stripe webhook rejected: IP {client_ip} not in whitelist")
        raise HTTPException(
            status_code=403,
            detail="Webhook source IP not authorized"
        )

    # Get raw body for signature verification
    payload = await request.body()

    # Log incoming webhook (without sensitive data)
    logger.info(
        f"Stripe webhook received, "
        f"signature_present={bool(stripe_signature)}, "
        f"payload_size={len(payload)}, "
        f"client_ip={client_ip}"
    )

    # Signature verification is MANDATORY
    if not stripe_signature:
        logger.error("Stripe webhook received without signature")
        raise HTTPException(
            status_code=400,
            detail="Missing Stripe-Signature header"
        )

    try:
        from app.services.stripe_payment import get_stripe_service

        service = get_stripe_service()

        # Verify signature (CRITICAL for security)
        event = service.verify_webhook_signature(payload, stripe_signature)

        # Process the verified event
        result = await service.handle_webhook_event(event, db)

        logger.info(
            f"Webhook processed: type={event.type}, "
            f"id={event.id}, result={result.get('status')}"
        )

        return WebhookResponse(
            received=True,
            event_id=event.id,
            event_type=event.type,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Webhook processing error: {e}")
        # Return 200 to acknowledge receipt (Stripe will retry otherwise)
        # But log the error for investigation
        return WebhookResponse(
            received=True,
            event_id=None,
            event_type=None,
        )


# =============================================================================
# Checkout Endpoints
# =============================================================================

@router.post("/checkout/session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = None,  # Should come from auth dependency
):
    """
    Create a Stripe Checkout Session for credit purchase.

    This endpoint creates a secure checkout session that redirects
    the user to Stripe's hosted payment page.

    Security:
    - Uses idempotency keys to prevent duplicate sessions
    - Session expires after 30 minutes
    - No card details touch our servers (PCI compliance)
    """
    # TODO: Add proper auth dependency
    if not user_id:
        # For now, require user_id in development
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    try:
        from app.services.stripe_payment import get_stripe_service

        service = get_stripe_service()

        result = await service.create_checkout_session(
            user_id=user_id,
            credits=request.credits,
            price_cents=request.price_cents,
            db=db,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )

        return CheckoutSessionResponse(
            session_id=result.session_id,
            checkout_url=result.checkout_url,
        )

    except HTTPException:
        raise
    except RuntimeError as e:
        # Stripe not configured
        logger.error(f"Stripe service error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Payment service unavailable"
        )
    except Exception as e:
        logger.exception(f"Checkout session error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create checkout session"
        )


@router.get("/checkout/session/{session_id}")
async def get_checkout_session_status(
    session_id: str,
):
    """
    Get checkout session status.

    Used by frontend to verify payment completion.
    """
    try:
        from app.services.stripe_payment import get_stripe_service

        service = get_stripe_service()
        return await service.get_session_status(session_id)

    except HTTPException:
        raise
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="Payment service unavailable"
        )


# =============================================================================
# Configuration Endpoint
# =============================================================================

@router.get("/config", response_model=PaymentConfigResponse)
async def get_payment_config():
    """
    Get payment configuration for frontend.

    Returns:
    - Publishable key for Stripe.js
    - Available credit packages
    """
    try:
        from app.services.stripe_payment import get_stripe_service

        service = get_stripe_service()

        return PaymentConfigResponse(
            publishable_key=service.get_publishable_key(),
            credit_packages=service.get_credit_packages(),
        )

    except RuntimeError:
        # Stripe not configured - return empty config
        return PaymentConfigResponse(
            publishable_key="",
            credit_packages=[],
        )
