"use client";

/**
 * QualitySelection - Unified UQSL Comparison Component
 *
 * Consolidates ABComparison, ThreeWay, and MultiGenerate wrappers
 * into a single component with strategy prop.
 *
 * P1.1 Consolidation - Reduces 3 files (~700 LOC) to 1 unified component.
 *
 * @see UQSL_SPEC.md - Universal Quality Selection Layer
 */

import { type ComponentProps, type ReactNode, useCallback, useState } from "react";
import { useDimensionPanel } from "./DimensionPanelContext";
import { useUQSLFeedback } from "@/hooks/useUQSL";
import { type ThemeColor as DimensionThemeColor } from "@/lib/dimension-theme";
import type {
  DimensionMultiGenerateResponse,
  DimensionDiversityStrategy,
  UQSLQualityScore,
} from "@/lib/api";

// Import underlying components
import ABComparisonCard, { type CandidateData } from "../ABComparisonCard";
import ThreeWayComparison, {
  type ThreeWayCandidateData,
  type ThreeWaySelection,
} from "../ThreeWayComparison";

// =============================================================================
// TYPES
// =============================================================================

export type QualitySelectionStrategy = "ab" | "three-way" | "multi";

/** Base props shared across all strategies */
interface BaseQualitySelectionProps {
  /** Selection strategy */
  strategy: QualitySelectionStrategy;
  /** Additional className */
  className?: string;
  /** Whether disabled */
  disabled?: boolean;
  /** Session/Comparison ID for Thompson Sampling */
  sessionId?: string;
  /** Callback when selection is submitted */
  onSelectionSubmitted?: (result: { status: string; [key: string]: unknown }) => void;
}

/** AB Comparison specific props */
export interface ABSelectionProps extends BaseQualitySelectionProps {
  strategy: "ab";
  candidates: [CandidateData, CandidateData];
  onSelect?: (selectedId: string, selectedIndex: 0 | 1) => Promise<void>;
  onSkip?: () => void;
  showMetrics?: boolean;
  labels?: { a: string; b: string };
  initialSelected?: 0 | 1;
  compact?: boolean;
}

/** Three-Way Comparison specific props */
export interface ThreeWaySelectionProps extends BaseQualitySelectionProps {
  strategy: "three-way";
  candidates: {
    a: ThreeWayCandidateData;
    b: ThreeWayCandidateData;
    ab: ThreeWayCandidateData;
  };
  onSelect?: (selected: ThreeWaySelection) => Promise<void>;
  labels?: { a: string; b: string; ab: string };
  showConfidence?: boolean;
  recommended?: "a" | "b" | "ab";
  initialSelected?: ThreeWaySelection;
  layout?: "auto" | "tabs" | "cards";
}

/** Multi-Generate specific props */
export interface MultiGenerateCandidate {
  idx: number;
  content: string | ReactNode;
  metadata?: Record<string, unknown>;
  latencyMs?: number;
  qualityScore?: UQSLQualityScore;
  isRecommended?: boolean;
}

export interface MultiSelectionProps extends BaseQualitySelectionProps {
  strategy: "multi";
  candidates: MultiGenerateCandidate[];
  recommendedIdx?: number;
  strategyUsed?: DimensionDiversityStrategy;
  selectedIdx?: number;
  onSelect?: (idx: number) => void;
  onSubmit?: (idx: number, rating?: number) => Promise<void>;
  submitted?: boolean;
  isSubmitting?: boolean;
  showQualityScores?: boolean;
  showMetadata?: boolean;
  compact?: boolean;
  isLoading?: boolean;
  error?: string;
}

export type QualitySelectionProps =
  | ABSelectionProps
  | ThreeWaySelectionProps
  | MultiSelectionProps;

// =============================================================================
// THEME MAPPING
// =============================================================================

const THEME_COLOR_MAP: Record<string, DimensionThemeColor> = {
  violet: "violet",
  cyan: "cyan",
  emerald: "emerald",
  amber: "amber",
  rose: "rose",
  fuchsia: "fuchsia",
  indigo: "indigo",
  sky: "sky",
  purple: "violet",
  red: "rose",
};

const QUALITY_BAR_COLORS: Record<string, string> = {
  groundedness: "bg-emerald-500",
  relevance: "bg-cyan-500",
  coherence: "bg-violet-500",
  creativity: "bg-amber-500",
  safety: "bg-rose-500",
};

const STRATEGY_LABELS: Record<DimensionDiversityStrategy, string> = {
  standard: "Standard",
  verbalized: "Verbalized Sampling",
  diversified: "Diversified Sampling",
  compute_optimal: "Compute-Optimal",
};

// =============================================================================
// UTILITY
// =============================================================================

function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(" ");
}

// =============================================================================
// SUB-COMPONENTS
// =============================================================================

function QualityScoreBar({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  const percentage = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-20 text-muted-foreground truncate">{label}</span>
      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-500", color)}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="w-8 text-right font-mono">{percentage}%</span>
    </div>
  );
}

