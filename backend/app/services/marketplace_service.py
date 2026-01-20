"""Marketplace Service for Phase 10 IP Licensing.

Handles IP listing, purchases, and revenue distribution.

Revenue split: Creator 60% / Platform 30% / Fork Original 10%

Based on: SSOT_DECISIONS_LOG.md Phase 10 design
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_ip import IPCatalog
from app.models_marketplace import MarketplaceListing, MarketplacePurchase, MarketplaceReview

logger = logging.getLogger(__name__)


# Revenue split percentages
SELLER_SHARE_PERCENT = 60
PLATFORM_SHARE_PERCENT = 30
FORK_SHARE_PERCENT = 10


class MarketplaceService:
    """Service for IP marketplace operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Listing Management
    # =========================================================================

    async def create_listing(
        self,
        seller_id: str,
        ip_id: uuid.UUID,
        title_ko: str,
        title_en: str,
        description_ko: Optional[str] = None,
        description_en: Optional[str] = None,
        license_tier: str = "free",
        price_credits: int = 0,
        royalty_percent: int = 0,
        usage_rights: Optional[List[str]] = None,
        territory_restrictions: Optional[List[str]] = None,
    ) -> MarketplaceListing:
        """Create a new marketplace listing.

        Args:
            seller_id: Seller user ID
            ip_id: IP catalog entry ID
            title_ko: Korean title
            title_en: English title
            description_ko: Korean description
            description_en: English description
            license_tier: free, commercial, exclusive
            price_credits: One-time price in credits
            royalty_percent: Per-use royalty percentage
            usage_rights: List of granted rights (chat, generation, commercial)
            territory_restrictions: List of restricted country codes

        Returns:
            Created listing
        """
        # Verify IP exists and seller owns it
        ip = await self.db.get(IPCatalog, ip_id)
        if not ip:
            raise ValueError(f"IP not found: {ip_id}")

        # Check for existing listing
        existing = await self.db.execute(
            select(MarketplaceListing).where(
                MarketplaceListing.ip_id == ip_id,
                MarketplaceListing.seller_id == seller_id,
                MarketplaceListing.status != "suspended",
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Listing already exists for this IP")

        listing = MarketplaceListing(
            ip_id=ip_id,
            seller_id=seller_id,
            title_ko=title_ko,
            title_en=title_en,
            description_ko=description_ko,
            description_en=description_en,
            license_tier=license_tier,
            price_credits=price_credits,
            royalty_percent=royalty_percent,
            usage_rights=usage_rights or ["chat"],
            territory_restrictions=territory_restrictions or [],
            status="pending",  # Requires review before active
        )

        self.db.add(listing)
        await self.db.commit()

        # Update IP with marketplace listing reference
        ip.marketplace_listing_id = listing.id
        await self.db.commit()

        logger.info(f"Created marketplace listing {listing.id} for IP {ip.slug}")
        return listing

    async def get_listing(self, listing_id: uuid.UUID) -> Optional[MarketplaceListing]:
        """Get a listing by ID."""
        return await self.db.get(MarketplaceListing, listing_id)

    async def get_listing_by_ip(self, ip_id: uuid.UUID) -> Optional[MarketplaceListing]:
        """Get the active listing for an IP."""
        result = await self.db.execute(
            select(MarketplaceListing).where(
                MarketplaceListing.ip_id == ip_id,
                MarketplaceListing.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def list_listings(
        self,
        license_tier: Optional[str] = None,
        is_featured: Optional[bool] = None,
        search_query: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "popular",  # popular, recent, price_low, price_high
    ) -> Tuple[List[MarketplaceListing], int]:
        """List marketplace listings with filters.

        Returns:
            Tuple of (listings, total_count)
        """
        query = select(MarketplaceListing).where(MarketplaceListing.status == "active")

        if license_tier:
            query = query.where(MarketplaceListing.license_tier == license_tier)

        if is_featured is not None:
            query = query.where(MarketplaceListing.is_featured == is_featured)

        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.where(
                or_(
                    MarketplaceListing.title_ko.ilike(search_pattern),
                    MarketplaceListing.title_en.ilike(search_pattern),
                )
            )

        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Apply sorting
        if sort_by == "recent":
            query = query.order_by(desc(MarketplaceListing.created_at))
        elif sort_by == "price_low":
            query = query.order_by(MarketplaceListing.price_credits)
        elif sort_by == "price_high":
            query = query.order_by(desc(MarketplaceListing.price_credits))
        else:  # popular
            query = query.order_by(
                desc(MarketplaceListing.purchase_count),
                desc(MarketplaceListing.view_count),
            )

        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        listings = list(result.scalars().all())

        return listings, total

    async def update_listing(
        self,
        listing_id: uuid.UUID,
        seller_id: str,
        **updates,
    ) -> Optional[MarketplaceListing]:
        """Update a listing (only seller can update)."""
        listing = await self.get_listing(listing_id)
        if not listing or listing.seller_id != seller_id:
            return None

        allowed_fields = {
            "title_ko", "title_en", "description_ko", "description_en",
            "license_tier", "price_credits", "royalty_percent",
            "usage_rights", "territory_restrictions",
        }

        for key, value in updates.items():
            if key in allowed_fields:
                setattr(listing, key, value)

        listing.updated_at = datetime.utcnow()
        await self.db.commit()

        return listing

    async def approve_listing(self, listing_id: uuid.UUID) -> bool:
        """Approve a pending listing (admin only)."""
        listing = await self.get_listing(listing_id)
        if not listing or listing.status != "pending":
            return False

        listing.status = "active"
        listing.updated_at = datetime.utcnow()
        await self.db.commit()

        return True

    async def increment_view_count(self, listing_id: uuid.UUID) -> None:
        """Increment view count for a listing."""
        listing = await self.get_listing(listing_id)
        if listing:
            listing.view_count += 1
            await self.db.commit()

    # =========================================================================
    # Purchase Management
    # =========================================================================

    async def purchase_listing(
        self,
        listing_id: uuid.UUID,
        buyer_id: str,
        fork_original_creator_id: Optional[str] = None,
    ) -> MarketplacePurchase:
        """Purchase a marketplace listing.

        Args:
            listing_id: Listing to purchase
            buyer_id: Buyer user ID
            fork_original_creator_id: Optional original creator for fork royalty

        Returns:
            Purchase record
        """
        listing = await self.get_listing(listing_id)
        if not listing or listing.status != "active":
            raise ValueError("Listing not available for purchase")

        if listing.seller_id == buyer_id:
            raise ValueError("Cannot purchase your own listing")

        # Check for existing purchase
        existing = await self.db.execute(
            select(MarketplacePurchase).where(
                MarketplacePurchase.listing_id == listing_id,
                MarketplacePurchase.buyer_id == buyer_id,
                MarketplacePurchase.is_active == True,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Already purchased this listing")

        # Calculate revenue split
        price = listing.price_credits
        seller_revenue = int(price * SELLER_SHARE_PERCENT / 100)
        platform_fee = int(price * PLATFORM_SHARE_PERCENT / 100)
        fork_royalty = 0

        if fork_original_creator_id:
            fork_royalty = int(price * FORK_SHARE_PERCENT / 100)
            # Adjust seller revenue to account for fork royalty
            seller_revenue = price - platform_fee - fork_royalty

        purchase = MarketplacePurchase(
            listing_id=listing_id,
            buyer_id=buyer_id,
            seller_id=listing.seller_id,
            price_paid=price,
            seller_revenue=seller_revenue,
            platform_fee=platform_fee,
            fork_royalty=fork_royalty,
            license_granted=listing.usage_rights,
        )

        self.db.add(purchase)

        # Update listing stats
        listing.purchase_count += 1

        await self.db.commit()

        logger.info(
            f"Purchase {purchase.id} completed: buyer={buyer_id}, "
            f"seller_revenue={seller_revenue}, platform_fee={platform_fee}"
        )

        return purchase

    async def get_purchase(self, purchase_id: uuid.UUID) -> Optional[MarketplacePurchase]:
        """Get a purchase by ID."""
        return await self.db.get(MarketplacePurchase, purchase_id)

    async def list_purchases_by_buyer(
        self,
        buyer_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[MarketplacePurchase], int]:
        """List purchases made by a buyer."""
        query = select(MarketplacePurchase).where(
            MarketplacePurchase.buyer_id == buyer_id,
            MarketplacePurchase.is_active == True,
        )

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        query = query.order_by(desc(MarketplacePurchase.created_at)).offset(offset).limit(limit)
        result = await self.db.execute(query)
        purchases = list(result.scalars().all())

        return purchases, total

    async def list_purchases_by_seller(
        self,
        seller_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[MarketplacePurchase], int]:
        """List purchases of a seller's listings."""
        query = select(MarketplacePurchase).where(
            MarketplacePurchase.seller_id == seller_id,
        )

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        query = query.order_by(desc(MarketplacePurchase.created_at)).offset(offset).limit(limit)
        result = await self.db.execute(query)
        purchases = list(result.scalars().all())

        return purchases, total

    async def check_license(
        self,
        buyer_id: str,
        ip_id: uuid.UUID,
        required_right: str = "chat",
    ) -> bool:
        """Check if user has purchased license for an IP with required right."""
        # Get active listing for IP
        listing = await self.get_listing_by_ip(ip_id)
        if not listing:
            return True  # No listing means free access

        if listing.license_tier == "free":
            return True

        # Check for active purchase
        result = await self.db.execute(
            select(MarketplacePurchase).where(
                MarketplacePurchase.listing_id == listing.id,
                MarketplacePurchase.buyer_id == buyer_id,
                MarketplacePurchase.is_active == True,
            )
        )
        purchase = result.scalar_one_or_none()
        if not purchase:
            return False

        return required_right in (purchase.license_granted or [])

    # =========================================================================
    # Review Management
    # =========================================================================

    async def create_review(
        self,
        purchase_id: uuid.UUID,
        reviewer_id: str,
        rating: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
    ) -> MarketplaceReview:
        """Create a review for a purchase.

        Args:
            purchase_id: Purchase to review
            reviewer_id: Reviewer user ID
            rating: 1-5 star rating
            title: Review title
            content: Review content

        Returns:
            Created review
        """
        purchase = await self.get_purchase(purchase_id)
        if not purchase:
            raise ValueError("Purchase not found")

        if purchase.buyer_id != reviewer_id:
            raise ValueError("Only buyer can review this purchase")

        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        # Check for existing review
        existing = await self.db.execute(
            select(MarketplaceReview).where(
                MarketplaceReview.purchase_id == purchase_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Review already exists for this purchase")

        review = MarketplaceReview(
            listing_id=purchase.listing_id,
            purchase_id=purchase_id,
            reviewer_id=reviewer_id,
            rating=rating,
            title=title,
            content=content,
        )

        self.db.add(review)

        # Update listing average rating
        listing = await self.get_listing(purchase.listing_id)
        if listing:
            # Calculate new average
            total_rating = listing.average_rating * listing.rating_count + rating
            listing.rating_count += 1
            listing.average_rating = total_rating / listing.rating_count

        await self.db.commit()

        return review

    async def list_reviews(
        self,
        listing_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[MarketplaceReview], int]:
        """List reviews for a listing."""
        query = select(MarketplaceReview).where(
            MarketplaceReview.listing_id == listing_id,
        )

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        query = query.order_by(desc(MarketplaceReview.created_at)).offset(offset).limit(limit)
        result = await self.db.execute(query)
        reviews = list(result.scalars().all())

        return reviews, total

    async def mark_review_helpful(self, review_id: uuid.UUID) -> bool:
        """Increment helpful count for a review."""
        review = await self.db.get(MarketplaceReview, review_id)
        if not review:
            return False

        review.helpful_count += 1
        await self.db.commit()
        return True

    # =========================================================================
    # Analytics
    # =========================================================================

    async def get_seller_stats(self, seller_id: str) -> Dict:
        """Get seller statistics."""
        # Total revenue
        revenue_result = await self.db.execute(
            select(func.sum(MarketplacePurchase.seller_revenue)).where(
                MarketplacePurchase.seller_id == seller_id,
            )
        )
        total_revenue = revenue_result.scalar() or 0

        # Total purchases
        purchase_result = await self.db.execute(
            select(func.count()).where(
                MarketplacePurchase.seller_id == seller_id,
            )
        )
        total_purchases = purchase_result.scalar() or 0

        # Active listings
        listing_result = await self.db.execute(
            select(func.count()).where(
                MarketplaceListing.seller_id == seller_id,
                MarketplaceListing.status == "active",
            )
        )
        active_listings = listing_result.scalar() or 0

        # Average rating across all listings
        avg_rating_result = await self.db.execute(
            select(func.avg(MarketplaceListing.average_rating)).where(
                MarketplaceListing.seller_id == seller_id,
                MarketplaceListing.rating_count > 0,
            )
        )
        avg_rating = avg_rating_result.scalar() or 0

        return {
            "total_revenue": total_revenue,
            "total_purchases": total_purchases,
            "active_listings": active_listings,
            "average_rating": round(avg_rating, 2),
        }
