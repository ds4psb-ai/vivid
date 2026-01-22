"""Marketplace Router for Phase 10 IP Licensing.

REST endpoints for IP marketplace operations.

Endpoints:
- POST /marketplace/listings - Create listing
- GET /marketplace/listings - List listings
- GET /marketplace/listings/{id} - Get listing details
- PUT /marketplace/listings/{id} - Update listing
- POST /marketplace/listings/{id}/purchase - Purchase listing
- POST /marketplace/listings/{id}/review - Create review
- GET /marketplace/listings/{id}/reviews - List reviews
- GET /marketplace/purchases - List user's purchases
- GET /marketplace/sales - List user's sales
- GET /marketplace/stats - Get seller stats
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.utils.error_sanitize import safe_error_detail
from app.services.marketplace_service import MarketplaceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/marketplace", tags=["marketplace"])


# =============================================================================
# Pydantic Models
# =============================================================================

class CreateListingRequest(BaseModel):
    """Request to create a marketplace listing."""
    ip_id: UUID
    title_ko: str = Field(min_length=1, max_length=200)
    title_en: str = Field(min_length=1, max_length=200)
    description_ko: Optional[str] = None
    description_en: Optional[str] = None
    license_tier: str = Field(default="free", pattern="^(free|commercial|exclusive)$")
    price_credits: int = Field(default=0, ge=0)
    royalty_percent: int = Field(default=0, ge=0, le=100)
    usage_rights: List[str] = Field(default=["chat"])
    territory_restrictions: List[str] = Field(default=[])


class UpdateListingRequest(BaseModel):
    """Request to update a listing."""
    title_ko: Optional[str] = Field(None, min_length=1, max_length=200)
    title_en: Optional[str] = Field(None, min_length=1, max_length=200)
    description_ko: Optional[str] = None
    description_en: Optional[str] = None
    license_tier: Optional[str] = Field(None, pattern="^(free|commercial|exclusive)$")
    price_credits: Optional[int] = Field(None, ge=0)
    royalty_percent: Optional[int] = Field(None, ge=0, le=100)
    usage_rights: Optional[List[str]] = None
    territory_restrictions: Optional[List[str]] = None


class ListingResponse(BaseModel):
    """Marketplace listing response."""
    id: UUID
    ip_id: UUID
    seller_id: str
    title_ko: str
    title_en: str
    description_ko: Optional[str]
    description_en: Optional[str]
    license_tier: str
    price_credits: int
    royalty_percent: int
    usage_rights: List[str]
    territory_restrictions: List[str]
    view_count: int
    purchase_count: int
    average_rating: float
    rating_count: int
    is_featured: bool
    is_verified: bool
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ListingListResponse(BaseModel):
    """Paginated listing list response."""
    listings: List[ListingResponse]
    total: int
    page: int
    page_size: int


class PurchaseResponse(BaseModel):
    """Purchase response."""
    id: UUID
    listing_id: UUID
    buyer_id: str
    seller_id: str
    price_paid: int
    seller_revenue: int
    platform_fee: int
    fork_royalty: int
    license_granted: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PurchaseListResponse(BaseModel):
    """Paginated purchase list response."""
    purchases: List[PurchaseResponse]
    total: int
    page: int
    page_size: int


class CreateReviewRequest(BaseModel):
    """Request to create a review."""
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(None, max_length=2000)


class ReviewResponse(BaseModel):
    """Review response."""
    id: UUID
    listing_id: UUID
    purchase_id: UUID
    reviewer_id: str
    rating: int
    title: Optional[str]
    content: Optional[str]
    is_verified_purchase: bool
    helpful_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    """Paginated review list response."""
    reviews: List[ReviewResponse]
    total: int
    page: int
    page_size: int


class SellerStatsResponse(BaseModel):
    """Seller statistics response."""
    total_revenue: int
    total_purchases: int
    active_listings: int
    average_rating: float


# =============================================================================
# Listing Endpoints
# =============================================================================

@router.post("/listings", response_model=ListingResponse)
async def create_listing(
    request: CreateListingRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new marketplace listing."""
    service = MarketplaceService(db)

    try:
        listing = await service.create_listing(
            seller_id=user["id"],
            ip_id=request.ip_id,
            title_ko=request.title_ko,
            title_en=request.title_en,
            description_ko=request.description_ko,
            description_en=request.description_en,
            license_tier=request.license_tier,
            price_credits=request.price_credits,
            royalty_percent=request.royalty_percent,
            usage_rights=request.usage_rights,
            territory_restrictions=request.territory_restrictions,
        )

        return ListingResponse(
            id=listing.id,
            ip_id=listing.ip_id,
            seller_id=listing.seller_id,
            title_ko=listing.title_ko,
            title_en=listing.title_en,
            description_ko=listing.description_ko,
            description_en=listing.description_en,
            license_tier=listing.license_tier,
            price_credits=listing.price_credits,
            royalty_percent=listing.royalty_percent,
            usage_rights=listing.usage_rights,
            territory_restrictions=listing.territory_restrictions,
            view_count=listing.view_count,
            purchase_count=listing.purchase_count,
            average_rating=listing.average_rating,
            rating_count=listing.rating_count,
            is_featured=listing.is_featured,
            is_verified=listing.is_verified,
            status=listing.status,
            created_at=listing.created_at,
            updated_at=listing.updated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Marketplace operation"))


@router.get("/listings", response_model=ListingListResponse)
async def list_listings(
    license_tier: Optional[str] = None,
    is_featured: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = Query(default="popular", pattern="^(popular|recent|price_low|price_high)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List marketplace listings with filters."""
    service = MarketplaceService(db)

    offset = (page - 1) * page_size
    listings, total = await service.list_listings(
        license_tier=license_tier,
        is_featured=is_featured,
        search_query=search,
        limit=page_size,
        offset=offset,
        sort_by=sort_by,
    )

    return ListingListResponse(
        listings=[
            ListingResponse(
                id=l.id,
                ip_id=l.ip_id,
                seller_id=l.seller_id,
                title_ko=l.title_ko,
                title_en=l.title_en,
                description_ko=l.description_ko,
                description_en=l.description_en,
                license_tier=l.license_tier,
                price_credits=l.price_credits,
                royalty_percent=l.royalty_percent,
                usage_rights=l.usage_rights,
                territory_restrictions=l.territory_restrictions,
                view_count=l.view_count,
                purchase_count=l.purchase_count,
                average_rating=l.average_rating,
                rating_count=l.rating_count,
                is_featured=l.is_featured,
                is_verified=l.is_verified,
                status=l.status,
                created_at=l.created_at,
                updated_at=l.updated_at,
            )
            for l in listings
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/listings/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get listing details."""
    service = MarketplaceService(db)

    listing = await service.get_listing(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Increment view count
    await service.increment_view_count(listing_id)

    return ListingResponse(
        id=listing.id,
        ip_id=listing.ip_id,
        seller_id=listing.seller_id,
        title_ko=listing.title_ko,
        title_en=listing.title_en,
        description_ko=listing.description_ko,
        description_en=listing.description_en,
        license_tier=listing.license_tier,
        price_credits=listing.price_credits,
        royalty_percent=listing.royalty_percent,
        usage_rights=listing.usage_rights,
        territory_restrictions=listing.territory_restrictions,
        view_count=listing.view_count + 1,
        purchase_count=listing.purchase_count,
        average_rating=listing.average_rating,
        rating_count=listing.rating_count,
        is_featured=listing.is_featured,
        is_verified=listing.is_verified,
        status=listing.status,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
    )


@router.put("/listings/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: UUID,
    request: UpdateListingRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a listing (seller only)."""
    service = MarketplaceService(db)

    updates = request.model_dump(exclude_unset=True)
    listing = await service.update_listing(listing_id, user["id"], **updates)

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found or not authorized")

    return ListingResponse(
        id=listing.id,
        ip_id=listing.ip_id,
        seller_id=listing.seller_id,
        title_ko=listing.title_ko,
        title_en=listing.title_en,
        description_ko=listing.description_ko,
        description_en=listing.description_en,
        license_tier=listing.license_tier,
        price_credits=listing.price_credits,
        royalty_percent=listing.royalty_percent,
        usage_rights=listing.usage_rights,
        territory_restrictions=listing.territory_restrictions,
        view_count=listing.view_count,
        purchase_count=listing.purchase_count,
        average_rating=listing.average_rating,
        rating_count=listing.rating_count,
        is_featured=listing.is_featured,
        is_verified=listing.is_verified,
        status=listing.status,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
    )


# =============================================================================
# Purchase Endpoints
# =============================================================================

@router.post("/listings/{listing_id}/purchase", response_model=PurchaseResponse)
async def purchase_listing(
    listing_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Purchase a marketplace listing."""
    service = MarketplaceService(db)

    try:
        purchase = await service.purchase_listing(
            listing_id=listing_id,
            buyer_id=user["id"],
        )

        return PurchaseResponse(
            id=purchase.id,
            listing_id=purchase.listing_id,
            buyer_id=purchase.buyer_id,
            seller_id=purchase.seller_id,
            price_paid=purchase.price_paid,
            seller_revenue=purchase.seller_revenue,
            platform_fee=purchase.platform_fee,
            fork_royalty=purchase.fork_royalty,
            license_granted=purchase.license_granted,
            is_active=purchase.is_active,
            created_at=purchase.created_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Marketplace operation"))


@router.get("/purchases", response_model=PurchaseListResponse)
async def list_purchases(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's purchases."""
    service = MarketplaceService(db)

    offset = (page - 1) * page_size
    purchases, total = await service.list_purchases_by_buyer(
        buyer_id=user["id"],
        limit=page_size,
        offset=offset,
    )

    return PurchaseListResponse(
        purchases=[
            PurchaseResponse(
                id=p.id,
                listing_id=p.listing_id,
                buyer_id=p.buyer_id,
                seller_id=p.seller_id,
                price_paid=p.price_paid,
                seller_revenue=p.seller_revenue,
                platform_fee=p.platform_fee,
                fork_royalty=p.fork_royalty,
                license_granted=p.license_granted,
                is_active=p.is_active,
                created_at=p.created_at,
            )
            for p in purchases
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/sales", response_model=PurchaseListResponse)
async def list_sales(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's sales."""
    service = MarketplaceService(db)

    offset = (page - 1) * page_size
    purchases, total = await service.list_purchases_by_seller(
        seller_id=user["id"],
        limit=page_size,
        offset=offset,
    )

    return PurchaseListResponse(
        purchases=[
            PurchaseResponse(
                id=p.id,
                listing_id=p.listing_id,
                buyer_id=p.buyer_id,
                seller_id=p.seller_id,
                price_paid=p.price_paid,
                seller_revenue=p.seller_revenue,
                platform_fee=p.platform_fee,
                fork_royalty=p.fork_royalty,
                license_granted=p.license_granted,
                is_active=p.is_active,
                created_at=p.created_at,
            )
            for p in purchases
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


# =============================================================================
# Review Endpoints
# =============================================================================

@router.post("/purchases/{purchase_id}/review", response_model=ReviewResponse)
async def create_review(
    purchase_id: UUID,
    request: CreateReviewRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a review for a purchase."""
    service = MarketplaceService(db)

    try:
        review = await service.create_review(
            purchase_id=purchase_id,
            reviewer_id=user["id"],
            rating=request.rating,
            title=request.title,
            content=request.content,
        )

        return ReviewResponse(
            id=review.id,
            listing_id=review.listing_id,
            purchase_id=review.purchase_id,
            reviewer_id=review.reviewer_id,
            rating=review.rating,
            title=review.title,
            content=review.content,
            is_verified_purchase=review.is_verified_purchase,
            helpful_count=review.helpful_count,
            created_at=review.created_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_error_detail(e, "Marketplace operation"))


@router.get("/listings/{listing_id}/reviews", response_model=ReviewListResponse)
async def list_reviews(
    listing_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List reviews for a listing."""
    service = MarketplaceService(db)

    offset = (page - 1) * page_size
    reviews, total = await service.list_reviews(
        listing_id=listing_id,
        limit=page_size,
        offset=offset,
    )

    return ReviewListResponse(
        reviews=[
            ReviewResponse(
                id=r.id,
                listing_id=r.listing_id,
                purchase_id=r.purchase_id,
                reviewer_id=r.reviewer_id,
                rating=r.rating,
                title=r.title,
                content=r.content,
                is_verified_purchase=r.is_verified_purchase,
                helpful_count=r.helpful_count,
                created_at=r.created_at,
            )
            for r in reviews
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/reviews/{review_id}/helpful")
async def mark_review_helpful(
    review_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a review as helpful."""
    service = MarketplaceService(db)

    success = await service.mark_review_helpful(review_id)
    if not success:
        raise HTTPException(status_code=404, detail="Review not found")

    return {"success": True}


# =============================================================================
# Stats Endpoints
# =============================================================================

@router.get("/stats", response_model=SellerStatsResponse)
async def get_seller_stats(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get seller statistics."""
    service = MarketplaceService(db)

    stats = await service.get_seller_stats(user["id"])

    return SellerStatsResponse(
        total_revenue=stats["total_revenue"],
        total_purchases=stats["total_purchases"],
        active_listings=stats["active_listings"],
        average_rating=stats["average_rating"],
    )
