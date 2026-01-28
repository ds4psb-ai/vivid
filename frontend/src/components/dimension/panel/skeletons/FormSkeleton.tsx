"use client";

/**
 * FormSkeleton - Skeleton loader for form layouts
 *
 * Provides a visual preview of form structure during loading.
 * Matches the typical dimension panel form layout.
 *
 * 2026 UX Pattern: Progressive loading with layout hints
 */

import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/utils";

export interface FormSkeletonProps {
  /** Number of input fields to show */
  fields?: number;
  /** Show textarea */
  showTextarea?: boolean;
  /** Show select dropdowns */
  showSelects?: boolean;
  /** Show action button */
  showButton?: boolean;
  /** Additional className */
  className?: string;
}

/**
 * FormSkeleton - Skeleton for form layouts
 *
 * @example
 * ```tsx
 * {isLoading ? <FormSkeleton fields={3} showTextarea /> : <ActualForm />}
 * ```
 */
export function FormSkeleton({
  fields = 2,
  showTextarea = true,
  showSelects = true,
  showButton = true,
  className,
}: FormSkeletonProps) {
  const prefersReducedMotion = useReducedMotion();
  const animationClass = prefersReducedMotion ? "" : "animate-pulse";

  return (
    <div className={cn("space-y-4", animationClass, className)}>
      {/* Input fields */}
      {Array.from({ length: fields }).map((_, i) => (
        <div key={i} className="space-y-2">
          {/* Label */}
          <div className="h-3 w-20 bg-white/10 rounded" />
          {/* Input */}
          <div className="h-11 bg-white/5 rounded-xl border border-white/10" />
        </div>
      ))}

      {/* Textarea */}
      {showTextarea && (
        <div className="space-y-2">
          <div className="h-3 w-24 bg-white/10 rounded" />
          <div className="h-32 bg-white/5 rounded-xl border border-white/10" />
        </div>
      )}

      {/* Select row */}
      {showSelects && (
        <div className="flex gap-4">
          <div className="h-11 w-32 bg-white/5 rounded-lg border border-white/10" />
          <div className="h-11 w-32 bg-white/5 rounded-lg border border-white/10" />
        </div>
      )}

      {/* Button */}
      {showButton && (
        <div className="h-12 w-full bg-white/10 rounded-xl" />
      )}
    </div>
  );
}
