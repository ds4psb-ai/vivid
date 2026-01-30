"use client";

/**
 * useQuickGenerate - Quick Generate Hook
 *
 * Phase 2-2: 메가앱별 "한번에 생성" 기능을 위한 hook
 * 기존 backend /workflow/execute API를 활용합니다.
 *
 * 기능:
 * - 워크플로우 계획 및 크레딧 추정
 * - 전체 단계 순차 실행
 * - 진행 상태 추적
 * - 에러 처리 및 환불
 */

import { useState, useCallback } from "react";
import { workflowApi } from "@/lib/workflowApi";
import type {
  WorkflowPlanResponse,
  WorkflowStartResponse,
  WorkflowExecuteResponse,
  WorkflowStatusResponse,
} from "@/lib/workflowApi";
import type {
  QuickGenerateState,
  QuickGenerateStatus,
  QuickGenerateStepProgress,
  QuickGenerateResult,
  MegaAppId,
} from "../types";

// =============================================================================
// Types
// =============================================================================

export interface UseQuickGenerateOptions {
  /** Mega app ID */
  appId: MegaAppId;
  /** Callback when execution completes */
  onComplete?: (result: QuickGenerateResult) => void;
  /** Callback when error occurs */
  onError?: (error: Error) => void;
  /** Callback for progress updates */
  onProgress?: (state: QuickGenerateState) => void;
}

export interface UseQuickGenerateResult {
  /** Current state */
  state: QuickGenerateState;
  /** Plan the workflow (estimate credits) */
  plan: (inputs: Record<string, unknown>) => Promise<WorkflowPlanResponse | null>;
  /** Execute the workflow */
  execute: (inputs: Record<string, unknown>) => Promise<QuickGenerateResult | null>;
  /** Open confirmation modal */
  confirm: () => void;
  /** Close confirmation modal */
  cancelConfirm: () => void;
  /** Reset state */
  reset: () => void;
  /** Cancel running execution */
  cancel: () => Promise<void>;
  /** Whether execution is in progress */
  isExecuting: boolean;
  /** Whether confirmation modal is open */
  isConfirming: boolean;
  /** Last plan result for confirmation modal */
  planResult: WorkflowPlanResponse | null;
}

// =============================================================================
// Initial State
// =============================================================================

const INITIAL_STATE: QuickGenerateState = {
  status: "idle",
  currentStepIndex: 0,
  totalSteps: 0,
  steps: [],
  totalCreditCost: 0,
  usedCredits: 0,
};

// =============================================================================
// Hook
// =============================================================================

