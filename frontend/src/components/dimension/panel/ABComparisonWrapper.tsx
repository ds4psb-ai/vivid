"use client";

/**
 * ABComparisonWrapper - DimensionPanel.ABComparison compound component
 *
 * Wraps existing ABComparisonCard component with dimension theming
 * for UQSL (Universal Quality Selection Layer) 2-way comparison.
 *
 * 2026 Best Practice:
 * - useUQSLFeedback hook integration for Thompson Sampling
 * - Real-time feedback submission
 *
 * @see UQSL_SPEC.md - Universal Quality Selection Layer
 */

import { type ComponentProps, useCallback, useState } from "react";
import ABComparisonCard, { type CandidateData } from "../ABComparisonCard";
import { type ThemeColor as DimensionThemeColor } from "@/lib/dimension-theme";
import { useDimensionPanel } from "./DimensionPanelContext";
import { useUQSLFeedback } from "@/hooks/useUQSL";

type ABComparisonCardProps = ComponentProps<typeof ABComparisonCard>;

export interface ABComparisonWrapperProps
  extends Omit<ABComparisonCardProps, "themeColor" | "onSelect"> {
  /** Callback when a candidate is selected (simplified signature) */
  onSelect?: (selectedId: string, selectedIndex: 0 | 1) => Promise<void>;
  /** Additional className */
  className?: string;
  /** UQSL session ID for Thompson Sampling feedback */
  sessionId?: string;
  /** Callback when selection is submitted to backend */
  onSelectionSubmitted?: (result: { status: string; session_id: string }) => void;
}

// Map tokens.ts ThemeColor to dimension-theme.ts ThemeColor
const THEME_COLOR_MAP: Record<string, DimensionThemeColor> = {
  violet: "violet",
  cyan: "cyan",
  emerald: "emerald",
  amber: "amber",
  rose: "rose",
  fuchsia: "fuchsia",
  indigo: "indigo",
  sky: "sky",
  purple: "violet", // Fallback
  red: "rose", // Fallback
};

export function ABComparisonWrapper({
  candidates,
  onSelect,
  onSkip,
  showMetrics = true,
  labels,
  disabled,
  initialSelected,
  compact = false,
  className = "",
  sessionId,
  onSelectionSubmitted,
}: ABComparisonWrapperProps) {
  const { token, isLoading, hasResult } = useDimensionPanel();
  const { selectCandidate, isSubmitting } = useUQSLFeedback();
  const [selectionMade, setSelectionMade] = useState(false);

  // Only render when there's a result to compare
  // Or when candidates are explicitly provided
  if (!candidates || candidates.length !== 2) return null;

  // Map themeColor to ABComparisonCard supported color
  const mappedThemeColor = THEME_COLOR_MAP[token.themeColor] || "violet";

  // Handle selection with UQSL backend integration
  const handleSelect = useCallback(
    async (selectedId: string, selectedIndex: 0 | 1) => {
      // First, call the original onSelect callback if provided
      if (onSelect) {
        await onSelect(selectedId, selectedIndex);
      }

      // If sessionId is provided, submit selection to backend for Thompson Sampling
      if (sessionId && !selectionMade) {
        try {
          const result = await selectCandidate(sessionId, selectedIndex);
          setSelectionMade(true);
          onSelectionSubmitted?.(result);
        } catch (error) {
          console.error("[ABComparisonWrapper] Failed to submit selection:", error);
        }
      }
    },
    [onSelect, sessionId, selectionMade, selectCandidate, onSelectionSubmitted]
  );

  return (
    <div className={`mt-4 ${className}`}>
      <ABComparisonCard
        candidates={candidates}
        onSelect={handleSelect}
        onSkip={onSkip}
        showMetrics={showMetrics}
        labels={labels}
        themeColor={mappedThemeColor}
        disabled={disabled || isLoading || isSubmitting}
        initialSelected={initialSelected}
        compact={compact}
      />
      {isSubmitting && (
        <div className="mt-2 text-sm text-muted-foreground animate-pulse">
          선택 결과를 저장하는 중...
        </div>
      )}
    </div>
  );
}

ABComparisonWrapper.displayName = "DimensionPanel.ABComparison";

/**
 * Helper to create CandidateData from generation results
 */
export function createCandidateData(
  id: string,
  content: string | React.ReactNode,
  metadata?: CandidateData["metadata"]
): CandidateData {
  return { id, content, metadata };
}
