/**
 * Cache Tag Management for Next.js 16
 *
 * Phase 6: IP-First UX Optimization with cacheLife + ISR
 *
 * Tag naming conventions:
 * - ip:${slug} - Individual IP detail
 * - ip-rails - IP home rails/sections
 * - ip-genres - Genre list
 * - ip-catalog - Full catalog
 * - ip-popular - Popular IPs (for generateStaticParams)
 * - user:${id} - User-specific data
 * - user:${id}:history - User history
 */

// =============================================================================
// Cache Tags Constants
// =============================================================================

export const CACHE_TAGS = {
  // IP-related tags
  IP_RAILS: "ip-rails",
  IP_GENRES: "ip-genres",
  IP_CATALOG: "ip-catalog",
  IP_POPULAR: "ip-popular",

  // User-related tags (functions for dynamic IDs)
  USER_PROFILE: (userId: string) => `user:${userId}` as const,
  USER_HISTORY: (userId: string) => `user:${userId}:history` as const,

  // IP individual tags (functions for dynamic slugs)
  IP_DETAIL: (slug: string) => `ip:${slug}` as const,
  IP_PRESETS: (slug: string) => `ip:${slug}:presets` as const,
  IP_RECOMMENDATIONS: (slug: string) => `ip:${slug}:recommendations` as const,
  IP_RIGHTS: (slug: string) => `ip:${slug}:rights` as const,
} as const;

// =============================================================================
// Cache Profiles (matches next.config.ts cacheLife)
// =============================================================================

/**
 * Cache profile types defined in next.config.ts
 *
 * - 'ip': IP metadata (1h stale, 15min revalidate, 1d expire)
 * - 'editorial': Editorial content (1d stale, 1h revalidate, 1w expire)
 * - 'realtime': Real-time data (1min stale, 30s revalidate, 5min expire)
 */
export type CacheProfile = "ip" | "editorial" | "realtime";

// Profile timing reference (seconds)
export const CACHE_PROFILE_TIMINGS = {
  ip: {
    stale: 3600, // 1 hour
    revalidate: 900, // 15 minutes
    expire: 86400, // 1 day
  },
  editorial: {
    stale: 86400, // 1 day
    revalidate: 3600, // 1 hour
    expire: 604800, // 1 week
  },
  realtime: {
    stale: 60, // 1 minute
    revalidate: 30, // 30 seconds
    expire: 300, // 5 minutes
  },
} as const;

// =============================================================================
// ISR Revalidation Times (seconds)
// =============================================================================

export const REVALIDATE_TIMES = {
  /** IP catalog and detail pages - 15 minutes */
  IP_PAGES: 900,
  /** Editorial content - 1 hour */
  EDITORIAL: 3600,
  /** Frequently changing data - 5 minutes */
  DYNAMIC: 300,
} as const;

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get all tags for a specific IP (for bulk invalidation)
 */
export function getIPTags(slug: string): string[] {
  return [
    CACHE_TAGS.IP_DETAIL(slug),
    CACHE_TAGS.IP_PRESETS(slug),
    CACHE_TAGS.IP_RECOMMENDATIONS(slug),
    CACHE_TAGS.IP_RIGHTS(slug),
  ];
}

/**
 * Get all catalog-related tags (for bulk catalog invalidation)
 */
export function getCatalogTags(): string[] {
  return [
    CACHE_TAGS.IP_RAILS,
    CACHE_TAGS.IP_GENRES,
    CACHE_TAGS.IP_CATALOG,
    CACHE_TAGS.IP_POPULAR,
  ];
}

/**
 * Get all user-related tags (for user data invalidation)
 */
export function getUserTags(userId: string): string[] {
  return [CACHE_TAGS.USER_PROFILE(userId), CACHE_TAGS.USER_HISTORY(userId)];
}
