/**
 * IP Catalog Server Component
 *
 * Phase 6: Next.js 16 Cache Components
 *
 * This server component fetches IP catalog data with caching and passes it
 * to the client component for interactivity.
 *
 * Features:
 * - ISR with 15-minute revalidation for rails, 1-hour for genres
 * - Retry with exponential backoff for transient failures
 * - Graceful fallback to empty data on persistent failures
 *
 * Caching Strategy:
 * - When cacheComponents is disabled: Uses traditional ISR with `next: { revalidate }`
 * - When cacheComponents is enabled: Uses "use cache" + cacheLife (uncomment TODOs)
 */

import IPCatalogClient, {
  type HomeRailSectionData,
  type Genre,
} from "./IPCatalogClient";
import { REVALIDATE_TIMES } from "@/lib/cache-tags";
import { fetchWithRetry } from "@/lib/fetch-utils";

// =============================================================================
// API Base URL
// =============================================================================

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

// =============================================================================
// API Response Types
// =============================================================================

interface HomeRailResponse {
  sections: HomeRailSectionData[];
}

interface GenresResponse {
  genres: Genre[];
}

// =============================================================================
// Cached Data Fetchers (ISR mode with retry)
// =============================================================================

/**
 * Fetch IP home rails with ISR caching and retry
 * Revalidates every 15 minutes
 */
async function getCachedIPRails(): Promise<HomeRailSectionData[]> {
  // TODO: Enable "use cache" when cacheComponents is enabled
  // "use cache";
  // cacheLife("ip");
  // cacheTag(CACHE_TAGS.IP_RAILS);

  const result = await fetchWithRetry<HomeRailResponse>(
    `${API_URL}/api/v1/ip/home/rails`,
    {
      headers: {
        "Content-Type": "application/json",
      },
      // ISR: Revalidate every 15 minutes
      next: { revalidate: REVALIDATE_TIMES.IP_PAGES },
      // Retry config
      maxRetries: 3,
      baseDelay: 1000,
      timeout: 15000,
    }
  );

  if (result.error) {
    console.error(
      `[IPCatalogServer] Failed to fetch rails after ${result.retries} retries:`,
      result.error
    );
    return [];
  }

  return result.data?.sections || [];
}

/**
 * Fetch IP genres with ISR caching and retry
 * Revalidates every hour (editorial content changes less frequently)
 */
async function getCachedGenres(): Promise<Genre[]> {
  // TODO: Enable "use cache" when cacheComponents is enabled
  // "use cache";
  // cacheLife("editorial");
  // cacheTag(CACHE_TAGS.IP_GENRES);

  const result = await fetchWithRetry<GenresResponse>(
    `${API_URL}/api/v1/ip/genres`,
    {
      headers: {
        "Content-Type": "application/json",
      },
      // ISR: Revalidate every hour
      next: { revalidate: REVALIDATE_TIMES.EDITORIAL },
      // Retry config
      maxRetries: 3,
      baseDelay: 1000,
      timeout: 15000,
    }
  );

  if (result.error) {
    console.error(
      `[IPCatalogServer] Failed to fetch genres after ${result.retries} retries:`,
      result.error
    );
    return [];
  }

  return result.data?.genres || [];
}

// =============================================================================
// Server Component
// =============================================================================

/**
 * IP Catalog Server Component
 *
 * Fetches initial data with caching and passes to client for interactivity.
 * The client component handles:
 * - Search and filtering
 * - Pagination
 * - View mode switching
 */
export async function IPCatalogServer() {
  // Fetch cached data in parallel
  const [rails, genres] = await Promise.all([
    getCachedIPRails(),
    getCachedGenres(),
  ]);

  return <IPCatalogClient initialRails={rails} initialGenres={genres} />;
}
