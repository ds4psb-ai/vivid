"use client";

/**
 * useDNALabWorkflow - DNA Lab Workflow State Management Hook
 *
 * 2026 Trends Implementation:
 * 1. Non-sequential access - any step accessible directly
 * 2. AI inference - suggests when data missing
 * 3. Parallel preview - can view all steps simultaneously
 *
 * Integrates with DimensionChainContext for data persistence.
 */

import { useCallback, useMemo } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";
import {
  DNA_LAB_STEPS,
  DNA_LAB_STEPS_MAP,
  DNA_LAB_INPUT_MAP,
  DNA_LAB_STEP_PARAM,
  DNA_LAB_DEFAULT_STEP,
  getStepIndex,
  getNextStep,
  getPreviousStep,
  getMissingInputs,
  hasRequiredInputs,
  type DNALabStepId,
  type DNALabStep,
  type StepStatus,
} from "../constants";

/**
 * Step state with completion and data info
 */
export interface StepState {
  step: DNALabStep;
  status: StepStatus;
  hasData: boolean;
  missingInputs: DNALabStepId[];
  canInfer: boolean;
}

/**
 * Workflow state and actions
 */
export interface DNALabWorkflowState {
  // Current state
  currentStep: DNALabStep;
  currentStepId: DNALabStepId;
  currentStepIndex: number;

  // All steps state
  steps: StepState[];
  completedSteps: DNALabStepId[];
  completionPercentage: number;

  // Navigation
  canGoNext: boolean;
  canGoPrevious: boolean;
  nextStep: DNALabStep | undefined;
  previousStep: DNALabStep | undefined;

  // Actions
  goToStep: (stepId: DNALabStepId) => void;
  goToNext: () => void;
  goToPrevious: () => void;
  markStepComplete: (stepId: DNALabStepId, data: Record<string, unknown>) => void;

  // Data
  getStepData: (stepId: DNALabStepId) => Record<string, unknown> | undefined;
  getInputDataForStep: (stepId: DNALabStepId) => Record<string, Record<string, unknown>>;
  chainData: Record<string, Record<string, unknown>>;

  // AI Inference
  canInferForStep: (stepId: DNALabStepId) => boolean;
  getMissingInputsForStep: (stepId: DNALabStepId) => DNALabStepId[];
}

/**
 * DNA Lab Workflow Hook
 *
 * Manages step navigation, completion tracking, and chain data integration.
 */
