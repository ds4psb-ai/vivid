/**
 * Unified Workflow State - Merge workflow-state and chainData
 *
 * Provides a unified view of workflow execution state that combines:
 * - workflow-state: Step-based IP workflow (steps, currentStep)
 * - chainData: Dimension execution outputs (from DimensionChainContext)
 *
 * P7+ Chain UX Enhancement
 */

import type { ChainData } from "@/contexts/DimensionChainContext";

export interface WorkflowStep {
  id: string;
  name: string;
  description?: string;
  dimension?: string;
  completed: boolean;
  skipped?: boolean;
}

export interface UnifiedWorkflowState {
  // From workflow-state
  ipSlug: string;
  currentStep: number;
  steps: WorkflowStep[];

  // From chainData
  chainData: Record<string, ChainData>;
  accumulatedEvidenceRefs: string[];

  // Unified mapping
  stepToChainMap: Record<number, string>;

  // Server persistence
  serverSessionId?: string;
  version?: number;
}

/**
 * Merge workflow steps with chain data into unified state
 */
export function mergeWorkflowWithChain(
  ipSlug: string,
  steps: WorkflowStep[],
  currentStep: number,
  chainData: Record<string, ChainData>,
  accumulatedEvidenceRefs: string[],
  serverSessionId?: string,
  version?: number
): UnifiedWorkflowState {
  // Build step-to-chain mapping
  const stepToChainMap: Record<number, string> = {};

  steps.forEach((step, index) => {
    if (step.dimension) {
      stepToChainMap[index] = step.dimension;
    }
  });

  // Mark steps as completed based on chain data
  const enrichedSteps = steps.map((step, index) => {
    if (step.dimension && chainData[step.dimension]) {
      return { ...step, completed: true };
    }
    return step;
  });

  return {
    ipSlug,
    currentStep,
    steps: enrichedSteps,
    chainData,
    accumulatedEvidenceRefs,
    stepToChainMap,
    serverSessionId,
    version,
  };
}

/**
 * Get chain data for a specific workflow step
 */
export function getChainDataForStep(
  state: UnifiedWorkflowState,
  stepIndex: number
): ChainData | null {
  const dimensionKey = state.stepToChainMap[stepIndex];
  if (!dimensionKey) return null;
  return state.chainData[dimensionKey] || null;
}

/**
 * Check if a step has completed chain data
 */
export function isStepCompleted(
  state: UnifiedWorkflowState,
  stepIndex: number
): boolean {
  const chainData = getChainDataForStep(state, stepIndex);
  return !!chainData && Object.keys(chainData.output).length > 0;
}

/**
 * Get the next incomplete step index
 */
export function getNextIncompleteStep(state: UnifiedWorkflowState): number {
  for (let i = 0; i < state.steps.length; i++) {
    if (!isStepCompleted(state, i) && !state.steps[i].skipped) {
      return i;
    }
  }
  return state.steps.length; // All complete
}

/**
 * Calculate workflow progress percentage
 */
export function getWorkflowProgress(state: UnifiedWorkflowState): number {
  if (state.steps.length === 0) return 0;

  const completedCount = state.steps.filter(
    (_, index) => isStepCompleted(state, index)
  ).length;

  return Math.round((completedCount / state.steps.length) * 100);
}

/**
 * Get dimensions that have chain data
 */
export function getCompletedDimensions(
  state: UnifiedWorkflowState
): string[] {
  return Object.keys(state.chainData).filter(
    (key) => state.chainData[key] && Object.keys(state.chainData[key].output).length > 0
  );
}
