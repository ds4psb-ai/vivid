"""Affiliate and referral endpoints."""
from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_is_admin, get_user_id
from app.credit_service import grant_promo_credits
from app.database import get_db
from app.models import AffiliateProfile, AffiliateReferral, GenerationRun

router = APIRouter()

DEFAULT_REFERRER_REWARD = int(os.getenv("AFFILIATE_REFERRER_REWARD", "100"))
DEFAULT_REFEREE_REWARD = int(os.getenv("AFFILIATE_REFEREE_REWARD", "100"))


class AffiliateProfileResponse(BaseModel):
    user_id: str
    affiliate_code: str
    referral_link: Optional[str] = None
    total_referrals: int
    total_earned: int
    pending_count: int


class AffiliateLinkResponse(BaseModel):
    affiliate_code: str
    referral_link: Optional[str] = None


class AffiliateTrackRequest(BaseModel):
    affiliate_code: str
    referee_label: Optional[str] = None


class AffiliateRegisterRequest(BaseModel):
    affiliate_code: str
    referee_label: Optional[str] = None


class AffiliateReferralItem(BaseModel):
    id: str
    referee_label: Optional[str] = None
    status: str
    reward_status: str
    reward_amount: int
    referee_reward_amount: int
    created_at: datetime


class AffiliateRewardRequest(BaseModel):
    referral_id: str
    referrer_reward: Optional[int] = None
    referee_reward: Optional[int] = None
    note: Optional[str] = None


class AffiliateRewardResponse(BaseModel):
    referral_id: str
    status: str
    reward_status: str
    referrer_reward: int
    referee_reward: int
    reward_ledger_id: Optional[str] = None
    referee_reward_ledger_id: Optional[str] = None


def _generate_affiliate_code() -> str:
    return f"VIVID-{uuid.uuid4().hex[:8].upper()}"


async def _get_or_create_profile(db: AsyncSession, user_id: str) -> AffiliateProfile:
    result = await db.execute(
        select(AffiliateProfile).where(AffiliateProfile.user_id == user_id)
    )
    profile = result.scalars().first()
    if profile:
        return profile

    for _ in range(5):
        code = _generate_affiliate_code()
        result = await db.execute(
            select(AffiliateProfile).where(AffiliateProfile.affiliate_code == code)
        )
        if result.scalars().first() is None:
            profile = AffiliateProfile(user_id=user_id, affiliate_code=code)
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
            return profile

    raise HTTPException(status_code=500, detail="Failed to generate affiliate code")


