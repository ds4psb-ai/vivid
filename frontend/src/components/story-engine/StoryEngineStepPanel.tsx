"use client";

/**
 * StoryEngineStepPanel - Panel Wrapper with Chain Data Integration
 *
 * Wraps individual panel components with:
 * - Input data injection from previous steps (DNA Lab and Story Engine)
 * - Output data capture for chain flow
 * - Missing data indicators
 * - Production bridge (for final step)
 *
 * 2026 Patterns:
 * - Cross-app data flow visualization
 * - Guide, Don't Block (show missing data but allow action)
 * - Progressive disclosure
 */

import { AlertCircle, Sparkles, ArrowRight, ExternalLink, Rocket } from "lucide-react";
import { cn } from "@/lib/utils";
import { useStoryEngineWorkflow } from "./hooks/useStoryEngineWorkflow";
import {
  STORY_ENGINE_STEPS_MAP,
  STORY_ENGINE_INPUT_MAP,
  isFinalStep,
  getInputLabel,
  type StoryEngineStepId,
} from "./constants";
import { CHAIN_DATA_SOURCE_MAP } from "@/components/workflow/workflow-configs";

interface StoryEngineStepPanelProps {
  /** Current step ID */
  stepId: StoryEngineStepId;
  /** Panel component */
  children: React.ReactNode;
  /** Show input data banner */
  showInputBanner?: boolean;
  /** Show Production bridge button (auto-enabled for system-prompt) */
  showProductionBridge?: boolean;
  /** Custom class name */
  className?: string;
}

/**
 * Panel wrapper that shows input data status and provides chain integration
 */
