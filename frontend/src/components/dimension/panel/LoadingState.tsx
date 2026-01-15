"use client";

/**
 * LoadingState - DimensionPanel.Loading compound component
 *
 * Displays loading indicator with optional message and progress.
 * Only renders when context isLoading is true.
 */

import { Loader2 } from "lucide-react";
import { useDimensionPanel } from "./DimensionPanelContext";

export interface LoadingStateProps {
  /** Loading message */
  message?: string;
  /** Show progress indicator (0-100) */
  progress?: number;
  /** Show skeleton instead of spinner */
  skeleton?: boolean;
  /** Additional className */
  className?: string;
}

export function LoadingState({
  message = "처리 중...",
  progress,
  skeleton = false,
  className = "",
}: LoadingStateProps) {
  const { isLoading, classes, styles } = useDimensionPanel();

  // Only render when loading
  if (!isLoading) return null;

  if (skeleton) {
    return (
      <div className={`space-y-4 animate-pulse ${className}`}>
        <div className="h-8 bg-white/10 rounded-lg w-3/4" />
        <div className="h-4 bg-white/10 rounded-lg w-full" />
        <div className="h-4 bg-white/10 rounded-lg w-5/6" />
        <div className="h-32 bg-white/10 rounded-xl w-full" />
      </div>
    );
  }

  return (
    <div
      className={`flex flex-col items-center justify-center py-12 ${className}`}
      role="status"
      aria-live="polite"
    >
      {/* Spinner */}
      <div className="relative mb-6">
        <div className={`w-16 h-16 rounded-full ${styles.glowLg}`}>
          <Loader2
            className={`w-16 h-16 animate-spin ${classes.text}`}
            strokeWidth={1.5}
          />
        </div>
      </div>

      {/* Message */}
      <p className={`text-sm font-medium ${classes.text} mb-2`}>
        {message}
      </p>

      {/* Progress Bar */}
      {progress !== undefined && (
        <div className="w-48 h-1.5 bg-white/10 rounded-full overflow-hidden">
          <div
            className={`h-full ${classes.bg} transition-all duration-300 ease-out`}
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>
      )}

      <span className="sr-only">{message}</span>
    </div>
  );
}

LoadingState.displayName = "DimensionPanel.Loading";
