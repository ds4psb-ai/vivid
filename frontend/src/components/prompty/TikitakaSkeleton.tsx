"use client";

/**
 * TikitakaSkeleton - Loading skeleton for TikitakaWorkflow
 *
 * Displays a skeleton UI while the Tikitaka workflow is loading.
 */
export function TikitakaSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Step Progress Skeleton */}
      <div className="flex items-center justify-between">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="flex items-center">
            <div className="flex flex-col items-center gap-1 p-2">
              <div className="w-10 h-10 rounded-full bg-muted" />
              <div className="h-3 w-12 bg-muted rounded" />
            </div>
            {i < 6 && <div className="w-8 h-0.5 bg-muted" />}
          </div>
        ))}
      </div>

      {/* Step Header Skeleton */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-14 h-14 rounded-xl bg-muted" />
          <div className="space-y-2">
            <div className="h-6 w-32 bg-muted rounded" />
            <div className="h-5 w-20 bg-muted rounded-full" />
          </div>
        </div>
        <div className="h-4 w-3/4 bg-muted rounded" />
      </div>

      {/* Prompt Section Skeleton */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="h-6 w-16 bg-muted rounded" />
            <div className="h-5 w-24 bg-muted rounded" />
          </div>
          <div className="h-10 w-20 bg-muted rounded-lg" />
        </div>
        <div className="p-4 bg-muted rounded-lg">
          <div className="space-y-3">
            <div className="h-4 w-full bg-muted-foreground/10 rounded" />
            <div className="h-4 w-5/6 bg-muted-foreground/10 rounded" />
            <div className="h-4 w-4/5 bg-muted-foreground/10 rounded" />
            <div className="h-4 w-full bg-muted-foreground/10 rounded" />
            <div className="h-4 w-3/4 bg-muted-foreground/10 rounded" />
          </div>
        </div>
      </div>

      {/* Attachments Skeleton */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="h-5 w-24 bg-muted rounded mb-4" />
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="w-5 h-5 rounded bg-muted" />
              <div className="flex-1 space-y-1">
                <div className="h-4 w-24 bg-muted rounded" />
                <div className="h-3 w-48 bg-muted rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tips Skeleton */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="h-5 w-12 bg-muted rounded mb-4" />
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-start gap-2">
              <div className="w-3 h-3 mt-1 bg-muted rounded" />
              <div className="h-4 w-64 bg-muted rounded" />
            </div>
          ))}
        </div>
      </div>

      {/* Action Buttons Skeleton */}
      <div className="flex justify-between items-center p-6 rounded-xl border border-border bg-card">
        <div className="h-12 w-24 bg-muted rounded-lg" />
        <div className="h-12 w-32 bg-muted rounded-lg" />
      </div>
    </div>
  );
}

export default TikitakaSkeleton;