@router.get("/profile", response_model=AffiliateProfileResponse)
async def get_affiliate_profile(
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> AffiliateProfileResponse:
    resolved_user_id = user_id or "demo-user"
    profile = await _get_or_create_profile(db, resolved_user_id)

    total_referrals_result = await db.execute(
        select(func.count()).select_from(AffiliateReferral).where(
            AffiliateReferral.referrer_user_id == resolved_user_id
        )
    )
    total_referrals = int(total_referrals_result.scalar() or 0)
    earned_result = await db.execute(
        select(func.coalesce(func.sum(AffiliateReferral.reward_amount), 0)).where(
            AffiliateReferral.referrer_user_id == resolved_user_id,
            AffiliateReferral.reward_status == "granted",
        )
    )
    total_earned = int(earned_result.scalar() or 0)
    pending_result = await db.execute(
        select(func.count()).select_from(AffiliateReferral).where(
            AffiliateReferral.referrer_user_id == resolved_user_id,
            AffiliateReferral.reward_status == "pending",
        )
    )
    pending_count = int(pending_result.scalar() or 0)

    return AffiliateProfileResponse(
        user_id=resolved_user_id,
        affiliate_code=profile.affiliate_code,
        referral_link=None,
        total_referrals=total_referrals,
        total_earned=total_earned,
        pending_count=pending_count,
    )


@router.post("/link", response_model=AffiliateLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_affiliate_link(
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> AffiliateLinkResponse:
    resolved_user_id = user_id or "demo-user"
    profile = await _get_or_create_profile(db, resolved_user_id)
    return AffiliateLinkResponse(affiliate_code=profile.affiliate_code, referral_link=None)


@router.post("/track", response_model=AffiliateReferralItem, status_code=status.HTTP_201_CREATED)
async def track_referral_click(
    payload: AffiliateTrackRequest,
    db: AsyncSession = Depends(get_db),
) -> AffiliateReferralItem:
    result = await db.execute(
        select(AffiliateProfile).where(AffiliateProfile.affiliate_code == payload.affiliate_code)
    )
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Affiliate code not found")

    existing = None
    if payload.referee_label:
        result = await db.execute(
            select(AffiliateReferral).where(
                AffiliateReferral.referrer_user_id == profile.user_id,
                AffiliateReferral.referee_user_id.is_(None),
                AffiliateReferral.referee_label == payload.referee_label,
            )
        )
        existing = result.scalars().first()

    if existing:
        existing.status = "clicked"
        existing.updated_at = datetime.utcnow()
        await db.commit()
        referral = existing
    else:
        referral = AffiliateReferral(
            affiliate_code=payload.affiliate_code,
            referrer_user_id=profile.user_id,
            referee_label=payload.referee_label,
            status="clicked",
            reward_status="pending",
            reward_amount=DEFAULT_REFERRER_REWARD,
            referee_reward_amount=DEFAULT_REFEREE_REWARD,
        )
        db.add(referral)
        await db.commit()
        await db.refresh(referral)

    return AffiliateReferralItem(
        id=str(referral.id),
        referee_label=referral.referee_label,
        status=referral.status,
        reward_status=referral.reward_status,
        reward_amount=referral.reward_amount,
        referee_reward_amount=referral.referee_reward_amount,
        created_at=referral.created_at,
    )


@router.post("/register", response_model=AffiliateReferralItem, status_code=status.HTTP_201_CREATED)
async def register_referral(
    payload: AffiliateRegisterRequest,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> AffiliateReferralItem:
    resolved_user_id = user_id or "demo-user"
    result = await db.execute(
        select(AffiliateProfile).where(AffiliateProfile.affiliate_code == payload.affiliate_code)
    )
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Affiliate code not found")
    if profile.user_id == resolved_user_id:
        raise HTTPException(status_code=400, detail="Self-referral is not allowed")

    result = await db.execute(
        select(AffiliateReferral).where(
            AffiliateReferral.referrer_user_id == profile.user_id,
            AffiliateReferral.referee_user_id == resolved_user_id,
        )
    )
    referral = result.scalars().first()

    if not referral and payload.referee_label:
        result = await db.execute(
            select(AffiliateReferral).where(
                AffiliateReferral.referrer_user_id == profile.user_id,
                AffiliateReferral.referee_user_id.is_(None),
                AffiliateReferral.referee_label == payload.referee_label,
            )
        )
        referral = result.scalars().first()

    if referral:
        referral.referee_user_id = resolved_user_id
        referral.status = "signed_up"
        referral.reward_status = "pending"
        referral.reward_amount = referral.reward_amount or DEFAULT_REFERRER_REWARD
        referral.referee_reward_amount = referral.referee_reward_amount or DEFAULT_REFEREE_REWARD
    else:
        referral = AffiliateReferral(
            affiliate_code=payload.affiliate_code,
            referrer_user_id=profile.user_id,
            referee_user_id=resolved_user_id,
            referee_label=payload.referee_label,
            status="signed_up",
            reward_status="pending",
            reward_amount=DEFAULT_REFERRER_REWARD,
            referee_reward_amount=DEFAULT_REFEREE_REWARD,
        )
        db.add(referral)

    activation_result = await db.execute(
        select(func.count()).select_from(GenerationRun).where(
            GenerationRun.owner_id == resolved_user_id
        )
    )
    if int(activation_result.scalar() or 0) > 0:
        referral.status = "activated"

    referral.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(referral)

    return AffiliateReferralItem(
        id=str(referral.id),
        referee_label=referral.referee_label,
        status=referral.status,
        reward_status=referral.reward_status,
        reward_amount=referral.reward_amount,
        referee_reward_amount=referral.referee_reward_amount,
        created_at=referral.created_at,
    )


@router.get("/referrals", response_model=List[AffiliateReferralItem])
async def list_referrals(
    limit: int = 20,
    user_id: Optional[str] = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[AffiliateReferralItem]:
    resolved_user_id = user_id or "demo-user"
    limit = max(1, min(limit, 50))
    result = await db.execute(
        select(AffiliateReferral)
        .where(AffiliateReferral.referrer_user_id == resolved_user_id)
        .order_by(AffiliateReferral.created_at.desc())
        .limit(limit)
    )
    referrals = result.scalars().all()
    return [
        AffiliateReferralItem(
            id=str(referral.id),
            referee_label=referral.referee_label,
            status=referral.status,
            reward_status=referral.reward_status,
            reward_amount=referral.reward_amount,
            referee_reward_amount=referral.referee_reward_amount,
            created_at=referral.created_at,
        )
        for referral in referrals
    ]


@router.post("/reward", response_model=AffiliateRewardResponse)
async def grant_referral_reward(
    payload: AffiliateRewardRequest,
    is_admin: bool = Depends(get_is_admin),
    db: AsyncSession = Depends(get_db),
) -> AffiliateRewardResponse:
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        referral_uuid = uuid.UUID(payload.referral_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid referral_id") from exc

    result = await db.execute(
        select(AffiliateReferral).where(AffiliateReferral.id == referral_uuid)
    )
    referral = result.scalars().first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    if referral.reward_status == "granted":
        raise HTTPException(status_code=409, detail="Reward already granted")
    if not referral.referee_user_id:
        raise HTTPException(status_code=400, detail="Referee not linked to a user")

    activation_result = await db.execute(
        select(func.count()).select_from(GenerationRun).where(
            GenerationRun.owner_id == referral.referee_user_id
        )
    )
    if int(activation_result.scalar() or 0) == 0:
        raise HTTPException(status_code=400, detail="Referee not activated")

    referrer_reward = payload.referrer_reward or DEFAULT_REFERRER_REWARD
    referee_reward = payload.referee_reward or DEFAULT_REFEREE_REWARD

    referrer_entry = await grant_promo_credits(
        db=db,
        user_id=referral.referrer_user_id,
        amount=referrer_reward,
        description=payload.note or "Affiliate reward",
        meta={"referral_id": payload.referral_id, "role": "referrer"},
        event_type="reward",
    )
    referee_entry = await grant_promo_credits(
        db=db,
        user_id=referral.referee_user_id,
        amount=referee_reward,
        description=payload.note or "Affiliate reward",
        meta={"referral_id": payload.referral_id, "role": "referee"},
        event_type="reward",
    )

    referral.status = "paid"
    referral.reward_status = "granted"
    referral.reward_amount = referrer_reward
    referral.referee_reward_amount = referee_reward
    referral.reward_ledger_id = referrer_entry.id
    referral.referee_reward_ledger_id = referee_entry.id
    referral.updated_at = datetime.utcnow()
    await db.commit()

    return AffiliateRewardResponse(
        referral_id=str(referral.id),
        status=referral.status,
        reward_status=referral.reward_status,
        referrer_reward=referrer_reward,
        referee_reward=referee_reward,
        reward_ledger_id=str(referral.reward_ledger_id) if referral.reward_ledger_id else None,
        referee_reward_ledger_id=str(referral.referee_reward_ledger_id)
        if referral.referee_reward_ledger_id
        else None,
    )
