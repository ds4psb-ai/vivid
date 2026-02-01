"use client";

/**
 * StoryEngineOverview - Full Workflow Overview for Story Engine
 *
 * Phase 7: Workflow UX Innovation
 *
 * Shows all 3 Story Engine steps at a glance when no specific step is selected.
 * Entry points:
 * - /story-engine (without step param, with existing session)
 * - /story-engine?step=overview
 *
 * Features:
 * - DNA Lab connection status header
 * - 3-column responsive grid (ParallelPreviewGrid)
 * - Click to navigate to step detail
 * - Production bridge when system-prompt completed
 * - Chain data summary (optional)
 *
 * 2026 Pattern: "Overview First, Details on Demand"
 */

import { useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Database,
  ArrowRight,
  BookOpen,
  Link,
  AlertCircle,
  CheckCircle,
  Clapperboard,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useStoryEngineWorkflow } from "@/components/story-engine";
import { ParallelPreviewGrid } from "./ParallelPreviewGrid";
import { STORY_ENGINE_STEPS, CHAIN_DATA_SOURCE_MAP } from "./workflow-configs";
import type {
  WorkflowStepMetadata,
  StepState,
  StepStatus,
  ChainDataEntry,
} from "./types";

// =============================================================================
// Types
// =============================================================================

export interface StoryEngineOverviewProps {
  /** Callback when step card is clicked */
  onStepClick: (stepId: string) => void;
  /** Custom className */
  className?: string;
}

// =============================================================================
// Sub-Components
// =============================================================================

/**
 * Overview header with DNA Lab connection status
 */
function OverviewHeader({
  hasDNALabData,
  hasVPE,
  hasAD,
  className,
}: {
  hasDNALabData: boolean;
  hasVPE: boolean;
  hasAD: boolean;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--stitch-primary)]/20 to-[var(--stitch-primary-accent)]/20 flex items-center justify-center">
            <BookOpen className="w-5 h-5 text-[var(--stitch-primary)]" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-white">
              Story Engine Overview
            </h1>
            <p className="text-sm text-white/50">
              3단계 스토리 구성 워크플로우
            </p>
          </div>
        </div>

        {/* DNA Lab connection status */}
        <div className="flex items-center gap-2">
          {hasDNALabData ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[var(--stitch-primary)]/10 text-[var(--stitch-primary)] text-xs">
              <Link className="w-3.5 h-3.5" />
              <span>DNA Lab 연결됨</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-400 text-xs">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>DNA Lab 미연결</span>
            </div>
          )}
        </div>
      </div>

      {/* Data availability tags */}
      <div className="flex items-center gap-2 ml-[52px]">
        <DataTag
          label="영상 분석 (VPE)"
          available={hasVPE}
        />
        <DataTag
          label="미학 적용 (AD)"
          available={hasAD}
        />
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
 * DNA Lab connection banner (shown when DNA Lab data is missing)
 */
