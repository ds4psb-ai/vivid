"use client";

/**
 * DNALabWorkflowProgress - Horizontal Stepper UI
 *
 * 2026 Trends:
 * - Non-sequential access (click any step)
 * - Visual completion indicators
 * - Missing data warnings (non-blocking)
 * - Mobile-responsive (vertical on small screens)
 * - Pipeline execution status integration
 * - Real-time step highlighting with credits/time display
 */

import { Check, AlertCircle, Sparkles, Loader2, Clock, Coins } from "lucide-react";
import { cn } from "@/lib/utils";
import { useDNALabWorkflow, type StepState } from "./hooks/useDNALabWorkflow";
import { DNA_LAB_STEPS, DNA_LAB_STEP_THEMES, type DNALabStepId } from "./constants";
import type { StepExecutionStatus, PipelineStepId, LegacyPipelineStepId } from "./hooks/useDNALabPipeline";

/**
 * Map legacy pipeline step IDs to DNA Lab step IDs
 * Phase 1-2: VPE and AD pipeline steps map to merged "analysis" step
 * Backend still returns legacy step IDs (vpe, ad), so we need this mapping
 */
const PIPELINE_TO_STEP_MAP: Record<LegacyPipelineStepId, DNALabStepId> = {
  vpe: "analysis",
  ad: "analysis",
  mirror: "mirror",
  qc: "qc",
};

interface DNALabWorkflowProgressProps {
  /** Compact mode for narrow spaces */
  compact?: boolean;
  /** Show AI inference indicator */
  showInferenceHint?: boolean;
  /** Custom class name */
  className?: string;
  /** Pipeline execution status (from useDNALabPipeline) */
  pipelineSteps?: StepExecutionStatus[];
  /** Currently running pipeline step (uses legacy step IDs from backend) */
  pipelineCurrentStep?: LegacyPipelineStepId | null;
  /** Is pipeline currently running */
  isPipelineRunning?: boolean;
}

/**
 * Workflow progress stepper for DNA Lab
 */
export function DNALabWorkflowProgress({
  compact = false,
  showInferenceHint = true,
  className,
  pipelineSteps,
  pipelineCurrentStep,
  isPipelineRunning = false,
}: DNALabWorkflowProgressProps) {
  const { steps, currentStepId, goToStep, completionPercentage, canInferForStep } =
    useDNALabWorkflow();

  // Get pipeline status for a step
  // For "analysis" step, we need to find vpe or ad status (whichever is available)
  const getPipelineStatus = (stepId: DNALabStepId): StepExecutionStatus | undefined => {
    if (!pipelineSteps) return undefined;
    // Find all legacy step IDs that map to this step
    const legacyIds = Object.entries(PIPELINE_TO_STEP_MAP)
      .filter(([, id]) => id === stepId)
      .map(([legacyId]) => legacyId as LegacyPipelineStepId);
    // Return first matching pipeline status
    return pipelineSteps.find((s) => legacyIds.includes(s.step));
  };

  // Check if a step is currently running in the pipeline
  const isStepRunning = (stepId: DNALabStepId): boolean => {
    if (!pipelineCurrentStep) return false;
    return PIPELINE_TO_STEP_MAP[pipelineCurrentStep] === stepId;
  };

  return (
    <div className={cn("w-full", className)}>
      {/* Progress bar */}
      <div className="mb-4 hidden sm:block">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-white/40">워크플로우 진행</span>
          <span className="text-xs text-white/60">{completionPercentage}%</span>
        </div>
        <div className="h-1 bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-500"
            style={{ width: `${completionPercentage}%` }}
          />
        </div>
      </div>

      {/* Steps - Horizontal on desktop, vertical on mobile */}
      <div
        className={cn(
          "flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-0",
          compact && "sm:gap-2"
        )}
      >
        {steps.map((stepState, index) => (
          <StepItem
            key={stepState.step.id}
            stepState={stepState}
            index={index}
            isLast={index === steps.length - 1}
            isCurrent={stepState.step.id === currentStepId}
            compact={compact}
            showInferenceHint={showInferenceHint && canInferForStep(stepState.step.id)}
            onClick={() => goToStep(stepState.step.id)}
            pipelineStatus={getPipelineStatus(stepState.step.id)}
            isRunning={isStepRunning(stepState.step.id)}
            isPipelineMode={isPipelineRunning}
          />
        ))}
      </div>
    </div>
  );
}

interface StepItemProps {
  stepState: StepState;
  index: number;
  isLast: boolean;
  isCurrent: boolean;
  compact: boolean;
  showInferenceHint: boolean;
  onClick: () => void;
  pipelineStatus?: StepExecutionStatus;
  isRunning?: boolean;
  isPipelineMode?: boolean;
}

