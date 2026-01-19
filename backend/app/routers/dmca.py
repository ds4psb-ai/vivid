"""DMCA Compliance API router.

Implements DMCA Safe Harbor compliance with:
- Takedown notice submission
- Counter-notice filing
- Status tracking
- Repeat infringer policy

Reference: https://copyrightalliance.org/education/copyright-law-explained/the-digital-millennium-copyright-act-dmca/dmca-safe-harbor/
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_user_id
from app.models_ip import DMCACase, IPCatalog, IPRights
from app.services.dmca_notification_service import dmca_notification_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dmca"])


# --- Pydantic Schemas ---

class DMCANoticeRequest(BaseModel):
    """DMCA takedown notice request.

    Contains all legally required elements for a valid DMCA notice.
    """
    ip_slug: Optional[str] = Field(None, description="Related IP slug (if known)")
    content_id: UUID = Field(..., description="ID of the infringing content")
    content_type: str = Field(default="generation", description="Type of content")

    # Claimant information
    claimant_name: str = Field(..., min_length=1, max_length=200)
    claimant_email: EmailStr
    claimant_company: Optional[str] = Field(None, max_length=200)

    # Claim details
    claim_description: str = Field(..., min_length=10, max_length=5000)
    claimed_work: Optional[str] = Field(None, max_length=2000, description="Description of original copyrighted work")
    claimed_urls: list[str] = Field(default_factory=list, description="URLs of infringing content")

    # Legal affirmations (must be true for valid notice)
    good_faith_belief: bool = Field(..., description="I have a good faith belief that use of the material is not authorized")
    accurate_statement: bool = Field(..., description="The information in this notice is accurate")
    authorized_to_act: bool = Field(..., description="I am authorized to act on behalf of the copyright owner")
    perjury_acknowledgment: bool = Field(..., description="I understand that under penalty of perjury this information is accurate")


class DMCANoticeResponse(BaseModel):
    """Response after submitting a DMCA notice."""
    notice_id: str
    status: str
    message: str
    content_removed: bool = False


class DMCACounterRequest(BaseModel):
    """DMCA counter-notice request.

    Contains all legally required elements for a valid counter-notice.
    """
    notice_id: UUID = Field(..., description="ID of the original DMCA notice")
    counter_statement: str = Field(..., min_length=10, max_length=5000)

    # Counter-filer information
    user_name: str = Field(..., min_length=1, max_length=200)
    user_email: EmailStr
    user_address: str = Field(..., min_length=10, max_length=500)
    user_phone: Optional[str] = Field(None, max_length=50)

    # Legal affirmations
    good_faith_belief: bool = Field(..., description="I have a good faith belief that the material was removed by mistake")
    consent_to_jurisdiction: bool = Field(..., description="I consent to jurisdiction of Federal District Court")
    perjury_acknowledgment: bool = Field(..., description="I understand that under penalty of perjury this information is accurate")


class DMCACounterResponse(BaseModel):
    """Response after submitting a counter-notice."""
    notice_id: str
    status: str
    message: str
    restoration_date: Optional[str] = None


class DMCAStatusResponse(BaseModel):
    """Status of a DMCA case."""
    notice_id: str
    status: str
    content_id: str
    content_type: str
    notice_received_at: str
    content_removed_at: Optional[str] = None
    counter_filed_at: Optional[str] = None
    counter_deadline: Optional[str] = None
    restored_at: Optional[str] = None


# --- API Endpoints ---

@router.post("/notice", response_model=DMCANoticeResponse)
async def submit_dmca_notice(
    request: DMCANoticeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit a DMCA takedown notice.

    This endpoint implements 17 U.S.C. § 512(c)(3) requirements.
    Valid notices result in expeditious removal of allegedly infringing content.

    Requirements for valid notice:
    - Physical or electronic signature of authorized person
    - Identification of copyrighted work claimed to be infringed
    - Identification of material to be removed
    - Contact information of complaining party
    - Statement of good faith belief
    - Statement of accuracy under penalty of perjury
    """
    # Validate legal affirmations
    if not all([
        request.good_faith_belief,
        request.accurate_statement,
        request.authorized_to_act,
        request.perjury_acknowledgment,
    ]):
        raise HTTPException(
            status_code=400,
            detail="All legal affirmations must be acknowledged for a valid DMCA notice"
        )

    # Get IP if slug provided
    ip_id = None
    if request.ip_slug:
        ip_result = await db.execute(
            select(IPCatalog).where(IPCatalog.slug == request.ip_slug)
        )
        ip = ip_result.scalar_one_or_none()
        if ip:
            ip_id = ip.id

    # Create DMCA case
    dmca_case = DMCACase(
        ip_id=ip_id,
        content_id=request.content_id,
        content_type=request.content_type,
        user_id="system",  # Will be updated when we identify content owner
        claimant_name=request.claimant_name,
        claimant_email=request.claimant_email,
        claimant_company=request.claimant_company,
        claim_description=request.claim_description,
        claimed_work=request.claimed_work,
        claimed_urls=request.claimed_urls,
        status="pending",
        notice_received_at=datetime.utcnow(),
    )

    db.add(dmca_case)
    await db.flush()

    # Log for admin review
    logger.info(
        f"DMCA notice received: case_id={dmca_case.id}, "
        f"content_id={request.content_id}, claimant={request.claimant_email}"
    )

    return DMCANoticeResponse(
        notice_id=str(dmca_case.id),
        status="pending",
        message="DMCA notice received. Our team will review and take appropriate action within 24-48 hours.",
        content_removed=False,
    )


