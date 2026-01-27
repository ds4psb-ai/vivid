"""Homepage API Schemas.

Schemas for homepage data endpoints:
- Featured IP for hero section
- Characters for chat
- Cinema cards for user AI cinema
- Creators for human cloud CTA
- Variations for dimension apps grid
"""
from typing import Optional
from pydantic import BaseModel, ConfigDict


class FeaturedCharacter(BaseModel):
    """Character card for hero section."""
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str
    status: str
    image_url: Optional[str] = None


class FeaturedIPResponse(BaseModel):
    """Featured IP for cinematic hero section."""
    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    title_accent: str
    description: str
    banner_url: str
    tags: list[str]
    rating: float
    remix_count: str
    match_percent: int
    character: Optional[FeaturedCharacter] = None


class HomepageCharacter(BaseModel):
    """Character card for featured characters section."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    image_url: str
    chat_count: str
    quote: str
    creator: str
    badge: Optional[str] = None  # "NEW" | "TOP_RATED"
    category: Optional[str] = None


class CreatorInfo(BaseModel):
    """Creator info for cinema card."""
    name: str
    avatar_url: str


class CinemaCard(BaseModel):
    """Cinema card for user AI cinema section."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    thumbnail_url: str
    duration: str
    category: str
    category_color: str
    creator: CreatorInfo
    views: str
    like_percent: float


class HomepageCreator(BaseModel):
    """Creator card for human cloud CTA section."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    initial: str
    name: str
    specialty: str
    specialty_color: str  # "primary" | "blue" | "green"
    rating: float
    description: str


class VariationCard(BaseModel):
    """Variation card for bento grid."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    thumbnail_url: str
    category: str  # "visual" | "video" | "story" | "audio" | "interactive"
    badge: Optional[str] = None
    badge_color: Optional[str] = None
    href: str
    layout: Optional[str] = None  # "tall" | "wide" | "normal"


class HomepageDataResponse(BaseModel):
    """Combined homepage data response."""
    featured: Optional[FeaturedIPResponse] = None
    characters: list[HomepageCharacter] = []
    cinema: list[CinemaCard] = []
    creators: list[HomepageCreator] = []
    variations: list[VariationCard] = []


class CharacterListParams(BaseModel):
    """Query parameters for character list."""
    search: Optional[str] = None
    category: Optional[str] = None
    page: int = 1
    page_size: int = 20


class CharacterListResponse(BaseModel):
    """Paginated character list response."""
    items: list[HomepageCharacter]
    total: int
    page: int
    page_size: int
    has_more: bool
