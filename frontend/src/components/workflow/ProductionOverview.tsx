"use client";

/**
 * ProductionOverview - Full Workflow Overview for Production
 *
 * Phase 12: Workflow UX Innovation - Integration
 *
 * Shows all 3 Production steps at a glance when no specific step is selected.
 * Entry points:
 * - /production (without step param)
 * - /production?step=overview
 *
 * Features:
 * - Story Engine connection status header
 * - 3-column responsive grid (ParallelPreviewGrid)
 * - SmartProviderSelector integration
 * - CostEstimator preview
 * - Click to navigate to step detail
 *
 * 2026 Pattern: "Overview First, Details on Demand"
 */

import { useMemo, useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Database,
  ArrowRight,
  Clapperboard,
  Link,
  AlertCircle,
  CheckCircle,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useProductionWorkflow } from "@/components/production";
import { ParallelPreviewGrid } from "./ParallelPreviewGrid";
import { SmartProviderSelector } from "./SmartProviderSelector";
import { CostEstimator } from "./CostEstimator";
import { PRODUCTION_STEPS } from "./workflow-configs";
import type {
  WorkflowStepMetadata,
  StepState,
  StepStatus,
  ChainDataEntry,
} from "./types";
import type { ProviderId } from "./hooks/types";

// =============================================================================
// Types
// =============================================================================

export interface ProductionOverviewProps {
  /** Callback when step card is clicked */
  onStepClick: (stepId: string) => void;
  /** Custom className */
  className?: string;
}

// =============================================================================
// Sub-Components
// =============================================================================

/**
 * Overview header with Story Engine connection status
 */
function OverviewHeader({
  hasStoryEngineData,
  hasSystemPrompt,
  hasStory,
  className,
}: {
  hasStoryEngineData: boolean;
  hasSystemPrompt: boolean;
  hasStory: boolean;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--stitch-primary)]/20 to-[var(--stitch-primary-accent)]/20 flex items-center justify-center">
            <Clapperboard className="w-5 h-5 text-[var(--stitch-primary)]" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-white">
              Production Overview
            </h1>
            <p className="text-sm text-white/50">
              3개 Provider로 미디어 생성
            </p>
          </div>
        </div>

        {/* Story Engine connection status */}
        <div className="flex items-center gap-2">
          {hasStoryEngineData ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[var(--stitch-primary)]/10 text-[var(--stitch-primary)] text-xs">
              <Link className="w-3.5 h-3.5" />
              <span>Story Engine 연결됨</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-400 text-xs">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>Story Engine 미연결</span>
            </div>
          )}
        </div>
      </div>

      {/* Data availability tags */}
      <div className="flex items-center gap-2 ml-[52px]">
        <DataTag label="시스템 프롬프트" available={hasSystemPrompt} />
        <DataTag label="스토리 데이터" available={hasStory} />
      </div>
    </div>
  );
}

/**
 * Small tag showing data availability
 */
function DataTag({ label, available }: { label: string; available: boolean }) {
  return (
    <span
      className={cn(
        "text-xs px-2 py-0.5 rounded flex items-center gap-1",
        available
          ? "bg-[var(--stitch-primary)]/10 text-[var(--stitch-primary)]"
          : "bg-white/5 text-white/40"
      )}
    >
      {available ? (
        <CheckCircle className="w-3 h-3" />
      ) : (
        <div className="w-3 h-3 rounded-full border border-current opacity-50" />
      )}
      {label}
    </span>
  );
}

/**
 * Story Engine connection banner (shown when data is missing)
 */
