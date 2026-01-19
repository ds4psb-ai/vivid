"use client";

/**
 * ErrorState - DimensionPanel.Error compound component
 *
 * Displays error message with retry option.
 * Only renders when context hasError is true.
 */

import { AlertTriangle, RefreshCw, X } from "lucide-react";
import { useDimensionPanel } from "./DimensionPanelContext";
import { getErrorStyle } from "@/lib/tokens";

export interface ErrorStateProps {
  /** Custom error message (uses context error if not provided) */
  error?: Error | string;
  /** Retry handler */
  onRetry?: () => void;
  /** Dismiss handler */
  onDismiss?: () => void;
  /** Additional className */
  className?: string;
}

export function ErrorState({
  error: propError,
  onRetry,
  onDismiss,
  className = "",
}: ErrorStateProps) {
  const { error: contextError, setError, hasError } = useDimensionPanel();

  // Use prop error or context error
  const error = propError || contextError;

  // Only render when there's an error
  if (!error && !hasError) return null;

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
        {/* Icon */}
        <div className="flex-shrink-0 p-1">
          <AlertTriangle className="w-5 h-5 text-red-400" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-red-300 mb-1">
            오류 발생
          </h3>
          <p className="text-sm text-red-400/80 break-words">
            {errorMessage}
          </p>
        </div>

        {/* Dismiss Button */}
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

      {/* Retry Button */}
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

ErrorState.displayName = "DimensionPanel.Error";
