"use client";

import { motion, AnimatePresence } from "framer-motion";
import type { ProgressEvent } from "@/hooks/useAsyncOperation";
import { type DimensionCode, getDimensionToken } from "@/lib/tokens";

/**
 * Theme colors matching DimensionPanelLayout.
 */
export type ThemeColor =
  | "violet"
  | "cyan"
  | "emerald"
  | "amber"
  | "rose"
  | "fuchsia"
  | "indigo"
  | "sky";

const THEME_COLORS = {
  violet: {
    accent: "text-violet-400",
    bg: "bg-violet-500/10",
    border: "border-violet-500/30",
    progress: "bg-gradient-to-r from-violet-500 to-purple-500",
    progressBg: "bg-violet-500/20",
    button: "bg-violet-500/20 hover:bg-violet-500/30 text-violet-400",
    spinner: "border-violet-500",
  },
  cyan: {
    accent: "text-cyan-400",
    bg: "bg-cyan-500/10",
    border: "border-cyan-500/30",
    progress: "bg-gradient-to-r from-cyan-500 to-blue-500",
    progressBg: "bg-cyan-500/20",
    button: "bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400",
    spinner: "border-cyan-500",
  },
  emerald: {
    accent: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    progress: "bg-gradient-to-r from-emerald-500 to-teal-500",
    progressBg: "bg-emerald-500/20",
    button: "bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400",
    spinner: "border-emerald-500",
  },
  amber: {
    accent: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    progress: "bg-gradient-to-r from-amber-400 to-orange-500",
    progressBg: "bg-amber-500/20",
    button: "bg-amber-500/20 hover:bg-amber-500/30 text-amber-400",
    spinner: "border-amber-500",
  },
  rose: {
    accent: "text-rose-400",
    bg: "bg-rose-500/10",
    border: "border-rose-500/30",
    progress: "bg-gradient-to-r from-rose-500 to-pink-500",
    progressBg: "bg-rose-500/20",
    button: "bg-rose-500/20 hover:bg-rose-500/30 text-rose-400",
    spinner: "border-rose-500",
  },
  fuchsia: {
    accent: "text-fuchsia-400",
    bg: "bg-fuchsia-500/10",
    border: "border-fuchsia-500/30",
    progress: "bg-gradient-to-r from-fuchsia-500 to-purple-500",
    progressBg: "bg-fuchsia-500/20",
    button: "bg-fuchsia-500/20 hover:bg-fuchsia-500/30 text-fuchsia-400",
    spinner: "border-fuchsia-500",
  },
  indigo: {
    accent: "text-indigo-400",
    bg: "bg-indigo-500/10",
    border: "border-indigo-500/30",
    progress: "bg-gradient-to-r from-indigo-500 to-violet-500",
    progressBg: "bg-indigo-500/20",
    button: "bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-400",
    spinner: "border-indigo-500",
  },
  sky: {
    accent: "text-sky-400",
    bg: "bg-sky-500/10",
    border: "border-sky-500/30",
    progress: "bg-gradient-to-r from-sky-500 to-blue-500",
    progressBg: "bg-sky-500/20",
    button: "bg-sky-500/20 hover:bg-sky-500/30 text-sky-400",
    spinner: "border-sky-500",
  },
};

const getDimensionTheme = (dimensionCode?: DimensionCode) => {
  if (!dimensionCode) return null;
  const token = getDimensionToken(dimensionCode);
  const key = token.tailwindKey;
  return {
    accent: `text-${key}`,
    bg: `bg-${key}/10`,
    border: `border-${key}/30`,
    progress: `bg-${key}`,
    progressBg: `bg-${key}/20`,
    button: `bg-${key}/20 hover:bg-${key}/30 text-${key}`,
    spinner: `border-${key}`,
  };
};

export interface OperationProgressProps {
  /** Current progress state */
  progress: ProgressEvent | null;
  /** Whether operation is in progress */
  isLoading: boolean;
  /** Error message if operation failed */
  error: string | null;
  /** Called when user clicks cancel */
  onCancel: () => void;
  /** Called when user clicks retry */
  onRetry: () => void;
  /** Whether retry is available */
  canRetry: boolean;
  /** Theme color for styling */
  themeColor?: ThemeColor;
  /** Dimension code for token-driven styling (preferred) */
  dimensionCode?: DimensionCode;
  /** Show cancel button (default: true) */
  showCancelButton?: boolean;
  /** Show retry button (default: true) */
  showRetryButton?: boolean;
  /** Cancel button label (default: "취소") */
  cancelLabel?: string;
  /** Retry button label (default: "다시 시도") */
  retryLabel?: string;
  /** Dismiss button label for error state (default: "닫기") */
  dismissLabel?: string;
  /** Current retry count (for display) */
  retryCount?: number;
  /** Max retry count (for display) */
  maxRetries?: number;
}