export function StoryEngineStepPanel({
  stepId,
  children,
  showInputBanner = true,
  showProductionBridge,
  className,
}: StoryEngineStepPanelProps) {
  const {
    getInputDataForStep,
    getMissingInputsForStep,
    canInferForStep,
    goToStep,
    goToDNALab,
    goToProduction,
    canProceedToProduction,
    chainData,
  } = useStoryEngineWorkflow();

  const step = STORY_ENGINE_STEPS_MAP[stepId];
  const inputData = getInputDataForStep(stepId);
  const missingInputs = getMissingInputsForStep(stepId);
  const canInfer = canInferForStep(stepId);
  const hasInputs = Object.keys(inputData).length > 0;
  const hasMissingInputs = missingInputs.length > 0;

  // Auto-enable Production bridge for final step
  const shouldShowProductionBridge = showProductionBridge ?? isFinalStep(stepId);
  const hasSystemPromptResult = !!chainData["system-prompt"];

  // Categorize inputs
  const externalMissing = missingInputs.filter(
    (key) => CHAIN_DATA_SOURCE_MAP[key]?.app === "dna-lab"
  );
  const internalMissing = missingInputs.filter(
    (key) => CHAIN_DATA_SOURCE_MAP[key]?.app === "story-engine"
  );

  // Navigation handler
  const handleGoToSource = (key: string) => {
    const source = CHAIN_DATA_SOURCE_MAP[key];
    if (source?.app === "dna-lab") {
      goToDNALab(source.step);
    } else if (source?.app === "story-engine") {
      goToStep(source.step as StoryEngineStepId);
    }
  };

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Input Data Banner */}
      {showInputBanner && (hasInputs || hasMissingInputs) && (
        <div className="px-4 py-2 border-b border-white/10 bg-white/5">
          {/* Available inputs */}
          {hasInputs && (
            <div className="flex items-center flex-wrap gap-2 text-xs text-white/60 mb-1">
              <span className="text-[var(--stitch-primary)]">입력 데이터:</span>
              {Object.keys(inputData).map((inputKey) => {
                const source = CHAIN_DATA_SOURCE_MAP[inputKey];
                const isExternal = source?.app === "dna-lab";

                return (
                  <span
                    key={inputKey}
                    className={cn(
                      "px-2 py-0.5 rounded flex items-center gap-1",
                      isExternal
                        ? "bg-cyan-500/10 text-cyan-400"
                        : "bg-[var(--stitch-primary)]/10 text-[var(--stitch-primary)]"
                    )}
                  >
                    {getInputLabel(inputKey)}
                    {isExternal && (
                      <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                    )}
                  </span>
                );
              })}
            </div>
          )}

          {/* Missing inputs warning */}
          {hasMissingInputs && (
            <div className="flex items-center flex-wrap gap-2 text-xs">
              <AlertCircle className="w-3 h-3 text-amber-400" />
              <span className="text-amber-400">미완료:</span>

              {/* External missing (DNA Lab) */}
              {externalMissing.map((inputKey) => (
                <button
                  key={inputKey}
                  onClick={() => handleGoToSource(inputKey)}
                  className="px-2 py-0.5 bg-cyan-500/10 text-cyan-400 rounded hover:bg-cyan-500/20 transition-colors flex items-center gap-1"
                >
                  {getInputLabel(inputKey)}
                  <ExternalLink className="w-2.5 h-2.5" />
                </button>
              ))}

              {/* Internal missing (Story Engine) */}
              {internalMissing.map((inputKey) => (
                <button
                  key={inputKey}
                  onClick={() => handleGoToSource(inputKey)}
                  className="px-2 py-0.5 bg-amber-500/10 text-amber-400 rounded hover:bg-amber-500/20 transition-colors flex items-center gap-1"
                >
                  {getInputLabel(inputKey)}
                  <ArrowRight className="w-2.5 h-2.5" />
                </button>
              ))}

              {/* AI inference hint */}
              {canInfer && (
                <span className="ml-2 px-2 py-0.5 bg-[var(--stitch-primary)]/10 text-[var(--stitch-primary)] rounded flex items-center gap-1">
                  <Sparkles className="w-3 h-3" />
                  AI 추론 가능
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {/* Panel Content */}
      <div className="flex-1 overflow-auto">{children}</div>

      {/* Production Bridge (for final step when complete) */}
      {shouldShowProductionBridge && hasSystemPromptResult && (
        <div className="px-4 py-3 border-t border-white/10 bg-gradient-to-r from-[var(--stitch-primary)]/10 via-transparent to-[var(--stitch-primary-accent)]/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-[var(--stitch-primary)]/20">
                <Rocket className="w-5 h-5 text-[var(--stitch-primary)]" />
              </div>
              <div>
                <p className="text-sm font-medium text-white">시스템 프롬프트 완료!</p>
                <p className="text-xs text-white/60">
                  Production에서 VEO 또는 Kling으로 영상을 생성하세요.
                </p>
              </div>
            </div>
            <button
              onClick={goToProduction}
              className="flex items-center gap-2 px-4 py-2 bg-[var(--stitch-primary)]/20 text-[var(--stitch-primary)] rounded-lg hover:bg-[var(--stitch-primary)]/30 transition-colors font-medium text-sm"
            >
              <span>Production으로 이동</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Hook to inject chain input data into panel props
 */
export function useChainInputInjection(stepId: StoryEngineStepId) {
  const {
    getInputDataForStep,
    getMissingInputsForStep,
    canInferForStep,
    chainData,
  } = useStoryEngineWorkflow();

  const inputData = getInputDataForStep(stepId);
  const missingInputs = getMissingInputsForStep(stepId);
  const canInfer = canInferForStep(stepId);

  // Build injected props based on step
  const injectedProps: Record<string, unknown> = {};

  switch (stepId) {
    case "story":
      // Story Architect gets VPE Logic Vector + AD Aesthetic Guidelines from DNA Lab
      if (inputData.vpe) {
        injectedProps.prefillLogicVector = inputData.vpe;
      }
      if (inputData.ad) {
        injectedProps.prefillAesthetics = inputData.ad;
      }
      break;

    case "prompt":
      // Phase 1-3: Unified Prompt (merged with System Prompt)
      // Gets everything from DNA Lab + Story
      if (inputData.vpe) {
        injectedProps.prefillLogicVector = inputData.vpe;
      }
      if (inputData.ad) {
        injectedProps.prefillAesthetics = inputData.ad;
      }
      if (inputData.story) {
        injectedProps.prefillStory = inputData.story;
      }
      break;
  }

  return {
    inputData,
    missingInputs,
    canInfer,
    injectedProps,
    hasAllInputs: missingInputs.length === 0,
  };
}
