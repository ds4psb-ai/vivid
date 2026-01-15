"use client";

/**
 * ThreeWayComparisonWrapper - DimensionPanel.ThreeWay compound component
 *
 * Wraps existing ThreeWayComparison component with dimension theming
 * for UQSL (Universal Quality Selection Layer) Ensemble++ 3-way comparison.
 *
 * 2026 Best Practice:
 * - NeurIPS 2025 Ensemble++ framework (arXiv:2407.13195)
 * - A vs B vs A+B comparison
 * - Thompson Sampling feedback integration with useUQSLFeedback hook
 *
 * @see UQSL_SPEC.md - Universal Quality Selection Layer
 */

import { type ComponentProps, useCallback, useState } from "react";
import ThreeWayComparison, {
  type ThreeWayCandidateData,
  type ThreeWaySelection,
} from "../ThreeWayComparison";
import { type ThemeColor as DimensionThemeColor } from "@/lib/dimension-theme";
import { useDimensionPanel } from "./DimensionPanelContext";
import { useUQSLFeedback } from "@/hooks/useUQSL";

type ThreeWayComparisonProps = ComponentProps<typeof ThreeWayComparison>;

export interface ThreeWayComparisonWrapperProps
  extends Omit<ThreeWayComparisonProps, "themeColor" | "onSelect"> {
  /** Callback when a candidate is selected */
  onSelect?: (selected: ThreeWaySelection) => Promise<void>;
  /** Additional className */
  className?: string;
  /** UQSL comparison ID for Thompson Sampling feedback */
  comparisonId?: string;
  /** Callback when selection is submitted to backend */
  onSelectionSubmitted?: (result: { status: string; selected: string }) => void;
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

export function ThreeWayComparisonWrapper({
  candidates,
  onSelect,
  labels,
  showConfidence = true,
  recommended,
  disabled,
  initialSelected,
  layout = "auto",
  className = "",
  comparisonId,
  onSelectionSubmitted,
}: ThreeWayComparisonWrapperProps) {
  const { token, isLoading } = useDimensionPanel();
  const { selectThreeWay, isSubmitting } = useUQSLFeedback();
  const [selectionMade, setSelectionMade] = useState(false);

  // Validate candidates structure
  if (!candidates || !candidates.a || !candidates.b || !candidates.ab) {
    return null;
  }

  // Map themeColor to ThreeWayComparison supported color
  const mappedThemeColor = THEME_COLOR_MAP[token.themeColor] || "violet";

  // Handle selection with UQSL backend integration
  const handleSelect = useCallback(
    async (selected: ThreeWaySelection) => {
      // First, call the original onSelect callback if provided
      if (onSelect) {
        await onSelect(selected);
      }

      // If comparisonId is provided, submit selection to backend for Thompson Sampling
      if (comparisonId && !selectionMade) {
        try {
          const result = await selectThreeWay(comparisonId, selected);
          setSelectionMade(true);
          onSelectionSubmitted?.(result);
        } catch (error) {
          console.error("[ThreeWayComparisonWrapper] Failed to submit selection:", error);
        }
      }
    },
    [onSelect, comparisonId, selectionMade, selectThreeWay, onSelectionSubmitted]
  );

  return (
    <div className={`mt-4 ${className}`}>
      <ThreeWayComparison
        candidates={candidates}
        onSelect={handleSelect}
        labels={labels}
        showConfidence={showConfidence}
        recommended={recommended}
        themeColor={mappedThemeColor}
        disabled={disabled || isLoading || isSubmitting}
        initialSelected={initialSelected}
        layout={layout}
      />
      {isSubmitting && (
        <div className="mt-2 text-sm text-muted-foreground animate-pulse">
          선택 결과를 저장하는 중...
        </div>
      )}
    </div>
  );
}

ThreeWayComparisonWrapper.displayName = "DimensionPanel.ThreeWay";

/**
 * Helper to create ThreeWayCandidateData from generation results
 */
export function createThreeWayCandidateData(
  id: string,
  content: string | React.ReactNode,
  options?: {
    confidence?: number;
    backendUsed?: string;
    metadata?: Record<string, unknown>;
  }
): ThreeWayCandidateData {
  return {
    id,
    content,
    confidence: options?.confidence,
    backendUsed: options?.backendUsed,
    metadata: options?.metadata,
  };
}

/**
 * Helper to create Ensemble++ candidates structure
 *
 * @example
 * const candidates = createEnsembleCandidates(
 *   { id: "qdrant-1", content: "Result from Qdrant", confidence: 0.85 },
 *   { id: "nlm-1", content: "Result from NotebookLM", confidence: 0.92 },
 *   { id: "ensemble-1", content: "Merged result", confidence: 0.96 }
 * );
 */
export function createEnsembleCandidates(
  candidateA: ThreeWayCandidateData,
  candidateB: ThreeWayCandidateData,
  candidateAB: ThreeWayCandidateData
): ThreeWayComparisonProps["candidates"] {
  return {
    a: candidateA,
    b: candidateB,
    ab: candidateAB,
  };
}
