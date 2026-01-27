/**
 * Homepage API Types
 *
 * Type definitions for homepage data endpoints
 */

export interface FeaturedCharacter {
  name: string;
  description: string;
  status: string;
  imageUrl?: string;
}

export interface FeaturedIP {
  slug: string;
  title: string;
  titleAccent: string;
  description: string;
  bannerUrl: string;
  tags: string[];
  rating: number;
  remixCount: string;
  matchPercent: number;
  character?: FeaturedCharacter;
}

export interface HomepageCharacter {
  id: string;
  name: string;
  imageUrl: string;
  chatCount: string;
  quote: string;
  creator: string;
  badge?: "NEW" | "TOP_RATED";
  category?: string;
}

export interface CreatorInfo {
  name: string;
  avatarUrl: string;
}

export interface CinemaCard {
  id: string;
  title: string;
  description: string;
  thumbnailUrl: string;
  duration: string;
  category: string;
  categoryColor: string;
  creator: CreatorInfo;
  views: string;
  likePercent: number;
}

export interface HomepageCreator {
  id: string;
  initial: string;
  name: string;
  specialty: string;
  specialtyColor: "primary" | "blue" | "green";
  rating: number;
  description: string;
}

export interface VariationCard {
  id: string;
  name: string;
  description: string;
  thumbnailUrl: string;
  category: "visual" | "video" | "story" | "audio" | "interactive";
  badge?: string;
  badgeColor?: string;
  href: string;
  layout?: "tall" | "wide" | "normal";
}

export interface HomepageData {
  featured: FeaturedIP | null;
  characters: HomepageCharacter[];
  cinema: CinemaCard[];
  creators: HomepageCreator[];
  variations: VariationCard[];
}

export interface CharacterListParams {
  search?: string;
  category?: string;
  page?: number;
  pageSize?: number;
}

export interface CharacterListResponse {
  items: HomepageCharacter[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}