function StoryEngineConnectionBanner({
  onGoToStoryEngine,
  className,
}: {
  onGoToStoryEngine: () => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "p-4 rounded-xl bg-amber-500/5 border border-amber-500/20",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
            <Database className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-white">
              Story Engine 데이터 필요
            </h3>
            <p className="text-xs text-white/50 mt-0.5">
              Production은 Story Engine의 시스템 프롬프트를 기반으로 합니다.
            </p>
          </div>
        </div>
        <button
          onClick={onGoToStoryEngine}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 transition-colors"
        >
          Story Engine으로 이동
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

/**
 * Quick provider selection panel
 */
function QuickProviderPanel({
  selectedProvider,
  onProviderChange,
  onStartGeneration,
  hasSystemPrompt,
  className,
}: {
  selectedProvider: ProviderId;
  onProviderChange: (id: ProviderId) => void;
  onStartGeneration: () => void;
  hasSystemPrompt: boolean;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "p-4 rounded-xl bg-white/[0.02] border border-white/5",
        className
      )}
    >
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="w-4 h-4 text-cyan-400" />
        <h3 className="text-sm font-medium text-white">빠른 시작</h3>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Provider Selector */}
        <div>
          <SmartProviderSelector
            value={selectedProvider}
            onChange={onProviderChange}
            mediaType="video"
            compact
          />
        </div>

        {/* Cost Estimator + Action */}
        <div className="flex flex-col gap-3">
          <CostEstimator provider={selectedProvider} compact />
          <button
            onClick={onStartGeneration}
            disabled={!hasSystemPrompt}
            className={cn(
              "flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-all",
              hasSystemPrompt
                ? "bg-[var(--stitch-primary)] text-white hover:opacity-90"
                : "bg-white/5 text-white/30 cursor-not-allowed"
            )}
          >
            {hasSystemPrompt ? (
              <>
                생성 시작
                <ArrowRight className="w-4 h-4" />
              </>
            ) : (
              "시스템 프롬프트 필요"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Chain data summary
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
        <h3 className="text-sm font-medium text-white/60">생성 결과</h3>
        <span className="text-xs text-white/30 ml-auto">
          {entries.length}개 완료
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {entries.map(([key, entry]) => (
          <div key={key} className="p-2 rounded-lg bg-black/20 text-xs">
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
 * Convert chain data object to ChainDataEntry format
 */
function buildChainDataEntries(
  rawChainData: Record<string, Record<string, unknown>>
): Record<string, ChainDataEntry> {
  const entries: Record<string, ChainDataEntry> = {};

  for (const [key, value] of Object.entries(rawChainData)) {
    if (value && typeof value === "object") {
      entries[key] = {
        key,
        output: value,
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
 * ProductionOverview - Full 3-step overview for Production
 *
 * @example
 * ```tsx
 * <ProductionOverview
 *   onStepClick={(stepId) => router.push(`/production?step=${stepId}`)}
 * />
 * ```
 */
export function ProductionOverview({
  onStepClick,
  className,
}: ProductionOverviewProps) {
  const router = useRouter();
  const workflow = useProductionWorkflow();
  const [selectedProvider, setSelectedProvider] = useState<ProviderId>("veo");

  const { chainData, goToStoryEngine } = workflow;

  // Check Story Engine data availability
  const hasSystemPrompt = !!chainData["system-prompt"];
  const hasStory = !!chainData["story"];
  const hasStoryEngineData = hasSystemPrompt;

  // Build chain data entries for display
  const chainDataEntries = useMemo(
    () => buildChainDataEntries(chainData),
    [chainData]
  );

  // Build step states for the grid
  const stepStates = useMemo(
    () => buildStepStates(PRODUCTION_STEPS, chainDataEntries),
    [chainDataEntries]
  );

  // Has any Production output
  const hasAnyOutput = useMemo(() => {
    const productionKeys = ["veo", "kling", "suno"];
    return productionKeys.some((key) => !!chainData[key]);
  }, [chainData]);

  // Handle step click
  const handleStepClick = useCallback(
    (stepId: string) => {
      onStepClick(stepId);
    },
    [onStepClick]
  );

  // Handle Story Engine navigation
  const handleGoToStoryEngine = useCallback(() => {
    goToStoryEngine("system-prompt");
  }, [goToStoryEngine]);

  // Handle start generation
  const handleStartGeneration = useCallback(() => {
    onStepClick(selectedProvider);
  }, [onStepClick, selectedProvider]);

  return (
    <div className={cn("flex flex-col gap-6 p-6", className)}>
      {/* Header with Story Engine connection status */}
      <OverviewHeader
        hasStoryEngineData={hasStoryEngineData}
        hasSystemPrompt={hasSystemPrompt}
        hasStory={hasStory}
      />

      {/* Story Engine connection banner (if data missing) */}
      {!hasStoryEngineData && (
        <StoryEngineConnectionBanner onGoToStoryEngine={handleGoToStoryEngine} />
      )}

      {/* Quick provider selection panel */}
      <QuickProviderPanel
        selectedProvider={selectedProvider}
        onProviderChange={setSelectedProvider}
        onStartGeneration={handleStartGeneration}
        hasSystemPrompt={hasSystemPrompt}
      />

      {/* 3-step grid */}
      <ParallelPreviewGrid
        steps={PRODUCTION_STEPS}
        stepStates={stepStates}
        chainData={chainDataEntries}
        columns={3}
        cardMode="compact"
        onStepClick={handleStepClick}
        currentApp="production"
        animate={true}
      />

      {/* Chain data summary (if any output exists) */}
      {hasAnyOutput && <ChainDataSummary chainData={chainDataEntries} />}
    </div>
  );
}

export default ProductionOverview;
