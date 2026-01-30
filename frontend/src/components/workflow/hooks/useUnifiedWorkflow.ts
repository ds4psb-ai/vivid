"use client";

/**
 * useUnifiedWorkflow - Unified Workflow State Management Hook
 *
 * Provides workflow state management across all Mega Apps.
 * Replaces app-specific hooks (useDNALabWorkflow, etc.) with config-driven approach.
 *
 * 2026 Pattern: "Config over Code"
 * - Behavior determined by WorkflowConfig
 * - Single hook, multiple behaviors
 */

import { useCallback, useMemo, useState, useEffect } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";
import {
  getStepMetadata,
  getStepIndex,
  getNextStep,
  getPreviousStep,
  getMissingInputs,
} from "../workflow-configs";
import type {
  WorkflowConfig,
  WorkflowStepMetadata,
  StepState,
  StepStatus,
  UnifiedWorkflowState,
  DisclosureLevel,
} from "../types";

/**
 * Get localStorage key for disclosure level
 */
function getDisclosureStorageKey(appId: string): string {
  return `vivid_disclosure_${appId}`;
}

/**
 * Read disclosure level from localStorage
 */
function readDisclosureLevel(appId: string): DisclosureLevel {
  if (typeof window === "undefined") return "intermediate";
  try {
    const stored = localStorage.getItem(getDisclosureStorageKey(appId));
    if (stored === "basic" || stored === "intermediate" || stored === "advanced") {
      return stored;
    }
  } catch {
    // localStorage may not be available
  }
  return "intermediate"; // default
}

/**
 * Write disclosure level to localStorage
 */
function writeDisclosureLevel(appId: string, level: DisclosureLevel): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(getDisclosureStorageKey(appId), level);
  } catch {
    // localStorage may not be available
  }
}

/**
 * Unified Workflow Hook
 *
 * Manages step navigation, completion tracking, and chain data integration
 * for any Mega App based on its configuration.
 *
 * @param config - Workflow configuration for the current app
 */