function DNALabConnectionBanner({
  onGoToDNALab,
  className,
}: {
  onGoToDNALab: () => void;
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
              DNA Lab 데이터 필요
            </h3>
            <p className="text-xs text-white/50 mt-0.5">
              Story Engine은 DNA Lab의 영상 분석(VPE)과 미학 적용(AD) 데이터를 기반으로 합니다.
            </p>
          </div>
        </div>
        <button
          onClick={onGoToDNALab}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 transition-colors"
        >
          DNA Lab으로 이동
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

/**
 * Production bridge banner (shown when system-prompt is completed)
 */
function ProductionBridgeBanner({
  onGoToProduction,
  className,
}: {
  onGoToProduction: () => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "p-4 rounded-xl bg-gradient-to-r from-[var(--stitch-primary)]/10 to-[var(--stitch-primary-accent)]/10 border border-[var(--stitch-primary)]/20",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[var(--stitch-primary)]/10 flex items-center justify-center">
            <Clapperboard className="w-5 h-5 text-[var(--stitch-primary)]" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-white">
              시스템 프롬프트 완료!
            </h3>
            <p className="text-xs text-white/50 mt-0.5">
              Production에서 VEO 3.1, Kling 2.6으로 영상을 생성할 준비가 되었습니다.
            </p>
          </div>
        </div>
        <button
          onClick={onGoToProduction}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-[var(--stitch-primary)] text-white hover:opacity-90 transition-opacity"
        >
          Production으로 이동
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

/**
 * Quick action bar
 */
function QuickActionBar({
  hasCompletedSteps,
  hasDNALabData,
  onStartFromFirst,
  className,
}: {
  hasCompletedSteps: boolean;
  hasDNALabData: boolean;
  onStartFromFirst?: () => void;
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
          {!hasDNALabData
            ? "먼저 DNA Lab에서 영상 분석과 미학 적용을 완료하세요."
            : hasCompletedSteps
            ? "진행 중인 작업을 계속하거나 특정 단계를 선택하세요."
            : "단계를 선택하여 시작하세요."}
        </div>
      </div>
      {hasDNALabData && onStartFromFirst && (
        <button
          onClick={onStartFromFirst}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-[var(--stitch-primary)] text-white hover:opacity-90 transition-opacity"
        >
          스토리 설계 시작
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
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
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
      // No inputs required - always ready
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
 * StoryEngineOverview - Full 3-step overview for Story Engine
 *
 * @example
 * ```tsx
 * <StoryEngineOverview
 *   onStepClick={(stepId) => router.push(`/story-engine?step=${stepId}`)}
 * />
 * ```
 */
export function StoryEngineOverview({
  onStepClick,
  className,
}: StoryEngineOverviewProps) {
  const router = useRouter();
  const workflow = useStoryEngineWorkflow();

  const { chainData, goToProduction, goToDNALab } = workflow;

  // Check DNA Lab data availability
  const hasVPE = !!chainData["vpe"];
  const hasAD = !!chainData["ad"];
  const hasDNALabData = hasVPE && hasAD;

  // Check system-prompt completion for Production bridge
  const hasSystemPrompt = !!chainData["system-prompt"];

  // Build chain data entries for display
  const chainDataEntries = useMemo(
    () => buildChainDataEntries(chainData),
    [chainData]
  );

  // Build step states for the grid
  const stepStates = useMemo(
    () => buildStepStates(STORY_ENGINE_STEPS, chainDataEntries),
    [chainDataEntries]
  );

  // Check if any steps are completed
  const hasCompletedSteps = useMemo(
    () => Object.values(stepStates).some((s) => s.status === "completed"),
    [stepStates]
  );

  // Has any Story Engine chain data
  const hasAnyData = useMemo(() => {
    const storyEngineKeys = ["story", "prompt", "system-prompt"];
    return storyEngineKeys.some((key) => !!chainData[key]);
  }, [chainData]);

  // Handle step click - navigate to step detail
  const handleStepClick = useCallback(
    (stepId: string) => {
      onStepClick(stepId);
    },
    [onStepClick]
  );

  // Handle DNA Lab navigation
  const handleGoToDNALab = useCallback(() => {
    goToDNALab("vpe");
  }, [goToDNALab]);

  // Handle Production navigation
  const handleGoToProduction = useCallback(() => {
    goToProduction();
  }, [goToProduction]);

  // Start from first step
  const handleStartFromFirst = useCallback(() => {
    onStepClick("story");
  }, [onStepClick]);

  return (
    <div className={cn("flex flex-col gap-6 p-6", className)}>
      {/* Header with DNA Lab connection status */}
      <OverviewHeader
        hasDNALabData={hasDNALabData}
        hasVPE={hasVPE}
        hasAD={hasAD}
      />

      {/* DNA Lab connection banner (if data missing) */}
      {!hasDNALabData && (
        <DNALabConnectionBanner onGoToDNALab={handleGoToDNALab} />
      )}

      {/* Quick actions bar */}
      <QuickActionBar
        hasCompletedSteps={hasCompletedSteps}
        hasDNALabData={hasDNALabData}
        onStartFromFirst={hasDNALabData ? handleStartFromFirst : undefined}
      />

      {/* 3-step grid */}
      <ParallelPreviewGrid
        steps={STORY_ENGINE_STEPS}
        stepStates={stepStates}
        chainData={chainDataEntries}
        columns={3}
        cardMode="compact"
        onStepClick={handleStepClick}
        currentApp="story-engine"
        animate={true}
      />

      {/* Production bridge (when system-prompt is complete) */}
      {hasSystemPrompt && (
        <ProductionBridgeBanner onGoToProduction={handleGoToProduction} />
      )}

      {/* Chain data summary (if any Story Engine data exists) */}
      {hasAnyData && <ChainDataSummary chainData={chainDataEntries} />}
    </div>
  );
}

export default StoryEngineOverview;
