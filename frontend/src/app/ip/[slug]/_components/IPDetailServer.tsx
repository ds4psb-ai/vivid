/**
 * IP Detail Server Component
 *
 * Phase 6: Next.js 16 Cache Components
 *
 * This server component fetches IP detail data with caching and passes it
 * to the client component for interactivity.
 *
 * Features:
 * - ISR with 15-minute revalidation
 * - Retry with exponential backoff for transient failures
 * - Graceful fallback to null on persistent failures (client will retry)
 *
 * Caching Strategy:
 * - When cacheComponents is disabled: Uses traditional ISR with `next: { revalidate }`
 * - When cacheComponents is enabled: Uses "use cache" + cacheLife (uncomment TODOs)
 */

import IPDetailClient, {
  type IPDetail,
  type IPRights,
} from "./IPDetailClient";
import { REVALIDATE_TIMES } from "@/lib/cache-tags";
import { fetchWithRetry } from "@/lib/fetch-utils";

// =============================================================================
// API Base URL
// =============================================================================

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

// =============================================================================
// Cached Data Fetchers (ISR mode with retry)
// =============================================================================

/**
 * Fetch IP detail with ISR caching and retry
 * Revalidates every 15 minutes
 */
async function getCachedIPDetail(slug: string): Promise<IPDetail | null> {
  // TODO: Enable "use cache" when cacheComponents is enabled
  // "use cache";
  // cacheLife("ip");
  // cacheTag(CACHE_TAGS.IP_DETAIL(slug));

  const result = await fetchWithRetry<IPDetail>(
    `${API_URL}/api/v1/ip/catalog/${encodeURIComponent(slug)}`,
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
    // 404 is expected for invalid slugs, don't log as error
    if (result.status === 404) {
      console.warn(`[IPDetailServer] IP not found: ${slug}`);
    } else {
      console.error(
        `[IPDetailServer] Failed to fetch IP detail for ${slug} after ${result.retries} retries:`,
        result.error
      );
    }
    return null;
  }

  return result.data;
}

/**
 * Fetch IP rights with ISR caching and retry
 * Revalidates every 15 minutes
 */
async function getCachedIPRights(slug: string): Promise<IPRights | null> {
  // TODO: Enable "use cache" when cacheComponents is enabled
  // "use cache";
  // cacheLife("ip");
  // cacheTag(CACHE_TAGS.IP_RIGHTS(slug));

  const result = await fetchWithRetry<IPRights>(
    `${API_URL}/api/v1/ip/catalog/${encodeURIComponent(slug)}/rights`,
    {
      headers: {
        "Content-Type": "application/json",
      },
      // ISR: Revalidate every 15 minutes
      next: { revalidate: REVALIDATE_TIMES.IP_PAGES },
      // Retry config - fewer retries for rights since it may legitimately not exist
      maxRetries: 2,
      baseDelay: 500,
      timeout: 10000,
    }
  );

  if (result.error) {
    // Rights might not exist for all IPs, so 404 is not an error
    if (result.status !== 404) {
      console.error(
        `[IPDetailServer] Failed to fetch IP rights for ${slug} after ${result.retries} retries:`,
        result.error
      );
    }
    return null;
  }

  return result.data;
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
