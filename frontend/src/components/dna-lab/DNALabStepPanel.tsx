"use client";

/**
 * DNALabStepPanel - Panel Wrapper with Chain Data Integration
 *
 * Wraps individual panel components with:
 * - Input data injection from previous steps
 * - Output data capture for chain flow
 * - Missing data indicators
 * - AI inference suggestions
 *
 * 2026 Trends:
 * - Auto-fills from chain data
 * - Shows AI inference option when data missing
 */

import { AlertCircle, Sparkles, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { useDNALabWorkflow } from "./hooks/useDNALabWorkflow";
import {
  DNA_LAB_STEPS_MAP,
  DNA_LAB_INPUT_MAP,
  type DNALabStepId,
} from "./constants";

interface DNALabStepPanelProps {
  /** Current step ID */
  stepId: DNALabStepId;
  /** Panel component */
  children: React.ReactNode;
  /** Show input data banner */
  showInputBanner?: boolean;
  /** Custom class name */
  className?: string;
}

/**
 * Panel wrapper that shows input data status and provides chain integration
 */
export function DNALabStepPanel({
  stepId,
  children,
  showInputBanner = true,
  className,
}: DNALabStepPanelProps) {
  const {
    getInputDataForStep,
    getMissingInputsForStep,
    canInferForStep,
    goToStep,
  } = useDNALabWorkflow();

  const step = DNA_LAB_STEPS_MAP[stepId];
  const inputData = getInputDataForStep(stepId);
  const missingInputs = getMissingInputsForStep(stepId);
  const canInfer = canInferForStep(stepId);
  const hasInputs = Object.keys(inputData).length > 0;
  const hasMissingInputs = missingInputs.length > 0;

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Input Data Banner */}
      {showInputBanner && (hasInputs || hasMissingInputs) && (
        <div className="px-4 py-2 border-b border-white/10 bg-white/5">
          {/* Available inputs */}
          {hasInputs && (
            <div className="flex items-center gap-2 text-xs text-white/60 mb-1">
              <span className="text-emerald-400">입력 데이터:</span>
              {Object.keys(inputData).map((inputId) => {
                const inputStep = DNA_LAB_STEPS_MAP[inputId as DNALabStepId];
                return (
                  <span
                    key={inputId}
                    className="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 rounded"
                  >
                    {inputStep?.label || inputId}
                  </span>
                );
              })}
            </div>
          )}

          {/* Missing inputs warning */}
          {hasMissingInputs && (
            <div className="flex items-center gap-2 text-xs">
              <AlertCircle className="w-3 h-3 text-amber-400" />
              <span className="text-amber-400">미완료:</span>
              {missingInputs.map((inputId) => {
                const inputStep = DNA_LAB_STEPS_MAP[inputId];
                return (
                  <button
                    key={inputId}
                    onClick={() => goToStep(inputId)}
                    className="px-2 py-0.5 bg-amber-500/10 text-amber-400 rounded hover:bg-amber-500/20 transition-colors flex items-center gap-1"
                  >
                    {inputStep?.label || inputId}
                    <ArrowRight className="w-2.5 h-2.5" />
                  </button>
                );
              })}

              {/* AI inference hint */}
              {canInfer && (
                <span className="ml-2 px-2 py-0.5 bg-purple-500/10 text-purple-400 rounded flex items-center gap-1">
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
    </div>
  );
}

/**
 * Hook to inject chain input data into panel props
 */
export function useChainInputInjection(stepId: DNALabStepId) {
  const { getInputDataForStep, chainData, getMissingInputsForStep, canInferForStep } =
    useDNALabWorkflow();

  const inputData = getInputDataForStep(stepId);
  const missingInputs = getMissingInputsForStep(stepId);
  const canInfer = canInferForStep(stepId);

  // Build injected props based on step
  // Phase 1-2: Updated for merged analysis step
  const injectedProps: Record<string, unknown> = {};

  switch (stepId) {
    case "analysis":
      // Analysis is entry point, no injection needed
      break;

    case "mirror":
      // Abyss Mirror gets Logic Vector + Aesthetic Guidelines from Analysis
      if (inputData.analysis?.logicVector) {
        injectedProps.prefillLogicVector = inputData.analysis.logicVector;
      }
      if (inputData.analysis?.aestheticGuidelines) {
        injectedProps.prefillAesthetics = inputData.analysis.aestheticGuidelines;
      }
      break;

    case "qc":
      // Quality Director gets all previous outputs
      if (inputData.analysis?.logicVector) {
        injectedProps.prefillLogicVector = inputData.analysis.logicVector;
      }
      if (inputData.analysis?.aestheticGuidelines) {
        injectedProps.prefillAesthetics = inputData.analysis.aestheticGuidelines;
      }
      if (inputData.mirror?.personaDNA) {
        injectedProps.prefillPersonaDNA = inputData.mirror.personaDNA;
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
