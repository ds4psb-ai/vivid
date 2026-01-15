"use client";

/**
 * ResultCard - DimensionPanel.Result compound component
 *
 * Glassmorphism result container with dimension accent.
 * Only renders when context hasResult is true.
 */

import { type ReactNode } from "react";
import { useDimensionPanel } from "./DimensionPanelContext";

export interface ResultCardProps {
  /** Result content */
  children: ReactNode;
  /** Response ID for feedback tracking (uses context if not provided) */
  responseId?: string;
  /** Title for result section */
  title?: string;
  /** Additional className */
  className?: string;
  /** Force show even without context result */
  forceShow?: boolean;
}

export function ResultCard({
  children,
  responseId: propResponseId,
  title,
  className = "",
  forceShow = false,
}: ResultCardProps) {
  const {
    hasResult,
    responseId: contextResponseId,
    styles,
    isLoading,
  } = useDimensionPanel();

  // Only render when there's a result (unless forceShow)
  if (!forceShow && !hasResult) return null;

  // Don't render while loading
  if (isLoading) return null;

  const responseId = propResponseId || contextResponseId;

  return (
    <div
      className={`${styles.result} animate-in fade-in slide-in-from-bottom-4 duration-500 ${className}`}
      data-response-id={responseId}
    >
      {title && (
        <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
      )}
      {children}
    </div>
  );
}

ResultCard.displayName = "DimensionPanel.Result";