export function useUnifiedWorkflow(config: WorkflowConfig): UnifiedWorkflowState {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const chain = useDimensionChainOptional();

  const stepParamName = config.stepParamName || "step";
  const defaultStep = config.defaultStep || config.steps[0]?.id;

  // Phase 2-1: Progressive Disclosure state with localStorage persistence
  const [disclosureLevel, setDisclosureLevelState] = useState<DisclosureLevel>(() =>
    readDisclosureLevel(config.id)
  );

  // Sync disclosure level with localStorage on change
  const setDisclosureLevel = useCallback(
    (level: DisclosureLevel) => {
      setDisclosureLevelState(level);
      writeDisclosureLevel(config.id, level);
    },
    [config.id]
  );

  // Initialize from localStorage on mount (hydration fix)
  useEffect(() => {
    const stored = readDisclosureLevel(config.id);
    if (stored !== disclosureLevel) {
      setDisclosureLevelState(stored);
    }
  }, [config.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // Get current step from URL
  const currentStepId = useMemo((): string => {
    const stepParam = searchParams?.get(stepParamName);
    if (stepParam && config.steps.some((s) => s.id === stepParam)) {
      return stepParam;
    }
    return defaultStep;
  }, [searchParams, stepParamName, config.steps, defaultStep]);

  const currentStep = getStepMetadata(config, currentStepId) || config.steps[0];
  const currentStepIndex = getStepIndex(config, currentStepId);

  // Build chain data from dimension chain context
  // Map dimension keys to step outputs
  const chainData = useMemo((): Record<string, Record<string, unknown>> => {
    if (!chain?.chainData) return {};

    const data: Record<string, Record<string, unknown>> = {};

    // Map all chain data by key
    for (const [key, chainEntry] of Object.entries(chain.chainData)) {
      if (chainEntry?.output) {
        data[key] = chainEntry.output;
      }
    }

    // Also check step outputs mapping
    config.steps.forEach((step) => {
      step.outputs.forEach((outputKey) => {
        // Check if dimension chain has this key
        const dimensionData = chain.chainData[outputKey];
        if (dimensionData?.output) {
          data[outputKey] = dimensionData.output;
        }
        // Also try step.id as key (for backward compatibility with DNA Lab)
        const stepData = chain.chainData[step.id];
        if (stepData?.output && !data[outputKey]) {
          data[outputKey] = stepData.output;
        }
      });
    });

    return data;
  }, [chain?.chainData, config.steps]);

  // Calculate step states
  const steps = useMemo((): StepState[] => {
    return config.steps.map((step): StepState => {
      // Check if step has data (check both step.id and step.outputs[0])
      const hasData = step.outputs.some((outputKey) => !!chainData[outputKey]) ||
                     !!chainData[step.id];
      const missingInputs = getMissingInputs(step, chainData);

      let status: StepStatus = "pending";
      if (step.id === currentStepId) {
        status = "active";
      } else if (hasData) {
        status = "completed";
      } else if (missingInputs.length === 0 || step.canInfer) {
        status = "pending";
      }

      return {
        step,
        status,
        hasData,
        missingInputs,
        canInfer: step.canInfer ?? false,
      };
    });
  }, [config.steps, chainData, currentStepId]);

  // Completed steps
  const completedSteps = useMemo((): string[] => {
    return steps.filter((s) => s.status === "completed").map((s) => s.step.id);
  }, [steps]);

  // Completion percentage
  const completionPercentage = useMemo((): number => {
    return Math.round((completedSteps.length / config.steps.length) * 100);
  }, [completedSteps, config.steps.length]);

  // Navigation state
  const nextStep = getNextStep(config, currentStepId);
  const previousStep = getPreviousStep(config, currentStepId);
  const canGoNext = !!nextStep;
  const canGoPrevious = !!previousStep;

  // Navigate to step
  const goToStep = useCallback(
    (stepId: string) => {
      const params = new URLSearchParams(searchParams?.toString() || "");
      params.set(stepParamName, stepId);
      router.push(`${pathname}?${params.toString()}`);
    },
    [router, pathname, searchParams, stepParamName]
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
    (stepId: string, data: Record<string, unknown>) => {
      if (!chain) return;

      const step = getStepMetadata(config, stepId);
      if (!step) return;

      // Store in dimension chain context using step's output key
      const outputKey = step.outputs[0] || step.id;
      chain.setChainData(
        outputKey,
        data,
        `${step.label} completed`,
        []
      );
    },
    [chain, config]
  );

  // Get step data
  const getStepData = useCallback(
    (stepId: string): Record<string, unknown> | undefined => {
      const step = getStepMetadata(config, stepId);
      if (!step) return undefined;

      // Check output keys first, then step id
      for (const outputKey of step.outputs) {
        if (chainData[outputKey]) {
          return chainData[outputKey];
        }
      }
      return chainData[stepId];
    },
    [chainData, config]
  );

  // Get input data for a step (from dependency steps)
  const getInputDataForStep = useCallback(
    (stepId: string): Record<string, Record<string, unknown>> => {
      const step = getStepMetadata(config, stepId);
      if (!step) return {};

      const inputData: Record<string, Record<string, unknown>> = {};

      step.inputs.forEach((inputKey) => {
        if (chainData[inputKey]) {
          inputData[inputKey] = chainData[inputKey];
        }
      });

      return inputData;
    },
    [chainData, config]
  );

  // Check if AI can infer missing data for step
  const canInferForStep = useCallback(
    (stepId: string): boolean => {
      const step = getStepMetadata(config, stepId);
      if (!step?.canInfer) return false;

      const missingInputs = getMissingInputs(step, chainData);
      return missingInputs.length > 0;
    },
    [chainData, config]
  );

  // Get missing inputs for a step
  const getMissingInputsForStep = useCallback(
    (stepId: string): string[] => {
      const step = getStepMetadata(config, stepId);
      if (!step) return [];
      return getMissingInputs(step, chainData);
    },
    [chainData, config]
  );

  return {
    // Config
    config,

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

    // Phase 2-1: Progressive Disclosure
    disclosureLevel,
    setDisclosureLevel,
  };
}
