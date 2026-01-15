"use client";

/**
 * MultiGenerateWrapper - DimensionPanel.MultiGenerate compound component
 *
 * Wraps UQSL multi-candidate generation with dimension theming
 * for N-way comparison with quality scores.
 *
 * 2026 Best Practice:
 * - Diversified Sampling strategies (verbalized, diversified, compute_optimal)
 * - G-Eval Chain-of-Thought quality evaluation
 * - Dynamic Thompson Sampling feedback integration
 * - SSE streaming for real-time progress
 *
 * @see UQSL_SPEC.md - Universal Quality Selection Layer
 */

import { type ReactNode, useCallback, useState } from "react";
import { useDimensionPanel } from "./DimensionPanelContext";
import {
  type DimensionMultiGenerateResponse,
  type DimensionDiversityStrategy,
  type UQSLQualityScore,
} from "@/lib/api";

/** Simple class name utility (inline to avoid external dependency) */
function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(" ");
}

// =============================================================================
// TYPES
// =============================================================================

export interface MultiGenerateCandidate {
  idx: number;
  content: string | ReactNode;
  metadata?: Record<string, unknown>;
  latencyMs?: number;
  qualityScore?: UQSLQualityScore;
  isRecommended?: boolean;
}

export interface MultiGenerateWrapperProps {
  /** Generated candidates */
  candidates: MultiGenerateCandidate[];
  /** Session ID for Thompson Sampling */
  sessionId?: string;
  /** Index of the recommended candidate */
  recommendedIdx?: number;
  /** Strategy used for generation */
  strategyUsed?: DimensionDiversityStrategy;
  /** Currently selected candidate index */
  selectedIdx?: number;
  /** Callback when candidate is selected */
  onSelect?: (idx: number) => void;
  /** Callback when selection is submitted */
  onSubmit?: (idx: number, rating?: number) => Promise<void>;
  /** Whether selection has been submitted */
  submitted?: boolean;
  /** Whether submission is in progress */
  isSubmitting?: boolean;
  /** Show quality score breakdown */
  showQualityScores?: boolean;
  /** Show candidate metadata */
  showMetadata?: boolean;
  /** Compact mode */
  compact?: boolean;
  /** Additional className */
  className?: string;
  /** Loading state */
  isLoading?: boolean;
  /** Error message */
  error?: string;
}

// =============================================================================
// THEME COLOR MAP
// =============================================================================

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