function MultiCandidateCard({
  candidate,
  isSelected,
  isRecommended,
  isDisabled,
  showQualityScores,
  showMetadata,
  compact,
  onSelect,
}: {
  candidate: MultiGenerateCandidate;
  isSelected: boolean;
  isRecommended: boolean;
  isDisabled: boolean;
  showQualityScores: boolean;
  showMetadata: boolean;
  compact: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      disabled={isDisabled}
      className={cn(
        "w-full p-4 rounded-lg border text-left transition-all duration-200",
        "hover:border-primary/50 hover:shadow-md",
        isSelected && "border-primary ring-2 ring-primary/20 bg-primary/5",
        isRecommended && !isSelected && "border-amber-500/50 bg-amber-50/5",
        isDisabled && "opacity-50 cursor-not-allowed",
        compact && "p-3"
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">
            Candidate {candidate.idx + 1}
          </span>
          {isRecommended && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-600">
              Recommended
            </span>
          )}
        </div>
        {candidate.latencyMs && (
          <span className="text-xs text-muted-foreground">
            {candidate.latencyMs}ms
          </span>
        )}
      </div>

      <div className={cn("text-sm text-foreground/90", compact ? "line-clamp-3" : "line-clamp-6")}>
        {candidate.content}
      </div>

      {showQualityScores && candidate.qualityScore && (
        <div className="mt-3 pt-3 border-t border-border/50 space-y-1.5">
          <QualityScoreBar label="Groundedness" value={candidate.qualityScore.groundedness} color={QUALITY_BAR_COLORS.groundedness} />
          <QualityScoreBar label="Relevance" value={candidate.qualityScore.relevance} color={QUALITY_BAR_COLORS.relevance} />
          <QualityScoreBar label="Coherence" value={candidate.qualityScore.coherence} color={QUALITY_BAR_COLORS.coherence} />
          <QualityScoreBar label="Creativity" value={candidate.qualityScore.creativity} color={QUALITY_BAR_COLORS.creativity} />
          <QualityScoreBar label="Safety" value={candidate.qualityScore.safety} color={QUALITY_BAR_COLORS.safety} />
          <div className="flex justify-between text-xs font-medium pt-1">
            <span>Total Score</span>
            <span>{Math.round(candidate.qualityScore.total_score * 100)}%</span>
          </div>
        </div>
      )}

      {showMetadata && candidate.metadata && (
        <div className="mt-2 pt-2 border-t border-border/50">
          <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
            {"strategy" in candidate.metadata && candidate.metadata.strategy != null && (
              <span>Strategy: {String(candidate.metadata.strategy)}</span>
            )}
            {"temperature" in candidate.metadata && candidate.metadata.temperature != null && (
              <span>Temp: {Number(candidate.metadata.temperature).toFixed(2)}</span>
            )}
          </div>
        </div>
      )}
    </button>
  );
}

// =============================================================================
// STRATEGY COMPONENTS
// =============================================================================

function ABSelection(props: ABSelectionProps) {
  const { token, isLoading } = useDimensionPanel();
  const { selectCandidate, isSubmitting } = useUQSLFeedback();
  const [selectionMade, setSelectionMade] = useState(false);

  const mappedThemeColor = THEME_COLOR_MAP[token.themeColor] || "violet";

  const handleSelect = useCallback(
    async (selectedId: string, selectedIndex: 0 | 1) => {
      if (props.onSelect) {
        await props.onSelect(selectedId, selectedIndex);
      }

      if (props.sessionId && !selectionMade) {
        try {
          const result = await selectCandidate(props.sessionId, selectedIndex);
          setSelectionMade(true);
          props.onSelectionSubmitted?.(result);
        } catch (error) {
          console.error("[QualitySelection.AB] Failed to submit selection:", error);
        }
      }
    },
    [props, selectionMade, selectCandidate]
  );

  if (!props.candidates) return null;

  return (
    <div className={cn("mt-4", props.className)}>
      <ABComparisonCard
        candidates={props.candidates}
        onSelect={handleSelect}
        onSkip={props.onSkip}
        showMetrics={props.showMetrics}
        labels={props.labels}
        themeColor={mappedThemeColor}
        disabled={props.disabled || isLoading || isSubmitting}
        initialSelected={props.initialSelected}
        compact={props.compact}
      />
      {isSubmitting && (
        <div className="mt-2 text-sm text-muted-foreground animate-pulse">
          선택 결과를 저장하는 중...
        </div>
      )}
    </div>
  );
}

function ThreeWaySelection(props: ThreeWaySelectionProps) {
  const { token, isLoading } = useDimensionPanel();
  const { selectThreeWay, isSubmitting } = useUQSLFeedback();
  const [selectionMade, setSelectionMade] = useState(false);

  const mappedThemeColor = THEME_COLOR_MAP[token.themeColor] || "violet";

  const handleSelect = useCallback(
    async (selected: ThreeWaySelection) => {
      if (props.onSelect) {
        await props.onSelect(selected);
      }

      if (props.sessionId && !selectionMade) {
        try {
          const result = await selectThreeWay(props.sessionId, selected);
          setSelectionMade(true);
          props.onSelectionSubmitted?.(result);
        } catch (error) {
          console.error("[QualitySelection.ThreeWay] Failed to submit selection:", error);
        }
      }
    },
    [props, selectionMade, selectThreeWay]
  );

  if (!props.candidates || !props.candidates.a || !props.candidates.b || !props.candidates.ab) {
    return null;
  }

  return (
    <div className={cn("mt-4", props.className)}>
      <ThreeWayComparison
        candidates={props.candidates}
        onSelect={handleSelect}
        labels={props.labels}
        showConfidence={props.showConfidence}
        recommended={props.recommended}
        themeColor={mappedThemeColor}
        disabled={props.disabled || isLoading || isSubmitting}
        initialSelected={props.initialSelected}
        layout={props.layout}
      />
      {isSubmitting && (
        <div className="mt-2 text-sm text-muted-foreground animate-pulse">
          선택 결과를 저장하는 중...
        </div>
      )}
    </div>
  );
}

function MultiSelection(props: MultiSelectionProps) {
  const { isLoading: panelLoading } = useDimensionPanel();
  const [localSelected, setLocalSelected] = useState<number | null>(null);

  const currentSelected = props.selectedIdx ?? localSelected;
  const isSubmitting = props.isSubmitting ?? false;
  const submitted = props.submitted ?? false;

  const handleSelect = useCallback(
    (idx: number) => {
      if (submitted || isSubmitting) return;
      setLocalSelected(idx);
      props.onSelect?.(idx);
    },
    [submitted, isSubmitting, props]
  );

  const handleSubmit = useCallback(async () => {
    if (currentSelected === null || submitted || isSubmitting) return;
    await props.onSubmit?.(currentSelected);
  }, [currentSelected, submitted, isSubmitting, props]);

  if (!props.candidates || props.candidates.length === 0) return null;

  if (props.isLoading || panelLoading) {
    return (
      <div className={cn("flex flex-col items-center justify-center py-12", props.className)}>
        <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full" />
        <p className="mt-3 text-sm text-muted-foreground">
          Generating {props.candidates.length || 3} candidates...
        </p>
      </div>
    );
  }

  if (props.error) {
    return (
      <div className={cn("p-4 rounded-lg border border-destructive/50 bg-destructive/5", props.className)}>
        <p className="text-sm text-destructive">{props.error}</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", props.className)}>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium">Select the best candidate</h3>
          {props.strategyUsed && (
            <p className="text-xs text-muted-foreground mt-0.5">
              Generated with {STRATEGY_LABELS[props.strategyUsed]}
            </p>
          )}
        </div>
        {props.sessionId && (
          <span className="text-xs text-muted-foreground font-mono">
            {props.sessionId.slice(0, 8)}...
          </span>
        )}
      </div>

      <div
        className={cn(
          "grid gap-3",
          props.candidates.length === 2 && "grid-cols-2",
          props.candidates.length === 3 && "grid-cols-3",
          props.candidates.length >= 4 && "grid-cols-2 lg:grid-cols-4"
        )}
      >
        {props.candidates.map((candidate) => (
          <MultiCandidateCard
            key={candidate.idx}
            candidate={candidate}
            isSelected={currentSelected === candidate.idx}
            isRecommended={props.recommendedIdx === candidate.idx}
            isDisabled={submitted || isSubmitting}
            showQualityScores={props.showQualityScores ?? true}
            showMetadata={props.showMetadata ?? false}
            compact={props.compact ?? false}
            onSelect={() => handleSelect(candidate.idx)}
          />
        ))}
      </div>

      {!submitted && props.onSubmit && (
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={handleSubmit}
            disabled={currentSelected === null || isSubmitting}
            className={cn(
              "px-4 py-2 rounded-md text-sm font-medium transition-colors",
              "bg-primary text-primary-foreground",
              "hover:bg-primary/90",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            {isSubmitting ? "Submitting..." : "Confirm Selection"}
          </button>
        </div>
      )}

      {submitted && (
        <div className="flex items-center gap-2 text-sm text-emerald-600">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Selection saved - feedback recorded for improvement
        </div>
      )}
    </div>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export function QualitySelection(props: QualitySelectionProps) {
  switch (props.strategy) {
    case "ab":
      return <ABSelection {...props} />;
    case "three-way":
      return <ThreeWaySelection {...props} />;
    case "multi":
      return <MultiSelection {...props} />;
    default:
      return null;
  }
}

QualitySelection.displayName = "DimensionPanel.QualitySelection";

// =============================================================================
// HELPER FUNCTIONS (Re-exports for backward compatibility)
// =============================================================================

export function createCandidateData(
  id: string,
  content: string | ReactNode,
  metadata?: CandidateData["metadata"]
): CandidateData {
  return { id, content, metadata };
}

export function createThreeWayCandidateData(
  id: string,
  content: string | ReactNode,
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

export function toMultiGenerateCandidates(
  response: DimensionMultiGenerateResponse
): MultiGenerateCandidate[] {
  return response.candidates.map((c) => ({
    idx: c.idx,
    content: c.content,
    metadata: c.metadata,
    latencyMs: c.latency_ms,
    qualityScore: c.quality_score,
    isRecommended: c.idx === response.recommended_idx,
  }));
}
