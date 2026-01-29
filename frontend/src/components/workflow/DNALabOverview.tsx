"use client";

/**
 * DNALabOverview - Full Workflow Overview for DNA Lab
 *
 * Phase 6: Workflow UX Innovation
 *
 * Shows all 4 DNA Lab steps at a glance when no specific step is selected.
 * Entry points:
 * - /dna-lab (with existing session)
 * - /dna-lab?ip=slug
 * - /dna-lab?step=overview
 *
 * Features:
 * - IP context header when connected
 * - 4-column responsive grid (ParallelPreviewGrid)
 * - Click to navigate to step detail
 * - Session restoration indicator
 * - Chain data summary (optional)
 *
 * 2026 Pattern: "Overview First, Details on Demand"
 */

import { useMemo, useCallback } from "react";
import { Database, Clock, ArrowRight, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { useIPChainData } from "./hooks/useIPChainData";
import { ParallelPreviewGrid } from "./ParallelPreviewGrid";
import { DNA_LAB_STEPS } from "./workflow-configs";
import type {
  WorkflowStepMetadata,
  StepState,
  StepStatus,
  ChainDataEntry,
} from "./types";

// =============================================================================
// Types
// =============================================================================

export interface DNALabOverviewProps {
  /** IP slug for data loading */
  ipSlug?: string | null;
  /** Callback when step card is clicked */
  onStepClick: (stepId: string) => void;
  /** Custom className */
  className?: string;
}

// =============================================================================
// Sub-Components
// =============================================================================

/**
 * Overview header with IP info or default title
 */
function OverviewHeader({
  ipData,
  sessionRestored,
  hasExistingSession,
  className,
}: {
  ipData?: { name_ko: string; slug: string; genre?: string[] } | null;
  sessionRestored: boolean;
  hasExistingSession: boolean;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 to-violet-500/20 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-white">
              {ipData ? ipData.name_ko : "DNA Lab Overview"}
            </h1>
            <p className="text-sm text-white/50">
              {ipData
                ? `프로젝트: ${ipData.slug}`
                : "4단계 통합 워크플로우"}
            </p>
          </div>
        </div>

        {/* Session status badges */}
        <div className="flex items-center gap-2">
          {ipData && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-violet-500/10 text-violet-400 text-xs">
              <Database className="w-3.5 h-3.5" />
              <span className="font-medium">{ipData.slug}</span>
            </div>
          )}
          {sessionRestored && hasExistingSession && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 text-xs">
              <Clock className="w-3.5 h-3.5" />
              <span>세션 복원됨</span>
            </div>
          )}
        </div>
      </div>

      {/* Genre tags if available */}
      {ipData?.genre && ipData.genre.length > 0 && (
        <div className="flex items-center gap-2 ml-[52px]">
          {ipData.genre.slice(0, 3).map((g) => (
            <span
              key={g}
              className="text-xs px-2 py-0.5 rounded bg-white/5 text-white/40"
            >
              {g}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Quick action bar for common workflows
 */
function QuickActionBar({
  onStartPipeline,
  hasCompletedSteps,
  className,
}: {
  onStartPipeline?: () => void;
  hasCompletedSteps: boolean;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-center justify-between p-4 rounded-xl bg-white/[0.02] border border-white/5",
        className
      )}
    >
      <div className="flex items-center gap-3">
        <div className="text-sm text-white/60">
          {hasCompletedSteps
            ? "진행 중인 작업을 계속하거나 특정 단계를 선택하세요."
            : "단계를 선택하여 시작하거나 전체 파이프라인을 실행하세요."}
        </div>
      </div>
      {onStartPipeline && (
        <button
          onClick={onStartPipeline}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-gradient-to-r from-cyan-500 to-violet-500 text-white hover:opacity-90 transition-opacity"
        >
          전체 실행
          <ArrowRight className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

/**
 * Chain data summary (optional, shown when data exists)
 */
function ChainDataSummary({
  chainData,
  className,
}: {
  chainData: Record<string, ChainDataEntry>;
  className?: string;
}) {
  const entries = Object.entries(chainData).filter(
    ([_, entry]) => entry && entry.output
  );

  if (entries.length === 0) return null;

  return (
    <div
      className={cn(
        "p-4 rounded-xl bg-white/[0.02] border border-white/5",
        className
      )}
    >
      <div className="flex items-center gap-2 mb-3">
        <Database className="w-4 h-4 text-white/40" />
        <h3 className="text-sm font-medium text-white/60">
          체인 데이터 요약
        </h3>
        <span className="text-xs text-white/30 ml-auto">
          {entries.length}개 단계 완료
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {entries.map(([key, entry]) => (
          <div
            key={key}
            className="p-2 rounded-lg bg-black/20 text-xs"
          >
            <div className="font-medium text-white/70 mb-1">
              {key.toUpperCase()}
            </div>
            <div className="text-white/40 line-clamp-2">
              {entry.summary || `${Object.keys(entry.output).length} properties`}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Build step states from chain data for ParallelPreviewGrid
 */
function buildStepStates(
  steps: WorkflowStepMetadata[],
  chainData: Record<string, ChainDataEntry>
): Record<string, StepState> {
  const states: Record<string, StepState> = {};

  for (const step of steps) {
    const hasData = !!chainData[step.id]?.output;
    const missingInputs = step.inputs.filter(
      (inputKey) => !chainData[inputKey]?.output
    );

    let status: StepStatus = "pending";
    if (hasData) {
      status = "completed";
    } else if (missingInputs.length === 0 && step.inputs.length > 0) {
      // Has all inputs but no output - ready to run
      status = "pending";
    } else if (step.inputs.length === 0) {
      // First step (VPE) - always ready
      status = "pending";
    }

    states[step.id] = {
      step,
      status,
      hasData,
      missingInputs,
      canInfer: step.canInfer ?? false,
    };
  }

  return states;
}

/**
 * Convert IP chain data to ChainDataEntry format
 */
function buildChainDataEntries(
  partialData: Partial<Record<string, unknown>>
): Record<string, ChainDataEntry> {
  const entries: Record<string, ChainDataEntry> = {};

  for (const [key, value] of Object.entries(partialData)) {
    if (value && typeof value === "object") {
      entries[key] = {
        key,
        output: value as Record<string, unknown>,
        timestamp: Date.now(),
      };
    }
  }

  return entries;
}

// =============================================================================
// Main Component
// =============================================================================

/**
 * DNALabOverview - Full 4-step overview for DNA Lab
 *
 * @example
 * ```tsx
 * <DNALabOverview
 *   ipSlug={ipSlug}
 *   onStepClick={(stepId) => router.push(`/dna-lab?step=${stepId}`)}
 * />
 * ```
 */
export function DNALabOverview({
  ipSlug,
  onStepClick,
  className,
}: DNALabOverviewProps) {
  // Load IP + chain data
  const {
    ipData,
    ipLoading,
    partialData,
    sessionRestored,
    hasExistingSession,
  } = useIPChainData({
    ipSlug: ipSlug ?? null,
    autoFetchIP: !!ipSlug,
    autoRestoreSession: true,
  });

  // Build chain data entries from partial data
  const chainData = useMemo(
    () => buildChainDataEntries(partialData),
    [partialData]
  );

  // Build step states for the grid
  const stepStates = useMemo(
    () => buildStepStates(DNA_LAB_STEPS, chainData),
    [chainData]
  );

  // Check if any steps are completed
  const hasCompletedSteps = useMemo(
    () => Object.values(stepStates).some((s) => s.status === "completed"),
    [stepStates]
  );

  // Has any chain data
  const hasAnyData = useMemo(
    () => Object.keys(chainData).length > 0,
    [chainData]
  );

  // Handle step click - navigate to step detail
  const handleStepClick = useCallback(
    (stepId: string) => {
      onStepClick(stepId);
    },
    [onStepClick]
  );

  // Loading state
  if (ipSlug && ipLoading) {
    return (
      <div className={cn("flex flex-col gap-6 p-6", className)}>
        <div className="animate-pulse flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-white/10" />
          <div className="flex-1">
            <div className="h-5 w-48 bg-white/10 rounded mb-2" />
            <div className="h-4 w-32 bg-white/5 rounded" />
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="h-32 rounded-xl bg-white/5 animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col gap-6 p-6", className)}>
      {/* Header with IP info */}
      <OverviewHeader
        ipData={ipData}
        sessionRestored={sessionRestored}
        hasExistingSession={hasExistingSession}
      />

      {/* Quick actions bar */}
      <QuickActionBar hasCompletedSteps={hasCompletedSteps} />

      {/* 4-step grid */}
      <ParallelPreviewGrid
        steps={DNA_LAB_STEPS}
        stepStates={stepStates}
        chainData={chainData}
        columns={4}
        cardMode="compact"
        onStepClick={handleStepClick}
        currentApp="dna-lab"
        animate={true}
      />

      {/* Chain data summary (if data exists) */}
      {hasAnyData && <ChainDataSummary chainData={chainData} />}
    </div>
  );
}

export default DNALabOverview;
