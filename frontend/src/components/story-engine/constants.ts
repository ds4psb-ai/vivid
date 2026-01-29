/**
 * Story Engine Workflow Constants
 *
 * Step definitions, themes, and input mapping for the Story Engine workflow.
 * Builds upon DNA Lab outputs (vpe, ad) and produces system prompts for Production.
 *
 * 2026 Patterns:
 * - Non-sequential access (any step accessible)
 * - AI inference when data missing
 * - Cross-app chain data flow (DNA Lab → Story Engine → Production)
 */

import { Layers, Wand2, FileCode, type LucideIcon } from "lucide-react";

/**
 * Step IDs for Story Engine workflow
 */
export type StoryEngineStepId = "story" | "prompt" | "system-prompt";

/**
 * Step configuration for Story Engine workflow
 */
export interface StoryEngineStep {
  /** Unique step identifier */
  id: StoryEngineStepId;
  /** Korean label */
  label: string;
  /** English label */
  labelEn: string;
  /** Lucide icon component */
  icon: LucideIcon;
  /** Short description */
  description: string;
  /** Output data key (for chain data) */
  outputKey: string;
  /** Dimension route key mapping (for panel component reference) */
  dimensionKey: string;
  /** Whether this step can auto-infer missing input data */
  canInferInput?: boolean;
}

/**
 * Story Engine workflow steps
 * Order represents logical flow, but access is non-sequential
 */
export const STORY_ENGINE_STEPS: StoryEngineStep[] = [
  {
    id: "story",
    label: "스토리 설계",
    labelEn: "Story Architect",
    icon: Layers,
    description: "내러티브 구조 설계",
    outputKey: "story",
    dimensionKey: "story-architect",
    canInferInput: false, // Needs DNA Lab data
  },
  {
    id: "prompt",
    label: "프롬프트 연금술",
    labelEn: "Prompt Alchemy",
    icon: Wand2,
    description: "AI 프롬프트 생성",
    outputKey: "prompt",
    dimensionKey: "prompt-alchemy",
    canInferInput: true, // Can work with partial data
  },
  {
    id: "system-prompt",
    label: "시스템 프롬프트",
    labelEn: "System Prompt",
    icon: FileCode,
    description: "최종 시스템 프롬프트",
    outputKey: "system-prompt",
    dimensionKey: "system-prompt",
    canInferInput: false, // Needs story and prompt data
  },
];

/**
 * Step ID to Step lookup
 */
export const STORY_ENGINE_STEPS_MAP: Record<StoryEngineStepId, StoryEngineStep> =
  STORY_ENGINE_STEPS.reduce(
    (acc, step) => ({ ...acc, [step.id]: step }),
    {} as Record<StoryEngineStepId, StoryEngineStep>
  );

/**
 * Input dependency map for Story Engine
 * Defines which steps/data keys provide input to other steps
 *
 * Note: "vpe" and "ad" come from DNA Lab (cross-app dependency)
 */
export const STORY_ENGINE_INPUT_MAP: Record<StoryEngineStepId, string[]> = {
  story: ["vpe", "ad"], // From DNA Lab
  prompt: ["vpe", "ad", "story"], // DNA Lab + Story
  "system-prompt": ["story", "prompt"], // Story Engine internal
};

/**
 * Output dependency map (reverse of input)
 * Which steps consume this step's output
 */
export const STORY_ENGINE_OUTPUT_MAP: Record<StoryEngineStepId, string[]> = {
  story: ["prompt", "system-prompt"], // Story flows to Prompt and System Prompt
  prompt: ["system-prompt"], // Prompt flows to System Prompt
  "system-prompt": [], // Final step within Story Engine, flows to Production
};

/**
 * Step status for workflow progress
 */
export type StepStatus = "pending" | "active" | "completed" | "skipped";

/**
 * Chain data output structure for each step
 */
