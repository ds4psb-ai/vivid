/**
 * IP Detail Page
 *
 * Phase 6: Next.js 16 Cache Components + ISR
 *
 * This page uses:
 * - generateStaticParams to pre-generate popular IP pages at build time
 * - ISR to revalidate every 15 minutes
 * - Server component with caching for IP detail and rights
 *
 * Dynamic routes that aren't pre-generated will be generated on-demand
 * and cached for subsequent requests.
 */

import type { Metadata } from "next";
import { Suspense } from "react";
import { notFound } from "next/navigation";
import { IPDetailServer } from "./_components/IPDetailServer";
import { IPDetailFallback } from "./_components/IPDetailFallback";
import { fetchWithRetry } from "@/lib/fetch-utils";

// =============================================================================
// Page Configuration
// =============================================================================

// Note: With cacheComponents enabled, caching is controlled via "use cache" directive
// and cacheLife() in server components, not via route segment config.
// See IPDetailServer.tsx for cache configuration.

// =============================================================================
// API Base URL
// =============================================================================

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

// =============================================================================
// Types
// =============================================================================

interface PopularIPItem {
  id: string;
  slug: string;
  name_ko: string;
  name_en: string;
}

// =============================================================================
// Static Params Generation
// =============================================================================

/**
 * Pre-generate pages for popular IPs at build time
 * Fetches popular IP slugs for static generation with retry logic
 */
async function getPopularIPSlugs(): Promise<string[]> {
  const result = await fetchWithRetry<PopularIPItem[]>(
    `${API_URL}/api/v1/ip/popular?limit=50`,
    {
      headers: {
        "Content-Type": "application/json",
      },
      // Use next cache for build-time fetching
      next: { revalidate: 3600 }, // Revalidate every hour during builds
      // Retry config for build time
      maxRetries: 3,
      baseDelay: 2000,
      timeout: 30000,
    }
  );

  if (result.error) {
    console.warn(
      `[generateStaticParams] Failed to fetch popular IPs after ${result.retries} retries:`,
      result.error
    );
    return [];
  }

  if (!result.data || !Array.isArray(result.data)) {
    console.warn("[generateStaticParams] Invalid response format");
    return [];
  }

  return result.data.map((ip) => ip.slug);
}

/**
 * Generate static params for popular IPs
 * These pages will be pre-rendered at build time
 *
 * With cacheComponents enabled, at least one param must be returned for
 * build-time validation. Returns a placeholder if API is unavailable.
 */
export async function generateStaticParams(): Promise<{ slug: string }[]> {
  const slugs = await getPopularIPSlugs();

  // With cacheComponents, at least one result is required for build validation
  // Return placeholder if API is unavailable (will 404 gracefully at runtime)
  if (slugs.length === 0) {
    return [{ slug: "_placeholder" }];
  }

  return slugs.map((slug) => ({ slug }));
}

// =============================================================================
// Dynamic Metadata
// =============================================================================

interface PageProps {
  params: Promise<{ slug: string }>;
}

/**
 * Generate metadata for each IP page
 */
export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { slug } = await params;

  // Default metadata if IP fetch fails
  return {
    title: `IP Detail | Crebit`,
    description: "View IP details and create AI fan-fiction videos",
    openGraph: {
      title: `IP Detail | Crebit`,
      description: "View IP details and create AI fan-fiction videos",
      type: "website",
      url: `/ip/${slug}`,
    },
  };
}

// =============================================================================
// Page Component
// =============================================================================

export default async function IPDetailPage({ params }: PageProps) {
  const { slug } = await params;

  // Validate slug format
  if (!slug || typeof slug !== "string") {
    notFound();
  }

  return (
    <Suspense fallback={<IPDetailFallback />}>
      <IPDetailServer slug={slug} />
    </Suspense>
  );
}
