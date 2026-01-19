/**
 * IP Detail Loading Fallback
 *
 * Phase 6: Next.js 16 Cache Components
 *
 * Displays a skeleton loading state that matches the actual IP detail layout.
 * Used as the Suspense fallback in the page component.
 *
 * Best Practice: Skeleton should mirror final UI to prevent layout shift.
 */

// Skeleton pulse animation class
const skeletonClass = "animate-pulse bg-[var(--bg-2)] rounded";

// Preset card skeleton
function PresetCardSkeleton() {
  return (
    <div className="border border-[var(--border)] rounded-lg p-4">
      {/* Thumbnail */}
      <div className={`${skeletonClass} w-full aspect-video mb-3`} />
      {/* Title */}
      <div className={`${skeletonClass} h-5 w-2/3 mb-2`} />
      {/* Description */}
      <div className={`${skeletonClass} h-4 w-full mb-1`} />
      <div className={`${skeletonClass} h-4 w-3/4 mb-3`} />
      {/* Credits & Duration */}
      <div className="flex justify-between">
        <div className={`${skeletonClass} h-4 w-20`} />
        <div className={`${skeletonClass} h-4 w-16`} />
      </div>
    </div>
  );
}

// Tool recommendation skeleton
function RecommendationSkeleton() {
  return (
    <div className="border border-[var(--border)] rounded-lg p-4">
      <div className={`${skeletonClass} h-5 w-1/2 mb-2`} />
      <div className={`${skeletonClass} h-4 w-full mb-1`} />
      <div className={`${skeletonClass} h-4 w-2/3`} />
    </div>
  );
}

export function IPDetailFallback() {
  return (
    <div className="min-h-screen bg-[var(--bg-0)]">
      {/* Banner skeleton */}
      <div className={`${skeletonClass} w-full h-64`} />

      <div className="max-w-7xl mx-auto px-4 -mt-16 relative z-10">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Left column - IP Info */}
          <div className="lg:w-2/3">
            {/* Header card */}
            <div className="bg-[var(--bg-1)] rounded-lg p-6 mb-6 shadow-lg">
              <div className="flex gap-4">
                {/* Thumbnail */}
                <div className={`${skeletonClass} w-32 h-48 flex-shrink-0`} />

                <div className="flex-1">
                  {/* Title */}
                  <div className={`${skeletonClass} h-8 w-2/3 mb-2`} />
                  {/* Subtitle */}
                  <div className={`${skeletonClass} h-5 w-1/3 mb-4`} />
                  {/* Tags */}
                  <div className="flex gap-2 mb-4">
                    <div className={`${skeletonClass} h-6 w-16`} />
                    <div className={`${skeletonClass} h-6 w-20`} />
                    <div className={`${skeletonClass} h-6 w-14`} />
                  </div>
                  {/* Description */}
                  <div className={`${skeletonClass} h-4 w-full mb-1`} />
                  <div className={`${skeletonClass} h-4 w-full mb-1`} />
                  <div className={`${skeletonClass} h-4 w-2/3`} />
                </div>
              </div>
            </div>

            {/* Presets section */}
            <div className="mb-6">
              <div className={`${skeletonClass} h-6 w-32 mb-4`} />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <PresetCardSkeleton />
                <PresetCardSkeleton />
                <PresetCardSkeleton />
                <PresetCardSkeleton />
              </div>
            </div>
          </div>

          {/* Right column - Generation panel */}
          <div className="lg:w-1/3">
            <div className="bg-[var(--bg-1)] rounded-lg p-6 sticky top-4 shadow-lg">
              {/* Selected preset */}
              <div className={`${skeletonClass} h-6 w-40 mb-4`} />
              <div className={`${skeletonClass} w-full aspect-video mb-4`} />

              {/* Prompt input */}
              <div className={`${skeletonClass} h-24 w-full mb-4`} />

              {/* Generate button */}
              <div className={`${skeletonClass} h-12 w-full mb-6`} />

              {/* Recommendations */}
              <div className={`${skeletonClass} h-5 w-32 mb-3`} />
              <div className="space-y-3">
                <RecommendationSkeleton />
                <RecommendationSkeleton />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Loading indicator (accessible) */}
      <div className="sr-only" role="status" aria-live="polite">
        Loading IP details...
      </div>
    </div>
  );
}
