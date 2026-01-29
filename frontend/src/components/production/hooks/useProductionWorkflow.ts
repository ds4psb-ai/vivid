"use client";

/**
 * useProductionWorkflow - Production Workflow State Management Hook
 *
 * Provides Production-specific workflow state management.
 * Wraps useUnifiedWorkflow with Production-specific logic.
 *
 * 2026 Patterns:
 * - Cross-app data flow (Story Engine → Production)
 * - Independent step access (any step accessible)
 * - Optional steps (all can be skipped)
 * - Completion actions (gallery/share)
 */

import { useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useUnifiedWorkflow } from "@/components/workflow/hooks/useUnifiedWorkflow";
import { getWorkflowConfig, CHAIN_DATA_SOURCE_MAP } from "@/components/workflow/workflow-configs";
import {
  PRODUCTION_STEPS_MAP,
  PRODUCTION_INPUT_MAP,
  getMissingInputs,
  getInputLabel,
  getOtherProductionTools,
  type ProductionStepId,
  type ProductionStep,
} from "../constants";
import type { StepState, StepStatus, UnifiedWorkflowState } from "@/components/workflow/types";

/**
 * Step state with completion and data info (Production specific)
 */
export interface ProductionStepState {
  step: ProductionStep;
  status: StepStatus;
  hasData: boolean;
  missingInputs: string[];
  /** Production steps don't use AI inference */
  canInfer: false;
  /** External inputs from Story Engine / DNA Lab */
  externalInputs: string[];
  /** Whether this step is optional */
  optional: boolean;
}

/**
 * Completed output entry
 */
export interface CompletedOutput {
  step: ProductionStep;
  data: Record<string, unknown>;
}

/**
 * Extended workflow state for Production
 */
export interface ProductionWorkflowState extends Omit<UnifiedWorkflowState, 'steps'> {
  // Production specific
  steps: ProductionStepState[];

  // Navigation
  goToStep: (stepId: ProductionStepId | string) => void;

  // Completion outputs
  completedOutputs: CompletedOutput[];
  hasAnyOutput: boolean;

  // Actions
  goToGallery: () => void;
  goToStoryEngine: (stepId?: string) => void;
  goToDNALab: (stepId?: string) => void;

  // Input data helpers
  getExternalInputsForStep: (stepId: ProductionStepId) => string[];
  getInputLabelForKey: (key: string) => string;

  // Other tools navigation
  getOtherTools: (currentStepId: ProductionStepId) => ProductionStep[];
}

/**
 * Production Workflow Hook
 *
 * Extends unified workflow with Production-specific functionality:
 * - Completed outputs tracking (for gallery/share)
 * - Independent step access
 * - Cross-app navigation (Story Engine, DNA Lab)
 */
export function useProductionWorkflow(): ProductionWorkflowState {
  const router = useRouter();
  const config = getWorkflowConfig("production");
  const unifiedWorkflow = useUnifiedWorkflow(config);

  const { chainData, goToStep: baseGoToStep } = unifiedWorkflow;

  // Calculate Production specific step states
  const steps = useMemo((): ProductionStepState[] => {
    return unifiedWorkflow.steps.map((stepState): ProductionStepState => {
      const stepId = stepState.step.id as ProductionStepId;
      const productionStep = PRODUCTION_STEPS_MAP[stepId];
      const inputKeys = PRODUCTION_INPUT_MAP[stepId] || [];

      // All inputs are external (from Story Engine or DNA Lab)
      const externalInputs = inputKeys.filter((key) =>
        CHAIN_DATA_SOURCE_MAP[key]?.app === "story-engine" ||
        CHAIN_DATA_SOURCE_MAP[key]?.app === "dna-lab"
      );

      return {
        step: productionStep || {
          id: stepId,
          label: stepState.step.label,
          labelEn: stepState.step.labelEn,
          icon: stepState.step.icon,
          description: stepState.step.description,
          outputKey: stepState.step.outputs[0] || stepId,
          dimensionKey: stepId,
          optional: true,
          mediaType: "video" as const,
        },
        status: stepState.status,
        hasData: stepState.hasData,
        missingInputs: stepState.missingInputs,
        canInfer: false, // Production steps don't use AI inference
        externalInputs,
        optional: true, // All Production steps are optional
      };
    });
  }, [unifiedWorkflow.steps]);

  // Track completed outputs (for gallery/share)
  const completedOutputs = useMemo((): CompletedOutput[] => {
    return steps
      .filter((stepState) => stepState.hasData)
      .map((stepState) => ({
        step: stepState.step,
        data: chainData[stepState.step.outputKey] || {},
      }));
  }, [steps, chainData]);

  // Check if any output exists
  const hasAnyOutput = completedOutputs.length > 0;

  // Navigate to Gallery/IP page
  const goToGallery = useCallback(() => {
    router.push("/ip");
  }, [router]);

  // Navigate to Story Engine
  const goToStoryEngine = useCallback((stepId?: string) => {
    const step = stepId || "story";
    router.push(`/story-engine?step=${step}`);
  }, [router]);

  // Navigate to DNA Lab
  const goToDNALab = useCallback((stepId?: string) => {
    const step = stepId || "vpe";
    router.push(`/dna-lab?step=${step}`);
  }, [router]);

  // Get external inputs for a step
  const getExternalInputsForStep = useCallback(
    (stepId: ProductionStepId): string[] => {
      const inputKeys = PRODUCTION_INPUT_MAP[stepId] || [];
      return inputKeys.filter((key) =>
        CHAIN_DATA_SOURCE_MAP[key]?.app === "story-engine" ||
        CHAIN_DATA_SOURCE_MAP[key]?.app === "dna-lab"
      );
    },
    []
  );

  // Get display label for input key
  const getInputLabelForKey = useCallback(
    (key: string): string => {
      return getInputLabel(key);
    },
    []
  );

  // Get other production tools (for "try another tool" feature)
  const getOtherTools = useCallback(
    (currentStepId: ProductionStepId): ProductionStep[] => {
      return getOtherProductionTools(currentStepId);
    },
    []
  );

  // Type-safe goToStep
  const goToStep = useCallback(
    (stepId: ProductionStepId | string) => {
      baseGoToStep(stepId);
    },
    [baseGoToStep]
  );

  return {
    ...unifiedWorkflow,
    steps,
    goToStep,
    completedOutputs,
    hasAnyOutput,
    goToGallery,
    goToStoryEngine,
    goToDNALab,
    getExternalInputsForStep,
    getInputLabelForKey,
    getOtherTools,
  };
}