export function useDNALabWorkflow(): DNALabWorkflowState {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const chain = useDimensionChainOptional();

  // Get current step from URL
  const currentStepId = useMemo((): DNALabStepId => {
    const stepParam = searchParams?.get(DNA_LAB_STEP_PARAM);
    if (stepParam && DNA_LAB_STEPS_MAP[stepParam as DNALabStepId]) {
      return stepParam as DNALabStepId;
    }
    return DNA_LAB_DEFAULT_STEP;
  }, [searchParams]);

  const currentStep = DNA_LAB_STEPS_MAP[currentStepId];
  const currentStepIndex = getStepIndex(currentStepId);

  // Build chain data from dimension chain context
  // Map dimension keys to step IDs
  const chainData = useMemo((): Record<string, Record<string, unknown>> => {
    if (!chain?.chainData) return {};

    const data: Record<string, Record<string, unknown>> = {};

    // Map dimension chain data to step IDs
    DNA_LAB_STEPS.forEach((step) => {
      const dimensionData = chain.chainData[step.dimensionKey];
      if (dimensionData?.output) {
        data[step.id] = dimensionData.output;
      }
    });

    return data;
  }, [chain?.chainData]);

  // Calculate step states
  const steps = useMemo((): StepState[] => {
    return DNA_LAB_STEPS.map((step): StepState => {
      const hasData = !!chainData[step.id];
      const missingInputs = getMissingInputs(step.id, chainData);

      let status: StepStatus = "pending";
      if (step.id === currentStepId) {
        status = "active";
      } else if (hasData) {
        status = "completed";
      } else if (missingInputs.length === 0 || step.canInferInput) {
        status = "pending";
      }

      return {
        step,
        status,
        hasData,
        missingInputs,
        canInfer: step.canInferInput ?? false,
      };
    });
  }, [chainData, currentStepId]);

  // Completed steps
  const completedSteps = useMemo((): DNALabStepId[] => {
    return steps.filter((s) => s.status === "completed").map((s) => s.step.id);
  }, [steps]);

  // Completion percentage
  const completionPercentage = useMemo((): number => {
    return Math.round((completedSteps.length / DNA_LAB_STEPS.length) * 100);
  }, [completedSteps]);

  // Navigation state
  const nextStep = getNextStep(currentStepId);
  const previousStep = getPreviousStep(currentStepId);
  const canGoNext = !!nextStep;
  const canGoPrevious = !!previousStep;

  // Navigate to step
  const goToStep = useCallback(
    (stepId: DNALabStepId) => {
      const params = new URLSearchParams(searchParams?.toString() || "");
      params.set(DNA_LAB_STEP_PARAM, stepId);
      router.push(`${pathname}?${params.toString()}`);
    },
    [router, pathname, searchParams]
  );

  // Navigate to next step
  const goToNext = useCallback(() => {
    if (nextStep) {
      goToStep(nextStep.id);
    }
  }, [nextStep, goToStep]);

  // Navigate to previous step
  const goToPrevious = useCallback(() => {
    if (previousStep) {
      goToStep(previousStep.id);
    }
  }, [previousStep, goToStep]);

  // Mark step as complete with data
  const markStepComplete = useCallback(
    (stepId: DNALabStepId, data: Record<string, unknown>) => {
      if (!chain) return;

      const step = DNA_LAB_STEPS_MAP[stepId];
      if (!step) return;

      // Store in dimension chain context with dimension key mapping
      chain.setChainData(
        step.dimensionKey,
        data,
        `${step.label} completed`, // summary
        [] // evidence refs (panel should provide these)
      );
    },
    [chain]
  );

  // Get step data
  const getStepData = useCallback(
    (stepId: DNALabStepId): Record<string, unknown> | undefined => {
      return chainData[stepId];
    },
    [chainData]
  );

  // Get input data for a step (from dependency steps)
  const getInputDataForStep = useCallback(
    (stepId: DNALabStepId): Record<string, Record<string, unknown>> => {
      const inputStepIds = DNA_LAB_INPUT_MAP[stepId];
      const inputData: Record<string, Record<string, unknown>> = {};

      inputStepIds.forEach((inputId) => {
        if (chainData[inputId]) {
          inputData[inputId] = chainData[inputId];
        }
      });

      return inputData;
    },
    [chainData]
  );

  // Check if AI can infer missing data for step
  const canInferForStep = useCallback(
    (stepId: DNALabStepId): boolean => {
      const step = DNA_LAB_STEPS_MAP[stepId];
      if (!step?.canInferInput) return false;

      // Can infer if step supports it and has some context
      const missingInputs = getMissingInputs(stepId, chainData);
      return missingInputs.length > 0;
    },
    [chainData]
  );

  // Get missing inputs for a step
  const getMissingInputsForStep = useCallback(
    (stepId: DNALabStepId): DNALabStepId[] => {
      return getMissingInputs(stepId, chainData);
    },
    [chainData]
  );

  return {
    // Current state
    currentStep,
    currentStepId,
    currentStepIndex,

    // All steps state
    steps,
    completedSteps,
    completionPercentage,

    // Navigation
    canGoNext,
    canGoPrevious,
    nextStep,
    previousStep,

    // Actions
    goToStep,
    goToNext,
    goToPrevious,
    markStepComplete,

    // Data
    getStepData,
    getInputDataForStep,
    chainData,

    // AI Inference
    canInferForStep,
    getMissingInputsForStep,
  };
}