export interface StoryEngineChainOutput {
  story?: {
    narrative: Record<string, unknown>;
    structure?: Record<string, unknown>;
    analysisTimestamp: number;
  };
  prompt?: {
    generatedPrompt: string;
    parameters?: Record<string, unknown>;
    targetPlatform?: string;
  };
  "system-prompt"?: {
    systemPrompt: string;
    platform: "veo" | "kling" | "both";
    metadata?: Record<string, unknown>;
  };
}

/**
 * Theme configuration for Story Engine
 */
export const STORY_ENGINE_THEME = {
  hue: 270, // Purple (story/creative theme)
  primaryColor: "oklch(0.64 0.18 270)",
  glowColor: "oklch(0.64 0.18 270 / 0.3)",
  gradientFrom: "from-purple-500/20",
  gradientTo: "to-pink-500/20",
};

/**
 * Step theme colors (for visual distinction)
 */
export const STORY_ENGINE_STEP_THEMES: Record<StoryEngineStepId, { hue: number; color: string }> = {
  story: { hue: 270, color: "oklch(0.7 0.15 270)" }, // Purple
  prompt: { hue: 320, color: "oklch(0.7 0.15 320)" }, // Pink
  "system-prompt": { hue: 190, color: "oklch(0.7 0.15 190)" }, // Cyan
};

/**
 * URL parameter name for step navigation
 */
export const STORY_ENGINE_STEP_PARAM = "step";

/**
 * Default step when no parameter provided
 */
export const STORY_ENGINE_DEFAULT_STEP: StoryEngineStepId = "story";

/**
 * Get step by ID with type safety
 */
export function getStepById(id: string): StoryEngineStep | undefined {
  return STORY_ENGINE_STEPS_MAP[id as StoryEngineStepId];
}

/**
 * Get step index in workflow
 */
export function getStepIndex(id: StoryEngineStepId): number {
  return STORY_ENGINE_STEPS.findIndex((step) => step.id === id);
}

/**
 * Get next step in workflow (sequential)
 */
export function getNextStep(id: StoryEngineStepId): StoryEngineStep | undefined {
  const index = getStepIndex(id);
  return index < STORY_ENGINE_STEPS.length - 1 ? STORY_ENGINE_STEPS[index + 1] : undefined;
}

/**
 * Get previous step in workflow (sequential)
 */
export function getPreviousStep(id: StoryEngineStepId): StoryEngineStep | undefined {
  const index = getStepIndex(id);
  return index > 0 ? STORY_ENGINE_STEPS[index - 1] : undefined;
}

/**
 * Check if step has all required input data
 */
export function hasRequiredInputs(
  stepId: StoryEngineStepId,
  chainData: Record<string, unknown>
): boolean {
  const requiredInputs = STORY_ENGINE_INPUT_MAP[stepId];
  return requiredInputs.every((inputKey) => !!chainData[inputKey]);
}

/**
 * Get missing inputs for a step
 */
export function getMissingInputs(
  stepId: StoryEngineStepId,
  chainData: Record<string, unknown>
): string[] {
  const requiredInputs = STORY_ENGINE_INPUT_MAP[stepId];
  return requiredInputs.filter((inputKey) => !chainData[inputKey]);
}

/**
 * Check if a step is the final step that should show Production bridge
 */
export function isFinalStep(stepId: StoryEngineStepId): boolean {
  return stepId === "system-prompt";
}

/**
 * Labels for external data sources (from DNA Lab)
 */
export const EXTERNAL_INPUT_LABELS: Record<string, string> = {
  vpe: "영상 분석 (DNA Lab)",
  ad: "미학 적용 (DNA Lab)",
};

/**
 * Get display label for an input key
 */
export function getInputLabel(inputKey: string): string {
  // Check external inputs first
  if (EXTERNAL_INPUT_LABELS[inputKey]) {
    return EXTERNAL_INPUT_LABELS[inputKey];
  }
  // Check Story Engine steps
  const step = STORY_ENGINE_STEPS_MAP[inputKey as StoryEngineStepId];
  return step?.label || inputKey;
}
