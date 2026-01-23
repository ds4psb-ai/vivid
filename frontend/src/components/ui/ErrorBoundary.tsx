"use client";

/**
 * Error Boundary Components
 *
 * React Error Boundaries for graceful error handling in the UI.
 * Uses react-error-boundary for declarative error handling.
 */

import { ErrorBoundary, type FallbackProps } from "react-error-boundary";
import { AlertCircle, RefreshCw } from "lucide-react";

interface ErrorFallbackProps extends FallbackProps {
  /** Custom title for the error message */
  title?: string;
}

/**
 * Default error fallback component.
 */
function DefaultErrorFallback({
  error,
  resetErrorBoundary,
  title = "오류가 발생했습니다",
}: ErrorFallbackProps) {
  return (
    <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-center">
      <div className="flex items-center justify-center gap-2 mb-2">
        <AlertCircle className="w-5 h-5 text-red-400" />
        <span className="text-red-400 font-medium">{title}</span>
      </div>
      <p className="text-white/60 text-sm mb-3">
        {error?.message || "알 수 없는 오류가 발생했습니다."}
      </p>
      <button
        onClick={resetErrorBoundary}
        className="inline-flex items-center gap-2 px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-red-300 text-sm transition-colors"
      >
        <RefreshCw className="w-4 h-4" />
        다시 시도
      </button>
    </div>
  );
}

interface DimensionErrorBoundaryProps {
  children: React.ReactNode;
  /** Dimension name for error context */
  dimensionName?: string;
  /** Callback when error occurs */
  onError?: (error: Error, info: React.ErrorInfo) => void;
  /** Custom fallback render function */
  fallbackRender?: (props: FallbackProps) => React.ReactNode;
}

/**
 * Error boundary wrapper for Dimension panels.
 *
 * Catches errors in dimension panel rendering and displays
 * a graceful fallback UI.
 */
export function DimensionErrorBoundary({
  children,
  dimensionName,
  onError,
  fallbackRender,
}: DimensionErrorBoundaryProps) {
  const handleError = (error: Error, info: React.ErrorInfo) => {
    // Log error for debugging
    console.error(`[DimensionError${dimensionName ? `:${dimensionName}` : ""}]`, error, info);

    // Call custom error handler if provided
    onError?.(error, info);
  };

  return (
    <ErrorBoundary
      fallbackRender={
        fallbackRender ||
        ((props) => (
          <DefaultErrorFallback
            {...props}
            title={dimensionName ? `${dimensionName} 오류` : "오류가 발생했습니다"}
          />
        ))
      }
      onError={handleError}
    >
      {children}
    </ErrorBoundary>
  );
}

interface GenericErrorBoundaryProps {
  children: React.ReactNode;
  /** Callback when error occurs */
  onError?: (error: Error, info: React.ErrorInfo) => void;
}

/**
 * Generic error boundary for any component.
 */
export function GenericErrorBoundary({
  children,
  onError,
}: GenericErrorBoundaryProps) {
  return (
    <ErrorBoundary
      fallback={
        <div className="p-4 text-red-400 text-center">
          오류가 발생했습니다. 페이지를 새로고침해 주세요.
        </div>
      }
      onError={(error, info) => {
        console.error("[GenericError]", error, info);
        onError?.(error, info);
      }}
    >
      {children}
    </ErrorBoundary>
  );
}

export { ErrorBoundary } from "react-error-boundary";
export type { FallbackProps } from "react-error-boundary";