/**
 * Reusable progress indicator with cancel/retry actions.
 *
 * Shows:
 * - Animated progress bar with percentage
 * - Status message
 * - Cancel button during loading
 * - Retry button on error (if retryable)
 *
 * @example
 * ```tsx
 * <OperationProgress
 *   progress={progress}
 *   isLoading={isLoading}
 *   error={error}
 *   onCancel={cancel}
 *   onRetry={retry}
 *   canRetry={canRetry}
 *   themeColor="sky"
 * />
 * ```
 */
export function OperationProgress({
  progress,
  isLoading,
  error,
  onCancel,
  onRetry,
  canRetry,
  themeColor = "amber",
  dimensionCode,
  showCancelButton = true,
  showRetryButton = true,
  cancelLabel = "취소",
  retryLabel = "다시 시도",
  dismissLabel = "닫기",
  retryCount = 0,
  maxRetries = 3,
}: OperationProgressProps) {
  const tokenTheme = getDimensionTheme(dimensionCode);
  const theme = tokenTheme ?? THEME_COLORS[themeColor];

  // Don't render if not loading and no error
  if (!isLoading && !error) {
    return null;
  }

  return (
    <AnimatePresence mode="wait">
      {/* Loading State */}
      {isLoading && progress && (
        <motion.div
          key="loading"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
          className={`rounded-2xl ${theme.bg} border ${theme.border} p-5 backdrop-blur-xl`}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              {/* Spinner */}
              <div className="relative w-5 h-5">
                <div
                  className={`absolute inset-0 border-2 ${theme.spinner} border-t-transparent rounded-full animate-spin`}
                />
              </div>
              <span className={`text-sm font-medium ${theme.accent}`}>
                처리 중...
              </span>
            </div>

            {/* Cancel Button */}
            {showCancelButton && (
              <button
                onClick={onCancel}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium ${theme.button} transition-colors`}
              >
                {cancelLabel}
              </button>
            )}
          </div>

          {/* Progress Bar */}
          <div className="mb-3">
            <div className={`h-2 rounded-full ${theme.progressBg} overflow-hidden`}>
              <motion.div
                className={`h-full rounded-full ${theme.progress}`}
                initial={{ width: 0 }}
                animate={{ width: `${progress.percent}%` }}
                transition={{ duration: 0.3, ease: "easeOut" }}
              />
            </div>
          </div>

          {/* Status */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-white/50 truncate max-w-[var(--layout-bubble-max-medium)]">
              {progress.message}
            </span>
            <span className={`text-xs font-mono ${theme.accent}`}>
              {progress.percent}%
            </span>
          </div>
        </motion.div>
      )}

      {/* Error State */}
      {!isLoading && error && (
        <motion.div
          key="error"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
          className="rounded-2xl bg-red-500/10 border border-red-500/30 p-5 backdrop-blur-xl"
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              {/* Error Icon */}
              <div className="w-5 h-5 rounded-full bg-red-500/20 flex items-center justify-center">
                <svg
                  className="w-3 h-3 text-red-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </div>
              <span className="text-sm font-medium text-red-400">오류 발생</span>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              {/* Retry Button */}
              {showRetryButton && canRetry && (
                <button
                  onClick={onRetry}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/20 hover:bg-red-500/30 text-red-400 transition-colors flex items-center gap-1.5"
                >
                  <svg
                    className="w-3 h-3"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  {retryLabel}
                  {maxRetries > 1 && (
                    <span className="text-red-400/60">
                      ({retryCount}/{maxRetries})
                    </span>
                  )}
                </button>
              )}

              {/* Dismiss Button - always show to let user close error overlay */}
              <button
                onClick={onCancel}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white/5 hover:bg-white/10 text-white/60 hover:text-white/80 transition-colors"
              >
                {dismissLabel}
              </button>
            </div>
          </div>

          {/* Error Message */}
          <p className="text-xs text-white/60 leading-relaxed">{error}</p>

          {/* Hint if can't retry */}
          {!canRetry && retryCount > 0 && (
            <p className="text-xs text-white/40 mt-2">
              최대 재시도 횟수에 도달했습니다. 잠시 후 다시 시도해주세요.
            </p>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default OperationProgress;
