"use client";

/**
 * UnifiedWorkflowProgress - Horizontal Stepper UI
 *
 * Unified progress stepper for all Mega Apps.
 * Adapts to each app's configuration.
 *
 * 2026 Trends:
 * - Non-sequential access (click any step)
 * - Visual completion indicators
 * - Missing data warnings (non-blocking)
 * - Mobile-responsive (vertical on small screens)
 */

import { Check, AlertCircle, Sparkles, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { WorkflowConfig, UnifiedWorkflowState, StepState } from "./types";

interface UnifiedWorkflowProgressProps {
  /** Workflow state from useUnifiedWorkflow */
  workflow: UnifiedWorkflowState;
  /** Workflow config */
  config: WorkflowConfig;
  /** Compact mode for narrow spaces */
  compact?: boolean;
  /** Show AI inference indicator */
  showInferenceHint?: boolean;
  /** Custom class name */
  className?: string;
}

/**
 * Workflow progress stepper
 */
export function UnifiedWorkflowProgress({
  workflow,
  config,
  compact = false,
  showInferenceHint = true,
  className,
}: UnifiedWorkflowProgressProps) {
  const { steps, currentStepId, goToStep, completionPercentage, canInferForStep } = workflow;

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
}

function StepItem({
  stepState,
  index,
  isLast,
  isCurrent,
  compact,
  showInferenceHint,
  onClick,
}: StepItemProps) {
  const { step, status, hasData, missingInputs } = stepState;
  const Icon = step.icon;
  const isCompleted = status === "completed";
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
              "border-2",
              // Status-based styles
              isCompleted && "bg-emerald-500/20 border-emerald-500",
              isCurrent && !isCompleted && "bg-white/10 border-white/40",
              !isCurrent && !isCompleted && "bg-white/5 border-white/20",
              // Hover effect
              "group-hover:scale-105"
            )}
            style={{
              borderColor: isCurrent ? step.color : undefined,
              boxShadow: isCurrent ? `0 0 20px ${step.color}40` : undefined,
            }}
          >
            {isCompleted ? (
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
              className="absolute -top-1 -right-1 w-4 h-4 rounded-full flex items-center justify-center bg-amber-500/80"
              title={`${missingInputs.length}개 입력 미완료`}
            >
              <AlertCircle className="w-3 h-3 text-white" />
            </div>
          )}

          {/* AI inference hint badge */}
          {showInferenceHint && !isCompleted && (
            <div
              className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full flex items-center justify-center bg-purple-500/80"
              title="AI 추론 가능"
            >
              <Sparkles className="w-2.5 h-2.5 text-white" />
            </div>
          )}
        </div>

        {/* Step info */}
        <div
          className={cn(
            "flex-1 sm:flex-initial text-left sm:text-center",
            compact && "hidden sm:block"
          )}
        >
          <div
            className={cn(
              "text-sm font-medium transition-colors",
              isCurrent && "text-white",
              isCompleted && "text-emerald-400",
              !isCurrent && !isCompleted && "text-white/60"
            )}
          >
            {step.label}
          </div>
          {!compact && (
            <div className="text-xs text-white/40 mt-0.5 hidden sm:block">
              {step.description}
            </div>
          )}
        </div>

        {/* Mobile: status badge */}
        <div className="sm:hidden">
          {isCompleted ? (
            <span className="text-xs text-emerald-400 px-2 py-1 bg-emerald-500/10 rounded">
              완료
            </span>
          ) : isCurrent ? (
            <span className="text-xs text-cyan-400 px-2 py-1 bg-cyan-500/10 rounded">
              진행 중
            </span>
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
export function UnifiedWorkflowProgressCompact({
  workflow,
  config,
  className,
}: {
  workflow: UnifiedWorkflowState;
  config: WorkflowConfig;
  className?: string;
}) {
  return (
    <UnifiedWorkflowProgress
      workflow={workflow}
      config={config}
      compact
      showInferenceHint={false}
      className={className}
    />
  );
}
