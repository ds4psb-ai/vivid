"use client";

/**
 * UnifiedStepNav - Step Navigation Component
 *
 * Provides Previous/Next navigation between workflow steps.
 * Adapts to each app's configuration.
 *
 * 2026 Trends:
 * - Non-blocking navigation (warnings, not blocks)
 * - AI inference suggestions
 * - Context-aware hints
 */

import { ChevronLeft, ChevronRight, AlertCircle, Sparkles, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { UnifiedWorkflowState } from "./types";

interface UnifiedStepNavProps {
  /** Workflow state from useUnifiedWorkflow */
  workflow: UnifiedWorkflowState;
  /** Custom class name */
  className?: string;
  /** Show completion hint */
  showCompletionHint?: boolean;
}

/**
 * Step navigation with Previous/Next buttons
 */
export function UnifiedStepNav({
  workflow,
  className,
  showCompletionHint = true,
}: UnifiedStepNavProps) {
  const {
    currentStepId,
    canGoNext,
    canGoPrevious,
    nextStep,
    previousStep,
    goToNext,
    goToPrevious,
    getMissingInputsForStep,
    canInferForStep,
    getStepData,
  } = workflow;

  const currentStepData = getStepData(currentStepId);
  const isCurrentStepComplete = !!currentStepData;

  // Check if next step has missing inputs
  const nextStepMissingInputs = nextStep
    ? getMissingInputsForStep(nextStep.id)
    : [];
  const nextStepCanInfer = nextStep ? canInferForStep(nextStep.id) : false;

  return (
    <div
      className={cn(
        "flex items-center justify-between px-4 py-3 border-t border-white/10 bg-stitch-surface backdrop-blur-sm",
        className
      )}
    >
      {/* Previous button */}
      <div className="flex-1">
        {canGoPrevious && previousStep && (
          <button
            onClick={goToPrevious}
            className="flex items-center gap-2 px-4 py-2 text-sm text-white/60 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            <span className="hidden sm:inline">{previousStep.label}</span>
            <span className="sm:hidden">이전</span>
          </button>
        )}
      </div>

      {/* Center: Current step status */}
      {showCompletionHint && (
        <div className="flex items-center gap-2 text-xs">
          {isCurrentStepComplete ? (
            <span className="flex items-center gap-1 text-emerald-400">
              <Check className="w-3 h-3" />
              완료
            </span>
          ) : (
            <span className="text-white/40">진행 중</span>
          )}
        </div>
      )}

      {/* Next button */}
      <div className="flex-1 flex justify-end">
        {canGoNext && nextStep && (
          <div className="flex flex-col items-end gap-1">
            <button
              onClick={goToNext}
              className={cn(
                "flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-colors",
                isCurrentStepComplete
                  ? "bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30"
                  : "bg-white/5 text-white/60 hover:bg-white/10 hover:text-white"
              )}
            >
              <span className="hidden sm:inline">{nextStep.label}</span>
              <span className="sm:hidden">다음</span>
              <ChevronRight className="w-4 h-4" />
            </button>

            {/* Missing inputs warning for next step */}
            {nextStepMissingInputs.length > 0 && (
              <div className="flex items-center gap-1.5 text-[10px]">
                <AlertCircle className="w-2.5 h-2.5 text-amber-400" />
                <span className="text-amber-400/80">
                  {nextStepMissingInputs.length}개 입력 미완료
                </span>
                {nextStepCanInfer && (
                  <span className="flex items-center gap-0.5 text-purple-400/80">
                    <Sparkles className="w-2.5 h-2.5" />
                    AI 추론 가능
                  </span>
                )}
              </div>
            )}
          </div>
        )}

        {/* Final step indicator */}
        {!canGoNext && (
          <div className="text-xs text-white/40">마지막 단계</div>
        )}
      </div>
    </div>
  );
}

/**
 * Compact navigation for inline use
 */
export function UnifiedStepNavCompact({
  workflow,
  className,
}: {
  workflow: UnifiedWorkflowState;
  className?: string;
}) {
  const { canGoNext, canGoPrevious, goToNext, goToPrevious } = workflow;

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <button
        onClick={goToPrevious}
        disabled={!canGoPrevious}
        className={cn(
          "p-1.5 rounded-lg transition-colors",
          canGoPrevious
            ? "text-white/60 hover:text-white hover:bg-white/10"
            : "text-white/20 cursor-not-allowed"
        )}
      >
        <ChevronLeft className="w-4 h-4" />
      </button>
      <button
        onClick={goToNext}
        disabled={!canGoNext}
        className={cn(
          "p-1.5 rounded-lg transition-colors",
          canGoNext
            ? "text-white/60 hover:text-white hover:bg-white/10"
            : "text-white/20 cursor-not-allowed"
        )}
      >
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  );
}
