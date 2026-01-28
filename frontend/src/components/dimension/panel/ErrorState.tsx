"use client";

/**
 * ErrorState - DimensionPanel.Error compound component
 *
 * Displays error message with retry option.
 * Categorizes errors (user/system/network) for differentiated UX.
 *
 * 2026 UX Pattern: Contextual error styling
 */

import { AlertTriangle, RefreshCw, X, WifiOff, AlertCircle, Loader2 } from "lucide-react";
import { useDimensionPanel } from "./DimensionPanelContext";
import { categorizeError, getErrorStyle, type ErrorCategory } from "@/lib/validation";
import { CopyButton } from "@/components/ui/CopyButton";
import { cn } from "@/lib/utils";

export interface ErrorStateProps {
  /** Custom error message (uses context error if not provided) */
  error?: Error | string;
  /** Retry handler */
  onRetry?: () => void;
  /** Dismiss handler */
  onDismiss?: () => void;
  /** Additional className */
  className?: string;
  /** Show copy button for error message */
  showCopy?: boolean;
}

// Category-specific titles and hints
const CATEGORY_CONFIG: Record<ErrorCategory, { title: string; hint: string; Icon: typeof AlertTriangle }> = {
  user: {
    title: "입력 확인 필요",
    hint: "입력값을 확인 후 다시 시도해주세요.",
    Icon: AlertTriangle,
  },
  system: {
    title: "시스템 오류",
    hint: "잠시 후 다시 시도해주세요.",
    Icon: AlertCircle,
  },
  network: {
    title: "네트워크 오류",
    hint: "인터넷 연결을 확인해주세요. 자동 재시도 중...",
    Icon: WifiOff,
  },
};

export function ErrorState({
  error: propError,
  onRetry,
  onDismiss,
  className = "",
  showCopy = true,
}: ErrorStateProps) {
  const { error: contextError, setError, hasError } = useDimensionPanel();

  // Use prop error or context error
  const error = propError || contextError;

  // Only render when there's an error
  if (!error && !hasError) return null;

  const errorMessage =
    typeof error === "string" && error
      ? error
      : error instanceof Error && error.message
        ? error.message
        : "요청 처리에 실패했습니다. 다시 시도해주세요.";

  // Categorize the error for differentiated UX
  const category = categorizeError(error);
  const styles = getErrorStyle(category);
  const config = CATEGORY_CONFIG[category];
  const CategoryIcon = config.Icon;

  const handleDismiss = () => {
    setError(null);
    onDismiss?.();
  };

  // Retry button style based on category
  const retryButtonStyle = cn(
    "mt-3 w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors min-h-[44px]",
    category === "user" && "bg-amber-500/20 hover:bg-amber-500/30 text-amber-300",
    category === "system" && "bg-red-500/20 hover:bg-red-500/30 text-red-300",
    category === "network" && "bg-gray-500/20 hover:bg-gray-500/30 text-gray-300"
  );

  return (
    <div
      className={cn(
        "p-4 rounded-xl border",
        styles.bgColor,
        styles.borderColor,
        className
      )}
      role="alert"
      aria-live="assertive"
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="flex-shrink-0 p-1">
          <CategoryIcon className={cn("w-5 h-5", styles.textColor)} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className={cn("text-sm font-semibold mb-1", styles.textColor)}>
            {config.title}
          </h3>
          <div className="flex items-start gap-2">
            <p className={cn("text-sm break-words flex-1", styles.textColor, "opacity-80")}>
              {errorMessage}
            </p>
            {showCopy && (
              <CopyButton
                text={errorMessage}
                label="에러 메시지 복사"
                size="sm"
                variant={category === "user" ? "amber" : category === "network" ? "gray" : "red"}
              />
            )}
          </div>
          {/* Hint text */}
          <p className={cn("text-xs mt-2 opacity-60", styles.textColor)}>
            {category === "network" && (
              <span className="inline-flex items-center gap-1">
                <Loader2 className="w-3 h-3 animate-spin" />
                {config.hint}
              </span>
            )}
            {category !== "network" && config.hint}
          </p>
        </div>

        {/* Dismiss Button */}
        {onDismiss && (
          <button
            onClick={handleDismiss}
            className={cn(
              "flex-shrink-0 p-1.5 rounded-lg transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center",
              category === "user" && "hover:bg-amber-500/20",
              category === "system" && "hover:bg-red-500/20",
              category === "network" && "hover:bg-gray-500/20"
            )}
            aria-label="오류 닫기"
          >
            <X className={cn("w-4 h-4", styles.textColor)} />
          </button>
        )}
      </div>

      {/* Retry Button */}
      {onRetry && (
        <button onClick={onRetry} className={retryButtonStyle}>
          <RefreshCw className="w-4 h-4" />
          다시 시도
        </button>
      )}
    </div>
  );
}

ErrorState.displayName = "DimensionPanel.Error";
