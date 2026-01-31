"use client";

/**
 * DNALabStepNav - Step Navigation Component
 *
 * Provides Previous/Next navigation between workflow steps.
 * Shows context about current and next steps.
 *
 * 2026 Trends:
 * - Non-blocking navigation (warnings, not blocks)
 * - AI inference suggestions
 * - Unified pipeline execution
 */

import { ChevronLeft, ChevronRight, AlertCircle, Sparkles, Check, Play, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useDNALabWorkflow } from "./hooks/useDNALabWorkflow";
import { useDNALabPipeline, type PipelineOptions } from "./hooks/useDNALabPipeline";
import { DNA_LAB_STEPS_MAP, type DNALabStepId } from "./constants";

interface DNALabStepNavProps {
  /** Custom class name */
  className?: string;
  /** Show completion hint */
  showCompletionHint?: boolean;
}

/**
 * Step navigation with Previous/Next buttons
 */
export function DNALabStepNav({ className, showCompletionHint = true }: DNALabStepNavProps) {
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
  } = useDNALabWorkflow();

  const currentStepData = getStepData(currentStepId);
  const isCurrentStepComplete = !!currentStepData;

  // Check if next step has missing inputs
  const nextStepMissingInputs = nextStep ? getMissingInputsForStep(nextStep.id) : [];
  const nextStepCanInfer = nextStep ? canInferForStep(nextStep.id) : false;

  return (
    <div
      className={cn(
        "flex items-center justify-between px-4 py-3 border-t border-white/10 bg-black/50 backdrop-blur-sm",
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
export function DNALabStepNavCompact({ className }: { className?: string }) {
  const { canGoNext, canGoPrevious, goToNext, goToPrevious } = useDNALabWorkflow();

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

/**
 * Run Pipeline Button Props
 */
interface DNALabRunPipelineButtonProps {
  /** Custom class name */
  className?: string;
  /** Optional pipeline options override */
  options?: Partial<PipelineOptions>;
  /** Callback when pipeline completes */
  onComplete?: () => void;
  /** Callback when pipeline fails */
  onError?: (error: string) => void;
}

/**
 * Run Pipeline Button - Executes unified DNA Lab pipeline
 *
 * Triggers execution of VPE → AD → Mirror → QC pipeline
 * with automatic chain data integration.
 */
export function DNALabRunPipelineButton({
  className,
  options,
  onComplete,
  onError,
}: DNALabRunPipelineButtonProps) {
  const { isRunning, progress, error, runPipeline, creditsUsed, processingTimeMs } =
    useDNALabPipeline();
  const workflow = useDNALabWorkflow();

  const handleRunPipeline = async () => {
    try {
      // Extract existing chain data for pipeline input
      // Phase 1-2: "analysis" is unified step containing vpe + ad data
      const analysisData = workflow.chainData.analysis;

      const pipelineOptions: PipelineOptions = {
        steps: ["analysis", "mirror", "qc"],
        video_uri: (analysisData as Record<string, unknown>)?.videoUrl as string | undefined,
        concept: (analysisData as Record<string, unknown>)?.concept as string | undefined,
        auteur_key: (analysisData as Record<string, unknown>)?.auteurKey as string | undefined,
        ...options,
      };

      await runPipeline(pipelineOptions);
      onComplete?.();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "파이프라인 실행 실패";
      onError?.(errorMessage);
    }
  };

  return (
    <div className={cn("flex flex-col items-end gap-1", className)}>
      <button
        onClick={handleRunPipeline}
        disabled={isRunning}
        className={cn(
          "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all",
          isRunning
            ? "bg-emerald-500/20 text-emerald-400/60 cursor-wait"
            : "bg-emerald-500/30 text-emerald-400 hover:bg-emerald-500/40 hover:scale-[1.02]"
        )}
      >
        {isRunning ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>실행 중... {progress}%</span>
          </>
        ) : (
          <>
            <Play className="w-4 h-4" />
            <span>전체 파이프라인 실행</span>
          </>
        )}
      </button>

      {/* Error display */}
      {error && !isRunning && (
        <div className="flex items-center gap-1.5 text-[10px] text-red-400">
          <AlertCircle className="w-2.5 h-2.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Success info */}
      {!isRunning && creditsUsed > 0 && !error && (
        <div className="flex items-center gap-2 text-[10px] text-white/40">
          <span>{creditsUsed} 크레딧 사용</span>
          <span>•</span>
          <span>{(processingTimeMs / 1000).toFixed(1)}초</span>
        </div>
      )}
    </div>
  );
}