export function useQuickGenerate(options: UseQuickGenerateOptions): UseQuickGenerateResult {
  const { appId, onComplete, onError, onProgress } = options;

  const [state, setState] = useState<QuickGenerateState>(INITIAL_STATE);
  const [planResult, setPlanResult] = useState<WorkflowPlanResponse | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  // Update state and notify
  const updateState = useCallback(
    (updates: Partial<QuickGenerateState>) => {
      setState((prev) => {
        const next = { ...prev, ...updates };
        onProgress?.(next);
        return next;
      });
    },
    [onProgress]
  );

  // Plan the workflow
  const plan = useCallback(
    async (inputs: Record<string, unknown>): Promise<WorkflowPlanResponse | null> => {
      try {
        updateState({ status: "planning" });

        const result = await workflowApi.plan({
          appId,
          inputs,
        });

        const steps: QuickGenerateStepProgress[] = result.steps.map((step) => ({
          stepId: step.stepId,
          label: step.label,
          status: "pending",
          creditCost: step.estimatedCreditCost,
        }));

        updateState({
          status: "confirming",
          totalSteps: result.steps.length,
          steps,
          totalCreditCost: result.totalEstimatedCredits,
          sessionId: result.sessionId,
        });

        setPlanResult(result);
        setCurrentSessionId(result.sessionId);

        return result;
      } catch (error) {
        const err = error instanceof Error ? error : new Error("Plan failed");
        updateState({
          status: "error",
          error: err.message,
        });
        onError?.(err);
        return null;
      }
    },
    [appId, updateState, onError]
  );

  // Execute the workflow
  const execute = useCallback(
    async (inputs: Record<string, unknown>): Promise<QuickGenerateResult | null> => {
      try {
        // Plan if not already planned
        let sessionId = currentSessionId;
        if (!sessionId) {
          const planRes = await plan(inputs);
          if (!planRes) return null;
          sessionId = planRes.sessionId;
        }

        updateState({ status: "executing", currentStepIndex: 0 });

        // Start (reserve credits)
        const startResult = await workflowApi.start(sessionId, { reserveCredits: true });

        if (!startResult.success || startResult.status === "insufficient_credits") {
          const result: QuickGenerateResult = {
            success: false,
            sessionId,
            outputs: {},
            totalCreditsUsed: 0,
            completedSteps: [],
            error: startResult.error || "크레딧이 부족합니다",
          };
          updateState({
            status: "error",
            error: result.error,
          });
          return result;
        }

        // Execute all steps
        const executeResult = await workflowApi.executeAll(sessionId, {
          stopOnError: true,
        });

        // Build result
        const outputs: Record<string, Record<string, unknown>> = {};
        const completedSteps: string[] = [];
        let failedStep: string | undefined;

        const updatedSteps = state.steps.map((step, index) => {
          const stepResult = executeResult.steps.find((s) => s.stepId === step.stepId);
          if (stepResult) {
            if (stepResult.status === "completed") {
              completedSteps.push(step.stepId);
              if (stepResult.output) {
                outputs[step.stepId] = stepResult.output;
              }
              return { ...step, status: "completed" as const, output: stepResult.output };
            } else if (stepResult.status === "error") {
              failedStep = step.stepId;
              return { ...step, status: "error" as const, error: stepResult.error };
            }
          }
          return step;
        });

        const result: QuickGenerateResult = {
          success: executeResult.status === "completed",
          sessionId,
          outputs,
          totalCreditsUsed: executeResult.totalCreditsUsed,
          completedSteps,
          failedStep,
          error: executeResult.error,
        };

        updateState({
          status: executeResult.status === "completed" ? "completed" : "error",
          steps: updatedSteps,
          usedCredits: executeResult.totalCreditsUsed,
          currentStepIndex: state.totalSteps,
          error: executeResult.error,
        });

        onComplete?.(result);
        return result;
      } catch (error) {
        const err = error instanceof Error ? error : new Error("Execution failed");
        updateState({
          status: "error",
          error: err.message,
        });
        onError?.(err);
        return null;
      }
    },
    [currentSessionId, plan, state.steps, state.totalSteps, updateState, onComplete, onError]
  );

  // Open confirmation modal
  const confirm = useCallback(() => {
    updateState({ status: "confirming" });
  }, [updateState]);

  // Close confirmation modal
  const cancelConfirm = useCallback(() => {
    updateState({ status: "idle" });
    setPlanResult(null);
    setCurrentSessionId(null);
  }, [updateState]);

  // Reset state
  const reset = useCallback(() => {
    setState(INITIAL_STATE);
    setPlanResult(null);
    setCurrentSessionId(null);
  }, []);

  // Cancel running execution
  const cancel = useCallback(async () => {
    if (currentSessionId && state.status === "executing") {
      try {
        await workflowApi.cancel(currentSessionId);
        updateState({ status: "idle" });
      } catch {
        // Ignore cancel errors
      }
    }
    reset();
  }, [currentSessionId, state.status, updateState, reset]);

  return {
    state,
    plan,
    execute,
    confirm,
    cancelConfirm,
    reset,
    cancel,
    isExecuting: state.status === "executing" || state.status === "planning",
    isConfirming: state.status === "confirming",
    planResult,
  };
}
