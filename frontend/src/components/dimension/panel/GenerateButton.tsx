"use client";

/**
 * GenerateButton - DimensionPanel.GenerateButton compound component
 *
 * Primary action button with dimension gradient, glow effect, and loading state.
 */

import { type ReactNode, type ButtonHTMLAttributes } from "react";
import { Loader2 } from "lucide-react";
import { useDimensionPanel } from "./DimensionPanelContext";

export interface GenerateButtonProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className"> {
  /** Button text / children */
  children?: ReactNode;
  /** Loading state (auto-detected from context if not provided) */
  loading?: boolean;
  /** Credit cost to show on button */
  creditCost?: number;
  /** Full width (default: true) */
  fullWidth?: boolean;
  /** Additional className */
  className?: string;
}

export function GenerateButton({
  children,
  loading,
  creditCost,
  fullWidth = true,
  className = "",
  disabled,
  onClick,
  ...props
}: GenerateButtonProps) {
  const { styles, isLoading, classes } = useDimensionPanel();

  // Use context loading state if not explicitly provided
  const isLoadingState = loading !== undefined ? loading : isLoading;
  const isDisabled = disabled || isLoadingState;

  return (
    <button
      onClick={onClick}
      disabled={isDisabled}
      className={`
        ${fullWidth ? "w-full" : ""}
        ${styles.button}
        ${className}
      `}
      {...props}
    >
      {isLoadingState ? (
        <span className="flex items-center justify-center gap-2">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>처리 중...</span>
        </span>
      ) : (
        <span className="flex items-center justify-center gap-2">
          {children || "생성하기"}
          {creditCost !== undefined && (
            <span className="text-xs opacity-70">({creditCost} 크레딧)</span>
          )}
        </span>
      )}
    </button>
  );
}

GenerateButton.displayName = "DimensionPanel.GenerateButton";
