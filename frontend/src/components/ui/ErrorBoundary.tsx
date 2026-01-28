"use client";

/**
 * Error Boundary Components
 *
 * React Error Boundaries for graceful error handling in the UI.
 * Uses react-error-boundary for declarative error handling.
 * Categorizes errors for differentiated UX treatment.
 *
 * 2026 UX Pattern: Contextual error styling
 */

import { ErrorBoundary, type FallbackProps } from "react-error-boundary";
import { AlertCircle, RefreshCw, AlertTriangle, WifiOff } from "lucide-react";
import { categorizeError, getErrorStyle, type ErrorCategory } from "@/lib/validation";
import { CopyButton } from "@/components/ui/CopyButton";
import { cn } from "@/lib/utils";

interface ErrorFallbackProps extends FallbackProps {
  /** Custom title for the error message */
  title?: string;
}

// Category-specific config
const CATEGORY_CONFIG: Record<ErrorCategory, { title: string; Icon: typeof AlertCircle }> = {
  user: { title: "입력 확인 필요", Icon: AlertTriangle },
  system: { title: "시스템 오류", Icon: AlertCircle },
  network: { title: "네트워크 오류", Icon: WifiOff },
};

/**
 * Default error fallback component with categorized styling.
 */
function DefaultErrorFallback({
  error,
  resetErrorBoundary,
  title,
}: ErrorFallbackProps) {
  const category = categorizeError(error);
  const styles = getErrorStyle(category);
  const config = CATEGORY_CONFIG[category];
  const Icon = config.Icon;
  const displayTitle = title || config.title;
  const errorMessage = error?.message || "알 수 없는 오류가 발생했습니다.";

  return (
    <div
      className={cn(
        "p-4 rounded-xl border text-center",
        styles.bgColor,
        styles.borderColor
      )}
    >
      <div className="flex items-center justify-center gap-2 mb-2">
        <Icon className={cn("w-5 h-5", styles.textColor)} />
        <span className={cn("font-medium", styles.textColor)}>{displayTitle}</span>
      </div>
      <div className="flex items-center justify-center gap-2 mb-3">
        <p className="text-white/60 text-sm">{errorMessage}</p>
        <CopyButton
          text={errorMessage}
          label="에러 복사"
          size="sm"
          variant={category === "user" ? "amber" : category === "network" ? "gray" : "red"}
        />
      </div>
      <button
        onClick={resetErrorBoundary}
        className={cn(
          "inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors min-h-[44px]",
          category === "user" && "bg-amber-500/20 hover:bg-amber-500/30 text-amber-300",
          category === "system" && "bg-red-500/20 hover:bg-red-500/30 text-red-300",
          category === "network" && "bg-gray-500/20 hover:bg-gray-500/30 text-gray-300"
        )}
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