function StepItem({
  stepState,
  index,
  isLast,
  isCurrent,
  compact,
  showInferenceHint,
  onClick,
  pipelineStatus,
  isRunning = false,
  isPipelineMode = false,
}: StepItemProps) {
  const { step, status, hasData, missingInputs } = stepState;
  const Icon = step.icon;
  const theme = DNA_LAB_STEP_THEMES[step.id];

  // In pipeline mode, use pipeline status over workflow status
  const isCompleted =
    pipelineStatus?.status === "completed" || status === "completed";
  const isPipelineCompleted = pipelineStatus?.status === "completed";
  const isPipelineFailed = pipelineStatus?.status === "failed";
  const hasMissingInputs = missingInputs.length > 0;

  return (
    <div className="flex items-center flex-1 sm:flex-initial">
      {/* Step button */}
      <button
        onClick={onClick}
        className={cn(
          "group relative flex items-center gap-3 sm:flex-col sm:gap-2 p-3 sm:p-4 rounded-xl transition-all duration-200",
          "hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-white/20",
          // Mobile: full width row
          "w-full sm:w-auto",
          // Current step highlight
          isCurrent && "bg-white/10 ring-1 ring-white/20",
          // Completed step
          isCompleted && "bg-white/5"
        )}
      >
        {/* Step icon with status indicator */}
        <div className="relative">
          <div
            className={cn(
              "w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center transition-all",
              // Base styles
              "border-2",
              // Status-based styles
              isCompleted && !isPipelineFailed && "bg-emerald-500/20 border-emerald-500",
              isPipelineFailed && "bg-red-500/20 border-red-500",
              isRunning && "bg-cyan-500/20 border-cyan-500 animate-pulse",
              isCurrent && !isCompleted && !isRunning && !isPipelineFailed && "bg-white/10 border-white/40",
              !isCurrent && !isCompleted && !isRunning && !isPipelineFailed && "bg-white/5 border-white/20",
              // Hover effect
              "group-hover:scale-105"
            )}
            style={{
              borderColor: isRunning ? theme.color : isCurrent ? theme.color : undefined,
              boxShadow: isRunning
                ? `0 0 25px ${theme.color}60`
                : isCurrent
                ? `0 0 20px ${theme.color}40`
                : undefined,
            }}
          >
            {/* Icon based on status */}
            {isRunning ? (
              <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
            ) : isPipelineFailed ? (
              <AlertCircle className="w-5 h-5 text-red-400" />
            ) : isCompleted ? (
              <Check className="w-5 h-5 text-emerald-400" />
            ) : (
              <Icon
                className={cn(
                  "w-5 h-5 transition-colors",
                  isCurrent ? "text-white" : "text-white/60"
                )}
              />
            )}
          </div>

          {/* Missing input warning badge */}
          {!isCompleted && hasMissingInputs && (
            <div
              className={cn(
                "absolute -top-1 -right-1 w-4 h-4 rounded-full flex items-center justify-center",
                "bg-amber-500/80"
              )}
              title={`${missingInputs.length}개 입력 미완료`}
            >
              <AlertCircle className="w-3 h-3 text-white" />
            </div>
          )}

          {/* AI inference hint badge */}
          {showInferenceHint && !isCompleted && (
            <div
              className={cn(
                "absolute -bottom-1 -right-1 w-4 h-4 rounded-full flex items-center justify-center",
                "bg-purple-500/80"
              )}
              title="AI 추론 가능"
            >
              <Sparkles className="w-2.5 h-2.5 text-white" />
            </div>
          )}
        </div>

        {/* Step info */}
        <div className={cn("flex-1 sm:flex-initial text-left sm:text-center", compact && "hidden sm:block")}>
          <div
            className={cn(
              "text-sm font-medium transition-colors",
              isRunning && "text-cyan-400",
              isPipelineFailed && "text-red-400",
              isCurrent && !isRunning && "text-white",
              isCompleted && !isPipelineFailed && "text-emerald-400",
              !isCurrent && !isCompleted && !isRunning && "text-white/60"
            )}
          >
            {step.label}
          </div>
          {/* Pipeline execution stats */}
          {isPipelineMode && pipelineStatus && (
            <div className="flex items-center gap-2 justify-center mt-1">
              {pipelineStatus.duration_ms && (
                <span className="text-[10px] text-white/40 flex items-center gap-0.5">
                  <Clock className="w-3 h-3" />
                  {(pipelineStatus.duration_ms / 1000).toFixed(1)}s
                </span>
              )}
              {pipelineStatus.credits_used && (
                <span className="text-[10px] text-amber-400/60 flex items-center gap-0.5">
                  <Coins className="w-3 h-3" />
                  {pipelineStatus.credits_used}
                </span>
              )}
            </div>
          )}
          {!compact && !isPipelineMode && (
            <div className="text-xs text-white/40 mt-0.5 hidden sm:block">{step.description}</div>
          )}
        </div>

        {/* Mobile: status badge */}
        <div className="sm:hidden">
          {isRunning ? (
            <span className="text-xs text-cyan-400 px-2 py-1 bg-cyan-500/10 rounded animate-pulse">
              실행 중
            </span>
          ) : isPipelineFailed ? (
            <span className="text-xs text-red-400 px-2 py-1 bg-red-500/10 rounded">
              실패
            </span>
          ) : isCompleted ? (
            <span className="text-xs text-emerald-400 px-2 py-1 bg-emerald-500/10 rounded">
              완료
            </span>
          ) : isCurrent ? (
            <span className="text-xs text-cyan-400 px-2 py-1 bg-cyan-500/10 rounded">진행 중</span>
          ) : hasMissingInputs ? (
            <span className="text-xs text-amber-400 px-2 py-1 bg-amber-500/10 rounded">
              대기
            </span>
          ) : null}
        </div>
      </button>

      {/* Connector line (desktop only, not after last step) */}
      {!isLast && (
        <div
          className={cn(
            "hidden sm:block h-0.5 flex-1 mx-2 transition-colors",
            isCompleted ? "bg-emerald-500/50" : "bg-white/10"
          )}
        />
      )}
    </div>
  );
}

/**
 * Compact version for sidebar/header usage
 */
export function DNALabWorkflowProgressCompact({ className }: { className?: string }) {
  return <DNALabWorkflowProgress compact showInferenceHint={false} className={className} />;
}
