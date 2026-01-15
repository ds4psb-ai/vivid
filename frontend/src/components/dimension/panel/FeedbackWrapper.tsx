"use client";

/**
 * FeedbackWrapper - DimensionPanel.Feedback compound component
 *
 * Wraps existing FeedbackButtons component with dimension theming.
 */

import { type ComponentProps } from "react";
import FeedbackButtons from "../FeedbackButtons";
import { useDimensionPanel } from "./DimensionPanelContext";

type FeedbackButtonsProps = ComponentProps<typeof FeedbackButtons>;

export interface FeedbackWrapperProps
  extends Omit<FeedbackButtonsProps, "responseId" | "themeColor"> {
  /** Override response ID (uses context if not provided) */
  responseId?: string;
  /** Additional className */
  className?: string;
}

export function FeedbackWrapper({
  responseId: propResponseId,
  className = "",
  ...props
}: FeedbackWrapperProps) {
  const {
    responseId: contextResponseId,
    token,
    hasResult,
    isLoading,
  } = useDimensionPanel();

  // Only render when there's a result
  if (!hasResult || isLoading) return null;

  const responseId = propResponseId || contextResponseId;

  // Need a response ID for feedback
  if (!responseId) return null;

  // Map dimension themeColor to FeedbackButtons supported colors
  const themeColorMap: Record<string, FeedbackButtonsProps["themeColor"]> = {
    violet: "emerald", // Default feedback color
    cyan: "emerald",
    emerald: "emerald",
    amber: "emerald",
    rose: "emerald",
    fuchsia: "emerald",
    indigo: "emerald",
    sky: "emerald",
    purple: "emerald",
    red: "emerald",
  };

  const feedbackThemeColor = themeColorMap[token.themeColor] || "emerald";

  return (
    <div className={`mt-4 ${className}`}>
      <FeedbackButtons
        responseId={responseId}
        themeColor={feedbackThemeColor}
        {...props}
      />
    </div>
  );
}

FeedbackWrapper.displayName = "DimensionPanel.Feedback";