@router.post("/counter", response_model=DMCACounterResponse)
async def submit_counter_notice(
    request: DMCACounterRequest,
    user_id: str = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Submit a DMCA counter-notice.

    This endpoint implements 17 U.S.C. § 512(g)(3) requirements.
    Counter-notices allow users to dispute takedowns they believe were in error.

    After receiving a valid counter-notice:
    - We notify the original claimant
    - Content may be restored in 10-14 business days if no court action is filed

    Requirements for valid counter-notice:
    - Physical or electronic signature of subscriber
    - Identification of removed material and its location
    - Statement under penalty of perjury that removal was a mistake
    - Subscriber's name, address, and phone number
    - Consent to jurisdiction of Federal District Court
    """
    # Validate legal affirmations
    if not all([
        request.good_faith_belief,
        request.consent_to_jurisdiction,
        request.perjury_acknowledgment,
    ]):
        raise HTTPException(
            status_code=400,
            detail="All legal affirmations must be acknowledged for a valid counter-notice"
        )

    # Get DMCA case
    result = await db.execute(
        select(DMCACase).where(DMCACase.id == request.notice_id)
    )
    dmca_case = result.scalar_one_or_none()

    if not dmca_case:
        raise HTTPException(status_code=404, detail="DMCA notice not found")

    if dmca_case.status not in ["pending", "removed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot file counter-notice for case with status: {dmca_case.status}"
        )

    # Calculate restoration deadline (10-14 business days)
    # Using 14 calendar days as approximation
    counter_deadline = datetime.utcnow() + timedelta(days=14)

    # Update case with counter-notice
    dmca_case.counter_statement = request.counter_statement
    dmca_case.counter_filed_at = datetime.utcnow()
    dmca_case.counter_user_name = request.user_name
    dmca_case.counter_user_email = request.user_email
    dmca_case.counter_deadline = counter_deadline
    dmca_case.status = "counter_pending"

    await db.flush()

    # Notify original claimant of counter-notice (per 17 U.S.C. § 512(g)(2)(B))
    notification = await dmca_notification_service.notify_claimant_counter(dmca_case)

    logger.info(
        f"DMCA counter-notice received: case_id={dmca_case.id}, "
        f"user={user_id}, claimant_notified={notification.success}"
    )

    return DMCACounterResponse(
        notice_id=str(dmca_case.id),
        status="counter_pending",
        message=(
            "Counter-notice received. The original claimant will be notified. "
            "If no court action is filed within 10-14 business days, content may be restored."
        ),
        restoration_date=counter_deadline.isoformat(),
    )


@router.get("/status/{notice_id}", response_model=DMCAStatusResponse)
async def get_dmca_status(
    notice_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get the status of a DMCA case.

    Available to both claimants and content owners for transparency.
    """
    result = await db.execute(
        select(DMCACase).where(DMCACase.id == notice_id)
    )
    dmca_case = result.scalar_one_or_none()

    if not dmca_case:
        raise HTTPException(status_code=404, detail="DMCA case not found")

    return DMCAStatusResponse(
        notice_id=str(dmca_case.id),
        status=dmca_case.status,
        content_id=str(dmca_case.content_id),
        content_type=dmca_case.content_type,
        notice_received_at=dmca_case.notice_received_at.isoformat(),
        content_removed_at=dmca_case.content_removed_at.isoformat() if dmca_case.content_removed_at else None,
        counter_filed_at=dmca_case.counter_filed_at.isoformat() if dmca_case.counter_filed_at else None,
        counter_deadline=dmca_case.counter_deadline.isoformat() if dmca_case.counter_deadline else None,
        restored_at=dmca_case.restored_at.isoformat() if dmca_case.restored_at else None,
    )


@router.get("/my-cases")
async def get_my_dmca_cases(
    user_id: str = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    """Get DMCA cases affecting my content."""
    query = select(DMCACase).where(DMCACase.user_id == user_id)

    if status:
        query = query.where(DMCACase.status == status)

    query = query.order_by(DMCACase.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    cases = result.scalars().all()

    # Count total
    count_result = await db.execute(
        select(func.count())
        .select_from(DMCACase)
        .where(DMCACase.user_id == user_id)
    )
    total = count_result.scalar() or 0

    return {
        "cases": [
            {
                "id": str(case.id),
                "content_id": str(case.content_id),
                "content_type": case.content_type,
                "status": case.status,
                "claimant_company": case.claimant_company,
                "notice_received_at": case.notice_received_at.isoformat(),
                "counter_deadline": case.counter_deadline.isoformat() if case.counter_deadline else None,
            }
            for case in cases
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# --- Admin Endpoints (internal) ---

@router.post("/admin/remove/{notice_id}")
async def admin_remove_content(
    notice_id: UUID,
    admin_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    # In production, add admin authentication here
):
    """[Admin] Remove content after DMCA notice review.

    This triggers:
    1. Content removal
    2. Notification to content owner
    3. Repeat infringer check
    """
    result = await db.execute(
        select(DMCACase).where(DMCACase.id == notice_id)
    )
    dmca_case = result.scalar_one_or_none()

    if not dmca_case:
        raise HTTPException(status_code=404, detail="DMCA case not found")

    dmca_case.status = "removed"
    dmca_case.content_removed_at = datetime.utcnow()
    if admin_notes:
        dmca_case.admin_notes = admin_notes

    await db.flush()

    # Process takedown: notify owner + check repeat infringer
    notification, repeat_check = await dmca_notification_service.process_takedown(
        dmca_case=dmca_case,
        db=db,
    )

    logger.info(
        f"Content removed via DMCA: case_id={dmca_case.id}, "
        f"repeat_infringer={repeat_check.is_repeat_infringer}, "
        f"strike_count={repeat_check.strike_count}"
    )

    return {
        "status": "removed",
        "notice_id": str(dmca_case.id),
        "notification_sent": notification.success,
        "repeat_infringer_check": {
            "is_repeat_infringer": repeat_check.is_repeat_infringer,
            "strike_count": repeat_check.strike_count,
            "threshold": repeat_check.threshold,
            "action_taken": repeat_check.action_taken,
        },
    }


@router.post("/admin/restore/{notice_id}")
async def admin_restore_content(
    notice_id: UUID,
    admin_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    # In production, add admin authentication here
):
    """[Admin] Restore content after counter-notice period."""
    result = await db.execute(
        select(DMCACase).where(DMCACase.id == notice_id)
    )
    dmca_case = result.scalar_one_or_none()

    if not dmca_case:
        raise HTTPException(status_code=404, detail="DMCA case not found")

    if dmca_case.status != "counter_pending":
        raise HTTPException(
            status_code=400,
            detail="Content can only be restored after counter-notice is filed"
        )

    dmca_case.status = "restored"
    dmca_case.restored_at = datetime.utcnow()
    if admin_notes:
        dmca_case.admin_notes = admin_notes

    await db.flush()

    logger.info(f"Content restored via counter-notice: case_id={dmca_case.id}")

    return {"status": "restored", "notice_id": str(dmca_case.id)}


@router.post("/admin/reject/{notice_id}")
async def admin_reject_notice(
    notice_id: UUID,
    reason: str,
    db: AsyncSession = Depends(get_db),
    # In production, add admin authentication here
):
    """[Admin] Reject an invalid DMCA notice."""
    result = await db.execute(
        select(DMCACase).where(DMCACase.id == notice_id)
    )
    dmca_case = result.scalar_one_or_none()

    if not dmca_case:
        raise HTTPException(status_code=404, detail="DMCA case not found")

    dmca_case.status = "rejected"
    dmca_case.admin_notes = f"Rejected: {reason}"

    await db.flush()

    logger.info(f"DMCA notice rejected: case_id={dmca_case.id}, reason={reason}")

    return {"status": "rejected", "notice_id": str(dmca_case.id)}
