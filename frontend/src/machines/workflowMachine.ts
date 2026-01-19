/**
 * XState Workflow Machine
 *
 * 거장 RAG + 페르소나 → 차원 조합 → 세계관 컨텐츠 생성
 *
 * States:
 * - idle: 초기 상태, 시작점 선택 대기
 * - selectStart: 시작 옵션 선택 (4D, Story, 1D)
 * - phase1_4D: 4D (Reference Decoder) 실행
 * - phase1_Story: Story (Story Architect) 실행
 * - phase1_AD: AD (Aesthetic Director) 실행
 * - phase2_1D: 1D (Prompt Alchemy) 실행
 * - phase2_2D: 2D (Storyboard Sketch) 실행
 * - phase2_Sound: Sound (Sound Crafter) 실행
 * - phase3_3D: 3D (Visual Realizer) 실행
 * - phase3_VEO: VEO (Video Maker) 실행
 * - phase3_QC: QC (Quality Director) 실행
 * - completed: 워크플로우 완료
 * - error: 에러 발생
 */

import { setup, assign, fromPromise } from "xstate";

// =============================================================================
// TYPES
// =============================================================================

export type WorkflowPhase =
  | "4D"
  | "Story"
  | "AD"
  | "1D"
  | "2D"
  | "Sound"
  | "3D"
  | "VEO"
  | "QC";

export interface ChainDataEntry {
  phase: WorkflowPhase;
  output: Record<string, unknown>;
  timestamp: number;
}

export interface WorkflowContext {
  /** 거장 키 (bong, kubrick 등) */
  auteurKey: string | null;
  /** AI 분석 페르소나 (별도 컨텍스트로 주입) */
  personaData: Record<string, unknown> | null;
  /** 각 단계 출력 */
  chainData: Record<WorkflowPhase, ChainDataEntry | null>;
  /** 현재 실행 중인 단계 */
  currentPhase: WorkflowPhase | null;
  /** 에러 메시지 */
  errorMessage: string | null;
  /** 세션 ID */
  sessionId: string | null;
}

export type WorkflowEvent =
  | { type: "START_4D" }
  | { type: "START_STORY" }
  | { type: "START_1D" }
  | { type: "NEXT" }
  | { type: "SKIP" }
  | { type: "BACK" }
  | { type: "COMPLETE_PHASE"; output: Record<string, unknown> }
  | { type: "SET_AUTEUR"; auteurKey: string }
  | { type: "SET_PERSONA"; personaData: Record<string, unknown> }
  | { type: "ERROR"; message: string }
  | { type: "RESET" };

// =============================================================================
// INITIAL CONTEXT
// =============================================================================

const initialContext: WorkflowContext = {
  auteurKey: null,
  personaData: null,
  chainData: {
    "4D": null,
    Story: null,
    AD: null,
    "1D": null,
    "2D": null,
    Sound: null,
    "3D": null,
    VEO: null,
    QC: null,
  },
  currentPhase: null,
  errorMessage: null,
  sessionId: null,
};

// =============================================================================
// PHASE TRANSITIONS
// =============================================================================

/**
 * DAG 기반 다음 단계 결정
 * 현재 단계와 chainData를 기반으로 가능한 다음 단계 반환
 */
export function getNextPhases(
  currentPhase: WorkflowPhase,
  chainData: WorkflowContext["chainData"]
): WorkflowPhase[] {
  const transitions: Record<WorkflowPhase, WorkflowPhase[]> = {
    "4D": ["Story", "AD"],
    Story: ["1D", "2D", "AD"],
    AD: ["Story", "3D"],
    "1D": ["2D", "3D"],
    "2D": ["Sound", "3D"],
    Sound: ["VEO"],
    "3D": ["VEO", "QC"],
    VEO: ["QC"],
    QC: [],
  };

  return transitions[currentPhase] || [];
}

/**
 * 가능한 첫 번째 다음 단계 반환 (자동 진행용)
 */
export function getDefaultNextPhase(
  currentPhase: WorkflowPhase
): WorkflowPhase | null {
  const nextPhases = getNextPhases(currentPhase, initialContext.chainData);
  return nextPhases[0] || null;
}

