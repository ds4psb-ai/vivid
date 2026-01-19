/**
 * IP Catalog Server Component
 *
 * Phase 6: Next.js 16 Cache Components
 *
 * This server component fetches IP catalog data with caching and passes it
 * to the client component for interactivity.
 *
 * Caching Strategy:
 * - When cacheComponents is disabled: Uses traditional ISR with `next: { revalidate }`
 * - When cacheComponents is enabled: Uses "use cache" + cacheLife (uncomment)
 *
 * TODO: Enable "use cache" once cacheComponents is enabled globally
 */

import IPCatalogClient, {
  type HomeRailSectionData,
  type Genre,
} from "./IPCatalogClient";
import { REVALIDATE_TIMES } from "@/lib/cache-tags";

// =============================================================================
// API Base URL
// =============================================================================

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

// =============================================================================
// Cached Data Fetchers (ISR mode)
// =============================================================================

/**
 * Fetch IP home rails with ISR caching
 * Revalidates every 15 minutes
 */
async function getCachedIPRails(): Promise<HomeRailSectionData[]> {
  // TODO: Enable "use cache" when cacheComponents is enabled
  // "use cache";
  // cacheLife("ip");
  // cacheTag(CACHE_TAGS.IP_RAILS);

  try {
    const res = await fetch(`${API_URL}/api/v1/ip/home/rails`, {
      headers: {
        "Content-Type": "application/json",
      },
      // ISR: Revalidate every 15 minutes
      next: { revalidate: REVALIDATE_TIMES.IP_PAGES },
    });

    if (!res.ok) {
      console.error("[IPCatalogServer] Failed to fetch rails:", res.status);
      return [];
    }

    const data = await res.json();
    return data.sections || [];
  } catch (error) {
    console.error("[IPCatalogServer] Error fetching rails:", error);
    return [];
  }
}

/**
 * Fetch IP genres with ISR caching
 * Revalidates every hour (editorial content changes less frequently)
 */
async function getCachedGenres(): Promise<Genre[]> {
  // TODO: Enable "use cache" when cacheComponents is enabled
  // "use cache";
  // cacheLife("editorial");
  // cacheTag(CACHE_TAGS.IP_GENRES);

  try {
    const res = await fetch(`${API_URL}/api/v1/ip/genres`, {
      headers: {
        "Content-Type": "application/json",
      },
      // ISR: Revalidate every hour
      next: { revalidate: REVALIDATE_TIMES.EDITORIAL },
    });

    if (!res.ok) {
      console.error("[IPCatalogServer] Failed to fetch genres:", res.status);
      return [];
    }

    const data = await res.json();
    return data.genres || [];
  } catch (error) {
    console.error("[IPCatalogServer] Error fetching genres:", error);
    return [];
  }
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
