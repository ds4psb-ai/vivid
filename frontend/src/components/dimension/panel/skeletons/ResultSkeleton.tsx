"use client";

/**
 * ResultSkeleton - Skeleton loader for result content
 *
 * Provides type-specific skeleton layouts for different result types:
 * - video: 16:9 aspect ratio placeholder
 * - image: Square/custom aspect ratio placeholder
 * - text: Line-by-line text skeleton
 * - card: Card layout skeleton
 *
 * 2026 UX Pattern: Content-aware loading states
 */

import { Film, Image as ImageIcon, FileText, LayoutGrid } from "lucide-react";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/utils";

export type ResultSkeletonType = "video" | "image" | "text" | "card" | "audio";

export interface ResultSkeletonProps {
  /** Type of result to show skeleton for */
  type: ResultSkeletonType;
  /** Number of items (for text lines or cards) */
  count?: number;
  /** Aspect ratio for media types (default: 16:9 for video, 1:1 for image) */
  aspectRatio?: string;
  /** Additional className */
  className?: string;
}

/**
 * ResultSkeleton - Type-specific result skeleton
 *
 * @example
 * ```tsx
 * {isLoading ? <ResultSkeleton type="video" /> : <VideoPlayer url={result} />}
 * ```
 */
export function ResultSkeleton({
  type,
  count = 3,
  aspectRatio,
  className,
}: ResultSkeletonProps) {
  const prefersReducedMotion = useReducedMotion();
  const animationClass = prefersReducedMotion ? "" : "animate-pulse";

  switch (type) {
    case "video":
      return (
        <div
          className={cn(
            "bg-white/5 rounded-xl flex items-center justify-center border border-white/10",
            animationClass,
            className
          )}
          style={{ aspectRatio: aspectRatio || "16/9" }}
        >
          <Film className="w-12 h-12 text-white/20" />
        </div>
      );

    case "image":
      return (
        <div
          className={cn(
            "bg-white/5 rounded-xl flex items-center justify-center border border-white/10",
            animationClass,
            className
          )}
          style={{ aspectRatio: aspectRatio || "1/1" }}
        >
          <ImageIcon className="w-12 h-12 text-white/20" />
        </div>
      );

    case "audio":
      return (
        <div className={cn("space-y-3", animationClass, className)}>
          {/* Waveform placeholder */}
          <div className="h-16 bg-white/5 rounded-xl border border-white/10 flex items-center justify-center gap-1 px-4">
            {Array.from({ length: 20 }).map((_, i) => (
              <div
                key={i}
                className="w-1 bg-white/20 rounded-full"
                style={{
                  height: `${Math.random() * 100}%`,
                  minHeight: "4px",
                }}
              />
            ))}
          </div>
          {/* Controls placeholder */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/10 rounded-full" />
            <div className="flex-1 h-2 bg-white/10 rounded-full" />
            <div className="w-12 h-4 bg-white/10 rounded" />
          </div>
        </div>
      );

    case "text":
      return (
        <div className={cn("space-y-2", animationClass, className)}>
          {Array.from({ length: count }).map((_, i) => (
            <div
              key={i}
              className="h-4 bg-white/10 rounded"
              style={{
                width: i === count - 1 ? "60%" : i % 2 === 0 ? "100%" : "85%",
              }}
            />
          ))}
        </div>
      );

    case "card":
      return (
        <div className={cn("grid gap-4 grid-cols-1 sm:grid-cols-2", animationClass, className)}>
          {Array.from({ length: count }).map((_, i) => (
            <div
              key={i}
              className="p-4 bg-white/5 rounded-xl border border-white/10 space-y-3"
            >
              <div className="h-4 w-2/3 bg-white/10 rounded" />
              <div className="h-3 w-full bg-white/10 rounded" />
              <div className="h-3 w-4/5 bg-white/10 rounded" />
            </div>
          ))}
        </div>
      );

    default:
      return (
        <div className={cn("flex items-center justify-center h-32", animationClass, className)}>
          <LayoutGrid className="w-8 h-8 text-white/20" />
        </div>
      );
  }
}

/**
 * Multi-result skeleton for grids
 */
export function ResultGridSkeleton({
  type,
  count = 4,
  columns = 2,
  className,
}: {
  type: ResultSkeletonType;
  count?: number;
  columns?: number;
  className?: string;
}) {
  const prefersReducedMotion = useReducedMotion();
  const animationClass = prefersReducedMotion ? "" : "animate-pulse";

  return (
    <div
      className={cn("grid gap-4", animationClass, className)}
      style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
    >
      {Array.from({ length: count }).map((_, i) => (
        <ResultSkeleton key={i} type={type} />
      ))}
    </div>
  );
}