// =============================================================================
// WORKFLOW MACHINE
// =============================================================================

export const workflowMachine = setup({
  types: {
    context: {} as WorkflowContext,
    events: {} as WorkflowEvent,
  },
  actions: {
    setAuteur: assign({
      auteurKey: ({ event }) => {
        if (event.type === "SET_AUTEUR") {
          return event.auteurKey;
        }
        return null;
      },
    }),
    setPersona: assign({
      personaData: ({ event }) => {
        if (event.type === "SET_PERSONA") {
          return event.personaData;
        }
        return null;
      },
    }),
    setPhase: assign({
      currentPhase: (_, params: { phase: WorkflowPhase }) => params.phase,
    }),
    savePhaseOutput: assign({
      chainData: ({ context, event }) => {
        if (event.type !== "COMPLETE_PHASE" || !context.currentPhase) {
          return context.chainData;
        }
        return {
          ...context.chainData,
          [context.currentPhase]: {
            phase: context.currentPhase,
            output: event.output,
            timestamp: Date.now(),
          },
        };
      },
    }),
    setError: assign({
      errorMessage: ({ event }) => {
        if (event.type === "ERROR") {
          return event.message;
        }
        return null;
      },
    }),
    clearError: assign({
      errorMessage: () => null,
    }),
    resetContext: assign(() => initialContext),
  },
  guards: {
    hasChainData: ({ context }, params: { phase: WorkflowPhase }) => {
      return context.chainData[params.phase] !== null;
    },
    canProceed: ({ context }) => {
      if (!context.currentPhase) return false;
      const nextPhases = getNextPhases(
        context.currentPhase,
        context.chainData
      );
      return nextPhases.length > 0;
    },
    isCompleted: ({ context }) => {
      // QC가 완료되면 워크플로우 완료
      return context.chainData.QC !== null;
    },
  },
}).createMachine({
  id: "dimensionWorkflow",
  initial: "idle",
  context: initialContext,
  states: {
    idle: {
      on: {
        START_4D: {
          target: "phase1_4D",
          actions: [{ type: "setPhase", params: { phase: "4D" as const } }],
        },
        START_STORY: {
          target: "phase1_Story",
          actions: [{ type: "setPhase", params: { phase: "Story" as const } }],
        },
        START_1D: {
          target: "phase2_1D",
          actions: [{ type: "setPhase", params: { phase: "1D" as const } }],
        },
        SET_AUTEUR: {
          actions: ["setAuteur"],
        },
        SET_PERSONA: {
          actions: ["setPersona"],
        },
      },
    },

    // Phase 1: 거장 분석 단계
    phase1_4D: {
      on: {
        COMPLETE_PHASE: {
          actions: ["savePhaseOutput"],
        },
        NEXT: [
          {
            target: "phase1_Story",
            actions: [{ type: "setPhase", params: { phase: "Story" as const } }],
          },
        ],
        SKIP: {
          target: "phase1_Story",
          actions: [{ type: "setPhase", params: { phase: "Story" as const } }],
        },
        ERROR: {
          target: "error",
          actions: ["setError"],
        },
      },
    },

    phase1_Story: {
      on: {
        COMPLETE_PHASE: {
          actions: ["savePhaseOutput"],
        },
        NEXT: [
          {
            target: "phase2_1D",
            actions: [{ type: "setPhase", params: { phase: "1D" as const } }],
          },
        ],
        SKIP: {
          target: "phase2_1D",
          actions: [{ type: "setPhase", params: { phase: "1D" as const } }],
        },
        BACK: {
          target: "phase1_4D",
          actions: [{ type: "setPhase", params: { phase: "4D" as const } }],
        },
        ERROR: {
          target: "error",
          actions: ["setError"],
        },
      },
    },

    phase1_AD: {
      on: {
        COMPLETE_PHASE: {
          actions: ["savePhaseOutput"],
        },
        NEXT: [
          {
            target: "phase3_3D",
            actions: [{ type: "setPhase", params: { phase: "3D" as const } }],
          },
        ],
        BACK: {
          target: "phase1_Story",
          actions: [{ type: "setPhase", params: { phase: "Story" as const } }],
        },
        ERROR: {
          target: "error",
          actions: ["setError"],
        },
      },
    },

    // Phase 2: 프롬프트 & 스토리보드 단계
    phase2_1D: {
      on: {
        COMPLETE_PHASE: {
          actions: ["savePhaseOutput"],
        },
        NEXT: [
          {
            target: "phase2_2D",
            actions: [{ type: "setPhase", params: { phase: "2D" as const } }],
          },
        ],
        SKIP: {
          target: "phase2_2D",
          actions: [{ type: "setPhase", params: { phase: "2D" as const } }],
        },
        BACK: {
          target: "phase1_Story",
          actions: [{ type: "setPhase", params: { phase: "Story" as const } }],
        },
        ERROR: {
          target: "error",
          actions: ["setError"],
        },
      },
    },

    phase2_2D: {
      on: {
        COMPLETE_PHASE: {
          actions: ["savePhaseOutput"],
        },
        NEXT: [
          {
            target: "phase3_3D",
            actions: [{ type: "setPhase", params: { phase: "3D" as const } }],
          },
        ],
        SKIP: {
          target: "phase3_3D",
          actions: [{ type: "setPhase", params: { phase: "3D" as const } }],
        },
        BACK: {
          target: "phase2_1D",
          actions: [{ type: "setPhase", params: { phase: "1D" as const } }],
        },
        ERROR: {
          target: "error",
          actions: ["setError"],
        },
      },
    },

    phase2_Sound: {
      on: {
        COMPLETE_PHASE: {
          actions: ["savePhaseOutput"],
        },
        NEXT: [
          {
            target: "phase3_VEO",
            actions: [{ type: "setPhase", params: { phase: "VEO" as const } }],
          },
        ],
        BACK: {
          target: "phase2_2D",
          actions: [{ type: "setPhase", params: { phase: "2D" as const } }],
        },
        ERROR: {
          target: "error",
          actions: ["setError"],
        },
      },
    },

    // Phase 3: 비주얼 & 비디오 단계
    phase3_3D: {
      on: {
        COMPLETE_PHASE: {
          actions: ["savePhaseOutput"],
        },
        NEXT: [
          {
            target: "phase3_VEO",
            actions: [{ type: "setPhase", params: { phase: "VEO" as const } }],
          },
        ],
        SKIP: {
          target: "phase3_VEO",
          actions: [{ type: "setPhase", params: { phase: "VEO" as const } }],
        },
        BACK: {
          target: "phase2_2D",
          actions: [{ type: "setPhase", params: { phase: "2D" as const } }],
        },
        ERROR: {
          target: "error",
          actions: ["setError"],
        },
      },
    },

    phase3_VEO: {
      on: {
        COMPLETE_PHASE: {
          actions: ["savePhaseOutput"],
        },
        NEXT: [
          {
            target: "phase3_QC",
            actions: [{ type: "setPhase", params: { phase: "QC" as const } }],
          },
        ],
        SKIP: {
          target: "phase3_QC",
          actions: [{ type: "setPhase", params: { phase: "QC" as const } }],
        },
        BACK: {
          target: "phase3_3D",
          actions: [{ type: "setPhase", params: { phase: "3D" as const } }],
        },
        ERROR: {
          target: "error",
          actions: ["setError"],
        },
      },
    },

    phase3_QC: {
      on: {
        COMPLETE_PHASE: [
          {
            target: "completed",
            actions: ["savePhaseOutput"],
          },
        ],
        BACK: {
          target: "phase3_VEO",
          actions: [{ type: "setPhase", params: { phase: "VEO" as const } }],
        },
        ERROR: {
          target: "error",
          actions: ["setError"],
        },
      },
    },

    completed: {
      type: "final",
      entry: [{ type: "setPhase", params: { phase: null as unknown as WorkflowPhase } }],
    },

    error: {
      on: {
        RESET: {
          target: "idle",
          actions: ["resetContext"],
        },
      },
    },
  },
});

// =============================================================================
// HOOKS
// =============================================================================

export type WorkflowMachineType = typeof workflowMachine;
