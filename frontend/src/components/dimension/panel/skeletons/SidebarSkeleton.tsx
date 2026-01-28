"use client";

/**
 * SidebarSkeleton - Skeleton loader for chain sidebar
 *
 * Matches the UnifiedChainSidebar layout for seamless loading.
 *
 * 2026 UX Pattern: Layout-preserving loading states
 */

import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/utils";

export interface SidebarSkeletonProps {
  /** Number of chain items to show */
  items?: number;
  /** Show header */
  showHeader?: boolean;
  /** Additional className */
  className?: string;
}

/**
 * SidebarSkeleton - Skeleton for chain sidebar
 *
 * @example
 * ```tsx
 * {isLoading ? <SidebarSkeleton items={4} /> : <UnifiedChainSidebar />}
 * ```
 */
export function SidebarSkeleton({
  items = 4,
  showHeader = true,
  className,
}: SidebarSkeletonProps) {
  const prefersReducedMotion = useReducedMotion();
  const animationClass = prefersReducedMotion ? "" : "animate-pulse";

  return (
    <div className={cn("p-4 space-y-4", animationClass, className)}>
      {/* Header */}
      {showHeader && (
        <div className="space-y-2 pb-4 border-b border-white/10">
          <div className="h-5 w-24 bg-white/10 rounded" />
          <div className="h-3 w-32 bg-white/10 rounded" />
        </div>
      )}

      {/* Chain items */}
      <div className="space-y-3">
        {Array.from({ length: items }).map((_, i) => (
          <div
            key={i}
            className="p-3 bg-white/5 rounded-lg border border-white/10 space-y-2"
          >
            {/* Item header */}
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-white/10 rounded" />
              <div className="h-4 w-20 bg-white/10 rounded" />
            </div>
            {/* Item content */}
            <div className="h-3 w-full bg-white/10 rounded" />
            <div className="h-3 w-3/4 bg-white/10 rounded" />
          </div>
        ))}
      </div>

      {/* Action button */}
      <div className="h-10 w-full bg-white/10 rounded-lg" />
    </div>
  );
}

/**
 * Compact chain item skeleton for inline use
 */
export function ChainItemSkeleton({ className }: { className?: string }) {
  const prefersReducedMotion = useReducedMotion();
  const animationClass = prefersReducedMotion ? "" : "animate-pulse";

  return (
    <div
      className={cn(
        "flex items-center gap-2 p-2 bg-white/5 rounded-lg",
        animationClass,
        className
      )}
    >
      <div className="w-5 h-5 bg-white/10 rounded" />
      <div className="flex-1">
        <div className="h-3 w-16 bg-white/10 rounded mb-1" />
        <div className="h-2 w-24 bg-white/10 rounded" />
      </div>
    </div>
  );
}
