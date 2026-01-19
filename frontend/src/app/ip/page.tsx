/**
 * IP Catalog Page
 *
 * Phase 6: Next.js 16 Cache Components + ISR
 *
 * This page uses ISR (Incremental Static Regeneration) to:
 * - Pre-render with cached data at build time
 * - Revalidate every 15 minutes in the background
 * - Serve cached HTML for fast initial load
 *
 * The server component fetches rails and genres with caching,
 * while the client component handles interactivity.
 */

import type { Metadata } from "next";
import { Suspense } from "react";
import { IPCatalogServer } from "./_components/IPCatalogServer";
import { IPCatalogFallback } from "./_components/IPCatalogFallback";

// =============================================================================
// Page Configuration
// =============================================================================

// Note: With cacheComponents enabled, caching is controlled via "use cache" directive
// and cacheLife() in server components, not via route segment config.
// See IPCatalogServer.tsx for cache configuration.

export const metadata: Metadata = {
  title: "IP Gallery | Crebit",
  description: "Browse IP catalog and create AI fan-fiction videos",
  openGraph: {
    title: "IP Gallery | Crebit",
    description: "Browse IP catalog and create AI fan-fiction videos",
    type: "website",
  },
};

// =============================================================================
// Page Component
// =============================================================================

export default function IPCatalogPage() {
  return (
    <Suspense fallback={<IPCatalogFallback />}>
      <IPCatalogServer />
    </Suspense>
  );
}
