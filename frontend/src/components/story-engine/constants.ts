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

import { Layers, Wand2, type LucideIcon } from "lucide-react";

/**
 * Step IDs for Story Engine workflow
 *
 * Phase 1-3: Reduced from 3 steps to 2 steps
 * - Prompt and System-Prompt merged into "prompt"
 */
export type StoryEngineStepId = "story" | "prompt";

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
 *
 * Phase 1-3: Reduced from 3 steps to 2 steps
 * - Story: Narrative structure design
 * - Prompt: AI prompt generation + System prompt (merged)
 *
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
    label: "프롬프트 생성",
    labelEn: "Prompt Generator",
    icon: Wand2,
    description: "AI 프롬프트 + System Prompt 통합 생성",
    outputKey: "prompt", // Also outputs "system-prompt"
    dimensionKey: "prompt-generator",
    canInferInput: true, // Can work with partial data
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
 * Phase 1-3: Simplified to 2 steps
 * Note: "vpe" and "ad" come from DNA Lab (cross-app dependency)
 */
export const STORY_ENGINE_INPUT_MAP: Record<StoryEngineStepId, string[]> = {
  story: ["vpe", "ad"], // From DNA Lab
  prompt: ["vpe", "ad", "story"], // DNA Lab + Story (outputs both prompt and system-prompt)
};

/**
 * Output dependency map (reverse of input)
 * Which steps consume this step's output
 *
 * Phase 1-3: Prompt is now the final step, outputs to Production
 */
export const STORY_ENGINE_OUTPUT_MAP: Record<StoryEngineStepId, string[]> = {
  story: ["prompt"], // Story flows to Prompt
  prompt: [], // Final step, outputs prompt + system-prompt to Production
};

/**
 * Step status for workflow progress
 */
export type StepStatus = "pending" | "active" | "completed" | "skipped";

/**
 * Chain data output structure for each step
 *
 * Phase 1-3: prompt step now outputs both prompt and system-prompt
 */
export interface StoryEngineChainOutput {
  story?: {
    narrative: Record<string, unknown>;
    structure?: Record<string, unknown>;
    analysisTimestamp: number;
  };
  /** Merged prompt + system-prompt output (Phase 1-3) */
  prompt?: {
    generatedPrompt: string;
    systemPrompt: string; // Merged from system-prompt step
    parameters?: Record<string, unknown>;
    targetPlatform?: string;
    platform?: "veo" | "kling" | "both";
    metadata?: Record<string, unknown>;
  };
  /** @deprecated Use prompt.systemPrompt instead (Phase 1-3 backward compatibility) */
  "system-prompt"?: {
    systemPrompt: string;
    platform: "veo" | "kling" | "both";
    metadata?: Record<string, unknown>;
  };
}

/**
 * Theme configuration for Story Engine
 * V7 Design: Unified Neon Red theme
 */
export const STORY_ENGINE_THEME = {
  hue: 0, // Neon Red (V7 unified theme)
  primaryColor: "oklch(0.62 0.28 20)",
  glowColor: "oklch(0.62 0.28 20 / 0.3)",
  gradientFrom: "from-[var(--stitch-primary)]/20",
  gradientTo: "to-[var(--stitch-primary-accent)]/20",
};

/**
 * Step theme colors (for visual distinction)
 * V7 Design: Unified Neon Red theme with slight variations
 *
 * Phase 1-3: Reduced to 2 steps
 */
export const STORY_ENGINE_STEP_THEMES: Record<StoryEngineStepId, { hue: number; color: string }> = {
  story: { hue: 0, color: "oklch(0.62 0.28 20)" }, // Neon Red
  prompt: { hue: 10, color: "oklch(0.60 0.26 15)" }, // Neon Red variant
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
 *
 * Phase 1-3: prompt is now the final step (merged with system-prompt)
 */
export function isFinalStep(stepId: StoryEngineStepId): boolean {
  return stepId === "prompt";
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
