/**
 * IP Catalog Loading Fallback
 *
 * Phase 6: Next.js 16 Cache Components
 *
 * Displays a skeleton loading state that matches the actual IP catalog layout.
 * Used as the Suspense fallback in the page component.
 *
 * Best Practice: Skeleton should mirror final UI to prevent layout shift.
 */

// Skeleton pulse animation class
const skeletonClass = "animate-pulse bg-[var(--bg-2)] rounded";

// Rail item skeleton
function RailItemSkeleton() {
  return (
    <div className="flex-shrink-0 w-[180px]">
      {/* Thumbnail */}
      <div className={`${skeletonClass} w-full aspect-[3/4] mb-2`} />
      {/* Title */}
      <div className={`${skeletonClass} h-4 w-3/4 mb-1`} />
      {/* Subtitle */}
      <div className={`${skeletonClass} h-3 w-1/2`} />
    </div>
  );
}

// Rail section skeleton
function RailSectionSkeleton() {
  return (
    <div className="mb-8">
      {/* Section title */}
      <div className={`${skeletonClass} h-6 w-32 mb-4`} />
      {/* Rail items */}
      <div className="flex gap-4 overflow-hidden">
        {Array.from({ length: 6 }).map((_, i) => (
          <RailItemSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}

export function IPCatalogFallback() {
  return (
    <div className="min-h-screen bg-[var(--bg-0)]">
      {/* Header skeleton */}
      <div className="border-b border-[var(--border)]">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Title */}
            <div className={`${skeletonClass} h-8 w-40`} />
            {/* Search bar */}
            <div className={`${skeletonClass} h-10 w-64`} />
            {/* View toggle */}
            <div className="flex gap-2">
              <div className={`${skeletonClass} h-10 w-10`} />
              <div className={`${skeletonClass} h-10 w-10`} />
            </div>
          </div>
        </div>
      </div>

      {/* Content skeleton */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Rails - 3 sections */}
        <RailSectionSkeleton />
        <RailSectionSkeleton />
        <RailSectionSkeleton />
      </div>

      {/* Loading indicator (accessible) */}
      <div className="sr-only" role="status" aria-live="polite">
        Loading IP Gallery...
      </div>
    </div>
  );
}
