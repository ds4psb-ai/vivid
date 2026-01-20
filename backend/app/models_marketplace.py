"""Marketplace Models for Phase 10 IP Licensing.

This module defines models for the IP marketplace:
- MarketplaceListing: IP listing for licensing
- MarketplacePurchase: Purchase records
- MarketplaceReview: User reviews
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, Float, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MarketplaceListing(Base):
    """Marketplace Listing - IP available for licensing.

    Revenue split: Creator 60% / Platform 30% / Fork Original 10%
    """
    __tablename__ = "marketplace_listings"
    __table_args__ = (
        Index("ix_marketplace_ip", "ip_id"),
        Index("ix_marketplace_seller", "seller_id"),
        Index("ix_marketplace_tier", "license_tier"),
        Index("ix_marketplace_status", "status"),
        Index("ix_marketplace_featured", "is_featured", "is_verified"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ip_catalog.id", ondelete="CASCADE"), nullable=False)
    seller_id: Mapped[str] = mapped_column(String(160), nullable=False)

    # Display info
    title_ko: Mapped[str] = mapped_column(String(200), nullable=False)
    title_en: Mapped[str] = mapped_column(String(200), nullable=False)
    description_ko: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Licensing
    license_tier: Mapped[str] = mapped_column(String(32), default="free")  # free, commercial, exclusive
    price_credits: Mapped[int] = mapped_column(Integer, default=0)  # One-time price
    royalty_percent: Mapped[int] = mapped_column(Integer, default=0)  # Per-use royalty

    # Rights
    usage_rights: Mapped[list] = mapped_column(JSONB, default=list)  # [chat, generation, commercial]
    territory_restrictions: Mapped[list] = mapped_column(JSONB, default=list)  # Country codes

    # Stats
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    purchase_count: Mapped[int] = mapped_column(Integer, default=0)
    average_rating: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="draft")  # draft, pending, active, suspended

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    purchases: Mapped[List["MarketplacePurchase"]] = relationship("MarketplacePurchase", back_populates="listing", cascade="all, delete-orphan")
    reviews: Mapped[List["MarketplaceReview"]] = relationship("MarketplaceReview", back_populates="listing", cascade="all, delete-orphan")


class MarketplacePurchase(Base):
    """Marketplace Purchase - License purchase record.

    Tracks revenue distribution: 60/30/10 split.
    """
    __tablename__ = "marketplace_purchases"
    __table_args__ = (
        Index("ix_purchase_listing", "listing_id"),
        Index("ix_purchase_buyer", "buyer_id"),
        Index("ix_purchase_seller", "seller_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("marketplace_listings.id", ondelete="CASCADE"), nullable=False)
    buyer_id: Mapped[str] = mapped_column(String(160), nullable=False)
    seller_id: Mapped[str] = mapped_column(String(160), nullable=False)

    # Revenue breakdown
    price_paid: Mapped[int] = mapped_column(Integer, nullable=False)
    seller_revenue: Mapped[int] = mapped_column(Integer, nullable=False)  # 60%
    platform_fee: Mapped[int] = mapped_column(Integer, nullable=False)  # 30%
    fork_royalty: Mapped[int] = mapped_column(Integer, default=0)  # 10% (if applicable)

    # License details
    license_granted: Mapped[list] = mapped_column(JSONB, default=list)  # Copy of usage_rights at purchase time
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    listing: Mapped["MarketplaceListing"] = relationship("MarketplaceListing", back_populates="purchases")
    review: Mapped[Optional["MarketplaceReview"]] = relationship("MarketplaceReview", back_populates="purchase", uselist=False)


class MarketplaceReview(Base):
    """Marketplace Review - User review for a listing.

    One review per purchase (verified purchase).
    """
    __tablename__ = "marketplace_reviews"
    __table_args__ = (
        Index("ix_review_listing", "listing_id"),
        UniqueConstraint("purchase_id", name="uq_review_purchase"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("marketplace_listings.id", ondelete="CASCADE"), nullable=False)
    purchase_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("marketplace_purchases.id", ondelete="CASCADE"), nullable=False)
    reviewer_id: Mapped[str] = mapped_column(String(160), nullable=False)

    # Review content
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    is_verified_purchase: Mapped[bool] = mapped_column(Boolean, default=True)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    listing: Mapped["MarketplaceListing"] = relationship("MarketplaceListing", back_populates="reviews")
    purchase: Mapped["MarketplacePurchase"] = relationship("MarketplacePurchase", back_populates="review")