function CandidateCard({
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
      {/* Header */}
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

      {/* Content */}
      <div
        className={cn(
          "text-sm text-foreground/90",
          compact ? "line-clamp-3" : "line-clamp-6"
        )}
      >
        {candidate.content}
      </div>

      {/* Quality Scores */}
      {showQualityScores && candidate.qualityScore && (
        <div className="mt-3 pt-3 border-t border-border/50 space-y-1.5">
          <QualityScoreBar
            label="Groundedness"
            value={candidate.qualityScore.groundedness}
            color={QUALITY_BAR_COLORS.groundedness}
          />
          <QualityScoreBar
            label="Relevance"
            value={candidate.qualityScore.relevance}
            color={QUALITY_BAR_COLORS.relevance}
          />
          <QualityScoreBar
            label="Coherence"
            value={candidate.qualityScore.coherence}
            color={QUALITY_BAR_COLORS.coherence}
          />
          <QualityScoreBar
            label="Creativity"
            value={candidate.qualityScore.creativity}
            color={QUALITY_BAR_COLORS.creativity}
          />
          <QualityScoreBar
            label="Safety"
            value={candidate.qualityScore.safety}
            color={QUALITY_BAR_COLORS.safety}
          />
          <div className="flex justify-between text-xs font-medium pt-1">
            <span>Total Score</span>
            <span>{Math.round(candidate.qualityScore.total_score * 100)}%</span>
          </div>
        </div>
      )}

      {/* Metadata */}
      {showMetadata && candidate.metadata && (
        <div className="mt-2 pt-2 border-t border-border/50">
          <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
            {"strategy" in candidate.metadata && candidate.metadata.strategy != null && (
              <span>Strategy: {String(candidate.metadata.strategy)}</span>
            )}
            {"temperature" in candidate.metadata && candidate.metadata.temperature != null && (
              <span>Temp: {Number(candidate.metadata.temperature).toFixed(2)}</span>
            )}
            {"seed" in candidate.metadata && candidate.metadata.seed != null && (
              <span>Seed: {String(candidate.metadata.seed)}</span>
            )}
          </div>
        </div>
      )}
    </button>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export function MultiGenerateWrapper({
  candidates,
  sessionId,
  recommendedIdx,
  strategyUsed,
  selectedIdx,
  onSelect,
  onSubmit,
  submitted = false,
  isSubmitting = false,
  showQualityScores = true,
  showMetadata = false,
  compact = false,
  className = "",
  isLoading = false,
  error,
}: MultiGenerateWrapperProps) {
  const { token, isLoading: panelLoading } = useDimensionPanel();
  const [localSelected, setLocalSelected] = useState<number | null>(null);

  const currentSelected = selectedIdx ?? localSelected;

  // Handle candidate selection
  const handleSelect = useCallback(
    (idx: number) => {
      if (submitted || isSubmitting) return;
      setLocalSelected(idx);
      onSelect?.(idx);
    },
    [submitted, isSubmitting, onSelect]
  );

  // Handle submit
  const handleSubmit = useCallback(async () => {
    if (currentSelected === null || submitted || isSubmitting) return;
    await onSubmit?.(currentSelected);
  }, [currentSelected, submitted, isSubmitting, onSubmit]);

  // Don't render if no candidates
  if (!candidates || candidates.length === 0) return null;

  // Loading state
  if (isLoading || panelLoading) {
    return (
      <div className={cn("flex flex-col items-center justify-center py-12", className)}>
        <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full" />
        <p className="mt-3 text-sm text-muted-foreground">
          Generating {candidates.length || 3} candidates...
        </p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={cn("p-4 rounded-lg border border-destructive/50 bg-destructive/5", className)}>
        <p className="text-sm text-destructive">{error}</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium">
            Select the best candidate
          </h3>
          {strategyUsed && (
            <p className="text-xs text-muted-foreground mt-0.5">
              Generated with {STRATEGY_LABELS[strategyUsed]}
            </p>
          )}
        </div>
        {sessionId && (
          <span className="text-xs text-muted-foreground font-mono">
            {sessionId.slice(0, 8)}...
          </span>
        )}
      </div>

      {/* Candidates Grid */}
      <div
        className={cn(
          "grid gap-3",
          candidates.length === 2 && "grid-cols-2",
          candidates.length === 3 && "grid-cols-3",
          candidates.length >= 4 && "grid-cols-2 lg:grid-cols-4"
        )}
      >
        {candidates.map((candidate) => (
          <CandidateCard
            key={candidate.idx}
            candidate={candidate}
            isSelected={currentSelected === candidate.idx}
            isRecommended={recommendedIdx === candidate.idx}
            isDisabled={submitted || isSubmitting}
            showQualityScores={showQualityScores}
            showMetadata={showMetadata}
            compact={compact}
            onSelect={() => handleSelect(candidate.idx)}
          />
        ))}
      </div>

      {/* Submit Button */}
      {!submitted && onSubmit && (
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

      {/* Submitted State */}
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

MultiGenerateWrapper.displayName = "DimensionPanel.MultiGenerate";

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Convert API response to MultiGenerateCandidate array
 */
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

/**
 * Create a candidate from raw data
 */
export function createMultiGenerateCandidate(
  idx: number,
  content: string | ReactNode,
  options?: Partial<MultiGenerateCandidate>
): MultiGenerateCandidate {
  return {
    idx,
    content,
    ...options,
  };
}
