"use client";

/**
 * useWorkflowController - Flow 페이지 워크플로우 상태 관리 hook
 *
 * XState 기반 워크플로우 머신과 핸들러들을 캡슐화
 */

import { useCallback } from "react";
import { useMachine } from "@xstate/react";
import { workflowMachine, type WorkflowPhase } from "@/machines/workflowMachine";
import { FLOW_START_OPTIONS } from "@/lib/dimension-data";

// Phase -> Start Event 매핑 (SSoT)
const PHASE_TO_START_EVENT = {
  "4D": "START_4D",
  "Story": "START_STORY",
  "1D": "START_1D",
} as const;

type StartEventType = (typeof PHASE_TO_START_EVENT)[keyof typeof PHASE_TO_START_EVENT];

export function useWorkflowController() {
  // XState workflow machine
  const [workflowState, sendWorkflow] = useMachine(workflowMachine);

  // Current phase from context
  const currentPhase = workflowState.context.currentPhase;
  const chainData = workflowState.context.chainData;

  // Start workflow from option
  const handleStartWorkflow = useCallback(
    (startOption: (typeof FLOW_START_OPTIONS)[number]) => {
      const event = PHASE_TO_START_EVENT[startOption.phase];
      if (event) {
        sendWorkflow({ type: event });
      }
    },
    [sendWorkflow]
  );

  // Start workflow from phase directly
  const handlePhaseClick = useCallback(
    (phase: WorkflowPhase) => {
      if (workflowState.matches("idle")) {
        const event = PHASE_TO_START_EVENT[phase as keyof typeof PHASE_TO_START_EVENT];
        if (event) {
          sendWorkflow({ type: event });
        }
      }
    },
    [workflowState, sendWorkflow]
  );

  // Workflow control (reset, etc.)
  const handleWorkflowControl = useCallback(
    (action: "play" | "pause" | "reset") => {
      if (action === "reset") {
        sendWorkflow({ type: "RESET" });
      }
    },
    [sendWorkflow]
  );

  // Get simplified workflow state for UI
  const getWorkflowStateForSidebar = useCallback((): "idle" | "running" | "completed" | "error" => {
    if (workflowState.matches("idle")) return "idle";
    if (workflowState.matches("completed")) return "completed";
    if (workflowState.matches("error")) return "error";
    return "running";
  }, [workflowState]);

  // Start from phase (for sidebar)
  const startFromPhase = useCallback(
    (phase: WorkflowPhase) => {
      const option = FLOW_START_OPTIONS.find((o) => o.phase === phase);
      if (option) handleStartWorkflow(option);
    },
    [handleStartWorkflow]
  );

  return {
    // State
    workflowState,
    currentPhase,
    chainData,

    // Actions
    sendWorkflow,
    handleStartWorkflow,
    handlePhaseClick,
    handleWorkflowControl,
    startFromPhase,

    // Derived
    getWorkflowStateForSidebar,
    isIdle: workflowState.matches("idle"),
    isRunning: !workflowState.matches("idle") && !workflowState.matches("completed") && !workflowState.matches("error"),
    isCompleted: workflowState.matches("completed"),
  };
}

export type WorkflowController = ReturnType<typeof useWorkflowController>;
