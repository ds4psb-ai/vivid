"use client";

/**
 * useStoryEngineWorkflow - Story Engine Workflow State Management Hook
 *
 * Provides Story Engine-specific workflow state management.
 * Wraps useUnifiedWorkflow with Story Engine-specific logic.
 *
 * 2026 Patterns:
 * - Cross-app data flow (DNA Lab → Story Engine → Production)
 * - Non-sequential access
 * - AI inference suggestions
 */

import { useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useUnifiedWorkflow } from "@/components/workflow/hooks/useUnifiedWorkflow";
import { getWorkflowConfig, CHAIN_DATA_SOURCE_MAP } from "@/components/workflow/workflow-configs";
import {
  STORY_ENGINE_STEPS_MAP,
  STORY_ENGINE_INPUT_MAP,
  getMissingInputs,
  isFinalStep,
  getInputLabel,
  type StoryEngineStepId,
  type StoryEngineStep,
} from "../constants";
import type { StepState, StepStatus, UnifiedWorkflowState } from "@/components/workflow/types";

/**
 * Step state with completion and data info (Story Engine specific)
 */
export interface StoryEngineStepState {
  step: StoryEngineStep;
  status: StepStatus;
  hasData: boolean;
  missingInputs: string[];
  canInfer: boolean;
  /** External inputs from DNA Lab */
  externalInputs: string[];
  /** Internal inputs from previous Story Engine steps */
  internalInputs: string[];
}

/**
 * Extended workflow state for Story Engine
 */
export interface StoryEngineWorkflowState extends Omit<UnifiedWorkflowState, 'steps'> {
  // Story Engine specific
  steps: StoryEngineStepState[];

  // Navigation
  goToStep: (stepId: StoryEngineStepId | string) => void;

  // Production bridge
  canProceedToProduction: boolean;
  goToProduction: () => void;

  // Input data helpers
  getExternalInputsForStep: (stepId: StoryEngineStepId) => string[];
  getInternalInputsForStep: (stepId: StoryEngineStepId) => string[];
  getInputLabelForKey: (key: string) => string;

  // DNA Lab navigation
  goToDNALab: (stepId?: string) => void;
}

/**
 * Story Engine Workflow Hook
 *
 * Extends unified workflow with Story Engine-specific functionality:
 * - Production bridge navigation
 * - External (DNA Lab) vs internal input categorization
 * - Cross-app data flow management
 */
export function useStoryEngineWorkflow(): StoryEngineWorkflowState {
  const router = useRouter();
  const config = getWorkflowConfig("story-engine");
  const unifiedWorkflow = useUnifiedWorkflow(config);

  const { chainData, goToStep: baseGoToStep } = unifiedWorkflow;

  // Calculate Story Engine specific step states
  const steps = useMemo((): StoryEngineStepState[] => {
    return unifiedWorkflow.steps.map((stepState): StoryEngineStepState => {
      const stepId = stepState.step.id as StoryEngineStepId;
      const storyEngineStep = STORY_ENGINE_STEPS_MAP[stepId];
      const inputKeys = STORY_ENGINE_INPUT_MAP[stepId] || [];

      // Categorize inputs as external (DNA Lab) or internal (Story Engine)
      const externalInputs = inputKeys.filter((key) =>
        CHAIN_DATA_SOURCE_MAP[key]?.app === "dna-lab"
      );
      const internalInputs = inputKeys.filter((key) =>
        CHAIN_DATA_SOURCE_MAP[key]?.app === "story-engine"
      );

      return {
        step: storyEngineStep || {
          id: stepId,
          label: stepState.step.label,
          labelEn: stepState.step.labelEn,
          icon: stepState.step.icon,
          description: stepState.step.description,
          outputKey: stepState.step.outputs[0] || stepId,
          dimensionKey: stepId,
          canInferInput: stepState.step.canInfer,
        },
        status: stepState.status,
        hasData: stepState.hasData,
        missingInputs: stepState.missingInputs,
        canInfer: stepState.canInfer,
        externalInputs,
        internalInputs,
      };
    });
  }, [unifiedWorkflow.steps]);

  // Check if can proceed to Production (prompt step completed with system-prompt)
  // Phase 1-3: prompt step now outputs both prompt and system-prompt
  const canProceedToProduction = useMemo((): boolean => {
    // Check either the merged prompt output or legacy system-prompt key
    return !!chainData["system-prompt"] || !!chainData["prompt"]?.systemPrompt;
  }, [chainData]);

  // Navigate to Production with system-prompt data
  const goToProduction = useCallback(() => {
    router.push("/production?step=veo");
  }, [router]);

  // Navigate to DNA Lab
  const goToDNALab = useCallback((stepId?: string) => {
    const step = stepId || "vpe";
    router.push(`/dna-lab?step=${step}`);
  }, [router]);

  // Get external inputs for a step (from DNA Lab)
  const getExternalInputsForStep = useCallback(
    (stepId: StoryEngineStepId): string[] => {
      const inputKeys = STORY_ENGINE_INPUT_MAP[stepId] || [];
      return inputKeys.filter((key) =>
        CHAIN_DATA_SOURCE_MAP[key]?.app === "dna-lab"
      );
    },
    []
  );

  // Get internal inputs for a step (from Story Engine)
  const getInternalInputsForStep = useCallback(
    (stepId: StoryEngineStepId): string[] => {
      const inputKeys = STORY_ENGINE_INPUT_MAP[stepId] || [];
      return inputKeys.filter((key) =>
        CHAIN_DATA_SOURCE_MAP[key]?.app === "story-engine"
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

  // Type-safe goToStep
  const goToStep = useCallback(
    (stepId: StoryEngineStepId | string) => {
      baseGoToStep(stepId);
    },
    [baseGoToStep]
  );

  return {
    ...unifiedWorkflow,
    steps,
    goToStep,
    canProceedToProduction,
    goToProduction,
    getExternalInputsForStep,
    getInternalInputsForStep,
    getInputLabelForKey,
    goToDNALab,
  };
}

/**
 * Check if current step is the final step
 */
export function useIsFinalStep(stepId: StoryEngineStepId): boolean {
  return isFinalStep(stepId);
}
