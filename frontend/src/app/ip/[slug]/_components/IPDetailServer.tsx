/**
 * IP Detail Server Component
 *
 * Phase 6: Next.js 16 Cache Components
 *
 * This server component fetches IP detail data with caching and passes it
 * to the client component for interactivity.
 *
 * Caching Strategy:
 * - When cacheComponents is disabled: Uses traditional ISR with `next: { revalidate }`
 * - When cacheComponents is enabled: Uses "use cache" + cacheLife (uncomment)
 *
 * TODO: Enable "use cache" once cacheComponents is enabled globally
 */

import IPDetailClient, {
  type IPDetail,
  type IPRights,
} from "./IPDetailClient";
import { REVALIDATE_TIMES } from "@/lib/cache-tags";

// =============================================================================
// API Base URL
// =============================================================================

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

// =============================================================================
// Cached Data Fetchers (ISR mode)
// =============================================================================

/**
 * Fetch IP detail with ISR caching
 * Revalidates every 15 minutes
 */
async function getCachedIPDetail(slug: string): Promise<IPDetail | null> {
  // TODO: Enable "use cache" when cacheComponents is enabled
  // "use cache";
  // cacheLife("ip");
  // cacheTag(CACHE_TAGS.IP_DETAIL(slug));

  try {
    const res = await fetch(`${API_URL}/api/v1/ip/catalog/${slug}`, {
      headers: {
        "Content-Type": "application/json",
      },
      // ISR: Revalidate every 15 minutes
      next: { revalidate: REVALIDATE_TIMES.IP_PAGES },
    });

    if (!res.ok) {
      console.error(
        `[IPDetailServer] Failed to fetch IP detail for ${slug}:`,
        res.status
      );
      return null;
    }

    return await res.json();
  } catch (error) {
    console.error(`[IPDetailServer] Error fetching IP detail for ${slug}:`, error);
    return null;
  }
}

/**
 * Fetch IP rights with ISR caching
 * Revalidates every 15 minutes
 */
async function getCachedIPRights(slug: string): Promise<IPRights | null> {
  // TODO: Enable "use cache" when cacheComponents is enabled
  // "use cache";
  // cacheLife("ip");
  // cacheTag(CACHE_TAGS.IP_RIGHTS(slug));

  try {
    const res = await fetch(`${API_URL}/api/v1/ip/catalog/${slug}/rights`, {
      headers: {
        "Content-Type": "application/json",
      },
      // ISR: Revalidate every 15 minutes
      next: { revalidate: REVALIDATE_TIMES.IP_PAGES },
    });

    if (!res.ok) {
      // Rights might not exist for all IPs, so this is not an error
      return null;
    }

    return await res.json();
  } catch (error) {
    console.error(`[IPDetailServer] Error fetching IP rights for ${slug}:`, error);
    return null;
  }
}

// =============================================================================
// Server Component
// =============================================================================

export interface IPDetailServerProps {
  slug: string;
}

/**
 * IP Detail Server Component
 *
 * Fetches IP detail and rights with caching, passes to client for interactivity.
 * The client component handles:
 * - Preset selection
 * - Generation flow
 * - Tool recommendations
 * - License acceptance
 */
export async function IPDetailServer({ slug }: IPDetailServerProps) {
  // Fetch cached data in parallel
  const [ip, rights] = await Promise.all([
    getCachedIPDetail(slug),
    getCachedIPRights(slug),
  ]);

  return <IPDetailClient slug={slug} initialIP={ip} initialRights={rights} />;
}
