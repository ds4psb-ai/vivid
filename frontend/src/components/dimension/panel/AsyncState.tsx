"use client";

/**
 * AsyncState - Unified Loading/Error State Component
 *
 * P1.1 Consolidation - Merges LoadingState and ErrorState into single component.
 * Automatically handles loading and error states from DimensionPanel context.
 *
 * Usage:
 * ```tsx
 * <DimensionPanel.AsyncState
 *   loadingMessage="생성 중..."
 *   onRetry={handleRetry}
 * />
 * ```
 */

import { Loader2, AlertTriangle, RefreshCw, X } from "lucide-react";
import { useDimensionPanel } from "./DimensionPanelContext";
import { getErrorStyle } from "@/lib/tokens";

export interface AsyncStateProps {
  // Loading props
  /** Loading message */
  loadingMessage?: string;
  /** Progress value (0-100) */
  progress?: number;
  /** Display variant for loading */
  loadingVariant?: "spinner" | "skeleton";
  /** Cancel handler */
  onCancel?: () => void;

  // Error props
  /** Custom error (overrides context error) */
  error?: Error | string;
  /** Retry handler */
  onRetry?: () => void;
  /** Dismiss handler */
  onDismiss?: () => void;

  // Shared props
  /** Additional className */
  className?: string;
  /** Force show loading (override context) */
  forceLoading?: boolean;
  /** Force show error (override context) */
  forceError?: boolean;
}

export function AsyncState({
  // Loading props
  loadingMessage = "처리 중...",
  progress,
  loadingVariant = "spinner",
  onCancel,
  // Error props
  error: propError,
  onRetry,
  onDismiss,
  // Shared props
  className = "",
  forceLoading = false,
  forceError = false,
}: AsyncStateProps) {
  const { isLoading, error: contextError, setError, hasError, classes, styles } = useDimensionPanel();

  // Determine actual states
  const showLoading = forceLoading || isLoading;
  const error = propError || contextError;
  const showError = forceError || error || hasError;

  // Error takes priority over loading
  if (showError && !showLoading) {
    const errorMessage =
      typeof error === "string"
        ? error
        : error instanceof Error
          ? error.message
          : "알 수 없는 오류가 발생했습니다.";

    const handleDismiss = () => {
      setError(null);
      onDismiss?.();
    };

    return (
      <div
        className={`${getErrorStyle()} ${className}`}
        role="alert"
        aria-live="assertive"
      >
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 p-1">
            <AlertTriangle className="w-5 h-5 text-red-400" />
          </div>

          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-red-300 mb-1">
              오류 발생
            </h3>
            <p className="text-sm text-red-400/80 break-words">
              {errorMessage}
            </p>
          </div>

          {onDismiss && (
            <button
              onClick={handleDismiss}
              className="flex-shrink-0 p-1 rounded-lg hover:bg-red-500/20 transition-colors"
              aria-label="오류 닫기"
            >
              <X className="w-4 h-4 text-red-400" />
            </button>
          )}
        </div>

        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-3 w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-300 text-sm font-medium transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            다시 시도
          </button>
        )}
      </div>
    );
  }

  // Loading state
  if (showLoading) {
    if (loadingVariant === "skeleton") {
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
        <div className="relative mb-6">
          <div className={`w-16 h-16 rounded-full ${styles.glowLg}`}>
            <Loader2
              className={`w-16 h-16 animate-spin ${classes.text}`}
              strokeWidth={1.5}
            />
          </div>
        </div>

        <p className={`text-sm font-medium ${classes.text} mb-2`}>
          {loadingMessage}
        </p>

        {progress !== undefined && (
          <div className="w-48 h-1.5 bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full ${classes.bg} transition-all duration-300 ease-out`}
              style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
            />
          </div>
        )}

        {onCancel && (
          <button
            onClick={onCancel}
            className="mt-4 px-4 py-2 text-sm text-white/60 hover:text-white border border-white/10 hover:border-white/20 rounded-lg transition-all"
          >
            취소
          </button>
        )}

        <span className="sr-only">{loadingMessage}</span>
      </div>
    );
  }

  // No state to show
  return null;
}

AsyncState.displayName = "DimensionPanel.AsyncState";

// =============================================================================
// CONVENIENCE COMPONENTS (for backward compatibility)
// =============================================================================

/**
 * @deprecated Use AsyncState with loadingMessage prop instead
 */
export function LoadingOnly(props: Omit<AsyncStateProps, "error" | "onRetry" | "onDismiss" | "forceError">) {
  return <AsyncState {...props} forceLoading />;
}

/**
 * @deprecated Use AsyncState with error prop instead
 */
export function ErrorOnly(props: Omit<AsyncStateProps, "loadingMessage" | "progress" | "loadingVariant" | "onCancel" | "forceLoading">) {
  return <AsyncState {...props} forceError />;
}
